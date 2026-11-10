
import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]

# Load variables from backend/.env
load_dotenv(BACKEND_DIR / ".env")

# Beta application limits
MAX_LINKS_PER_IMPORT = 10

# Reject videos longer than 30 minutes.
MAX_VIDEO_SECONDS = int(
    os.getenv("MAX_VIDEO_SECONDS", "1800")
)

# Node.js is already installed for the Vue/Vite project.
# yt-dlp can use it as its JavaScript runtime.
JS_RUNTIME = os.getenv("JS_RUNTIME", "node")
