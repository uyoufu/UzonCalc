"""测试 show/hide 的作用域功能"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc.setup import uzon_calc
from uzoncalc.utils import *


@uzon_calc()
def test_hide_show_scope():
    """测试在子块中调用 show() 后，退出子块应该恢复外部的 hide() 状态"""
    
    a = 1  # 应该显示
    
    hide()
    b = 2  # 不应该显示
    
    if True:
        c = 3  # 不应该显示（继承外部的 hide）
        show()
        d = 4  # 应该显示（在子块中调用了 show）
        e = 5  # 应该显示
    
    # 退出 if 块后，期望恢复 hide() 状态
    f = 6  # 不应该显示（应该恢复外部的 hide 状态）
    
    show()
    g = 7  # 应该显示
    
    save("../output/test_show_hide_scope.html")


if __name__ == "__main__":
    test_hide_show_scope()
    print("测试完成，请查看 output/test_show_hide_scope.html")
