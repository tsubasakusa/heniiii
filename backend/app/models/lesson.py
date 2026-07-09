import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# JSONB on PostgreSQL, generic JSON elsewhere (e.g. SQLite in tests).
JSONType = JSON().with_variant(JSONB(), "postgresql")


class LessonStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    difficulty_id: Mapped[int] = mapped_column(ForeignKey("difficulty_levels.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[list] = mapped_column(JSONType, default=list)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, values_callable=lambda e: [m.value for m in e]),
        default=LessonStatus.DRAFT,
        server_default="draft",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
