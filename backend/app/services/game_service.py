import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crossword import (
    CrosswordPuzzle,
    CrosswordStatus,
    CrosswordSubmission,
)
from app.models.difficulty import DifficultyLevel
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

    # ------------------------------------------------------------------ admin

    async def admin_list(self, db: AsyncSession) -> list[CrosswordPuzzle]:
        result = await db.execute(
            select(CrosswordPuzzle).order_by(CrosswordPuzzle.publish_date.desc())
        )
        return list(result.scalars().all())

    async def admin_get(
        self, db: AsyncSession, puzzle_id: uuid.UUID
    ) -> CrosswordPuzzle:
        puzzle = await db.scalar(
            select(CrosswordPuzzle).where(CrosswordPuzzle.id == puzzle_id)
        )
        if not puzzle:
            raise ValueError("Puzzle not found")
        return puzzle

    async def _validate(
        self, db: AsyncSession, language_id: int, difficulty_id: int
    ) -> None:
        level = await db.scalar(
            select(DifficultyLevel).where(DifficultyLevel.id == difficulty_id)
        )
        if not level or level.language_id != language_id:
            raise ValueError("Difficulty level does not belong to the language")

    async def _assert_date_free(
        self,
        db: AsyncSession,
        publish_date: date,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        existing = await db.scalar(
            select(CrosswordPuzzle).where(CrosswordPuzzle.publish_date == publish_date)
        )
        if existing and existing.id != exclude_id:
            raise ValueError("該日期已有題目")

    async def create_puzzle(
        self,
        db: AsyncSession,
        *,
        created_by: uuid.UUID,
        language_id: int,
        difficulty_id: int,
        publish_date: date,
        grid_data: dict[str, Any],
        clues: dict[str, Any],
        status: str,
    ) -> CrosswordPuzzle:
        await self._validate(db, language_id, difficulty_id)
        await self._assert_date_free(db, publish_date)
        puzzle = CrosswordPuzzle(
            created_by=created_by,
            language_id=language_id,
            difficulty_id=difficulty_id,
            publish_date=publish_date,
            grid_data=grid_data,
            clues=clues,
            status=CrosswordStatus(status),
        )
        db.add(puzzle)
        await db.commit()
        await db.refresh(puzzle)
        return puzzle

    async def update_puzzle(
        self, db: AsyncSession, puzzle_id: uuid.UUID, **fields: Any
    ) -> CrosswordPuzzle:
        puzzle = await self.admin_get(db, puzzle_id)
        new_diff = fields.get("difficulty_id")
        new_lang = fields.get("language_id", puzzle.language_id)
        if new_diff is not None:
            await self._validate(db, new_lang, new_diff)
        if fields.get("publish_date") is not None:
            await self._assert_date_free(
                db, fields["publish_date"], exclude_id=puzzle.id
            )
        for key, value in fields.items():
            if value is None:
                continue
            if key == "status":
                value = CrosswordStatus(value)
            setattr(puzzle, key, value)
        await db.commit()
        await db.refresh(puzzle)
        return puzzle

    async def delete_puzzle(self, db: AsyncSession, puzzle_id: uuid.UUID) -> None:
        puzzle = await self.admin_get(db, puzzle_id)
        await db.delete(puzzle)
        await db.commit()

    async def promote_scheduled(self, db: AsyncSession, today: date) -> int:
        """Publish any 'scheduled' puzzle whose date has arrived. Returns count."""
        result = await db.execute(
            update(CrosswordPuzzle)
            .where(
                CrosswordPuzzle.status == CrosswordStatus.SCHEDULED,
                CrosswordPuzzle.publish_date <= today,
            )
            .values(status=CrosswordStatus.PUBLISHED)
        )
        await db.commit()
        return result.rowcount or 0
