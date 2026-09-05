from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)
    subtopic_id: int | None = None


class ChunkResult(BaseModel):
    id: int
    subtopic_id: int
    content: str
    subtopic_name: str | None = None
    similarity: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[ChunkResult]
