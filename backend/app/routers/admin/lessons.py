import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.learn import LessonCreate, LessonDetail, LessonSummary, LessonUpdate
from app.services.learning_service import LearningService

router = APIRouter(prefix="/admin/lessons", tags=["admin:lessons"])
learning_service = LearningService()

require_editor = require_role(UserRole.ADMIN, UserRole.EDITOR)


@router.get("", response_model=list[LessonSummary])
async def list_lessons(
    lang: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await learning_service.admin_list_lessons(db, lang)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=LessonDetail, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    req: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    try:
        return await learning_service.create_lesson(
            db,
            language_id=req.language_id,
            difficulty_id=req.difficulty_id,
            title=req.title,
            content=req.content,
            status=req.status,
            author_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await learning_service.get_lesson(db, lesson_id, include_drafts=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{lesson_id}", response_model=LessonDetail)
async def update_lesson(
    lesson_id: uuid.UUID,
    req: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await learning_service.update_lesson(
            db, lesson_id, **req.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        await learning_service.delete_lesson(db, lesson_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
