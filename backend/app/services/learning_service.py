import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.difficulty import DifficultyLevel
from app.models.language import Language
from app.models.lesson import Lesson, LessonStatus
from app.models.progress import UserProgress


class LearningService:
    """Lessons and per-user learning progress.

    HTTP-agnostic so the same methods can back both the FastAPI routers and a
    future MCP `learning_service` tool handler.
    """

    async def _get_language(self, db: AsyncSession, code: str) -> Language:
        result = await db.execute(select(Language).where(Language.code == code))
        lang = result.scalar_one_or_none()
        if not lang:
            raise ValueError("Language not found")
        return lang

    async def _resolve_level(
        self, db: AsyncSession, language_id: int, slug: str
    ) -> DifficultyLevel:
        result = await db.execute(
            select(DifficultyLevel).where(
                DifficultyLevel.language_id == language_id,
                DifficultyLevel.slug == slug,
            )
        )
        level = result.scalar_one_or_none()
        if not level:
            raise ValueError("Level not found")
        return level

    async def list_levels(self, db: AsyncSession, code: str) -> list[DifficultyLevel]:
        lang = await self._get_language(db, code)
        result = await db.execute(
            select(DifficultyLevel)
            .where(DifficultyLevel.language_id == lang.id)
            .order_by(DifficultyLevel.sort_order)
        )
        return list(result.scalars().all())

    async def list_lessons(
        self,
        db: AsyncSession,
        code: str,
        level_slug: str | None = None,
        include_drafts: bool = False,
    ) -> list[Lesson]:
        lang = await self._get_language(db, code)
        stmt = select(Lesson).where(Lesson.language_id == lang.id)
        if not include_drafts:
            stmt = stmt.where(Lesson.status == LessonStatus.PUBLISHED)
        if level_slug:
            level = await self._resolve_level(db, lang.id, level_slug)
            stmt = stmt.where(Lesson.difficulty_id == level.id)
        stmt = stmt.order_by(Lesson.created_at)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_lesson(
        self, db: AsyncSession, lesson_id: uuid.UUID, include_drafts: bool = False
    ) -> Lesson:
        result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
        lesson = result.scalar_one_or_none()
        if not lesson or (
            lesson.status != LessonStatus.PUBLISHED and not include_drafts
        ):
            raise ValueError("Lesson not found")
        return lesson

    async def complete_lesson(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        score: int,
    ) -> UserProgress:
        lesson = await self.get_lesson(db, lesson_id)  # published only
        result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id,
            )
        )
        progress = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if progress:
            # Keep the best score; refresh the completion timestamp.
            progress.score = max(progress.score, score)
            progress.completed_at = now
        else:
            progress = UserProgress(
                user_id=user_id,
                language_id=lesson.language_id,
                lesson_id=lesson_id,
                score=score,
                completed_at=now,
            )
            db.add(progress)
        await db.commit()
        await db.refresh(progress)
        return progress

    async def list_progress(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> list[UserProgress]:
        result = await db.execute(
            select(UserProgress)
            .where(UserProgress.user_id == user_id)
            .order_by(UserProgress.created_at)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------ admin

    async def admin_list_lessons(
        self, db: AsyncSession, code: str | None = None
    ) -> list[Lesson]:
        stmt = select(Lesson)
        if code:
            lang = await self._get_language(db, code)
            stmt = stmt.where(Lesson.language_id == lang.id)
        stmt = stmt.order_by(Lesson.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _validate_language_and_level(
        self, db: AsyncSession, language_id: int, difficulty_id: int
    ) -> None:
        result = await db.execute(
            select(DifficultyLevel).where(DifficultyLevel.id == difficulty_id)
        )
        level = result.scalar_one_or_none()
        if not level or level.language_id != language_id:
            raise ValueError("Difficulty level does not belong to the language")

    async def create_lesson(
        self,
        db: AsyncSession,
        *,
        language_id: int,
        difficulty_id: int,
        title: str,
        content: list[dict[str, Any]],
        status: str,
        author_id: uuid.UUID,
    ) -> Lesson:
        await self._validate_language_and_level(db, language_id, difficulty_id)
        lesson = Lesson(
            language_id=language_id,
            difficulty_id=difficulty_id,
            title=title,
            content=content,
            status=LessonStatus(status),
            author_id=author_id,
        )
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    async def update_lesson(
        self, db: AsyncSession, lesson_id: uuid.UUID, **fields: Any
    ) -> Lesson:
        lesson = await self.get_lesson(db, lesson_id, include_drafts=True)
        new_difficulty = fields.get("difficulty_id")
        if new_difficulty is not None:
            await self._validate_language_and_level(
                db, lesson.language_id, new_difficulty
            )
        for key, value in fields.items():
            if value is None:
                continue
            if key == "status":
                value = LessonStatus(value)
            setattr(lesson, key, value)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    async def delete_lesson(self, db: AsyncSession, lesson_id: uuid.UUID) -> None:
        lesson = await self.get_lesson(db, lesson_id, include_drafts=True)
        await db.delete(lesson)
        await db.commit()
