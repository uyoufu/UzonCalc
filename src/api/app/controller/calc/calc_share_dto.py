"""DTOs for approved-version sharing and receiver-owned imports."""

import datetime

from pydantic import Field, model_validator

from app.controller.calc.calc_state import ShareAccessType
from app.controller.dto_base import BaseDTO


class ShareLinkCreateDTO(BaseDTO):
    """Describe a revocable share link for one approved version."""

    versionName: str
    accessType: ShareAccessType = ShareAccessType.LINK
    recipientUserOids: list[str] = Field(default_factory=list)
    expiresAt: datetime.datetime | None = None
    maxUseCount: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_recipients(self) -> "ShareLinkCreateDTO":
        """Validate recipients against the selected access mode.

        Returns:
            The validated request.

        Raises:
            ValueError: If recipients do not match the access mode.
        """
        if (
            self.accessType is ShareAccessType.SPECIFIED_USERS
            and not self.recipientUserOids
        ):
            raise ValueError("specified_users requires at least one recipient")
        if (
            self.accessType is not ShareAccessType.SPECIFIED_USERS
            and self.recipientUserOids
        ):
            raise ValueError("recipients are only valid for specified_users")
        if len(self.recipientUserOids) != len(set(self.recipientUserOids)):
            raise ValueError("recipientUserOids must be unique")
        return self


class ShareLinkResDTO(BaseDTO):
    """Return share-link metadata without exposing its secret token."""

    shareOid: str
    reportOid: str
    versionName: str
    accessType: ShareAccessType
    expiresAt: datetime.datetime | None
    revokedAt: datetime.datetime | None
    maxUseCount: int | None
    useCount: int
    createdAt: datetime.datetime
    token: str | None = None


class SharePreviewResDTO(BaseDTO):
    """Return the approved root version and transitive import footprint."""

    reportName: str
    reportDescription: str | None
    reportOid: str
    versionName: str
    dependencyCount: int
    totalFileCount: int
    totalSize: int


class ShareImportDTO(BaseDTO):
    """Select the receiver category and optional root report name."""

    categoryOid: str
    name: str | None = Field(default=None, min_length=1, max_length=100)


class ShareImportResDTO(BaseDTO):
    """Return the receiver-owned root report and imported closure size."""

    reportOid: str
    versionName: str
    importedReportCount: int
