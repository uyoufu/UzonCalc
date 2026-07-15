"""Safe compatibility import for legacy executable ``.uzc`` archives."""

from __future__ import annotations

import hashlib
import io
import json
import stat
import zipfile
from pathlib import PurePosixPath

from sqlalchemy.ext.asyncio import AsyncSession

from app.controller.calc.calc_error import CalcErrorCode
from app.controller.calc.calc_workspace_dto import (
    WorkspaceCreateDTO,
    WorkspaceFileDTO,
    WorkspaceResDTO,
    WorkspaceSaveDTO,
)
from app.db.models.calc_report import CalcReportOrigin
from app.db.models.enums import ReportOriginType
from app.db.models.object_id import ObjectId
from app.exception.custom_exception import raise_ex
from app.service.calc_report_artifact_service import (
    ArtifactValidationError,
    normalize_workspace_path,
)
from app.service.calc_report_workspace_service import get_owned_report, save_workspace
from config import app_config

_ARCHIVE_SOURCE_PREFIX = "__uzoncalc_bundle__/src/"
_ARCHIVE_MANIFEST_PATH = "__uzoncalc_bundle__/manifest.json"
_MAX_COMPRESSION_RATIO = 200


async def import_uzc_archive(
    user_id: int,
    category_oid: str,
    report_name: str,
    archive_bytes: bytes,
    session: AsyncSession,
) -> WorkspaceResDTO:
    """Convert a legacy archive to an unpublished platform workspace.

    Args:
        user_id: Current user database ID.
        category_oid: Receiver-owned category identifier.
        report_name: New report display name.
        archive_bytes: Complete untrusted ``.uzc`` bytes.
        session: Database session.

    Returns:
        Created workspace metadata.

    Raises:
        CustomException: If the archive is unsafe, malformed, or too large.
    """
    files, entry_path = _read_uzc_files(archive_bytes)
    calcbook = json.dumps(
        {"formatVersion": 1, "entryPath": entry_path},
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    files["calcbook.json"] = calcbook
    report_oid = str(ObjectId())
    request = WorkspaceSaveDTO(
        workspaceRevision=0,
        create=WorkspaceCreateDTO(
            categoryOid=category_oid,
            name=report_name.strip(),
        ),
        files=[WorkspaceFileDTO(path=path) for path in sorted(files)],
    )
    workspace = await save_workspace(user_id, report_oid, request, files, session)
    report = await get_owned_report(user_id, report_oid, session)
    session.add(
        CalcReportOrigin(
            reportId=report.id,
            originType=ReportOriginType.UZC_IMPORT.value,
            sourceArtifactId=report.workspaceArtifactId,
            sourceArchiveHash=hashlib.sha256(archive_bytes).hexdigest(),
            originMetadata={"archiveFormat": "legacy-uzc-v1"},
        )
    )
    await session.commit()
    return workspace


def _read_uzc_files(archive_bytes: bytes) -> tuple[dict[str, bytes], str]:
    """Read and validate archive members without extracting to the filesystem.

    Args:
        archive_bytes: Untrusted archive bytes, optionally prefixed by a shebang.

    Returns:
        Workspace file mapping and normalized workspace entry path.

    Raises:
        CustomException: If ZIP structure, limits, or the legacy manifest is invalid.
    """
    if len(archive_bytes) > app_config.calc_report_max_total_size:
        _raise_invalid_archive("UZC archive exceeds the upload limit", 413)
    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except zipfile.BadZipFile:
        _raise_invalid_archive("UZC archive is not a valid ZIP file")
    with archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if len(infos) > app_config.calc_report_max_file_count + 2:
            _raise_invalid_archive("UZC archive contains too many files", 413)
        total_size = 0
        by_name: dict[str, zipfile.ZipInfo] = {}
        for info in infos:
            _validate_archive_info(info)
            if info.filename in by_name:
                _raise_invalid_archive("UZC archive contains duplicate paths")
            by_name[info.filename] = info
            total_size += info.file_size
            if total_size > app_config.calc_report_max_total_size:
                _raise_invalid_archive("UZC archive expands beyond the size limit", 413)
        manifest_info = by_name.get(_ARCHIVE_MANIFEST_PATH)
        if manifest_info is None:
            _raise_invalid_archive("UZC archive manifest is missing")
        try:
            manifest = json.loads(archive.read(manifest_info).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _raise_invalid_archive("UZC archive manifest is invalid")
        raw_entry_path = (
            manifest.get("entry_path") if isinstance(manifest, dict) else None
        )
        if not isinstance(raw_entry_path, str):
            _raise_invalid_archive("UZC archive entry path is invalid")
        source_files: dict[str, bytes] = {}
        for name, info in by_name.items():
            if not name.startswith(_ARCHIVE_SOURCE_PREFIX):
                continue
            relative_path = name.removeprefix(_ARCHIVE_SOURCE_PREFIX)
            workspace_path = _normalize_imported_source_path(relative_path)
            content = archive.read(info)
            if len(content) != info.file_size:
                _raise_invalid_archive("UZC archive file size is inconsistent")
            source_files[workspace_path] = content
        entry_path = _normalize_imported_source_path(raw_entry_path)
        if entry_path not in source_files:
            _raise_invalid_archive("UZC archive entry source is missing")
        return source_files, entry_path


def _validate_archive_info(info: zipfile.ZipInfo) -> None:
    """Reject one unsafe, encrypted, oversized, or suspicious ZIP member."""
    path = PurePosixPath(info.filename)
    if (
        not info.filename
        or "\\" in info.filename
        or "\x00" in info.filename
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _raise_invalid_archive("UZC archive contains an unsafe path")
    file_mode = info.external_attr >> 16
    file_type = stat.S_IFMT(file_mode)
    if file_type not in {0, stat.S_IFREG}:
        _raise_invalid_archive("UZC archive contains a non-regular file")
    if info.flag_bits & 0x1:
        _raise_invalid_archive("Encrypted UZC archives are not supported")
    if info.file_size > app_config.calc_report_max_file_size:
        _raise_invalid_archive("UZC archive contains an oversized file", 413)
    if info.file_size and (
        info.compress_size == 0
        or info.file_size / info.compress_size > _MAX_COMPRESSION_RATIO
    ):
        _raise_invalid_archive("UZC archive has a suspicious compression ratio", 413)


def _normalize_imported_source_path(relative_path: str) -> str:
    """Map one legacy source-relative path into the workspace ``src`` tree."""
    path = PurePosixPath(relative_path)
    if (
        not relative_path
        or "\\" in relative_path
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _raise_invalid_archive("UZC archive source path is invalid")
    workspace_path = f"src/{path.as_posix()}"
    try:
        return normalize_workspace_path(workspace_path)
    except ArtifactValidationError:
        _raise_invalid_archive("UZC archive source path is invalid")


def _raise_invalid_archive(message: str, code: int = 400) -> None:
    """Raise the stable workspace error used by archive validation failures."""
    raise_ex(message, code=code, error_code=CalcErrorCode.ARCHIVE_INVALID)
