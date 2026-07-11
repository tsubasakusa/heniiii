import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel


class CellPlay(BaseModel):
    r: int
    c: int
    number: int | None = None


class Clue(BaseModel):
    number: int
    row: int
    col: int
    length: int
    clue: str


class Clues(BaseModel):
    across: list[Clue] = []
    down: list[Clue] = []


class PuzzlePlayResponse(BaseModel):
    """Playable puzzle view — answers are intentionally omitted (anti-cheat)."""

    id: uuid.UUID
    publish_date: date
    language_id: int
    difficulty_id: int
    rows: int
    cols: int
    cells: list[CellPlay]
    clues: Clues


class PuzzleSummary(BaseModel):
    id: uuid.UUID
    publish_date: date
    language_id: int
    difficulty_id: int


class TodayResponse(BaseModel):
    date: date
    puzzle: PuzzlePlayResponse | None


class SubmitRequest(BaseModel):
    puzzle_id: uuid.UUID
    answers: dict[str, str] = {}
    time_spent_seconds: int = 0


class SubmitResult(BaseModel):
    score: int
    base_score: int
    time_bonus: int
    correct_cells: int
    total_cells: int
    is_perfect: bool
    per_cell: dict[str, bool]
    solution: dict[str, str]


# --- admin (includes answers) ---

CrosswordStatusLiteral = Literal["draft", "scheduled", "published"]


class PuzzleAdminSummary(BaseModel):
    id: uuid.UUID
    publish_date: date
    language_id: int
    difficulty_id: int
    status: str

    model_config = {"from_attributes": True}


class PuzzleAdminDetail(PuzzleAdminSummary):
    grid_data: dict[str, Any]
    clues: dict[str, Any]


class PuzzleAdminCreate(BaseModel):
    language_id: int
    difficulty_id: int
    publish_date: date
    grid_data: dict[str, Any]
    clues: dict[str, Any]
    status: CrosswordStatusLiteral = "draft"


class PuzzleAdminUpdate(BaseModel):
    language_id: int | None = None
    difficulty_id: int | None = None
    publish_date: date | None = None
    grid_data: dict[str, Any] | None = None
    clues: dict[str, Any] | None = None
    status: CrosswordStatusLiteral | None = None
