import json
from io import BytesIO
import subprocess
import struct
import sys
import zipfile
import zlib
from pathlib import Path

from PIL import Image
import pytest

from uzoncalc import cli
from uzoncalc.cli_core import cli_thumbnail
from uzoncalc.cli_core.cli_archive_analysis import (
    ArchiveEntryPreview,
    analyze_archive_script,
)
from uzoncalc.cli_core.cli_png_container import (
    read_png_zip_container,
    write_png_zip_container,
)
from uzoncalc.cli_core.cli_thumbnail import render_archive_thumbnail
from uzoncalc.cli_core.cli_workspace_archive import (
    read_workspace_archive,
    write_workspace_archive,
)


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _write_uzoncalc_stub(project_dir: Path) -> None:
    """写入测试用的 uzoncalc 包，避免启动真实 HTTP 预览服务。

    Args:
        project_dir: 临时脚本项目根目录。

    Returns:
        None.

    Raises:
        OSError: 当测试文件无法写入时抛出。
    """
    package_dir = project_dir / "uzoncalc"
    package_dir.mkdir()
    package_dir.joinpath("__init__.py").write_text(
        "\n".join(
            [
                "def uzon_calc(func=None, **kwargs):",
                "    def decorate(entry):",
                "        entry._uzon_calc_entry = True",
                "        return entry",
                "    return decorate(func) if func else decorate",
                "",
                "def view(entry):",
                "    print('view:' + entry())",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_png_chunks(archive_path: Path) -> list[tuple[bytes, bytes]]:
    """Read and validate every chunk in a generated PNG archive.

    Args:
        archive_path: Generated ``.uzc`` file expected to contain a PNG stream.

    Returns:
        Ordered chunk-type and chunk-data pairs.

    Raises:
        AssertionError: When PNG framing, chunk bounds, or CRC values are invalid.
        OSError: When the archive cannot be read.
    """
    png_bytes = archive_path.read_bytes()
    assert png_bytes.startswith(_PNG_SIGNATURE)
    offset = len(_PNG_SIGNATURE)
    chunks: list[tuple[bytes, bytes]] = []
    while offset < len(png_bytes):
        assert offset + 12 <= len(png_bytes)
        chunk_length = struct.unpack(">I", png_bytes[offset : offset + 4])[0]
        chunk_type = png_bytes[offset + 4 : offset + 8]
        chunk_data_start = offset + 8
        chunk_data_end = chunk_data_start + chunk_length
        chunk_crc_end = chunk_data_end + 4
        assert chunk_crc_end <= len(png_bytes)
        chunk_data = png_bytes[chunk_data_start:chunk_data_end]
        expected_crc = struct.unpack(">I", png_bytes[chunk_data_end:chunk_crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        assert actual_crc == expected_crc
        chunks.append((chunk_type, chunk_data))
        offset = chunk_crc_end

    assert offset == len(png_bytes)
    assert chunks[-1][0] == b"IEND"
    return chunks


def test_png_container_reader_returns_validated_zip_payload(tmp_path):
    """共享容器读取器应返回写入 PNG 私有块的原始 ZIP 数据。"""
    thumbnail = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(thumbnail, format="PNG")
    output_path = tmp_path / "report.png"

    def write_payload(stream) -> None:
        """向给定流写入确定性的测试 ZIP。"""
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("manifest.json", "{}")

    write_png_zip_container(output_path, thumbnail.getvalue(), write_payload)

    payload = read_png_zip_container(output_path.read_bytes())
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert archive.read("manifest.json") == b"{}"


def test_png_container_reader_rejects_tampered_crc(tmp_path):
    """共享容器读取器应拒绝 CRC 未同步更新的篡改数据。"""
    thumbnail = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(thumbnail, format="PNG")
    output_path = tmp_path / "report.uzc"
    write_png_zip_container(
        output_path, thumbnail.getvalue(), lambda stream: stream.write(b"zip")
    )
    tampered = bytearray(output_path.read_bytes())
    payload_offset = tampered.index(b"uzCa") + 4
    tampered[payload_offset] ^= 0x01

    with pytest.raises(ValueError, match="CRC"):
        read_png_zip_container(bytes(tampered))


@pytest.mark.parametrize("suffix", [".png", ".uzc"])
def test_workspace_archive_v3_round_trip_supports_both_extensions(tmp_path, suffix):
    """V3 workspace archives should use identical validated PNG containers."""
    thumbnail = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(thumbnail, format="PNG")
    output_path = tmp_path / f"report{suffix}"
    files = {
        "executable/src/main.py": b"print('ok')\n",
        "workspace/root/calcbook.json": b'{"formatVersion": 1}',
    }

    write_workspace_archive(
        output_path,
        thumbnail.getvalue(),
        {"rootReportOid": "0123456789abcdef01234567", "canEdit": False},
        files,
    )

    archive = read_workspace_archive(output_path.read_bytes())
    assert archive.manifest["formatVersion"] == 3
    assert archive.manifest["canEdit"] is False
    assert archive.files == files


def test_workspace_archive_v3_rejects_manifest_hash_tampering(tmp_path):
    """V3 reads should reject content whose declared digest no longer matches."""
    thumbnail = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(thumbnail, format="PNG")
    output_path = tmp_path / "report.png"
    write_workspace_archive(
        output_path,
        thumbnail.getvalue(),
        {"rootReportOid": "0123456789abcdef01234567"},
        {"executable/src/main.py": b"print('ok')\n"},
    )
    payload = read_png_zip_container(output_path.read_bytes())
    source = BytesIO(payload)
    rewritten = BytesIO()
    with zipfile.ZipFile(source) as input_archive, zipfile.ZipFile(
        rewritten, "w", compression=zipfile.ZIP_DEFLATED
    ) as output_archive:
        for info in input_archive.infolist():
            content = input_archive.read(info)
            if info.filename == "executable/src/main.py":
                content = b"print('tampered')\n"
            output_archive.writestr(info.filename, content)

    tampered_path = tmp_path / "tampered.png"
    write_png_zip_container(
        tampered_path,
        thumbnail.getvalue(),
        lambda stream: stream.write(rewritten.getvalue()),
    )
    with pytest.raises(ValueError, match="哈希"):
        read_workspace_archive(tampered_path.read_bytes())


def test_archive_analysis_prefers_h1_and_first_entry(tmp_path):
    """Static analysis should select the first entry and its literal H1 title.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None.

    Raises:
        AssertionError: When title priority, entry order, or excerpt limits regress.
    """
    script_path = tmp_path / "multi_report.py"
    body_lines = [f"    value_{index} = {index}" for index in range(16)]
    script_path.write_text(
        "\n".join(
            [
                "from uzoncalc import *",
                "",
                "@uzon_calc('Decorator title')",
                "async def first():",
                "    doc_title('Document title')",
                "    def nested():",
                "        H1('Nested title')",
                "    H1('Primary title')",
                *body_lines,
                "",
                "@uzon_calc()",
                "async def second():",
                "    H1('Second title')",
                "",
                "if __name__ == '__main__':",
                "    pass",
                "",
            ]
        ),
        encoding="utf-8",
    )

    analysis = analyze_archive_script(script_path)

    assert analysis.entry_names == ("first", "second")
    assert analysis.has_main_guard is True
    assert analysis.preview is not None
    assert analysis.preview.entry_name == "first"
    assert analysis.preview.title == "Primary title"
    excerpt_lines = analysis.preview.source_excerpt.splitlines()
    assert excerpt_lines[0] == "@uzon_calc('Decorator title')"
    assert len(excerpt_lines) == 14
    assert excerpt_lines[-1].endswith("...")


@pytest.mark.parametrize(
    ("entry_source", "expected_title"),
    [
        (
            "@uzon_calc('Decorator title')\ndef sheet():\n"
            "    H1(dynamic_title)\n    doc_title(title='Document title')\n",
            "Document title",
        ),
        (
            "@uzon_calc(name='Decorator title')\ndef sheet():\n    pass\n",
            "Decorator title",
        ),
        ("@uzon_calc\ndef sheet():\n    pass\n", "fallback_report"),
    ],
)
def test_archive_analysis_title_fallbacks(
    tmp_path,
    entry_source: str,
    expected_title: str,
):
    """Dynamic or missing titles should use the documented static fallbacks.

    Args:
        tmp_path: Pytest temporary directory fixture.
        entry_source: Entry source exercising one title fallback branch.
        expected_title: Title expected from static analysis.

    Returns:
        None.

    Raises:
        AssertionError: When the configured fallback order changes.
    """
    script_path = tmp_path / "fallback_report.py"
    script_path.write_text(entry_source, encoding="utf-8")

    analysis = analyze_archive_script(script_path)

    assert analysis.preview is not None
    assert analysis.preview.title == expected_title


def test_zip_command_requires_uzon_calc_entry(tmp_path, capsys):
    """入口脚本没有 @uzon_calc 时，打包应失败且不生成归档。"""
    script_path = tmp_path / "report.py"
    archive_path = tmp_path / "report.uzc"
    script_path.write_text(
        "def sheet():\n    return 'missing decorator'\n", encoding="utf-8"
    )

    exit_code = cli.main(["zip", "-p", str(script_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "未找到 @uzon_calc 装饰的入口函数" in captured.err
    assert not archive_path.exists()


def test_zip_archive_runs_existing_main_guard_like_python_file(tmp_path):
    """已有 __main__ 入口时，python report.uzc 应按原脚本入口执行。"""
    _write_uzoncalc_stub(tmp_path)
    script_path = tmp_path / "report.py"
    archive_path = tmp_path / "report.uzc"
    script_path.write_text(
        "\n".join(
            [
                "import sys",
                "from helper import message",
                "import uzoncalc",
                "",
                "@uzoncalc.uzon_calc()",
                "def sheet():",
                "    return message()",
                "",
                "if __name__ == '__main__':",
                "    print('main:' + sheet() + ':' + sys.argv[1])",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "helper.py").write_text(
        "def message():\n    return 'hello'\n", encoding="utf-8"
    )

    assert cli.main(["zip", "-p", str(script_path)]) == 0

    result = subprocess.run(
        [sys.executable, str(archive_path), "arg-value"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert result.stdout.strip() == "main:hello:arg-value"


def test_zip_archive_adds_view_main_for_single_entry_without_main_guard(tmp_path):
    """没有 __main__ 入口且只有一个计算入口时，归档应自动调用 view(entry)。"""
    _write_uzoncalc_stub(tmp_path)
    script_path = tmp_path / "report.py"
    archive_path = tmp_path / "custom.uzc"
    script_path.write_text(
        "\n".join(
            [
                "from nested.calc import message",
                "from uzoncalc import uzon_calc",
                "",
                "@uzon_calc",
                "def sheet():",
                "    return message()",
                "",
            ]
        ),
        encoding="utf-8",
    )
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested_dir.joinpath("__init__.py").write_text("", encoding="utf-8")
    nested_dir.joinpath("calc.py").write_text(
        "def message():\n    return 'auto-main'\n", encoding="utf-8"
    )

    assert cli.main(["zip", "-p", str(script_path), "-o", str(archive_path)]) == 0

    result = subprocess.run(
        [sys.executable, str(archive_path)],
        check=True,
        text=True,
        capture_output=True,
    )

    assert result.stdout.strip() == "view:auto-main"


def test_zip_archive_is_valid_png_with_embedded_zip(tmp_path):
    """The generated archive should be a loadable PNG containing a valid ZIP.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None.

    Raises:
        AssertionError: When PNG, ZIP, or manifest contracts are invalid.
        OSError: When Pillow cannot decode the generated thumbnail.
    """
    _write_uzoncalc_stub(tmp_path)
    script_path = tmp_path / "report.py"
    archive_path = tmp_path / "report.uzc"
    script_path.write_text(
        "\n".join(
            [
                "from uzoncalc import uzon_calc",
                "",
                "@uzon_calc",
                "def sheet():",
                "    H1('结构计算缩略图')",
                "    return 'thumbnail'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert cli.main(["zip", "-p", str(script_path)]) == 0

    chunks = _read_png_chunks(archive_path)
    assert [chunk_type for chunk_type, _ in chunks].count(b"uzCa") == 1
    with Image.open(archive_path) as thumbnail:
        thumbnail.load()
        assert thumbnail.format == "PNG"
        assert thumbnail.size == (1280, 720)

    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        manifest = json.loads(
            archive.read("__uzoncalc_bundle__/manifest.json").decode("utf-8")
        )
    assert manifest["format_version"] == 2
    assert manifest["thumbnail"] == {
        "entry_name": "sheet",
        "title": "结构计算缩略图",
        "width": 1280,
        "height": 720,
    }


def test_thumbnail_rendering_falls_back_when_system_fonts_are_missing(
    monkeypatch,
):
    """Missing system fonts should warn and still produce a loadable thumbnail.

    Args:
        monkeypatch: Pytest fixture used to remove configured font candidates.

    Returns:
        None.

    Raises:
        AssertionError: When fallback rendering does not produce valid PNG bytes.
    """
    monkeypatch.setattr(cli_thumbnail, "_TITLE_FONT_CANDIDATES", ())
    monkeypatch.setattr(cli_thumbnail, "_CODE_FONT_CANDIDATES", ())
    preview = ArchiveEntryPreview(
        entry_name="sheet",
        title="Fallback title",
        source_excerpt="@uzon_calc\ndef sheet():\n    pass",
    )

    with pytest.warns(RuntimeWarning, match="Pillow 默认字体"):
        thumbnail_png = render_archive_thumbnail(preview)

    assert thumbnail_png.startswith(_PNG_SIGNATURE)
    with Image.open(BytesIO(thumbnail_png)) as thumbnail:
        thumbnail.load()
        assert thumbnail.size == (1280, 720)


def test_png_zip_container_preserves_existing_output_on_writer_failure(tmp_path):
    """A ZIP writer failure should not replace an existing archive.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        None.

    Raises:
        AssertionError: When atomic replacement or temporary cleanup regresses.
    """
    output_path = tmp_path / "existing.uzc"
    output_path.write_bytes(b"existing archive")
    preview = ArchiveEntryPreview(
        entry_name="sheet",
        title="Atomic output",
        source_excerpt="@uzon_calc\ndef sheet():\n    pass",
    )
    thumbnail_png = render_archive_thumbnail(preview)

    def write_failing_zip(archive_file) -> None:
        """Write partial bytes and raise to simulate ZIP creation failure.

        Args:
            archive_file: Temporary seekable archive stream.

        Returns:
            None.

        Raises:
            RuntimeError: Always raised after writing partial payload bytes.
        """
        archive_file.write(b"partial zip")
        raise RuntimeError("simulated writer failure")

    with pytest.raises(RuntimeError, match="simulated writer failure"):
        write_png_zip_container(output_path, thumbnail_png, write_failing_zip)

    assert output_path.read_bytes() == b"existing archive"
    assert list(tmp_path.glob(".existing.uzc.*.tmp")) == []


def test_zip_command_rejects_multiple_entries_without_main_guard(tmp_path, capsys):
    """没有 __main__ 且存在多个计算入口时，应要求用户显式添加入口。"""
    script_path = tmp_path / "report.py"
    script_path.write_text(
        "\n".join(
            [
                "from uzoncalc import uzon_calc",
                "",
                "@uzon_calc",
                "def first():",
                "    return 'first'",
                "",
                "@uzon_calc()",
                "def second():",
                "    return 'second'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(["zip", "-p", str(script_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "存在多个 @uzon_calc 入口" in captured.err
    assert not (tmp_path / "report.uzc").exists()


def test_zip_archive_collects_static_local_imports_only(tmp_path):
    """打包应包含静态引用的本地模块和包初始化文件，排除未引用模块。"""
    _write_uzoncalc_stub(tmp_path)
    script_path = tmp_path / "report.py"
    script_path.write_text(
        "\n".join(
            [
                "from package.tool import message",
                "from uzoncalc import uzon_calc",
                "",
                "@uzon_calc",
                "def sheet():",
                "    return message()",
                "",
                "if __name__ == '__main__':",
                "    print(sheet())",
                "",
            ]
        ),
        encoding="utf-8",
    )
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    package_dir.joinpath("__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    package_dir.joinpath("tool.py").write_text(
        "def message():\n    return 'package'\n", encoding="utf-8"
    )
    (tmp_path / "unused.py").write_text("VALUE = 'unused'\n", encoding="utf-8")

    assert cli.main(["zip", "-p", str(script_path)]) == 0

    with zipfile.ZipFile(tmp_path / "report.uzc") as archive:
        names = set(archive.namelist())

    assert "__main__.py" in names
    assert "__uzoncalc_bundle__/manifest.json" in names
    assert "__uzoncalc_bundle__/src/report.py" in names
    assert "__uzoncalc_bundle__/src/package/__init__.py" in names
    assert "__uzoncalc_bundle__/src/package/tool.py" in names
    assert "__uzoncalc_bundle__/src/unused.py" not in names
