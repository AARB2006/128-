from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .exporter import create_playlist_zip, ExportError

from datetime import datetime
import logging

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from .database import get_db
from .models import Playlist, Song, PlaylistSong
from .schemas import (
    ImportRequest,
    ImportResponse,
    ImportedTrack,
    SkippedTrack,
    PlaylistListResponse,
    PlaylistResponse,
    TrackResponse,
)
from .config import MAX_LINKS_PER_IMPORT
from .youtube import parse_video_id, watch_url, InvalidLink
from .metadata import fetch_metadata, VideoRejected


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YT-MP3 Family Playlist Maker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["Content-Disposition"],
)


def api_error(status_code, message, problems=None):
    raise HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "problems": problems or [],
        },
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/playlists", response_model=PlaylistListResponse)
def list_playlists(db: Session = Depends(get_db)):
    playlists = (
        db.query(Playlist)
        .options(
            joinedload(Playlist.playlist_songs)
            .joinedload(PlaylistSong.song)
        )
        .order_by(Playlist.created_at.desc(), Playlist.playlist_id.desc())
        .all()
    )

    result = []

    for playlist in playlists:
        associations = sorted(
            playlist.playlist_songs,
            key=lambda item: item.position,
        )

        tracks = [
            TrackResponse(
                song_id=item.song.song_id,
                video_id=item.song.video_id,
                title=item.song.title,
                source_url=item.song.source_url,
                duration_seconds=item.song.duration_seconds,
                position=item.position,
            )
            for item in associations
        ]

        created_at = (
            playlist.created_at.isoformat()
            if playlist.created_at
            else None
        )

        result.append(
            PlaylistResponse(
                playlist_id=playlist.playlist_id,
                name=playlist.name,
                created_at=created_at,
                track_count=len(tracks),
                tracks=tracks,
            )
        )

    return PlaylistListResponse(
        playlists=result,
        max_links_per_import=MAX_LINKS_PER_IMPORT,
    )


@app.post("/playlists", response_model=ImportResponse, status_code=201)
def import_playlist(
    request: ImportRequest,
    db: Session = Depends(get_db),
):
    # 1. Remove blank lines while preserving their original line numbers.
    entries = [
        {"line": index + 1, "url": raw.strip()}
        for index, raw in enumerate(request.urls)
        if raw.strip()
    ]

    if not entries:
        api_error(422, "Enter at least one YouTube link.")

    if len(entries) > MAX_LINKS_PER_IMPORT:
        api_error(
            422,
            f"You can import at most {MAX_LINKS_PER_IMPORT} links at a time.",
        )

    # 2. Validate every URL before making network requests.
    problems = []
    skipped = []
    unique_entries = []
    seen_ids = set()

    for entry in entries:
        try:
            video_id = parse_video_id(entry["url"])
        except InvalidLink as error:
            problems.append({
                "line": entry["line"],
                "url": entry["url"],
                "reason": str(error),
            })
            continue

        if video_id in seen_ids:
            skipped.append(
                SkippedTrack(
                    line=entry["line"],
                    url=entry["url"],
                    reason="Duplicate video in this import.",
                )
            )
            continue

        seen_ids.add(video_id)

        unique_entries.append({
            "line": entry["line"],
            "url": entry["url"],
            "video_id": video_id,
        })

    if problems:
        api_error(422, "Some submitted links are invalid.", problems)

    if not unique_entries:
        api_error(409, "There are no new videos to import.")

    # 3. Retrieve and verify metadata before touching the database.
    verified_tracks = []

    for entry in unique_entries:
        try:
            metadata = fetch_metadata(watch_url(entry["video_id"]))

            verified_tracks.append({
                **metadata,
                "source_url": watch_url(entry["video_id"]),
                "line": entry["line"],
            })

        except VideoRejected as error:
            problems.append({
                "line": entry["line"],
                "url": entry["url"],
                "reason": str(error),
            })

        except Exception:
            logger.exception(
                "Unexpected metadata error for video %s",
                entry["video_id"],
            )
            problems.append({
                "line": entry["line"],
                "url": entry["url"],
                "reason": "An unexpected error occurred while checking this video.",
            })

    if problems:
        api_error(
            422,
            "Some videos could not be verified. Nothing was imported.",
            problems,
        )

    if not verified_tracks:
        api_error(409, "There are no videos available to import.")

    # 4. Save the playlist, songs, and associations in one transaction.
    try:
        with db.begin():
            playlist = Playlist(name=request.name)
            db.add(playlist)
            db.flush()

            video_ids = [
                track["video_id"]
                for track in verified_tracks
            ]

            existing_songs = (
                db.query(Song)
                .filter(Song.video_id.in_(video_ids))
                .all()
            )

            songs_by_video_id = {
                song.video_id: song
                for song in existing_songs
            }

            for track in verified_tracks:
                video_id = track["video_id"]

                if video_id not in songs_by_video_id:
                    song = Song(
                        video_id=video_id,
                        source_url=track["source_url"],
                        title=track["title"],
                        duration_seconds=track["duration_seconds"],
                    )

                    db.add(song)
                    db.flush()

                    songs_by_video_id[video_id] = song

            added = []

            for position, track in enumerate(verified_tracks, start=1):
                song = songs_by_video_id[track["video_id"]]

                association = PlaylistSong(
                    playlist_id=playlist.playlist_id,
                    song_id=song.song_id,
                    position=position,
                )

                db.add(association)

                added.append(
                    ImportedTrack(
                        video_id=song.video_id,
                        title=song.title,
                        duration_seconds=song.duration_seconds,
                        position=position,
                    )
                )

            playlist_id = playlist.playlist_id

    except IntegrityError:
        db.rollback()
        logger.exception("Database integrity error during playlist import")
        api_error(
            409,
            "The playlist could not be saved because of a database conflict.",
        )

    return ImportResponse(
        playlist_id=playlist_id,
        name=request.name,
        track_count=len(added),
        added=added,
        skipped=skipped,
    )


@app.post("/playlists/{playlist_id}/export")
def export_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
):
    # Retrieve the playlist and its tracks.
    playlist = (
        db.query(Playlist)
        .options(
            joinedload(Playlist.playlist_songs)
            .joinedload(PlaylistSong.song)
        )
        .filter(Playlist.playlist_id == playlist_id)
        .first()
    )

    if playlist is None:
        raise HTTPException(
            status_code=404,
            detail="Playlist not found.",
        )

    associations = sorted(
        playlist.playlist_songs,
        key=lambda item: item.position,
    )

    playlist_name = playlist.name

    # Copy the necessary data before closing the database session.
    tracks = [
        {
            "video_id": item.song.video_id,
            "title": item.song.title,
            "position": item.position,
        }
        for item in associations
    ]

    # Don't keep a database connection occupied during downloads.
    db.close()

    if not tracks:
        raise HTTPException(
            status_code=409,
            detail="This playlist has no tracks to export.",
        )

    try:
        temp_dir, zip_path, zip_name = create_playlist_zip(
            playlist_name,
            tracks,
        )

    except ExportError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    except Exception:
        logger.exception("Unexpected playlist export error")

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while exporting the playlist.",
        )

    return FileResponse(
        path=zip_path,
        filename=zip_name,
        media_type="application/zip",
        background=BackgroundTask(temp_dir.cleanup),
    )

