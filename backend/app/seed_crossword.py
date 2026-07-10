"""Seed a small demo crossword for today (a CAT / ARE / TEA word square)."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crossword import CrosswordPuzzle, CrosswordStatus
from app.models.difficulty import DifficultyLevel
from app.models.language import Language

GRID_DATA = {
    "rows": 3,
    "cols": 3,
    "cells": [
        {"r": 0, "c": 0, "answer": "C", "number": 1},
        {"r": 0, "c": 1, "answer": "A", "number": 2},
        {"r": 0, "c": 2, "answer": "T", "number": 3},
        {"r": 1, "c": 0, "answer": "A", "number": 4},
        {"r": 1, "c": 1, "answer": "R"},
        {"r": 1, "c": 2, "answer": "E"},
        {"r": 2, "c": 0, "answer": "T", "number": 5},
        {"r": 2, "c": 1, "answer": "E"},
        {"r": 2, "c": 2, "answer": "A"},
    ],
}

CLUES = {
    "across": [
        {"number": 1, "row": 0, "col": 0, "length": 3, "clue": "貓"},
        {"number": 4, "row": 1, "col": 0, "length": 3, "clue": "be 動詞（複數/第二人稱）"},
        {"number": 5, "row": 2, "col": 0, "length": 3, "clue": "茶"},
    ],
    "down": [
        {"number": 1, "row": 0, "col": 0, "length": 3, "clue": "貓"},
        {"number": 2, "row": 0, "col": 1, "length": 3, "clue": "be 動詞（複數/第二人稱）"},
        {"number": 3, "row": 0, "col": 2, "length": 3, "clue": "茶"},
    ],
}


async def seed_demo_crossword(db: AsyncSession) -> None:
    """Publish a demo puzzle for today's date if none exists yet. Idempotent."""
    today = date.today()

    existing = await db.execute(
        select(CrosswordPuzzle).where(CrosswordPuzzle.publish_date == today)
    )
    if existing.scalar_one_or_none():
        return

    lang = (
        await db.execute(select(Language).where(Language.code == "en"))
    ).scalar_one_or_none()
    if not lang:
        return
    level = (
        await db.execute(
            select(DifficultyLevel).where(
                DifficultyLevel.language_id == lang.id,
                DifficultyLevel.slug == "beginner",
            )
        )
    ).scalar_one_or_none()
    if not level:
        return

    puzzle = CrosswordPuzzle(
        language_id=lang.id,
        difficulty_id=level.id,
        publish_date=today,
        grid_data=GRID_DATA,
        clues=CLUES,
        status=CrosswordStatus.PUBLISHED,
    )
    db.add(puzzle)
    await db.commit()
