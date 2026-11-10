
from pydantic import BaseModel, Field, field_validator


class ImportRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    urls: list[str] = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Playlist name cannot be empty.")

        return value


class TrackResponse(BaseModel):
    song_id: int
    video_id: str
    title: str
    source_url: str
    duration_seconds: int | None
    position: int


class PlaylistResponse(BaseModel):
    playlist_id: int
    name: str
    created_at: str | None
    track_count: int
    tracks: list[TrackResponse]


class PlaylistListResponse(BaseModel):
    playlists: list[PlaylistResponse]
    max_links_per_import: int


class ImportedTrack(BaseModel):
    video_id: str
    title: str
    duration_seconds: int
    position: int


class SkippedTrack(BaseModel):
    line: int
    url: str
    reason: str


class ImportResponse(BaseModel):
    playlist_id: int
    name: str
    track_count: int
    added: list[ImportedTrack]
    skipped: list[SkippedTrack]
