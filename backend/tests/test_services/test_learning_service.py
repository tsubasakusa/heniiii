import uuid

import pytest

from app.models.difficulty import DifficultyLevel
from app.models.language import Language
from app.models.user import User
from app.services.learning_service import LearningService

service = LearningService()


async def _seed(db):
    lang = Language(code="en", name_zh="英文", display_system="alphabet")
    db.add(lang)
    await db.flush()
    beginner = DifficultyLevel(
        language_id=lang.id, slug="beginner", label_zh="初級", sort_order=1
    )
    advanced = DifficultyLevel(
        language_id=lang.id, slug="advanced", label_zh="高級", sort_order=2
    )
    db.add_all([beginner, advanced])
    user = User(email="a@example.com", display_name="A", password_hash="x")
    db.add(user)
    await db.commit()
    await db.refresh(beginner)
    await db.refresh(user)
    return lang, beginner, advanced, user


@pytest.mark.asyncio
async def test_create_and_list_published_only(db_session):
    lang, beginner, _adv, user = await _seed(db_session)
    await service.create_lesson(
        db_session,
        language_id=lang.id,
        difficulty_id=beginner.id,
        title="Published",
        content=[],
        status="published",
        author_id=user.id,
    )
    await service.create_lesson(
        db_session,
        language_id=lang.id,
        difficulty_id=beginner.id,
        title="Draft",
        content=[],
        status="draft",
        author_id=user.id,
    )

    public = await service.list_lessons(db_session, "en")
    assert [lsn.title for lsn in public] == ["Published"]

    all_lessons = await service.admin_list_lessons(db_session, "en")
    assert len(all_lessons) == 2


@pytest.mark.asyncio
async def test_level_mismatch_rejected(db_session):
    lang, beginner, _adv, user = await _seed(db_session)
    # A difficulty id from a different language should be rejected.
    other = Language(code="ja", name_zh="日文", display_system="kana_kanji")
    db_session.add(other)
    await db_session.flush()
    ja_level = DifficultyLevel(
        language_id=other.id, slug="n5", label_zh="N5", sort_order=1
    )
    db_session.add(ja_level)
    await db_session.commit()
    await db_session.refresh(ja_level)

    with pytest.raises(ValueError):
        await service.create_lesson(
            db_session,
            language_id=lang.id,
            difficulty_id=ja_level.id,
            title="Bad",
            content=[],
            status="draft",
            author_id=user.id,
        )


@pytest.mark.asyncio
async def test_complete_lesson_keeps_best_score(db_session):
    lang, beginner, _adv, user = await _seed(db_session)
    lesson = await service.create_lesson(
        db_session,
        language_id=lang.id,
        difficulty_id=beginner.id,
        title="L",
        content=[],
        status="published",
        author_id=user.id,
    )

    p1 = await service.complete_lesson(db_session, user.id, lesson.id, 40)
    assert p1.score == 40
    # Lower re-score does not overwrite the best score.
    p2 = await service.complete_lesson(db_session, user.id, lesson.id, 20)
    assert p2.score == 40
    assert p2.id == p1.id  # same progress row, not a duplicate

    progress = await service.list_progress(db_session, user.id)
    assert len(progress) == 1


@pytest.mark.asyncio
async def test_cannot_complete_draft_lesson(db_session):
    lang, beginner, _adv, user = await _seed(db_session)
    draft = await service.create_lesson(
        db_session,
        language_id=lang.id,
        difficulty_id=beginner.id,
        title="Draft",
        content=[],
        status="draft",
        author_id=user.id,
    )
    with pytest.raises(ValueError):
        await service.complete_lesson(db_session, user.id, draft.id, 10)


@pytest.mark.asyncio
async def test_get_missing_lesson_raises(db_session):
    with pytest.raises(ValueError):
        await service.get_lesson(db_session, uuid.uuid4())
