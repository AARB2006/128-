from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ImportRequest(BaseModel):
    # One entry per link. Blank entries are ignored by the importer.
    urls: list[str] = Field(min_length=1, max_length=50)


class ImportStarted(BaseModel):
    batch_id: str
    total_links: int


class ExportRequest(BaseModel):
    playlist_id: UUID
    format: Literal["zip"] = "zip"  # ZIP is the only format for now


class ExportStarted(BaseModel):
    export_id: str
    total_songs: int


class DownloadLink(BaseModel):
    # A path on this server, valid for 60 seconds: /exports/download/<token>
    path: str
