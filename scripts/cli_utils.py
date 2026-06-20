from __future__ import annotations

from collections.abc import Callable

from rich.console import Console


KEYBOARD_INTERRUPT_EXIT_CODE = 130


def run_cli_with_keyboard_interrupt(
    run_cli: Callable[[], int | None],
    *,
    interrupt_message: str = "已取消操作",
    console: Console | None = None,
) -> int:
    """运行 CLI 入口，并将 Ctrl+C 中断转换为友好退出。"""
    output_console = console or Console(highlight=False)
    try:
        exit_code = run_cli()
    except KeyboardInterrupt:
        output_console.print()
        output_console.print(f"[yellow]{interrupt_message}[/yellow]")
        return KEYBOARD_INTERRUPT_EXIT_CODE
    return 0 if exit_code is None else exit_code
