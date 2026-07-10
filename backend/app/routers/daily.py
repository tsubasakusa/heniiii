from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.crossword import CrosswordPuzzle
from app.models.user import User
from app.schemas.crossword import (
    PuzzlePlayResponse,
    PuzzleSummary,
    SubmitRequest,
    SubmitResult,
    TodayResponse,
)
from app.services.game_service import GameService
from app.utils.crossword import mask_cells

router = APIRouter(prefix="/daily", tags=["daily"])
game_service = GameService()


def to_play_response(puzzle: CrosswordPuzzle) -> PuzzlePlayResponse:
    grid = puzzle.grid_data or {}
    return PuzzlePlayResponse(
        id=puzzle.id,
        publish_date=puzzle.publish_date,
        language_id=puzzle.language_id,
        difficulty_id=puzzle.difficulty_id,
        rows=grid.get("rows", 0),
        cols=grid.get("cols", 0),
        cells=mask_cells(grid),
        clues=puzzle.clues or {"across": [], "down": []},
    )


@router.get("/today", response_model=TodayResponse)
async def today(db: AsyncSession = Depends(get_db)):
    d = date.today()
    puzzle = await game_service.get_today(db, d)
    return TodayResponse(
        date=d, puzzle=to_play_response(puzzle) if puzzle else None
    )


@router.get("/crossword/archive", response_model=list[PuzzleSummary])
async def archive(db: AsyncSession = Depends(get_db)):
    puzzles = await game_service.list_archive(db, date.today())
    return puzzles


@router.get("/crossword/{puzzle_date}", response_model=PuzzlePlayResponse)
async def crossword_by_date(puzzle_date: date, db: AsyncSession = Depends(get_db)):
    try:
        puzzle = await game_service.get_by_date(db, puzzle_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return to_play_response(puzzle)


@router.post("/crossword/submit", response_model=SubmitResult)
async def submit(
    req: SubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await game_service.submit(
            db, current_user.id, req.puzzle_id, req.answers, req.time_spent_seconds
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return result
