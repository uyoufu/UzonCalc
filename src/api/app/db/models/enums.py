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


class ExecutionSourceType(IntEnum):
    """Identify how an execution selected its report source."""

    WORKSPACE = 1
    LATEST = 2
    VERSION = 3


class ExecutionTargetType(IntEnum):
    """Identify the retained-result slot targeted by an execution."""

    WORKSPACE = 1
    VERSION = 2
    INSTANCE = 3
    SHARE_PREVIEW = 4


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

    PUBLIC = 1
    INTERNAL = 2
    SPECIFIED_USERS = 3
    SPECIFIED_DEPARTMENTS = 4


class ReportOriginType(IntEnum):
    """Describe how a calculation report was initially created."""

    NATIVE = 1
    COPY = 2
    SHARE_IMPORT = 3
    SHARE_SYNC = 4
    FILE_IMPORT = 5
