
import logging
import zipfile

from pathlib import Path
from tempfile import TemporaryDirectory

import yt_dlp

from .names import safe_filename
from .youtube import watch_url
from .ytdlp_opts import base_options


logger = logging.getLogger(__name__)


class ExportError(Exception):
    pass


def create_playlist_zip(playlist_name: str, tracks: list[dict]):
    if not tracks:
        raise ExportError("This playlist has no tracks to export.")

    temp_dir = TemporaryDirectory(prefix="ytmp3_export_")
    work_dir = Path(temp_dir.name)

    try:
        # Calculate numbering width: 01, 02, ... 10, etc.
        width = max(2, len(str(len(tracks))))

        mp3_files = []

        for index, track in enumerate(tracks, start=1):
            video_id = track["video_id"]
            title = safe_filename(track["title"], fallback=f"track_{index}")

            output_stem = f"{index:0{width}d} - {title}"
            output_template = str(work_dir / f"{output_stem}.%(ext)s")

            url = watch_url(video_id)

            options = base_options()
            options.update({
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "noplaylist": True,
                "ignoreerrors": False,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            })

            try:
                logger.info(
                    "Exporting track %s/%s: %s",
                    index,
                    len(tracks),
                    video_id,
                )

                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])

            except Exception as error:
                logger.exception("Failed to export video %s", video_id)
                raise ExportError(
                    f"Could not download or convert track {index}: {title}"
                ) from error

            mp3_path = work_dir / f"{output_stem}.mp3"

            if not mp3_path.is_file() or mp3_path.stat().st_size == 0:
                raise ExportError(
                    f"MP3 conversion did not produce a valid file for track {index}."
                )

            mp3_files.append(mp3_path)

        # Build the ZIP archive.
        zip_name = safe_filename(playlist_name, fallback="playlist") + ".zip"
        zip_path = work_dir / zip_name

        with zipfile.ZipFile(
            zip_path,
            mode="w",
            compression=zipfile.ZIP_STORED,
        ) as archive:
            for mp3_path in mp3_files:
                archive.write(mp3_path, arcname=mp3_path.name)

        if not zip_path.is_file() or zip_path.stat().st_size == 0:
            raise ExportError("The ZIP archive could not be created.")

        return temp_dir, zip_path, zip_name

    except Exception:
        temp_dir.cleanup()
        raise
