from pydantic import BaseModel, Field


class ImportRequest(BaseModel):
    # One entry per link. Blank entries are ignored by the importer.
    urls: list[str] = Field(min_length=1, max_length=50)


class ImportStarted(BaseModel):
    batch_id: str
    total_links: int