"""
将 examples 下以 help. 开头的帮助脚本渲染为 HTML 并保存到 web 端的 public/helps 目录。

脚本约定：
- 匹配 examples/**/help.*.py 文件
- 输出文件名保留原 stem，仅将扩展名替换为 .html（例如 help.zh-CN.py -> help.zh-CN.html）

用法：
    python scripts/update_help_to_web.py
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from rich.console import Console

from cli_utils import run_cli_with_keyboard_interrupt


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
HELPS_OUTPUT_DIR = PROJECT_ROOT / "src" / "web" / "public" / "helps"

HELP_GLOB_PATTERN = "help.*.py"


def find_help_scripts(examples_dir: Path) -> list[Path]:
    """查找 examples 目录下所有以 help. 开头的 Python 帮助脚本。"""
    return sorted(examples_dir.rglob(HELP_GLOB_PATTERN))


def build_output_filename(script_path: Path) -> str:
    """根据帮助脚本文件名生成同名 .html 文件名。"""
    return f"{script_path.stem}.html"


def render_help_script(
    script_path: Path,
    output_path: Path,
    *,
    console: Console,
) -> int:
    """使用 uzoncalc CLI 将帮助脚本渲染为 HTML。"""
    console.print(f"[yellow]Rendering:[/yellow] {script_path} -> {output_path}")
    completed = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PROJECT_ROOT),
            "--package",
            "uzoncalc",
            "uzoncalc",
            str(script_path),
            "--output",
            str(output_path),
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        console.print(
            f"[red]ERROR: Failed to render {script_path} with exit code "
            f"{completed.returncode}[/red]"
        )
    return completed.returncode


def copy_html_into_helps(
    generated_dir: Path,
    scripts: list[Path],
    *,
    console: Console,
) -> int:
    """将临时目录中生成的 HTML 文件拷贝到 public/helps 目录。"""
    if not HELPS_OUTPUT_DIR.exists():
        HELPS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    exit_code = 0
    for script_path in scripts:
        output_name = build_output_filename(script_path)
        source_html = generated_dir / output_name
        target_html = HELPS_OUTPUT_DIR / output_name
        if not source_html.exists():
            console.print(f"[red]ERROR: Missing generated file: {source_html}[/red]")
            exit_code = 1
            continue
        shutil.copy2(source_html, target_html)
        console.print(f"[green]Updated:[/green] {target_html.relative_to(PROJECT_ROOT)}")
    return exit_code


def main(*, console: Console | None = None) -> int:
    """渲染帮助文档并保存到 public/helps 目录。"""
    output_console = console or Console(highlight=False)
    output_console.rule("[cyan]Rendering help documents[/cyan]")

    if not EXAMPLES_DIR.exists():
        output_console.print(f"[red]ERROR: Examples directory not found: {EXAMPLES_DIR}[/red]")
        return 1

    help_scripts = find_help_scripts(EXAMPLES_DIR)
    if not help_scripts:
        output_console.print(
            f"[red]ERROR: No help scripts matching {HELP_GLOB_PATTERN!r} "
            f"found under {EXAMPLES_DIR}[/red]"
        )
        return 1

    with tempfile.TemporaryDirectory(prefix="uzoncalc-update-help-") as temp_root_text:
        temp_root = Path(temp_root_text)
        for script_path in help_scripts:
            output_path = temp_root / build_output_filename(script_path)
            exit_code = render_help_script(
                script_path,
                output_path,
                console=output_console,
            )
            if exit_code != 0:
                return exit_code

        exit_code = copy_html_into_helps(
            temp_root,
            help_scripts,
            console=output_console,
        )
        if exit_code != 0:
            return exit_code

    output_console.rule("[green]Help documents updated[/green]")
    output_console.print(f"Files saved to: {HELPS_OUTPUT_DIR}")
    return 0


def run_entrypoint(*, console: Console | None = None) -> int:
    """运行脚本入口并复用共享 Ctrl+C 处理。"""
    return run_cli_with_keyboard_interrupt(
        lambda: main(console=console),
        interrupt_message="已取消帮助文档更新",
        console=console,
    )


if __name__ == "__main__":
    raise SystemExit(run_entrypoint())