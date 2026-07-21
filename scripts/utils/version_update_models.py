"""Define semantic versions and project upgrade-plan models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class VersionUpdateError(RuntimeError):
    """Report a validation, Git, or version-file update failure."""


class ProjectKey(Enum):
    """Identify one independently versioned project."""

    WEB = "web"
    API = "api"
    CORE = "core"


class BumpLevel(Enum):
    """Define supported semantic-version increment levels."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    SKIP = "skip"


@dataclass(frozen=True, order=True)
class SemanticVersion:
    """Represent a strict numeric ``major.minor.patch`` version."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str, *, source: str) -> SemanticVersion:
        """Parse one strict three-part numeric version.

        Args:
            value: Version text to parse.
            source: Human-readable source used in validation errors.

        Returns:
            Parsed semantic version.

        Raises:
            VersionUpdateError: If the value is not ``major.minor.patch``.
        """
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value.strip())
        if match is None:
            raise VersionUpdateError(
                f"{source} 的版本必须是 major.minor.patch 三段数字格式，当前值为 {value!r}"
            )
        return cls(*(int(part) for part in match.groups()))

    def bump(self, level: BumpLevel) -> SemanticVersion:
        """Increment this version using semantic-version reset rules.

        Args:
            level: Major, minor, or patch increment level.

        Returns:
            Incremented version.

        Raises:
            VersionUpdateError: If ``SKIP`` is passed as an increment level.
        """
        if level is BumpLevel.MAJOR:
            return SemanticVersion(self.major + 1, 0, 0)
        if level is BumpLevel.MINOR:
            return SemanticVersion(self.major, self.minor + 1, 0)
        if level is BumpLevel.PATCH:
            return SemanticVersion(self.major, self.minor, self.patch + 1)
        raise VersionUpdateError("跳过项目时不能计算目标版本")

    def __str__(self) -> str:
        """Return the normalized dotted version text."""
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class GitCommit:
    """Store the identifier and subject of one relevant Git commit."""

    commit_hash: str
    subject: str


@dataclass(frozen=True)
class ProjectConfig:
    """Describe one project's Git scope and canonical version source."""

    key: ProjectKey
    display_name: str
    project_path: Path
    canonical_path: Path
    canonical_kind: str
    version_history_pattern: str


@dataclass
class ProjectUpgradePlan:
    """Hold detected changes and the user's version choice for one project."""

    config: ProjectConfig
    current_version: SemanticVersion
    baseline_commit: str
    commits: list[GitCommit]
    bump_level: BumpLevel | None = None
    target_version: SemanticVersion | None = None

    @property
    def has_changes(self) -> bool:
        """Return whether Git contains project commits after the baseline."""
        return bool(self.commits)

    @property
    def should_upgrade(self) -> bool:
        """Return whether this plan has a concrete selected target version."""
        return self.target_version is not None


PROJECT_CONFIGS = (
    ProjectConfig(
        ProjectKey.WEB,
        "Web",
        Path("src/web"),
        Path("src/web/src/config/app.config.ts"),
        "typescript",
        r"^[[:space:]]*version[[:space:]]*:",
    ),
    ProjectConfig(
        ProjectKey.API,
        "API",
        Path("src/api"),
        Path("src/api/pyproject.toml"),
        "pyproject",
        r"^version[[:space:]]*=",
    ),
    ProjectConfig(
        ProjectKey.CORE,
        "Core",
        Path("src/core"),
        Path("src/core/pyproject.toml"),
        "pyproject",
        r"^version[[:space:]]*=",
    ),
)
