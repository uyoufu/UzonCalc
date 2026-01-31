"""调试行号偏移计算"""
from pathlib import Path
import sys
import inspect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import uzon_calc


@uzon_calc()
def test_func():
    x = 10  # Line 13
    y = 20  # Line 14
    z = x / 0  # Line 15
    return z


if __name__ == "__main__":
    # 获取原始函数
    original_func = test_func.__wrapped__ if hasattr(test_func, '__wrapped__') else test_func
    
    print("=" * 60)
    print("函数信息:")
    print("=" * 60)
    print(f"函数名: {original_func.__name__}")
    print(f"实际行号 (co_firstlineno): {original_func.__code__.co_firstlineno}")
    
    # 获取源码
    src = inspect.getsource(original_func)
    print(f"\n源码 (前5行):")
    lines = src.split('\n')[:5]
    for i, line in enumerate(lines, start=1):
        print(f"  {i}: {line}")
    
    # 解析 AST
    import ast
    import textwrap
    src_dedented = textwrap.dedent(src)
    tree = ast.parse(src_dedented)
    
    print(f"\nAST 解析后:")
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            print(f"  FunctionDef '{node.name}' lineno: {node.lineno}")
            print(f"  装饰器数量: {len(node.decorator_list)}")
            for i, dec in enumerate(node.decorator_list):
                print(f"    装饰器 {i+1} lineno: {dec.lineno}")
    
    print(f"\n行号计算:")
    print(f"  原始函数实际行号: {original_func.__code__.co_firstlineno}")
    
    # 模拟插桩过程中的行号计算
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == original_func.__name__:
            original_ast_lineno = node.lineno
            actual_lineno = original_func.__code__.co_firstlineno
            offset = actual_lineno - original_ast_lineno
            
            print(f"  AST 中函数起始行号: {original_ast_lineno}")
            print(f"  计算的偏移量: {offset}")
            print(f"  应用偏移后的行号: {original_ast_lineno + offset}")
