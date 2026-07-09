import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.learn import (
    CompleteLessonRequest,
    DifficultyLevelResponse,
    LessonDetail,
    LessonSummary,
    ProgressResponse,
    VocabularyResponse,
)
from app.services.dictionary_service import DictionaryService
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learn", tags=["learn"])
learning_service = LearningService()
dictionary_service = DictionaryService()


# --- personal / studying (login required) --- declared before /{lang}/* so the
# literal "lessons" and "progress" segments are not swallowed by {lang}. ---

@router.get("/progress", response_model=list[ProgressResponse])
async def my_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await learning_service.list_progress(db, current_user.id)


@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await learning_service.get_lesson(db, lesson_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/lessons/{lesson_id}/complete", response_model=ProgressResponse)
async def complete_lesson(
    lesson_id: uuid.UUID,
    req: CompleteLessonRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await learning_service.complete_lesson(
            db, current_user.id, lesson_id, req.score
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# --- catalogue browsing (public) ---

@router.get("/{lang}/levels", response_model=list[DifficultyLevelResponse])
async def get_levels(lang: str, db: AsyncSession = Depends(get_db)):
    try:
        return await learning_service.list_levels(db, lang)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{lang}/lessons", response_model=list[LessonSummary])
async def get_lessons(
    lang: str,
    level: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await learning_service.list_lessons(db, lang, level)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{lang}/vocabulary", response_model=list[VocabularyResponse])
async def get_vocabulary(
    lang: str,
    level: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await dictionary_service.list_vocabulary(db, lang, level)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
