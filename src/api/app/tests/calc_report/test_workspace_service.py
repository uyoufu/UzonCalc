"""Tests for atomic calculation-report workspace saves."""

import asyncio
import json
from pathlib import Path

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.controller.calc.calc_workspace_dto import (
    WorkspaceCreateDTO,
    WorkspaceFileDTO,
    WorkspaceSaveDTO,
)
from app.controller.calc.calc_execution_dto import CalcExecutionStartDTO
from app.controller.calc.calc_state import (
    BuildStatus,
    ExecutionSourceType,
    WorkspaceFileSource,
)
from app.db.models import Base, CalcReport, CalcReportCategory, User
from app.exception.custom_exception import CustomException
from app.service.calc_report_workspace_service import get_workspace, save_workspace
from app.service.calc_execution_service import get_current_execution_step


def _run(coro):
    """Run one async service scenario from a synchronous pytest test."""
    return asyncio.run(coro)


async def _create_session_factory():
    """Create an isolated foreign-key-enabled SQLite database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        """Enable SQLite foreign keys for model-contract tests."""
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _snapshot(
    revision: int, *, source: WorkspaceFileSource = WorkspaceFileSource.UPLOAD
) -> WorkspaceSaveDTO:
    """Build a minimal complete workspace request."""
    return WorkspaceSaveDTO(
        workspaceRevision=revision,
        create=(
            WorkspaceCreateDTO(
                categoryOid="b" * 24,
                name="Beam report",
            )
            if revision == 0
            else None
        ),
        files=[
            WorkspaceFileDTO(path="calcbook.json", source=source),
            WorkspaceFileDTO(path="__init__.py", source=source),
            WorkspaceFileDTO(path="main.py", source=source),
        ],
    )


def test_first_save_creates_report_and_current_files_can_be_reused(
    tmp_path: Path, monkeypatch
) -> None:
    """First save should create the report and later snapshots may reuse bytes."""
    monkeypatch.chdir(tmp_path)

    async def scenario() -> None:
        """Execute the first-save and reuse workflow."""
        engine, factory = await _create_session_factory()
        async with factory() as session:
            user = User(
                oid="a" * 24,
                username="owner",
                password="hash",
                salt="salt",
                roles=["regular"],
            )
            session.add(user)
            await session.flush()
            session.add(
                CalcReportCategory(
                    oid="b" * 24,
                    userId=user.id,
                    name="Default",
                )
            )
            await session.commit()

            uploads = {
                "calcbook.json": json.dumps(
                    {"formatVersion": 2, "entryPath": "main.py"}
                ).encode(),
                "__init__.py": b"",
                "main.py": b"from uzoncalc import *\n",
            }
            first = await save_workspace(
                user.id, "c" * 24, _snapshot(0), uploads, session
            )
            reused = await save_workspace(
                user.id,
                "c" * 24,
                _snapshot(1, source=WorkspaceFileSource.CURRENT),
                {},
                session,
            )
            loaded = await get_workspace(user.id, "c" * 24, session)
            report = await session.scalar(
                select(CalcReport).where(CalcReport.oid == "c" * 24)
            )
            retained = await get_current_execution_step(
                session,
                user.id,
                CalcExecutionStartDTO(
                    reportOid="c" * 24,
                    source={"type": ExecutionSourceType.WORKSPACE},
                ),
            )

            assert first.workspaceRevision == 1
            assert reused.workspaceRevision == 2
            assert loaded.workspaceHash == first.workspaceHash
            assert loaded.buildStatus is BuildStatus.NOT_REQUESTED
            assert report is not None and report.workspaceArtifactId is None
            assert retained is None
        await engine.dispose()

    _run(scenario())


def test_direct_workspace_edit_is_reconciled_without_publishing_artifact(
    tmp_path: Path, monkeypatch
) -> None:
    """A direct file edit should advance mutable identity but remain unfrozen."""
    monkeypatch.chdir(tmp_path)

    async def scenario() -> None:
        """Save a workspace, edit its file directly, and reconcile metadata."""
        engine, factory = await _create_session_factory()
        async with factory() as session:
            user = User(
                oid="a" * 24,
                username="owner",
                password="hash",
                salt="salt",
                roles=["regular"],
            )
            session.add(user)
            await session.flush()
            session.add(
                CalcReportCategory(oid="b" * 24, userId=user.id, name="Default")
            )
            await session.commit()
            uploads = {
                "calcbook.json": b'{"formatVersion":2,"entryPath":"main.py"}',
                "__init__.py": b"",
                "main.py": b"x = 1\n",
            }
            first = await save_workspace(
                user.id, "c" * 24, _snapshot(0), uploads, session
            )
            workspace_file = (
                tmp_path
                / "data/calc-reports"
                / str(user.id)
                / ("c" * 24)
                / "workspace/main.py"
            )
            workspace_file.write_bytes(b"x = 2\n")

            reconciled = await get_workspace(user.id, "c" * 24, session)
            report = await session.scalar(
                select(CalcReport).where(CalcReport.oid == "c" * 24)
            )

            assert reconciled.workspaceRevision == first.workspaceRevision + 1
            assert reconciled.workspaceHash != first.workspaceHash
            assert report is not None and report.workspaceArtifactId is None
        await engine.dispose()

    _run(scenario())


def test_stale_workspace_revision_is_rejected(tmp_path: Path, monkeypatch) -> None:
    """A stale complete snapshot must not overwrite a newer workspace."""
    monkeypatch.chdir(tmp_path)

    async def scenario() -> None:
        """Create a report and attempt a stale second save."""
        engine, factory = await _create_session_factory()
        async with factory() as session:
            user = User(
                oid="a" * 24,
                username="owner",
                password="hash",
                salt="salt",
                roles=["regular"],
            )
            session.add(user)
            await session.flush()
            session.add(
                CalcReportCategory(oid="b" * 24, userId=user.id, name="Default")
            )
            await session.commit()
            uploads = {
                "calcbook.json": b'{"formatVersion":2,"entryPath":"main.py"}',
                "__init__.py": b"",
                "main.py": b"x = 1\n",
            }
            await save_workspace(user.id, "c" * 24, _snapshot(0), uploads, session)

            with pytest.raises(CustomException) as error:
                await save_workspace(
                    user.id,
                    "c" * 24,
                    WorkspaceSaveDTO(
                        workspaceRevision=0,
                        files=_snapshot(0).files,
                    ),
                    uploads,
                    session,
                )
            assert error.value.code == 409
            assert error.value.error_code == "WORKSPACE_REVISION_CONFLICT"
        await engine.dispose()

    _run(scenario())
