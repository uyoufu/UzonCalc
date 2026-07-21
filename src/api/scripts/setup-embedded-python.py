from __future__ import annotations

import argparse
import hashlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from rich.console import Console


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SCRIPT_DIR.parents[2]
CORE_PROJECT_ROOT = REPO_ROOT / "src/core"
BUILD_BACKEND_REQUIREMENTS = ["setuptools>=61.0", "wheel"]

CONSOLE = Console(highlight=False)


class SetupError(RuntimeError):
    pass


def write_info(message: str) -> None:
    CONSOLE.print(f"[cyan][INFO][/cyan] {message}")


def write_warn(message: str) -> None:
    CONSOLE.print(f"[yellow][WARN][/yellow] {message}")


def write_error(message: str) -> None:
    CONSOLE.print(f"[red][ERROR][/red] {message}", style="red")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def remove_directory_if_exists(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def copy_directory_contents(source: Path, destination: Path) -> None:
    ensure_directory(destination)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def run_command(command: list[str], *, failure_message: str) -> None:
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SetupError(failure_message)


def pip_install(python_exe: Path, arguments: list[str]) -> None:
    run_command(
        [str(python_exe), "-m", "pip", *arguments, "--no-warn-script-location"],
        failure_message="pip command failed.",
    )


def install_build_backend_requirements(python_exe: Path) -> None:
    write_info("Ensure local source build backends are available...")
    pip_install(python_exe, ["install", *BUILD_BACKEND_REQUIREMENTS])
    write_info("Local source build backends are available")


def test_pip_available(python_exe: Path) -> bool:
    completed = subprocess.run(
        [str(python_exe), "-m", "pip", "--version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def get_dependency_hash_part(path: Path, fallback_name: str) -> str:
    if path.exists():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return f"missing-{fallback_name}"


def embedded_python_version_matches(python_exe: Path, expected_version: str) -> bool:
    if not python_exe.exists():
        return False
    completed = subprocess.run(
        [
            str(python_exe),
            "-c",
            "import sys; print('.'.join(str(part) for part in sys.version_info[:3]))",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and completed.stdout.strip() == expected_version


UZONCALC_REQUIREMENT_RE = re.compile(
    r"^\s*uzoncalc(?:\[[^\]]+\])?(?:\s*(?:===|[<>=!~]=?)\s*[^#;\s]+)?\s*(?:[#;].*)?$",
    re.IGNORECASE,
)


def is_filtered_requirement(line: str) -> bool:
    stripped = line.strip()
    return bool(
        re.match(r"^-e\s+file:", stripped, re.IGNORECASE)
        or UZONCALC_REQUIREMENT_RE.match(stripped)
    )


def filter_requirements(lines: list[str]) -> list[str]:
    return [line for line in lines if not is_filtered_requirement(line)]


def get_windows_embed_arch() -> str:
    machine = platform.machine().lower()
    return "amd64" if machine in {"amd64", "x86_64"} or sys.maxsize > 2**32 else "win32"


def configure_python_path_file(embed_dir: Path) -> None:
    pth_files = sorted(embed_dir.glob("python*._pth"))
    if not pth_files:
        return

    pth_path = pth_files[0]
    write_info(f"Configure {pth_path.name} to enable site-packages...")
    content = pth_path.read_text(encoding="ascii").splitlines()
    new_content = [
        "import site" if line == "#import site" else line for line in content
    ]
    if "import site" not in new_content:
        new_content.append("import site")
    if "Lib\\site-packages" not in new_content:
        new_content.append("Lib\\site-packages")
    pth_path.write_text("\n".join(new_content) + "\n", encoding="ascii")
    write_info("Configuration complete")


def download_file(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url) as response:
        destination.write_bytes(response.read())


def resolve_target_dir(target_dir: str) -> Path:
    target_path = Path(target_dir)
    if target_path.is_absolute():
        return target_path.resolve()
    return (PROJECT_ROOT / target_path).resolve()


def resolve_cache_root(cache_root: str | None) -> Path:
    if not cache_root or not cache_root.strip():
        return (REPO_ROOT / ".cache/desktop-maui/python").resolve()
    cache_path = Path(cache_root)
    if cache_path.is_absolute():
        return cache_path.resolve()
    return (REPO_ROOT / cache_path).resolve()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Setup embedded Python for the UzonCalc API portable package."
    )
    parser.add_argument("--python-version", default="3.13.14")
    parser.add_argument("--target-dir", default="dist/python-embedded")
    parser.add_argument("--cache-root")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    embed_dir = resolve_target_dir(args.target_dir)
    python_exe = embed_dir / "python.exe"
    cache_root = resolve_cache_root(args.cache_root)

    write_info("Start setting up embedded Python...")

    arch = get_windows_embed_arch()
    download_url = f"https://www.python.org/ftp/python/{args.python_version}/python-{args.python_version}-embed-{arch}.zip"
    temp_dir = Path(tempfile.gettempdir())
    zip_file = temp_dir / f"python-{args.python_version}-embed-{arch}.zip"
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_file = temp_dir / "get-pip.py"
    requirements_file = PROJECT_ROOT / "requirements.txt"
    core_pyproject_file = CORE_PROJECT_ROOT / "pyproject.toml"
    dependency_hash_parts = [
        get_dependency_hash_part(requirements_file, "api-requirements"),
        get_dependency_hash_part(core_pyproject_file, "core-pyproject"),
    ]
    requirements_hash = "-".join(dependency_hash_parts)

    cache_key = f"v4-{args.python_version}-{arch}-{requirements_hash}"
    cache_dir = cache_root / cache_key
    cache_python_exe = cache_dir / "python.exe"
    cache_hit = False

    write_info(f"Python cache root: {cache_root}")
    write_info(f"Python cache key: {cache_key}")

    if cache_python_exe.exists() and not embedded_python_version_matches(
        cache_python_exe, args.python_version
    ):
        write_info(
            f"Cached embedded Python version does not match {args.python_version}. Removing cache."
        )
        remove_directory_if_exists(cache_dir)

    if cache_python_exe.exists():
        write_info(
            "Found cached embedded Python environment. Copying to target directory..."
        )
        remove_directory_if_exists(embed_dir)
        copy_directory_contents(cache_dir, embed_dir)
        python_exe = embed_dir / "python.exe"
        cache_hit = True
        write_info(
            "Cached environment copied. Local workspace packages will still be refreshed."
        )

    downloaded_python = False

    if cache_hit:
        write_info("Using cached embedded Python. Skipping download and extraction.")
    elif python_exe.exists():
        if embedded_python_version_matches(python_exe, args.python_version):
            write_info(f"Found existing embedded Python: {embed_dir}")
            write_info(
                "Skipping download and extraction. Continuing with configuration and dependency installation."
            )
        else:
            write_info(
                f"Existing embedded Python is not {args.python_version}. Rebuilding: {embed_dir}"
            )
            remove_directory_if_exists(embed_dir)

    if not cache_hit and not python_exe.exists():
        write_info(f"Download Python {args.python_version} ({arch})...")
        CONSOLE.print(f"  [dim]URL:[/dim] {download_url}")
        try:
            download_file(download_url, zip_file)
            downloaded_python = True
            write_info("Download complete")
        except Exception as exc:  # noqa: BLE001 - preserve the original failure details.
            write_error(f"Download failed: {exc}")
            CONSOLE.print(f"Please manually download and extract to: {embed_dir}")
            CONSOLE.print(f"Download URL: {download_url}")
            raise

    write_info(f"Extract Python to {embed_dir}...")
    if downloaded_python:
        if embed_dir.exists():
            write_info("Target directory already exists. Overwriting...")
            remove_directory_if_exists(embed_dir)
        ensure_directory(embed_dir)
        with zipfile.ZipFile(zip_file) as python_archive:
            python_archive.extractall(embed_dir)
        if not python_exe.exists():
            raise SetupError(f"Python extraction failed. Missing: {python_exe}")
    else:
        write_info("No new Python download. Skipping extraction.")

    if not embedded_python_version_matches(python_exe, args.python_version):
        raise SetupError(
            f"Embedded Python version is not {args.python_version}: {python_exe}"
        )

    write_info("Configure Python environment...")
    configure_python_path_file(embed_dir)

    write_info("Check pip...")
    if test_pip_available(python_exe):
        write_info("pip module is available. Skipping pip installation.")
    else:
        write_info("Install pip...")
        try:
            download_file(get_pip_url, get_pip_file)
            run_command(
                [str(python_exe), str(get_pip_file), "--no-warn-script-location"],
                failure_message="pip installation command failed.",
            )
            if not test_pip_available(python_exe):
                raise SetupError(
                    "pip still cannot run through python -m pip after installation."
                )
            get_pip_file.unlink(missing_ok=True)
            write_info("pip installed")
        except Exception as exc:  # noqa: BLE001 - preserve the original failure details.
            write_error(f"pip installation failed: {exc}")
            raise

    site_packages = embed_dir / "Lib/site-packages"
    ensure_directory(site_packages)

    try:
        install_build_backend_requirements(python_exe)
    except Exception as exc:  # noqa: BLE001 - preserve the original failure details.
        write_error(f"Build backend dependency installation failed: {exc}")
        raise

    write_info("Install third-party dependencies...")
    if cache_hit:
        write_info(
            "Using cached environment. Skipping third-party dependency installation."
        )
    else:
        if requirements_file.exists():
            filtered_requirements_file = temp_dir / "uzoncalc-api-requirements.txt"
            requirements_content = requirements_file.read_text(
                encoding="utf-8"
            ).splitlines()
            filtered_content = filter_requirements(requirements_content)
            filtered_requirements_file.write_text(
                "\n".join(filtered_content) + "\n", encoding="utf-8"
            )

            try:
                pip_install(
                    python_exe, ["install", "-r", str(filtered_requirements_file)]
                )
            except Exception as exc:  # noqa: BLE001 - preserve the original failure details.
                write_error(f"API dependency installation failed: {exc}")
                raise
            finally:
                filtered_requirements_file.unlink(missing_ok=True)
            write_info("API dependencies installed")
        else:
            CONSOLE.print(
                "  [yellow]requirements.txt was not found. Skipping API dependency installation.[/yellow]"
            )

        try:
            write_info(
                "Install core package third-party dependencies from local source..."
            )
            pip_install(
                python_exe,
                ["install", "--no-build-isolation", f"{CORE_PROJECT_ROOT}[all]"],
            )
            run_command(
                [str(python_exe), "-m", "pip", "uninstall", "-y", "uzoncalc"],
                failure_message="Temporary core package uninstall failed.",
            )
        except Exception as exc:  # noqa: BLE001 - preserve the original failure details.
            write_error(f"Core dependency installation failed: {exc}")
            raise

        write_info("Dependencies installed")

    if cache_hit:
        write_info("Current environment came from cache. Skipping cache write.")
    else:
        write_info("Write embedded Python cache...")
        ensure_directory(cache_root)
        remove_directory_if_exists(cache_dir)
        copy_directory_contents(embed_dir, cache_dir)
        write_info(f"Cache complete: {cache_dir}")

    write_info("Install local workspace packages...")
    try:
        pip_install(
            python_exe,
            [
                "install",
                "--no-build-isolation",
                "--no-deps",
                "--force-reinstall",
                str(CORE_PROJECT_ROOT),
            ],
        )
        pip_install(
            python_exe,
            [
                "install",
                "--no-build-isolation",
                "--no-deps",
                "--force-reinstall",
                str(PROJECT_ROOT),
            ],
        )
    except Exception as exc:  # noqa: BLE001 - preserve the original failure details.
        write_error(f"Local workspace package installation failed: {exc}")
        raise

    write_info("Installed local package versions:")
    run_command(
        [str(python_exe), "-m", "pip", "show", "uzoncalc", "uzoncalc-api"],
        failure_message="Local package version check failed.",
    )

    write_info("Check Python dependency consistency...")
    run_command(
        [str(python_exe), "-m", "pip", "check"],
        failure_message="Python dependency consistency check failed.",
    )

    CONSOLE.rule("[bold cyan]Embedded Python setup complete.[/bold cyan]")
    CONSOLE.print()
    CONSOLE.print(f"[green]Python path:[/green] {embed_dir}")
    CONSOLE.print(f"[green]Python executable:[/green] {python_exe}")
    CONSOLE.print()
    write_info("Next steps:")
    CONSOLE.print(f"  1. Test Python: {python_exe} --version")
    CONSOLE.print(f"  2. Run app: {python_exe} main.py")
    CONSOLE.print(
        "  3. Keep the embedded Python environment under dist when distributing"
    )
    CONSOLE.print()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        CONSOLE.print()
        CONSOLE.print("[yellow][WARN] Setup cancelled.[/yellow]")
        raise SystemExit(130)
    except SetupError as exc:
        write_error(str(exc))
        raise SystemExit(1)
