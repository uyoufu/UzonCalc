from core.uzoncalc import *


@uzon_calc()
async def sheet():
    # 在此处编写计算逻辑

    "土压力计算"

    height = 3 * unit.m
    phi = 0 * unit.degree
    alpha = 0 * unit.degree
    beta = 0 * unit.degree
    gamma = 18 * unit.kN / unit.m**3

    f"计算土层高度：{height}"
    f"土的摩擦角 φ: {phi}"
    f"桥台或挡土墙背与竖直面的夹角 α: {alpha}"
    f"填土表面与水平面的夹角 β: {beta}"
    f"土的重度 γ: {gamma}"

    save("../output/miniExample.html")


if __name__ == "__main__":
    run_sync(sheet)