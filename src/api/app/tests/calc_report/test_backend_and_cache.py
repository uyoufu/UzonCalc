"""Boundary tests for bubblewrap commands and local cache cleanup."""

import asyncio
import datetime
import os
import zipfile
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import (
    Base,
    CalcExecutionBundle,
    CalcReport,
    CalcReportArtifact,
    CalcReportArtifactBuild,
    CalcReportCategory,
    User,
)
from app.db.models.enums import ArtifactBuildStatus, ArtifactKind
from app.sandbox.core.backend_types import PreparedExecutionBundle
from app.sandbox.core.executor_bubblewrap import BubblewrapSandboxExecutor
from app.sandbox import sandbox_server
from app.schedule.jobs.calc_cache_cleaner import (
    _prune_unreferenced_cache_rows,
    _remove_orphan_hash_directories,
)
from app.service import calc_execution_bundle_service
from app.service.calc_report_artifact_service import ArtifactFile


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
        entry_path="main.py",
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


def test_local_bundle_keeps_root_relative_code_and_resources(
    monkeypatch, tmp_path: Path
) -> None:
    """Local bundle assembly should overlay instrumented code without path rewrites."""
    artifacts = {
        "instrumented": [
            ArtifactFile(path="__init__.py", content=b""),
            ArtifactFile(path="main.py", content=b"instrumented"),
            ArtifactFile(path="helpers/math.py", content=b"instrumented helper"),
        ],
        "source": [
            ArtifactFile(path="calcbook.json", content=b"{}"),
            ArtifactFile(path="main.py", content=b"source"),
            ArtifactFile(path="assets/logo.txt", content=b"logo"),
        ],
    }
    monkeypatch.setattr(
        calc_execution_bundle_service.artifact_store,
        "read_all",
        lambda storage_key: artifacts[storage_key],
    )
    component = calc_execution_bundle_service._ResolvedComponent(
        component_key="entry",
        scope_key="entry",
        alias=None,
        selector_key=None,
        source_artifact=SimpleNamespace(storageKey="source"),
        execution_artifact=SimpleNamespace(storageKey="instrumented"),
        is_entry=True,
    )

    calc_execution_bundle_service._write_component(tmp_path, component)

    assert (tmp_path / "main.py").read_bytes() == b"instrumented"
    assert (tmp_path / "helpers/math.py").read_bytes() == b"instrumented helper"
    assert (tmp_path / "assets/logo.txt").read_bytes() == b"logo"
    assert (tmp_path / "calcbook.json").read_bytes() == b"{}"


def test_remote_bundle_keeps_root_relative_code_and_resources(
    monkeypatch, tmp_path: Path
) -> None:
    """Remote extraction should use the same root-relative overlay as local execution."""
    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()
    with zipfile.ZipFile(artifact_root / "payload.zip", "w") as archive:
        archive.writestr("main.py", b"instrumented")
        archive.writestr("helpers/math.py", b"helper")
        archive.writestr("assets/logo.txt", b"logo")
    monkeypatch.setattr(sandbox_server, "_artifact_path", lambda _: artifact_root)
    destination = tmp_path / "bundle"

    sandbox_server._extract_component_artifact(
        "artifact-hash", destination, is_entry=True, code=True
    )
    sandbox_server._extract_component_artifact(
        "artifact-hash", destination, is_entry=True, code=False
    )

    assert (destination / "main.py").read_bytes() == b"instrumented"
    assert (destination / "helpers/math.py").read_bytes() == b"helper"
    assert (destination / "assets/logo.txt").read_bytes() == b"logo"


def test_cache_cleanup_prunes_old_unreferenced_database_rows() -> None:
    """Cleanup should retain workspace sources and remove detached cache metadata."""

    async def scenario() -> None:
        """Create protected and detached cache rows, then run database pruning."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            user = User(
                username="owner", password="hash", salt="salt", roles=["regular"]
            )
            session.add(user)
            await session.flush()
            category = CalcReportCategory(userId=user.id, name="reports")
            session.add(category)
            await session.flush()
            old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
                days=2
            )
            source = CalcReportArtifact(
                artifactKind=ArtifactKind.SOURCE.value,
                contentHash="a" * 64,
                storageKey="source",
                manifest={},
                fileCount=1,
                totalSize=1,
                createdAt=old,
            )
            output = CalcReportArtifact(
                artifactKind=ArtifactKind.INSTRUMENTED.value,
                contentHash="b" * 64,
                storageKey="output",
                manifest={},
                fileCount=1,
                totalSize=1,
                createdAt=old,
            )
            session.add_all([source, output])
            await session.flush()
            report = CalcReport(
                userId=user.id,
                categoryId=category.id,
                name="report",
                workspaceArtifactId=source.id,
            )
            bundle = CalcExecutionBundle(
                bundleHash="c" * 64,
                runtimeFingerprint="runtime",
                entrySourceArtifactId=source.id,
                entryExecutionArtifactId=output.id,
                manifest={},
                createdAt=old,
            )
            build = CalcReportArtifactBuild(
                sourceArtifactId=source.id,
                outputArtifactId=output.id,
                runtimeFingerprint="runtime",
                status=ArtifactBuildStatus.READY.value,
                attemptCount=1,
                updatedAt=old,
            )
            session.add_all([report, bundle, build])
            await session.commit()

            removed = await _prune_unreferenced_cache_rows(session)

            assert removed == (1, 1, 1)
            assert await session.get(CalcReportArtifact, source.id) is not None
            assert await session.scalar(select(CalcExecutionBundle.id)) is None
        await engine.dispose()

    asyncio.run(scenario())
