import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models.user import User, UserRole
from app.seed import seed_languages_and_levels
from app.utils.security import create_access_token
from tests.conftest import TestSessionLocal


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


async def _auth(role: UserRole, email: str) -> dict:
    async with TestSessionLocal() as db:
        await seed_languages_and_levels(db)
        user = User(email=email, display_name="U", role=role, password_hash="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id), 'role': role.value})}"}


@pytest.mark.asyncio
async def test_dashboard_requires_editor(client):
    user = await _auth(UserRole.USER, "u@example.com")
    assert (await client.get("/admin/dashboard", headers=user)).status_code == 403


@pytest.mark.asyncio
async def test_dashboard_returns_stats(client):
    editor = await _auth(UserRole.EDITOR, "e@example.com")
    resp = await client.get("/admin/dashboard", headers=editor)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] >= 1
    assert data["new_users_today"] >= 1
    # three seeded languages appear in the distribution
    assert len(data["language_distribution"]) == 3
    assert {"total_lessons", "total_decks", "crossword_submissions_today"} <= data.keys()


@pytest.mark.asyncio
async def test_users_list_admin_only(client):
    editor = await _auth(UserRole.EDITOR, "e2@example.com")
    assert (await client.get("/admin/users", headers=editor)).status_code == 403

    admin = await _auth(UserRole.ADMIN, "admin@example.com")
    resp = await client.get("/admin/users", headers=admin)
    assert resp.status_code == 200
    assert any(u["email"] == "admin@example.com" for u in resp.json())
