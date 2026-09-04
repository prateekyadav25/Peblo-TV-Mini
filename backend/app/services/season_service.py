import uuid
import math
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.season import Season
from app.models.show import Show
from app.schemas.season import SeasonCreate, SeasonUpdate
from app.schemas.common import PaginatedResponse

class SeasonService:
    @staticmethod
    async def get_seasons(db: AsyncSession, show_id: uuid.UUID, page: int = 1, size: int = 50) -> PaginatedResponse[Season]:
        # verify show exists
        result = await db.execute(select(Show).where(Show.id == show_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Show not found")

        query = select(Season).where(Season.show_id == show_id)
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        seasons = result.scalars().all()
        
        pages = math.ceil(total / size) if size > 0 else 0
        return PaginatedResponse(
            items=list(seasons),
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    @staticmethod
    async def get_season(db: AsyncSession, season_id: uuid.UUID) -> Season:
        result = await db.execute(select(Season).where(Season.id == season_id))
        season = result.scalar_one_or_none()
        if not season:
            raise HTTPException(status_code=404, detail="Season not found")
        return season

    @staticmethod
    def _validate_business_rules(season_number: int):
        # Season 0 trailer constraint is more about episodes inside it, but we can enforce logic here if needed.
        # Actually, "Season 0 is reserved for trailers" means we just allow it. No specific season-level constraint other than existence.
        pass

    @staticmethod
    async def create_season(db: AsyncSession, show_id: uuid.UUID, season_in: SeasonCreate) -> Season:
        # Check show
        result = await db.execute(select(Show).where(Show.id == show_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Show not found")
            
        SeasonService._validate_business_rules(season_in.season_number)
        
        season = Season(show_id=show_id, **season_in.model_dump())
        db.add(season)
        try:
            await db.commit()
            await db.refresh(season)
            return season
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def update_season(db: AsyncSession, season_id: uuid.UUID, season_in: SeasonUpdate) -> Season:
        season = await SeasonService.get_season(db, season_id)
        
        update_data = season_in.model_dump(exclude_unset=True)
        eff_number = update_data.get("season_number", season.season_number)
        SeasonService._validate_business_rules(eff_number)
        
        for field, value in update_data.items():
            setattr(season, field, value)
            
        try:
            await db.commit()
            await db.refresh(season)
            return season
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def delete_season(db: AsyncSession, season_id: uuid.UUID) -> None:
        season = await SeasonService.get_season(db, season_id)
        await db.delete(season)
        await db.commit()
