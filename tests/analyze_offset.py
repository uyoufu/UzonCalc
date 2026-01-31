"""深入分析行号偏移问题"""

from pathlib import Path
import sys
import inspect
import ast
import textwrap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import uzon_calc


@uzon_calc()
def test_func():
    a = 1  # Line 15
    b = 2  # Line 16
    c = a / 0  # Line 17
    return c


if __name__ == "__main__":
    # 原始函数
    orig_func = test_func

    # 查找被装饰前的原始函数
    while hasattr(orig_func, "__wrapped__"):
        orig_func = orig_func.__wrapped__

    print("=" * 70)
    print("函数信息分析")
    print("=" * 70)
    print(f"函数名: {orig_func.__name__}")
    print(f"函数实际起始行号 (co_firstlineno): {orig_func.__code__.co_firstlineno}")

    # 获取完整源码（包含装饰器）
    print("\n" + "=" * 70)
    print("第1步：inspect.getsource 获取的源码（包含装饰器）")
    print("=" * 70)
    src_with_decorator = inspect.getsource(orig_func)
    lines = src_with_decorator.split("\n")
    for i, line in enumerate(lines[:8], start=1):
        print(f"  {i}: {line}")

    # dedent后解析
    print("\n" + "=" * 70)
    print("第2步：textwrap.dedent + ast.parse")
    print("=" * 70)
    src_dedented = textwrap.dedent(src_with_decorator)
    tree = ast.parse(src_dedented)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            print(f"  FunctionDef lineno: {node.lineno}")
            print(f"  装饰器:")
            for dec in node.decorator_list:
                print(f"    - lineno {dec.lineno}: {ast.unparse(dec)}")
            print(f"  函数体语句:")
            for stmt in node.body[:5]:
                lineno = stmt.lineno if hasattr(stmt, "lineno") else "?"
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    print(f"    lineno {lineno}: 文档字符串")
                elif isinstance(stmt, ast.Assign):
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        print(f"    lineno {lineno}: {target.id} = ...")

    # 计算偏移
    print("\n" + "=" * 70)
    print("第3步：计算偏移量")
    print("=" * 70)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == orig_func.__name__:
            ast_func_lineno = node.lineno
            actual_func_lineno = orig_func.__code__.co_firstlineno

            print(f"  AST 中函数定义行号: {ast_func_lineno}")
            print(f"  实际函数定义行号: {actual_func_lineno}")
            print(f"  偏移量: {actual_func_lineno - ast_func_lineno}")

            # 找到第一个赋值语句
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name) and target.id == "a":
                        print(f"\n  AST 中 'a = 1' 的行号: {stmt.lineno}")
                        print(f"  期望实际行号: 15")
                        offset = actual_func_lineno - ast_func_lineno
                        adjusted_lineno = stmt.lineno + offset
                        print(f"  应用偏移后: {adjusted_lineno}")
                        break

    # 重点分析：decorator 占用的行数
    print("\n" + "=" * 70)
    print("问题分析")
    print("=" * 70)
    print("可能的问题:")
    print("1. inspect.getsource 获取的源码包含装饰器")
    print("2. 装饰器 @uzon_calc() 占用1行")
    print("3. def test_func(): 实际在源文件的第12行")
    print(f"4. 但 co_firstlineno 显示为: {orig_func.__code__.co_firstlineno}")
    print("5. 这说明 co_firstlineno 指向的是装饰器的起始行，不是 def 行")
    print("\n推论:")
    print(f"  - 装饰器在文件的第{orig_func.__code__.co_firstlineno}行")
    print(f"  - def 在第{orig_func.__code__.co_firstlineno + 1}行")
    print(f"  - 函数体第一行在第{orig_func.__code__.co_firstlineno + 2}行")
