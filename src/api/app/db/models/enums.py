"""Integer enumerations shared by calculation-report database models."""

from enum import IntEnum


class ArtifactKind(IntEnum):
    """Identify immutable source and instrumented artifacts."""

    SOURCE = 1
    INSTRUMENTED = 2


class ArtifactBuildStatus(IntEnum):
    """Describe the lifecycle of an artifact instrumentation build."""

    PENDING = 0
    BUILDING = 1
    READY = 2
    FAILED = 3


class VersionReviewStatus(IntEnum):
    """Describe the review outcome for a published report version."""

    PENDING = 0
    APPROVED = 1
    REJECTED = 2


class ExecutionSourceType(IntEnum):
    """Identify how an execution selected its report source."""

    WORKSPACE = 1
    LATEST = 2
    VERSION = 3


class ExecutorType(IntEnum):
    """Identify the sandbox implementation used for an execution."""

    LOCAL = 1
    DOCKER = 2


class ExecutionStatus(IntEnum):
    """Describe the lifecycle of a calculation execution."""

    PENDING = 0
    RUNNING = 1
    SUCCEEDED = 2
    FAILED = 3
    CANCELLED = 4
    EXPIRED = 5


class ShareAccessType(IntEnum):
    """Describe who may consume a version share link."""

    LINK = 1
    PUBLIC = 2
    SPECIFIED_USERS = 3


class ReportOriginType(IntEnum):
    """Describe how a calculation report was initially created."""

    CREATED = 1
    COPY = 2
    SHARE = 3
    UZC_IMPORT = 4
