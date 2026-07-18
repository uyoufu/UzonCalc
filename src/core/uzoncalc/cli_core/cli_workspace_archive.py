"""Read and write secure UzonCalc v3 workspace archives in PNG containers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
from typing import Mapping
import zipfile

from .cli_png_container import read_png_zip_container, write_png_zip_container

ARCHIVE_FORMAT_VERSION = 3
ARCHIVE_MANIFEST_PATH = "__uzoncalc_bundle__/manifest.json"
_MAX_COMPRESSION_RATIO = 200


@dataclass(frozen=True)
class WorkspaceArchive:
    """Hold a validated v3 manifest and its content files.

    Attributes:
        manifest: Parsed v3 archive manifest.
        files: Archive content keyed by normalized POSIX path.
    """

    manifest: dict
    files: dict[str, bytes]


def write_workspace_archive(
    output_path: Path,
    thumbnail_png: bytes,
    manifest: Mapping[str, object],
    files: Mapping[str, bytes],
) -> None:
    """Write a deterministic v3 workspace archive as PNG or UZC.

    Args:
        output_path: Final ``.png`` or ``.uzc`` path.
        thumbnail_png: Standards-compliant PNG thumbnail.
        manifest: Domain metadata excluding generated file hashes.
        files: Complete executable closure keyed by archive-relative path.

    Returns:
        None.

    Raises:
        ValueError: If paths, manifest version, or duplicate names are invalid.
        OSError: If the output cannot be written atomically.
    """
    if output_path.suffix.lower() not in {".png", ".uzc"}:
        raise ValueError("归档扩展名必须为 .png 或 .uzc")
    normalized_files = {
        _normalize_archive_path(path): bytes(content) for path, content in files.items()
    }
    if len(normalized_files) != len(files):
        raise ValueError("归档包含规范化后重复的路径")
    archive_manifest = dict(manifest)
    archive_manifest["formatVersion"] = ARCHIVE_FORMAT_VERSION
    archive_manifest["files"] = [
        {
            "path": path,
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for path, content in sorted(normalized_files.items())
    ]

    def write_payload(stream) -> None:
        """Write the v3 ZIP payload to the private PNG chunk stream."""
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                ARCHIVE_MANIFEST_PATH,
                json.dumps(archive_manifest, ensure_ascii=False, sort_keys=True),
            )
            for path, content in sorted(normalized_files.items()):
                archive.writestr(path, content)

    write_png_zip_container(output_path, thumbnail_png, write_payload)


def read_workspace_archive(
    container_bytes: bytes,
    *,
    max_file_count: int = 1000,
    max_file_size: int = 25 * 1024 * 1024,
    max_total_size: int = 100 * 1024 * 1024,
) -> WorkspaceArchive:
    """Read and fully validate an untrusted v3 PNG workspace archive.

    Args:
        container_bytes: Complete PNG or UZC bytes.
        max_file_count: Maximum declared content file count.
        max_file_size: Maximum uncompressed size of one member.
        max_total_size: Maximum combined uncompressed content size.

    Returns:
        Validated manifest and content bytes.

    Raises:
        ValueError: If PNG, ZIP, paths, limits, manifest, or hashes are invalid.
    """
    try:
        payload = read_png_zip_container(container_bytes)
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except (ValueError, zipfile.BadZipFile) as error:
        raise ValueError("归档容器无效") from error
    with archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if len(infos) > max_file_count + 1:
            raise ValueError("归档文件数量超过限制")
        by_name: dict[str, zipfile.ZipInfo] = {}
        total_size = 0
        for info in infos:
            normalized_path = _normalize_archive_path(info.filename)
            if normalized_path != info.filename or normalized_path in by_name:
                raise ValueError("归档包含非法或重复路径")
            file_type = stat.S_IFMT(info.external_attr >> 16)
            if file_type not in {0, stat.S_IFREG} or info.flag_bits & 0x1:
                raise ValueError("归档只允许未加密的普通文件")
            if info.file_size > max_file_size:
                raise ValueError("归档单文件大小超过限制")
            if info.file_size and (
                info.compress_size == 0
                or info.file_size / info.compress_size > _MAX_COMPRESSION_RATIO
            ):
                raise ValueError("归档压缩比异常")
            total_size += info.file_size
            if total_size > max_total_size:
                raise ValueError("归档解压总大小超过限制")
            by_name[normalized_path] = info
        manifest_info = by_name.pop(ARCHIVE_MANIFEST_PATH, None)
        if manifest_info is None:
            raise ValueError("归档 manifest 缺失")
        try:
            manifest = json.loads(archive.read(manifest_info).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("归档 manifest 无效") from error
        if not isinstance(manifest, dict) or manifest.get("formatVersion") != 3:
            raise ValueError("归档格式版本不受支持")
        declarations = manifest.get("files")
        if not isinstance(declarations, list) or len(declarations) != len(by_name):
            raise ValueError("归档文件清单不完整")
        files: dict[str, bytes] = {}
        declared_paths: set[str] = set()
        for declaration in declarations:
            if not isinstance(declaration, dict):
                raise ValueError("归档文件声明无效")
            path = _normalize_archive_path(str(declaration.get("path", "")))
            if path in declared_paths or path not in by_name:
                raise ValueError("归档文件声明重复或缺失")
            content = archive.read(by_name[path])
            if declaration.get("size") != len(content) or declaration.get(
                "sha256"
            ) != hashlib.sha256(content).hexdigest():
                raise ValueError("归档文件哈希校验失败")
            files[path] = content
            declared_paths.add(path)
        return WorkspaceArchive(manifest=manifest, files=files)


def _normalize_archive_path(path: str) -> str:
    """Validate and normalize one portable archive-relative path."""
    candidate = PurePosixPath(path)
    if (
        not path
        or "\\" in path
        or "\x00" in path
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise ValueError("归档路径无效")
    return candidate.as_posix()
