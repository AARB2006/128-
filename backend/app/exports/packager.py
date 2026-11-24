"""FilePackager: put the finished MP3s into one ZIP, or nothing at all."""

import os
import zipfile
from pathlib import Path


class PackagingError(Exception):
    pass


def build_zip(files: list[Path], zip_path: Path) -> int:
    """
    Write `files` (already in playlist order) into `zip_path` and return its size.

    The archive is written to `<name>.part` and only renamed once it has been
    checked, so an incomplete ZIP can never be offered for download.
    """
    if not files:
        raise PackagingError("There are no songs to package.")

    part_path = zip_path.with_name(zip_path.name + ".part")
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # MP3 is already compressed, so store the files as they are (like the POC).
        with zipfile.ZipFile(
            part_path, mode="w", compression=zipfile.ZIP_STORED, allowZip64=True
        ) as archive:
            for path in files:
                archive.write(path, arcname=path.name)

        with zipfile.ZipFile(part_path) as archive:
            if archive.testzip() is not None or len(archive.namelist()) != len(files):
                raise PackagingError("The ZIP archive failed its check.")

        os.replace(part_path, zip_path)

    except Exception:
        part_path.unlink(missing_ok=True)
        zip_path.unlink(missing_ok=True)
        raise

    return zip_path.stat().st_size
