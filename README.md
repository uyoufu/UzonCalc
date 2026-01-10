# UzonCalc

UzonCalc is a tool for writing engineering calculation documents using Python. With it, you can write calculation reports as smoothly as writing Python, and benefit from the full Python ecosystem and AI assistance.

## Features

1. Write using Python code — no extra syntax to learn
2. Benefit from the Python ecosystem and AI support
3. Focus on calculations, not layout
4. Output beautiful HTML directly; convertible to PDF and Docx

## Example

``` python
from pathlib import Path
import sys

# Ensure project root is on sys.path so `import core` works when running
# this script from the `core` folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from pint import UnitRegistry
from core.setup import uzon_calc


@uzon_calc()
def sheet(*, unit: UnitRegistry):
    from core.utils.doc import doc_title, page_size
    from core.utils.elements import H1, H2, H3, Plot, p, div, span, input
    from core.utils.options import hide, show

    doc_title("UzonCalc Full Example")
    page_size("A4")

    H1("UzonCalc Full Example")
    "This is a full example demonstrating various features of UzonCalc."

    # description:
    # this is a full example of using UzonCalc.

    H2("Basic Constants")
    # number
    H3("Numbers")
    intNumber = 100
    floatNumber = 3.1415
    scientificNumber = 1.2e3
    complexNumber = 2 + 3j

    H3("Strings")
    helloString = "Hello,"
    uzonCalcString = "UzonCalc!"
    greeting = helloString + uzonCalcString

    H3("String Output")
    # you can output strings directly
    "This is a string output inline."

    """
    This is a string output block.
    It can span multiple lines.
    It will be rendered as paragraph.
    """

    H3("String Formatting")
    name = "Uzon"
    f"Hello, {name}! Welcome to UzonCalc."
    pi = 3.1415926535
    # format are not supported now, will be supported in future
    f"Value of pi up to 3 decimal places: {pi:.3f}"

    H2("Units and Calculations")
    length = 5 * unit.meter
    time = 2 * unit.second
    speed = length / time

    H3("Complex Calculation")

    acceleration = speed / time
    force = 10 * unit.kilogram * acceleration
    stress = force / (length**2)

    H3("Unit Conversion")
    speedKmh = speed.to(unit.kilometer / unit.hour)
    f"Speed in km/h: {speedKmh}"

    # use matplotlib to plot a sine wave
    H2("Plotting Example")
    hide()
    import numpy as np
    import matplotlib.pyplot as plt

    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)
    plt.plot(x, y)
    plt.title("Sine Wave")
    plt.xlabel("x (radians)")
    plt.ylabel("sin(x)")
    plt.grid(True)
    show()
    Plot(plt)

    # sub
    H2("Variable subscription")
    "if you want to make a word to be subscript, you can use _ after it. For example, H_2O will be rendered as H₂."
    f_a = 10 * unit.meter / unit.second**2
    f_x = f_a * 2 * unit.second

    from core.utils.doc import save

    save("../output/example-full.html")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    sheet()  # type: ignore
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")

```

Preview:

![image-20260110162359040](https://oss.uzoncloud.com:2234/public/files/images/image-20260110162359040.png)
