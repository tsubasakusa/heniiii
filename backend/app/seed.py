from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.language import Language
from app.models.difficulty import DifficultyLevel

LANGUAGES = [
    {"code": "en", "name_zh": "英文", "display_system": "alphabet"},
    {"code": "ja", "name_zh": "日文", "display_system": "kana_kanji"},
    {"code": "tailo", "name_zh": "台語", "display_system": "tailo_hanzi"},
]

DIFFICULTY_LEVELS = {
    "en": [
        {"slug": "beginner", "label_zh": "初級", "sort_order": 1},
        {"slug": "intermediate", "label_zh": "中級", "sort_order": 2},
        {"slug": "advanced", "label_zh": "高級", "sort_order": 3},
    ],
    "ja": [
        {"slug": "n5", "label_zh": "N5", "sort_order": 1},
        {"slug": "n4", "label_zh": "N4", "sort_order": 2},
        {"slug": "n3", "label_zh": "N3", "sort_order": 3},
        {"slug": "n2", "label_zh": "N2", "sort_order": 4},
        {"slug": "n1", "label_zh": "N1", "sort_order": 5},
    ],
    "tailo": [
        {"slug": "basic", "label_zh": "基礎", "sort_order": 1},
        {"slug": "intermediate", "label_zh": "進階", "sort_order": 2},
        {"slug": "advanced", "label_zh": "高級", "sort_order": 3},
    ],
}


async def seed_languages_and_levels(db: AsyncSession) -> None:
    """Seed the 3 supported languages and their difficulty levels.

    Idempotent: skips a language (and its levels) that already exists.
    """
    for lang_data in LANGUAGES:
        result = await db.execute(
            select(Language).where(Language.code == lang_data["code"])
        )
        if result.scalar_one_or_none():
            continue

        lang = Language(**lang_data)
        db.add(lang)
        await db.flush()

        for level_data in DIFFICULTY_LEVELS[lang_data["code"]]:
            level = DifficultyLevel(language_id=lang.id, **level_data)
            db.add(level)

    await db.commit()
