from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus
from app.models.crossword import CrosswordSubmission
from app.models.flashcard import FlashcardDeck
from app.models.language import Language
from app.models.lesson import Lesson, LessonStatus
from app.models.progress import UserProgress
from app.models.user import User
from app.models.vocabulary import Vocabulary


def _today_start() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)


class DashboardService:
    """Aggregate statistics for the admin dashboard."""

    async def _count(self, db: AsyncSession, stmt) -> int:
        return (await db.scalar(stmt)) or 0

    async def stats(self, db: AsyncSession) -> dict[str, Any]:
        today = _today_start()

        total_users = await self._count(db, select(func.count()).select_from(User))
        new_users_today = await self._count(
            db, select(func.count()).select_from(User).where(User.created_at >= today)
        )
        total_lessons = await self._count(db, select(func.count()).select_from(Lesson))
        published_lessons = await self._count(
            db,
            select(func.count())
            .select_from(Lesson)
            .where(Lesson.status == LessonStatus.PUBLISHED),
        )
        total_articles = await self._count(db, select(func.count()).select_from(Article))
        published_articles = await self._count(
            db,
            select(func.count())
            .select_from(Article)
            .where(Article.status == ArticleStatus.PUBLISHED),
        )
        total_vocabulary = await self._count(
            db, select(func.count()).select_from(Vocabulary)
        )
        total_decks = await self._count(
            db, select(func.count()).select_from(FlashcardDeck)
        )
        crossword_submissions_today = await self._count(
            db,
            select(func.count())
            .select_from(CrosswordSubmission)
            .where(CrosswordSubmission.created_at >= today),
        )

        # learners per language (distinct users with progress)
        dist_rows = await db.execute(
            select(
                Language.id,
                Language.name_zh,
                func.count(func.distinct(UserProgress.user_id)),
            )
            .select_from(Language)
            .outerjoin(UserProgress, UserProgress.language_id == Language.id)
            .group_by(Language.id, Language.name_zh)
            .order_by(Language.id)
        )
        language_distribution = [
            {"language_id": lid, "name_zh": name, "learner_count": count or 0}
            for lid, name, count in dist_rows.all()
        ]

        recent_lessons_rows = await db.execute(
            select(Lesson)
            .where(Lesson.status == LessonStatus.PUBLISHED)
            .order_by(Lesson.created_at.desc())
            .limit(5)
        )
        recent_lessons = [
            {"id": lsn.id, "title": lsn.title, "published_at": lsn.created_at}
            for lsn in recent_lessons_rows.scalars()
        ]

        recent_articles_rows = await db.execute(
            select(Article)
            .where(Article.status == ArticleStatus.PUBLISHED)
            .order_by(Article.published_at.desc().nulls_last())
            .limit(5)
        )
        recent_articles = [
            {"id": a.id, "title": a.title, "published_at": a.published_at}
            for a in recent_articles_rows.scalars()
        ]

        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "total_lessons": total_lessons,
            "published_lessons": published_lessons,
            "total_articles": total_articles,
            "published_articles": published_articles,
            "total_vocabulary": total_vocabulary,
            "total_decks": total_decks,
            "crossword_submissions_today": crossword_submissions_today,
            "language_distribution": language_distribution,
            "recent_lessons": recent_lessons,
            "recent_articles": recent_articles,
        }

    async def list_users(self, db: AsyncSession) -> list[User]:
        result = await db.execute(
            select(User).order_by(User.created_at.desc()).limit(200)
        )
        return list(result.scalars().all())
