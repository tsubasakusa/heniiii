from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis import get_redis
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])
service = LeaderboardService()


@router.get("", response_model=LeaderboardResponse)
async def leaderboard(
    scope: str = Query("total", description="total / language / daily"),
    lang: str | None = Query(None, description="語言代碼（scope=language 時使用）"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    entries = await service.get_leaderboard(db, redis, scope, lang, limit)
    return LeaderboardResponse(
        scope=scope,
        lang=lang,
        entries=[LeaderboardEntry(**e) for e in entries],
    )
