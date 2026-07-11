import uuid
from datetime import date
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crossword import CrosswordPuzzle, CrosswordStatus, CrosswordSubmission
from app.models.flashcard import FlashcardDeck, FlashcardItem
from app.models.language import Language
from app.models.progress import UserProgress
from app.models.user import User

CACHE_TTL_SECONDS = 60


class LeaderboardService:
    """Rankings across crossword, lessons and flashcard review.

    The database is the source of truth: `compute()` aggregates points with pure
    SQL (testable on SQLite). `get_leaderboard()` caches a ranking into a Redis
    sorted set with a short TTL and serves top-N reads from it (ZREVRANGE).
    """

    # --- point sources (each returns {user_id_str: points}) ---

    async def _crossword_points(
        self, db: AsyncSession, language_id: int | None = None
    ) -> dict[str, int]:
        best = select(
            CrosswordSubmission.user_id.label("uid"),
            CrosswordSubmission.puzzle_id.label("pid"),
            func.max(CrosswordSubmission.score).label("best"),
        )
        if language_id is not None:
            best = best.join(
                CrosswordPuzzle, CrosswordPuzzle.id == CrosswordSubmission.puzzle_id
            ).where(CrosswordPuzzle.language_id == language_id)
        best = best.group_by(
            CrosswordSubmission.user_id, CrosswordSubmission.puzzle_id
        ).subquery()

        rows = await db.execute(
            select(best.c.uid, func.sum(best.c.best)).group_by(best.c.uid)
        )
        return {str(uid): int(total or 0) for uid, total in rows.all()}

    async def _lesson_points(
        self, db: AsyncSession, language_id: int | None = None
    ) -> dict[str, int]:
        stmt = select(UserProgress.user_id, func.sum(UserProgress.score))
        if language_id is not None:
            stmt = stmt.where(UserProgress.language_id == language_id)
        stmt = stmt.group_by(UserProgress.user_id)
        rows = await db.execute(stmt)
        return {str(uid): int(total or 0) for uid, total in rows.all()}

    async def _flashcard_points(
        self, db: AsyncSession, language_id: int | None = None
    ) -> dict[str, int]:
        stmt = select(
            FlashcardDeck.user_id, func.sum(FlashcardItem.familiarity)
        ).join(FlashcardItem, FlashcardItem.deck_id == FlashcardDeck.id)
        if language_id is not None:
            stmt = stmt.where(FlashcardDeck.language_id == language_id)
        stmt = stmt.group_by(FlashcardDeck.user_id)
        rows = await db.execute(stmt)
        return {str(uid): int(total or 0) for uid, total in rows.all()}

    async def _daily_points(self, db: AsyncSession, day: date) -> dict[str, int]:
        puzzle = await db.scalar(
            select(CrosswordPuzzle).where(
                CrosswordPuzzle.publish_date == day,
                CrosswordPuzzle.status == CrosswordStatus.PUBLISHED,
            )
        )
        if not puzzle:
            return {}
        rows = await db.execute(
            select(CrosswordSubmission.user_id, func.max(CrosswordSubmission.score))
            .where(CrosswordSubmission.puzzle_id == puzzle.id)
            .group_by(CrosswordSubmission.user_id)
        )
        return {str(uid): int(total or 0) for uid, total in rows.all()}

    @staticmethod
    def _merge(*dicts: dict[str, int]) -> dict[str, int]:
        out: dict[str, int] = {}
        for d in dicts:
            for k, v in d.items():
                out[k] = out.get(k, 0) + v
        return out

    async def _rank(
        self, db: AsyncSession, points: dict[str, int]
    ) -> list[dict[str, Any]]:
        ids = [uuid.UUID(k) for k, v in points.items() if v > 0]
        if not ids:
            return []
        names = {
            str(u.id): u.display_name
            for u in (
                await db.execute(select(User).where(User.id.in_(ids)))
            ).scalars()
        }
        rows = [
            {"user_id": k, "display_name": names.get(k, ""), "score": v}
            for k, v in points.items()
            if v > 0
        ]
        rows.sort(key=lambda r: r["score"], reverse=True)
        return rows

    async def compute(
        self, db: AsyncSession, scope: str, lang_code: str | None = None
    ) -> list[dict[str, Any]]:
        if scope == "daily":
            return await self._rank(db, await self._daily_points(db, date.today()))

        language_id: int | None = None
        if scope == "language":
            lang = await db.scalar(select(Language).where(Language.code == lang_code))
            if not lang:
                return []
            language_id = lang.id

        points = self._merge(
            await self._crossword_points(db, language_id),
            await self._lesson_points(db, language_id),
            await self._flashcard_points(db, language_id),
        )
        return await self._rank(db, points)

    # --- Redis sorted-set cache layer ---

    async def get_leaderboard(
        self,
        db: AsyncSession,
        redis: Redis,
        scope: str,
        lang_code: str | None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        key = f"lb:{scope}:{lang_code or 'all'}"
        names_key = f"{key}:names"

        if not await redis.exists(key):
            rows = await self.compute(db, scope, lang_code)
            if rows:
                await redis.zadd(key, {r["user_id"]: r["score"] for r in rows})
                await redis.hset(
                    names_key, mapping={r["user_id"]: r["display_name"] for r in rows}
                )
                await redis.expire(key, CACHE_TTL_SECONDS)
                await redis.expire(names_key, CACHE_TTL_SECONDS)

        top = await redis.zrevrange(key, 0, limit - 1, withscores=True)
        entries: list[dict[str, Any]] = []
        for rank, (member, score) in enumerate(top, start=1):
            uid = member.decode() if isinstance(member, bytes) else member
            name = await redis.hget(names_key, uid)
            name = name.decode() if isinstance(name, bytes) else (name or "")
            entries.append(
                {"rank": rank, "user_id": uid, "display_name": name, "score": int(score)}
            )
        return entries
