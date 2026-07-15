"""Security tests for legacy ``.uzc`` compatibility parsing."""

import io
import json
import stat
import zipfile

import pytest

from app.exception.custom_exception import CustomException
from app.service.calc_report_import_service import _read_uzc_files


def _archive_bytes(entries: dict[str, bytes]) -> bytes:
    """Create an in-memory ZIP containing the requested test entries."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, content in entries.items():
            archive.writestr(path, content)
    return buffer.getvalue()


def test_read_uzc_maps_legacy_source_tree_without_runner() -> None:
    """The adapter should retain user sources and ignore executable runner files."""
    archive = _archive_bytes(
        {
            "__main__.py": b"raise RuntimeError('must not run')",
            "__uzoncalc_bundle__/manifest.json": json.dumps(
                {"entry_path": "main.py", "auto_view_entry": "book"}
            ).encode(),
            "__uzoncalc_bundle__/src/main.py": b"def book():\n    return 1\n",
            "__uzoncalc_bundle__/src/helpers.py": b"VALUE = 1\n",
        }
    )

    files, entry_path = _read_uzc_files(archive)

    assert entry_path == "src/main.py"
    assert set(files) == {"src/main.py", "src/helpers.py"}
    assert b"must not run" not in b"".join(files.values())


def test_read_uzc_rejects_path_traversal() -> None:
    """Archive members must not escape the declared legacy source root."""
    archive = _archive_bytes(
        {
            "__uzoncalc_bundle__/manifest.json": b'{"entry_path":"main.py"}',
            "__uzoncalc_bundle__/src/main.py": b"pass\n",
            "../outside.py": b"pass\n",
        }
    )

    with pytest.raises(CustomException, match="unsafe path"):
        _read_uzc_files(archive)


def test_read_uzc_rejects_symbolic_link_member() -> None:
    """A Unix symbolic-link ZIP entry must be rejected before reading content."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "__uzoncalc_bundle__/manifest.json", b'{"entry_path":"main.py"}'
        )
        link = zipfile.ZipInfo("__uzoncalc_bundle__/src/main.py")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, b"../../outside.py")

    with pytest.raises(CustomException, match="non-regular file"):
        _read_uzc_files(buffer.getvalue())
