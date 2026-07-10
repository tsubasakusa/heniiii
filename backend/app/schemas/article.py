import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ArticleStatusLiteral = Literal["draft", "published"]


class ArticleSummary(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    language_id: int | None
    tags: list[str]
    status: str
    published_at: datetime | None

    model_config = {"from_attributes": True}


class ArticleDetail(ArticleSummary):
    content: str
    cover_image_url: str | None
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ArticleCreate(BaseModel):
    title: str
    slug: str | None = None
    content: str = ""
    cover_image_url: str | None = None
    language_id: int | None = None
    tags: list[str] = []
    status: ArticleStatusLiteral = "draft"


class ArticleUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    content: str | None = None
    cover_image_url: str | None = None
    language_id: int | None = None
    tags: list[str] | None = None
    status: ArticleStatusLiteral | None = None
