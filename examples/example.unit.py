from core.uzoncalc import *


@uzon_calc()
async def sheet():
    doc_title("单位计算示例")

    H2("截面应力计算")

    "截面宽度："
    b = 300 * unit.millimeter
    alias("b", "截面宽度 b")

    "截面高度："
    h = 500 * unit.millimeter
    alias("h", "截面高度 h")

    "轴向力："
    N = 100 * unit.kilonewton
    alias("N", "轴向力 N")

    "截面面积："
    A = b * h
    alias("A", "截面面积 A")

    "截面应力："
    sigma = N / A

    save("../output/example_unit.html")


if __name__ == "__main__":
    ctx = run_sync(sheet)
    print(ctx.html_content)
