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
async def seeded():
    """Seed languages/levels; return the 'en' language id and its beginner level id."""
    async with TestSessionLocal() as db:
        await seed_languages_and_levels(db)
        lang = (
            await db.execute(select(Language).where(Language.code == "en"))
        ).scalar_one()
        level = (
            await db.execute(
                select(DifficultyLevel).where(
                    DifficultyLevel.language_id == lang.id,
                    DifficultyLevel.slug == "beginner",
                )
            )
        ).scalar_one()
        return {"language_id": lang.id, "difficulty_id": level.id}


async def _make_user(role: UserRole, email: str) -> tuple[str, str]:
    async with TestSessionLocal() as db:
        user = User(
            email=email, display_name="U", role=role, password_hash="x"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        token = create_access_token({"sub": str(user.id), "role": role.value})
        return str(user.id), token


@pytest.fixture
async def editor_auth():
    _id, token = await _make_user(UserRole.EDITOR, "editor@example.com")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user_auth():
    _id, token = await _make_user(UserRole.USER, "learner@example.com")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_languages_public(client, seeded):
    resp = await client.get("/learn/languages")
    assert resp.status_code == 200
    codes = {lang["code"] for lang in resp.json()}
    assert codes == {"en", "ja", "tailo"}
    assert all("id" in lang for lang in resp.json())


@pytest.mark.asyncio
async def test_get_levels_public(client, seeded):
    resp = await client.get("/learn/en/levels")
    assert resp.status_code == 200
    slugs = [lvl["slug"] for lvl in resp.json()]
    assert slugs == ["beginner", "intermediate", "advanced"]


@pytest.mark.asyncio
async def test_unknown_language_404(client, seeded):
    resp = await client.get("/learn/xx/levels")
    assert resp.status_code == 404


async def _create_lesson(client, headers, seeded, *, title, status_val):
    return await client.post(
        "/admin/lessons",
        headers=headers,
        json={
            "language_id": seeded["language_id"],
            "difficulty_id": seeded["difficulty_id"],
            "title": title,
            "content": [{"type": "text", "value": "hi"}],
            "status": status_val,
        },
    )


@pytest.mark.asyncio
async def test_admin_create_lesson_requires_role(client, seeded, user_auth):
    resp = await _create_lesson(
        client, user_auth, seeded, title="Nope", status_val="published"
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_public_list_shows_published_only(client, seeded, editor_auth):
    pub = await _create_lesson(
        client, editor_auth, seeded, title="Published", status_val="published"
    )
    assert pub.status_code == 201
    await _create_lesson(
        client, editor_auth, seeded, title="Draft", status_val="draft"
    )

    resp = await client.get("/learn/en/lessons")
    assert resp.status_code == 200
    titles = [lsn["title"] for lsn in resp.json()]
    assert titles == ["Published"]


@pytest.mark.asyncio
async def test_lesson_detail_requires_auth(client, seeded, editor_auth):
    pub = await _create_lesson(
        client, editor_auth, seeded, title="Published", status_val="published"
    )
    lesson_id = pub.json()["id"]

    anon = await client.get(f"/learn/lessons/{lesson_id}")
    assert anon.status_code == 401

    authed = await client.get(
        f"/learn/lessons/{lesson_id}", headers=editor_auth
    )
    assert authed.status_code == 200
    assert authed.json()["content"][0]["value"] == "hi"


@pytest.mark.asyncio
async def test_complete_lesson_records_progress(client, seeded, editor_auth, user_auth):
    pub = await _create_lesson(
        client, editor_auth, seeded, title="Published", status_val="published"
    )
    lesson_id = pub.json()["id"]

    done = await client.post(
        f"/learn/lessons/{lesson_id}/complete",
        headers=user_auth,
        json={"score": 88},
    )
    assert done.status_code == 200
    assert done.json()["score"] == 88

    progress = await client.get("/learn/progress", headers=user_auth)
    assert progress.status_code == 200
    assert len(progress.json()) == 1
    assert progress.json()[0]["lesson_id"] == lesson_id
