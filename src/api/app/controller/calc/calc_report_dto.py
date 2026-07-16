"""DTOs for report metadata, categories, versions, and favorites."""

import datetime
from typing import Literal

from pydantic import Field

from app.controller.dto_base import BaseDTO


class CalcReportUpdateDTO(BaseDTO):
    """Update mutable display metadata without changing workspace content."""

    categoryOid: str
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    cover: str | None = Field(default=None, max_length=500)


class CalcReportCopyDTO(CalcReportUpdateDTO):
    """Describe the metadata and optional OID of a workspace copy."""

    reportOid: str | None = None


class CalcReportResDTO(BaseDTO):
    """Return report metadata and derived workspace/publication state."""

    reportOid: str
    categoryOid: str
    name: str
    description: str | None
    cover: str | None
    entryPath: str
    formatVersion: int
    workspaceRevision: int
    workspaceArtifactHash: str | None
    latestVersionName: str | None
    latestArtifactHash: str | None
    buildStatus: str
    publishState: str
    isFavorite: bool
    createdAt: datetime.datetime
    updatedAt: datetime.datetime


class CalcReportListFilterDTO(BaseDTO):
    """Filter calculation reports for count and item queries."""

    categoryOid: str | None = None
    query: str | None = None
    favoriteOnly: bool = False


class CalcReportCategoryReqDTO(BaseDTO):
    """Create or update a report category."""

    name: str = Field(min_length=1, max_length=50)
    description: str | None = None


class CalcReportCategoryResDTO(CalcReportCategoryReqDTO):
    """Return a category and its derived active report count."""

    categoryOid: str
    sortOrder: int
    reportCount: int
    createdAt: datetime.datetime
    updatedAt: datetime.datetime


class CategoryOrderDTO(BaseDTO):
    """Assign one category's zero-based sort order."""

    categoryOid: str
    sortOrder: int = Field(ge=0)


class CalcReportVersionCreateDTO(BaseDTO):
    """Publish the current workspace as an immutable semantic version."""

    versionName: str
    description: str | None = None


class CalcReportVersionReviewDTO(BaseDTO):
    """Set an administrator review outcome for an immutable version."""

    reviewStatus: Literal["pending", "approved", "rejected"]
    reviewComment: str | None = None


class CalcReportVersionResDTO(BaseDTO):
    """Return an immutable report version and review/latest metadata."""

    versionOid: str
    versionName: str
    importSegment: str
    sourceArtifactHash: str
    description: str | None
    reviewStatus: str
    reviewedAt: datetime.datetime | None
    reviewComment: str | None
    isLatest: bool
    createdAt: datetime.datetime


class VersionNameDTO(BaseDTO):
    """Select one semantic version by its public name."""

    versionName: str
