from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DifficultyLevel(Base):
    __tablename__ = "difficulty_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    slug: Mapped[str] = mapped_column(String(50))
    label_zh: Mapped[str] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(default=0)
