from uzoncalc import *


@uzon_calc()
async def test_float_precision():
    b_f = 10000.2 * unit.millimeter
    alias("b_f", "翼缘宽度 b_翼缘")
    b_f_val = b_f.to(unit.meter).magnitude

    b_f


if __name__ == "__main__":
    ctx = run_sync(test_float_precision)
    ctx.save("../output/test_chain_invoke.html")
    print(ctx.contents)
