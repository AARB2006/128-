
import re
import unicodedata
from urllib.parse import parse_qs, unquote, urlsplit


MAX_URL_LENGTH = 2048

VIDEO_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{11}")

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}

SHORT_HOST = "youtu.be"

NOCOOKIE_HOSTS = {
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}

VIDEO_PATHS = {"shorts", "embed", "live", "v"}

ALLOWED_PORTS = {None, 80, 443}


class InvalidLink(ValueError):
    """Raised when a submitted URL is not a supported YouTube video link."""


def parse_video_id(raw: str) -> str:
    """Validate a YouTube URL and return its 11-character video ID."""

    text = raw.strip()

    if not text:
        raise InvalidLink("The link is empty.")

    if len(text) > MAX_URL_LENGTH:
        raise InvalidLink("The link is too long.")

    # Reject spaces, control characters, and hidden Unicode characters.
    if any(
        char.isspace()
        or unicodedata.category(char) in {"Cc", "Cf"}
        for char in text
    ):
        raise InvalidLink(
            "The link contains spaces or hidden characters."
        )

    # Allow users to paste links without explicitly including https://.
    if "://" not in text:
        text = "https://" + text

    try:
        parts = urlsplit(text)
        host = (parts.hostname or "").lower().rstrip(".")
        port = parts.port
    except ValueError:
        raise InvalidLink("The URL is malformed.") from None

    if parts.scheme.lower() not in {"http", "https"}:
        raise InvalidLink("Only HTTP and HTTPS links are accepted.")

    if parts.username is not None or parts.password is not None:
        raise InvalidLink("Links containing embedded credentials are not accepted.")

    if port not in ALLOWED_PORTS:
        raise InvalidLink("The URL uses an unsupported port.")

    if not host or not host.isascii():
        raise InvalidLink("The URL has an invalid hostname.")

    # Split the path into its individual segments.
    segments = [
        unquote(segment)
        for segment in parts.path.split("/")
        if segment
    ]

    video_id = None

    # Short links: https://youtu.be/VIDEO_ID
    if host == SHORT_HOST:
        if len(segments) != 1:
            raise InvalidLink("The short link has no valid video ID.")

        video_id = segments[0]

    # Privacy-enhanced embed links.
    elif host in NOCOOKIE_HOSTS:
        if len(segments) != 2 or segments[0] != "embed":
            raise InvalidLink("Unsupported YouTube embed URL.")

        video_id = segments[1]

    # Standard YouTube domains.
    elif host in YOUTUBE_HOSTS:

        # Standard watch URL.
        if parts.path == "/watch":
            values = set(
                parse_qs(
                    parts.query,
                    keep_blank_values=True
                ).get("v", [])
            )

            if not values:
                raise InvalidLink("The link is missing its video ID.")

            if len(values) > 1:
                raise InvalidLink("The link contains multiple video IDs.")

            video_id = values.pop()

        # Shorts, embed, live, and legacy /v/ URLs.
        elif segments and segments[0] in VIDEO_PATHS:
            if len(segments) != 2:
                raise InvalidLink("The YouTube video URL is malformed.")

            video_id = segments[1]

        else:
            raise InvalidLink(
                "This is not a supported single-video YouTube link."
            )

    elif host.endswith(".youtube.com") or host.endswith(".youtu.be"):
        raise InvalidLink("Only standard YouTube domains are accepted.")

    else:
        raise InvalidLink("This is not a YouTube link.")

    # Every YouTube video ID must contain exactly 11 valid characters.
    if not VIDEO_ID_PATTERN.fullmatch(video_id or ""):
        raise InvalidLink(
            "The video ID is malformed. It must contain 11 letters, "
            "numbers, hyphens, or underscores."
        )

    return video_id


def watch_url(video_id: str) -> str:
    """Build a canonical YouTube watch URL from a validated video ID."""

    if not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise InvalidLink("Cannot create a URL from an invalid video ID.")

    return f"https://www.youtube.com/watch?v={video_id}"
