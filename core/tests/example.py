from pathlib import Path
import sys

# Ensure project root is on sys.path so `import core` works when running
# this script from the `core` folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.setup import uzon_calc
from core.utils import *


@uzon_calc()
def sheet():
    operatorResult = (5 + 3) * 2 - 4 / 2**2
    comparisonResult = (5 > 3) and (2 == 2) or (4 != 5)

    from core.utils.doc import save

    save("../../output/example.html")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    props = {"field1"}  # 这里按你的业务填入 inputs
    # 异步调用 setup
    sheet()  # type: ignore
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
