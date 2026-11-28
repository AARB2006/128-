"""
Keys for the imports and exports this backend is running.

Starting a job (with the user's login token) returns a random job key; the
background work sends it with every progress update. The keys are kept in
memory and in a small file next to the backend, so that a job cut off by
closing YT-MP3 can be marked "interrupted" the next time it starts. A key can
only update its own job, and the database stops accepting it once the job ends.
"""

import json
import logging
import os
import threading
from pathlib import Path


logger = logging.getLogger(__name__)


class JobKeys:
    def __init__(self, path: Path | None = None):
        self._path = Path(path) if path else None
        self._lock = threading.Lock()
        self._keys: dict[str, tuple[str, str]] = {}  # job_id -> (kind, key)
        self._previous: dict[str, tuple[str, str]] = self._load()

    def remember(self, kind: str, job_id: str, key: str) -> None:
        with self._lock:
            self._keys[job_id] = (kind, key)
            self._save()

    def key_for(self, job_id: str) -> str | None:
        with self._lock:
            entry = self._keys.get(job_id) or self._previous.get(job_id)
        return entry[1] if entry else None

    def forget(self, job_id: str) -> None:
        with self._lock:
            self._keys.pop(job_id, None)
            self._previous.pop(job_id, None)
            self._save()

    def left_from_last_run(self) -> list[tuple[str, str, str]]:
        """(kind, job_id, key) for jobs that were running when the backend last stopped."""
        with self._lock:
            return [(kind, job_id, key) for job_id, (kind, key) in self._previous.items()]

    # ---- the file ----------------------------------------------------------------

    def _load(self) -> dict[str, tuple[str, str]]:
        if not self._path or not self._path.is_file():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return {
                job_id: (entry["kind"], entry["key"])
                for job_id, entry in data.items()
                if entry.get("kind") in ("import", "export") and entry.get("key")
            }
        except (OSError, ValueError, AttributeError, TypeError, KeyError):
            logger.warning("Ignoring an unreadable job file: %s", self._path)
            return {}

    def _save(self) -> None:
        """Write every key still in use. Called with the lock held."""
        if not self._path:
            return
        entries = {**self._previous, **self._keys}
        data = {job_id: {"kind": kind, "key": key} for job_id, (kind, key) in entries.items()}
        try:
            if not data:
                self._path.unlink(missing_ok=True)
                return
            temporary = self._path.with_name(self._path.name + ".tmp")
            temporary.write_text(json.dumps(data), encoding="utf-8")
            os.replace(temporary, self._path)
        except OSError:
            # Not fatal: the database also gives up on jobs left running far
            # too long, so a lost file only delays the cleanup.
            logger.warning("Could not save the job file %s", self._path)
