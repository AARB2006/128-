"""
Import logic: turn submitted links into songs in the user's library.

Refactored from the POC's POST /playlists. The differences:
  * it saves SONGS (no playlist is created),
  * one bad link no longer cancels the others: each link gets its own result,
  * progress is written to import_items as it happens, so the browser can show
    "Importing Music 3/10..." by reading those rows.
"""

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .config import DAILY_IMPORT_LIMIT, MAX_LINKS_PER_IMPORT
from .metadata import VideoRejected, fetch_metadata
from .youtube import InvalidLink, parse_video_id, watch_url


logger = logging.getLogger(__name__)

# Makes "check for a running import, then create one" atomic. This is enough
# for a single backend process, which is what we run.
_start_lock = threading.Lock()


class ImportRejected(Exception):
    """The request was refused before any batch was created."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@dataclass
class Entry:
    line_no: int  # 1-based position among the submitted (non-blank) links
    url: str
    video_id: str | None = None
    status: str = "pending"  # pending | success | duplicate | invalid | failed
    error: str | None = None


def plan_entries(urls: list[str]) -> list[Entry]:
    """Check every link's shape. Makes no network requests."""
    entries = []
    seen = set()

    for line_no, url in enumerate(urls, start=1):
        entry = Entry(line_no=line_no, url=url)
        entries.append(entry)

        try:
            entry.video_id = parse_video_id(url)
        except InvalidLink as error:
            entry.status = "invalid"
            entry.error = str(error)
            continue

        if entry.video_id in seen:
            entry.status = "duplicate"
            entry.error = "This video appears more than once in this import."
            continue

        seen.add(entry.video_id)

    return entries


def batch_status(entries: list[Entry]) -> str:
    added = any(e.status == "success" for e in entries)
    problems = any(e.status in ("failed", "invalid") for e in entries)

    if problems and added:
        return "partial"
    if problems:
        return "failed"
    return "completed"  # everything added, or only duplicates


def prepare_import(store, owner_id: str, raw_urls: list[str]):
    """
    Validate the request, record the batch and its links, and return
    (batch_id, entries). Raises ImportRejected if it must not start.
    """
    urls = [raw.strip() for raw in raw_urls if raw.strip()]

    if not urls:
        raise ImportRejected(422, "Enter at least one YouTube link.")

    if len(urls) > MAX_LINKS_PER_IMPORT:
        raise ImportRejected(
            422, f"You can import at most {MAX_LINKS_PER_IMPORT} links at a time."
        )

    since = datetime.now(timezone.utc) - timedelta(hours=24)

    with _start_lock:
        if store.has_active_batch(owner_id):
            raise ImportRejected(
                409, "An import is already running. Wait for it to finish."
            )

        used = store.recent_link_count(owner_id, since)
        if used + len(urls) > DAILY_IMPORT_LIMIT:
            remaining = max(DAILY_IMPORT_LIMIT - used, 0)
            raise ImportRejected(
                429,
                f"Daily import limit reached. You can import {remaining} more "
                "link(s) in the next 24 hours.",
            )

        entries = plan_entries(urls)

        # Videos the user already has are duplicates, decided in one query.
        waiting = [e.video_id for e in entries if e.status == "pending"]
        already_have = store.existing_video_ids(owner_id, waiting)
        for entry in entries:
            if entry.status == "pending" and entry.video_id in already_have:
                entry.status = "duplicate"
                entry.error = "Already in your library."

        needs_work = any(e.status == "pending" for e in entries)
        batch_id = store.create_batch(
            owner_id,
            total_links=len(entries),
            status="processing" if needs_work else batch_status(entries),
        )

    now = datetime.now(timezone.utc).isoformat()
    store.create_items(
        batch_id,
        [
            {
                "line_no": e.line_no,
                "submitted_url": e.url[:2048],
                "video_id": e.video_id,
                "status": e.status,
                "error_message": e.error,
                "processed_at": None if e.status == "pending" else now,
            }
            for e in entries
        ],
    )

    return batch_id, entries


def run_import(store, batch_id: str, owner_id: str, entries: list[Entry]) -> None:
    """Process the pending links one by one. Runs in the background."""
    try:
        for entry in entries:
            if entry.status == "pending":
                _process(store, batch_id, owner_id, entry)

    except Exception:
        # Most likely Supabase became unreachable. Don't leave the batch hanging.
        logger.exception("Import %s stopped unexpectedly", batch_id)
        for entry in entries:
            if entry.status == "pending":
                entry.status = "failed"
                entry.error = "The import stopped unexpectedly."

    finally:
        try:
            store.finish_batch(batch_id, batch_status(entries))
        except Exception:
            logger.exception("Could not finish import %s", batch_id)


def _process(store, batch_id: str, owner_id: str, entry: Entry) -> None:
    song_id = None

    try:
        url = watch_url(entry.video_id)
        metadata = fetch_metadata(url)  # looked up here so tests can replace it

        song_id = store.insert_song(
            owner_id,
            {
                "video_id": entry.video_id,
                "source_url": url,
                "title": metadata["title"],
                "duration_seconds": metadata["duration_seconds"],
            },
        )

        if song_id is None:  # added by another request in the meantime
            entry.status = "duplicate"
            entry.error = "Already in your library."
        else:
            entry.status = "success"

    except VideoRejected as error:
        entry.status = "failed"
        entry.error = str(error)

    except Exception:
        logger.exception("Unexpected error importing %s", entry.video_id)
        entry.status = "failed"
        entry.error = "An unexpected error occurred while checking this video."

    store.update_item(
        batch_id,
        entry.line_no,
        status=entry.status,
        error_message=entry.error,
        song_id=song_id,
    )