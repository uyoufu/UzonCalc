from pydantic import BaseModel


class BaseDTO(BaseModel):

    # Enable ORM mode for Pydantic models
    # This allows models to be created from ORM objects directly
    model_config = {"from_attributes": True}


class PaginationDTO(BaseDTO):
    skip: int = 0
    limit: int = 10
    sortBy: str = "id"
    descending: bool = True
