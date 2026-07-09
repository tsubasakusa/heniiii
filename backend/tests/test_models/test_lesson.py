import pytest
from sqlalchemy import select

from app.models.difficulty import DifficultyLevel
from app.models.language import Language
from app.models.lesson import Lesson, LessonStatus
from app.models.user import User


async def _seed_refs(db):
    lang = Language(code="en", name_zh="英文", display_system="alphabet")
    db.add(lang)
    await db.flush()
    level = DifficultyLevel(
        language_id=lang.id, slug="beginner", label_zh="初級", sort_order=1
    )
    db.add(level)
    user = User(email="author@example.com", display_name="Author", password_hash="x")
    db.add(user)
    await db.flush()
    return lang, level, user


@pytest.mark.asyncio
async def test_lesson_defaults_to_draft(db_session):
    lang, level, user = await _seed_refs(db_session)
    lesson = Lesson(
        language_id=lang.id,
        difficulty_id=level.id,
        title="Lesson 1",
        content=[{"type": "text", "value": "hello"}],
        author_id=user.id,
    )
    db_session.add(lesson)
    await db_session.commit()

    result = await db_session.execute(select(Lesson).where(Lesson.title == "Lesson 1"))
    saved = result.scalar_one()
    assert saved.status == LessonStatus.DRAFT
    assert saved.content[0]["value"] == "hello"
    assert saved.created_at is not None


@pytest.mark.asyncio
async def test_lesson_content_roundtrips_json(db_session):
    lang, level, user = await _seed_refs(db_session)
    blocks = [
        {"type": "text", "value": "Introduction"},
        {"type": "vocab_list", "words": ["apple", "banana"]},
    ]
    lesson = Lesson(
        language_id=lang.id,
        difficulty_id=level.id,
        title="Rich",
        content=blocks,
        author_id=user.id,
        status=LessonStatus.PUBLISHED,
    )
    db_session.add(lesson)
    await db_session.commit()

    result = await db_session.execute(select(Lesson).where(Lesson.title == "Rich"))
    saved = result.scalar_one()
    assert saved.status == LessonStatus.PUBLISHED
    assert saved.content == blocks
