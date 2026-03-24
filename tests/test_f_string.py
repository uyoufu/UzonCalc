from uzoncalc import *


@uzon_calc()
async def test_f_string():
    pi = 3.1415926535
    f"Value of pi up to 3 decimal places: {pi:.3f}"


if __name__ == "__main__":
    ctx = run_sync(test_f_string)
    print(ctx.contents)
    assert all("MText(text=" not in item for item in ctx.contents)
