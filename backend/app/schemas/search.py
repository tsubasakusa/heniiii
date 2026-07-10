from pydantic import BaseModel


class SearchResult(BaseModel):
    type: str  # lesson | vocabulary | article
    id: str
    title: str
    subtitle: str
    language_id: int | None = None
    slug: str | None = None  # articles link by slug; lessons by id


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResult]
