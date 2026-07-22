"""Publishing, latest-pointer, and workspace-restore services."""

import ast
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_state import ReservedDependencySelectorKey
from app.controller.calc.calc_report_dto import (
    CalcReportVersionCreateDTO,
    CalcReportVersionResDTO,
)
from app.controller.calc.calc_workspace_dto import WorkspaceResDTO
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import ArtifactKind
from app.exception.custom_exception import raise_ex
from app.service.calc_report_artifact_service import artifact_store, public_hash
from app.service.calc_report_workspace_service import (
    ensure_workspace_artifact,
    get_owned_report,
    parse_version_name,
    require_editable_report,
    restore_workspace_artifact,
)


async def publish_version(
    user_id: int,
    report_oid: str,
    request: CalcReportVersionCreateDTO,
    session: AsyncSession,
) -> CalcReportVersionResDTO:
    """Publish the current SOURCE after static validation without instrumentation."""
    report = await get_owned_report(user_id, report_oid, session)
    require_editable_report(report)
    try:
        major, minor, patch = parse_version_name(request.versionName)
    except ValueError as error:
        raise_ex(str(error), code=400, error_code=CalcErrorCode.WORKSPACE_INVALID)
    duplicate = await session.scalar(
        select(CalcReportVersion.id).where(
            CalcReportVersion.reportId == report.id,
            CalcReportVersion.major == major,
            CalcReportVersion.minor == minor,
            CalcReportVersion.patch == patch,
        )
    )
    if duplicate is not None:
        raise_ex(
            "Report version already exists",
            code=409,
            error_code=CalcErrorCode.VERSION_ALREADY_EXISTS,
        )
    artifact = await ensure_workspace_artifact(user_id, report, session)
    if artifact.artifactKind != ArtifactKind.SOURCE.value:
        raise_ex("Workspace SOURCE artifact not found", code=500)
    _validate_publishable_source(artifact)
    version = CalcReportVersion(
        reportId=report.id,
        sourceArtifactId=artifact.id,
        major=major,
        minor=minor,
        patch=patch,
        description=request.description,
        publishedByUserId=user_id,
    )
    session.add(version)
    await session.flush()
    report.latestVersionId = version.id
    await session.commit()
    await session.refresh(version)
    return _version_response(version, artifact, is_latest=True)


async def list_versions(
    user_id: int, report_oid: str, session: AsyncSession
) -> list[CalcReportVersionResDTO]:
    """List every immutable version for an owned report."""
    report = await get_owned_report(user_id, report_oid, session)
    versions = (
        await session.scalars(
            select(CalcReportVersion)
            .where(CalcReportVersion.reportId == report.id)
            .order_by(
                CalcReportVersion.major.desc(),
                CalcReportVersion.minor.desc(),
                CalcReportVersion.patch.desc(),
            )
        )
    ).all()
    responses = []
    for version in versions:
        artifact = await session.get(CalcReportArtifact, version.sourceArtifactId)
        if artifact is not None:
            responses.append(
                _version_response(
                    version, artifact, is_latest=version.id == report.latestVersionId
                )
            )
    return responses


async def set_latest_version(
    user_id: int,
    report_oid: str,
    version_name: str,
    session: AsyncSession,
) -> CalcReportVersionResDTO:
    """Move only the authoritative latest pointer to an existing version."""
    report = await get_owned_report(user_id, report_oid, session)
    require_editable_report(report)
    version = await _get_version(report, version_name, session)
    report.latestVersionId = version.id
    await session.commit()
    artifact = await session.get(CalcReportArtifact, version.sourceArtifactId)
    if artifact is None:
        raise_ex("Version artifact not found", code=500)
    return _version_response(version, artifact, is_latest=True)


async def restore_version_workspace(
    user_id: int,
    report_oid: str,
    version_name: str,
    session: AsyncSession,
) -> WorkspaceResDTO:
    """Restore version content into workspace without moving latest."""
    report = await get_owned_report(user_id, report_oid, session)
    version = await _get_version(report, version_name, session)
    artifact = await session.get(CalcReportArtifact, version.sourceArtifactId)
    if artifact is None:
        raise_ex("Version artifact not found", code=500)
    return await restore_workspace_artifact(user_id, report, artifact, session)


def _validate_publishable_source(artifact: CalcReportArtifact) -> None:
    """Parse Python files and validate declared static calcdeps imports."""
    declarations = {
        dependency["alias"]: {
            selector["selectorKey"] for selector in dependency.get("selectors", [])
        }
        for dependency in artifact.manifest.get("dependencies", [])
    }
    for artifact_file in artifact_store.read_all(artifact.storageKey):
        if not artifact_file.path.endswith(".py"):
            continue
        try:
            source = artifact_file.content.decode("utf-8")
            tree = ast.parse(source, filename=artifact_file.path)
            compile(tree, artifact_file.path, "exec")
        except (UnicodeDecodeError, SyntaxError) as error:
            raise_ex(
                "Workspace Python source is invalid",
                code=422,
                data={
                    "path": artifact_file.path,
                    "line": getattr(error, "lineno", None),
                    "message": str(error),
                },
                error_code=CalcErrorCode.WORKSPACE_INVALID,
            )
        for node in ast.walk(tree):
            module_name = None
            if isinstance(node, ast.Import):
                for imported in node.names:
                    if imported.name == "calcdeps" or imported.name.startswith(
                        "calcdeps."
                    ):
                        _validate_calcdeps_module(imported.name, declarations)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
            if module_name == "calcdeps" or (
                module_name and module_name.startswith("calcdeps.")
            ):
                _validate_calcdeps_module(module_name, declarations)
            if isinstance(node, ast.Call) and _is_dynamic_import_call(node):
                raise_ex(
                    "Dynamic calcdeps imports are not supported",
                    code=422,
                    data={"path": artifact_file.path, "line": node.lineno},
                    error_code=CalcErrorCode.DEPENDENCY_INVALID,
                )


def _validate_calcdeps_module(
    module_name: str, declarations: dict[str, set[str]]
) -> None:
    """Validate one public calcdeps module against the SOURCE declaration."""
    parts = module_name.split(".")
    if len(parts) < 2 or parts[1] not in declarations:
        raise_ex(
            "calcdeps import uses an undeclared dependency alias",
            code=422,
            data={"module": module_name},
            error_code=CalcErrorCode.DEPENDENCY_INVALID,
        )
    if len(parts) >= 3 and (
        parts[2] == ReservedDependencySelectorKey.LATEST or parts[2].startswith("v_")
    ):
        if parts[2] not in declarations[parts[1]]:
            raise_ex(
                "calcdeps import uses an undeclared selector",
                code=422,
                data={"module": module_name},
                error_code=CalcErrorCode.DEPENDENCY_INVALID,
            )


def _is_dynamic_import_call(node: ast.Call) -> bool:
    """Return whether a call dynamically loads the reserved calcdeps namespace."""
    function_name = None
    if isinstance(node.func, ast.Name):
        function_name = node.func.id
    elif isinstance(node.func, ast.Attribute):
        function_name = node.func.attr
    if function_name not in {"__import__", "import_module"} or not node.args:
        return False
    argument = node.args[0]
    return not isinstance(argument, ast.Constant) or (
        isinstance(argument.value, str) and argument.value.startswith("calcdeps")
    )


async def _get_version(
    report: CalcReport, version_name: str, session: AsyncSession
) -> CalcReportVersion:
    """Load one report-owned version by strict semantic name."""
    try:
        major, minor, patch = parse_version_name(version_name)
    except ValueError as error:
        raise_ex(str(error), code=400, error_code=CalcErrorCode.VERSION_NOT_FOUND)
    version = await session.scalar(
        select(CalcReportVersion).where(
            CalcReportVersion.reportId == report.id,
            CalcReportVersion.major == major,
            CalcReportVersion.minor == minor,
            CalcReportVersion.patch == patch,
        )
    )
    if version is None:
        raise_ex(
            "Report version not found",
            code=404,
            error_code=CalcErrorCode.VERSION_NOT_FOUND,
        )
    return cast(CalcReportVersion, version)


def _version_response(
    version: CalcReportVersion,
    artifact: CalcReportArtifact,
    *,
    is_latest: bool,
) -> CalcReportVersionResDTO:
    """Convert version/artifact models into the public immutable DTO."""
    version_name = f"{version.major}.{version.minor}.{version.patch}"
    return CalcReportVersionResDTO(
        versionOid=version.oid,
        versionName=version_name,
        importSegment=f"v_{version.major}_{version.minor}_{version.patch}",
        sourceArtifactHash=public_hash(artifact.contentHash),
        description=version.description,
        isLatest=is_latest,
        createdAt=version.createdAt,
    )
