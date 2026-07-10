import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import get_db
from app.main import app
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
async def en_id():
    async with TestSessionLocal() as db:
        await seed_languages_and_levels(db)
        lang = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one()
        return lang.id


async def _auth(email="learner@example.com"):
    async with TestSessionLocal() as db:
        user = User(email=email, display_name="U", role=UserRole.USER, password_hash="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        token = create_access_token({"sub": str(user.id), "role": "user"})
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth():
    return await _auth()


@pytest.mark.asyncio
async def test_requires_login(client):
    assert (await client.get("/flashcards")).status_code == 401


@pytest.mark.asyncio
async def test_full_deck_flow(client, en_id, auth):
    # create deck
    deck = await client.post("/flashcards", headers=auth, json={"title": "旅遊英文", "language_id": en_id})
    assert deck.status_code == 201
    deck_id = deck.json()["id"]

    # add cards
    for front, back in [("hello", "你好"), ("thanks", "謝謝")]:
        r = await client.post(
            f"/flashcards/{deck_id}/cards",
            headers=auth,
            json={"front_text": front, "back_text": back},
        )
        assert r.status_code == 201

    # list shows counts
    decks = await client.get("/flashcards", headers=auth)
    assert decks.json()[0]["card_count"] == 2
    assert decks.json()[0]["due_count"] == 2

    # due list has both
    due = await client.get(f"/flashcards/{deck_id}/due", headers=auth)
    assert len(due.json()) == 2
    card_id = due.json()[0]["id"]

    # review one with quality 5
    rev = await client.post(f"/flashcards/cards/{card_id}/review", headers=auth, json={"quality": 5})
    assert rev.status_code == 200
    assert rev.json()["familiarity"] == 5
    assert rev.json()["next_review_at"] is not None

    # now only 1 due
    due2 = await client.get(f"/flashcards/{deck_id}/due", headers=auth)
    assert len(due2.json()) == 1


@pytest.mark.asyncio
async def test_cannot_access_others_deck(client, en_id, auth):
    deck = await client.post("/flashcards", headers=auth, json={"title": "Mine", "language_id": en_id})
    deck_id = deck.json()["id"]

    other = await _auth("intruder@example.com")
    resp = await client.get(f"/flashcards/{deck_id}", headers=other)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_deck(client, en_id, auth):
    deck = await client.post("/flashcards", headers=auth, json={"title": "Temp", "language_id": en_id})
    deck_id = deck.json()["id"]
    resp = await client.delete(f"/flashcards/{deck_id}", headers=auth)
    assert resp.status_code == 204
    assert (await client.get(f"/flashcards/{deck_id}", headers=auth)).status_code == 404
