"""测试记录调用是否影响行号"""
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import *


@uzon_calc()
def test_exception():
    """测试异常行号"""
    a = 1  # 第14行
    b = 2  # 第15行
    # 下面这行会抛出异常
    c = a / 0  # 第17行
    d = 4  # 第18行
    return c


if __name__ == "__main__":
    print("测试异常行号...")
    try:
        ctx = run_sync(test_exception)
    except ZeroDivisionError:
        tb = traceback.extract_tb(sys.exc_info()[2])
        print("\n异常堆栈:")
        for frame in tb:
            print(f"  文件: {Path(frame.filename).name}")
            print(f"  函数: {frame.name}")
            print(f"  行号: {frame.lineno}")
            print(f"  代码: {frame.line}")
            print()
            
            if "test_record_call_line.py" in frame.filename and frame.name == "test_exception":
                # 读取实际文件内容
                with open(__file__, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                print(f"期望行号: 17 (c = a / 0)")
                print(f"实际行号: {frame.lineno}")
                print(f"实际行内容: {lines[frame.lineno - 1].rstrip()}")
                print(f"第17行内容: {lines[16].rstrip()}")
                
                if frame.lineno == 17:
                    print("\n✓ 行号正确！")
                else:
                    print(f"\n✗ 行号错误（期望17，实际{frame.lineno}，相差{17-frame.lineno}行）")
