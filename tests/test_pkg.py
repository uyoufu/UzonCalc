from uzoncalc import *


@uzon_calc()
async def sheet():
    doc_title("hello_uzoncalc")

    "Hello, UzonCalc!"

    save()


if __name__ == "__main__":
    sheet()
