import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import require_admin, require_editor, get_current_user
from app.schemas.episode import EpisodeCreate, EpisodeUpdate, EpisodeResponse
from app.schemas.common import PaginatedResponse
from app.services.episode_service import EpisodeService
from app.models.user import User

router = APIRouter(tags=["Episodes"])

@router.get("/admin/seasons/{season_id}/episodes", response_model=PaginatedResponse[EpisodeResponse])
async def get_episodes(
    season_id: uuid.UUID,
    page: int = 1,
    size: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await EpisodeService.get_episodes(db, season_id, page, size)

@router.post("/admin/seasons/{season_id}/episodes", response_model=EpisodeResponse)
async def create_episode(
    season_id: uuid.UUID,
    episode_in: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await EpisodeService.create_episode(db, season_id, episode_in)

@router.put("/admin/episodes/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: uuid.UUID,
    episode_in: EpisodeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await EpisodeService.update_episode(db, episode_id, episode_in)

@router.delete("/admin/episodes/{episode_id}", status_code=204)
async def delete_episode(
    episode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin) # Only admin can delete
):
    await EpisodeService.delete_episode(db, episode_id)
