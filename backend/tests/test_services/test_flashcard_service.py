from datetime import datetime, timedelta, timezone

import pytest

from app.models.language import Language
from app.models.user import User
from app.services.flashcard_service import FlashcardService

service = FlashcardService()


async def _user(db, email="fc@example.com"):
    user = User(email=email, display_name="U", password_hash="x")
    db.add(user)
    lang = Language(code="en", name_zh="英文", display_system="alphabet")
    db.add(lang)
    await db.commit()
    await db.refresh(user)
    await db.refresh(lang)
    return user, lang


@pytest.mark.asyncio
async def test_deck_lifecycle_and_counts(db_session):
    user, lang = await _user(db_session)
    deck = await service.create_deck(db_session, user.id, "My Deck", lang.id)

    await service.add_card(db_session, user.id, deck.id, front_text="hello", back_text="你好")
    await service.add_card(db_session, user.id, deck.id, front_text="cat", back_text="貓")

    decks = await service.list_decks(db_session, user.id)
    assert len(decks) == 1
    assert decks[0]["card_count"] == 2
    assert decks[0]["due_count"] == 2  # new cards are due


@pytest.mark.asyncio
async def test_ownership_is_enforced(db_session):
    owner, lang = await _user(db_session)
    other = User(email="other@example.com", display_name="O", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    deck = await service.create_deck(db_session, owner.id, "Owner Deck", lang.id)
    with pytest.raises(ValueError):
        await service.get_deck_with_cards(db_session, other.id, deck.id)


@pytest.mark.asyncio
async def test_review_schedules_future_and_reduces_due(db_session):
    user, lang = await _user(db_session)
    deck = await service.create_deck(db_session, user.id, "Deck", lang.id)
    card = await service.add_card(db_session, user.id, deck.id, front_text="a", back_text="b")

    now = datetime.now(timezone.utc)
    reviewed = await service.review_card(db_session, user.id, card.id, quality=5, now=now)
    assert reviewed.familiarity == 5
    assert reviewed.repetitions == 1
    assert reviewed.interval_days == 1
    assert reviewed.next_review_at is not None

    # not due now anymore
    due_now = await service.list_due(db_session, user.id, deck.id, now=now)
    assert len(due_now) == 0
    # due again once the interval has elapsed
    due_later = await service.list_due(
        db_session, user.id, deck.id, now=now + timedelta(days=2)
    )
    assert len(due_later) == 1


@pytest.mark.asyncio
async def test_lapse_makes_card_due_next_day(db_session):
    user, lang = await _user(db_session)
    deck = await service.create_deck(db_session, user.id, "Deck", lang.id)
    card = await service.add_card(db_session, user.id, deck.id, front_text="a", back_text="b")

    now = datetime.now(timezone.utc)
    reviewed = await service.review_card(db_session, user.id, card.id, quality=1, now=now)
    assert reviewed.repetitions == 0
    due_tomorrow = await service.list_due(
        db_session, user.id, deck.id, now=now + timedelta(days=1, minutes=1)
    )
    assert len(due_tomorrow) == 1


@pytest.mark.asyncio
async def test_delete_deck_removes_cards(db_session):
    user, lang = await _user(db_session)
    deck = await service.create_deck(db_session, user.id, "Deck", lang.id)
    await service.add_card(db_session, user.id, deck.id, front_text="a", back_text="b")
    await service.delete_deck(db_session, user.id, deck.id)

    decks = await service.list_decks(db_session, user.id)
    assert decks == []
    with pytest.raises(ValueError):
        await service.get_deck_with_cards(db_session, user.id, deck.id)


@pytest.mark.asyncio
async def test_create_deck_unknown_language(db_session):
    user, _lang = await _user(db_session)
    with pytest.raises(ValueError):
        await service.create_deck(db_session, user.id, "Bad", 9999)
