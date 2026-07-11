import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.crossword import (
    PuzzleAdminCreate,
    PuzzleAdminDetail,
    PuzzleAdminSummary,
    PuzzleAdminUpdate,
)
from app.services.game_service import GameService

router = APIRouter(prefix="/admin/crossword", tags=["admin:crossword"])
service = GameService()

require_editor = require_role(UserRole.ADMIN, UserRole.EDITOR)


@router.get("", response_model=list[PuzzleAdminSummary])
async def list_puzzles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    return await service.admin_list(db)


@router.post("/promote")
async def promote_scheduled(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Force-publish any scheduled puzzle whose date has arrived (also runs hourly)."""
    promoted = await service.promote_scheduled(db, date.today())
    return {"promoted": promoted}


@router.post("", response_model=PuzzleAdminDetail, status_code=status.HTTP_201_CREATED)
async def create_puzzle(
    req: PuzzleAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    try:
        return await service.create_puzzle(
            db,
            created_by=current_user.id,
            language_id=req.language_id,
            difficulty_id=req.difficulty_id,
            publish_date=req.publish_date,
            grid_data=req.grid_data,
            clues=req.clues,
            status=req.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{puzzle_id}", response_model=PuzzleAdminDetail)
async def get_puzzle(
    puzzle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await service.admin_get(db, puzzle_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{puzzle_id}", response_model=PuzzleAdminDetail)
async def update_puzzle(
    puzzle_id: uuid.UUID,
    req: PuzzleAdminUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        return await service.update_puzzle(
            db, puzzle_id, **req.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{puzzle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_puzzle(
    puzzle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        await service.delete_puzzle(db, puzzle_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
