"""DTOs for calculation-report workspaces and dependencies."""

from pydantic import Field, StringConstraints, model_validator
from typing_extensions import Annotated

from app.controller.calc.calc_state import (
    BuildStatus,
    PublishState,
    ReservedDependencySelectorKey,
    WorkspaceFileSource,
)
from app.controller.dto_base import BaseDTO

Sha256Text = Annotated[str, StringConstraints(pattern=r"^(sha256:)?[0-9a-f]{64}$")]


class WorkspaceCreateDTO(BaseDTO):
    """Describe report metadata required by the first workspace save."""

    categoryOid: str
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    cover: str | None = Field(default=None, max_length=500)


class WorkspaceFileDTO(BaseDTO):
    """Declare one file in a complete workspace snapshot."""

    path: str
    sha256: Sha256Text | None = None
    source: WorkspaceFileSource = WorkspaceFileSource.UPLOAD


class DependencySelectorDTO(BaseDTO):
    """Declare latest or an explicit semantic-version dependency selector."""

    selectorKey: str = Field(min_length=1, max_length=32)
    versionName: str | None = None
    isDefault: bool = False

    @model_validator(mode="after")
    def validate_selector_shape(self) -> "DependencySelectorDTO":
        """Ensure latest has no version and explicit selectors have one.

        Returns:
            The validated selector.

        Raises:
            ValueError: If selector fields describe an invalid target.
        """
        if (
            self.selectorKey == ReservedDependencySelectorKey.LATEST
            and self.versionName is not None
        ):
            raise ValueError("latest selector cannot specify versionName")
        if (
            self.selectorKey != ReservedDependencySelectorKey.LATEST
            and self.versionName is None
        ):
            raise ValueError("explicit selector requires versionName")
        return self


class ReportDependencyDTO(BaseDTO):
    """Declare one report-local dependency alias and its selectors."""

    alias: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
    targetReportOid: str
    selectors: list[DependencySelectorDTO] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_default_selector(self) -> "ReportDependencyDTO":
        """Require unique selector keys and exactly one default selector.

        Returns:
            The validated dependency.

        Raises:
            ValueError: If selector keys/defaults are inconsistent.
        """
        keys = [selector.selectorKey for selector in self.selectors]
        if len(keys) != len(set(keys)):
            raise ValueError("selectorKey must be unique within a dependency")
        if sum(selector.isDefault for selector in self.selectors) != 1:
            raise ValueError("dependency requires exactly one default selector")
        return self


class WorkspaceSaveDTO(BaseDTO):
    """Describe a complete optimistic workspace replacement."""

    workspaceRevision: int = Field(ge=0)
    create: WorkspaceCreateDTO | None = None
    files: list[WorkspaceFileDTO] = Field(min_length=1)
    dependencies: list[ReportDependencyDTO] = Field(default_factory=list)


class WorkspaceDependenciesUpdateDTO(BaseDTO):
    """Describe an optimistic replacement of workspace dependencies."""

    workspaceRevision: int = Field(ge=0)
    dependencies: list[ReportDependencyDTO] = Field(default_factory=list)


class WorkspaceFileResDTO(BaseDTO):
    """Return immutable metadata for one workspace file."""

    path: str
    size: int
    sha256: str


class WorkspaceBuildResDTO(BaseDTO):
    """Return the lazy build state for the selected runtime."""

    sourceArtifactHash: str
    runtimeFingerprint: str | None = None
    buildStatus: BuildStatus
    diagnostics: dict | None = None


class WorkspaceResDTO(BaseDTO):
    """Return a report workspace snapshot without inlining file bytes."""

    reportOid: str
    workspaceRevision: int
    sourceArtifactHash: str
    entryPath: str
    formatVersion: int
    files: list[WorkspaceFileResDTO]
    dependencies: list[ReportDependencyDTO]
    buildStatus: BuildStatus
    publishState: PublishState
