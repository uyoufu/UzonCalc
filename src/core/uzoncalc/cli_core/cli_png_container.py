"""Write executable ZIP payloads inside standards-compliant PNG containers."""

from collections.abc import Callable
import os
from pathlib import Path
import struct
import tempfile
from typing import BinaryIO
import zlib


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_IEND_CHUNK = b"\x00\x00\x00\x00IEND\xaeB`\x82"
_UZONCALC_ARCHIVE_CHUNK_TYPE = b"uzCa"
_PNG_CHUNK_MAX_SIZE = (1 << 31) - 1
_CRC_READ_SIZE = 1024 * 1024
_ARCHIVE_FILE_MODE = 0o644


def _validate_thumbnail_png(thumbnail_png: bytes) -> None:
    """Validate the structural boundaries required for chunk insertion.

    Args:
        thumbnail_png: Complete PNG bytes generated for the archive preview.

    Returns:
        None.

    Raises:
        ValueError: When the byte sequence lacks a PNG signature or final IEND.
    """
    if not thumbnail_png.startswith(_PNG_SIGNATURE):
        raise ValueError("缩略图缺少有效的 PNG 签名")
    if not thumbnail_png.endswith(_PNG_IEND_CHUNK):
        raise ValueError("缩略图缺少末尾 IEND 块")


def _calculate_archive_chunk_crc(
    archive_file: BinaryIO,
    payload_start: int,
    payload_length: int,
) -> int:
    """Calculate the PNG CRC for the private ZIP payload without loading it all.

    Args:
        archive_file: Seekable output stream containing the ZIP payload.
        payload_start: Absolute byte offset of the private chunk data.
        payload_length: Number of ZIP payload bytes covered by the chunk.

    Returns:
        Unsigned CRC-32 over the chunk type and payload.

    Raises:
        OSError: When the output stream cannot be read completely.
    """
    archive_file.seek(payload_start)
    remaining = payload_length
    checksum = zlib.crc32(_UZONCALC_ARCHIVE_CHUNK_TYPE)
    while remaining:
        block = archive_file.read(min(_CRC_READ_SIZE, remaining))
        if not block:
            raise OSError("读取 .uzc ZIP 数据计算 PNG 校验值时提前结束")
        checksum = zlib.crc32(block, checksum)
        remaining -= len(block)
    return checksum & 0xFFFFFFFF


def write_png_zip_container(
    output_path: Path,
    thumbnail_png: bytes,
    zip_payload_writer: Callable[[BinaryIO], None],
) -> None:
    """Atomically combine a PNG thumbnail and seekable ZIP payload.

    Args:
        output_path: Final ``.uzc`` path.
        thumbnail_png: Complete PNG thumbnail bytes.
        zip_payload_writer: Callback that writes a ZIP archive at the current offset.

    Returns:
        None.

    Raises:
        ValueError: When the thumbnail is invalid or ZIP exceeds PNG limits.
        OSError: When temporary output, CRC calculation, or replacement fails.
        Exception: Any error raised by ``zip_payload_writer`` is propagated.
    """
    _validate_thumbnail_png(thumbnail_png)
    thumbnail_without_iend = thumbnail_png[: -len(_PNG_IEND_CHUNK)]
    temp_path: Path | None = None
    try:
        temp_descriptor, temp_name = tempfile.mkstemp(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
        )
        temp_path = Path(temp_name)
        with os.fdopen(temp_descriptor, "w+b") as archive_file:
            archive_file.write(thumbnail_without_iend)
            chunk_header_start = archive_file.tell()
            archive_file.write(struct.pack(">I", 0))
            archive_file.write(_UZONCALC_ARCHIVE_CHUNK_TYPE)
            payload_start = archive_file.tell()

            zip_payload_writer(archive_file)
            payload_end = archive_file.seek(0, os.SEEK_END)
            payload_length = payload_end - payload_start
            if payload_length > _PNG_CHUNK_MAX_SIZE:
                raise ValueError(".uzc ZIP 数据超过 PNG 单块 2 GiB 上限")

            checksum = _calculate_archive_chunk_crc(
                archive_file,
                payload_start,
                payload_length,
            )
            archive_file.seek(chunk_header_start)
            archive_file.write(struct.pack(">I", payload_length))
            archive_file.seek(payload_end)
            archive_file.write(struct.pack(">I", checksum))
            archive_file.write(_PNG_IEND_CHUNK)
            archive_file.flush()
            os.fsync(archive_file.fileno())

        if temp_path is None:
            raise RuntimeError(".uzc 临时文件未创建")
        os.chmod(temp_path, _ARCHIVE_FILE_MODE)
        os.replace(temp_path, output_path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
