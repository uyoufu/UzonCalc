from numpy import sqrt
from pathlib import Path
from uzoncalc import *
from uzoncalc.extension.excel import get_excel_table
from uzoncalc.extension.echarts import use_echarts, EChart, Javascript
import numpy as np


@uzon_calc()
async def sheet():
    # Define UI

    # Set the title: it is displayed on the left side of the header when printing to PDF.
    doc_title("UzonCalc User Guide")

    # Set the page size, such as A3, A4, Letter, and so on.
    page_size("A4")

    # MARK: Level-1 heading, generally used as the cover title.
    Title("UzonCalc User Guide")

    Info("This document is generated with UzonCalc.")

    # Use double-quoted or triple-double-quoted strings as paragraphs.
    """
    UzonCalc is a Python-based tool for hand-written engineering calculation reports.
    You only need to focus on writing content and calculation logic, without worrying about calculation results, layout, and other details.
    UzonCalc automatically substitutes values, calculates results, and generates polished calculation report documents, including tables of contents, mathematical formulas, tables, charts, and more.
    UzonCalc supports unit calculation and Excel table calculation calls, which makes it well suited to engineering calculation reports.
    By calling formulas in Excel, you can reuse existing Excel calculation models and reduce migration cost.
    """

    Br()

    "Key features:"

    Markdown("""
- 🤖 **AI-friendly** — Comes with a SKILL; the calculation process is Python code, which is easy for AI to generate, review, and modify
- 🐍 **Native Python** — Uses native Python syntax, simple to learn and easy to extend
- 📐 **Automatic formula rendering** — Variables are automatically substituted with values, formulas are calculated automatically, and calculation steps are displayed automatically
- 📌 **Automatic layout** — Section numbers and figure numbers are generated automatically, with adaptive layout
- 📏 **Unit calculation** — Calculate with units, with automatic unit conversion and dimensional checks, without worrying about unit consistency
- 📊 **Chart support** — Draw many kinds of charts with ECharts, SVG, and Matplotlib
- 📋 **Excel reuse** — Automatically call Excel for calculation and extract results
- 📄 **Multiple output formats** — Uses standard MathML and supports conversion to PDF, Word, and other documents
    """)

    Br()

    """
    UzonCalc is very simple to use. You do not need to be proficient in Python.
    If you have experience using formulas in Excel, you can get started, and you can treat every operation as a function call.
    """

    Info(
        "Do not assume it is difficult just because it uses Python and involves programming. The important point bears repeating: it is simple, simple, simple."
    )

    # Automatically generate a table of contents here by calling toc().
    toc("Table of Contents")

    # MARK: Installation and usage
    H2("Installation and Usage")

    # MARK: Windows
    H3("Windows Desktop Installation")

    "The desktop app provides extra features such as calculation report management and UI input, and is intended for users. If you are a calculation report author, the CLI method below is recommended. It can be used with VS Code for automatic formatting and syntax checking to improve authoring efficiency."

    "Install the desktop app as follows:"

    "1. Download the software"

    Markdown(
        "Download the `win-x64` version from [Releases · uyoufu/UzonCalc](https://github.com/uyoufu/UzonCalc/releases), extract it, and double-click `UzonCalc.exe` to start."
    )

    "2. Copy the following code into the new editor box"

    Code(
        """
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("example")

    "Hello, UzonCalc!"

    w = 10*unit.m
    l = 5*unit.m
    A = w * l
""",
        "python",
    )

    "3. Click the run button"

    Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
        alt="UzonCalc run result",
    )

    # MARK: CLI
    H3("CLI Installation")

    """
The CLI method is mainly intended for calculation report authors. It supports automatic formatting and syntax checking, which improves authoring efficiency.
When editing calculation reports, AI-assisted authoring is recommended, especially for charts and complex calculation logic.
    """

    "Installation steps:"

    "1. Make sure Python is installed"

    Markdown("2. Install UzonCalc with `pip install uzoncalc` or `uv add uzoncalc`")

    "3. Create a calculation report script"

    Code(
        """
# example.py

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
""",
        "python",
    )

    "4. Run"

    Markdown("""
There are two ways to run a calculation report in CLI mode:
- Use `python --serve example.py`
- Use `uzoncalc example.py`
            """)

    Markdown("""
The difference is that the former requires `view(sheet)` at the end of the code to start the calculation report service,
while the latter does not require the `if __name__ == "__main__"` statement.
        """)

    "When you run the following command:"

    Code(
        """
python --serve example.py
""",
        "python",
    )

    "You will see `Serving document at: http://127.0.0.1:32180/`. Click it or open it in a browser to view the result."

    "A calculation report service started this way does not hot reload. When the report code changes, the service must be restarted manually."

    Markdown(
        "For convenient development, use `uzoncalc example.py` to run the calculation report. The service will reload automatically when the report code changes."
    )

    # MARK: Python basics
    H2("Basic Syntax")

    "UzonCalc is built on Python and introduces no additional language definitions, so writing calculations means writing Python code."

    "If you have not used the Python programming language before, the following basic syntax introduction will help you get started quickly."

    Markdown("""
1. Text: use single quotes `'`, double quotes `"`, or triple quotes `\"""` to wrap text content
2. Numbers: use integers and floating-point numbers directly, such as `42` or `3.14`
3. Boolean values: use `True` and `False`, such as `isValid = True`
4. Lists: use square brackets `[]` to create lists, such as `myList = [1, 2, 3, 4, 5]`
5. The `=` sign: used for assignment, such as `a = 5`, which assigns the number 5 to variable `a`
6. `+, -, *, /, **` operators: used for basic mathematical operations, such as addition, subtraction, multiplication, division, and exponentiation
7. `>, <, >=, <=, ==, !=` comparison operators: used to compare size or equality, such as `a > b` checking whether `a` is greater than `b`, and `a == b` checking whether `a` equals `b`
8. Variable names may contain letters, numbers, and underscores, but cannot start with a number. In UzonCalc, camelCase naming is recommended, such as `myVariableName`, because underscores are used as subscript symbols.
9. Indentation: Python uses indentation to represent code blocks, usually with 4 spaces
10. Comments: content starting with `#` is a comment. Comments are not executed and are only used to explain code
11. Function definitions: use the `def` keyword to define functions, such as `def myFunction(param1, param2):`, which defines a function named `myFunction` with two parameters, `param1` and `param2`. Call it with `myFunction(5, 10)` and pass parameter values 5 and 10.
12. Module imports: use `import` statements to import modules, such as `from numpy import sqrt` to import the `sqrt` function, then call `sqrt(16)` to calculate a square root.
""")

    "For now, understanding this basic syntax is enough to start writing calculation reports with UzonCalc. As you use it, gradually learn more Python syntax and features so you can use UzonCalc better."

    Br()

    "For beginners, the following code style suggestions are recommended:"

    "1. Use English for naming where possible and avoid Pinyin. English expresses meaning better and is easier to read."
    "2. Use camelCase for variable names and avoid underscores, because `_` is used as a subscript symbol."
    "3. Add comments where appropriate to help explain code logic."
    "4. Keep code concise, split complex logic into functions, and put code with different responsibilities into different files."

    # H2 creates a second-level heading.
    # Second-level headings are generally used as section headings.
    H2("Automatic Table of Contents")

    Markdown("""
Call `toc('Table of Contents')` to automatically generate a document table of contents at the call location.
The table of contents in this document is generated by calling `toc('Table of Contents')`.
It is generated automatically from heading levels in the document and page numbers are calculated automatically.
See the actual table of contents above for the result.
""")

    # MARK: Automatic figure and table numbering
    H2("Automatic Figure and Table Numbering")

    "When using UzonCalc, you do not need to number figures and tables manually. The system generates numbers automatically, which greatly reduces maintenance work when figures or tables are added or removed."

    "When you call Img, Table, Echarts, or Plot, the system returns a placeholder string. You can use that placeholder later in the document to reference the figure or table."

    "The following uses an image as an example. The code is:"

    Code(
        """
imgNo = Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
        alt="UzonCalc run result",
    )

f"Now you can use imgNo to reference this image: see {imgNo}."
""",
        "python",
    )

    "Actual result:"

    imgNo = Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
        alt="UzonCalc run result",
    )

    f"Now you can use imgNo to reference this image: see {imgNo}."

    "From the example above, you can also see that the placeholder is ultimately replaced with the image number, and you can click that number to jump to the corresponding image."

    "Figure and table numbers can be used anywhere later in the code."

    Markdown("""
The prefixes for figure and table numbers can be set with `figure_prefix("Figure")` and `table_prefix("Table")`.
This setting takes effect for subsequent figures and tables. The default prefixes are "Figure" and "Table" in this English example.
""")

    figure_prefix("Figure")

    imgNo2 = Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
        alt="UzonCalc run result",
    )

    f"Now reference the image above: see {imgNo2}. You can see that the prefix has changed to Figure."

    # Keep the English prefix for the rest of this example.
    figure_prefix("Figure")

    H2("Headings")

    Markdown("""
The system has two built-in title functions: `Title()` and `H1()`. Use them with calls such as `H1('Heading name')`.
There are 1 to 6 heading levels, corresponding to the H1, H2, H3, H4, H5, and H6 functions.

In general, H1 is used for the document main title, H2 for section headings, H3 for subsection headings, and so on.
""")

    H2("Text Types")

    Markdown(
        "Use single quotes (`'`), double quotes (`\"`), or triple quotes (`\"\"\"`) to mark content that should be output as a paragraph."
    )

    "Example:"

    Code(
        """
'Single-quoted text'

"Double-quoted text"

\"\"\"
Triple-quoted text,
this is line 1,
this is line 2
\"\"\"
""",
        "python",
    )

    "The code above outputs:"

    "Single-quoted text"

    "Double-quoted text"

    """
    Triple-quoted text,
    this is line 1,
    this is line 2
    """

    # Line break
    Br()

    """
    Single-quoted and double-quoted strings are suitable for single-line text, while triple-quoted strings are suitable for multi-line text.
    Triple-quoted strings can span multiple lines, but they are merged into a single paragraph during rendering and line breaks are not preserved.
    This is useful when writing longer paragraphs.
    """

    Info(
        "This differs from everyday Word document input. In UzonCalc, all text must be wrapped in quotes. This is required by Python syntax."
    )

    H2("Numeric Types")

    "Numeric values do not need to be wrapped in quotes. Enter them directly."

    "Example:"

    Code(
        """
# Integer
integerNumber = 100
# Floating-point number
floatNumber = 3.1415
# Scientific notation
scientificNumber = 1.2e3
# Complex number
complexNumber = 2 + 3j
""",
        "python",
    )

    "The output is:"

    integerNumber = 100
    floatNumber = 3.1415
    scientificNumber = 1.2e3
    complexNumber = 2 + 3j

    H2("Operations and Comparisons")

    Markdown(
        "Use standard arithmetic operators `+`, `-`, `*`, `/`, and `**` (`**` means power) to calculate numeric values."
    )
    Markdown("Use `>=`, `<=`, `==`, and `!=` to compare values.")

    "Example:"

    Code(
        """
operatorResult = (5 + 3) * 2 - 4 / 2**2
comparisonResult = (5 > 3) and (2 == 2) or (4 != 5)
        """,
        "python",
    )
    operatorResult = (5 + 3) * 2 - 4 / 2**2
    comparisonResult = (5 > 3) and (2 == 2) or (4 != 5)

    H2("Using Variables")

    "A variable is a container defined in a program to store data. It lets you reuse the same data without entering it repeatedly."

    Markdown("You can also think of variables as parameter symbols in formulas, such as `f_c`, `E`, and `I`.")

    "Consider the following code:"

    Code(
        """
N_s = 100 * unit.KN
A_s = 50 * unit.mm**2
sigma_s = N_s / A_s
         """,
        "python",
    )

    N_s = 100 * unit.kN
    A_s = 50 * unit.mm**2
    sigma_s = N_s / A_s

    H3("Variable Naming Rules")

    "Variable names can contain letters, numbers, and underscores, but cannot start with a number."

    Markdown(
        "In UzonCalc, camelCase naming is recommended, such as `myVariableName`, because `_` underscores are used as subscript symbols."
    )

    H3("Variable Aliases")

    "Because Python variable names are limited, you cannot directly use non-ASCII characters as variable names. Sometimes you may want to use a friendlier name in the document, and aliases are designed for that."

    Markdown('Define an alias with the `alias("variableName", "alias")` function:')

    "Example:"

    Code(
        """
# Concrete strength grade
f_c = 30 * unit.MPa
alias("f_c", "concrete strength grade")

# After the alias is defined, the variable is displayed with the alias until the alias is removed.
f"Now the alias will be output: {f_c}"

# Define a None alias to remove the alias.
alias("f_c", None)

# The alias has been removed and f_c is displayed with its original name again.
f"The alias has been removed. Now the original name is output: {f_c}"
""",
        "python",
    )

    # Concrete strength grade
    f_c = 30 * unit.MPa
    alias("f_c", "concrete strength grade")

    # After the alias is defined, the variable is displayed with the alias until the alias is removed.
    f"Now the alias will be output: {f_c}"

    # Define a None alias to remove the alias.
    alias("f_c", None)

    # The alias has been removed and f_c is displayed with its original name again.
    f"The alias has been removed. Now the original name is output: {f_c}"

    # MARK: Input variables
    H3("Input Variables")

    Markdown("""
This feature is only available in UI mode. Call the `UI()` function to create an input form.
The form renders input boxes in the user interface. When the program detects a UI, it pauses and waits for user input.
After input is complete, the program continues and uses the user's input as the function return value.

The UI function has 3 parameters. The first two are required and the last one is optional:

- `title`: window title
- `fields`: field list. Each field contains a field name, field description, field type, and default value, defined with the `Field()` function.
- `caption`: explanatory text at the bottom of the window

The code is:
    """)

    Code(
        """
inputs = await UI(
    "Structural Parameter Input",
    [
        Field("width", "Width", FieldType.number, value=10),
        Field("length", "Length", FieldType.number, value=30),
        Field("height", "Height", FieldType.number, value=20),
    ],
)

f"The user-entered width is {inputs.width}, length is {inputs.length}, and height is {inputs.height}."
""",
        "python",
    )

    inputs = await UI(
        "Structural Parameter Input",
        [
            Field("width", "Width", FieldType.number, value=10),
            Field("length", "Length", FieldType.number, value=30),
            Field("height", "Height", FieldType.number, value=20),
        ],
    )

    "The UI effect of the code above is shown in the figure below:"

    inputImg = Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260615090832320.png",
        "Input variable demo",
    )

    f"From {inputImg}, you can see that the system converts your input code into a visual UI, where users can enter values and interact with the program."

    "The output of the code above is:"

    f"The user-entered width is {inputs.width}, length is {inputs.length}, and height is {inputs.height}."

    # MARK: Variable subscripts
    H2("Variable Subscripts")

    H3("Default Subscript Rules")

    "If you want a word to become a subscript, put an underscore after it. For example, H_2 is rendered as H₂."

    "Example:"

    Code(
        """
a_x = 10 * unit.meter / unit.second**2
speed_car = a_x * 2 * unit.second
""",
        "python",
    )

    a_x = 10 * unit.meter / unit.second**2
    speed_car = a_x * 2 * unit.second

    H3("Non-ASCII Character Subscripts")

    "Because Python field names are restricted, non-ASCII characters cannot be used directly as variable names. If you want to use non-ASCII characters as subscripts, use aliases."

    "You can use an alias to represent non-ASCII characters as a subscript."

    "Example:"

    Code("""
alias("speed_car", "speed_车")
f"Now the alias subscript will be output: {speed_car}"
distance = speed_car * 5 * unit.second
alias("speed_car", None)
f"The alias has been removed, and speed_car is restored to its original name: {speed_car}"
""")

    alias("speed_car", "speed_车")
    f"Now the alias subscript will be output: {speed_car}"
    distance = speed_car * 5 * unit.second
    alias("speed_car", None)
    f"The alias has been removed, and speed_car is restored to its original name: {speed_car}"

    H3("Array Subscripts")

    "For arrays, the content inside [] is automatically handled as a subscript."

    Code(
        """
arr2d = np.array([[1, 2, 3], [4, 5, 6]])
firstRow = arr2d[0, :]
secondColumn = arr2d[:, 1]
firstCell = arr2d[0, 0]
list1 = [10, 20]
list2 = [30, 40]
combinedList = list1 + list2
secondItem = combinedList[1]
""",
        "python",
    )

    arr2d = np.array([[1, 2, 3], [4, 5, 6]])
    firstRow = arr2d[0, :]
    secondColumn = arr2d[:, 1]
    firstCell = arr2d[0, 0]

    list1 = [10, 20]
    list2 = [30, 40]
    combinedList = list1 + list2
    secondItem = combinedList[1]

    H2("Multidimensional Arrays")

    "The general representation of multidimensional arrays is often called a tensor. It can represent scalars (0-dimensional tensors), vectors (1-dimensional tensors), matrices (2-dimensional tensors), and higher-dimensional arrays."

    "UzonCalc supports tensor calculation with NumPy."

    "Here are some tensor examples:"

    Code(
        """
arr = np.array([[1, 2, 3], [4, 5, 6]])
firstRow = arr[0, :]
secondColumn = arr[:, 1]
firstCell = arr[0, 0]
""",
        "python",
    )

    arr = np.array([[1, 2, 3], [4, 5, 6]])
    firstRow = arr[0, :]
    secondColumn = arr[:, 1]
    firstCell = arr[0, 0]

    "In UzonCalc, variables are displayed in italic. Tensors with more than one dimension are displayed in bold upright style, matching the notation commonly used in papers."

    # MARK: Units
    H2("Units")

    "When calculating formulas, UzonCalc supports calculation with units. Different units with the same dimension do not need to be converted manually and can be calculated directly. For example:"

    totalLength = 10 * unit.m + 20 * unit.cm

    H3("Using Units")

    Markdown("""
UzonCalc uses pint as the unit calculation engine. Use units through `unit.*`, where `*` is the specific unit symbol, such as `unit.m` for meters.
For the specific unit list, see https://github.com/hgrecco/pint/blob/master/pint/default_en.txt .
Here are some unit calculation examples.
    """)

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

    H3("Unit Calculation")

    """
    You can perform mathematical operations directly on quantities with units: addition, subtraction, multiplication, division, powers, square roots, and so on.
    """

    Code(
        """
sqrtArea = sqrt(A_top + 10 * unit.meter**2)
acceleration = force * 1000 / (10 * unit.kilogram)
""",
        "python",
    )

    sqrtArea = sqrt(A_top + 10 * unit.meter**2)
    acceleration = force * 1000 / (10 * unit.kilogram)

    "Different units with the same dimension do not need to be converted manually and can be calculated directly. For example:"

    totalLength = 10 * unit.m + 20 * unit.cm

    H3("Unit Conversion")

    Markdown("Use the `to()` method to convert a quantity with units to another unit.")

    Code(
        """
speedMPerS = 18 * unit.meter / unit.second
speedKmPerH = speedMPerS.to(unit.kilometer / unit.hour)
"Before unit conversion, speed (m/s):"
speedMPerS
"After unit conversion, speed (km/h):"
speedKmPerH
""",
        "python",
    )

    speedMPerS = 18 * unit.meter / unit.second
    speedKmPerH = speedMPerS.to(unit.kilometer / unit.hour)
    "Before unit conversion, speed (m/s):"
    speedMPerS

    "After unit conversion, speed (km/h):"
    speedKmPerH

    H2("Greek Letter Conversion")

    "Use Greek letter English names directly, such as \\alpha (alpha), \\beta (beta), \\gamma (gamma), and \\delta (delta). The system automatically renders them as the corresponding Greek letters."

    "Names starting with lowercase letters are rendered as lowercase Greek letters, and names starting with uppercase letters are rendered as uppercase Greek letters."

    "If you do not want a name to be converted to a Greek letter, add \\ before the name, for example, \\\\alpha."

    Code(
        """
rho_water = 1000 * unit.kilogram / unit.meter**3
gamma_0 = 9.81 * unit.meter / unit.second**2
""",
        "python",
    )

    rho_water = 1000 * unit.kilogram / unit.meter**3
    gamma_0 = 9.81 * unit.meter / unit.second**2

    H2("Function Styles")

    "The following functions are automatically converted to mathematical style:"

    H3("Square Root")
    "Use sqrt(x) to represent the square root of x."

    Code(
        """
edge1 = 3 * unit.meter
edge2 = 4 * unit.meter
diagonal = sqrt(edge1**2 + edge2**2)
""",
        "python",
    )

    edge1 = 3 * unit.meter
    edge2 = 4 * unit.meter
    diagonal = sqrt(edge1**2 + edge2**2)

    H3("Absolute Value")

    "Use abs(x) to represent the absolute value of x."

    Code(
        """
value = -15 * unit.newton
absValue = abs(value)
""",
        "python",
    )

    value = -15 * unit.newton
    absValue = abs(value)

    H2("Advanced String Usage")

    H3("f-string")

    "An f-string, also called a formatted string literal, lets you embed expressions directly in a string and calculate their values at runtime."
    "To create an f-string, add `f` or `F` before the opening quote of the string."

    Code(
        """
 name = "Uzon"
 f"Hello, {name}! Welcome to UzonCalc."
 pi = 3.1415926535
 f"Value of pi up to 3 decimal places: {pi:.3f}"
""",
        "python",
    )

    "Run result:"

    name = "Uzon"
    f"Hello, {name}! Welcome to UzonCalc."
    pi = 3.1415926535
    f"Value of pi up to 3 decimal places: {pi:.3f}"

    H3("Displaying Formulas in f-strings")

    """
By default, expressions in f-strings display only their calculation results. Sometimes you may want to display both the formula and the calculation process in the document.
Use the \\enable_fstring_equation() function to enable this feature. After it is enabled, expressions in f-strings display both formulas and calculation results,
until you call \\disable_fstring_equation() to turn it off.
    """

    Code(
        """
enable_fstring_equation()
width = 10 * unit.meter
length = 20 * unit.meter
f"Area is calculated as {width * length}."
disable_fstring_equation()
""",
        "python",
    )

    enable_fstring_equation()
    width = 10 * unit.meter
    length = 20 * unit.meter
    f"Area is calculated as {width * length}."
    disable_fstring_equation()

    H3("Assigning f-string Calculation Results")
    "Use the `:=` walrus operator to assign the result of an expression in an f-string to a variable for later calculations."

    Code(
        """
f"Area is calculated as {(tempArea := width * length)}."
enable_fstring_equation()
f"Area is calculated as {(tempArea := width * length)}."
disable_fstring_equation()
tempArea
""",
        "python",
    )

    "Run result:"

    f"Area is calculated as {(tempArea := width * length)}."
    enable_fstring_equation()
    f"Area is calculated as {(tempArea := width * length)}."
    disable_fstring_equation()
    tempArea

    H2("String Escaping")

    Markdown(
        "As mentioned above, English names of characters and variable names connected with `_` are rendered as Greek letters and subscripts. To preserve the original characters, add \\ before the character, for example, `\\alpha`."
    )

    # MARK: Charts
    H2("Charts")

    "Use ECharts and Matplotlib to create charts in UzonCalc."

    "You can also use other plotting libraries you prefer, such as Plotly and Seaborn."

    "JavaScript charts are interactive, while Matplotlib charts are rendered as static images and are suitable for print output."

    H3("ECharts Example")

    "Use the echarts library to create rich interactive charts. For more details, see the official documentation and examples: https://echarts.apache.org/examples/zh/index.html#chart-type-line"

    Code(
        """
# Create an ECharts chart.
EChart(options)
""",
        "python",
    )

    "The options parameter in this example refers to: https://echarts.apache.org/examples/zh/editor.html?c=area-stack"

    # Parameter reference: https://echarts.apache.org/examples/zh/editor.html?c=area-stack
    EChart(
        {
            "title": {"text": "Stacked Area Chart"},
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross",
                    "label": {"backgroundColor": "#6a7985"},
                },
            },
            "legend": {
                "data": [
                    "Email",
                    "Union Ads",
                    "Video Ads",
                    "Direct",
                    "Search Engine",
                ]
            },
            "toolbox": {"feature": {"saveAsImage": {}}},
            "xAxis": [
                {
                    "type": "category",
                    "boundaryGap": False,
                    "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                }
            ],
            "yAxis": [{"type": "value"}],
            "series": [
                {
                    "name": "Email",
                    "type": "line",
                    "stack": "Total",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [120, 132, 101, 134, 90, 230, 210],
                },
                {
                    "name": "Union Ads",
                    "type": "line",
                    "stack": "Total",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [220, 182, 191, 234, 290, 330, 310],
                },
                {
                    "name": "Video Ads",
                    "type": "line",
                    "stack": "Total",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [150, 232, 201, 154, 190, 330, 410],
                },
                {
                    "name": "Direct",
                    "type": "line",
                    "stack": "Total",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [320, 332, 301, 334, 390, 330, 320],
                },
                {
                    "name": "Search Engine",
                    "type": "line",
                    "stack": "Total",
                    "label": {"show": True, "position": "top"},
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": [820, 932, 901, 934, 1290, 1330, 1320],
                },
            ],
        }
    )

    H3("ECharts 3D Example")

    "Use ECharts GL to create 3D charts. You can rotate and zoom the chart with the mouse to view different angles and details."

    Code(
        """
hide()
    ROOT_PATH = "https://oss.uzoncloud.com:2234/public/files/images"
    show()

    EChart(
        {
            "backgroundColor": "#000",
            "globe": {
                "baseTexture": ROOT_PATH + "/earth.jpg",
                "heightTexture": ROOT_PATH + "/bathymetry_bw_composite_4k.jpg",
                "displacementScale": 0.1,
                "shading": "lambert",
                "environment": ROOT_PATH + "/starfield.jpg",
                "light": {"ambient": {"intensity": 0.1}, "main": {"intensity": 1.5}},
                "layers": [
                    {
                        "type": "blend",
                        "blendTo": "emission",
                        "texture": ROOT_PATH + "/night.jpg",
                    },
                    {
                        "type": "overlay",
                        "texture": ROOT_PATH + "/clouds.png",
                        "shading": "lambert",
                        "distance": 5,
                    },
                ],
            },
            "series": [],
        },
        use_gl=True,
        caption="3D Earth Example",
    )
""",
        "python",
    )

    # Reference: https://echarts.apache.org/examples/zh/editor.html?c=globe-layers&gl=1
    hide()
    ROOT_PATH = "https://oss.uzoncloud.com:2234/public/files/images"
    show()

    EChart(
        {
            "backgroundColor": "#000",
            "globe": {
                "baseTexture": ROOT_PATH + "/earth.jpg",
                "heightTexture": ROOT_PATH + "/bathymetry_bw_composite_4k.jpg",
                "displacementScale": 0.1,
                "shading": "lambert",
                "environment": ROOT_PATH + "/starfield.jpg",
                "light": {"ambient": {"intensity": 0.1}, "main": {"intensity": 1.5}},
                "layers": [
                    {
                        "type": "blend",
                        "blendTo": "emission",
                        "texture": ROOT_PATH + "/night.jpg",
                    },
                    {
                        "type": "overlay",
                        "texture": ROOT_PATH + "/clouds.png",
                        "shading": "lambert",
                        "distance": 5,
                    },
                ],
            },
            "series": [],
        },
        use_gl=True,
        caption="3D Earth Example",
    )

    H3("Matplotlib Example")

    Code(
        """
hide()

def get_contour3d_plot():
    '''
    Create an example 3D contour plot.
    reference: https://matplotlib.org/stable/gallery/mplot3d/contour3d_3.html
    '''
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import axes3d
    ax = plt.figure().add_subplot(projection="3d")
    X, Y, Z = axes3d.get_test_data(0.05)
    # Plot the 3D surface
    ax.plot_surface(
        X, Y, Z, edgecolor="royalblue", lw=0.5, rstride=8, cstride=8, alpha=0.3
    )
    # Plot projections of the contours for each dimension.  By choosing offsets
    # that match the appropriate axes limits, the projected contours will sit on
    # the 'walls' of the graph.
    ax.contour(X, Y, Z, zdir="z", offset=-100, cmap="coolwarm")
    ax.contour(X, Y, Z, zdir="x", offset=-40, cmap="coolwarm")
    ax.contour(X, Y, Z, zdir="y", offset=40, cmap="coolwarm")
    ax.set(
        xlim=(-40, 40),
        ylim=(-40, 40),
        zlim=(-100, 100),
        xlabel="X",
        ylabel="Y",
        zlabel="Z",
    )
    return plt
show()
Plot(get_contour3d_plot(), caption="3D Contour Example")
""",
        "python",
    )

    hide()

    def get_contour3d_plot():
        """
        Create an example 3D contour plot.
        reference: https://matplotlib.org/stable/gallery/mplot3d/contour3d_3.html
        """
        import matplotlib.pyplot as plt

        from mpl_toolkits.mplot3d import axes3d

        ax = plt.figure().add_subplot(projection="3d")
        X, Y, Z = axes3d.get_test_data(0.05)

        # Plot the 3D surface
        ax.plot_surface(
            X, Y, Z, edgecolor="royalblue", lw=0.5, rstride=8, cstride=8, alpha=0.3
        )

        # Plot projections of the contours for each dimension.  By choosing offsets
        # that match the appropriate axes limits, the projected contours will sit on
        # the 'walls' of the graph.
        ax.contour(X, Y, Z, zdir="z", offset=-100, cmap="coolwarm")
        ax.contour(X, Y, Z, zdir="x", offset=-40, cmap="coolwarm")
        ax.contour(X, Y, Z, zdir="y", offset=40, cmap="coolwarm")

        ax.set(
            xlim=(-40, 40),
            ylim=(-40, 40),
            zlim=(-100, 100),
            xlabel="X",
            ylabel="Y",
            zlabel="Z",
        )
        return plt

    show()
    Plot(get_contour3d_plot(), caption="3D Contour Example")

    H2("Tables")

    "Call the Table() function to create tables."

    "The table header definition may look complex, but it is flexible and powerful, supporting merged cells and other features. See the example below:"

    "This rule is designed based on HTML table definitions. You can refer to HTML table materials for detailed usage."

    "In the example, rowspan means the number of rows a cell spans, and colspan means the number of columns a cell spans."

    Code(
        """
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
""",
        "python",
    )

    table_name = Table(
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

    f"The Table() function returns the table reference. You can use it directly later, for example: the reference to the table above is {table_name}."

    H2("Calling Existing Excel Calculation Tables")

    "You can update cell values in an Excel workbook from a calculation report, execute formulas in Excel, then retrieve and output calculation results in the report."

    "This is useful for reusing existing Excel calculation tables."

    "The P function can output table content as a paragraph."

    Code(
        """
P(
    get_excel_table(
        excel_path="examples/data/calculation.xlsx",
        values={
            "Sheet2!A3": 6,
            "Sheet2!B3": 10,
            "Sheet2!C3": 2,
        },
        range="Sheet2!A1:D3",
    )
)
""",
        "python",
    )

    P(
        get_excel_table(
            excel_path="examples/data/calculation.xlsx",
            values={
                "Sheet2!A3": 6,
                "Sheet2!B3": 10,
                "Sheet2!C3": 2,
            },
            range="Sheet2!A1:D3",
        )
    )

    "By default, if the input values do not change, the Excel table is cached to speed up the next render."

    H2("Saving Documents")

    H3("Saving as an HTML File")

    "Inside a function defined with uzoncalc, use the save() function to save the document as an HTML file."

    "You can get the calculation context object from the return value of run_sync(), then call the object's save() method to save the document."

    Code(
        """
ctx = run_sync(sheet2)
ctx.save("../output/example.en.html")
        """,
        "python",
    )

    H3("Printing as a PDF File")

    "Open the generated HTML file in a browser, then use the browser's built-in print feature to save the document as a PDF file."

    H3("Converting to a Word Document")

    "Use the pandoc command to convert an HTML document to a Word document. See the official pandoc documentation for detailed usage."

    H2("Future Plans")

    "UzonCalc will add the following features in the future:"

    "1. Add UI and calculation report publishing features."
    "2. Add AI support. After you accumulate enough calculation templates, AI can automatically generate initial drafts of new calculation reports."

    H2("Conclusion")

    "AI has arrived. Standing still means falling behind. Let us embrace AI and begin a new calculation journey."


if __name__ == "__main__":
    view(sheet)
