from pydantic import BaseModel, Field
from typing import Optional, List

from app.db.models.user import UserStatus


class CategoryInfoReqDTO(BaseModel):
    name: str
    description: Optional[str] = None
    cover: Optional[str] = None


class CategoryInfoResDTO(CategoryInfoReqDTO):
    _id: str
    order: int
    total: int
