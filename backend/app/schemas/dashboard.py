import uuid
from datetime import datetime

from pydantic import BaseModel


class LanguageStat(BaseModel):
    language_id: int
    name_zh: str
    learner_count: int


class RecentItem(BaseModel):
    id: uuid.UUID
    title: str
    published_at: datetime | None = None


class DashboardStats(BaseModel):
    total_users: int
    new_users_today: int
    total_lessons: int
    published_lessons: int
    total_articles: int
    published_articles: int
    total_vocabulary: int
    total_decks: int
    crossword_submissions_today: int
    language_distribution: list[LanguageStat]
    recent_lessons: list[RecentItem]
    recent_articles: list[RecentItem]


class UserRow(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
