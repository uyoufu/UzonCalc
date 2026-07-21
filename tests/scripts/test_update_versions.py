"""Test the repository version-update CLI with isolated Git repositories."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from rich.console import Console


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import update_versions  # noqa: E402
from version_update_models import (  # noqa: E402
    BumpLevel,
    GitCommit,
    ProjectUpgradePlan,
    SemanticVersion,
    VersionUpdateError,
)


def run_git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run a checked Git command in a temporary test repository.

    Args:
        repo_root: Repository working directory.
        arguments: Git command arguments.

    Returns:
        Completed Git process with captured text output.

    Raises:
        subprocess.CalledProcessError: If Git exits unsuccessfully.
    """
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def write_text(repo_root: Path, relative_path: str, content: str) -> None:
    """Write one UTF-8 fixture file under the temporary repository.

    Args:
        repo_root: Temporary repository root.
        relative_path: File path relative to the repository.
        content: Complete text to write.
    """
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def commit_all(repo_root: Path, subject: str) -> str:
    """Commit all temporary fixture changes.

    Args:
        repo_root: Temporary repository root.
        subject: Commit subject.

    Returns:
        Full hash of the created commit.
    """
    run_git(repo_root, "add", "--all")
    run_git(repo_root, "commit", "-m", subject)
    return run_git(repo_root, "rev-parse", "HEAD").stdout.strip()


def create_release_repository(tmp_path: Path) -> Path:
    """Create a clean repository containing every supported release file.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Initialized repository whose initial commit is the legacy baseline.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_git(repo_root, "init")
    run_git(repo_root, "config", "user.name", "Version Test")
    run_git(repo_root, "config", "user.email", "version-test@example.com")
    write_text(
        repo_root,
        "src/web/package.json",
        '{\n  "name": "uzoncalc",\n  "version": "0.20.3",\n  "private": true\n}\n',
    )
    write_text(
        repo_root,
        "src/web/src/config/app.config.ts",
        "export default {\n  default: {\n    version: '1.3.0'\n  }\n}\n",
    )
    write_text(
        repo_root,
        "src/web/src-tauri/Cargo.toml",
        '[package]\nname = "UzonCalc"\nversion = "1.3.0"\nedition = "2021"\n',
    )
    write_text(
        repo_root,
        "src/web/src-tauri/Cargo.lock",
        '# generated\nversion = 3\n\n[[package]]\nname = "UzonCalc"\nversion = "1.3.0"\n',
    )
    write_text(
        repo_root,
        "src/web/src-tauri/tauri.conf.json",
        '{\n  "productName": "uzoncalc",\n  "version": "0.1.0",\n  "identifier": "test"\n}\n',
    )
    write_text(
        repo_root,
        "src/api/pyproject.toml",
        '[project]\nname = "uzoncalc-api"\nversion = "1.3.0"\n',
    )
    write_text(
        repo_root,
        "src/api/config/app.ini",
        "[app]\nname = uzoncalc-api\nversion = 1.1.0\n",
    )
    write_text(
        repo_root,
        "src/core/pyproject.toml",
        '[project]\nname = "uzoncalc"\nversion = "1.3.3"\n',
    )
    write_text(
        repo_root,
        "uv.lock",
        'version = 1\n\n[[package]]\nname = "uzoncalc"\nversion = "1.3.3"\n'
        '\n[[package]]\nname = "uzoncalc-api"\nversion = "1.3.0"\n',
    )
    commit_all(repo_root, "Initial release versions")
    return repo_root


def add_project_change(repo_root: Path, project: str, subject: str) -> str:
    """Add and commit one non-version project change.

    Args:
        repo_root: Temporary repository root.
        project: Project directory name below ``src``.
        subject: Commit subject.

    Returns:
        Full hash of the new commit.
    """
    path = repo_root / "src" / project / f"change-{subject.replace(' ', '-')}.txt"
    path.write_text(subject, encoding="utf-8")
    return commit_all(repo_root, subject)


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (BumpLevel.MAJOR, "2.0.0"),
        (BumpLevel.MINOR, "1.4.0"),
        (BumpLevel.PATCH, "1.3.4"),
    ],
)
def test_semantic_version_bump_resets_lower_components(
    level: BumpLevel, expected: str
) -> None:
    """Each increment level should apply standard semantic-version resets."""
    version = SemanticVersion.parse("1.3.3", source="test")

    assert str(version.bump(level)) == expected


def test_semantic_version_rejects_non_numeric_or_incomplete_values() -> None:
    """Version parsing should reject formats outside strict major.minor.patch."""
    with pytest.raises(VersionUpdateError, match="major.minor.patch"):
        SemanticVersion.parse("1.3-beta", source="test")


def test_main_applies_independent_levels_and_commits_all_release_files(
    tmp_path: Path,
) -> None:
    """Mixed project choices should synchronize mirrors and create one Version commit."""
    repo_root = create_release_repository(tmp_path)
    add_project_change(repo_root, "web", "Web feature")
    add_project_change(repo_root, "api", "API feature")
    add_project_change(repo_root, "core", "Core feature")
    choices = {
        "Web": BumpLevel.MAJOR,
        "API": BumpLevel.MINOR,
        "Core": BumpLevel.PATCH,
    }

    exit_code = update_versions.main(
        repo_root=repo_root,
        console=Console(record=True, width=120),
        choose_level=lambda plan: choices[plan.config.display_name],
        confirm_upgrade=lambda: True,
    )

    assert exit_code == 0
    assert '"version": "2.0.0"' in (repo_root / "src/web/package.json").read_text()
    assert (
        "version: '2.0.0'"
        in (repo_root / "src/web/src/config/app.config.ts").read_text()
    )
    assert (
        'version = "2.0.0"' in (repo_root / "src/web/src-tauri/Cargo.toml").read_text()
    )
    assert (
        'version = "2.0.0"' in (repo_root / "src/web/src-tauri/Cargo.lock").read_text()
    )
    assert (
        '"version": "2.0.0"'
        in (repo_root / "src/web/src-tauri/tauri.conf.json").read_text()
    )
    assert 'version = "1.4.0"' in (repo_root / "src/api/pyproject.toml").read_text()
    assert "version = 1.4.0" in (repo_root / "src/api/config/app.ini").read_text()
    assert 'version = "1.3.4"' in (repo_root / "src/core/pyproject.toml").read_text()
    uv_lock = (repo_root / "uv.lock").read_text()
    assert 'name = "uzoncalc"\nversion = "1.3.4"' in uv_lock
    assert 'name = "uzoncalc-api"\nversion = "1.4.0"' in uv_lock
    assert (
        run_git(repo_root, "log", "-1", "--format=%s").stdout.strip()
        == "Version: Web 2.0.0, API 1.4.0, Core 1.3.4"
    )
    assert run_git(repo_root, "status", "--porcelain").stdout == ""


def test_successful_version_commit_becomes_next_run_baseline(tmp_path: Path) -> None:
    """A generated Version commit should prevent an immediate duplicate bump."""
    repo_root = create_release_repository(tmp_path)
    add_project_change(repo_root, "web", "Web feature")
    update_versions.main(
        repo_root=repo_root,
        choose_level=lambda plan: BumpLevel.PATCH,
        confirm_upgrade=lambda: True,
    )
    head_before_second_run = run_git(repo_root, "rev-parse", "HEAD").stdout.strip()

    exit_code = update_versions.main(
        repo_root=repo_root,
        console=Console(record=True, width=120),
        choose_level=lambda plan: pytest.fail("No project should request a level"),
        confirm_upgrade=lambda: pytest.fail("No confirmation should be requested"),
    )

    assert exit_code == 0
    assert (
        run_git(repo_root, "rev-parse", "HEAD").stdout.strip() == head_before_second_run
    )


def test_skip_and_final_cancel_do_not_modify_repository(tmp_path: Path) -> None:
    """Skipping every changed project or rejecting confirmation should remain a no-op."""
    repo_root = create_release_repository(tmp_path)
    add_project_change(repo_root, "web", "Web feature")
    original_head = run_git(repo_root, "rev-parse", "HEAD").stdout.strip()

    update_versions.main(
        repo_root=repo_root,
        choose_level=lambda plan: BumpLevel.SKIP,
        confirm_upgrade=lambda: pytest.fail("Skipped plans need no final confirmation"),
    )
    assert run_git(repo_root, "rev-parse", "HEAD").stdout.strip() == original_head

    update_versions.main(
        repo_root=repo_root,
        choose_level=lambda plan: BumpLevel.PATCH,
        confirm_upgrade=lambda: False,
    )
    assert run_git(repo_root, "rev-parse", "HEAD").stdout.strip() == original_head
    assert run_git(repo_root, "status", "--porcelain").stdout == ""


def test_dirty_worktree_aborts_before_project_selection(tmp_path: Path) -> None:
    """Any untracked or tracked worktree entry should block the release flow."""
    repo_root = create_release_repository(tmp_path)
    write_text(repo_root, "untracked.txt", "pending")

    with pytest.raises(VersionUpdateError, match="工作区存在未提交项"):
        update_versions.main(
            repo_root=repo_root,
            choose_level=lambda plan: pytest.fail("Dirty repositories must not prompt"),
            confirm_upgrade=lambda: pytest.fail("Dirty repositories must not confirm"),
        )


def test_prompt_lists_only_three_newest_commit_summaries(monkeypatch) -> None:
    """Long project histories should show three summaries and an omitted count."""
    plan = ProjectUpgradePlan(
        config=update_versions.PROJECT_CONFIGS[0],
        current_version=SemanticVersion(1, 3, 0),
        baseline_commit="baseline",
        commits=[GitCommit(str(index) * 40, f"Commit {index}") for index in range(5)],
    )
    console = Console(record=True, width=120)
    monkeypatch.setattr(
        update_versions.Prompt, "ask", lambda *args, **kwargs: "补丁版本"
    )

    selected = update_versions.prompt_for_bump_level(plan, console)
    output = console.export_text()

    assert selected is BumpLevel.PATCH
    assert "Commit 0" in output
    assert "Commit 1" in output
    assert "Commit 2" in output
    assert "Commit 3" not in output
    assert "另有 2 条提交未显示" in output


def test_commit_failure_restores_files_and_index(tmp_path: Path, monkeypatch) -> None:
    """A failed Git commit should restore every generated file and leave no staged diff."""
    repo_root = create_release_repository(tmp_path)
    add_project_change(repo_root, "web", "Web feature")
    original_package = (repo_root / "src/web/package.json").read_bytes()
    original_run_git = update_versions.run_git

    def fail_commit(
        target_repo: Path, arguments: list[str], *, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Fail only the commit command while delegating cleanup Git calls."""
        if arguments and arguments[0] == "commit":
            raise VersionUpdateError("commit rejected")
        return original_run_git(target_repo, arguments, check=check)

    monkeypatch.setattr(update_versions, "run_git", fail_commit)

    with pytest.raises(VersionUpdateError, match="commit rejected"):
        update_versions.main(
            repo_root=repo_root,
            choose_level=lambda plan: BumpLevel.PATCH,
            confirm_upgrade=lambda: True,
        )

    assert (repo_root / "src/web/package.json").read_bytes() == original_package
    assert run_git(repo_root, "status", "--porcelain").stdout == ""
