import logging
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .auth import get_current_user_id
from .errors import api_error
from .importer import ImportRejected, prepare_import, run_import
from .schemas import ImportRequest, ImportStarted
from .supabase_store import StoreError, SupabaseStore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@lru_cache
def get_store() -> SupabaseStore:
    if not config.supabase_is_configured():
        api_error(503, "The server is not configured yet.")

    return SupabaseStore(config.SUPABASE_URL, config.SUPABASE_SECRET_KEY)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A restart kills running imports; close out any that were left hanging.
    if config.supabase_is_configured():
        try:
            count = get_store().fail_interrupted_batches()
            if count:
                logger.info("Marked %s interrupted import(s) as failed", count)
        except Exception:
            logger.exception("Could not clean up interrupted imports")
    else:
        logger.warning("Supabase is not configured; imports are disabled.")

    yield


app = FastAPI(title="YT-MP3 Family Playlist Maker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=False,  # we use a bearer token, not cookies
    allow_methods=["GET", "POST"],
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
    owner_id: str = Depends(get_current_user_id),
    store: SupabaseStore = Depends(get_store),
):
    """
    Validate the links and start importing them in the background.

    Returns straight away with the batch id. The browser then watches
    progress by reading that batch's import_items rows from Supabase
    (row-level security lets each user read only their own).
    """
    try:
        batch_id, entries = prepare_import(store, owner_id, request.urls)

    except ImportRejected as error:
        api_error(error.status_code, error.message)

    except StoreError:
        api_error(503, "Could not reach the database. Please try again.")

    if any(entry.status == "pending" for entry in entries):
        background_tasks.add_task(run_import, store, batch_id, owner_id, entries)

    return ImportStarted(batch_id=batch_id, total_links=len(entries))