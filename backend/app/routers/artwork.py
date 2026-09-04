import uuid
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.show import Show
from app.models.episode import Episode
from app.models.artwork import Artwork
from app.models.user import User
from app.api.deps import require_editor
from app.storage import get_storage_backend
from app.services.artwork_service import ArtworkService, ArtworkValidationError

router = APIRouter(prefix="/admin/shows", tags=["Artwork"])
episode_router = APIRouter(prefix="/admin/episodes", tags=["Artwork"])

def get_artwork_service():
    storage = get_storage_backend()
    ref_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'reference.json')
    return ArtworkService(storage, ref_path)


@router.get("/{show_id}/artwork")
async def list_show_artwork(
    show_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor),
):
    result = await db.execute(select(Artwork).where(Artwork.show_id == show_id))
    return {
        "items": [
            {
                "id": str(artwork.id),
                "artwork_type": artwork.artwork_type,
                "storage_key": artwork.storage_key,
                "width": artwork.width,
                "height": artwork.height,
                "file_size": artwork.file_size,
            }
            for artwork in result.scalars().all()
        ]
    }

@router.post("/{show_id}/artwork/{artwork_type}")
async def upload_show_artwork(
    show_id: uuid.UUID,
    artwork_type: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    service: ArtworkService = Depends(get_artwork_service),
    user: User = Depends(require_editor)
):
    # Verify show exists
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
        
    try:
        artwork = await service.upload_artwork(db, show_id, show.slug, artwork_type, file)
        return {
            "id": str(artwork.id),
            "type": artwork.artwork_type,
            "url": await service.storage.get_url(artwork.storage_key)
        }
    except ArtworkValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@episode_router.post("/{episode_id}/artwork/{artwork_type}")
async def upload_episode_artwork(
    episode_id: uuid.UUID,
    artwork_type: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    service: ArtworkService = Depends(get_artwork_service),
    user: User = Depends(require_editor),
):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    try:
        artwork = await service.upload_artwork(
            db,
            None,
            None,
            artwork_type,
            file,
            episode_id=episode_id,
        )
        return {
            "id": str(artwork.id),
            "type": artwork.artwork_type,
            "url": await service.storage.get_url(artwork.storage_key),
        }
    except ArtworkValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
