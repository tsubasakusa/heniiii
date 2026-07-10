import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.lesson import JSONType


class CrosswordStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


class CrosswordPuzzle(Base):
    __tablename__ = "crossword_puzzles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    difficulty_id: Mapped[int] = mapped_column(ForeignKey("difficulty_levels.id"))
    publish_date: Mapped[date] = mapped_column(Date, unique=True)
    grid_data: Mapped[dict] = mapped_column(JSONType, default=dict)
    clues: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[CrosswordStatus] = mapped_column(
        Enum(CrosswordStatus, values_callable=lambda e: [m.value for m in e]),
        default=CrosswordStatus.DRAFT,
        server_default="draft",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class CrosswordSubmission(Base):
    __tablename__ = "crossword_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    puzzle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crossword_puzzles.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    answers: Mapped[dict] = mapped_column(JSONType, default=dict)
    score: Mapped[int] = mapped_column(Integer, default=0)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
