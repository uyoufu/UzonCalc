"""Integration tests for approved share dependency-closure imports."""

import asyncio
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.controller.calc.calc_share_dto import ShareImportDTO, ShareLinkCreateDTO
from app.db.models import (
    BaseModel,
    CalcReport,
    CalcReportArtifact,
    CalcReportCategory,
    CalcReportDependency,
    CalcReportVersion,
    User,
)
from app.db.models.enums import ArtifactKind, VersionReviewStatus
from app.service import calc_report_share_service
from app.service.calc_report_artifact_service import ArtifactFile, artifact_store
from app.service.calc_report_workspace_service import _get_or_create_source_artifact
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
                session.add_all([owner, receiver])
                await session.flush()
                owner_category = CalcReportCategory(userId=owner.id, name="owner")
                receiver_category = CalcReportCategory(
                    userId=receiver.id, name="receiver"
                )
                session.add_all([owner_category, receiver_category])
                await session.flush()
                dependency_report = CalcReport(
                    userId=owner.id, categoryId=owner_category.id, name="dependency"
                )
                root_report = CalcReport(
                    userId=owner.id, categoryId=owner_category.id, name="root"
                )
                session.add_all([dependency_report, root_report])
                await session.flush()

                dependency_versions = []
                for patch in (0, 1):
                    published = artifact_store.publish_source(
                        [
                            ArtifactFile(
                                "calcbook.json",
                                b'{"formatVersion":1,"entryPath":"src/main.py"}',
                            ),
                            ArtifactFile("src/main.py", f"VALUE = {patch}\n".encode()),
                        ],
                        {"formatVersion": 1, "entryPath": "src/main.py"},
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
                        reviewStatus=VersionReviewStatus.APPROVED.value,
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
                            b'{"formatVersion":1,"entryPath":"src/main.py"}',
                        ),
                        ArtifactFile(
                            "src/main.py",
                            b"from calcdeps.dependency.api import VALUE\n",
                        ),
                    ],
                    {"formatVersion": 1, "entryPath": "src/main.py"},
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
                    reviewStatus=VersionReviewStatus.APPROVED.value,
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
                imported = await calc_report_share_service.import_share(
                    receiver.id,
                    share.token or "",
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
        finally:
            await engine.dispose()

    asyncio.run(run_test())
