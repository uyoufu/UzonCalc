import ast
from pathlib import Path
import astpretty

current_dir = Path(__file__).parent

with open(current_dir / "example.py", "r", encoding="utf-8") as f:
    code = f.read()

tree = ast.parse(code)

# 美化后保存到 ast_print.ast
with open(current_dir / "ast_print.ast", "w", encoding="utf-8") as f:
    result = astpretty.pformat(tree)
    f.write(result)

print("AST 已保存到 ast_print.ast")
