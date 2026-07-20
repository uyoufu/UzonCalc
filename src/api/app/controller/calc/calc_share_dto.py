"""DTOs for approved-version sharing and receiver-owned imports."""

import datetime

from pydantic import Field, model_validator

from app.controller.calc.calc_state import ReportSyncState, ShareAccessType
from app.controller.calc.calc_execution_dto import CalcExecutionResDTO
from app.controller.dto_base import BaseDTO


class ShareLinkCreateDTO(BaseDTO):
    """Describe a revocable share link for one published version."""

    versionName: str
    accessType: ShareAccessType = ShareAccessType.PUBLIC
    recipientUserOids: list[str] = Field(default_factory=list)
    recipientDepartmentOids: list[str] = Field(default_factory=list)
    canEdit: bool = False
    canShare: bool = False
    expiresAt: datetime.datetime | None = None
    maxUseCount: int | None = Field(default=None, ge=1)
    note: str | None = Field(default=None, max_length=500)

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
        if (
            self.accessType is ShareAccessType.SPECIFIED_DEPARTMENTS
            and not self.recipientDepartmentOids
        ):
            raise ValueError("specified_departments requires at least one department")
        if (
            self.accessType is not ShareAccessType.SPECIFIED_DEPARTMENTS
            and self.recipientDepartmentOids
        ):
            raise ValueError("departments are only valid for specified_departments")
        if len(self.recipientDepartmentOids) != len(set(self.recipientDepartmentOids)):
            raise ValueError("recipientDepartmentOids must be unique")
        return self


class ShareLinkResDTO(BaseDTO):
    """Return owner-managed share-link metadata with its recoverable token."""

    shareOid: str
    reportOid: str
    versionName: str
    accessType: ShareAccessType
    canEdit: bool
    canShare: bool
    recipientUserOids: list[str] = Field(default_factory=list)
    recipientDepartmentOids: list[str] = Field(default_factory=list)
    note: str | None = None
    expiresAt: datetime.datetime | None
    revokedAt: datetime.datetime | None
    maxUseCount: int | None
    useCount: int
    createdAt: datetime.datetime
    token: str


class SharePreviewResDTO(BaseDTO):
    """Return the published root version and transitive import footprint."""

    reportName: str
    reportDescription: str | None
    reportOid: str
    versionName: str
    dependencyCount: int
    totalFileCount: int
    totalSize: int
    canEdit: bool
    canShare: bool
    note: str | None = None
    recentExecution: CalcExecutionResDTO | None = None


class ShareImportDTO(BaseDTO):
    """Select the receiver category and optional root report name."""

    categoryOid: str
    name: str | None = Field(default=None, min_length=1, max_length=100)
    shouldSync: bool = False


class RemoteShareSourceDTO(BaseDTO):
    """Identify one remote public backend share endpoint."""

    source: str = Field(min_length=1, max_length=2048)


class RemoteShareImportDTO(ShareImportDTO, RemoteShareSourceDTO):
    """Select a remote public share and receiver-owned import metadata."""


class ShareImportResDTO(BaseDTO):
    """Return the receiver-owned root report and imported closure size."""

    reportOid: str
    versionName: str
    importedReportCount: int


class ShareCatalogFilterDTO(BaseDTO):
    """Filter share links available to the current user."""

    query: str | None = None


class SharedReportResDTO(BaseDTO):
    """Return one accessible shared report for the dedicated catalog."""

    shareOid: str
    reportName: str
    qualifiedName: str
    sharedBy: str
    description: str | None
    note: str | None = None
    versionName: str
    sharedAt: datetime.datetime
    canEdit: bool
    canShare: bool


class ReportSyncResDTO(BaseDTO):
    """Return the cached and upstream state of a synchronized report."""

    reportOid: str
    state: ReportSyncState
    currentVersionName: str
    upstreamVersionName: str | None = None


class ShareUserOptionDTO(BaseDTO):
    """Return one active user selectable as a share recipient."""

    userOid: str
    username: str
    nickName: str | None


class ShareDepartmentOptionDTO(BaseDTO):
    """Return one active department selectable as a share audience."""

    departmentOid: str
    parentOid: str | None
    name: str
