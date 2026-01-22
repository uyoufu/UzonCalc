"""测试 show/hide 的嵌套作用域功能"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc.setup import uzon_calc
from uzoncalc.utils import *


@uzon_calc()
def test_nested_scope():
    """测试嵌套块中的 show/hide 作用域"""
    
    a = 1  # 应该显示
    
    hide()
    b = 2  # 不应该显示
    
    if True:
        c = 3  # 不应该显示
        show()
        d = 4  # 应该显示
        
        if True:
            e = 5  # 应该显示（继承外部的 show）
            hide()
            f = 6  # 不应该显示
        
        g = 7  # 应该显示（退出内部 if 后恢复 show 状态）
    
    h = 8  # 不应该显示（退出外部 if 后恢复 hide 状态）
    
    show()
    i = 9  # 应该显示
    
    save("../output/test_nested_scope.html")


if __name__ == "__main__":
    test_nested_scope()
    print("测试完成，请查看 output/test_nested_scope.html")
    print("预期显示: a=1, d=4, e=5, g=7, i=9")
