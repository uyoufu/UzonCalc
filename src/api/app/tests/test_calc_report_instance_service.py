"""Service tests for execution-derived saved calculation instances."""

import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.controller.calc.calc_instance_dto import CalcInstanceCreateDTO
from app.db.models import (
    BaseModel,
    CalcExecution,
    CalcExecutionBundle,
    CalcReport,
    CalcReportArtifact,
    CalcReportCategory,
    CalcReportInstanceCategory,
    User,
    UserInputHistory,
)
from app.db.models.enums import ExecutionSourceType, ExecutionStatus, ExecutorType
from app.service import calc_report_instance_service


def test_create_instance_derives_provenance_and_copies_cached_result(
    tmp_path: Path, monkeypatch
):
    """Instance creation must trust persisted execution fields, not client paths."""

    async def run_test() -> None:
        """Build a normalized execution graph and assert the saved snapshot."""
        monkeypatch.chdir(tmp_path)
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(BaseModel.metadata.create_all)

            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            async with session_factory() as session:
                user = User(
                    username="owner",
                    password="hash",
                    salt="salt",
                    roles=["regular"],
                )
                session.add(user)
                await session.flush()
                report_category = CalcReportCategory(userId=user.id, name="reports")
                instance_category = CalcReportInstanceCategory(
                    userId=user.id, name="instances"
                )
                session.add_all([report_category, instance_category])
                await session.flush()
                source = CalcReportArtifact(
                    artifactKind=1,
                    contentHash="a" * 64,
                    storageKey="source",
                    manifest={},
                    fileCount=1,
                    totalSize=1,
                )
                instrumented = CalcReportArtifact(
                    artifactKind=2,
                    contentHash="b" * 64,
                    storageKey="instrumented",
                    manifest={},
                    fileCount=1,
                    totalSize=1,
                )
                session.add_all([source, instrumented])
                await session.flush()
                report = CalcReport(
                    userId=user.id,
                    categoryId=report_category.id,
                    name="demo",
                    workspaceArtifactId=source.id,
                )
                session.add(report)
                await session.flush()
                bundle = CalcExecutionBundle(
                    bundleHash="c" * 64,
                    runtimeFingerprint="runtime-1",
                    entrySourceArtifactId=source.id,
                    entryExecutionArtifactId=instrumented.id,
                    manifest={},
                )
                session.add(bundle)
                await session.flush()
                execution = CalcExecution(
                    userId=user.id,
                    reportId=report.id,
                    bundleId=bundle.id,
                    sourceType=ExecutionSourceType.WORKSPACE.value,
                    executorType=ExecutorType.LOCAL.value,
                    status=ExecutionStatus.SUCCEEDED.value,
                    resultPath="public/calcs/1/exec-1/result.html",
                )
                session.add(execution)
                await session.flush()
                session.add(
                    UserInputHistory(
                        executionId=execution.id,
                        defaults={"parameters": {"a": 1}},
                        inputHistory=[],
                    )
                )
                await session.commit()

                cache_dir = tmp_path / "data/public/calcs/1/exec-1"
                images_dir = cache_dir / "images"
                images_dir.mkdir(parents=True)
                (cache_dir / "result.html").write_text(
                    '<img src="images/image_1.png">', encoding="utf-8"
                )
                (images_dir / "image_1.png").write_bytes(b"image")
                request = CalcInstanceCreateDTO(
                    categoryOid=instance_category.oid,
                    executionId=execution.oid,
                    name="instance-a",
                    description="saved result",
                )

                result = await calc_report_instance_service.create_instance(
                    user.id, request, session
                )

                assert result.resultPath.startswith("public/calc-instances/1/")
                assert result.instanceOid in result.resultPath
                saved_html = tmp_path / "data" / result.resultPath
                assert saved_html.exists()
                assert (saved_html.parent / "images/image_1.png").exists()
                assert result.defaults == {"parameters": {"a": 1}}
                assert result.reportOid == report.oid
                assert result.bundleHash == f"sha256:{'c' * 64}"
        finally:
            await engine.dispose()

    asyncio.run(run_test())
