from src.uzoncalc import *


@uzon_calc()
async def test_float_precision():
    pi = 3.1415926535

    # 默认精度（3 位小数）
    pi

    # 修改精度为 6 位小数
    decimal(6)
    pi

    # f-string 带格式化规范时，以实际格式化结果为准，不受 float_precision 影响
    f"Value of pi up to 3 decimal places: {pi:.3f}"

    # 回退到默认精度
    decimal(3)
    pi + 1


@uzon_calc()
async def test_float_decimal_places():
    value = 1234.56789

    decimal(2)
    value


@uzon_calc()
async def test_float_fstring_default_precision():
    value = 3.200

    decimal(3)
    f"Value without explicit precision: {value}"


if __name__ == "__main__":
    ctx = run_sync(test_float_precision)
    print(ctx.contents)

    ctx = run_sync(test_float_decimal_places)
    assert any("1234.57" in content for content in ctx.contents)

    ctx = run_sync(test_float_fstring_default_precision)
    assert any("3.2" in content for content in ctx.contents)
