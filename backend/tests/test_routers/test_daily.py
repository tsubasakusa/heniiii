from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import get_db
from app.main import app
from app.models.crossword import CrosswordPuzzle, CrosswordStatus
from app.models.difficulty import DifficultyLevel
from app.models.language import Language
from app.models.user import User, UserRole
from app.seed import seed_languages_and_levels
from app.utils.security import create_access_token
from tests.conftest import TestSessionLocal

GRID = {
    "rows": 1,
    "cols": 2,
    "cells": [
        {"r": 0, "c": 0, "answer": "H", "number": 1},
        {"r": 0, "c": 1, "answer": "I"},
    ],
}
CLUES = {"across": [{"number": 1, "row": 0, "col": 0, "length": 2, "clue": "嗨"}], "down": []}


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def puzzle_id():
    async with TestSessionLocal() as db:
        await seed_languages_and_levels(db)
        lang = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one()
        level = (
            await db.execute(
                select(DifficultyLevel).where(
                    DifficultyLevel.language_id == lang.id,
                    DifficultyLevel.slug == "beginner",
                )
            )
        ).scalar_one()
        puzzle = CrosswordPuzzle(
            language_id=lang.id,
            difficulty_id=level.id,
            publish_date=date.today(),
            grid_data=GRID,
            clues=CLUES,
            status=CrosswordStatus.PUBLISHED,
        )
        db.add(puzzle)
        await db.commit()
        await db.refresh(puzzle)
        return str(puzzle.id)


@pytest.fixture
async def user_auth():
    async with TestSessionLocal() as db:
        user = User(email="player@example.com", display_name="P", role=UserRole.USER, password_hash="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        token = create_access_token({"sub": str(user.id), "role": "user"})
        return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_today_masks_answers(client, puzzle_id):
    resp = await client.get("/daily/today")
    assert resp.status_code == 200
    data = resp.json()
    assert data["puzzle"] is not None
    assert data["puzzle"]["rows"] == 1 and data["puzzle"]["cols"] == 2
    # answers must not leak to the client
    for cell in data["puzzle"]["cells"]:
        assert "answer" not in cell
    assert data["puzzle"]["cells"][0]["number"] == 1


@pytest.mark.asyncio
async def test_archive_lists_published(client, puzzle_id):
    resp = await client.get("/daily/crossword/archive")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert puzzle_id in ids


@pytest.mark.asyncio
async def test_submit_requires_login(client, puzzle_id):
    resp = await client.post(
        "/daily/crossword/submit",
        json={"puzzle_id": puzzle_id, "answers": {"0,0": "H", "0,1": "I"}, "time_spent_seconds": 10},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submit_perfect_scores_with_bonus(client, puzzle_id, user_auth):
    resp = await client.post(
        "/daily/crossword/submit",
        headers=user_auth,
        json={"puzzle_id": puzzle_id, "answers": {"0,0": "h", "0,1": "I"}, "time_spent_seconds": 100},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_perfect"] is True
    assert data["base_score"] == 1000
    assert data["time_bonus"] == 500
    assert data["score"] == 1500
    assert data["solution"] == {"0,0": "H", "0,1": "I"}


@pytest.mark.asyncio
async def test_submit_partial_no_bonus(client, puzzle_id, user_auth):
    resp = await client.post(
        "/daily/crossword/submit",
        headers=user_auth,
        json={"puzzle_id": puzzle_id, "answers": {"0,0": "H", "0,1": "X"}, "time_spent_seconds": 10},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_perfect"] is False
    assert data["correct_cells"] == 1
    assert data["time_bonus"] == 0
    assert data["per_cell"] == {"0,0": True, "0,1": False}
