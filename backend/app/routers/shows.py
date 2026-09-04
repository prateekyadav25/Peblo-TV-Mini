import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import require_admin, require_editor, get_current_user
from app.schemas.show import ShowCreate, ShowUpdate, ShowResponse
from app.schemas.common import PaginatedResponse
from app.services.show_service import ShowService
from app.models.user import User

router = APIRouter(prefix="/admin/shows", tags=["Shows"])

@router.get("", response_model=PaginatedResponse[ShowResponse])
async def get_shows(
    page: int = 1,
    size: int = 50,
    section: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    language: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await ShowService.get_shows(db, page, size, section, status, q, language)


@router.get("/{show_id}", response_model=ShowResponse)
async def get_show(
    show_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor),
):
    return await ShowService.get_show(db, show_id)

@router.post("", response_model=ShowResponse)
async def create_show(
    show_in: ShowCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await ShowService.create_show(db, show_in)

@router.put("/{show_id}", response_model=ShowResponse)
async def update_show(
    show_id: uuid.UUID,
    show_in: ShowUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor)
):
    return await ShowService.update_show(db, show_id, show_in)

@router.delete("/{show_id}", status_code=204)
async def delete_show(
    show_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin) # Only admin can delete
):
    await ShowService.delete_show(db, show_id)
