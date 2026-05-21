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
PACKAGE_VERSION = "1.1.1"
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


def test_workspace_discovers_core_package_from_src_core():
    """核心包项目根目录应位于 src/core，便于 uv workspace 自动发现。"""
    root_config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text("utf-8"))
    core_config_path = REPO_ROOT / "src/core/pyproject.toml"

    assert "src/core" in root_config["tool"]["uv"]["workspace"]["members"]
    assert "src/uzoncalc" not in root_config["tool"]["uv"]["workspace"]["members"]
    assert core_config_path.exists()
    assert not (REPO_ROOT / "src/core/uzoncalc/pyproject.toml").exists()

    core_config = tomllib.loads(core_config_path.read_text("utf-8"))
    assert core_config["project"]["name"] == "uzoncalc"
    assert core_config["project"]["readme"]["file"] == "uzoncalc/README.md"
    assert core_config["tool"]["setuptools"]["packages"]["find"]["where"] == ["."]
    assert core_config["tool"]["setuptools"]["packages"]["find"]["namespaces"] is False


def test_power_shell_scripts_reference_current_core_layout():
    """编译和上传脚本应使用 src/core/uzoncalc 目录结构。"""
    publish_script = (REPO_ROOT / "scripts/publish-uzoncalc-core.ps1").read_text("utf-8")
    upload_script = (REPO_ROOT / "scripts/upload-template-js.ps1").read_text("utf-8")
    setup_script = (REPO_ROOT / "src/api/scripts/setup-embedded-python.ps1").read_text("utf-8-sig")

    assert 'Join-Path $projectRoot "src/core"' in publish_script
    assert 'Join-Path $projectRoot "src/core/uzoncalc/template/js/dist/template.js"' in upload_script
    assert 'Join-Path $REPO_ROOT "src/core"' in setup_script

    assert "src/uzoncalc" not in publish_script
    assert "src/uzoncalc" not in upload_script


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
