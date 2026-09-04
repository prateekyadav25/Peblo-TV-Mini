import uuid
import math
from typing import Tuple, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.show import Show
from app.models.season import Season
from app.models.episode import Episode
from app.schemas.show import ShowCreate, ShowUpdate
from app.schemas.common import PaginatedResponse

class ShowService:
    @staticmethod
    async def get_shows(
        db: AsyncSession, 
        page: int = 1, 
        size: int = 50,
        section: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        language: Optional[str] = None,
    ) -> PaginatedResponse[Show]:
        query = select(Show)
        
        if section:
            query = query.where(Show.section == section)
        if status:
            query = query.where(Show.status == status)
        if q:
            query = query.where(Show.title.ilike(f"%{q}%"))
        if language:
            query = query.join(Season, Season.show_id == Show.id).join(Episode, Episode.season_id == Season.id).where(Episode.language == language).distinct()
            
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Paginate
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        shows = result.scalars().all()
        
        pages = math.ceil(total / size) if size > 0 else 0
        return PaginatedResponse(
            items=list(shows),
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    async def get_show(db: AsyncSession, show_id: uuid.UUID) -> Show:
        result = await db.execute(select(Show).where(Show.id == show_id))
        show = result.scalar_one_or_none()
        if not show:
            raise HTTPException(status_code=404, detail="Show not found")
        return show

    @staticmethod
    def _validate_business_rules(status: str, section: Optional[str]):
        if status == 'published' and not section:
            raise HTTPException(
                status_code=400, 
                detail="A published show must have a section."
            )

    @staticmethod
    async def create_show(db: AsyncSession, show_in: ShowCreate) -> Show:
        ShowService._validate_business_rules(show_in.status, show_in.section)
        
        show = Show(**show_in.model_dump())
        db.add(show)
        try:
            await db.commit()
            await db.refresh(show)
            return show
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def update_show(db: AsyncSession, show_id: uuid.UUID, show_in: ShowUpdate) -> Show:
        show = await ShowService.get_show(db, show_id)
        
        update_data = show_in.model_dump(exclude_unset=True)
        
        # Determine effective values for validation
        eff_status = update_data.get("status", show.status)
        eff_section = update_data.get("section", show.section)
        
        ShowService._validate_business_rules(eff_status, eff_section)
        
        for field, value in update_data.items():
            setattr(show, field, value)
            
        try:
            await db.commit()
            await db.refresh(show)
            return show
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def delete_show(db: AsyncSession, show_id: uuid.UUID) -> None:
        show = await ShowService.get_show(db, show_id)
        await db.delete(show)
        await db.commit()
