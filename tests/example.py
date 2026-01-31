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
    run_sync(sheet)
