from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime

class EpisodeBase(BaseModel):
    episode_number: int
    title: str
    content_group: str
    language: str
    duration_seconds: Optional[int] = None
    status: str = "draft"

class EpisodeCreate(EpisodeBase):
    pass

class EpisodeUpdate(BaseModel):
    episode_number: Optional[int] = None
    title: Optional[str] = None
    content_group: Optional[str] = None
    language: Optional[str] = None
    duration_seconds: Optional[int] = None
    status: Optional[str] = None

class EpisodeResponse(EpisodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    season_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
