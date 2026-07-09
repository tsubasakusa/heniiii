import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    difficulty_id: Mapped[int] = mapped_column(ForeignKey("difficulty_levels.id"))
    word: Mapped[str] = mapped_column(String(200))
    pronunciation: Mapped[str] = mapped_column(String(200))
    meaning_zh: Mapped[str] = mapped_column(String(500))
    example_sentence: Mapped[str | None] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(String(500))
