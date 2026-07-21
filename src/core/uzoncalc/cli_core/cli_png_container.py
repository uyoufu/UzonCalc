"""Write executable ZIP payloads inside standards-compliant PNG containers."""

from collections.abc import Callable
from io import BytesIO
import os
from pathlib import Path
import struct
import tempfile
from typing import BinaryIO, cast
import zlib


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_IEND_CHUNK = b"\x00\x00\x00\x00IEND\xaeB`\x82"
_UZONCALC_ARCHIVE_CHUNK_TYPE = b"uzCa"
_PNG_CHUNK_MAX_SIZE = (1 << 31) - 1
_CRC_READ_SIZE = 1024 * 1024
_ARCHIVE_FILE_MODE = 0o644
_SPOOLED_PAYLOAD_MEMORY_LIMIT = 8 * 1024 * 1024


def read_png_zip_container(container_bytes: bytes) -> bytes:
    """Read and validate the ZIP payload stored in a UzonCalc PNG container.

    Args:
        container_bytes: Complete PNG container bytes from an untrusted source.

    Returns:
        The ZIP payload from the unique private ``uzCa`` chunk.

    Raises:
        ValueError: If PNG framing, chunk CRC, payload count, or IEND is invalid.
    """
    if not container_bytes.startswith(_PNG_SIGNATURE):
        raise ValueError("归档缺少有效的 PNG 签名")

    stream = BytesIO(container_bytes)
    stream.seek(len(_PNG_SIGNATURE))
    payload: bytes | None = None
    has_iend = False
    while stream.tell() < len(container_bytes):
        header = stream.read(8)
        if len(header) != 8:
            raise ValueError("PNG 块头不完整")
        chunk_length, chunk_type = struct.unpack(">I4s", header)
        if chunk_length > _PNG_CHUNK_MAX_SIZE:
            raise ValueError("PNG 块长度超过允许上限")
        chunk_data = stream.read(chunk_length)
        chunk_crc = stream.read(4)
        if len(chunk_data) != chunk_length or len(chunk_crc) != 4:
            raise ValueError("PNG 块数据不完整")
        expected_crc = struct.unpack(">I", chunk_crc)[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError("PNG 块 CRC 校验失败")

        if chunk_type == _UZONCALC_ARCHIVE_CHUNK_TYPE:
            if payload is not None:
                raise ValueError("PNG 包含多个 UzonCalc 归档块")
            payload = chunk_data
        if chunk_type == b"IEND":
            if chunk_length != 0 or stream.tell() != len(container_bytes):
                raise ValueError("PNG IEND 块不是最终空块")
            has_iend = True
            break

    if not has_iend:
        raise ValueError("PNG 缺少最终 IEND 块")
    if payload is None:
        raise ValueError("PNG 不包含 UzonCalc 归档块")
    return payload


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
        with tempfile.SpooledTemporaryFile(
            max_size=_SPOOLED_PAYLOAD_MEMORY_LIMIT, mode="w+b"
        ) as payload_file:
            # ZIP offsets must start at zero so the private chunk is independently readable.
            # Typeshed does not model SpooledTemporaryFile as BinaryIO despite its API.
            zip_payload_writer(cast(BinaryIO, payload_file))
            payload_length = payload_file.seek(0, os.SEEK_END)
            if payload_length > _PNG_CHUNK_MAX_SIZE:
                raise ValueError(".uzc ZIP 数据超过 PNG 单块 2 GiB 上限")
            payload_file.seek(0)

            temp_descriptor, temp_name = tempfile.mkstemp(
                dir=output_path.parent,
                prefix=f".{output_path.name}.",
                suffix=".tmp",
            )
            temp_path = Path(temp_name)
            with os.fdopen(temp_descriptor, "w+b") as archive_file:
                archive_file.write(thumbnail_without_iend)
                archive_file.write(struct.pack(">I", payload_length))
                archive_file.write(_UZONCALC_ARCHIVE_CHUNK_TYPE)
                checksum = zlib.crc32(_UZONCALC_ARCHIVE_CHUNK_TYPE)
                while block := payload_file.read(_CRC_READ_SIZE):
                    archive_file.write(block)
                    checksum = zlib.crc32(block, checksum)
                archive_file.write(struct.pack(">I", checksum & 0xFFFFFFFF))
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
