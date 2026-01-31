"""详细调试插桩过程中的行号变化"""
from pathlib import Path
import sys
import inspect
import ast
import textwrap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def debug_function():
    """原始函数 - 第11行"""
    x = 10  # 第13行
    y = 20  # 第14行
    z = x / 0  # 第15行
    return z


if __name__ == "__main__":
    from uzoncalc.handcalc.ast_visitor import AstNodeVisitor
    
    print("=" * 60)
    print("第1步：获取原始函数信息")
    print("=" * 60)
    print(f"函数实际行号: {debug_function.__code__.co_firstlineno}")
    
    # 获取源码
    src = inspect.getsource(debug_function)
    print(f"\n源码:")
    for i, line in enumerate(src.split('\n'), start=1):
        print(f"{i:3}: {line}")
    
    # 解析
    print("\n" + "=" * 60)
    print("第2步：解析AST")
    print("=" * 60)
    src_dedented = textwrap.dedent(src)
    mod = ast.parse(src_dedented)
    
    for node in mod.body:
        if isinstance(node, ast.FunctionDef):
            print(f"函数定义行号: {node.lineno}")
            print(f"函数体语句:")
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    print(f"  行 {stmt.lineno}: 文档字符串")
                elif isinstance(stmt, ast.Assign):
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        print(f"  行 {stmt.lineno}: {target.id} = ...")
                elif isinstance(stmt, ast.Return):
                    print(f"  行 {stmt.lineno}: return ...")
    
    # 移除装饰器
    print("\n" + "=" * 60)
    print("第3步：移除装饰器")
    print("=" * 60)
    original_lineno = None
    for node in mod.body:
        if isinstance(node, ast.FunctionDef) and node.name == "debug_function":
            original_lineno = node.lineno
            node.decorator_list = []
            print(f"函数原始 lineno: {original_lineno}")
            break
    
    # 应用visitor
    print("\n" + "=" * 60)
    print("第4步：应用插桩visitor")
    print("=" * 60)
    visitor = AstNodeVisitor()
    mod = visitor.visit(mod)
    
    for node in mod.body:
        if isinstance(node, ast.FunctionDef):
            print(f"插桩后函数定义行号: {node.lineno}")
            print(f"函数体语句:")
            for i, stmt in enumerate(node.body):
                if isinstance(stmt, ast.Expr):
                    if isinstance(stmt.value, ast.Call):
                        func_name = ""
                        if isinstance(stmt.value.func, ast.Name):
                            func_name = stmt.value.func.id
                        if func_name.startswith('__uzon'):
                            print(f"  [{i}] 行 {stmt.lineno}: 记录调用")
                        else:
                            print(f"  [{i}] 行 {stmt.lineno}: 其他表达式")
                    elif isinstance(stmt.value, ast.Constant):
                        print(f"  [{i}] 行 {stmt.lineno}: 常量")
                elif isinstance(stmt, ast.Assign):
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        print(f"  [{i}] 行 {stmt.lineno}: {target.id} = ...")
                elif isinstance(stmt, ast.Return):
                    print(f"  [{i}] 行 {stmt.lineno}: return ...")
    
    # Fix missing locations
    print("\n" + "=" * 60)
    print("第5步：fix_missing_locations")
    print("=" * 60)
    ast.fix_missing_locations(mod)
    print("完成")
    
    # 计算偏移并应用
    print("\n" + "=" * 60)
    print("第6步：计算并应用行号偏移")
    print("=" * 60)
    actual_lineno = debug_function.__code__.co_firstlineno
    lineno_offset = actual_lineno - original_lineno
    print(f"实际行号: {actual_lineno}")
    print(f"AST行号: {original_lineno}")
    print(f"偏移量: {lineno_offset}")
    
    ast.increment_lineno(mod, lineno_offset)
    
    for node in mod.body:
        if isinstance(node, ast.FunctionDef):
            print(f"\n调整后函数定义行号: {node.lineno}")
            print(f"函数体语句:")
            for i, stmt in enumerate(node.body):
                if isinstance(stmt, ast.Expr):
                    if isinstance(stmt.value, ast.Call):
                        func_name = ""
                        if isinstance(stmt.value.func, ast.Name):
                            func_name = stmt.value.func.id
                        if func_name.startswith('__uzon'):
                            print(f"  [{i}] 行 {stmt.lineno}: 记录调用")
                elif isinstance(stmt, ast.Assign):
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        print(f"  [{i}] 行 {stmt.lineno}: {target.id} = ...")
                elif isinstance(stmt, ast.Return):
                    print(f"  [{i}] 行 {stmt.lineno}: return ...")
