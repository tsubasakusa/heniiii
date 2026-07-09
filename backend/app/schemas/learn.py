import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

LessonStatusLiteral = Literal["draft", "published"]


class DifficultyLevelResponse(BaseModel):
    id: int
    slug: str
    label_zh: str
    sort_order: int

    model_config = {"from_attributes": True}


class LessonSummary(BaseModel):
    id: uuid.UUID
    title: str
    language_id: int
    difficulty_id: int
    status: str

    model_config = {"from_attributes": True}


class LessonDetail(LessonSummary):
    content: list[dict[str, Any]]
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class LessonCreate(BaseModel):
    language_id: int
    difficulty_id: int
    title: str
    content: list[dict[str, Any]] = []
    status: LessonStatusLiteral = "draft"


class LessonUpdate(BaseModel):
    title: str | None = None
    difficulty_id: int | None = None
    content: list[dict[str, Any]] | None = None
    status: LessonStatusLiteral | None = None


class VocabularyResponse(BaseModel):
    id: uuid.UUID
    language_id: int
    difficulty_id: int
    word: str
    pronunciation: str
    meaning_zh: str
    example_sentence: str | None
    audio_url: str | None

    model_config = {"from_attributes": True}


class VocabularyCreate(BaseModel):
    language_id: int
    difficulty_id: int
    word: str
    pronunciation: str
    meaning_zh: str
    example_sentence: str | None = None
    audio_url: str | None = None


class VocabularyUpdate(BaseModel):
    difficulty_id: int | None = None
    word: str | None = None
    pronunciation: str | None = None
    meaning_zh: str | None = None
    example_sentence: str | None = None
    audio_url: str | None = None


class CompleteLessonRequest(BaseModel):
    score: int = 0


class ProgressResponse(BaseModel):
    id: uuid.UUID
    lesson_id: uuid.UUID
    language_id: int
    score: int
    completed_at: datetime | None

    model_config = {"from_attributes": True}
