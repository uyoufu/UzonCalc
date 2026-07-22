"""Integration tests for approved share dependency-closure imports."""

import asyncio
from pathlib import Path
from unittest.mock import Mock

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.controller.calc.calc_share_dto import ShareImportDTO, ShareLinkCreateDTO
from app.db.models import (
    BaseModel,
    CalcReport,
    CalcReportArtifact,
    CalcReportCategory,
    CalcReportDependency,
    CalcReportShareLink,
    CalcReportVersion,
    User,
)
from app.db.models.enums import ArtifactKind
from app.service import calc_report_archive_service, calc_report_share_service
from uzoncalc.cli_core import cli_archive_runtime
from uzoncalc.cli_core.cli_archive import create_uzc_archive
from app.service.calc_report_artifact_service import ArtifactFile, artifact_store
from app.service.calc_report_workspace_service import _get_or_create_source_artifact
from app.service.secret_storage_service import decrypt_persisted_secret
from config import app_config


def test_share_import_rebuilds_multi_version_dependency_under_receiver_ownership(
    tmp_path: Path, monkeypatch
) -> None:
    """One imported dependency report should retain every selected approved version."""

    async def run_test() -> None:
        """Create an approved graph, import it, and inspect rewritten relationships."""
        monkeypatch.setattr(artifact_store, "root", tmp_path / "artifacts")
        monkeypatch.setattr(
            type(app_config),
            "calc_report_reports_root",
            property(lambda _self: str(tmp_path / "reports")),
        )
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(BaseModel.metadata.create_all)
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            async with session_factory() as session:
                owner = User(
                    username="owner", password="hash", salt="salt", roles=["regular"]
                )
                receiver = User(
                    username="receiver",
                    password="hash",
                    salt="salt",
                    roles=["regular"],
                )
                archive_receiver = User(
                    username="archive-receiver",
                    password="hash",
                    salt="salt",
                    roles=["regular"],
                )
                session.add_all([owner, receiver, archive_receiver])
                await session.flush()
                owner_category = CalcReportCategory(userId=owner.id, name="owner")
                receiver_category = CalcReportCategory(
                    userId=receiver.id, name="receiver"
                )
                archive_category = CalcReportCategory(
                    userId=archive_receiver.id, name="archive-receiver"
                )
                session.add_all([owner_category, receiver_category, archive_category])
                await session.flush()
                dependency_report = CalcReport(
                    userId=owner.id, categoryId=owner_category.id, name="dependency"
                )
                root_report = CalcReport(
                    userId=owner.id,
                    categoryId=owner_category.id,
                    name="root",
                    description="root report description",
                )
                session.add_all([dependency_report, root_report])
                await session.flush()

                dependency_versions = []
                for patch in (0, 1):
                    published = artifact_store.publish_source(
                        [
                            ArtifactFile(
                                "calcbook.json",
                                b'{"formatVersion":2,"entryPath":"main.py"}',
                            ),
                            ArtifactFile("__init__.py", b""),
                            ArtifactFile("main.py", f"VALUE = {patch}\n".encode()),
                            ArtifactFile("api.py", f"VALUE = {patch}\n".encode()),
                        ],
                        {"formatVersion": 2, "entryPath": "main.py"},
                        [],
                    )
                    artifact = await _get_or_create_source_artifact(published, session)
                    version = CalcReportVersion(
                        reportId=dependency_report.id,
                        sourceArtifactId=artifact.id,
                        major=1,
                        minor=0,
                        patch=patch,
                        publishedByUserId=owner.id,
                    )
                    session.add(version)
                    await session.flush()
                    dependency_versions.append((version, artifact))
                dependency_report.workspaceArtifactId = dependency_versions[1][1].id
                dependency_report.latestVersionId = dependency_versions[1][0].id

                declarations = [
                    {
                        "alias": "dependency",
                        "targetReportOid": dependency_report.oid,
                        "selectors": [
                            {
                                "selectorKey": "latest",
                                "versionName": None,
                                "isDefault": True,
                            },
                            {
                                "selectorKey": "v_1_0_0",
                                "versionName": "1.0.0",
                                "isDefault": False,
                            },
                        ],
                    }
                ]
                root_published = artifact_store.publish_source(
                    [
                        ArtifactFile(
                            "calcbook.json",
                            b'{"formatVersion":2,"entryPath":"main.py"}',
                        ),
                        ArtifactFile("__init__.py", b""),
                        ArtifactFile(
                            "main.py",
                            b"from calcdeps.dependency.api import VALUE\n"
                            b"from uzoncalc import uzon_calc\n\n"
                            b"@uzon_calc()\n"
                            b"async def sheet():\n"
                            b"    return VALUE\n",
                        ),
                    ],
                    {"formatVersion": 2, "entryPath": "main.py"},
                    declarations,
                )
                root_artifact = await _get_or_create_source_artifact(
                    root_published, session
                )
                root_version = CalcReportVersion(
                    reportId=root_report.id,
                    sourceArtifactId=root_artifact.id,
                    major=2,
                    minor=0,
                    patch=0,
                    publishedByUserId=owner.id,
                )
                session.add(root_version)
                await session.flush()
                root_report.workspaceArtifactId = root_artifact.id
                root_report.latestVersionId = root_version.id
                await session.commit()

                share = await calc_report_share_service.create_share_link(
                    owner.id,
                    root_report.oid,
                    ShareLinkCreateDTO(versionName="2.0.0"),
                    session,
                )
                updated_share = await calc_report_share_service.update_share_link(
                    owner.id,
                    share.shareOid,
                    ShareLinkCreateDTO(
                        versionName="2.0.0", canEdit=True, note="review copy"
                    ),
                    session,
                )
                listed_shares = await calc_report_share_service.list_share_links(
                    owner.id, root_report.oid, session
                )
                stored_share = await session.scalar(
                    select(CalcReportShareLink).where(
                        CalcReportShareLink.oid == share.shareOid
                    )
                )
                assert stored_share is not None
                assert stored_share.tokenCiphertext != share.token
                assert decrypt_persisted_secret(stored_share.tokenCiphertext) == share.token
                assert updated_share.token == share.token
                assert updated_share.canEdit is True
                assert updated_share.note == "review copy"
                assert listed_shares[0].token == share.token
                assert listed_shares[0].note == "review copy"
                imported = await calc_report_share_service.import_share(
                    receiver.id,
                    share.token,
                    ShareImportDTO(categoryOid=receiver_category.oid),
                    session,
                )

                assert imported.importedReportCount == 2
                imported_root = await session.scalar(
                    select(CalcReport).where(CalcReport.oid == imported.reportOid)
                )
                dependency = await session.scalar(
                    select(CalcReportDependency).where(
                        CalcReportDependency.reportId == imported_root.id
                    )
                )
                imported_target = await session.get(
                    CalcReport, dependency.targetReportId
                )
                version_count = await session.scalar(
                    select(func.count(CalcReportVersion.id)).where(
                        CalcReportVersion.reportId == imported_target.id
                    )
                )
                assert version_count == 2
                assert imported_target.userId == receiver.id
                imported_artifact = await session.get(
                    CalcReportArtifact, imported_root.workspaceArtifactId
                )
                assert (
                    imported_artifact.manifest["dependencies"][0]["targetReportOid"]
                    == imported_target.oid
                )
                assert imported_artifact.artifactKind == ArtifactKind.SOURCE.value

                thumbnail_renderer = Mock(
                    wraps=calc_report_archive_service.render_workspace_archive_thumbnail
                )
                monkeypatch.setattr(
                    calc_report_archive_service,
                    "render_workspace_archive_thumbnail",
                    thumbnail_renderer,
                )
                exported = await calc_report_archive_service.export_version_closure(
                    root_report,
                    root_version,
                    can_edit=False,
                    can_share=True,
                    session=session,
                )
                assert thumbnail_renderer.call_args.kwargs == {
                    "title": "root",
                    "description": "root report description",
                }
                try:
                    selected_entries = []
                    monkeypatch.setattr(
                        cli_archive_runtime, "view", selected_entries.append
                    )
                    cli_archive_runtime.run_workspace_archive(exported.path)
                    assert [entry.__name__ for entry in selected_entries] == ["sheet"]
                    archive_import = (
                        await calc_report_archive_service.import_archive_closure(
                            archive_receiver.id,
                            ShareImportDTO(categoryOid=archive_category.oid),
                            exported.path.read_bytes(),
                            session,
                        )
                    )
                finally:
                    calc_report_archive_service.remove_exported_archive(exported)
                archive_root = await session.scalar(
                    select(CalcReport).where(CalcReport.oid == archive_import.reportOid)
                )
                archive_dependency = await session.scalar(
                    select(CalcReportDependency).where(
                        CalcReportDependency.reportId == archive_root.id
                    )
                )
                archive_target = await session.get(
                    CalcReport, archive_dependency.targetReportId
                )
                assert archive_import.importedReportCount == 2
                assert archive_root.canEdit is False
                assert archive_root.canShare is True
                assert archive_target.userId == archive_receiver.id

                script_path = tmp_path / "standalone.py"
                script_path.write_text(
                    "from uzoncalc import uzon_calc\n\n"
                    "@uzon_calc()\n"
                    "async def sheet():\n"
                    "    return 1\n",
                    encoding="utf-8",
                )
                cli_archive_path = create_uzc_archive(
                    script_path, tmp_path / "standalone.png"
                )
                cli_import = await calc_report_archive_service.import_archive_closure(
                    archive_receiver.id,
                    ShareImportDTO(
                        categoryOid=archive_category.oid, name="CLI imported"
                    ),
                    cli_archive_path.read_bytes(),
                    session,
                )
                cli_report = await session.scalar(
                    select(CalcReport).where(CalcReport.oid == cli_import.reportOid)
                )
                assert cli_import.importedReportCount == 1
                assert cli_report.name == "CLI imported"
                assert cli_report.entryPath == "standalone.py"
        finally:
            await engine.dispose()

    asyncio.run(run_test())
