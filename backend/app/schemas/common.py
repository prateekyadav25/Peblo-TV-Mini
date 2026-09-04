from typing import Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
