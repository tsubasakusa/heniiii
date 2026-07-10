from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.article import ArticleDetail, ArticleSummary
from app.services.content_service import ContentService

router = APIRouter(prefix="/blog", tags=["blog"])
service = ContentService()


@router.get("", response_model=list[ArticleSummary])
async def list_articles(
    lang: int | None = Query(None),
    tag: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_published(db, lang, tag)


@router.get("/{slug}", response_model=ArticleDetail)
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    try:
        return await service.get_by_slug(db, slug)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
