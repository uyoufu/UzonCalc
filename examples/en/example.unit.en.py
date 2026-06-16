from core.uzoncalc import *


@uzon_calc()
async def sheet():
    doc_title("Unit Calculation Example")

    H2("Section Stress Calculation")

    "Section width:"
    b = 300 * unit.millimeter
    alias("b", "Section width b")

    "Section height:"
    h = 500 * unit.millimeter
    alias("h", "Section height h")

    "Axial force:"
    N = 100 * unit.kilonewton
    alias("N", "Axial force N")

    "Section area:"
    A = b * h
    alias("A", "Section area A")

    "Section stress:"
    sigma = N / A


if __name__ == "__main__":
    view(sheet)
