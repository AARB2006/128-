"""
Backend settings read from backend/.env
(limits, paths, timeouts), with defaults.
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]

# Load variables from backend/.env
load_dotenv(BACKEND_DIR / ".env")

# ---- Import limits ----------------------------------------------------------

# Matches the 1-10 check on import_batches.total_links in the database.
MAX_LINKS_PER_IMPORT = 10

# The daily import limit, the song limit per export and the daily export limit
# are the same for every user and computer, so they live in the database
# (private.app_limits; see database/schema.sql, section 10).

# Reject videos longer than 30 minutes.
MAX_VIDEO_SECONDS = int(os.getenv("MAX_VIDEO_SECONDS", "1800"))

# Node.js is already installed for the Vue/Vite project.
# yt-dlp can use it as its JavaScript runtime.
JS_RUNTIME = os.getenv("JS_RUNTIME", "node")

# ---- Export limits ----------------------------------------------------------

# Exports running at the same time on this server. Others wait in a queue.
MAX_CONCURRENT_EXPORTS = int(os.getenv("MAX_CONCURRENT_EXPORTS", "2"))

# How long a finished ZIP stays downloadable before it is deleted.
EXPORT_FILE_TTL_MINUTES = int(os.getenv("EXPORT_FILE_TTL_MINUTES", "60"))

# Free disk space to keep in reserve, plus a rough size per song.
EXPORT_MIN_FREE_MB = int(os.getenv("EXPORT_MIN_FREE_MB", "1024"))
EXPORT_ESTIMATED_MB_PER_SONG = 15

# Stop early when this many songs in a row fail because YouTube is blocking
# or unreachable, instead of hammering it for every remaining song.
EXPORT_MAX_CONSECUTIVE_FAILURES = 3

# Where temporary audio and finished ZIPs live (deleted automatically).
EXPORT_DIR = Path(
    os.getenv("EXPORT_DIR", str(Path(tempfile.gettempdir()) / "ytmp3_exports"))
)

# ---- Supabase ---------------------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")

# Public key (safe to share; row-level security protects the data). The
# backend sends it with every request, together with the user's login token
# or a job key. There is no secret key: the backend never needs one.
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")

# Keys of the jobs this backend is running, so ones cut off by closing
# YT-MP3 can be marked "interrupted" when it starts again.
JOBS_FILE = Path(os.getenv("JOBS_FILE", str(BACKEND_DIR / ".jobs.json")))

# ---- CORS -------------------------------------------------------------------

# Comma-separated list of browser origins allowed to call this API.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]


# ---- Installed app ----------------------------------------------------------

# Folder with the built frontend (`npm run build` makes `dist/`). When set, the
# backend also serves the app itself, so the whole system runs from one address
# (http://localhost:8000). The Windows start script sets it; leave it unset in
# development, where `npm run dev` serves the frontend on port 5173.
FRONTEND_DIST_DIR = os.getenv("FRONTEND_DIST_DIR", "").strip()

def supabase_is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY)