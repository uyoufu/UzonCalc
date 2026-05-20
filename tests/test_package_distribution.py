import os
import subprocess
import sys
import tarfile
import venv
import zipfile
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
    "uzoncalc/__init__.py",
    "uzoncalc/template/calc_template.html",
}


def build_distribution_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    """构建临时发行包，避免复用仓库内旧 dist 产物。"""
    output_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(output_dir)],
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

    with tarfile.open(sdist_path) as sdist_file:
        sdist_names = set(sdist_file.getnames())
    for required_suffix in SDIST_REQUIRED_SUFFIXES:
        assert any(name.endswith(required_suffix) for name in sdist_names)


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
