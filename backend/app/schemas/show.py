from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime

class ShowBase(BaseModel):
    slug: str
    title: str
    section: Optional[str] = None
    categories: List[str] = []
    synopsis: Optional[str] = None
    status: str = "draft"

class ShowCreate(ShowBase):
    pass

class ShowUpdate(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = None
    section: Optional[str] = None
    categories: Optional[List[str]] = None
    synopsis: Optional[str] = None
    status: Optional[str] = None

class ShowResponse(ShowBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
