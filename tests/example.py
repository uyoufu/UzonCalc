from pathlib import Path
import sys
import numpy as np

# Ensure project root is on sys.path so `import core` works when running
# this script from the `core` folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from uzoncalc import *


@uzon_calc()
async def sheet():
    """
    示例计算函数，演示 UI 交互
    这个函数可以：
    1. 通过 run_sync() 手动调用 - 自动使用默认值
    2. 通过 API 调用 - 由前端提供用户输入
    """

    # 第一个 UI 交互
    inputs1 = await UI(
        "输入数据",
        fields=[
            Field(name="field1", label="字段 1", type=FieldType.number, default=10),
            Field(name="field2", label="字段 2", type=FieldType.number, default=20),
        ],
    )

    # 使用用户输入
    field1 = inputs1["field1"]
    field2 = inputs1["field2"]

    # 计算
    result = field1 + field2

    # 第二个 UI 交互
    inputs2 = await UI(
        "确认结果",
        fields=[
            Field(
                name="confirm",
                label=f"结果是 {result}，是否继续？",
                type=FieldType.checkbox,
                default=True,
            ),
        ],
    )

    if inputs2.get("confirm"):
        final_result = result * 2
    else:
        final_result = result

    # 保存输出
    save("../output/example.html")


if __name__ == "__main__":
    # 测试模式 1: run_sync 静默执行，使用默认值
    print("=" * 60)
    print("模式 1: run_sync 静默执行")
    print("=" * 60)
    
    # 可以通过 defaults 传入自定义值
    defaults = {
        "field1": 15,
        "field2": 25,
        "confirm": True,
    }
    ctx = run_sync(sheet, defaults=defaults)
    print("✓ run_sync 执行完成，UI 自动使用了默认值")
    print(f"生成的 HTML 长度: {len(ctx.html_content())} 字符\n")
    
    # 测试模式 2: 不传入 defaults，使用字段定义的默认值
    print("=" * 60)
    print("模式 2: run_sync 使用字段默认值")
    print("=" * 60)
    ctx2 = run_sync(sheet)
    print("✓ run_sync 执行完成，UI 使用了字段定义的默认值 (field1=10, field2=20)")
    print(f"生成的 HTML 长度: {len(ctx2.html_content())} 字符\n")
    
    print("\n提示：在 API/sandbox 模式下，UI 会返回定义给前端，等待用户输入")
