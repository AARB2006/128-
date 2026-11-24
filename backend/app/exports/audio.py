"""AudioProcessor: download one song from YouTube and convert it to MP3."""

import logging
from collections.abc import Callable
from pathlib import Path

import yt_dlp

from ..youtube import watch_url
from ..ytdlp_opts import base_options


logger = logging.getLogger(__name__)

# Share of one song's progress spent downloading; the rest is the MP3 conversion.
DOWNLOAD_SHARE = 0.85


class Cancelled(Exception):
    """The user cancelled the export while this song was being processed."""


class AudioError(Exception):
    """The song could not be downloaded or converted."""


def download_mp3(
    video_id: str,
    work_dir: Path,
    stem: str,
    on_progress: Callable[[float], None] = lambda fraction: None,
    should_cancel: Callable[[], bool] = lambda: False,
) -> Path:
    """
    Download `video_id` and convert it to `<work_dir>/<stem>.mp3`.

    on_progress(fraction) is called with 0.0-1.0 for this song.
    should_cancel() is checked while downloading, so a cancel stops promptly.
    """

    def progress_hook(info):
        if should_cancel():
            raise Cancelled()

        if info.get("status") == "downloading":
            total = info.get("total_bytes") or info.get("total_bytes_estimate")
            done = info.get("downloaded_bytes") or 0
            if total:
                on_progress(min(done / total, 1.0) * DOWNLOAD_SHARE)

    def postprocessor_hook(info):
        if should_cancel():
            raise Cancelled()

        if info.get("status") == "started":
            on_progress(DOWNLOAD_SHARE)

    options = base_options()
    options.update({
        "format": "bestaudio/best",
        "outtmpl": str(work_dir / f"{stem}.%(ext)s"),
        "ignoreerrors": False,
        "noprogress": True,  # we report progress ourselves
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    })

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([watch_url(video_id)])
    except Exception as error:
        # yt-dlp may wrap our Cancelled in its own error type.
        if should_cancel():
            raise Cancelled() from error
        raise

    mp3_path = work_dir / f"{stem}.mp3"

    if not mp3_path.is_file() or mp3_path.stat().st_size == 0:
        raise AudioError("The MP3 conversion did not produce a file.")

    on_progress(1.0)
    return mp3_path
