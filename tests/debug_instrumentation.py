"""调试插桩生成的代码，查看实际的 AST 结构"""
from pathlib import Path
import sys
import ast
import inspect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import *


@uzon_calc()
def test_calc():
    """测试行号对应"""
    # 行号 15
    x = 10
    # 行号 17
    y = 20
    # 行号 19
    z = x / 0
    return z


if __name__ == "__main__":
    # 获取插桩后的函数
    from uzoncalc.handcalc.ast_instrument import instrument_function
    instrumented = instrument_function(test_calc.__wrapped__)
    
    # 打印插桩后的代码
    print("插桩后的代码:")
    print("=" * 60)
    try:
        import textwrap
        src = textwrap.dedent(inspect.getsource(test_calc.__wrapped__))
        tree = ast.parse(src)
        
        # 移除装饰器
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "test_calc":
                node.decorator_list = []
                break
        
        # 应用插桩
        from uzoncalc.handcalc.ast_visitor import AstNodeVisitor
        visitor = AstNodeVisitor()
        tree = visitor.visit(tree)
        
        # 打印AST
        print(ast.unparse(tree))
        print()
        print("=" * 60)
        print("\nAST 节点行号信息:")
        print("=" * 60)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if hasattr(node, 'lineno'):
                    target = node.targets[0]
                    if isinstance(target, ast.Name):
                        print(f"赋值语句 '{target.id} = ...' 在第 {node.lineno} 行")
            elif isinstance(node, ast.Expr) and hasattr(node, 'lineno'):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id.startswith('__uzon'):
                            print(f"记录调用在第 {node.lineno} 行")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
