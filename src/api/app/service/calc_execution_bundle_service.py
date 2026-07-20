"""Resolve immutable dependency closures and assemble execution bundles."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_state import (
    ExecutionSourceType as ApiExecutionSourceType,
    ReservedDependencySelectorKey,
)
from app.db.models.calc_execution import (
    CalcExecutionBundle,
    CalcExecutionBundleComponent,
)
from app.db.models.calc_report import CalcReport
from app.db.models.calc_report_artifact import CalcReportArtifact
from app.db.models.calc_report_version import CalcReportVersion
from app.db.models.enums import ExecutionSourceType
from app.exception.custom_exception import raise_ex
from app.sandbox.core.backend_types import PreparedExecutionBundle, RuntimeDescriptor
from app.service.calc_report_artifact_service import artifact_store
from app.service.calc_report_build_service import ensure_instrumented_artifact
from app.service.calc_report_workspace_service import (
    get_owned_report,
    parse_version_name,
)
from config import app_config


@dataclass(frozen=True)
class ResolvedExecutionSource:
    """Describe the entry SOURCE selected by one public execution request."""

    report: CalcReport
    source_artifact: CalcReportArtifact
    source_type: ExecutionSourceType
    resolved_version: CalcReportVersion | None


@dataclass(frozen=True)
class _ResolvedComponent:
    """Hold one database component and its deterministic bundle mount identity."""

    component_key: str
    scope_key: str
    alias: str | None
    selector_key: str | None
    source_artifact: CalcReportArtifact
    execution_artifact: CalcReportArtifact
    is_entry: bool


async def resolve_execution_source(
    user_id: int,
    report_oid: str,
    source_type: ApiExecutionSourceType,
    version_name: str | None,
    session: AsyncSession,
) -> ResolvedExecutionSource:
    """Resolve workspace/latest/version into one explicit immutable SOURCE."""
    report = await get_owned_report(user_id, report_oid, session)
    resolved_type = ExecutionSourceType[source_type.name]
    version = None
    artifact_id = report.workspaceArtifactId
    if resolved_type is ExecutionSourceType.LATEST:
        if report.latestVersionId is None:
            raise_ex("Report has no latest published version", code=409)
        version = await session.get(CalcReportVersion, report.latestVersionId)
        artifact_id = version.sourceArtifactId if version is not None else None
    elif resolved_type is ExecutionSourceType.VERSION:
        if not version_name:
            raise_ex("versionName is required for version execution", code=400)
        try:
            major, minor, patch = parse_version_name(version_name)
        except ValueError as error:
            raise_ex(str(error), code=400)
        version = await session.scalar(
            select(CalcReportVersion).where(
                CalcReportVersion.reportId == report.id,
                CalcReportVersion.major == major,
                CalcReportVersion.minor == minor,
                CalcReportVersion.patch == patch,
            )
        )
        artifact_id = version.sourceArtifactId if version is not None else None
    if artifact_id is None:
        raise_ex(
            "Execution source artifact not found",
            code=404,
            error_code=CalcErrorCode.WORKSPACE_NOT_FOUND,
        )
    artifact = await session.get(CalcReportArtifact, artifact_id)
    if artifact is None:
        raise_ex("Execution source artifact not found", code=500)
    return ResolvedExecutionSource(
        report=report,
        source_artifact=artifact,
        source_type=resolved_type,
        resolved_version=version,
    )


async def prepare_execution_bundle(
    user_id: int,
    source: ResolvedExecutionSource,
    runtime: RuntimeDescriptor,
    session: AsyncSession,
) -> tuple[CalcExecutionBundle, PreparedExecutionBundle]:
    """Resolve/build a full dependency closure and assemble a reusable bundle."""
    components: dict[str, _ResolvedComponent] = {}
    expanded: set[int] = set()
    active: set[int] = set()
    entry_execution = await ensure_instrumented_artifact(
        source.source_artifact.id, runtime.fingerprint, session
    )
    entry_scope = _scope_key(source.source_artifact)
    components["entry"] = _ResolvedComponent(
        component_key="entry",
        scope_key=entry_scope,
        alias=None,
        selector_key=None,
        source_artifact=source.source_artifact,
        execution_artifact=entry_execution,
        is_entry=True,
    )
    await _expand_dependencies(
        user_id,
        source.source_artifact,
        runtime,
        components,
        expanded,
        active,
        session,
    )
    manifest = {
        "formatVersion": 1,
        "runtimeFingerprint": runtime.fingerprint,
        "runtimeImageDigest": runtime.image_digest,
        "entry": {
            "reportOid": source.report.oid,
            "sourceType": source.source_type.name.lower(),
            "resolvedVersion": (
                _version_name(source.resolved_version)
                if source.resolved_version is not None
                else None
            ),
            "sourceArtifactHash": source.source_artifact.contentHash,
            "executionArtifactHash": entry_execution.contentHash,
            "entryPath": source.report.entryPath,
        },
        "components": [
            {
                "componentKey": component.component_key,
                "scopeKey": component.scope_key,
                "alias": component.alias,
                "selectorKey": component.selector_key,
                "sourceArtifactHash": component.source_artifact.contentHash,
                "executionArtifactHash": component.execution_artifact.contentHash,
                "isEntry": component.is_entry,
            }
            for component in sorted(
                components.values(), key=lambda value: value.component_key
            )
        ],
    }
    canonical = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    bundle_hash = hashlib.sha256(canonical).hexdigest()
    bundle = await session.scalar(
        select(CalcExecutionBundle).where(CalcExecutionBundle.bundleHash == bundle_hash)
    )
    if bundle is None:
        try:
            bundle = CalcExecutionBundle(
                bundleHash=bundle_hash,
                runtimeFingerprint=runtime.fingerprint,
                runtimeImageDigest=runtime.image_digest,
                entrySourceArtifactId=source.source_artifact.id,
                entryExecutionArtifactId=entry_execution.id,
                manifest=manifest,
            )
            session.add(bundle)
            await session.flush()
            for component in components.values():
                session.add(
                    CalcExecutionBundleComponent(
                        bundleId=bundle.id,
                        componentKey=component.component_key,
                        scopeKey=component.scope_key,
                        alias=component.alias,
                        selectorKey=component.selector_key,
                        sourceArtifactId=component.source_artifact.id,
                        executionArtifactId=component.execution_artifact.id,
                        isEntry=component.is_entry,
                    )
                )
            await session.commit()
            await session.refresh(bundle)
        except IntegrityError:
            await session.rollback()
            bundle = await session.scalar(
                select(CalcExecutionBundle).where(
                    CalcExecutionBundle.bundleHash == bundle_hash
                )
            )
            if bundle is None:
                raise
    root = _materialize_bundle(bundle_hash, manifest, components)
    prepared = PreparedExecutionBundle(
        oid=bundle.oid,
        bundle_hash=bundle_hash,
        root=root,
        entry_path=source.report.entryPath,
        manifest=manifest,
    )
    return bundle, prepared


async def _expand_dependencies(
    user_id: int,
    source_artifact: CalcReportArtifact,
    runtime: RuntimeDescriptor,
    components: dict[str, _ResolvedComponent],
    expanded: set[int],
    active: set[int],
    session: AsyncSession,
) -> None:
    """Resolve every declared selector recursively into immutable components."""
    if source_artifact.id in active:
        raise_ex(
            "Dependency cycle detected",
            code=400,
            error_code=CalcErrorCode.DEPENDENCY_CYCLE,
        )
    if source_artifact.id in expanded:
        return
    active.add(source_artifact.id)
    scope_key = _scope_key(source_artifact)
    for dependency in source_artifact.manifest.get("dependencies", []):
        target_report = await session.scalar(
            select(CalcReport).where(
                CalcReport.oid == dependency["targetReportOid"],
                CalcReport.userId == user_id,
                CalcReport.deletedAt.is_(None),
            )
        )
        if target_report is None:
            raise_ex(
                "Dependency report is unavailable",
                code=403,
                error_code=CalcErrorCode.DEPENDENCY_INVALID,
            )
        for selector in dependency["selectors"]:
            version = await _resolve_dependency_version(
                target_report, selector, session
            )
            source = await session.get(CalcReportArtifact, version.sourceArtifactId)
            if source is None:
                raise_ex("Dependency SOURCE artifact not found", code=500)
            execution = await ensure_instrumented_artifact(
                source.id, runtime.fingerprint, session
            )
            component_key = (
                f"{scope_key}/{dependency['alias']}/{selector['selectorKey']}"
            )
            existing = components.get(component_key)
            if existing is not None and existing.source_artifact.id != source.id:
                raise_ex("Dependency component key collision", code=500)
            components[component_key] = _ResolvedComponent(
                component_key=component_key,
                scope_key=scope_key,
                alias=dependency["alias"],
                selector_key=selector["selectorKey"],
                source_artifact=source,
                execution_artifact=execution,
                is_entry=False,
            )
            await _expand_dependencies(
                user_id,
                source,
                runtime,
                components,
                expanded,
                active,
                session,
            )
    active.remove(source_artifact.id)
    expanded.add(source_artifact.id)


async def _resolve_dependency_version(
    report: CalcReport, selector: dict, session: AsyncSession
) -> CalcReportVersion:
    """Resolve a latest or explicit immutable dependency version."""
    if selector["selectorKey"] == ReservedDependencySelectorKey.LATEST:
        version = (
            await session.get(CalcReportVersion, report.latestVersionId)
            if report.latestVersionId is not None
            else None
        )
    else:
        try:
            major, minor, patch = parse_version_name(selector["versionName"])
        except (TypeError, ValueError) as error:
            raise_ex(str(error), code=400, error_code=CalcErrorCode.DEPENDENCY_INVALID)
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
            "Dependency version not found",
            code=404,
            error_code=CalcErrorCode.DEPENDENCY_INVALID,
        )
    return version


def _scope_key(artifact: CalcReportArtifact) -> str:
    """Return the valid Python namespace assigned to one SOURCE artifact."""
    return f"scope_{artifact.contentHash[:16]}"


def _version_name(version: CalcReportVersion) -> str:
    """Derive a semantic version name without duplicating it in storage."""
    return f"{version.major}.{version.minor}.{version.patch}"


def _materialize_bundle(
    bundle_hash: str,
    manifest: dict,
    components: dict[str, _ResolvedComponent],
) -> Path:
    """Assemble one immutable read-only bundle cache directory atomically."""
    root = (
        Path(app_config.calc_report_bundles_root)
        / "sha256"
        / bundle_hash[:2]
        / bundle_hash
    ).resolve()
    if root.is_dir() and (root / "manifest.json").is_file():
        return root
    root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{bundle_hash}-", dir=root.parent))
    try:
        for component in components.values():
            if component.is_entry:
                base = temporary
            else:
                base = (
                    temporary
                    / "__uzon_deps__"
                    / component.scope_key
                    / (component.alias or "")
                    / (component.selector_key or "")
                )
                _ensure_python_packages(base, temporary)
            _write_component(base, component)
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        for path in temporary.rglob("*"):
            if path.is_file():
                path.chmod(0o444)
            elif path.is_dir():
                path.chmod(0o555)
        try:
            os.replace(temporary, root)
        except OSError:
            if not root.is_dir():
                raise
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return root


def _write_component(base: Path, component: _ResolvedComponent) -> None:
    """Combine instrumented Python and SOURCE resources at one bundle mount."""
    for file in artifact_store.read_all(component.execution_artifact.storageKey):
        relative = Path(file.path)
        destination = (
            base / relative if component.is_entry else base / Path(*relative.parts[1:])
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(file.content)
    for file in artifact_store.read_all(component.source_artifact.storageKey):
        if file.path.startswith("src/"):
            continue
        destination = base / file.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(file.content)


def _ensure_python_packages(base: Path, bundle_root: Path) -> None:
    """Create missing namespace package markers through a dependency mount."""
    current = base
    while current != bundle_root:
        current.mkdir(parents=True, exist_ok=True)
        init_file = current / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")
        current = current.parent
