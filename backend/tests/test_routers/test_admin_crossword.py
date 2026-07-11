from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import get_db
from app.main import app
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
async def ctx():
    async with TestSessionLocal() as db:
        await seed_languages_and_levels(db)
        lang = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one()
        level = (
            await db.execute(select(DifficultyLevel).where(DifficultyLevel.language_id == lang.id))
        ).scalars().first()
        editor = User(email="ed@example.com", display_name="Ed", role=UserRole.EDITOR, password_hash="x")
        user = User(email="u@example.com", display_name="U", role=UserRole.USER, password_hash="x")
        db.add_all([editor, user])
        await db.commit()
        await db.refresh(editor)
        await db.refresh(user)
        return {
            "lang": lang.id,
            "diff": level.id,
            "editor": {"Authorization": f"Bearer {create_access_token({'sub': str(editor.id), 'role': 'editor'})}"},
            "user": {"Authorization": f"Bearer {create_access_token({'sub': str(user.id), 'role': 'user'})}"},
        }


def _payload(ctx, when: date):
    return {
        "language_id": ctx["lang"], "difficulty_id": ctx["diff"],
        "publish_date": when.isoformat(), "grid_data": GRID, "clues": CLUES,
        "status": "published",
    }


@pytest.mark.asyncio
async def test_requires_editor(client, ctx):
    resp = await client.post("/admin/crossword", headers=ctx["user"], json=_payload(ctx, date.today()))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_and_admin_get_includes_answers(client, ctx):
    resp = await client.post("/admin/crossword", headers=ctx["editor"], json=_payload(ctx, date.today()))
    assert resp.status_code == 201
    pid = resp.json()["id"]
    # admin detail keeps the answers
    got = await client.get(f"/admin/crossword/{pid}", headers=ctx["editor"])
    assert got.json()["grid_data"]["cells"][0]["answer"] == "H"


@pytest.mark.asyncio
async def test_public_today_still_masks_answers(client, ctx):
    await client.post("/admin/crossword", headers=ctx["editor"], json=_payload(ctx, date.today()))
    today = await client.get("/daily/today")
    cells = today.json()["puzzle"]["cells"]
    assert all("answer" not in c for c in cells)


@pytest.mark.asyncio
async def test_duplicate_publish_date_rejected(client, ctx):
    today = date.today()
    a = await client.post("/admin/crossword", headers=ctx["editor"], json=_payload(ctx, today))
    assert a.status_code == 201
    b = await client.post("/admin/crossword", headers=ctx["editor"], json=_payload(ctx, today))
    assert b.status_code == 400


@pytest.mark.asyncio
async def test_update_and_delete(client, ctx):
    created = await client.post(
        "/admin/crossword", headers=ctx["editor"], json=_payload(ctx, date.today() + timedelta(days=1))
    )
    pid = created.json()["id"]
    upd = await client.put(f"/admin/crossword/{pid}", headers=ctx["editor"], json={"status": "draft"})
    assert upd.json()["status"] == "draft"
    dele = await client.delete(f"/admin/crossword/{pid}", headers=ctx["editor"])
    assert dele.status_code == 204
    assert (await client.get(f"/admin/crossword/{pid}", headers=ctx["editor"])).status_code == 404
