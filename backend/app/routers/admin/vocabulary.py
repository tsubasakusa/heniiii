import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.learn import VocabularyCreate, VocabularyResponse, VocabularyUpdate
from app.services.dictionary_service import DictionaryService

router = APIRouter(prefix="/admin/vocabulary", tags=["admin:vocabulary"])
dictionary_service = DictionaryService()

require_editor = require_role(UserRole.ADMIN, UserRole.EDITOR)


@router.get("", response_model=list[VocabularyResponse])
async def list_vocabulary(
    lang: str = Query(...),
    level: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await dictionary_service.list_vocabulary(db, lang, level)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=VocabularyResponse, status_code=status.HTTP_201_CREATED)
async def create_vocabulary(
    req: VocabularyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await dictionary_service.create_vocabulary(
            db,
            language_id=req.language_id,
            difficulty_id=req.difficulty_id,
            word=req.word,
            pronunciation=req.pronunciation,
            meaning_zh=req.meaning_zh,
            example_sentence=req.example_sentence,
            audio_url=req.audio_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{vocab_id}", response_model=VocabularyResponse)
async def update_vocabulary(
    vocab_id: uuid.UUID,
    req: VocabularyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await dictionary_service.update_vocabulary(
            db, vocab_id, **req.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{vocab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vocabulary(
    vocab_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        await dictionary_service.delete_vocabulary(db, vocab_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
