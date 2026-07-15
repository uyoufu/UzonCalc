"""Boundary tests for bubblewrap commands and local cache cleanup."""

import os
from pathlib import Path

from app.sandbox.core.backend_types import PreparedExecutionBundle
from app.sandbox.core.executor_bubblewrap import BubblewrapSandboxExecutor
from app.schedule.jobs.calc_cache_cleaner import _remove_orphan_hash_directories


def test_bubblewrap_command_creates_mount_parents(monkeypatch, tmp_path: Path) -> None:
    """Empty namespaces must create nested destination parents before ro-bind."""
    runtime = tmp_path / "home/user/runtime"
    runtime.mkdir(parents=True)
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    monkeypatch.setattr(
        "app.sandbox.core.executor_bubblewrap._runtime_readonly_paths",
        lambda: [runtime],
    )
    bundle = PreparedExecutionBundle(
        oid="bundle-oid",
        bundle_hash="a" * 64,
        root=bundle_root,
        entry_path="src/main.py",
        manifest={},
    )

    command = BubblewrapSandboxExecutor()._build_command(bundle, False)

    parent = str(runtime.parent)
    assert command.index(parent) < command.index(str(runtime))
    assert "--unshare-all" in command
    assert "--ro-bind" in command


def test_cache_cleanup_preserves_tracked_and_recent_orphans(tmp_path: Path) -> None:
    """Cleanup should remove only untracked hash directories older than its grace."""
    root = tmp_path / "sha256"
    tracked = root / "aa" / ("a" * 64)
    recent = root / "bb" / ("b" * 64)
    old = root / "cc" / ("c" * 64)
    for directory in (tracked, recent, old):
        directory.mkdir(parents=True)
        (directory / "manifest.json").write_text("{}", encoding="utf-8")
    old_timestamp = old.stat().st_mtime - 172800
    os.utime(old, (old_timestamp, old_timestamp))

    removed = _remove_orphan_hash_directories(root, {tracked.name})

    assert removed == 1
    assert tracked.is_dir()
    assert recent.is_dir()
    assert not old.exists()
