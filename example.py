from pint import UnitRegistry
from core.setup import uzon_calc


@uzon_calc()
def sheet(*, unit: UnitRegistry):

    from core.renders.elements import p, div, span, input
    from core.renders.options import hide, show

    speed2 = 10 * unit.m / unit.second**2


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    props = {"field1"}  # 这里按你的业务填入 inputs
    # 异步调用 setup
    ctx = sheet()  # type: ignore
    print("\n".join(ctx.contents))
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
