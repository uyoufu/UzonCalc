from uzoncalc import *


@uzon_calc()
async def test_float_precision():
    pi = 3.1415926535

    # 默认精度（3 位有效数字）
    pi

    # 修改精度为 6 位有效数字
    decimal(6)
    pi

    # f-string 带格式化规范时，以实际格式化结果为准，不受 float_precision 影响
    f"Value of pi up to 3 decimal places: {pi:.3f}"

    # 回退到默认精度
    decimal(3)
    pi + 1


if __name__ == "__main__":
    ctx = run_sync(test_float_precision)
    print(ctx.contents)
