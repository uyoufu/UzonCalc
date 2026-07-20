"""Shared request and response DTO foundations."""

from pydantic import BaseModel, Field


class BaseDTO(BaseModel):
    """Enable Pydantic DTOs to validate ORM-backed objects."""

    # Enable ORM mode for Pydantic models
    # This allows models to be created from ORM objects directly
    model_config = {"from_attributes": True}


class PaginationDTO(BaseDTO):
    """Describe server-side table pagination and sorting.

    Attributes:
        skip: Number of matching rows to skip.
        limit: Maximum number of rows to return.
        sortBy: Public field name used for resource-specific sorting.
        descending: Whether to sort in descending order.
    """

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)
    sortBy: str = Field(default="id", min_length=1, max_length=64)
    descending: bool = True
