import pytest
from sqlalchemy import func, select

from app.models.difficulty import DifficultyLevel
from app.models.language import Language
from app.seed import seed_languages_and_levels


@pytest.mark.asyncio
async def test_seed_creates_three_languages(db_session):
    await seed_languages_and_levels(db_session)

    result = await db_session.execute(select(func.count()).select_from(Language))
    assert result.scalar_one() == 3


@pytest.mark.asyncio
async def test_seed_creates_difficulty_levels_for_each_language(db_session):
    await seed_languages_and_levels(db_session)

    result = await db_session.execute(
        select(func.count()).select_from(DifficultyLevel)
    )
    # en: 3, ja: 5, tailo: 3
    assert result.scalar_one() == 11


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session):
    await seed_languages_and_levels(db_session)
    await seed_languages_and_levels(db_session)

    result = await db_session.execute(select(func.count()).select_from(Language))
    assert result.scalar_one() == 3

    result = await db_session.execute(
        select(func.count()).select_from(DifficultyLevel)
    )
    assert result.scalar_one() == 11
