"""
UzonCalc CLI 入口

用法：
    uzoncalc path/to/script.py
    uzoncalc path/to/script.py --output path/to/output.html
"""

import argparse
import importlib.util
import inspect
import os
import sys

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


def _save_ctx(ctx, output_path: str | None, script_path: str):
    """将 CalcContext 渲染并保存为 HTML，逻辑与 doc.save() 一致"""
    from core.uzoncalc.template.utils import render_html_template

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
    content = ctx.html_content()
    html_output = render_html_template(content, ctx.options)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"Document saved to (open with browser): file:///{filename}")


def main():
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
    args = parser.parse_args()

    script_path = os.path.abspath(args.script)
    if not os.path.isfile(script_path):
        print(f"Error: 脚本文件不存在: {script_path}", file=sys.stderr)
        sys.exit(1)

    output_path = os.path.abspath(args.output) if args.output else None

    # 将脚本所在目录加入 sys.path，支持同目录 import
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

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
        print("Error: 未找到 @uzon_calc 装饰的入口函数", file=sys.stderr)
        sys.exit(1)

    # 执行所有入口函数并保存
    from core.uzoncalc.startup import run_sync

    for entry_fn in entries:
        try:
            ctx = run_sync(entry_fn)
        except Exception as e:
            print(
                f"Error: 入口函数 '{entry_fn.__name__}' 执行失败: {e}", file=sys.stderr
            )
            raise
        _save_ctx(ctx, output_path, script_path)


if __name__ == "__main__":
    main()
