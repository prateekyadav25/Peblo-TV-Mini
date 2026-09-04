from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime

class SeasonBase(BaseModel):
    season_number: int

class SeasonCreate(SeasonBase):
    pass

class SeasonUpdate(BaseModel):
    season_number: Optional[int] = None

class SeasonResponse(SeasonBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    show_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
