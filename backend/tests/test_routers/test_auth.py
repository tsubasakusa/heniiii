import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
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


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/auth/register", json={
        "email": "reg@example.com",
        "password": "testpass123",
        "display_name": "Reg User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate(client):
    payload = {"email": "dup2@example.com", "password": "pass", "display_name": "User"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/auth/register", json={
        "email": "login2@example.com",
        "password": "mypass",
        "display_name": "User",
    })
    resp = await client.post("/auth/login", json={
        "email": "login2@example.com",
        "password": "mypass",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "wrong2@example.com",
        "password": "correct",
        "display_name": "User",
    })
    resp = await client.post("/auth/login", json={
        "email": "wrong2@example.com",
        "password": "incorrect",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client):
    reg = await client.post("/auth/register", json={
        "email": "me@example.com",
        "password": "pass123",
        "display_name": "Me User",
    })
    token = reg.json()["access_token"]

    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    # Note: in older FastAPI versions HTTPBearer raised 403 for a missing
    # Authorization header. The pinned version here (fastapi>=0.115, currently
    # 0.139.0) raises 401 "Not authenticated" instead, consistent with the
    # 401s returned elsewhere in get_current_user.
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


# NOTE: /auth/refresh and /auth/logout depend on Redis (blacklist lookups),
# which is not available in the SQLite-based test environment. They are
# intentionally left uncovered here; exercise them via docker compose with a
# live Redis instance instead.
