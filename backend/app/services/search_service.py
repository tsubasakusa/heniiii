from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus
from app.models.language import Language
from app.models.lesson import Lesson, LessonStatus
from app.models.vocabulary import Vocabulary

PER_TYPE_LIMIT = 20


class SearchService:
    """Cross-content search over lessons, vocabulary and articles.

    Uses case-insensitive substring matching (ILIKE) so it works identically on
    PostgreSQL and the SQLite test database. For Tailo, matching both the word
    and its pronunciation covers hanzi and romanization. A PostgreSQL tsvector
    index is a future optimization.
    """

    async def _lang_id(self, db: AsyncSession, code: str | None) -> int | None:
        if not code:
            return None
        lang = await db.scalar(select(Language).where(Language.code == code))
        return lang.id if lang else -1  # -1 => unknown code, matches nothing

    async def search(
        self,
        db: AsyncSession,
        query: str,
        lang: str | None = None,
        content_type: str | None = None,
    ) -> list[dict]:
        query = (query or "").strip()
        if not query:
            return []

        pattern = f"%{query}%"
        lang_id = await self._lang_id(db, lang)
        results: list[dict] = []

        want = lambda t: content_type in (None, "", t)  # noqa: E731

        if want("lesson"):
            stmt = select(Lesson).where(
                Lesson.status == LessonStatus.PUBLISHED,
                Lesson.title.ilike(pattern),
            )
            if lang_id is not None:
                stmt = stmt.where(Lesson.language_id == lang_id)
            for lesson in (await db.execute(stmt.limit(PER_TYPE_LIMIT))).scalars():
                results.append(
                    {
                        "type": "lesson",
                        "id": str(lesson.id),
                        "title": lesson.title,
                        "subtitle": "課程",
                        "language_id": lesson.language_id,
                        "slug": None,
                    }
                )

        if want("vocabulary"):
            stmt = select(Vocabulary).where(
                or_(
                    Vocabulary.word.ilike(pattern),
                    Vocabulary.pronunciation.ilike(pattern),
                    Vocabulary.meaning_zh.ilike(pattern),
                )
            )
            if lang_id is not None:
                stmt = stmt.where(Vocabulary.language_id == lang_id)
            for v in (await db.execute(stmt.limit(PER_TYPE_LIMIT))).scalars():
                results.append(
                    {
                        "type": "vocabulary",
                        "id": str(v.id),
                        "title": v.word,
                        "subtitle": f"{v.pronunciation} · {v.meaning_zh}",
                        "language_id": v.language_id,
                        "slug": None,
                    }
                )

        if want("article"):
            stmt = select(Article).where(
                Article.status == ArticleStatus.PUBLISHED,
                or_(Article.title.ilike(pattern), Article.content.ilike(pattern)),
            )
            if lang_id is not None:
                stmt = stmt.where(Article.language_id == lang_id)
            for a in (await db.execute(stmt.limit(PER_TYPE_LIMIT))).scalars():
                results.append(
                    {
                        "type": "article",
                        "id": str(a.id),
                        "title": a.title,
                        "subtitle": (a.content or "")[:60].replace("\n", " "),
                        "language_id": a.language_id,
                        "slug": a.slug,
                    }
                )

        return results
