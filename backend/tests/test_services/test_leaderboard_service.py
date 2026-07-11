from datetime import date

import pytest
from sqlalchemy import select

from app.models.crossword import CrosswordPuzzle, CrosswordStatus, CrosswordSubmission
from app.models.difficulty import DifficultyLevel
from app.models.flashcard import FlashcardDeck, FlashcardItem
from app.models.language import Language
from app.models.progress import UserProgress
from app.models.user import User
from app.seed import seed_languages_and_levels
from app.services.leaderboard_service import LeaderboardService

service = LeaderboardService()


async def _setup(db):
    await seed_languages_and_levels(db)
    en = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one()
    level = (
        await db.execute(select(DifficultyLevel).where(DifficultyLevel.language_id == en.id))
    ).scalars().first()

    alice = User(email="alice@example.com", display_name="Alice", password_hash="x")
    bob = User(email="bob@example.com", display_name="Bob", password_hash="x")
    db.add_all([alice, bob])
    await db.flush()

    # Alice: lesson 50 + flashcard familiarity 5 + crossword 100 = 155
    db.add(UserProgress(user_id=alice.id, language_id=en.id, lesson_id=alice.id, score=50))
    deck = FlashcardDeck(user_id=alice.id, language_id=en.id, title="d")
    db.add(deck)
    await db.flush()
    db.add(FlashcardItem(deck_id=deck.id, front_text="a", back_text="b", familiarity=5))

    puzzle = CrosswordPuzzle(
        language_id=en.id, difficulty_id=level.id, publish_date=date.today(),
        grid_data={"rows": 1, "cols": 1, "cells": []}, clues={}, status=CrosswordStatus.PUBLISHED,
    )
    db.add(puzzle)
    await db.flush()
    # two submissions for Alice on the same puzzle -> best (100) counts once
    db.add(CrosswordSubmission(puzzle_id=puzzle.id, user_id=alice.id, answers={}, score=80))
    db.add(CrosswordSubmission(puzzle_id=puzzle.id, user_id=alice.id, answers={}, score=100))

    # Bob: lesson 30 only
    db.add(UserProgress(user_id=bob.id, language_id=en.id, lesson_id=bob.id, score=30))

    await db.commit()
    return alice, bob


@pytest.mark.asyncio
async def test_total_combines_sources_and_ranks(db_session):
    alice, bob = await _setup(db_session)
    rows = await service.compute(db_session, "total")
    assert [r["display_name"] for r in rows] == ["Alice", "Bob"]
    assert rows[0]["score"] == 155  # 50 + 5 + 100 (best of 80/100)
    assert rows[1]["score"] == 30


@pytest.mark.asyncio
async def test_language_scope_filters(db_session):
    await _setup(db_session)
    rows = await service.compute(db_session, "language", "en")
    assert rows[0]["score"] == 155
    # a language with no activity is empty
    assert await service.compute(db_session, "language", "ja") == []
    # unknown language code -> empty
    assert await service.compute(db_session, "language", "zzz") == []


@pytest.mark.asyncio
async def test_daily_scope_uses_best_per_user(db_session):
    alice, _bob = await _setup(db_session)
    rows = await service.compute(db_session, "daily")
    assert len(rows) == 1
    assert rows[0]["display_name"] == "Alice"
    assert rows[0]["score"] == 100
