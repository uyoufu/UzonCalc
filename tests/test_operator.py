from src.uzoncalc import *


@uzon_calc()
async def sheet():
    doc_title("算术运算示例")

    "加法："
    a = 10
    b = 20
    c = a + b

    "减法："
    d = a - b

    "乘法："
    e = a * b

    "除法："
    f = b / a

    "取余："
    g = b % a

    "幂运算："
    h = a**2

    "混合运算："
    i = a + b * c - d / e + f**2

    save("../output/test_operator.html")


if __name__ == "__main__":
    run_sync(sheet)
