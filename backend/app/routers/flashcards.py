import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.flashcard import (
    CardCreate,
    CardResponse,
    CardUpdate,
    DeckCreate,
    DeckDetail,
    DeckSummary,
    DeckUpdate,
    ReviewRequest,
)
from app.services.flashcard_service import FlashcardService

router = APIRouter(prefix="/flashcards", tags=["flashcards"])
service = FlashcardService()


@router.get("", response_model=list[DeckSummary])
async def list_decks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.list_decks(db, current_user.id)


@router.post("", response_model=DeckSummary, status_code=status.HTTP_201_CREATED)
async def create_deck(
    req: DeckCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        deck = await service.create_deck(db, current_user.id, req.title, req.language_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return DeckSummary(
        id=deck.id,
        title=deck.title,
        language_id=deck.language_id,
        card_count=0,
        due_count=0,
    )


@router.get("/{deck_id}", response_model=DeckDetail)
async def get_deck(
    deck_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        deck, cards = await service.get_deck_with_cards(db, current_user.id, deck_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return DeckDetail(
        id=deck.id, title=deck.title, language_id=deck.language_id, cards=cards
    )


@router.put("/{deck_id}", response_model=DeckDetail)
async def update_deck(
    deck_id: uuid.UUID,
    req: DeckUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await service.update_deck(
            db, current_user.id, deck_id, **req.model_dump(exclude_unset=True)
        )
        deck, cards = await service.get_deck_with_cards(db, current_user.id, deck_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return DeckDetail(
        id=deck.id, title=deck.title, language_id=deck.language_id, cards=cards
    )


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    deck_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await service.delete_deck(db, current_user.id, deck_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{deck_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED
)
async def add_card(
    deck_id: uuid.UUID,
    req: CardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await service.add_card(
            db,
            current_user.id,
            deck_id,
            front_text=req.front_text,
            back_text=req.back_text,
            pronunciation=req.pronunciation,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{deck_id}/due", response_model=list[CardResponse])
async def due_cards(
    deck_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await service.list_due(db, current_user.id, deck_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: uuid.UUID,
    req: CardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await service.update_card(
            db, current_user.id, card_id, **req.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await service.delete_card(db, current_user.id, card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/cards/{card_id}/review", response_model=CardResponse)
async def review_card(
    card_id: uuid.UUID,
    req: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await service.review_card(db, current_user.id, card_id, req.quality)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
