import pytest
from sqlalchemy import select

from app.models.language import Language
from app.models.difficulty import DifficultyLevel


@pytest.mark.asyncio
async def test_create_language(db_session):
    lang = Language(code="en", name_zh="英文", display_system="alphabet")
    db_session.add(lang)
    await db_session.commit()

    result = await db_session.execute(select(Language).where(Language.code == "en"))
    saved = result.scalar_one()
    assert saved.name_zh == "英文"


@pytest.mark.asyncio
async def test_create_difficulty_level(db_session):
    lang = Language(code="ja", name_zh="日文", display_system="kana_kanji")
    db_session.add(lang)
    await db_session.commit()
    await db_session.refresh(lang)

    level = DifficultyLevel(
        language_id=lang.id, slug="n5", label_zh="N5", sort_order=1
    )
    db_session.add(level)
    await db_session.commit()

    result = await db_session.execute(
        select(DifficultyLevel).where(DifficultyLevel.slug == "n5")
    )
    saved = result.scalar_one()
    assert saved.label_zh == "N5"
    assert saved.language_id == lang.id
