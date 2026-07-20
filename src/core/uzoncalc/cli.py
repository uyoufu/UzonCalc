"""
UzonCalc CLI 入口

用法：
    uzoncalc path/to/script.py
    uzoncalc path/to/script.py --output path/to/output.html
    uzoncalc zip -p path/to/script.py
    uzoncalc run path/to/report.png
"""

import argparse
import importlib.util
import inspect
import os
from pathlib import Path
import sys

from .cli_core.cli_archive import create_uzc_archive
from .cli_core.cli_archive_runtime import run_v3_archive
from .http_server import DEFAULT_SERVER_PORT, serve_reloadable_html

# 环境变量名：设置后 doc.save() 将变为空操作
_CLI_MODE_ENV = "UZONCALC_CLI_MODE"


def _load_module_from_path(script_path: str):
    """将脚本作为独立模块加载并返回，不执行顶层代码中的 if __name__=="__main__" 块"""
    spec = importlib.util.spec_from_file_location("_uzoncalc_script", script_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载脚本模块: {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _find_entry_functions(module) -> list:
    """查找模块中所有被 @uzon_calc 装饰过的入口函数"""
    entries = []
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if getattr(obj, "_uzon_calc_entry", False):
            entries.append(obj)
    return entries


def _render_ctx_html(ctx) -> str:
    """将 CalcContext 渲染为完整 HTML，逻辑与 doc.save() 一致"""
    from .template.utils import render_html_template

    # 统一 CLI 保存和预览服务使用的 HTML 渲染入口
    content = ctx.html_content()
    return render_html_template(content, ctx.options)


def _save_ctx(ctx, output_path: str | None, script_path: str) -> str:
    """将 CalcContext 渲染并保存为 HTML，逻辑与 doc.save() 一致"""
    # 确定文件名
    if output_path:
        filename = output_path
    else:
        # 默认：脚本所在目录 + 文档标题（或脚本名）
        title = (
            ctx.options.doc_title or os.path.splitext(os.path.basename(script_path))[0]
        )
        if not title.endswith(".html"):
            title += ".html"
        filename = os.path.join(os.path.dirname(script_path), title)

    if not filename.endswith(".html"):
        filename += ".html"

    filename = os.path.abspath(filename)

    # 渲染 HTML
    html_output = _render_ctx_html(ctx)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"Document saved to (open with browser): file:///{filename}")
    return html_output


def _run_script_contexts(script_path: str) -> list:
    """加载脚本并执行所有计算入口，返回上下文列表。"""
    # 设置 CLI 模式环境变量，使脚本内 doc.save() 变为空操作
    os.environ[_CLI_MODE_ENV] = "1"
    try:
        module = _load_module_from_path(script_path)
    except Exception as e:
        print(f"Error: 脚本加载失败: {e}", file=sys.stderr)
        raise
    finally:
        os.environ.pop(_CLI_MODE_ENV, None)

    # 查找入口函数
    entries = _find_entry_functions(module)
    if not entries:
        raise RuntimeError("未找到 @uzon_calc 装饰的入口函数")

    # 执行所有入口函数，多个入口时由调用方决定如何处理结果
    from .startup import run_sync

    contexts = []
    for entry_fn in entries:
        try:
            ctx = run_sync(entry_fn)
        except Exception as e:
            print(
                f"Error: 入口函数 '{entry_fn.__name__}' 执行失败: {e}", file=sys.stderr
            )
            raise
        contexts.append(ctx)
    return contexts


def _render_script_html(script_path: str) -> str:
    """加载脚本并渲染 HTML 字符串，不写入文件。"""
    contexts = _run_script_contexts(script_path)
    html_output = ""
    for ctx in contexts:
        # 服务模式只保留内存结果，多个入口时预览最后一个结果
        html_output = _render_ctx_html(ctx)
    return html_output


def _render_and_save_script_html(script_path: str, output_path: str | None) -> str:
    """加载脚本、执行入口函数、保存文件并返回 HTML。"""
    contexts = _run_script_contexts(script_path)
    html_output = ""
    for ctx in contexts:
        html_output = _save_ctx(ctx, output_path, script_path)
    return html_output


def _serve_html(
    html_output: str,
    script_path: str,
    preferred_port: int = DEFAULT_SERVER_PORT,
):
    """启动带文件监听的本地 HTTP 预览服务。"""
    # CLI 只负责提供脚本渲染回调，服务生命周期交给 http_server 模块
    serve_reloadable_html(
        html_output,
        script_path,
        render_script_html=_render_script_html,
        preferred_port=preferred_port,
    )


def _build_zip_parser() -> argparse.ArgumentParser:
    """创建 zip 子命令参数解析器。

    Args:
        None.

    Returns:
        用于解析 uzoncalc zip 参数的 ArgumentParser。

    Raises:
        None.
    """
    parser = argparse.ArgumentParser(
        prog="uzoncalc zip",
        description="将计算脚本打包为带 PNG 缩略图且可通过 python 运行的 .uzc 归档",
    )
    parser.add_argument(
        "--path",
        "-p",
        required=True,
        help="要打包的 Python 脚本路径",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="输出 PNG/ZIP 格式的 .uzc 文件路径（省略时保存到脚本同目录）",
    )
    return parser


def _run_zip_command(argv: list[str]) -> int:
    """执行 zip 子命令。

    Args:
        argv: zip 子命令后的命令行参数。

    Returns:
        成功时返回 0，失败时返回 1。

    Raises:
        SystemExit: 当 argparse 解析失败时抛出。
    """
    parser = _build_zip_parser()
    args = parser.parse_args(argv)
    try:
        archive_path = create_uzc_archive(
            Path(args.path),
            Path(args.output) if args.output else None,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Archive created: {archive_path}")
    return 0


def _build_archive_run_parser() -> argparse.ArgumentParser:
    """Build the parser for executing one exported v3 archive.

    Args:
        None.

    Returns:
        Parser for the ``uzoncalc run`` command.

    Raises:
        None.
    """
    parser = argparse.ArgumentParser(
        prog="uzoncalc run",
        description="运行 UzonCalc 导出的 v3 PNG/UZC 计算书",
    )
    parser.add_argument("archive", help="要运行的 .png 或 .uzc 计算书归档")
    return parser


def _run_archive_command(argv: list[str]) -> int:
    """Execute one exported v3 archive from the command line.

    Args:
        argv: Arguments following the ``run`` subcommand.

    Returns:
        Zero on success and one when validation or execution fails.

    Raises:
        SystemExit: If command arguments are invalid.
    """
    args = _build_archive_run_parser().parse_args(argv)
    try:
        run_v3_archive(args.archive)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


def _build_legacy_parser() -> argparse.ArgumentParser:
    """创建既有脚本运行命令的参数解析器。

    Args:
        None.

    Returns:
        用于解析既有 CLI 参数的 ArgumentParser。

    Raises:
        None.
    """
    parser = argparse.ArgumentParser(
        prog="uzoncalc",
        description="运行 UzonCalc 计算脚本并导出 HTML 文档",
    )
    parser.add_argument(
        "script",
        help="要运行的 Python 脚本路径",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="输出 HTML 文件路径（省略时保存到脚本所在目录）",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help=f"启动本地 HTTP 预览服务（默认端口 {DEFAULT_SERVER_PORT}，占用时自动递增）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """运行 UzonCalc CLI。

    Args:
        argv: 可选命令行参数；为空时读取 sys.argv[1:]。

    Returns:
        成功时返回 0，失败时返回 1。

    Raises:
        SystemExit: 当 argparse 解析失败时抛出。
        Exception: 既有脚本运行路径中的业务异常会按原行为透传。
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "zip":
        return _run_zip_command(argv[1:])
    if argv and argv[0] == "run":
        return _run_archive_command(argv[1:])

    parser = _build_legacy_parser()
    args = parser.parse_args(argv)

    script_path = os.path.abspath(args.script)
    if not os.path.isfile(script_path):
        print(f"Error: 脚本文件不存在: {script_path}", file=sys.stderr)
        return 1

    output_path = os.path.abspath(args.output) if args.output else None

    # 将脚本所在目录加入 sys.path，支持同目录 import
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        if args.server:
            # 服务模式只返回内存 HTML，避免生成或更新本地文件
            html_output = _render_script_html(script_path)
            _serve_html(html_output, script_path)
        else:
            _render_and_save_script_html(script_path, output_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
