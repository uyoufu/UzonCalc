from numpy import sqrt
from pathlib import Path
import sys

# When installing via pip, this line is not needed; 
# only needed when running this script from the core directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.uzoncalc import *
from core.uzoncalc.extension.excel import get_excel_table
from core.uzoncalc.extension.echarts import use_echarts, EChart, Javascript
import numpy as np


@uzon_calc()
async def sheet1():
    "This is the second calculation sheet example."

    "You can create multiple calculation sheet scripts in the same project, each generating different calculation sheet documents."


@uzon_calc()
async def sheet2():
    # Define UI

    # Set title: Will be displayed on the left side of the header when printing to PDF
    doc_title("UzonCalc User Guide")

    # Set page size, such as A3, A4, Letter, etc.
    page_size("A4")

    # First-level heading, generally used for the cover title
    H1("UzonCalc User Guide")

    Info("This document is generated with UzonCalc.")

    # Use double quotes or triple-double quoted strings as paragraphs
    """
    UzonCalc is a Python-based hand-written engineering calculation sheet tool.
    You only need to focus on writing content and calculation logic, without worrying about calculation results, formatting, and other details.
    UzonCalc will automatically help you substitute values to calculate results, automatically generate beautiful calculation sheet documents, including table of contents, mathematical formulas, tables, charts, etc.
    UzonCalc supports unit calculations, Excel table calculation calls, and other functions, making it very suitable for writing engineering calculation sheets.
    By calling calculation formulas in Excel, you can reuse existing Excel calculation models and reduce migration costs.
    """

    Br()

    "Features"

    "1. Write calculation sheets using Python language, simple and easy to learn syntax"
    "2. AI-friendly, comes with SKILL, can help you write calculation sheets quickly"
    "3. All operations are functions, easy to understand and use"
    "4. Automatically substitute variable values to calculate results, reducing manual calculation errors"
    "5. Only need to focus on content and calculation logic, UzonCalc will automatically handle the dirty work for you"
    "6. Support unit calculations, automatic unit conversion and checking"
    "7. Support calling Excel calculation sheets to achieve calculation model reuse"
    "8. Compatible with MathML, can be converted to PDF, Word, and other formats"
    "9. Highly customizable, supports custom styles and templates"
    "10. Open-source and free, released under MIT license"

    Br()

    """
    Using UzonCalc is very simple. You don't need to be proficient in Python. With Excel formula usage experience, you can get started. You can treat all operations as functions.
    """

    # Automatically generate the table of contents here by calling the toc() function
    toc("Table of Contents")

    H2("Installation and Usage")

    "You can install UzonCalc via pip:"
    Code("pip install uzoncalc", "bash")

    "After installation, copy the following template and save it as example.py:"
    Code(
        """
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("uzoncalc example")

    "Hello, UzonCalc!"

    save()


if __name__ == "__main__":
    run_sync(sheet)
""",
        "python",
    )

    "Then run the script to generate the calculation sheet document:"
    Code("python example.py", "bash")

    H2("Python Basics")

    "If you haven't been exposed to the Python programming language before, here are some basic syntax introductions to help you get started quickly."

    '1. Strings: Use single quotes (\') or double quotes (") or triple quotes (""") to enclose text to represent strings'
    "2. Numbers: You can directly use integers and floating-point numbers, such as 42 or 3.14"
    "3. Booleans: Use True and False to represent boolean values, such as isValid = True"
    "4. Lists: Use square brackets [] to create lists, such as myList = [1, 2, 3, 4, 5]"
    "5. = sign: Used for assignment operations, such as a = 5 assigns the number 5 to variable a"
    "6. +, -, *, /, ** operators: Used for basic mathematical operations, such as + for addition, - for subtraction, * for multiplication, / for division, ** for exponentiation"
    "7. >, <, >=, <=, ==, != comparison operators: Used to compare the magnitude or equality of two values, such as a > b checks if a is greater than b, a == b checks if a equals b"
    "8. Variable names can contain letters, numbers, and underscores, but cannot start with a number. In UzonCalc, it is recommended to use camelCase naming convention, such as myVariableName. Because _ underscore will be used as a subscript symbol"
    "9. Indentation: Python uses indentation to represent the hierarchical relationship of code blocks, usually using 4 spaces for indentation"
    "10. Comments: Content starting with # is a comment. Comments will not be executed and are only used to explain the code"

    """
    11. Function definition: Use the def keyword to define functions, such as def myFunction(param1, param2): 
    Used to define a function named myFunction that accepts two parameters param1 and param2.
    Call the function through myFunction(5, 10) and pass parameter values 5 and 10.   
    """

    """
    12. Module import: Use the import statement to import modules, such as from numpy import sqrt to import the sqrt function, 
    Call the sqrt function in that module through sqrt(16) to calculate the square root.
    """

    "Currently, you only need to understand these basic syntaxes to start using UzonCalc to write calculation sheets. It is recommended to gradually learn more Python syntax and features during use to better utilize UzonCalc."

    Br()

    "For beginners, here are some suggestions regarding code style:"

    "1. Try to use English for naming, avoid Pinyin, English expresses meaning better and is easier to read"
    "2. Use camelCase style for variable naming, avoid using underscore _ because _ is used as a subscript symbol"
    "3. Add comments appropriately to help understand code logic"
    "4. Keep code concise, split complex logic into multiple functions, and put code with different responsibilities into multiple files"

    # H2 function represents a second-level heading
    # Second-level heading, generally used for chapter titles
    H2("Automatic Table of Contents")

    "You can automatically generate the document table of contents at the calling position by calling the toc() function."
    "The table of contents in this document is generated by the toc('Table of Contents') function."
    "The table of contents is automatically generated based on the heading levels in the document, and page numbers are added."
    "See the actual table of contents section above for the generated effect."

    H2("Headings")

    "There are multiple levels of headings, corresponding to H1, H2, H3, H4, H5, H6 functions."
    "Generally, H1 is used for the main title of the document, H2 for chapter titles, H3 for section titles, and so on."

    H2("Variables")

    H3("Variable Naming Rules")

    "Variable names can contain letters, numbers, and underscores, but cannot start with a number"

    "In UzonCalc, it is recommended to use camelCase naming convention, such as myVariableName. Because _ underscore will be used as a subscript symbol."

    H3("Variable Aliases")

    "Due to Python variable name limitations, you cannot directly use non-ASCII characters as variable names, but sometimes you may want to use more friendly names in documents to represent variables. In this case, you can use the alias feature."

    "Aliases are defined through the alias() function:"

    Code(
        """
# Concrete strength grade
f_c = 30 * unit.MPa
alias("f_c", "Concrete Strength Grade")

# After defining an alias, the variable will be displayed in alias form in the document until the alias is removed
f_c

# You can define an alias with a None value to remove the alias
alias("f_c", None)

# Alias has been removed, f_c variable restores its original name
f_c
""",
        "python",
    )

    # Concrete strength grade
    f_c = 30 * unit.MPa
    alias("f_c", "Concrete Strength Grade")

    # After defining an alias, the variable will be displayed in alias form in the document until the alias is removed
    f_c

    # You can define an alias with a None value to remove the alias
    alias("f_c", None)

    # Alias has been removed, f_c variable restores its original name
    f_c

    H3("Input Variables")

    """
    This feature is only available in UI mode. By calling the UI() function, you can create an input form.
    This form will render input boxes in the user interface for users to input. When the program detects a UI, it will pause and wait for user input.
    After input is completed, the program continues to execute and returns the user input values as the function's return value.
    """
    Code(
        """
inputs = await UI(
    "Structure Parameter Input",
    [
        Field("widht", "Width", FieldType.number, value=10),
        Field("length", "Length", FieldType.number, value=30),
        Field("height", "Height", FieldType.number, value=20),
    ],
)

f"The user input width is {inputs['widht']}, length is {inputs['length']}, height is {inputs['height']}."
""",
        "python",
    )

    inputs = await UI(
        "Structure Parameter Input",
        [
            Field("widht", "Width", FieldType.number, value=10),
            Field("length", "Length", FieldType.number, value=30),
            Field("height", "Height", FieldType.number, value=20),
        ],
    )

    "The output of the above code is:"

    f"The user input width is {inputs['widht']}, length is {inputs['length']}, height is {inputs['height']}."

    # sub
    H2("Variable Subscripts")

    H3("Default Subscript Rule")

    "If you want to make a word a subscript, you can use an underscore after it. For example, H_2 will be rendered as H₂."

    Code(
        """
a_x = 10 * unit.meter / unit.second**2
speed_car = a_x * 2 * unit.second
""",
        "python",
    )

    a_x = 10 * unit.meter / unit.second**2
    speed_car = a_x * 2 * unit.second

    H3("Complex Subscripts")

    "Due to Python field name limitations, non-ASCII characters cannot be used as variable names. If you want to use non-ASCII characters as subscripts, you can use the alias feature."

    "You can use aliases"

    alias("speed_car", "speed_汽车")
    speed_car
    distance = speed_car * 5 * unit.second
    alias("speed_car", None)
    "Alias has been removed, speed_car variable restores its original name"
    speed_car

    H3("Array Subscripts")

    "For arrays, the contents within [] are automatically treated as subscripts."

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

    H2("Strings")

    'You can output content as paragraphs using single quotes(\'), double quotes ("), or triple quotes (""").'

    Code(
        """
'Single quoted text'

"Double quoted text"

\"\"\"
Triple quoted text,
This is line 1,
This is line 2
\"\"\"
""",
        "python",
    )

    "The output is as follows:"

    "Single quoted text"

    "Double quoted text"

    """
    Triple quoted text,
    This is line 1,
    This is line 2
    """

    # Line break
    Br()

    """
    Single and double quote methods are suitable for outputting single-line text, while triple quote method is suitable for outputting multi-line text.
    In triple quotes, you can line break, but the actual rendering will merge into a paragraph and will not preserve line breaks.
    This is very useful when writing longer paragraphs.
    """

    H2("Numbers")

    Code(
        """         
# Integer
integerNumber = 100
# Float
floatNumber = 3.1415
# Scientific notation
scientificNumber = 1.2e3
# Complex number
complexNumber = 2 + 3j         
""",
        "python",
    )

    "The output is as follows:"

    integerNumber = 100
    floatNumber = 3.1415
    scientificNumber = 1.2e3
    complexNumber = 2 + 3j

    H2("Tensors")

    "Tensors are a general representation of multi-dimensional arrays. They can represent scalars (0-dimensional tensors), vectors (1-dimensional tensors), matrices (2-dimensional tensors), and higher-dimensional arrays."

    "UzonCalc supports using the NumPy library for tensor calculations."

    "Here are some examples of tensors:"

    arr = np.array([[1, 2, 3], [4, 5, 6]])
    firstRow = arr[0, :]
    secondColumn = arr[:, 1]
    firstCell = arr[0, 0]

    "In UzonCalc, variables are displayed in italics, and tensors are displayed in bold upright font to distinguish them."

    H2("Units")

    H3("Using Units")

    """
    UzonCalc uses pint as the unit calculation engine. You can use units through unit.*.
    For the specific unit list, please refer to the documentation: https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
    Here are some examples of unit calculations.
    """

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

    H3("Unit Calculations")

    """
    You can directly perform mathematical operations on quantities with units: addition, subtraction, multiplication, division, exponentiation, square root, etc.
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

    H3("Unit Conversion")

    "You can use the to() method to convert quantities with units to other units."

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

    H2("Advanced String Usage")

    H3("f-string")

    "f-string, also known as formatted string literals. It allows you to directly embed expressions in strings and evaluate these expressions at runtime."
    "To create an f-string, you just need to add an f or F before the opening quote of the string"

    Code(
        """
 name = "Uzon"
 f"Hello, {name}! Welcome to UzonCalc."
 pi = 3.1415926535
 f"Value of pi up to 3 decimal places: {pi:.3f}"
""",
        "python",
    )

    "The running effect is as follows:"

    name = "Uzon"
    f"Hello, {name}! Welcome to UzonCalc."
    pi = 3.1415926535
    f"Value of pi up to 3 decimal places: {pi:.3f}"

    H3("Show Equations in f-strings")

    """
By default, expressions in f-strings will only display the calculation result, but sometimes you may want to display both the formula and calculation process in the document.
In this case, you can use the enable_fstring_equation() function to enable this feature. After enabling, expressions in f-strings will display both the formula and calculation results.
Until you call the disable_fstring_equation() function to disable this feature.
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

    H3("Assign f-string Calculation Results")
    "You can use the := walrus operator to assign the calculation result of an expression in an f-string to a variable for use in subsequent calculations."

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

    "The running effect is as follows:"

    f"Area is calculated as {(tempArea := width * length)}."
    enable_fstring_equation()
    f"Area is calculated as {(tempArea := width * length)}."
    disable_fstring_equation()
    tempArea

    H2("Operators")

    "You can use standard arithmetic operators +, -, *, /, and ** (exponentiation) for calculations."
    "You can also use >=, <=, ==, != for comparisons."

    Code(
        """
operatorResult = (5 + 3) * 2 - 4 / 2**2
comparisonResult = (5 > 3) and (2 == 2) or (4 != 5)
        """,
        "python",
    )
    operatorResult = (5 + 3) * 2 - 4 / 2**2
    comparisonResult = (5 > 3) and (2 == 2) or (4 != 5)

    # use matplotlib to plot a sine wave
    H2("Charts")

    "You can use echarts, Matplotlib to create charts in UzonCalc."

    "You can also use other plotting libraries according to your preference, such as Plotly, Seaborn, etc."

    "Using JS charts has interactive effects, while using matplotlib charts will render the charts as static images, suitable for printing output."

    H3("ECharts Example")

    "You can use the echarts library to create rich interactive charts. For more content, please refer to the official documentation and examples: https://echarts.apache.org/examples/zh/index.html#chart-type-line"

    Code(
        """
# Create echarts chart
EChart(options)
""",
        "python",
    )

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

    "You can use ECharts GL to create 3D charts. You can use the mouse to rotate and zoom the chart to view different angles and details."

    Code(
        """
EChart(
        {
            "tooltip": {},
            "backgroundColor": "#fff",
            "visualMap": {
                "show": False,
                "dimension": 2,
                "min": -1,
                "max": 1,
                "inRange": {
                    "color": [
                        "#313695",
                        "#4575b4",
                        "#74add1",
                        "#abd9e9",
                        "#e0f3f8",
                        "#ffffbf",
                        "#fee090",
                        "#fdae61",
                        "#f46d43",
                        "#d73027",
                        "#a50026",
                    ]
                },
            },
            "xAxis3D": {"type": "value"},
            "yAxis3D": {"type": "value"},
            "zAxis3D": {"type": "value"},
            "grid3D": {"viewControl": {}},
            "series": [
                {
                    "type": "surface",
                    "wireframe": {},
                    "equation": {
                        "x": {"step": 0.05},
                        "y": {"step": 0.05},
                        "z": Javascript('''
function (x, y) {
  if (Math.abs(x) < 0.1 && Math.abs(y) < 0.1) {
    return '-';
  }
  return Math.sin(x * Math.PI) * Math.sin(y * Math.PI);
}
'''),
                    },
                }
            ],
        },
        use_gl=True,
    )
""",
        "python",
    )

    # Parameter reference: https://echarts.apache.org/examples/zh/editor.html?c=simple-surface&gl=1
    EChart(
        {
            "tooltip": {},
            "backgroundColor": "#fff",
            "visualMap": {
                "show": False,
                "dimension": 2,
                "min": -1,
                "max": 1,
                "inRange": {
                    "color": [
                        "#313695",
                        "#4575b4",
                        "#74add1",
                        "#abd9e9",
                        "#e0f3f8",
                        "#ffffbf",
                        "#fee090",
                        "#fdae61",
                        "#f46d43",
                        "#d73027",
                        "#a50026",
                    ]
                },
            },
            "xAxis3D": {"type": "value"},
            "yAxis3D": {"type": "value"},
            "zAxis3D": {"type": "value"},
            "grid3D": {"viewControl": {}},
            "series": [
                {
                    "type": "surface",
                    "wireframe": {},
                    "equation": {
                        "x": {"step": 0.05},
                        "y": {"step": 0.05},
                        "z": Javascript(
                            """
function (x, y) {
  if (Math.abs(x) < 0.1 && Math.abs(y) < 0.1) {
    return '-';
  }
  return Math.sin(x * Math.PI) * Math.sin(y * Math.PI);
}
"""
                        ),
                    },
                }
            ],
        },
        use_gl=True,
    )

    H3("Matplotlib Example")

    Code(
        """
hide()

def get_contour3d_plot():
    '''
    Example function to create a 3D contour plot
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
Plot(get_contour3d_plot())
""",
        "python",
    )

    hide()

    def get_contour3d_plot():
        """
        Example function to create a 3D contour plot
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
    Plot(get_contour3d_plot())

    H2("Greek Letter Conversion")

    "You can directly use English names of Greek letters such as 'alpha' (α), 'beta' (β), 'gamma' (γ), 'delta' (δ), and the system will automatically render them as corresponding Greek letters."

    "Names starting with lowercase letters will be rendered as lowercase Greek letters, and names starting with uppercase letters will be rendered as uppercase Greek letters."

    "If you don't want letters to be escaped as Greek letters, you can surround the name with quotes, such as 'alpha'"

    Code(
        """
rho_water = 1000 * unit.kilogram / unit.meter**3
gamma_0 = 9.81 * unit.meter / unit.second**2
""",
        "python",
    )

    rho_water = 1000 * unit.kilogram / unit.meter**3
    gamma_0 = 9.81 * unit.meter / unit.second**2

    H2("Function Conversion")

    "The following functions are automatically converted to mathematical style:"

    H3("Square Root")
    "You can use sqrt(x) to represent the square root of x."

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

    "You can use abs(x) to represent the absolute value of x."

    Code(
        """
value = -15 * unit.newton
absValue = abs(value)
""",
        "python",
    )

    value = -15 * unit.newton
    absValue = abs(value)

    H2("Tables")

    "You can call the Table() function to create tables."

    "The definition of table headers may look a bit complex, but it's actually very flexible and powerful, supporting features like merged cells. You can refer to the following example:"

    "This rule is designed based on the definition of HTML tables. You can refer to HTML table related materials for detailed usage."

    "In the example, rowspan represents the number of rows a cell spans, and colspan represents the number of columns a cell spans."

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

    H2("Calling Existing Excel Calculation Sheets")

    "You can update cell values in an Excel workbook in the calculation sheet, execute calculation formulas in Excel, and then obtain calculation results and output them to the calculation sheet."

    "This is very useful for reusing existing Excel calculation sheets."

    "The P function can output table content as a paragraph."

    Code(
        """
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
""",
        "python",
    )

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

    "By default, if input values have not changed, Excel tables will be cached to speed up the next rendering."

    H2("Saving the Document")

    H3("Save as HTML File")

    H4("Inside Function")

    "In a function defined by uzoncalc, you can use the save() function to save the document as an HTML file."

    Code(
        """
save("../output/example.en.html")
        """,
        "python",
    )

    H4("Outside Function")

    "Outside the function, you can obtain the calculation context object through the return value of the run_sync() function, and then call the save() method of that object to save the document."
    Code(
        """
ctx = run_sync(sheet2)
ctx.save("../output/example.en.html")
        """,
        "python",
    )

    H3("Print to PDF File")

    "Open the generated HTML file in a browser, then use the browser's built-in print function to save the document as a PDF file."

    H3("Convert to Word Document")

    "You can convert an HTML document to a Word document through the pandoc command."

    H2("Future Plans")

    "The following features will be added to UzonCalc in the future:"

    "1. Add UI and calculation sheet publishing features"
    "2. Add AI support. After you have accumulated certain calculation templates, you can use AI to automatically generate new calculation sheet drafts"


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    ctx = run_sync(sheet2)
    ctx.save("../output/example.en.html")
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
