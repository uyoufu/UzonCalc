"""Regression tests for split count/items pagination contracts."""

import asyncio
import datetime

import pytest
from fastapi import FastAPI
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.controller.calc import calc_execution, calc_report, calc_report_instance
from app.controller.calc.calc_instance_dto import CalcInstanceListFilterDTO
from app.controller.calc.calc_report_dto import CalcReportListFilterDTO
from app.controller.dto_base import PaginationDTO
from app.db.models import (
    BaseModel,
    CalcExecution,
    CalcExecutionBundle,
    CalcReport,
    CalcReportArtifact,
    CalcReportCategory,
    CalcReportInstance,
    CalcReportInstanceCategory,
    User,
)
from app.db.models.enums import ExecutionSourceType, ExecutionStatus, ExecutorType
from app.service import (
    calc_execution_service,
    calc_report_instance_service,
    calc_report_service,
)


def test_pagination_dto_validates_public_query_bounds() -> None:
    """PaginationDTO should preserve the previous API range constraints."""
    assert PaginationDTO(skip=0, limit=100).limit == 100
    with pytest.raises(ValidationError):
        PaginationDTO(skip=-1)
    with pytest.raises(ValidationError):
        PaginationDTO(limit=0)
    with pytest.raises(ValidationError):
        PaginationDTO(limit=101)


def test_calc_list_routers_expose_static_count_and_items_paths() -> None:
    """Static pagination routes must be registered ahead of object routes."""
    routers = [calc_report.router, calc_report_instance.router, calc_execution.router]
    for router in routers:
        get_paths = [
            route.path
            for route in router.routes
            if "GET" in getattr(route, "methods", set())
        ]
        assert f"{router.prefix}/count" in get_paths
        assert f"{router.prefix}/items" in get_paths
        assert get_paths.index(f"{router.prefix}/count") < next(
            index for index, path in enumerate(get_paths) if "{" in path
        )


def test_calc_list_openapi_reuses_pagination_dto_on_items_only() -> None:
    """OpenAPI should expose filters on both routes and pagination only on items."""
    app = FastAPI()
    for router in [
        calc_report.router,
        calc_report_instance.router,
        calc_execution.router,
    ]:
        app.include_router(router)
    schema_paths = app.openapi()["paths"]

    def parameter_names(path: str) -> list[str]:
        """Return generated GET query parameter names for one route."""
        return [
            parameter["name"]
            for parameter in schema_paths[path]["get"].get("parameters", [])
        ]

    assert parameter_names("/v1/calc-report/count") == ["categoryOid", "query"]
    assert parameter_names("/v1/calc-report/items") == [
        "categoryOid",
        "query",
        "skip",
        "limit",
        "sortBy",
        "descending",
    ]
    assert parameter_names("/v1/calc-report-instance/count") == ["categoryOid", "query"]
    assert parameter_names("/v1/calc-report-instance/items")[-4:] == [
        "skip",
        "limit",
        "sortBy",
        "descending",
    ]
    assert parameter_names("/v1/calc/execution/count") == []
    assert parameter_names("/v1/calc/execution/items") == [
        "skip",
        "limit",
        "sortBy",
        "descending",
    ]


def test_pagination_services_split_counts_from_sorted_items() -> None:
    """Count and items services should share filters but query independently."""

    async def run_test() -> None:
        """Create a normalized graph and verify each paginated resource."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(BaseModel.metadata.create_all)
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            async with session_factory() as session:
                user = User(
                    username="pagination-owner",
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
                    storageKey="pagination-source",
                    manifest={},
                    fileCount=1,
                    totalSize=1,
                )
                executable = CalcReportArtifact(
                    artifactKind=2,
                    contentHash="b" * 64,
                    storageKey="pagination-executable",
                    manifest={},
                    fileCount=1,
                    totalSize=1,
                )
                session.add_all([source, executable])
                await session.flush()
                older = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
                newer = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
                alpha_report = CalcReport(
                    userId=user.id,
                    categoryId=report_category.id,
                    name="Alpha report",
                    description="bridge",
                    createdAt=older,
                    updatedAt=older,
                )
                beta_report = CalcReport(
                    userId=user.id,
                    categoryId=report_category.id,
                    name="Beta report",
                    description="beam",
                    createdAt=newer,
                    updatedAt=newer,
                )
                session.add_all([alpha_report, beta_report])
                await session.flush()
                bundle = CalcExecutionBundle(
                    bundleHash="c" * 64,
                    runtimeFingerprint="pagination-runtime",
                    entrySourceArtifactId=source.id,
                    entryExecutionArtifactId=executable.id,
                    manifest={},
                )
                session.add(bundle)
                await session.flush()
                alpha_instance = CalcReportInstance(
                    userId=user.id,
                    categoryId=instance_category.id,
                    reportId=alpha_report.id,
                    bundleId=bundle.id,
                    reportName=alpha_report.name,
                    name="Alpha instance",
                    defaults={},
                    resultPath="alpha.html",
                    createdAt=older,
                    updatedAt=older,
                )
                beta_instance = CalcReportInstance(
                    userId=user.id,
                    categoryId=instance_category.id,
                    reportId=beta_report.id,
                    bundleId=bundle.id,
                    reportName=beta_report.name,
                    name="Beta instance",
                    defaults={},
                    resultPath="beta.html",
                    createdAt=newer,
                    updatedAt=newer,
                )
                first_execution = CalcExecution(
                    userId=user.id,
                    reportId=alpha_report.id,
                    bundleId=bundle.id,
                    sourceType=ExecutionSourceType.WORKSPACE.value,
                    executorType=ExecutorType.LOCAL.value,
                    status=ExecutionStatus.SUCCEEDED.value,
                    createdAt=older,
                )
                second_execution = CalcExecution(
                    userId=user.id,
                    reportId=beta_report.id,
                    bundleId=bundle.id,
                    sourceType=ExecutionSourceType.WORKSPACE.value,
                    executorType=ExecutorType.LOCAL.value,
                    status=ExecutionStatus.FAILED.value,
                    createdAt=newer,
                )
                session.add_all(
                    [
                        alpha_instance,
                        beta_instance,
                        first_execution,
                        second_execution,
                    ]
                )
                await session.commit()

                report_filter = CalcReportListFilterDTO(
                    categoryOid=report_category.oid, query="report"
                )
                assert (
                    await calc_report_service.count_reports(
                        user.id, report_filter, session
                    )
                    == 2
                )
                report_items = await calc_report_service.list_reports(
                    user.id,
                    report_filter,
                    PaginationDTO(skip=0, limit=1, sortBy="unknown", descending=True),
                    session,
                )
                assert [report.name for report in report_items] == ["Beta report"]

                instance_filter = CalcInstanceListFilterDTO(
                    categoryOid=instance_category.oid, query="Alpha"
                )
                assert (
                    await calc_report_instance_service.count_instances(
                        user.id, instance_filter, session
                    )
                    == 1
                )
                instance_items = await calc_report_instance_service.list_instances(
                    user.id,
                    instance_filter,
                    PaginationDTO(skip=0, limit=10, sortBy="name", descending=False),
                    session,
                )
                assert [instance.name for instance in instance_items] == [
                    "Alpha instance"
                ]

                assert (
                    await calc_execution_service.count_executions(session, user.id) == 2
                )
                execution_oids = await calc_execution_service.list_execution_oids(
                    session,
                    user.id,
                    PaginationDTO(
                        skip=0, limit=1, sortBy="createdAt", descending=False
                    ),
                )
                assert execution_oids == [first_execution.oid]
        finally:
            await engine.dispose()

    asyncio.run(run_test())
