"""DTOs for reproducible bundle-backed calculation execution."""

import datetime
from typing import Any

from pydantic import Field, model_validator

from app.controller.calc.calc_state import (
    ExecutionSourceType,
    ExecutionStatus,
    ExecutorType,
)
from app.controller.dto_base import BaseDTO
from app.sandbox.core.backend_types import SandboxBackendMode
from app.service.html_cache.html_cacher import HtmlUpdateType


class CalcExecutionSourceDTO(BaseDTO):
    """Select workspace, latest, or one explicit immutable version."""

    type: ExecutionSourceType = ExecutionSourceType.LATEST
    versionName: str | None = None

    @model_validator(mode="after")
    def validate_version_name(self) -> "CalcExecutionSourceDTO":
        """Require versionName only for explicit version execution."""
        if self.type is ExecutionSourceType.VERSION and not self.versionName:
            raise ValueError("versionName is required for version source")
        if (
            self.type is not ExecutionSourceType.VERSION
            and self.versionName is not None
        ):
            raise ValueError("versionName is only valid for version source")
        return self


class CalcExecutionStartDTO(BaseDTO):
    """Start one managed report execution."""

    reportOid: str
    source: CalcExecutionSourceDTO = Field(
        default_factory=lambda: CalcExecutionSourceDTO(type=ExecutionSourceType.LATEST)
    )
    defaults: dict[str, dict[str, Any]] = Field(default_factory=dict)
    isSilent: bool = False
    lastHtmlPath: str | None = None


class CalcExecutionContinueDTO(BaseDTO):
    """Continue an existing interactive execution."""

    defaults: dict[str, dict[str, Any]] = Field(default_factory=dict)
    lastHtmlPath: str | None = None


class CalcExecutionResDTO(BaseDTO):
    """Return one execution step plus immutable provenance."""

    executionId: str
    reportOid: str
    sourceType: ExecutionSourceType
    resolvedVersion: str | None
    sourceArtifactHash: str
    executionArtifactHash: str
    bundleHash: str
    runtimeFingerprint: str
    executorType: ExecutorType
    backendMode: SandboxBackendMode
    status: ExecutionStatus
    isCompleted: bool
    windows: list[dict[str, Any]] = Field(default_factory=list)
    htmlPath: str = ""
    updateType: HtmlUpdateType = HtmlUpdateType.Full
    htmlContentPatch: str | None = None
    createdAt: datetime.datetime
    completedAt: datetime.datetime | None = None
