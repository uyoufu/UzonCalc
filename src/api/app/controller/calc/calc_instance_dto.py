"""DTOs for saved calculation instances and their categories."""

import datetime

from pydantic import Field

from app.controller.dto_base import BaseDTO


class CalcInstanceCategoryReqDTO(BaseDTO):
    """Create or update an instance category."""

    name: str = Field(min_length=1, max_length=50)
    description: str | None = None


class CalcInstanceCategoryResDTO(CalcInstanceCategoryReqDTO):
    """Return an instance category with its derived active count."""

    categoryOid: str
    sortOrder: int
    instanceCount: int
    createdAt: datetime.datetime
    updatedAt: datetime.datetime


class CalcInstanceCreateDTO(BaseDTO):
    """Create a saved result from a persisted execution."""

    categoryOid: str
    executionId: str
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CalcInstanceUpdateDTO(BaseDTO):
    """Optimistically update saved-instance display metadata."""

    revision: int = Field(ge=1)
    categoryOid: str
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CalcInstanceResultUpdateDTO(BaseDTO):
    """Replace saved result/provenance from a newer execution."""

    revision: int = Field(ge=1)
    executionId: str


class CalcInstanceResDTO(BaseDTO):
    """Return a saved immutable bundle-backed result."""

    instanceOid: str
    categoryOid: str
    reportOid: str
    reportName: str | None
    sourceVersion: str | None
    bundleHash: str
    executionId: str | None
    name: str
    description: str | None
    defaults: dict
    inputWindows: list
    resultPath: str
    isShared: bool
    shareToken: str | None
    revision: int
    createdAt: datetime.datetime
    updatedAt: datetime.datetime


class CalcInstanceListFilterDTO(BaseDTO):
    """Filter saved instances for count and item queries."""

    categoryOid: str | None = None
    query: str | None = None


class CalcInstanceShareResDTO(BaseDTO):
    """Return the active anonymous share for one saved instance."""

    instanceOid: str
    shareOid: str
    token: str
    createdAt: datetime.datetime
