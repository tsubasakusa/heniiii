import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w一-鿿]+", "-", text)  # keep CJK, alnum, underscore
    text = re.sub(r"-+", "-", text).strip("-")
    return text


class ContentService:
    """Blog articles: public reads and admin authoring.

    HTTP-agnostic so the same methods can back a future MCP `content_service`
    (e.g. AI-drafted articles).
    """

    async def _unique_slug(
        self, db: AsyncSession, base: str, exclude_id: uuid.UUID | None = None
    ) -> str:
        base = base or f"article-{uuid.uuid4().hex[:8]}"
        candidate = base
        n = 1
        while True:
            result = await db.execute(select(Article).where(Article.slug == candidate))
            existing = result.scalar_one_or_none()
            if not existing or existing.id == exclude_id:
                return candidate
            n += 1
            candidate = f"{base}-{n}"

    async def list_published(
        self, db: AsyncSession, lang_id: int | None = None, tag: str | None = None
    ) -> list[Article]:
        stmt = select(Article).where(Article.status == ArticleStatus.PUBLISHED)
        if lang_id is not None:
            stmt = stmt.where(Article.language_id == lang_id)
        stmt = stmt.order_by(Article.published_at.desc().nulls_last())
        result = await db.execute(stmt)
        articles = list(result.scalars().all())
        if tag:
            articles = [a for a in articles if tag in (a.tags or [])]
        return articles

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Article:
        result = await db.execute(
            select(Article).where(
                Article.slug == slug, Article.status == ArticleStatus.PUBLISHED
            )
        )
        article = result.scalar_one_or_none()
        if not article:
            raise ValueError("Article not found")
        return article

    # ------------------------------------------------------------------ admin

    async def admin_list(self, db: AsyncSession) -> list[Article]:
        result = await db.execute(select(Article).order_by(Article.created_at.desc()))
        return list(result.scalars().all())

    async def get_article(self, db: AsyncSession, article_id: uuid.UUID) -> Article:
        result = await db.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()
        if not article:
            raise ValueError("Article not found")
        return article

    async def create_article(
        self,
        db: AsyncSession,
        *,
        author_id: uuid.UUID,
        title: str,
        slug: str | None,
        content: str,
        cover_image_url: str | None,
        language_id: int | None,
        tags: list[str],
        status: str,
    ) -> Article:
        final_slug = await self._unique_slug(db, slugify(slug or title))
        st = ArticleStatus(status)
        article = Article(
            author_id=author_id,
            title=title,
            slug=final_slug,
            content=content,
            cover_image_url=cover_image_url,
            language_id=language_id,
            tags=tags,
            status=st,
            published_at=datetime.now(timezone.utc)
            if st == ArticleStatus.PUBLISHED
            else None,
        )
        db.add(article)
        await db.commit()
        await db.refresh(article)
        return article

    async def update_article(
        self, db: AsyncSession, article_id: uuid.UUID, **fields: Any
    ) -> Article:
        article = await self.get_article(db, article_id)

        if fields.get("slug") is not None:
            article.slug = await self._unique_slug(
                db, slugify(fields.pop("slug")), exclude_id=article.id
            )

        new_status = fields.get("status")
        for key, value in fields.items():
            if value is None:
                continue
            if key == "status":
                value = ArticleStatus(value)
            setattr(article, key, value)

        # Stamp published_at the first time it goes live.
        if (
            new_status == "published"
            and article.status == ArticleStatus.PUBLISHED
            and article.published_at is None
        ):
            article.published_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(article)
        return article

    async def delete_article(self, db: AsyncSession, article_id: uuid.UUID) -> None:
        article = await self.get_article(db, article_id)
        await db.delete(article)
        await db.commit()
