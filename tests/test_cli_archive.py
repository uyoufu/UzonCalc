import subprocess
import sys
import zipfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/core"))

from uzoncalc import cli


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


def test_zip_command_requires_uzon_calc_entry(tmp_path, capsys):
    """入口脚本没有 @uzon_calc 时，打包应失败且不生成归档。"""
    script_path = tmp_path / "report.py"
    archive_path = tmp_path / "report.uzc"
    script_path.write_text("def sheet():\n    return 'missing decorator'\n", encoding="utf-8")

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
