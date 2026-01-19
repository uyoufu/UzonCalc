from numpy import sqrt
from pathlib import Path
import sys

# When running this script from the `core` folder during development,
# ensure the project root is on sys.path so `import core` works.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.setup import uzon_calc
from core.utils import *
from core.utils_extra.excel import get_excel_table
import numpy as np


@uzon_calc()
def sheet():
    # Document title (shown on printed PDF header-left)
    doc_title("UzonCalc User Guide")

    # Page size (e.g. A3, A4, Letter)
    page_size("A4")

    # Main title
    H1("UzonCalc User Guide")

    Info("This document is generated with UzonCalc.")

    """
    UzonCalc is a Python-based tool for hand-written engineering calculation
    reports. Focus on content and calculation logic; UzonCalc handles result
    rendering, formatting, and typesetting. It supports units, Excel calls,
    tables, charts, and more, enabling reuse of existing Excel models.
    """

    Br()

    "Features"

    "1. Write calculation reports using Pythonsimple and expressive"
    "2. AI-friendly: Python works well with AI assistance"
    "3. All operations are functions, easy to understand and use"
    "4. Automatically substitute and display computed values"
    "5. Focus on logic; UzonCalc handles the dirty work"
    "6. Unit-aware calculations with automatic conversions and checks"
    "7. Call Excel calculations to reuse existing models"
    "8. Output to HTML for viewing and printing to PDF/Word"
    "9. Highly customizable with templates and styles"
    "10. Open-source (MIT)"

    Br()

    "Getting started: basic Python syntax and conventions useful for UzonCalc"

    toc("Table of Contents")

    H2("Installation and Usage")

    "Install via pip:"
    Code("pip install uzoncalc", "bash")

    "A simple example script is as follows:"
    Code(
        """
from uzoncalc import *

@uzon_calc()
def sheet():
    doc_title("uzoncalc example")

    "Hello, UzonCalc!"

    save()


if __name__ == "__main__":
    sheet()

         """,
        "python",
    )

    "Run the script with:"
    Code("python example.py", "bash")

    H2("Python Basics")
    "Here are some Python basics to help you get started with UzonCalc."

    "1. Strings: use single, double, or triple quotes"
    "2. Numbers: integers and floats (e.g. 42, 3.14)"
    "3. Booleans: True and False"
    "4. Lists: use [ ] for lists, e.g. [1,2,3]"
    "5. Assignment: use = to assign values"
    "6. Operators: +, -, *, /, ** for math; comparison operators available"
    "7. Variable names: letters, digits and underscores; cannot start with digit"
    "8. Indentation: use 4 spaces for blocks"
    "9. Comments: start with #"

    Br()

    "Coding suggestions:"
    "- Prefer English names for variables"
    "- Use camelCase for variable names (UzonCalc treats _ as subscript)"
    "- Add comments where helpful"
    "- Keep functions small and focused"

    H2("Automatic Table of Contents")
    "Call `toc()` to automatically generate the document contents here."

    H2("Variables and Naming")
    H3("Naming rules")
    "Variable names can include letters, digits and underscores but cannot start with a digit."
    "Use camelCase in UzonCalc to avoid conflict with subscript notation."

    H3("Aliases")
    "You can define display aliases for variables. Aliases may include non-ASCII characters."
    Code(
        """
age_xm = 30
alias("age_xm", "Person's age")
age_xm
name_xm = "Xiao Ming"
alias("name_xm", "Name_XiaoMing")
name_xm
""",
        "python",
    )

    age_xm = 30
    alias("age_xm", "Person's age")
    age_xm
    name_xm = "Xiao Ming"
    alias("name_xm", "Name_XiaoMing")
    name_xm

    "You can remove an alias by setting it to None."
    alias(name_xm, None)
    name_xm
    alias("age_xm", None)
    age_xm

    H2("Strings")
    "Single, double or triple quotes can be used to output paragraphs."
    Code(
        """
'single quoted'

"double quoted"

\"\"\"
Triple quoted text becomes a paragraph when rendered.
\"\"\"
""",
        "python",
    )

    "single quoted"
    "double quoted"

    """
    Triple quoted text becomes a paragraph when rendered.
    """

    H2("Numbers")
    Code(
        """
# integer
integerNumber = 100
# float
floatNumber = 3.1415
# scientific
scientificNumber = 1.2e3
# complex
complexNumber = 2 + 3j
""",
        "python",
    )

    integerNumber = 100
    floatNumber = 3.1415
    scientificNumber = 1.2e3
    complexNumber = 2 + 3j

    H2("Tensors / Arrays")
    "UzonCalc supports NumPy for tensor/matrix operations."
    arr = np.array([[1, 2, 3], [4, 5, 6]])
    firstRow = arr[0, :]
    secondColumn = arr[:, 1]
    firstCell = arr[0, 0]

    H2("Units")
    H3("Using units")
    "UzonCalc uses pint for unit handling. Use `unit.*` to access units."
    Code(
        """
l_cp = 5 * unit.meter
w_cp = 10 * unit.m
h_cp = 2 * unit.meter
v_cp = l_cp * w_cp * h_cp
""",
        "python",
    )

    l_cp = 5 * unit.meter
    w_cp = 10 * unit.m
    h_cp = 2 * unit.meter
    v_cp = l_cp * w_cp * h_cp

    Code(
        """
force = 100 * unit.newton
A_top = l_cp * w_cp
stress_cp = force / A_top
""",
        "python",
    )

    force = 100 * unit.newton
    A_top = l_cp * w_cp
    stress_cp = force / A_top

    H3("Unit calculations")
    "You can perform arithmetic directly on quantities with units."
    Code(
        """
sqrtArea = sqrt(A_top + 10 * unit.meter**2)
acceleration = force * 1000 / (10 * unit.kilogram)
""",
        "python",
    )

    sqrtArea = sqrt(A_top + 10 * unit.meter**2)
    acceleration = force * 1000 / (10 * unit.kilogram)

    H3("Unit conversion")
    Code(
        """
originalSpeed = 18 * unit.meter / unit.second
speedKmh = originalSpeed.to(unit.kilometer / unit.hour)
"Original speed (m/s):"
originalSpeed
"Converted speed (km/h):"
speedKmh
""",
        "python",
    )

    originalSpeed = 18 * unit.meter / unit.second
    speedKmh = originalSpeed.to(unit.kilometer / unit.hour)
    "Original speed (m/s):"
    originalSpeed
    "Converted speed (km/h):"
    speedKmh

    H2("Advanced String Usage")
    H3("Formatting")
    "You can use f-strings for formatting."
    Code(
        """
name = "Uzon"
f"Hello, {name}! Welcome to UzonCalc."
pi = 3.1415926535
f"Value of pi up to 3 decimal places: {pi:.3f}"
""",
        "python",
    )

    name = "Uzon"
    f"Hello, {name}! Welcome to UzonCalc."
    pi = 3.1415926535
    f"Value of pi up to 3 decimal places: {pi:.3f}"

    H3("Show equations in f-strings")
    "Enable equation display inside f-strings with `enable_fstring_equation()` and disable with `disable_fstring_equation()`."
    enable_fstring_equation()
    f"Hello, {name}! Welcome to UzonCalc."
    f"The value of pi is approximately {pi:.3f}, which is useful in calculations."
    disable_fstring_equation()

    H2("Operators")
    "Use standard arithmetic and comparison operators."
    operatorResult = (5 + 3) * 2 - 4 / 2**2
    comparisonResult = (5 > 3) and (2 == 2) or (4 != 5)

    H2("Plotting")
    "You can create plots using Matplotlib inside UzonCalc."
    Code(
        """
hide()
import matplotlib.pyplot as plt
x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)
plt.plot(x, y)
plt.title("Sine Wave")
plt.xlabel("x (radians)")
plt.ylabel("sin(x)")
plt.legend(["sin(x)"])
plt.grid(True)
show()
Plot(plt)
""",
        "python",
    )

    hide()
    import matplotlib.pyplot as plt

    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)
    plt.plot(x, y)
    plt.title("Sine Wave")
    plt.xlabel("x (radians)")
    plt.ylabel("sin(x)")
    plt.legend(["sin(x)"])
    plt.grid(True)
    show()
    Plot(plt)

    H2("Subscripts")
    H3("Default rule")
    "Use underscore to indicate subscript in rendered names, e.g. H_2 becomes H."
    a_x = 10 * unit.meter / unit.second**2
    speed_car = a_x * 2 * unit.second

    H3("Complex subscripts")
    "Python identifiers cannot contain non-ASCII characters, but you can use aliases for display."
    alias("speed_car", "speed_汽车")
    speed_car
    distance = speed_car * 5 * unit.second
    alias("speed_car", None)
    "Alias removed; variable displays its original name"
    speed_car

    H3("Array subscripts")
    "Square bracket contents are treated as subscripts for arrays."
    arr2d = np.array([[1, 2, 3], [4, 5, 6]])
    firstRow = arr2d[0, :]
    secondColumn = arr2d[:, 1]
    firstCell = arr2d[0, 0]

    H2("Greek letters")
    "Use names like 'alpha', 'beta', 'gamma' to render Greek letters. Capitalized names render uppercase Greek letters."
    rho_water = 1000 * unit.kilogram / unit.meter**3
    gamma_0 = 9.81 * unit.meter / unit.second**2

    H2("Function converters")
    "Functions like sqrt and abs are rendered in math style."
    edge1 = 3 * unit.meter
    edge2 = 4 * unit.meter
    diagonal = sqrt(edge1**2 + edge2**2)

    value = -15 * unit.newton
    absValue = abs(value)

    H2("Tables")
    "Tables can be created with `Table()`; headers can use rowspan/colspan."
    Table(
        [
            [
                th("Component", rowspan=3),
                th("Material", rowspan=3),
                th("Elastic Modulus (MPa)", colspan=2),
                th("Design Strength (MPa)", colspan=2),
                th("Standard Strength (MPa)", colspan=2),
            ],
            [
                "Ec/Es",
                "Compressive",
                "Tensile",
                "Compressive",
                "Tensile",
            ],
        ],
        [
            ["Cap Beam", "C60", 3.6e4, 26.5, 1.96, 38.5, 2.85],
            ["Cap Beam 2", "C60", 3.6e4, 26.5, 1.96, 38.5, 2.85],
        ],
        title="Example Table",
    )

    H2("Calling Excel calculations")
    "You can update cell values in an Excel workbook and retrieve the result table."
    P(
        get_excel_table(
            excel_path="examples/calculation.xlsx",
            values={
                "Sheet2!A3": 6,
                "Sheet2!B3": 10,
                "Sheet2!C3": 2,
            },
            range="Sheet2!A1:D3",
        )
    )

    "By default, Excel results are cached when inputs do not change to speed up rendering."

    H2("Saving the document")
    H3("Save as HTML")
    "Use `save()` to export the document to an HTML file."

    H3("Print to PDF")
    "Open the generated HTML in a browser and use the print feature to save as PDF."

    H3("Export to Word")
    "You can convert HTML to Word using pandoc."

    save("../output/example.en.html")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    sheet()  # type: ignore
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
