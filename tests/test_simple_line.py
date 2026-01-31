"""测试实际运行时的行号"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import *
import traceback


@uzon_calc()
def simple_test():
    x = 10  # 这是第 13 行
    y = 20  # 这是第 14 行
    z = x / 0  # 这是第 15 行 - 会抛出错误
    return z


if __name__ == "__main__":
    print("测试简单场景的行号...")
    try:
        ctx = run_sync(simple_test)
    except ZeroDivisionError as e:
        print("捕获到 ZeroDivisionError")
        tb = traceback.extract_tb(e.__traceback__)
        for frame in tb:
            if "test_simple_line.py" in frame.filename:
                print(f"\n在函数 '{frame.name}' 中:")
                print(f"  文件: {frame.filename}")
                print(f"  行号: {frame.lineno}")
                print(f"  代码: {frame.line}")
                
                # 检查行号
                if frame.name == "simple_test":
                    if frame.lineno == 15:
                        print("  ✓ 行号正确！")
                    else:
                        print(f"  ✗ 行号错误（期望 15，实际 {frame.lineno}）")
                        # 显示实际内容
                        with open(frame.filename, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            print(f"\n  实际第 {frame.lineno} 行内容: {lines[frame.lineno-1].strip()}")
                            print(f"  期望第 15 行内容: {lines[14].strip()}")
