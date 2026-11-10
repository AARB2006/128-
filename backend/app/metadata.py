
import logging
import math

import yt_dlp

from .config import MAX_VIDEO_SECONDS
from .youtube import parse_video_id, watch_url
from .ytdlp_opts import base_options


logger = logging.getLogger(__name__)


class VideoRejected(Exception):
    """Raised when a YouTube video cannot be imported."""


# Convert recognizable yt-dlp errors into understandable messages.
ERROR_HINTS = [
    (
        ("private video",),
        "The video is private."
    ),
    (
        ("members-only", "members only", "join this channel"),
        "The video is for channel members only."
    ),
    (
        ("confirm your age", "age-restricted", "age restricted"),
        "The video is age-restricted."
    ),
    (
        ("not available in your country", "blocked it in your country"),
        "The video is not available in your region."
    ),
    (
        ("video unavailable", "has been removed", "no longer available",
         "this video is not available", "does not exist"),
        "The video is unavailable or has been removed."
    ),
    (
        ("sign in to confirm", "not a bot"),
        "YouTube requires sign-in verification. Try again later."
    ),
    (
        ("timed out", "timeout", "urlopen error", "temporary failure",
         "name resolution", "connection", "ssl"),
        "Could not reach YouTube. Check your internet connection."
    ),
]


AVAILABILITY_REJECTIONS = {
    "private": "The video is private.",
    "premium_only": "The video requires YouTube Premium.",
    "subscriber_only": "The video is for channel members only.",
    "needs_auth": "The video requires signing in to watch.",
}


LIVE_REJECTIONS = {
    "is_live": "Live streams cannot be exported.",
    "is_upcoming": "This is an upcoming stream and cannot be exported yet.",
    "post_live": "This stream is still being processed. Try again later.",
}


def classify_error(message: str) -> str:
    """Convert yt-dlp error messages into user-friendly explanations."""

    lowered = (message or "").lower()

    for keywords, reason in ERROR_HINTS:
        if any(keyword in lowered for keyword in keywords):
            return reason

    return "The video could not be accessed or its metadata could not be read."


def evaluate_metadata(info: dict, expected_id: str) -> dict:
    """Validate metadata returned by yt-dlp."""

    if not isinstance(info, dict):
        raise VideoRejected("YouTube returned invalid video information.")

    if info.get("_type") not in (None, "video"):
        raise VideoRejected("The link does not point to a single video.")

    # Make sure yt-dlp returned the video we originally requested.
    if info.get("id") != expected_id:
        raise VideoRejected(
            "YouTube returned a different video than the submitted link."
        )

    title = info.get("title")

    if not isinstance(title, str) or not title.strip():
        raise VideoRejected("The video does not have a valid title.")

    # Check video availability.
    availability = info.get("availability")

    if availability in AVAILABILITY_REJECTIONS:
        raise VideoRejected(AVAILABILITY_REJECTIONS[availability])

    # Reject live streams and upcoming streams.
    live_status = info.get("live_status")

    if live_status in LIVE_REJECTIONS:
        raise VideoRejected(LIVE_REJECTIONS[live_status])

    if info.get("is_live"):
        raise VideoRejected(LIVE_REJECTIONS["is_live"])

    # Reject age-restricted videos.
    age_limit = info.get("age_limit")

    if isinstance(age_limit, int) and age_limit >= 18:
        raise VideoRejected("The video is age-restricted.")

    # Validate duration.
    duration = info.get("duration")

    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or duration <= 0
    ):
        raise VideoRejected("The video's duration is unavailable.")

    if duration > MAX_VIDEO_SECONDS:
        minutes = MAX_VIDEO_SECONDS // 60
        raise VideoRejected(
            f"The video exceeds the {minutes}-minute duration limit."
        )

    return {
        "video_id": expected_id,
        "title": title.strip()[:500],
        "duration_seconds": int(duration),
    }


def fetch_metadata(url: str) -> dict:
    """
    Retrieve metadata without downloading audio.

    Returns:
        {
            "video_id": "...",
            "title": "...",
            "duration_seconds": 123
        }

    Raises:
        InvalidLink: if the submitted URL is malformed.
        VideoRejected: if the video cannot be imported.
    """

    # Validate the URL before passing anything to yt-dlp.
    expected_id = parse_video_id(url)

    # Rebuild the URL ourselves rather than passing the raw user input.
    canonical_url = watch_url(expected_id)

    options = base_options()
    options["skip_download"] = True

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                canonical_url,
                download=False
            )

    except Exception as error:
        # Keep technical details in the server logs.
        logger.warning(
            "Metadata lookup failed for video %s: %s",
            expected_id,
            error
        )

        raise VideoRejected(
            classify_error(str(error))
        ) from error

    return evaluate_metadata(info, expected_id)
