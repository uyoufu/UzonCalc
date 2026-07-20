from __future__ import annotations

import ast
import subprocess
import tempfile
import zipfile
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from cli_utils import run_cli_with_keyboard_interrupt


SERVER = "root@69.63.204.155"
REMOTE_PATH = "/var/www/uzoncalc/examples"
ARCHIVE_NAME = "examples-output.zip"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"


def has_uzon_calc_decorator(source_path: Path) -> bool:
    """检测脚本中是否存在真实的 @uzon_calc 函数装饰器。"""
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if isinstance(target, ast.Name) and target.id == "uzon_calc":
                return True
    return False


def find_example_files(examples_dir: Path) -> list[Path]:
    """递归查找包含 @uzon_calc 装饰器的示例脚本。"""
    return sorted(
        path
        for path in examples_dir.rglob("*.py")
        if path.name != "__init__.py" and has_uzon_calc_decorator(path)
    )


def build_html_output_path(example_path: Path, examples_dir: Path, output_dir: Path) -> Path:
    """根据示例相对路径生成对应的临时 HTML 输出路径。"""
    relative_path = example_path.relative_to(examples_dir).with_suffix(".html")
    return output_dir / relative_path


def run_command(command: list[str], *, console: Console, error_message: str) -> int:
    """运行外部命令，并在失败时输出带退出码的错误信息。"""
    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if completed.returncode != 0:
        console.print(f"[red]ERROR: {error_message} with exit code {completed.returncode}[/red]")
    return completed.returncode


def render_examples(example_files: list[Path], publish_output_dir: Path, *, console: Console) -> int:
    """将示例脚本渲染为临时 HTML 文件。"""
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    )
    with progress:
        task_id = progress.add_task("Rendering examples", total=len(example_files))
        for example_path in example_files:
            output_path = build_html_output_path(example_path, EXAMPLES_DIR, publish_output_dir)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            relative_example = example_path.relative_to(EXAMPLES_DIR)
            relative_output = output_path.relative_to(publish_output_dir)
            progress.console.print(f"[yellow]Rendering:[/yellow] {relative_example} -> {relative_output}")
            exit_code = run_command(
                [
                    "uv",
                    "run",
                    "--project",
                    str(PROJECT_ROOT),
                    "--package",
                    "uzoncalc",
                    "uzoncalc",
                    str(example_path),
                    "--output",
                    str(output_path),
                ],
                console=console,
                error_message=f"Failed to render {relative_example}",
            )
            if exit_code != 0:
                return exit_code
            progress.advance(task_id)
    return 0


def create_examples_archive(publish_output_dir: Path, archive_path: Path) -> list[Path]:
    """将生成的 HTML 文件打包，zip 内路径以输出目录为根。"""
    html_files = sorted(publish_output_dir.rglob("*.html"))
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for html_path in html_files:
            archive.write(html_path, html_path.relative_to(publish_output_dir))
    return html_files


def upload_and_extract_archive(archive_path: Path, *, console: Console) -> int:
    """上传压缩包到服务器并在远端解压。"""
    console.rule(f"[cyan]Uploading to {SERVER}:{REMOTE_PATH}[/cyan]")
    exit_code = run_command(
        ["ssh", SERVER, f"mkdir -p {REMOTE_PATH}"],
        console=console,
        error_message="Failed to ensure remote directory",
    )
    if exit_code != 0:
        return exit_code

    console.print(f"Uploading {ARCHIVE_NAME} ...")
    exit_code = run_command(
        ["scp", str(archive_path), f"{SERVER}:{REMOTE_PATH}/{ARCHIVE_NAME}"],
        console=console,
        error_message="Upload failed",
    )
    if exit_code != 0:
        return exit_code
    console.print("[green]Upload successful.[/green]")

    console.rule("[cyan]Extracting on server[/cyan]")
    return run_command(
        [
            "ssh",
            SERVER,
            f"cd {REMOTE_PATH} && unzip -o {ARCHIVE_NAME} && rm -f {ARCHIVE_NAME} && echo 'Extraction complete.'",
        ],
        console=console,
        error_message="Extraction failed",
    )


def main(*, console: Console | None = None) -> int:
    """发布示例计算书 HTML 到生产服务器。"""
    output_console = console or Console(highlight=False)
    output_console.rule("[cyan]Rendering example scripts[/cyan]")

    if not EXAMPLES_DIR.exists():
        output_console.print(f"[red]ERROR: Examples directory not found: {EXAMPLES_DIR}[/red]")
        return 1

    with tempfile.TemporaryDirectory(prefix="uzoncalc-publish-examples-") as temp_root_text:
        temp_root = Path(temp_root_text)
        publish_output_dir = temp_root / "html"
        archive_path = temp_root / ARCHIVE_NAME
        publish_output_dir.mkdir(parents=True, exist_ok=True)

        example_files = find_example_files(EXAMPLES_DIR)
        if not example_files:
            output_console.print(f"[red]ERROR: No @uzon_calc example scripts found in {EXAMPLES_DIR}[/red]")
            return 1

        exit_code = render_examples(example_files, publish_output_dir, console=output_console)
        if exit_code != 0:
            return exit_code

        output_console.rule("[cyan]Packaging output files[/cyan]")
        html_files = create_examples_archive(publish_output_dir, archive_path)
        if not html_files:
            output_console.print(f"[red]ERROR: No HTML files generated in {publish_output_dir}[/red]")
            return 1

        output_console.print(f"Found {len(html_files)} HTML file(s):")
        for html_path in html_files:
            output_console.print(f"  {html_path.relative_to(publish_output_dir)}")
        output_console.print(f"[green]Archive created: {archive_path}[/green]")

        exit_code = upload_and_extract_archive(archive_path, console=output_console)
        if exit_code != 0:
            return exit_code

    output_console.rule("[green]Publish complete[/green]")
    output_console.print(f"Examples published to {SERVER}:{REMOTE_PATH}/")
    return 0


def run_entrypoint(*, console: Console | None = None) -> int:
    """运行脚本入口并复用共享 Ctrl+C 处理。"""
    return run_cli_with_keyboard_interrupt(
        lambda: main(console=console),
        interrupt_message="已取消示例发布",
        console=console,
    )


if __name__ == "__main__":
    raise SystemExit(run_entrypoint())
