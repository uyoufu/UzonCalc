from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("example")

    "Hello, UzonCalc!"

    w = 10*unit.m
    l = 5*unit.m
    A = w * l

if __name__ == "__main__":
    view(sheet)