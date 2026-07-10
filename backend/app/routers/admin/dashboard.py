from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardStats, UserRow
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/admin", tags=["admin:dashboard"])
service = DashboardService()

require_editor = require_role(UserRole.ADMIN, UserRole.EDITOR)
require_admin = require_role(UserRole.ADMIN)


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    return await service.stats(db)


@router.get("/users", response_model=list[UserRow])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await service.list_users(db)
