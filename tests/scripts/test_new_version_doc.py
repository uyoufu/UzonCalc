"""Test release-document generation with isolated repositories and AI callbacks."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from rich.console import Console


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import new_version_doc  # noqa: E402
from utils.release_doc import (  # noqa: E402
    ReleaseDocError,
    apply_release_notes,
)
from utils.release_git import create_release_context  # noqa: E402


OLD_CHINESE_DOCUMENT = """---
title: 软件下载
editLink: false
---

## 1.3.0

> 更新日期：2026-06-20

### 下载地址

[uzoncalc-win-x64-1.3.0.zip](https://example.test/1.3.0.zip)
"""

OLD_ENGLISH_DOCUMENT = """---
title: Downloads
editLink: false
---

## 1.3.0

> Release date: 2026-06-20

### Download

[uzoncalc-win-x64-1.3.0.zip](https://example.test/1.3.0.zip)
"""

VALID_NOTES = {
    "zh": "### 功能新增\n\n1. 支持直接运行打包后的计算书。\n\n### Bug 修复\n\n1. 修复布尔值公式显示异常。",
    "en": "### New Features\n\n1. Run packaged calculation reports directly.\n\n### Bug Fixes\n\n1. Fixed incorrect Boolean formula rendering.",
}


def run_git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run a checked Git command in a temporary repository.

    Args:
        repo_root: Temporary repository working directory.
        arguments: Arguments following the Git executable.

    Returns:
        Completed Git process.

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
    """Write one UTF-8 fixture file below a temporary repository.

    Args:
        repo_root: Temporary repository root.
        relative_path: Destination relative to the repository.
        content: Complete text content.

    Returns:
        None.

    Raises:
        OSError: If the fixture cannot be written.
    """
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def commit_all(repo_root: Path, subject: str) -> None:
    """Commit all fixture changes with the supplied subject.

    Args:
        repo_root: Temporary repository root.
        subject: Commit subject.

    Returns:
        None.

    Raises:
        subprocess.CalledProcessError: If staging or committing fails.
    """
    run_git(repo_root, "add", "--all")
    run_git(repo_root, "commit", "-m", subject)


def create_release_repository(tmp_path: Path) -> Path:
    """Create a tagged repository with a pending desktop release.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Repository containing version sources, documents, and new commits.

    Raises:
        OSError: If fixture files cannot be created.
        subprocess.CalledProcessError: If Git setup fails.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_git(repo_root, "init")
    run_git(repo_root, "config", "user.name", "Release Test")
    run_git(repo_root, "config", "user.email", "release-test@example.com")
    write_text(
        repo_root,
        "src/web/src-tauri/Cargo.toml",
        '[package]\nname = "UzonCalc"\nversion = "1.3.0"\n',
    )
    write_text(repo_root, "src/docs/src/downloads.md", OLD_CHINESE_DOCUMENT)
    write_text(repo_root, "src/docs/src/en/downloads.md", OLD_ENGLISH_DOCUMENT)
    commit_all(repo_root, "Release 1.3.0")
    run_git(repo_root, "tag", "v1.3.0")

    write_text(
        repo_root,
        "src/web/src-tauri/Cargo.toml",
        '[package]\nname = "UzonCalc"\nversion = "1.4.0"\n',
    )
    commit_all(repo_root, "Version: Web 1.4.0")
    write_text(repo_root, "feature.txt", "feature")
    commit_all(repo_root, "Feat: Run packaged reports directly")
    return repo_root


def test_release_context_uses_reachable_tag_and_all_new_subjects(
    tmp_path: Path,
) -> None:
    """The context should use Tauri version and every subject after the tag.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        None.

    Raises:
        None.
    """
    repo_root = create_release_repository(tmp_path)

    context = create_release_context(repo_root, local_date=date(2026, 7, 21))

    assert context.previous_tag == "v1.3.0"
    assert context.target_version == "1.4.0"
    assert context.release_date == "2026-07-21"
    assert context.commit_subjects == (
        "Version: Web 1.4.0",
        "Feat: Run packaged reports directly",
    )


def test_apply_release_notes_inserts_localized_fixed_fields(
    tmp_path: Path,
) -> None:
    """AI bodies should receive script-owned version, date, and links.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        None.

    Raises:
        None.
    """
    repo_root = create_release_repository(tmp_path)

    apply_release_notes(
        repo_root,
        json.dumps(VALID_NOTES, ensure_ascii=False),
        local_date=date(2026, 7, 21),
    )

    chinese = (repo_root / "src/docs/src/downloads.md").read_text(encoding="utf-8")
    english = (repo_root / "src/docs/src/en/downloads.md").read_text(encoding="utf-8")
    assert chinese.index("## 1.4.0") < chinese.index("## 1.3.0")
    assert "> 更新日期：2026-07-21" in chinese
    assert "> Release date: 2026-07-21" in english
    assert "uzoncalc-win-x64-1.4.0.zip" in chinese
    assert "uzoncalc-win-x64-1.4.0.zip" in english
    assert "## 1.3.0" in chinese
    assert "## 1.3.0" in english


def test_apply_release_notes_replaces_existing_target_without_duplication(
    tmp_path: Path,
) -> None:
    """Repeating the callback should replace rather than duplicate a release.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        None.

    Raises:
        None.
    """
    repo_root = create_release_repository(tmp_path)
    first_payload = json.dumps(VALID_NOTES, ensure_ascii=False)
    apply_release_notes(repo_root, first_payload, local_date=date(2026, 7, 21))
    replacement = dict(VALID_NOTES)
    replacement["zh"] = "### 功能优化\n\n1. 简化计算书运行流程。"
    replacement["en"] = "### Improvements\n\n1. Simplified the report run workflow."

    apply_release_notes(
        repo_root,
        json.dumps(replacement, ensure_ascii=False),
        local_date=date(2026, 7, 22),
    )

    chinese = (repo_root / "src/docs/src/downloads.md").read_text(encoding="utf-8")
    assert chinese.count("## 1.4.0") == 1
    assert "简化计算书运行流程" in chinese
    assert "直接运行打包后的计算书" not in chinese
    assert "> 更新日期：2026-07-22" in chinese


def test_invalid_ai_wrapper_content_does_not_modify_documents(tmp_path: Path) -> None:
    """AI-owned version wrappers should be rejected before either write.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        None.

    Raises:
        None.
    """
    repo_root = create_release_repository(tmp_path)
    chinese_path = repo_root / "src/docs/src/downloads.md"
    english_path = repo_root / "src/docs/src/en/downloads.md"
    originals = (chinese_path.read_bytes(), english_path.read_bytes())
    invalid = dict(VALID_NOTES)
    invalid["zh"] = "## 1.4.0\n\n### 功能新增\n\n1. 不允许的包装。"

    with pytest.raises(ReleaseDocError, match="只能包含更新正文"):
        apply_release_notes(repo_root, json.dumps(invalid, ensure_ascii=False))

    assert (chinese_path.read_bytes(), english_path.read_bytes()) == originals


def test_opencode_failure_restores_documents_after_callback(tmp_path: Path) -> None:
    """A failing OpenCode run should restore both pre-run document snapshots.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        None.

    Raises:
        None.
    """
    repo_root = create_release_repository(tmp_path)
    chinese_path = repo_root / "src/docs/src/downloads.md"
    english_path = repo_root / "src/docs/src/en/downloads.md"
    originals = (chinese_path.read_bytes(), english_path.read_bytes())

    def failing_opencode(prompt: str, callback_repo_root: Path) -> int:
        """Simulate a callback followed by a nonzero OpenCode exit.

        Args:
            prompt: Generated OpenCode prompt.
            callback_repo_root: Repository passed to the callback.

        Returns:
            Nonzero simulated process exit code.

        Raises:
            ReleaseDocError: If applying the valid fixture unexpectedly fails.
        """
        assert "apply <<'UZONCALC_RELEASE_NOTES_JSON'" in prompt
        apply_release_notes(
            callback_repo_root,
            json.dumps(VALID_NOTES, ensure_ascii=False),
        )
        return 9

    with pytest.raises(ReleaseDocError, match="退出码: 9"):
        new_version_doc.generate_release_documents(
            repo_root,
            console=Console(record=True, width=120),
            assume_yes=True,
            run_opencode=failing_opencode,
        )

    assert (chinese_path.read_bytes(), english_path.read_bytes()) == originals
