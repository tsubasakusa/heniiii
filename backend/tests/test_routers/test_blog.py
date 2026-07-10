import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models.user import User, UserRole
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


async def _make(role: UserRole, email: str) -> dict:
    async with TestSessionLocal() as db:
        user = User(email=email, display_name="U", role=role, password_hash="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id), 'role': role.value})}"}


@pytest.fixture
async def editor_auth():
    return await _make(UserRole.EDITOR, "editor@example.com")


@pytest.fixture
async def user_auth():
    return await _make(UserRole.USER, "user@example.com")


@pytest.mark.asyncio
async def test_admin_create_requires_role(client, user_auth):
    resp = await client.post("/admin/articles", headers=user_auth, json={"title": "Nope"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_generates_slug_and_publishes(client, editor_auth):
    resp = await client.post(
        "/admin/articles",
        headers=editor_auth,
        json={"title": "如何學好英文", "content": "# 內容", "status": "published", "tags": ["學習"]},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["slug"]  # auto-generated
    assert data["published_at"] is not None


@pytest.mark.asyncio
async def test_public_blog_lists_published_only(client, editor_auth):
    await client.post(
        "/admin/articles", headers=editor_auth,
        json={"title": "Published", "slug": "published-one", "status": "published"},
    )
    await client.post(
        "/admin/articles", headers=editor_auth,
        json={"title": "Draft", "slug": "draft-one", "status": "draft"},
    )
    resp = await client.get("/blog")
    slugs = [a["slug"] for a in resp.json()]
    assert "published-one" in slugs
    assert "draft-one" not in slugs


@pytest.mark.asyncio
async def test_get_by_slug_and_draft_hidden(client, editor_auth):
    await client.post(
        "/admin/articles", headers=editor_auth,
        json={"title": "Hello", "slug": "hello-world", "content": "hi", "status": "published"},
    )
    ok = await client.get("/blog/hello-world")
    assert ok.status_code == 200
    assert ok.json()["content"] == "hi"

    await client.post(
        "/admin/articles", headers=editor_auth,
        json={"title": "Secret", "slug": "secret", "status": "draft"},
    )
    assert (await client.get("/blog/secret")).status_code == 404


@pytest.mark.asyncio
async def test_duplicate_slug_gets_suffixed(client, editor_auth):
    a = await client.post(
        "/admin/articles", headers=editor_auth,
        json={"title": "Dup", "slug": "dup", "status": "published"},
    )
    b = await client.post(
        "/admin/articles", headers=editor_auth,
        json={"title": "Dup2", "slug": "dup", "status": "published"},
    )
    assert a.json()["slug"] == "dup"
    assert b.json()["slug"] != "dup"
