import importlib.util
import os
import re
import subprocess
import tarfile
import tomllib
import venv
import zipfile
from email.parser import Parser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_CONFIG = tomllib.loads((REPO_ROOT / "src/core/pyproject.toml").read_text("utf-8"))
PACKAGE_VERSION = CORE_CONFIG["project"]["version"]
WHEEL_REQUIRED_FILES = {
    "uzoncalc/__init__.py",
    "uzoncalc/startup.py",
    "uzoncalc/template/calc_template.html",
}
SDIST_REQUIRED_SUFFIXES = {
    "pyproject.toml",
    "__init__.py",
    "template/calc_template.html",
}
FORBIDDEN_RUNTIME_DEPENDENCIES = {"fastapi", "uvicorn", "twine", "build"}


def load_script_module(module_name: str, script_path: Path):
    """按脚本文件路径导入模块，避免要求脚本文件名是合法模块名。"""
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_scripts_reference_current_core_layout():
    """编译和上传脚本应使用 src/core/uzoncalc 目录结构。"""
    publish_script = (REPO_ROOT / "scripts/publish-uzoncalc-core.ps1").read_text("utf-8")
    upload_script = (REPO_ROOT / "scripts/upload-template-js.ps1").read_text("utf-8")
    setup_script = (REPO_ROOT / "src/api/scripts/setup-embedded-python.py").read_text("utf-8")
    build_win_script = (REPO_ROOT / "scripts/build-win.py").read_text("utf-8")
    build_portable_script = (REPO_ROOT / "src/api/scripts/build-portable.py").read_text("utf-8")

    assert 'Join-Path $projectRoot "src/core"' in publish_script
    assert 'Join-Path $projectRoot "src/core/uzoncalc/template/js"' in upload_script
    assert 'Join-Path $projectRoot "src/core/uzoncalc/template/js/dist/template.js"' in upload_script
    assert "bun run build" in upload_script
    assert 'CORE_PROJECT_ROOT = REPO_ROOT / "src/core"' in setup_script
    assert '"--no-build-isolation", f"{CORE_PROJECT_ROOT}[all]"' in setup_script
    assert 'str(CORE_PROJECT_ROOT)' in setup_script
    assert 'setup-embedded-python.py' in build_portable_script
    assert 'build-portable.py' in build_win_script
    assert "$pipExe" not in setup_script

    assert "src/uzoncalc" not in publish_script
    assert "src/uzoncalc" not in upload_script


def test_embedded_python_setup_filters_released_uzoncalc_requirement():
    """便携包依赖安装不得从 PyPI 解析 uzoncalc，应只保留本地源码安装路径。"""
    module = load_script_module(
        "setup_embedded_python",
        REPO_ROOT / "src/api/scripts/setup-embedded-python.py",
    )

    filtered = module.filter_requirements(
        [
            "fastapi==0.134.0",
            "uzoncalc[all]",
            "uzoncalc>=1.3.0",
            "  -e file:///tmp/uzoncalc",
            "uzoncalc-api==1.3.0",
        ]
    )

    assert filtered == ["fastapi==0.134.0", "uzoncalc-api==1.3.0"]


def test_embedded_python_version_check_rejects_missing_python(tmp_path):
    """已存在环境只有版本匹配时才能复用。"""
    module = load_script_module(
        "setup_embedded_python",
        REPO_ROOT / "src/api/scripts/setup-embedded-python.py",
    )

    assert not module.embedded_python_version_matches(tmp_path / "python.exe", "3.13.14")


def test_embedded_python_setup_installs_local_build_backends(monkeypatch, tmp_path):
    """关闭构建隔离前必须先在嵌入式环境中安装项目声明的构建后端。"""
    module = load_script_module(
        "setup_embedded_python_build_backends",
        REPO_ROOT / "src/api/scripts/setup-embedded-python.py",
    )
    calls = []
    monkeypatch.setattr(module, "pip_install", lambda python_exe, args: calls.append((python_exe, args)))

    python_exe = tmp_path / "python.exe"
    module.install_build_backend_requirements(python_exe)

    assert calls == [(python_exe, ["install", "setuptools>=61.0", "wheel"])]


def test_build_win_reads_cargo_package_version():
    """Windows 整包输出版本号来自 Tauri Cargo package version。"""
    module = load_script_module("build_win", REPO_ROOT / "scripts/build-win.py")

    assert module.get_cargo_package_version(REPO_ROOT / "src/web/src-tauri/Cargo.toml") == "1.3.0"


def test_packaged_cli_uses_published_package_imports():
    """发布后的 CLI 入口不能依赖源码目录中的 core 命名空间。"""
    cli_source = (REPO_ROOT / "src/core/uzoncalc/cli.py").read_text("utf-8")

    assert "core.uzoncalc" not in cli_source


def build_distribution_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    """构建临时发行包，避免复用仓库内旧 dist 产物。"""
    output_dir = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--package", "uzoncalc", "--out-dir", str(output_dir)],
        cwd=REPO_ROOT,
        check=True,
        text=True,
    )

    wheel_path = output_dir / f"uzoncalc-{PACKAGE_VERSION}-py3-none-any.whl"
    sdist_path = output_dir / f"uzoncalc-{PACKAGE_VERSION}.tar.gz"
    assert wheel_path.exists()
    assert sdist_path.exists()
    return wheel_path, sdist_path


def test_distribution_artifacts_include_package_sources(tmp_path):
    wheel_path, sdist_path = build_distribution_artifacts(tmp_path)

    with zipfile.ZipFile(wheel_path) as wheel_file:
        wheel_names = set(wheel_file.namelist())
    assert WHEEL_REQUIRED_FILES <= wheel_names
    assert not any(name.startswith("uzoncalc/uzoncalc/") for name in wheel_names)

    with tarfile.open(sdist_path) as sdist_file:
        sdist_names = set(sdist_file.getnames())
    for required_suffix in SDIST_REQUIRED_SUFFIXES:
        assert any(name.endswith(required_suffix) for name in sdist_names)
    assert not any("/uzoncalc/uzoncalc/" in name for name in sdist_names)


def test_built_wheel_can_be_installed_and_imported(tmp_path):
    wheel_path, _ = build_distribution_artifacts(tmp_path)

    venv_dir = tmp_path / "install-check"
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    python_bin = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    subprocess.run(
        [str(python_bin), "-m", "pip", "install", str(wheel_path)],
        check=True,
        text=True,
    )
    subprocess.run(
        [
            str(python_bin),
            "-c",
            "import uzoncalc; from uzoncalc import run_sync, unit, uzon_calc; print(uzoncalc.__file__)",
        ],
        check=True,
        text=True,
    )


def test_built_wheel_runtime_dependencies_are_core_only(tmp_path):
    """核心包发布依赖不能混入根工具或 API 服务依赖。"""
    wheel_path, _ = build_distribution_artifacts(tmp_path)

    with zipfile.ZipFile(wheel_path) as wheel_file:
        metadata_name = next(
            name for name in wheel_file.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = Parser().parsestr(wheel_file.read(metadata_name).decode("utf-8"))

    runtime_dependencies = set()
    for dependency in metadata.get_all("Requires-Dist", []):
        normalized_name = re.split(r"[<>=!~ ;\[]", dependency, maxsplit=1)[0].lower()
        runtime_dependencies.add(normalized_name)

    assert FORBIDDEN_RUNTIME_DEPENDENCIES.isdisjoint(runtime_dependencies)
