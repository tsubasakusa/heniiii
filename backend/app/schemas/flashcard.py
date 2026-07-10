import uuid
from datetime import datetime

from pydantic import BaseModel


class DeckCreate(BaseModel):
    title: str
    language_id: int


class DeckUpdate(BaseModel):
    title: str | None = None


class DeckSummary(BaseModel):
    id: uuid.UUID
    title: str
    language_id: int
    card_count: int
    due_count: int


class CardCreate(BaseModel):
    front_text: str
    back_text: str
    pronunciation: str | None = None


class CardUpdate(BaseModel):
    front_text: str | None = None
    back_text: str | None = None
    pronunciation: str | None = None


class CardResponse(BaseModel):
    id: uuid.UUID
    deck_id: uuid.UUID
    front_text: str
    back_text: str
    pronunciation: str | None
    familiarity: int
    next_review_at: datetime | None
    last_reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class DeckDetail(BaseModel):
    id: uuid.UUID
    title: str
    language_id: int
    cards: list[CardResponse]


class ReviewRequest(BaseModel):
    quality: int  # 0-5
