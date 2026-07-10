import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flashcard import FlashcardDeck, FlashcardItem
from app.models.language import Language
from app.utils.sm2 import review as sm2_review


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FlashcardService:
    """User-owned flashcard decks with SM-2 review scheduling.

    Every method is scoped to the owning user; a deck/card belonging to someone
    else is reported as not found rather than leaking its existence.
    """

    async def _owned_deck(
        self, db: AsyncSession, user_id: uuid.UUID, deck_id: uuid.UUID
    ) -> FlashcardDeck:
        result = await db.execute(
            select(FlashcardDeck).where(
                FlashcardDeck.id == deck_id, FlashcardDeck.user_id == user_id
            )
        )
        deck = result.scalar_one_or_none()
        if not deck:
            raise ValueError("Deck not found")
        return deck

    async def _owned_card(
        self, db: AsyncSession, user_id: uuid.UUID, card_id: uuid.UUID
    ) -> FlashcardItem:
        result = await db.execute(
            select(FlashcardItem)
            .join(FlashcardDeck, FlashcardItem.deck_id == FlashcardDeck.id)
            .where(FlashcardItem.id == card_id, FlashcardDeck.user_id == user_id)
        )
        card = result.scalar_one_or_none()
        if not card:
            raise ValueError("Card not found")
        return card

    def _due_filter(self, now: datetime):
        return or_(
            FlashcardItem.next_review_at.is_(None),
            FlashcardItem.next_review_at <= now,
        )

    async def list_decks(
        self, db: AsyncSession, user_id: uuid.UUID, now: datetime | None = None
    ) -> list[dict[str, Any]]:
        now = now or _now()
        result = await db.execute(
            select(FlashcardDeck)
            .where(FlashcardDeck.user_id == user_id)
            .order_by(FlashcardDeck.created_at.desc())
        )
        decks = list(result.scalars().all())

        summaries = []
        for deck in decks:
            card_count = await db.scalar(
                select(func.count()).where(FlashcardItem.deck_id == deck.id)
            )
            due_count = await db.scalar(
                select(func.count()).where(
                    FlashcardItem.deck_id == deck.id, self._due_filter(now)
                )
            )
            summaries.append(
                {
                    "id": deck.id,
                    "title": deck.title,
                    "language_id": deck.language_id,
                    "card_count": card_count or 0,
                    "due_count": due_count or 0,
                }
            )
        return summaries

    async def create_deck(
        self, db: AsyncSession, user_id: uuid.UUID, title: str, language_id: int
    ) -> FlashcardDeck:
        lang = await db.scalar(select(Language).where(Language.id == language_id))
        if not lang:
            raise ValueError("Language not found")
        deck = FlashcardDeck(user_id=user_id, title=title, language_id=language_id)
        db.add(deck)
        await db.commit()
        await db.refresh(deck)
        return deck

    async def get_deck_with_cards(
        self, db: AsyncSession, user_id: uuid.UUID, deck_id: uuid.UUID
    ) -> tuple[FlashcardDeck, list[FlashcardItem]]:
        deck = await self._owned_deck(db, user_id, deck_id)
        result = await db.execute(
            select(FlashcardItem)
            .where(FlashcardItem.deck_id == deck.id)
            .order_by(FlashcardItem.created_at)
        )
        return deck, list(result.scalars().all())

    async def update_deck(
        self, db: AsyncSession, user_id: uuid.UUID, deck_id: uuid.UUID, **fields: Any
    ) -> FlashcardDeck:
        deck = await self._owned_deck(db, user_id, deck_id)
        for key, value in fields.items():
            if value is not None:
                setattr(deck, key, value)
        await db.commit()
        await db.refresh(deck)
        return deck

    async def delete_deck(
        self, db: AsyncSession, user_id: uuid.UUID, deck_id: uuid.UUID
    ) -> None:
        deck = await self._owned_deck(db, user_id, deck_id)
        await db.execute(delete(FlashcardItem).where(FlashcardItem.deck_id == deck.id))
        await db.delete(deck)
        await db.commit()

    async def add_card(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        deck_id: uuid.UUID,
        *,
        front_text: str,
        back_text: str,
        pronunciation: str | None = None,
    ) -> FlashcardItem:
        deck = await self._owned_deck(db, user_id, deck_id)
        card = FlashcardItem(
            deck_id=deck.id,
            front_text=front_text,
            back_text=back_text,
            pronunciation=pronunciation,
        )
        db.add(card)
        await db.commit()
        await db.refresh(card)
        return card

    async def update_card(
        self, db: AsyncSession, user_id: uuid.UUID, card_id: uuid.UUID, **fields: Any
    ) -> FlashcardItem:
        card = await self._owned_card(db, user_id, card_id)
        for key, value in fields.items():
            if value is not None:
                setattr(card, key, value)
        await db.commit()
        await db.refresh(card)
        return card

    async def delete_card(
        self, db: AsyncSession, user_id: uuid.UUID, card_id: uuid.UUID
    ) -> None:
        card = await self._owned_card(db, user_id, card_id)
        await db.delete(card)
        await db.commit()

    async def list_due(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        deck_id: uuid.UUID,
        now: datetime | None = None,
    ) -> list[FlashcardItem]:
        now = now or _now()
        deck = await self._owned_deck(db, user_id, deck_id)
        result = await db.execute(
            select(FlashcardItem)
            .where(FlashcardItem.deck_id == deck.id, self._due_filter(now))
            .order_by(FlashcardItem.next_review_at.nulls_first())
        )
        return list(result.scalars().all())

    async def review_card(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        card_id: uuid.UUID,
        quality: int,
        now: datetime | None = None,
    ) -> FlashcardItem:
        now = now or _now()
        card = await self._owned_card(db, user_id, card_id)

        schedule = sm2_review(
            card.ease_factor, card.interval_days, card.repetitions, quality
        )
        card.ease_factor = schedule.ease_factor
        card.interval_days = schedule.interval_days
        card.repetitions = schedule.repetitions
        card.familiarity = max(0, min(5, quality))
        card.last_reviewed_at = now
        card.next_review_at = now + timedelta(days=schedule.interval_days)

        await db.commit()
        await db.refresh(card)
        return card
