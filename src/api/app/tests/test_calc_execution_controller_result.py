"""Controller tests for the new bundle-backed execution response contract."""

import asyncio
import datetime

from app.controller.calc import calc_execution
from app.controller.calc.calc_execution_dto import CalcExecutionResDTO
from app.db.models.calc_execution import CalcExecution, CalcExecutionBundle
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.enums import ExecutionSourceType, ExecutionStatus, ExecutorType
from app.sandbox.core.backend_types import RuntimeDescriptor, SandboxBackendMode
from app.sandbox.core.execution_result import ExecutionResult
from app.service.calc_execution_service import ExecutionStep
from app.service.html_cache.html_cacher import HtmlContentPatchResult, HtmlUpdateType


class FakeHtmlCacher:
    """Return deterministic cache paths and patches without filesystem access."""

    async def cache_html(self, result, user_id, session) -> str:
        """Validate the internal result and return a stable public path."""
        assert result.executionId == "execution-oid"
        assert user_id == 1
        return "public/calcs/1/new.html"

    def build_content_patch_from_paths(
        self, last_html_path: str | None, html_path: str
    ) -> HtmlContentPatchResult:
        """Return a fixed partial patch for response-field verification."""
        assert last_html_path == "public/calcs/1/old.html"
        assert html_path == "public/calcs/1/new.html"
        return HtmlContentPatchResult(
            updateType=HtmlUpdateType.Partial,
            contentHtml="<p>new result</p>",
        )


def test_finalize_execution_step_builds_public_response(monkeypatch):
    """Finalization should expose immutable provenance and persist cache path."""

    async def record_result_path(session, execution_oid, user_id, result_path):
        """Capture the new cache path through the service boundary."""
        assert execution_oid == "execution-oid"
        assert user_id == 1
        assert result_path == "public/calcs/1/new.html"

    async def promote_successful_execution(session, execution_oid, user_id):
        """Verify successful finalization promotes the target slot."""
        assert execution_oid == "execution-oid"
        assert user_id == 1

    monkeypatch.setattr(calc_execution, "html_cacher", FakeHtmlCacher())
    monkeypatch.setattr(
        calc_execution.calc_execution_service,
        "record_result_path",
        record_result_path,
    )
    monkeypatch.setattr(
        calc_execution.calc_execution_service,
        "promote_successful_execution",
        promote_successful_execution,
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    execution = CalcExecution(
        oid="execution-oid",
        userId=1,
        reportId=1,
        bundleId=1,
        sourceType=ExecutionSourceType.WORKSPACE.value,
        executorType=ExecutorType.LOCAL.value,
        status=ExecutionStatus.SUCCEEDED.value,
        metrics={"backend": "in_process"},
        createdAt=now,
        completedAt=now,
    )
    report = CalcReport(
        oid="report-oid",
        userId=1,
        categoryId=1,
        name="demo",
    )
    source_artifact = CalcReportArtifact(
        contentHash="a" * 64,
        storageKey="source",
        artifactKind=1,
        manifest={},
        fileCount=1,
        totalSize=1,
    )
    execution_artifact = CalcReportArtifact(
        contentHash="b" * 64,
        storageKey="execution",
        artifactKind=2,
        manifest={},
        fileCount=1,
        totalSize=1,
    )
    bundle = CalcExecutionBundle(
        bundleHash="c" * 64,
        runtimeFingerprint="runtime-1",
        entrySourceArtifactId=1,
        entryExecutionArtifactId=2,
        manifest={},
    )
    runtime = RuntimeDescriptor(
        mode=SandboxBackendMode.IN_PROCESS,
        fingerprint="runtime-1",
        executor_type=ExecutorType.LOCAL,
    )
    step = ExecutionStep(
        execution=execution,
        result=ExecutionResult(
            executionId="backend-id",
            html="<html>raw</html>",
            isCompleted=True,
        ),
        report=report,
        source_artifact=source_artifact,
        execution_artifact=execution_artifact,
        bundle=bundle,
        runtime=runtime,
        resolved_version=None,
    )

    response = asyncio.run(
        calc_execution.finalize_execution_step(
            step, "public/calcs/1/old.html", 1, object()
        )
    )

    assert isinstance(response, CalcExecutionResDTO)
    assert response.sourceArtifactHash == f"sha256:{'a' * 64}"
    assert response.executionArtifactHash == f"sha256:{'b' * 64}"
    assert response.bundleHash == f"sha256:{'c' * 64}"
    assert response.htmlPath == "public/calcs/1/new.html"
    assert response.updateType == HtmlUpdateType.Partial
    assert response.htmlContentPatch == "<p>new result</p>"
