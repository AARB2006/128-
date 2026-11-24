"""
PlaylistExportService: turn one playlist into a downloadable ZIP of MP3s.

Like imports, an export runs in the background. The browser starts it with
POST /exports and then reads its progress from the `exports` row in Supabase
(row-level security lets each user read only their own).

Failure rules (use case B8):
  * A song that can't be downloaded is skipped and its reason recorded (E1).
  * A ZIP is offered only after it is fully written and checked (E2).
  * Missing FFmpeg, low disk space and a full disk are reported (E3).
  * Temporary audio is always deleted, whatever happens (the diagram's
    "Cleanup Guarantee").

This assumes ONE backend process: the queue, cancel requests and download
links are kept in memory.
"""

import errno
import logging
import math
import secrets
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import config
from ..metadata import classify_error
from ..names import safe_filename
from ..supabase_store import StoreError
from . import audio, packager, workspace


logger = logging.getLogger(__name__)

ACTIVE = ("pending", "processing", "packaging")
FINISHED_WITH_FILE = ("completed", "partial")

DOWNLOAD_LINK_SECONDS = 60
PROGRESS_WRITE_SECONDS = 1.0

# Reasons that mean YouTube is blocking us or can't be reached, rather than
# "this one video is gone". Several in a row stop the export early.
BLOCKED_HINTS = ("sign in to confirm", "not a bot", "429", "too many requests")
NETWORK_HINTS = ("timed out", "timeout", "urlopen error", "temporary failure",
                 "name resolution", "connection", "ssl")

RATE_LIMITED_REASON = "YouTube is limiting downloads right now. Try again later."
GENERIC_SONG_REASON = "This song could not be downloaded or converted."
METADATA_FALLBACK = classify_error("")


class ExportRejected(Exception):
    """The request was refused; nothing was started."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class DiskFull(Exception):
    pass


# The song details a job needs while it runs. They stay in memory only: the
# database records just which song was at which position, and the History
# page reads titles and names from `songs` and `playlists` when it loads.
@dataclass
class Track:
    position: int
    song_id: str | None
    video_id: str
    title: str


@dataclass
class ExportJob:
    export_id: str
    owner_id: str
    tracks: list[Track] = field(default_factory=list)


# ---- in-memory state (one backend process) ----------------------------------

_start_lock = threading.Lock()
_state_lock = threading.Lock()
_cancel_requested: set[str] = set()
_running: set[str] = set()
_download_links: dict[str, tuple[str, Path, str, float]] = {}

_executor = ThreadPoolExecutor(
    max_workers=max(1, config.MAX_CONCURRENT_EXPORTS),
    thread_name_prefix="export",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def running_ids() -> frozenset[str]:
    with _state_lock:
        return frozenset(_running)


# ---- starting -------------------------------------------------------------------

def prepare_export(store, owner_id: str, playlist_id: str) -> ExportJob:
    """Check everything that can be checked up front, then record the job."""
    if not ffmpeg_available():
        raise ExportRejected(
            503, "Export is not available right now (the audio converter is missing)."
        )

    playlist = store.get_owned_playlist(owner_id, playlist_id)
    if playlist is None:
        raise ExportRejected(404, "Playlist not found.")

    rows = store.get_playlist_tracks(owner_id, playlist_id)
    if not rows:
        raise ExportRejected(409, "This playlist has no songs to export.")

    if len(rows) > config.MAX_EXPORT_SONGS:
        raise ExportRejected(
            422,
            f"Playlists with more than {config.MAX_EXPORT_SONGS} songs can't be "
            "exported yet.",
        )

    needed_mb = config.EXPORT_MIN_FREE_MB + len(rows) * config.EXPORT_ESTIMATED_MB_PER_SONG
    if workspace.free_mb() < needed_mb:
        raise ExportRejected(
            507,
            "The server doesn't have enough space for this export right now. "
            "Try a smaller playlist or try again later.",
        )

    since = datetime.now(timezone.utc) - timedelta(hours=24)

    with _start_lock:
        used = store.recent_export_song_count(owner_id, since)
        if used + len(rows) > config.DAILY_EXPORT_SONG_LIMIT:
            remaining = max(config.DAILY_EXPORT_SONG_LIMIT - used, 0)
            raise ExportRejected(
                429,
                f"Daily export limit reached. You can export {remaining} more "
                "song(s) in the next 24 hours.",
            )

        try:
            export_id = store.create_export(owner_id, playlist, len(rows))
        except StoreError as error:
            if error.status_code == 409:
                raise ExportRejected(
                    409, "An export is already running. Wait for it to finish."
                ) from error
            raise

    store.create_export_items(export_id, rows)

    return ExportJob(
        export_id=export_id,
        owner_id=owner_id,
        tracks=[Track(**row) for row in rows],
    )


def submit(store, job: ExportJob) -> None:
    """Queue the job. At most MAX_CONCURRENT_EXPORTS run at once."""
    _executor.submit(run_export, store, job)


# ---- cancelling ----------------------------------------------------------------

def request_cancel(store, owner_id: str, export_id: str) -> None:
    row = store.get_export(owner_id, export_id)
    if row is None:
        raise ExportRejected(404, "Export not found.")
    if row["status"] not in ACTIVE:
        raise ExportRejected(409, "This export has already finished.")

    with _state_lock:
        _cancel_requested.add(export_id)


def _is_cancelled(export_id: str) -> bool:
    with _state_lock:
        return export_id in _cancel_requested


# ---- progress --------------------------------------------------------------------

class Progress:
    """Writes `exports.percent`, at most once a second."""

    def __init__(self, store, export_id: str, total: int, clock=time.monotonic):
        self.store = store
        self.export_id = export_id
        self.total = total
        self.clock = clock
        self.written = 0
        self.written_at = 0.0

    def song(self, index: int, fraction: float, force: bool = False, **extra) -> None:
        """index is 0-based; songs fill 0-95%, packaging takes the rest."""
        percent = math.floor((index + fraction) / self.total * 95)
        self.write(min(percent, 95), force=force, **extra)

    def write(self, percent: int, force: bool = False, **extra) -> None:
        percent = max(percent, self.written)
        now = self.clock()

        if not extra and percent == self.written:
            return
        if not force and now - self.written_at < PROGRESS_WRITE_SECONDS:
            return

        try:
            self.store.update_export(self.export_id, percent=percent, **extra)
            self.written = percent
            self.written_at = now
        except StoreError:
            # A missed progress update is harmless; the next one catches up.
            logger.warning("Could not save progress for export %s", self.export_id)


# ---- running -----------------------------------------------------------------------

def file_name_for(track: Track, width: int) -> str:
    title = safe_filename(track.title, fallback=f"track_{track.position}")
    return f"{track.position:0{width}d} - {title}"


def describe_failure(error: Exception) -> tuple[str, bool]:
    """(reason shown to the user, whether YouTube is blocking or unreachable)."""
    message = str(error)
    lowered = message.lower()

    if any(hint in lowered for hint in BLOCKED_HINTS):
        return RATE_LIMITED_REASON, True

    reason = classify_error(message)
    if reason == METADATA_FALLBACK:
        reason = GENERIC_SONG_REASON

    return reason, any(hint in lowered for hint in NETWORK_HINTS)


def _is_disk_full(error: Exception) -> bool:
    if isinstance(error, OSError) and error.errno == errno.ENOSPC:
        return True
    return "no space left on device" in str(error).lower()


def run_export(store, job: ExportJob) -> None:
    """Process every song, build the ZIP, and always clean up."""
    export_id = job.export_id
    status = "failed"
    final_fields = {}

    with _state_lock:
        _running.add(export_id)

    try:
        if _is_cancelled(export_id):
            status = "cancelled"
            store.skip_pending_export_items(export_id, "The export was cancelled.")
            return

        store.update_export(export_id, status="processing", started_at=now_iso())

        work = workspace.create(export_id)
        width = max(2, len(str(max(t.position for t in job.tracks))))
        progress = Progress(store, export_id, len(job.tracks))

        files: list[Path] = []
        failed = 0
        blocked_in_a_row = 0

        for index, track in enumerate(job.tracks):
            if _is_cancelled(export_id):
                status = "cancelled"
                store.skip_pending_export_items(export_id, "The export was cancelled.")
                return

            stem = file_name_for(track, width)

            try:
                path = audio.download_mp3(
                    track.video_id,
                    work,
                    stem,
                    on_progress=lambda fraction, i=index: progress.song(i, fraction),
                    should_cancel=lambda: _is_cancelled(export_id),
                )

            except audio.Cancelled:
                status = "cancelled"
                store.skip_pending_export_items(export_id, "The export was cancelled.")
                return

            except Exception as error:
                if _is_disk_full(error):
                    raise DiskFull() from error

                reason, blocked = describe_failure(error)
                logger.warning(
                    "Export %s: song %s (%s) failed: %s",
                    export_id, track.position, track.video_id, error,
                )
                failed += 1
                store.update_export_item(
                    export_id, track.position, status="failed", error_message=reason
                )

                blocked_in_a_row = blocked_in_a_row + 1 if blocked else 0
                if blocked_in_a_row >= config.EXPORT_MAX_CONSECUTIVE_FAILURES:
                    store.skip_pending_export_items(export_id, RATE_LIMITED_REASON)
                    final_fields["error_message"] = RATE_LIMITED_REASON
                    return

            else:
                files.append(path)
                blocked_in_a_row = 0
                store.update_export_item(export_id, track.position, status="success")

            progress.song(index + 1, 0.0, force=True, exported_songs=len(files))

        if not files:
            final_fields["error_message"] = "None of the songs could be exported."
            return

        if _is_cancelled(export_id):
            status = "cancelled"
            return

        store.update_export(export_id, status="packaging", percent=97)

        size = packager.build_zip(files, workspace.ready_path(export_id))
        expires = datetime.now(timezone.utc) + timedelta(
            minutes=config.EXPORT_FILE_TTL_MINUTES
        )

        status = "partial" if failed else "completed"
        final_fields.update(
            percent=100,
            exported_songs=len(files),
            file_size_bytes=size,
            file_expires_at=expires.isoformat(),
        )

    except DiskFull:
        logger.error("Export %s: the disk is full", export_id)
        status = "failed"
        final_fields = {
            "error_message": "The server ran out of space while exporting. Try again later."
        }

    except Exception:
        logger.exception("Export %s stopped unexpectedly", export_id)
        status = "failed"
        final_fields = {
            "error_message": "Something went wrong while creating the export."
        }

    finally:
        # Cleanup guarantee: temporary audio never outlives the job.
        workspace.remove(export_id)
        if status not in FINISHED_WITH_FILE:
            workspace.discard_ready(export_id)

        with _state_lock:
            _running.discard(export_id)
            _cancel_requested.discard(export_id)

        try:
            if status not in FINISHED_WITH_FILE:
                store.skip_pending_export_items(
                    export_id, final_fields.get("error_message") or "The export was stopped."
                )
            store.update_export(
                export_id, status=status, completed_at=now_iso(), **final_fields
            )
        except Exception:
            # Startup cleanup marks it failed if this never reaches Supabase.
            logger.exception("Could not save the result of export %s", export_id)


# ---- downloading -----------------------------------------------------------------------

def create_download_link(store, owner_id: str, export_id: str) -> str:
    """A path the browser can open for 60 seconds to download the ZIP."""
    row = store.get_export(owner_id, export_id)
    if row is None:
        raise ExportRejected(404, "Export not found.")

    if row["status"] not in FINISHED_WITH_FILE:
        raise ExportRejected(409, "This export has no file to download.")

    path = workspace.ready_path(export_id)
    expires_at = row.get("file_expires_at")
    expired = (
        not expires_at
        or datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc)
    )
    if expired or not path.is_file():
        raise ExportRejected(410, "This export has expired. Export the playlist again.")

    # The download is named after the playlist as it is now.
    playlist = row.get("playlist") or {}
    name = safe_filename(playlist.get("name") or "", fallback="playlist") + ".zip"

    token = secrets.token_urlsafe(32)
    with _state_lock:
        _forget_old_links()
        _download_links[token] = (
            export_id,
            path,
            name,
            time.monotonic() + DOWNLOAD_LINK_SECONDS,
        )

    return f"/exports/download/{token}"


def redeem_download_link(token: str) -> tuple[Path, str]:
    with _state_lock:
        _forget_old_links()
        entry = _download_links.get(token)

    if entry is None:
        raise ExportRejected(404, "This download link is no longer valid.")

    _, path, name, _ = entry
    if not path.is_file():
        raise ExportRejected(410, "This export has expired. Export the playlist again.")

    return path, name


def _forget_old_links() -> None:
    now = time.monotonic()
    for token in [t for t, entry in _download_links.items() if entry[3] <= now]:
        del _download_links[token]


# ---- deleting history -------------------------------------------------------------------

def _discard_file(export_id: str) -> None:
    try:
        workspace.discard_ready(export_id)
    except OSError:
        # E.g. the file is still being downloaded; the sweeper removes it later.
        logger.warning("Could not delete the ZIP for export %s yet", export_id)


def delete_export(store, owner_id: str, export_id: str) -> None:
    """Remove one finished export from the history, and its ZIP if it still exists."""
    row = store.get_export(owner_id, export_id)
    if row is None:
        raise ExportRejected(404, "Export not found.")
    if row["status"] in ACTIVE:
        raise ExportRejected(409, "This export is still running. Cancel it first.")

    if not store.delete_export(owner_id, export_id):
        raise ExportRejected(404, "Export not found.")

    _discard_file(export_id)


def clear_history(store, owner_id: str) -> int:
    """Remove every finished export of this user. A running export is kept."""
    ids = store.delete_finished_exports(owner_id)
    for export_id in ids:
        _discard_file(export_id)
    return len(ids)


# ---- housekeeping ------------------------------------------------------------------------

def sweep() -> int:
    return workspace.sweep(active_ids=running_ids())


def start_sweeper(interval_seconds: int = 600) -> threading.Thread:
    """Delete expired ZIPs every few minutes for as long as the server runs."""

    def loop():
        while True:
            time.sleep(interval_seconds)
            try:
                sweep()
            except Exception:
                logger.exception("Export cleanup failed")

    thread = threading.Thread(target=loop, name="export-sweeper", daemon=True)
    thread.start()
    return thread
