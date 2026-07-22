"""Database model registry for the shared SQLAlchemy metadata."""

from .base import Base, BaseModel
from .calc_execution import (
    CalcExecution,
    CalcExecutionBundle,
    CalcExecutionBundleComponent,
    CalcExecutionSlot as CalcExecutionSlot,
)
from .calc_report import CalcReport, CalcReportOrigin, CalcReportSyncSource
from .calc_report_artifact import CalcReportArtifact, CalcReportArtifactBuild
from .calc_report_category import CalcReportCategory
from .calc_report_dependency import (
    CalcReportDependency,
    CalcReportDependencySelector,
)
from .calc_report_instance import CalcReportInstance, CalcReportInstanceShare
from .calc_report_instance_category import CalcReportInstanceCategory
from .calc_report_share import (
    CalcReportShareDepartment,
    CalcReportShareLink,
    CalcReportShareRecipient,
)
from .calc_report_version import CalcReportVersion
from .department import Department, DepartmentUser
from .enums import (
    ArtifactBuildStatus,
    ArtifactKind,
    ExecutionSourceType,
    ExecutionStatus,
    ExecutorType,
    ReportOriginType,
    ShareAccessType,
)
from .favorite_calc_report import FavoriteCalcReport
from .system_setting import SystemSetting
from .tmp_file import TmpFile
from .user import User
from .user_input_history import InputCache, UserInputHistory
from .user_setting import UserSetting

__all__ = [
    "ArtifactBuildStatus",
    "ArtifactKind",
    "Base",
    "BaseModel",
    "CalcExecution",
    "CalcExecutionBundle",
    "CalcExecutionBundleComponent",
    "CalcReport",
    "CalcReportArtifact",
    "CalcReportArtifactBuild",
    "CalcReportCategory",
    "CalcReportDependency",
    "CalcReportDependencySelector",
    "CalcReportInstance",
    "CalcReportInstanceShare",
    "CalcReportInstanceCategory",
    "CalcReportOrigin",
    "CalcReportSyncSource",
    "CalcReportShareDepartment",
    "CalcReportShareLink",
    "CalcReportShareRecipient",
    "CalcReportVersion",
    "Department",
    "DepartmentUser",
    "ExecutionSourceType",
    "ExecutionStatus",
    "ExecutorType",
    "FavoriteCalcReport",
    "InputCache",
    "ReportOriginType",
    "ShareAccessType",
    "SystemSetting",
    "TmpFile",
    "User",
    "UserInputHistory",
    "UserSetting",
]
