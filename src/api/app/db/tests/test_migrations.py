"""Tests for the rebuilt database models and Alembic migration."""

import asyncio
import io
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.migration import migrations_helper
from app.db.migration.migrations_helper import MigrationHelper
from app.db.models import Base, UserInputHistory

EXPECTED_BUSINESS_TABLES = {
    "calc_execution",
    "calc_execution_bundle",
    "calc_execution_bundle_component",
    "calc_execution_slot",
    "calc_report",
    "calc_report_artifact",
    "calc_report_artifact_build",
    "calc_report_category",
    "calc_report_dependency",
    "calc_report_dependency_selector",
    "calc_report_instance",
    "calc_report_instance_category",
    "calc_report_instance_share",
    "calc_report_origin",
    "calc_report_sync_source",
    "calc_report_share_department",
    "calc_report_share_link",
    "calc_report_share_recipient",
    "calc_report_version",
    "department",
    "department_user",
    "favorite_calc_reports",
    "input_cache",
    "system_settings",
    "tmp_files",
    "user_input_history",
    "user_settings",
    "users",
}


def _table_names(db_path: Path) -> set[str]:
    """Read table names from a SQLite database.

    Args:
        db_path: SQLite database path.

    Returns:
        Names of all tables in the database.
    """

    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            "select name from sqlite_master where type='table'"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        connection.close()


async def _upgrade_database(db_path: Path) -> None:
    """Upgrade a temporary SQLite database to the current head.

    Args:
        db_path: SQLite database path.
    """

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    try:
        await MigrationHelper().upgrade_to_head(engine)
    finally:
        await engine.dispose()


async def _downgrade_database(db_path: Path) -> None:
    """Downgrade a temporary SQLite database to the Alembic base.

    Args:
        db_path: SQLite database path.
    """

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    helper = MigrationHelper()

    def run_downgrade(connection: Any) -> None:
        """Run synchronous Alembic downgrade on an async bridge connection.

        Args:
            connection: Synchronous SQLAlchemy connection supplied by run_sync.
        """

        config = helper._make_config()
        config.attributes["connection"] = connection
        command.downgrade(config, "base")

    try:
        async with engine.begin() as connection:
            await connection.run_sync(run_downgrade)
    finally:
        await engine.dispose()


def _insert_entity(
    connection: sqlite3.Connection,
    table_name: str,
    oid_number: int,
    **values: Any,
) -> int:
    """Insert one entity row with shared identity columns.

    Args:
        connection: SQLite connection with foreign keys enabled.
        table_name: Trusted table name from this test module.
        oid_number: Integer converted to a unique 24-character OID.
        **values: Table-specific column values.

    Returns:
        Generated integer primary key.
    """

    row = {
        "oid": f"{oid_number:024x}",
        "createdAt": "2026-01-01T00:00:00+00:00",
        **values,
    }
    columns = ", ".join(f'"{column}"' for column in row)
    placeholders = ", ".join("?" for _ in row)
    cursor = connection.execute(
        f'insert into "{table_name}" ({columns}) values ({placeholders})',
        tuple(row.values()),
    )
    return int(cursor.lastrowid)


def test_models_use_one_metadata_with_expected_tables() -> None:
    """All models should share one metadata registry with no legacy tables."""

    assert set(Base.metadata.tables) == EXPECTED_BUSINESS_TABLES
    assert UserInputHistory.metadata is Base.metadata
    assert "calc_report_archive" not in Base.metadata.tables
    assert "published_version" not in Base.metadata.tables


def test_upgrade_to_head_creates_exact_sqlite_schema(tmp_path: Path) -> None:
    """A blank SQLite database should receive exactly the rebuilt schema."""

    db_path = tmp_path / "app.sqlite3"
    asyncio.run(_upgrade_database(db_path))

    assert _table_names(db_path) == EXPECTED_BUSINESS_TABLES | {"alembic_version"}

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        inspector = inspect(engine)
        latest_foreign_key = next(
            foreign_key
            for foreign_key in inspector.get_foreign_keys("calc_report")
            if foreign_key["name"] == "fk_calc_report_latest_version"
        )
        assert latest_foreign_key["constrained_columns"] == [
            "id",
            "latestVersionId",
        ]
        assert latest_foreign_key["referred_columns"] == ["reportId", "id"]

        selector_foreign_keys = {
            foreign_key["name"]
            for foreign_key in inspector.get_foreign_keys(
                "calc_report_dependency_selector"
            )
        }
        assert selector_foreign_keys == {
            "fk_dependency_selector_dependency_target",
            "fk_dependency_selector_target_version",
        }

        selector_indexes = {
            index["name"]: index
            for index in inspector.get_indexes("calc_report_dependency_selector")
        }
        assert selector_indexes["uq_dependency_selector_default"]["unique"] == 1

        with engine.connect() as connection:
            differences = compare_metadata(
                MigrationContext.configure(connection), Base.metadata
            )
        assert differences == []
    finally:
        engine.dispose()


def test_upgrade_is_idempotent_and_skips_current_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A current database should skip a second Alembic upgrade call."""

    db_path = tmp_path / "app.sqlite3"
    asyncio.run(_upgrade_database(db_path))
    expected_head = MigrationHelper().get_heads()[0]

    def fail_if_called(*args: Any, **kwargs: Any) -> None:
        """Fail if Alembic upgrade runs after reaching head.

        Args:
            *args: Ignored positional arguments.
            **kwargs: Ignored keyword arguments.

        Raises:
            AssertionError: Always, because this function must not be called.
        """

        raise AssertionError("Alembic upgrade should be skipped for current database")

    monkeypatch.setattr(migrations_helper.command, "upgrade", fail_if_called)
    asyncio.run(_upgrade_database(db_path))

    connection = sqlite3.connect(db_path)
    try:
        revision = connection.execute(
            "select version_num from alembic_version"
        ).fetchone()[0]
    finally:
        connection.close()

    assert revision == expected_head


def test_sqlite_downgrade_and_reupgrade_round_trip(tmp_path: Path) -> None:
    """SQLite should support upgrade, downgrade to base, and re-upgrade."""

    db_path = tmp_path / "app.sqlite3"
    asyncio.run(_upgrade_database(db_path))
    asyncio.run(_downgrade_database(db_path))

    assert _table_names(db_path) == {"alembic_version"}

    asyncio.run(_upgrade_database(db_path))
    assert _table_names(db_path) == EXPECTED_BUSINESS_TABLES | {"alembic_version"}


def test_sqlite_enforces_report_ownership_and_build_constraints(
    tmp_path: Path,
) -> None:
    """SQLite should reject cross-report latest pointers and invalid builds."""

    db_path = tmp_path / "app.sqlite3"
    asyncio.run(_upgrade_database(db_path))

    connection = sqlite3.connect(db_path)
    connection.execute("pragma foreign_keys = on")
    try:
        user_id = _insert_entity(
            connection,
            "users",
            1,
            username="owner",
            nickName=None,
            avatar=None,
            password="hash",
            salt="salt",
            status=1,
            roles=json.dumps(["regular"]),
        )
        artifact_id = _insert_entity(
            connection,
            "calc_report_artifact",
            2,
            artifactKind=1,
            contentHash="a" * 64,
            storageKey="artifacts/a",
            manifest=json.dumps({}),
            fileCount=1,
            totalSize=10,
            formatVersion=1,
        )
        category_id = _insert_entity(
            connection,
            "calc_report_category",
            3,
            userId=user_id,
            name="General",
            description=None,
            manualOrder=0,
            updatedAt="2026-01-01T00:00:00+00:00",
            deletedAt=None,
        )
        first_report_id = _insert_entity(
            connection,
            "calc_report",
            4,
            userId=user_id,
            categoryId=category_id,
            name="First",
            description=None,
            cover=None,
            entryPath="src/main.py",
            formatVersion=1,
            workspaceRevision=1,
            workspaceArtifactId=artifact_id,
            latestVersionId=None,
            updatedAt="2026-01-01T00:00:00+00:00",
            deletedAt=None,
        )
        second_report_id = _insert_entity(
            connection,
            "calc_report",
            5,
            userId=user_id,
            categoryId=category_id,
            name="Second",
            description=None,
            cover=None,
            entryPath="src/main.py",
            formatVersion=1,
            workspaceRevision=1,
            workspaceArtifactId=artifact_id,
            latestVersionId=None,
            updatedAt="2026-01-01T00:00:00+00:00",
            deletedAt=None,
        )
        version_id = _insert_entity(
            connection,
            "calc_report_version",
            6,
            reportId=first_report_id,
            sourceArtifactId=artifact_id,
            major=1,
            minor=0,
            patch=0,
            description=None,
            publishedByUserId=user_id,
        )

        connection.execute(
            'update calc_report set "latestVersionId" = ? where id = ?',
            (version_id, first_report_id),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                'update calc_report set "latestVersionId" = ? where id = ?',
                (version_id, second_report_id),
            )

        with pytest.raises(sqlite3.IntegrityError):
            _insert_entity(
                connection,
                "calc_report_artifact_build",
                7,
                sourceArtifactId=artifact_id,
                runtimeFingerprint="runtime-1",
                outputArtifactId=None,
                status=2,
                diagnostics=None,
                attemptCount=1,
                leaseOwner=None,
                leaseExpiresAt=None,
                startedAt=None,
                completedAt=None,
                updatedAt="2026-01-01T00:00:00+00:00",
            )

        dependency_id = _insert_entity(
            connection,
            "calc_report_dependency",
            8,
            reportId=second_report_id,
            targetReportId=first_report_id,
            alias="first",
            updatedAt="2026-01-01T00:00:00+00:00",
        )
        with pytest.raises(sqlite3.IntegrityError):
            _insert_entity(
                connection,
                "calc_report_dependency_selector",
                9,
                dependencyId=dependency_id,
                targetReportId=second_report_id,
                selectorKey="v_1_0_0",
                targetVersionId=version_id,
                isDefault=True,
            )

        bundle_id = _insert_entity(
            connection,
            "calc_execution_bundle",
            10,
            bundleHash="b" * 64,
            runtimeFingerprint="runtime-1",
            runtimeImageDigest=None,
            entrySourceArtifactId=artifact_id,
            entryExecutionArtifactId=artifact_id,
            manifest=json.dumps({}),
            formatVersion=1,
        )
        with pytest.raises(sqlite3.IntegrityError):
            _insert_entity(
                connection,
                "calc_execution",
                11,
                userId=user_id,
                reportId=second_report_id,
                bundleId=bundle_id,
                sourceType=3,
                resolvedVersionId=version_id,
                executorType=1,
                status=0,
                sandboxExecutionId=None,
                executorNodeId=None,
                startedAt=None,
                lastActiveAt=None,
                expiresAt=None,
                completedAt=None,
                resultPath=None,
                errorCode=None,
                errorMessage=None,
                metrics=None,
            )

        instance_category_id = _insert_entity(
            connection,
            "calc_report_instance_category",
            12,
            userId=user_id,
            name="Saved",
            description=None,
            sortOrder=0,
            updatedAt="2026-01-01T00:00:00+00:00",
            deletedAt=None,
        )
        with pytest.raises(sqlite3.IntegrityError):
            _insert_entity(
                connection,
                "calc_report_instance",
                13,
                userId=user_id,
                categoryId=instance_category_id,
                reportId=second_report_id,
                sourceVersionId=version_id,
                bundleId=bundle_id,
                reportName="Second",
                name="Invalid source",
                description=None,
                defaults=json.dumps({}),
                inputWindows=json.dumps([]),
                resultPath="results/invalid.html",
                revision=1,
                updatedAt="2026-01-01T00:00:00+00:00",
                deletedAt=None,
            )
    finally:
        connection.close()


def test_postgresql_offline_ddl_can_be_generated() -> None:
    """The initial migration should render valid PostgreSQL-oriented DDL offline."""

    helper = MigrationHelper()
    config = helper._make_config("postgresql+asyncpg://user:pass@localhost/db")
    output = io.StringIO()
    config.output_buffer = output

    command.upgrade(config, "head", sql=True)

    ddl = output.getvalue()
    assert "CREATE TABLE calc_report_artifact" in ddl
    assert "fk_calc_report_latest_version" in ddl
    assert "CREATE UNIQUE INDEX uq_dependency_selector_default" in ddl


def test_upgrade_fails_for_unversioned_legacy_database(tmp_path: Path) -> None:
    """An unversioned database with legacy tables should fail strictly."""

    db_path = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("create table users (id integer primary key)")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(Exception):
        asyncio.run(_upgrade_database(db_path))
