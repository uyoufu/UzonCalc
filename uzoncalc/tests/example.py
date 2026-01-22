from pathlib import Path
import sys
import numpy as np

# Ensure project root is on sys.path so `import core` works when running
# this script from the `core` folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from uzoncalc.setup import uzon_calc
from uzoncalc.utils import *


@uzon_calc()
def sheet():

    width = 1 * unit.meter
    gtZero = True if width.magnitude > 0 else False

    hide()

    def compute_area(w: float, l: float) -> float:
        hide()
        area = w * l
        show()
        return area

    if width.magnitude > 0:
        show()

        area2 = compute_area(1, 2)

        length = 2 * width

    save("../../output/example.html")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    props = {"field1"}  # 这里按你的业务填入 inputs
    # 异步调用 setup
    sheet()  # type: ignore
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
