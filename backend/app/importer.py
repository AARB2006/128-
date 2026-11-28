"""
Import logic: turn submitted links into songs in the user's library.

Refactored from the POC's POST /playlists. The differences:
  * it saves SONGS (no playlist is created),
  * one bad link no longer cancels the others: each link gets its own result,
  * progress is written to import_items as it happens, so the browser can show
    "Importing Music 3/10..." by reading those rows.

The rules (one import at a time, the daily limit, links already in the
library) are checked by the database function start_import, called with the
user's login token. The background work then saves each result with the
job key that function returned.
"""

import logging
from dataclasses import dataclass

from .config import MAX_LINKS_PER_IMPORT
from .metadata import VideoRejected, fetch_metadata
from .supabase_store import StoreError
from .youtube import InvalidLink, parse_video_id, watch_url


logger = logging.getLogger(__name__)

# Database answers that are the user's to read (the rest become "try again").
REJECTION_STATUSES = (401, 409, 422, 429)


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


def prepare_import(store, user, raw_urls: list[str]):
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

    entries = plan_entries(urls)

    try:
        result = store.start_import(
            user,
            [
                {
                    "line_no": e.line_no,
                    "submitted_url": e.url[:2048],
                    "video_id": e.video_id,
                    "status": e.status,
                    "error_message": e.error,
                }
                for e in entries
            ],
        )
    except StoreError as error:
        if error.status_code in REJECTION_STATUSES:
            raise ImportRejected(error.status_code, str(error)) from error
        raise

    # The database marks links already in the library as duplicates.
    decided = {item["line_no"]: item for item in result["items"]}
    for entry in entries:
        entry.status = decided[entry.line_no]["status"]
        entry.error = decided[entry.line_no]["error_message"]

    return result["batch_id"], entries


def run_import(store, batch_id: str, entries: list[Entry]) -> None:
    """Process the pending links one by one. Runs in the background."""
    try:
        for entry in entries:
            if entry.status == "pending":
                _process(store, batch_id, entry)

    except Exception:
        # Most likely Supabase became unreachable. Don't leave the batch hanging.
        logger.exception("Import %s stopped unexpectedly", batch_id)
        for entry in entries:
            if entry.status == "pending":
                entry.status = "failed"
                entry.error = "The import stopped unexpectedly."

    finally:
        # Closes the batch; any link still pending is marked failed.
        try:
            store.finish_import(batch_id)
        except Exception:
            logger.exception("Could not finish import %s", batch_id)


def _process(store, batch_id: str, entry: Entry) -> None:
    try:
        url = watch_url(entry.video_id)
        metadata = fetch_metadata(url)  # looked up here so tests can replace it

    except VideoRejected as error:
        entry.status = "failed"
        entry.error = str(error)

    except Exception:
        logger.exception("Unexpected error importing %s", entry.video_id)
        entry.status = "failed"
        entry.error = "An unexpected error occurred while checking this video."

    else:
        # Saves the song; 'duplicate' if it was added by another request meanwhile.
        entry.status = store.record_import_item(
            batch_id,
            entry.line_no,
            "success",
            title=metadata["title"],
            duration_seconds=metadata["duration_seconds"],
        )
        entry.error = "Already in your library." if entry.status == "duplicate" else None
        return

    store.record_import_item(batch_id, entry.line_no, "failed", error_message=entry.error)
