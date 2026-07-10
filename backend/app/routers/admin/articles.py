import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.article import ArticleCreate, ArticleDetail, ArticleSummary, ArticleUpdate
from app.services.content_service import ContentService

router = APIRouter(prefix="/admin/articles", tags=["admin:articles"])
service = ContentService()

require_editor = require_role(UserRole.ADMIN, UserRole.EDITOR)


@router.get("", response_model=list[ArticleSummary])
async def list_articles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    return await service.admin_list(db)


@router.post("", response_model=ArticleDetail, status_code=status.HTTP_201_CREATED)
async def create_article(
    req: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    return await service.create_article(
        db,
        author_id=current_user.id,
        title=req.title,
        slug=req.slug,
        content=req.content,
        cover_image_url=req.cover_image_url,
        language_id=req.language_id,
        tags=req.tags,
        status=req.status,
    )


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await service.get_article(db, article_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{article_id}", response_model=ArticleDetail)
async def update_article(
    article_id: uuid.UUID,
    req: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await service.update_article(
            db, article_id, **req.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        await service.delete_article(db, article_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
