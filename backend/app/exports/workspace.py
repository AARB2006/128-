"""
TemporaryFileManager: where export files live, and when they are deleted.

    EXPORT_DIR/work/<export_id>/   MP3s while an export runs (removed when it ends)
    EXPORT_DIR/ready/<export_id>.zip   finished ZIPs (removed after the TTL)

Nothing here is permanent: the app only stores links.
"""

import logging
import shutil
import time
from pathlib import Path

from .. import config


logger = logging.getLogger(__name__)


def work_dir(export_id: str) -> Path:
    return config.EXPORT_DIR / "work" / export_id


def ready_path(export_id: str) -> Path:
    return config.EXPORT_DIR / "ready" / f"{export_id}.zip"


def create(export_id: str) -> Path:
    path = work_dir(export_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def remove(export_id: str) -> None:
    shutil.rmtree(work_dir(export_id), ignore_errors=True)


def discard_ready(export_id: str) -> None:
    path = ready_path(export_id)
    path.unlink(missing_ok=True)
    path.with_name(path.name + ".part").unlink(missing_ok=True)


def free_mb() -> int:
    config.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(config.EXPORT_DIR).free // (1024 * 1024)


def sweep(active_ids=frozenset(), now: float | None = None) -> int:
    """Delete expired ZIPs and leftover work folders. Returns how many were removed."""
    now = time.time() if now is None else now
    max_age = config.EXPORT_FILE_TTL_MINUTES * 60
    removed = 0

    ready = config.EXPORT_DIR / "ready"
    if ready.is_dir():
        for path in ready.iterdir():
            try:
                if now - path.stat().st_mtime > max_age:
                    path.unlink(missing_ok=True)
                    removed += 1
            except OSError:
                logger.exception("Could not remove %s", path)

    work = config.EXPORT_DIR / "work"
    if work.is_dir():
        for path in work.iterdir():
            if path.name not in active_ids:
                shutil.rmtree(path, ignore_errors=True)
                removed += 1

    return removed
