from pydantic import BaseModel
from typing import TypeVar, Generic, Sequence

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    data: Sequence[T]
    total: int
    page: int
    page_size: int
    total_pages: int
