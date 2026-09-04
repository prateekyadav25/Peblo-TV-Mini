import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import require_admin, require_editor, get_current_user
from app.schemas.season import SeasonCreate, SeasonUpdate, SeasonResponse
from app.schemas.common import PaginatedResponse
from app.services.season_service import SeasonService
from app.models.user import User

router = APIRouter(tags=["Seasons"])

@router.get("/admin/shows/{show_id}/seasons", response_model=PaginatedResponse[SeasonResponse])
async def get_seasons(
    show_id: uuid.UUID,
    page: int = 1,
    size: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await SeasonService.get_seasons(db, show_id, page, size)

@router.post("/admin/shows/{show_id}/seasons", response_model=SeasonResponse)
async def create_season(
    show_id: uuid.UUID,
    season_in: SeasonCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await SeasonService.create_season(db, show_id, season_in)

@router.put("/admin/seasons/{season_id}", response_model=SeasonResponse)
async def update_season(
    season_id: uuid.UUID,
    season_in: SeasonUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await SeasonService.update_season(db, season_id, season_in)

@router.delete("/admin/seasons/{season_id}", status_code=204)
async def delete_season(
    season_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin) # Only admin can delete
):
    await SeasonService.delete_season(db, season_id)
