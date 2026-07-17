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


class ReviewStatus(StrEnum):
    """Describe the public review outcome for a report version."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExecutionSourceType(StrEnum):
    """Identify the public source selected for an execution."""

    WORKSPACE = "workspace"
    LATEST = "latest"
    VERSION = "version"


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

    LINK = "link"
    PUBLIC = "public"
    SPECIFIED_USERS = "specified_users"


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
