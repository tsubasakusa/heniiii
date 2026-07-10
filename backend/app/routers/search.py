from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.search import SearchResponse, SearchResult
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])
service = SearchService()


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query("", description="搜尋關鍵字"),
    lang: str | None = Query(None, description="語言代碼 en/ja/tailo"),
    type: str | None = Query(None, description="lesson / vocabulary / article"),
    db: AsyncSession = Depends(get_db),
):
    results = await service.search(db, q, lang, type)
    return SearchResponse(
        query=q.strip(),
        total=len(results),
        results=[SearchResult(**r) for r in results],
    )
