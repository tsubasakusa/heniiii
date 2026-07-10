import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crossword import (
    CrosswordPuzzle,
    CrosswordStatus,
    CrosswordSubmission,
)
from app.utils.crossword import grade, solution_map


class GameService:
    """Daily crossword: fetch published puzzles and grade submissions.

    Grading and scoring happen server-side from the stored solution — the
    client's answers are trusted, its score is not.
    """

    async def get_today(
        self, db: AsyncSession, today: date
    ) -> CrosswordPuzzle | None:
        result = await db.execute(
            select(CrosswordPuzzle).where(
                CrosswordPuzzle.publish_date == today,
                CrosswordPuzzle.status == CrosswordStatus.PUBLISHED,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_date(
        self, db: AsyncSession, d: date
    ) -> CrosswordPuzzle:
        result = await db.execute(
            select(CrosswordPuzzle).where(
                CrosswordPuzzle.publish_date == d,
                CrosswordPuzzle.status == CrosswordStatus.PUBLISHED,
            )
        )
        puzzle = result.scalar_one_or_none()
        if not puzzle:
            raise ValueError("Puzzle not found")
        return puzzle

    async def get_puzzle(
        self, db: AsyncSession, puzzle_id: uuid.UUID
    ) -> CrosswordPuzzle:
        result = await db.execute(
            select(CrosswordPuzzle).where(
                CrosswordPuzzle.id == puzzle_id,
                CrosswordPuzzle.status == CrosswordStatus.PUBLISHED,
            )
        )
        puzzle = result.scalar_one_or_none()
        if not puzzle:
            raise ValueError("Puzzle not found")
        return puzzle

    async def list_archive(
        self, db: AsyncSession, today: date
    ) -> list[CrosswordPuzzle]:
        result = await db.execute(
            select(CrosswordPuzzle)
            .where(
                CrosswordPuzzle.status == CrosswordStatus.PUBLISHED,
                CrosswordPuzzle.publish_date <= today,
            )
            .order_by(CrosswordPuzzle.publish_date.desc())
        )
        return list(result.scalars().all())

    async def submit(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        puzzle_id: uuid.UUID,
        answers: dict[str, str],
        time_spent_seconds: int,
    ) -> dict[str, Any]:
        puzzle = await self.get_puzzle(db, puzzle_id)
        result = grade(puzzle.grid_data, answers, time_spent_seconds)

        submission = CrosswordSubmission(
            puzzle_id=puzzle.id,
            user_id=user_id,
            answers=answers,
            score=result["score"],
            time_spent_seconds=max(0, time_spent_seconds),
            completed_at=datetime.now(timezone.utc) if result["is_perfect"] else None,
        )
        db.add(submission)
        await db.commit()

        # Reveal the solution only after a submission, for the results view.
        result["solution"] = solution_map(puzzle.grid_data)
        return result
