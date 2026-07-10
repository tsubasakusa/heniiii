import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import get_db
from app.main import app
from app.models.difficulty import DifficultyLevel
from app.models.language import Language
from app.models.lesson import Lesson, LessonStatus
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.seed import seed_languages_and_levels
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
    async with TestSessionLocal() as db:
        await seed_languages_and_levels(db)
        lang = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one()
        level = (
            await db.execute(
                select(DifficultyLevel).where(DifficultyLevel.language_id == lang.id)
            )
        ).scalars().first()
        user = User(email="a@example.com", display_name="A", password_hash="x")
        db.add(user)
        await db.flush()
        db.add(
            Lesson(
                language_id=lang.id, difficulty_id=level.id, title="Greetings apple lesson",
                content=[], author_id=user.id, status=LessonStatus.PUBLISHED,
            )
        )
        db.add(
            Vocabulary(
                language_id=lang.id, difficulty_id=level.id, word="apple",
                pronunciation="ˈæpəl", meaning_zh="蘋果",
            )
        )
        await db.commit()
        return lang.id


@pytest.mark.asyncio
async def test_empty_query_returns_nothing(client, seeded):
    resp = await client.get("/search?q=")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_matches_lesson_and_vocab(client, seeded):
    resp = await client.get("/search?q=apple")
    data = resp.json()
    types = {r["type"] for r in data["results"]}
    assert "lesson" in types
    assert "vocabulary" in types


@pytest.mark.asyncio
async def test_search_matches_chinese_meaning(client, seeded):
    resp = await client.get("/search?q=蘋果")
    assert any(r["type"] == "vocabulary" and r["title"] == "apple" for r in resp.json()["results"])


@pytest.mark.asyncio
async def test_type_filter(client, seeded):
    resp = await client.get("/search?q=apple&type=vocabulary")
    assert all(r["type"] == "vocabulary" for r in resp.json()["results"])
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_unknown_language_matches_nothing(client, seeded):
    resp = await client.get("/search?q=apple&lang=zzz")
    assert resp.json()["total"] == 0
