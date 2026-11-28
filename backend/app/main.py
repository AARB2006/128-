"""
FastAPI app: defines the import and export endpoints,
CORS, and startup/shutdown tasks.
"""

import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from . import config
from .auth import SignedInUser, get_signed_in_user
from .errors import api_error
from .exports import service as exports
from .frontend import mount_frontend
from .importer import ImportRejected, prepare_import, run_import
from .schemas import (
    DownloadLink,
    ExportRequest,
    ExportStarted,
    ImportRequest,
    ImportStarted,
)
from .jobs import JobKeys
from .supabase_store import StoreError, SupabaseStore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@lru_cache
def get_store() -> SupabaseStore:
    if not config.supabase_is_configured():
        api_error(503, "The server is not configured yet.")

    return SupabaseStore(
        config.SUPABASE_URL, config.SUPABASE_PUBLISHABLE_KEY, jobs=JobKeys(config.JOBS_FILE)
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Closing YT-MP3 stops running imports and exports; mark the ones this
    # computer was running as interrupted instead of leaving them "running".
    if config.supabase_is_configured():
        try:
            count = get_store().recover_interrupted_jobs()
            if count:
                logger.info("Marked %s interrupted job(s) as failed", count)
        except Exception:
            logger.exception("Could not clean up interrupted jobs")
    else:
        logger.warning("Supabase is not configured; imports and exports are disabled.")

    # Then delete any files they left behind.
    try:
        exports.sweep()
    except Exception:
        logger.exception("Could not clean up old export files")
    exports.start_sweeper()

    if not exports.ffmpeg_available():
        logger.warning("FFmpeg was not found; exports are disabled.")

    yield


app = FastAPI(title="YT-MP3 Family Playlist Maker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=False,  # we use a bearer token, not cookies
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Content-Disposition"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/imports", response_model=ImportStarted, status_code=202)
def start_import(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    user: SignedInUser = Depends(get_signed_in_user),
    store: SupabaseStore = Depends(get_store),
):
    """
    Validate the links and start importing them in the background.

    Returns straight away with the batch id. The browser then watches
    progress by reading that batch's import_items rows from Supabase
    (row-level security lets each user read only their own).
    """
    try:
        batch_id, entries = prepare_import(store, user, request.urls)

    except ImportRejected as error:
        api_error(error.status_code, error.message)

    except StoreError:
        api_error(503, "Could not reach the database. Please try again.")

    if any(entry.status == "pending" for entry in entries):
        background_tasks.add_task(run_import, store, batch_id, entries)

    return ImportStarted(batch_id=batch_id, total_links=len(entries))


# ---- exports ------------------------------------------------------------------

def _export_error(error: exports.ExportRejected):
    api_error(error.status_code, error.message)


@app.post("/exports", response_model=ExportStarted, status_code=202)
def start_export(
    request: ExportRequest,
    user: SignedInUser = Depends(get_signed_in_user),
    store: SupabaseStore = Depends(get_store),
):
    """
    Check the playlist and queue its export. Returns straight away; the browser
    then reads progress from its `exports` row in Supabase.
    """
    try:
        job = exports.prepare_export(store, user, str(request.playlist_id))
    except exports.ExportRejected as error:
        _export_error(error)
    except StoreError:
        api_error(503, "Could not reach the database. Please try again.")

    exports.submit(store, job)
    return ExportStarted(export_id=job.export_id, total_songs=len(job.tracks))


@app.post("/exports/{export_id}/cancel", status_code=202)
def cancel_export(
    export_id: UUID,
    user: SignedInUser = Depends(get_signed_in_user),
    store: SupabaseStore = Depends(get_store),
):
    try:
        exports.request_cancel(store, user, str(export_id))
    except exports.ExportRejected as error:
        _export_error(error)
    except StoreError:
        api_error(503, "Could not reach the database. Please try again.")

    return {"status": "cancelling"}


@app.post("/exports/{export_id}/download-link", response_model=DownloadLink)
def export_download_link(
    export_id: UUID,
    user: SignedInUser = Depends(get_signed_in_user),
    store: SupabaseStore = Depends(get_store),
):
    try:
        path = exports.create_download_link(store, user, str(export_id))
    except exports.ExportRejected as error:
        _export_error(error)
    except StoreError:
        api_error(503, "Could not reach the database. Please try again.")

    return DownloadLink(path=path)


@app.get("/exports/download/{token}")
def download_export(token: str):
    """
    A normal browser download, so there is no Authorization header here:
    the short-lived token from /download-link is the permission.
    """
    try:
        path, name = exports.redeem_download_link(token)
    except exports.ExportRejected as error:
        _export_error(error)

    return FileResponse(path, filename=name, media_type="application/zip")


@app.delete("/exports/{export_id}", status_code=204)
def remove_export(
    export_id: UUID,
    user: SignedInUser = Depends(get_signed_in_user),
    store: SupabaseStore = Depends(get_store),
):
    """Remove one finished export from the history (and delete its ZIP)."""
    try:
        exports.delete_export(store, user, str(export_id))
    except exports.ExportRejected as error:
        _export_error(error)
    except StoreError:
        api_error(503, "Could not reach the database. Please try again.")

    return Response(status_code=204)


@app.delete("/exports")
def clear_export_history(
    user: SignedInUser = Depends(get_signed_in_user),
    store: SupabaseStore = Depends(get_store),
):
    """Remove every finished export from the history. A running one is kept."""
    try:
        deleted = exports.clear_history(store, user)
    except StoreError:
        api_error(503, "Could not reach the database. Please try again.")

    return {"deleted": deleted}


# ---- The app itself (installed mode) ------------------------------------------

# Added last, so every API route above is matched first.
if config.FRONTEND_DIST_DIR:
    served_from = mount_frontend(app, config.FRONTEND_DIST_DIR)
    logger.info("Serving the app from %s", served_from)
