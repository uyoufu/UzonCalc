from pathlib import Path
import sys

# Ensure project root is on sys.path so `import core` works when running
# this script from the `core` folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from matplotlib import pyplot as plt
from pint import UnitRegistry
from core.template.utils import get_html_template
from core.setup import uzon_calc


@uzon_calc()
def sheet(*, unit: UnitRegistry):

    from core.utils.elements import p, div, span, input, plot
    from core.utils.options import hide, show, inline, endline

    q_1 = 0.1 * 8 * 24 * unit.kN / unit.m**3

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
