"""String-valued state contracts shared by calculation-report APIs."""

from enum import StrEnum


class PublishState(StrEnum):
    """Describe how a mutable workspace relates to published versions."""

    UNPUBLISHED = "unpublished"
    PUBLISHED = "published"
    UNPUBLISHED_CHANGES = "unpublished_changes"
    WORKSPACE_VERSION_MISMATCH = "workspace_version_mismatch"


class BuildStatus(StrEnum):
    """Describe the public lifecycle of an artifact build."""

    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    BUILDING = "building"
    READY = "ready"
    FAILED = "failed"


class ExecutionSourceType(StrEnum):
    """Identify the public source selected for an execution."""

    WORKSPACE = "workspace"
    LATEST = "latest"
    VERSION = "version"


class ExecutionTargetType(StrEnum):
    """Identify the user-isolated retained execution target."""

    WORKSPACE = "workspace"
    VERSION = "version"
    INSTANCE = "instance"


class ExecutionStatus(StrEnum):
    """Describe the public lifecycle of a calculation execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ShareAccessType(StrEnum):
    """Describe who may consume a version share link."""

    PUBLIC = "public"
    INTERNAL = "internal"
    SPECIFIED_USERS = "specified_users"
    SPECIFIED_DEPARTMENTS = "specified_departments"


class ReportOriginType(StrEnum):
    """Describe how a calculation report entered the current library."""

    NATIVE = "native"
    COPY = "copy"
    SHARE_IMPORT = "share_import"
    SHARE_SYNC = "share_sync"
    FILE_IMPORT = "file_import"


class ReportSyncState(StrEnum):
    """Describe whether a synchronized report has a newer upstream version."""

    NOT_APPLICABLE = "not_applicable"
    CURRENT = "current"
    UPDATE_AVAILABLE = "update_available"
    SOURCE_UNAVAILABLE = "source_unavailable"
    ACCESS_REVOKED = "access_revoked"


class WorkspaceFileSource(StrEnum):
    """Identify where a workspace-save file obtains its bytes."""

    UPLOAD = "upload"
    CURRENT = "current"


class ExecutorType(StrEnum):
    """Identify the public sandbox executor implementation."""

    LOCAL = "local"
    DOCKER = "docker"


class ArtifactManifestKind(StrEnum):
    """Identify an artifact kind in persisted JSON manifests."""

    SOURCE = "source"
    INSTRUMENTED = "instrumented"


class ReservedDependencySelectorKey(StrEnum):
    """Identify reserved dependency selector keys among dynamic selector names."""

    LATEST = "latest"
