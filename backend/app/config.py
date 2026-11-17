import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]

# Load variables from backend/.env
load_dotenv(BACKEND_DIR / ".env")

# ---- Import limits ----------------------------------------------------------

# Matches the 1-10 check on import_batches.total_links in the database.
MAX_LINKS_PER_IMPORT = 10

# Import quota. This lives in application code on purpose (not in the
# database): it is the number of links one user may submit in a rolling
# 24 hours. The default is a placeholder; set DAILY_IMPORT_LIMIT to change it.
DAILY_IMPORT_LIMIT = int(os.getenv("DAILY_IMPORT_LIMIT", "100"))

# Reject videos longer than 30 minutes.
MAX_VIDEO_SECONDS = int(os.getenv("MAX_VIDEO_SECONDS", "1800"))

# Node.js is already installed for the Vue/Vite project.
# yt-dlp can use it as its JavaScript runtime.
JS_RUNTIME = os.getenv("JS_RUNTIME", "node")

# ---- Supabase ---------------------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")

# Public key: used only to ask Supabase Auth "is this user's token valid?".
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")

# SECRET key (sb_secret_... or the legacy service_role key). It bypasses
# row-level security, so it must only ever exist in backend/.env.
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")

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


def supabase_is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY and SUPABASE_SECRET_KEY)