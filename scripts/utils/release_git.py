"""Resolve the Git range and deterministic metadata for a new release."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .release_doc import (
    ReleaseContext,
    ReleaseDocError,
    parse_semantic_version,
    read_target_version,
)


def run_git(
    repo_root: Path, arguments: Sequence[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run Git without a shell and capture its text output.

    Args:
        repo_root: Repository working directory.
        arguments: Arguments following the ``git`` executable.
        check: Whether a nonzero exit code should fail.

    Returns:
        Completed Git process.

    Raises:
        ReleaseDocError: If Git cannot start or a checked command fails.
    """
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ReleaseDocError(f"无法执行 Git: {exc}") from exc
    if check and completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise ReleaseDocError(f"Git 命令执行失败: git {' '.join(arguments)}\n{details}")
    return completed


def find_latest_release_tag(repo_root: Path) -> str:
    """Find the nearest reachable ``vX.Y.Z`` tag from ``HEAD``.

    Args:
        repo_root: Repository whose history should be inspected.

    Returns:
        Release tag including its ``v`` prefix.

    Raises:
        ReleaseDocError: If no valid reachable tag exists.
    """
    completed = run_git(
        repo_root,
        ["describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", "HEAD"],
        check=False,
    )
    tag = completed.stdout.strip()
    if completed.returncode != 0 or not tag:
        raise ReleaseDocError("未找到可达的版本标签，请先创建 vX.Y.Z 标签。")
    parse_semantic_version(tag.removeprefix("v"), source=f"Git 标签 {tag}")
    return tag


def collect_commit_subjects(repo_root: Path, previous_tag: str) -> tuple[str, ...]:
    """Collect all subjects after a release tag in chronological order.

    Args:
        repo_root: Repository whose history should be inspected.
        previous_tag: Exclusive range start.

    Returns:
        Oldest-first subjects, including merge commits.

    Raises:
        ReleaseDocError: If Git cannot traverse the range.
    """
    output = run_git(
        repo_root,
        ["log", "--reverse", "--format=%s", f"{previous_tag}..HEAD"],
    ).stdout
    return tuple(subject for subject in output.splitlines() if subject.strip())


def create_release_context(
    repo_root: Path, *, local_date: date | None = None
) -> ReleaseContext:
    """Resolve and validate deterministic release metadata.

    Args:
        repo_root: Repository containing version sources and history.
        local_date: Optional date override used by tests.

    Returns:
        Validated release context.

    Raises:
        ReleaseDocError: If versions regress or the range is empty.
    """
    run_git(repo_root, ["rev-parse", "--show-toplevel"])
    target_version = read_target_version(repo_root)
    previous_tag = find_latest_release_tag(repo_root)
    previous_version = previous_tag.removeprefix("v")
    if parse_semantic_version(
        target_version, source="目标版本"
    ) <= parse_semantic_version(previous_version, source=f"Git 标签 {previous_tag}"):
        raise ReleaseDocError(
            f"目标版本 {target_version} 必须高于上一版本 {previous_version}。"
        )
    commit_subjects = collect_commit_subjects(repo_root, previous_tag)
    if not commit_subjects:
        raise ReleaseDocError(f"{previous_tag}..HEAD 范围内没有可用于发布说明的提交。")
    return ReleaseContext(
        previous_tag,
        target_version,
        (local_date or date.today()).isoformat(),
        commit_subjects,
    )
