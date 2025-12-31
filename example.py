from matplotlib import pyplot as plt
from pint import UnitRegistry
from core.setup import uzon_calc


@uzon_calc()
def sheet(*, unit: UnitRegistry):

    from core.renders.elements import p, div, span, input, plot
    from core.renders.options import hide, show

    h = 400 * unit.mm
    b = 300 * unit.mm
    f"截面尺寸: b={b}, h={h}, 面积 A_s={b*h}"
    f"截面尺寸: b={b}, h={h}, 面积 {(A_s :=b*h)}"

    p(f"截面尺寸: b={(c := 300)}, h={(d := 400)} 面积 {(A_s :=b*h)}")

    p(f"面积: {A_s}")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    props = {"field1"}  # 这里按你的业务填入 inputs
    # 异步调用 setup
    ctx = sheet()  # type: ignore
    print("\n".join(ctx.contents))
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
