"""测试插桩后行号对应是否正确"""

from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import *


@uzon_calc()
def test_calc():
    """测试行号对应"""
    # 这是一个赋值
    x = 10

    # 这是另一个赋值
    y = 20

    # 这里故意引发一个错误 - 第22行
    z = x / 0  # 除以零错误

    return z


if __name__ == "__main__":
    print("测试插桩后的行号对应...")
    print("=" * 60)

    try:
        ctx = run_sync(test_calc)
        print("计算完成")
    except Exception as e:
        print("捕获到异常:")
        print(f"异常类型: {type(e).__name__}")
        print(f"异常信息: {e}")
        print("\n完整堆栈:")
        traceback.print_exc()

        # 检查堆栈中是否包含正确的行号
        tb = traceback.extract_tb(e.__traceback__)
        print("\n堆栈帧分析:")
        for frame in tb:
            if "test_line_numbers.py" in frame.filename:
                print(f"  文件: {frame.filename}")
                print(f"  函数: {frame.name}")
                print(f"  行号: {frame.lineno}")
                print(f"  代码: {frame.line}")

                # 验证行号
                if frame.name == "test_calc" and frame.lineno == 22:
                    print("  ✓ 行号正确！指向了 'z = x / 0' 这一行")
                else:
                    print(f"  ✗ 行号可能不正确（期望 22，实际 {frame.lineno}）")
