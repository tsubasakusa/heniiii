import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.difficulty import DifficultyLevel
from app.models.language import Language
from app.models.vocabulary import Vocabulary


class DictionaryService:
    """Vocabulary CRUD and lookups.

    HTTP-agnostic; designed to also back a future MCP `dictionary_service`.
    """

    async def _get_language(self, db: AsyncSession, code: str) -> Language:
        result = await db.execute(select(Language).where(Language.code == code))
        lang = result.scalar_one_or_none()
        if not lang:
            raise ValueError("Language not found")
        return lang

    async def _validate_language_and_level(
        self, db: AsyncSession, language_id: int, difficulty_id: int
    ) -> None:
        result = await db.execute(
            select(DifficultyLevel).where(DifficultyLevel.id == difficulty_id)
        )
        level = result.scalar_one_or_none()
        if not level or level.language_id != language_id:
            raise ValueError("Difficulty level does not belong to the language")

    async def list_vocabulary(
        self, db: AsyncSession, code: str, level_slug: str | None = None
    ) -> list[Vocabulary]:
        lang = await self._get_language(db, code)
        stmt = select(Vocabulary).where(Vocabulary.language_id == lang.id)
        if level_slug:
            result = await db.execute(
                select(DifficultyLevel).where(
                    DifficultyLevel.language_id == lang.id,
                    DifficultyLevel.slug == level_slug,
                )
            )
            level = result.scalar_one_or_none()
            if not level:
                raise ValueError("Level not found")
            stmt = stmt.where(Vocabulary.difficulty_id == level.id)
        stmt = stmt.order_by(Vocabulary.word)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_vocabulary(
        self, db: AsyncSession, vocab_id: uuid.UUID
    ) -> Vocabulary:
        result = await db.execute(
            select(Vocabulary).where(Vocabulary.id == vocab_id)
        )
        vocab = result.scalar_one_or_none()
        if not vocab:
            raise ValueError("Vocabulary not found")
        return vocab

    async def create_vocabulary(
        self,
        db: AsyncSession,
        *,
        language_id: int,
        difficulty_id: int,
        word: str,
        pronunciation: str,
        meaning_zh: str,
        example_sentence: str | None = None,
        audio_url: str | None = None,
    ) -> Vocabulary:
        await self._validate_language_and_level(db, language_id, difficulty_id)
        vocab = Vocabulary(
            language_id=language_id,
            difficulty_id=difficulty_id,
            word=word,
            pronunciation=pronunciation,
            meaning_zh=meaning_zh,
            example_sentence=example_sentence,
            audio_url=audio_url,
        )
        db.add(vocab)
        await db.commit()
        await db.refresh(vocab)
        return vocab

    async def update_vocabulary(
        self, db: AsyncSession, vocab_id: uuid.UUID, **fields: Any
    ) -> Vocabulary:
        vocab = await self.get_vocabulary(db, vocab_id)
        new_difficulty = fields.get("difficulty_id")
        if new_difficulty is not None:
            await self._validate_language_and_level(
                db, vocab.language_id, new_difficulty
            )
        for key, value in fields.items():
            if value is None:
                continue
            setattr(vocab, key, value)
        await db.commit()
        await db.refresh(vocab)
        return vocab

    async def delete_vocabulary(
        self, db: AsyncSession, vocab_id: uuid.UUID
    ) -> None:
        vocab = await self.get_vocabulary(db, vocab_id)
        await db.delete(vocab)
        await db.commit()
