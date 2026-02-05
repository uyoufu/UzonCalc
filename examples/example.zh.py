from numpy import sqrt
from pathlib import Path
import sys

# 使用 pip 包时，不需要该行；仅在从 core 目录运行该脚本时需要
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc.utils_extra.excel import get_excel_table
from uzoncalc import *
import numpy as np


@uzon_calc()
async def sheet():
    # 定义 UI

    # 设置 title: 打印 pdf 时，将在页眉左侧显示
    doc_title("UzonCalc 使用说明")

    inputs = await UI(
        "自定义窗体",
        [
            Field("name", "姓名", FieldType.text, value="小明"),
            Field("age", "年龄", FieldType.number, value=18),
        ],
    )
    name = inputs["name"]

    # 设置页面大小, 如 A3, A4, Letter 等
    page_size("A4")

    # 一级标题，一般用于封面的标题
    H1("UzonCalc 使用说明")

    Info("本文档使用 UzonCalc 生成。")

    # 作用双引号或者双三引号字符串作为段落
    """
    UzonCalc 是一个基于 Python 的手写工程计算书工具。
    你只需专注于内容和计算逻辑的编写，而不必关心计算结果、排版等细节,
    UzonCalc 会自动帮你代入值计算结果，自动生成漂亮的计算书文档，包括目录、数学公式、表格、图表等。
    UzonCalc 支持单位计算、Excel 表格计算调用等功能，非常适合工程计算书的编写需求，
    通过调用 Excel 中的计算公式，可以复用已有的 Excel 计算模型，减少迁移成本。
    """

    Br()

    "功能特色"

    "1. 使用 python 语言编写计算书，语法简单易学"
    "2. AI 友好，AI 对 python 的支持非常好，可以使用 AI 辅助编写计算书"
    "3. 所有的操作均为函数，易于理解和使用"
    "4. 自动代入变量值计算结果，减少手动计算错误"
    "5. 只需要关心内容和计算逻辑，其它脏活 UzonCalc 会自动帮你处理"
    "6. 支持单位计算，自动进行单位换算和检查"
    "7. 支持调用 Excel 计算表格，复用现有计算模型"
    "8. 输出为 HTML 格式，方便查看和打印为 PDF、 Word 等格式"
    "9. 高度可定制化，支持自定义样式和模板"
    "10. 开源免费，基于 MIT 许可证发布"

    Br()

    """
    使用 UzonCalc 非常简单，不需要你精通 Python, 具有 Excel 的公式使用经验即可上手使用, 你可以把所有的操作都当成函数使用就可以了。
    """

    # 通过调用 toc() 函数自动在此处生成目录
    toc("目录")

    H2("安装使用")

    "你可以通过 pip 安装 UzonCalc："
    Code("pip install uzoncalc", "bash")

    "安装完成后，复制以下模板使用："
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

    "然后运行该脚本即可生成计算书文档："
    Code("python example.py", "bash")

    H2("Python 基础语法")

    "若你之前没有接触过 Python 编程语言，下面是一些基础语法介绍，帮助你快速上手。"

    '1. 字符串: 使用单引号 \' 或双引号 " 或 三引号 """ 包围文本表示字符串。'
    "2. 数字: 可以直接使用整数和浮点数，例如 42 或 3.14。"
    "3. 布尔值: 使用 True 和 False 表示布尔值，例如 isValid = True。"
    "4. 列表: 使用方括号 [] 创建列表，例如 myList = [1, 2, 3, 4, 5]。"
    "5. = 号: 用于赋值操作，例如 a = 5 将数字 5 赋值给变量 a。"
    "6. +, -, *, /, ** 运算符: 用于基本的数学运算，例如 + 用于加法，- 用于减法，* 用于乘法，/ 用于除法，** 用于幂运算。"
    "7. >, <, >=, <=, ==, != 比较运算符: 用于比较两个值的大小或相等性，例如 a > b 判断 a 是否大于 b，a == b 判断 a 是否等于 b。"
    "8. 变量名可以包含字母、数字和下划线，但不能以数字开头。在 UzonCalc 中, 推荐使用 camelCase 命名法，例如 myVariableName。因为 _ 下划线会被用作下标符号。"
    "9. 缩进: Python 使用缩进来表示代码块的层级关系，通常使用 4 个空格进行缩进。"
    "10. 注释: 使用 # 符号添加注释，例如 # 这是一个注释。注释不会被执行，仅用于解释代码。"

    """
    11. 函数定义: 使用 def 关键字定义函数，例如 def myFunction(param1, param2): 
    用于定义一个名为 myFunction 的函数，接受两个参数 param1 和 param2。
    通过 myFunction(5, 10) 调用该函数，并传入参数值 5 和 10。   
    """

    """
    12. 模块导入: 使用 import 语句导入模块，例如 import math 导入数学模块，
    通过 math.sqrt(16) 调用该模块中的 sqrt 函数计算平方根。
    """

    "目前，你只需要了解这些基础语法，就可以开始使用 UzonCalc 进行计算书编写了。建议在使用过程中逐步学习更多 Python 语法和功能，以便更好地使用 UzonCalc。"

    Br()

    "对于初学者，关于代码规范有以下建议："

    "1. 尽量使用英文进行命名，避免使用拼音，英语更能表达含义，方便阅读"
    "2. 变量命名使用 camelCase 风格，避免使用下划线 _，因为 _ 会被用作下标符号"
    "3. 适当添加注释，帮助理解代码逻辑"
    "4. 保持代码简洁，将复杂逻辑拆分为多个函数，将不同职责的代码放到多个文件中"

    # H2 函数表示二级标题
    # 二级标题，一般用于章节标题
    H2("自动目录")

    "你可以通过调用 toc() 函数自动在调用的位置生成文档目录。"
    "本文的目录即为通过 toc('目录') 函数生成。"
    "目录会根据文档中的标题层级自动生成，并添加页码。"

    H2("标题")

    "标题有多级，分别对应 H1, H2, H3, H4, H5, H6 函数。"
    "一般来说，H1 用于文档的主标题，H2 用于章节标题，H3 用于小节标题，依此类推。"

    H2("变量")

    H3("变量命名规则")

    "变量名可以包含字母、数字和下划线，但不能以数字开头"

    "在 UzonCalc 中, 推荐使用 camelCase 命名法，例如 myVariableName。因为 _ 下划线会被用作下标符号。"

    H3("变量别名")

    "你可以为变量定义别名，别名可以包含非 ASCII 字符。例如:"

    Code(
        """
age_xm = 30
alias("age_xm", "人的年龄")
age_xm
name_xm = "小明"
alias("name_xm", "姓名_小明")
name_xm
"别名定义后，变量在文档中将以别名形式显示。"
"可以定义一个 None 值的别名来移除别名，例如:"
alias(name_xm, None)
"别名已移除，name_xm 变量恢复原名"
name_xm
alias("age_xm", None)
"别名已移除，age_xm 变量恢复原名"
age_xm
""",
        "python",
    )

    age_xm = 30
    alias("age_xm", "小明的年龄")
    age_xm
    name_xm = "小明"
    alias("name_xm", "姓名_小明")
    name_xm

    "别名定义后，变量在文档中将以别名形式显示。"

    "可以定义一个 None 值的别名来移除别名。"

    alias(name_xm, None)
    "别名已移除，name_xm 变量恢复原名"
    name_xm

    alias("age_xm", None)
    "别名已移除，age_xm 变量恢复原名"
    age_xm

    H2("字符串")

    '可以通过单引号(\')、双引号(")、三引号(""")将要输出的内容作为段落输出。'

    Code(
        """
'单引号文本'

"双引号文本"

\"\"\"
三引号文本,
这是第 1 行,
这是第 2 行
\"\"\"
""",
        "python",
    )

    "单引号文本"

    "双引号文本"

    """
    三引号文本,
    这是第 1 行,
    这是第 2 行
    """

    """
    单引号与双引号方式适合输出单行文本，三引号方式适合输出多行文本。
    在三引号中可以换行，但是实际渲染时会合并为一个段落，并不会保留换行。
    这在写较长的段落时非常有用。
    """

    H2("数字")

    Code(
        """         
# 整数
integerNumber = 100
# 浮点数
floatNumber = 3.1415
# 科学计数法
scientificNumber = 1.2e3
# 复数
complexNumber = 2 + 3j         
""",
        "python",
    )

    integerNumber = 100
    floatNumber = 3.1415
    scientificNumber = 1.2e3
    complexNumber = 2 + 3j

    H2("张量")

    "张量是多维数组的通用表示，它可以表示标量（0维张量）、向量（1维张量）、矩阵（2维张量）以及更高维度的数组。"

    "UzonCalc 支持使用 NumPy 库进行张量计算。"

    "下面是一些张量的示例："

    arr = np.array([[1, 2, 3], [4, 5, 6]])
    firstRow = arr[0, :]
    secondColumn = arr[:, 1]
    firstCell = arr[0, 0]

    H2("单位")

    H3("使用单位")

    """
    UzonCalc 使用 pint 作为单位计算引擎。你可以通过 unit.* 的方式使用单位。
    具体的单位列表请参考文档：https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
    下面是一些单位计算的示例。
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

    H3("单位计算")

    """
    你可以直接对带单位的量进行数学运算: 加、减、乘、除、幂、开方等。
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

    H3("单位转换")

    "你可以使用 to() 方法将带单位的量转换为其他单位。"

    Code(
        """
originalSpeed = 18 * unit.meter / unit.second
speedKmh = originalSpeed.to(unit.kilometer / unit.hour)
"原始速度 (m/s):"
originalSpeed
"转换后的速度 (km/h):"
speedKmh
""",
        "python",
    )

    originalSpeed = 18 * unit.meter / unit.second
    speedKmh = originalSpeed.to(unit.kilometer / unit.hour)
    "原始速度 (m/s):"
    originalSpeed
    "转换后的速度 (km/h):"
    speedKmh

    H2("字符串高级应用")

    H3("字符串格式化")

    "可以使用 f 字符串进行字符串格式化。"

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

    H3("f 字符串中显示公式")

    "可以在 f 字符串中显示公式和计算过程。"
    "使用 enable_fstring_equation() 启用公式显示，使用 disable_fstring_equation() 关闭后续公式显示。"

    Code(
        """
enable_fstring_equation()
f"Hello, {name}! Welcome to UzonCalc."
f"The value of pi is approximately {pi:.3f}, which is useful in calculations."
disable_fstring_equation()
""",
        "python",
    )

    enable_fstring_equation()
    f"Hello, {name}! Welcome to UzonCalc."
    f"The value of pi is approximately {pi:.3f}, which is useful in calculations."
    disable_fstring_equation()

    H2("操作符")

    "你可以使用标准的算术运算符 +、-、*、/ 和 ** 进行计算。"
    "还可以使用 >=、<=、==、!= 进行比较。"

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
    H2("绘图")

    "你可以使用 Matplotlib 在 UzonCalc 中创建图表。"

    "当然，由于你是在使用 python, 你也可以使用其他绘图库，如 Plotly、Seaborn 等，还可以直接使用 js 库进行绘图。"

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

    # sub
    H2("变量下标")

    H3("默认下标规则")

    "如果你想让一个词成为下标，可以在它后面使用下划线。例如，H_2 将被渲染为 H₂。"

    Code(
        """
a_x = 10 * unit.meter / unit.second**2
speed_car = a_x * 2 * unit.second
""",
        "python",
    )

    a_x = 10 * unit.meter / unit.second**2
    speed_car = a_x * 2 * unit.second

    H3("复杂下标")

    "由于 python 字段名限制，无法使用非 ASCII 字符作为变量名，若想使用非 ASCII 字符作为下标，可以使用别名功能。"

    "你可以使用别名"

    alias("speed_car", "speed_汽车")
    speed_car
    distance = speed_car * 5 * unit.second
    alias("speed_car", None)
    "别名已移除，speed_car 变量恢复原名"
    speed_car

    H3("数组下标")

    "对于数组，会自动将 [] 内的内容作为下标处理。"

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

    H2("希腊字母")

    "你可以直接使用希腊字母的英文名称如 'alpha' (α), 'beta' (β), 'gamma' (γ), 'delta' (δ), 系统会自动将其渲染为对应的希腊字母。"

    "以小写字母开头的名称会被渲染为小写希腊字母，以大写字母开头的名称会被渲染为大写希腊字母。"

    Code(
        """
rho_water = 1000 * unit.kilogram / unit.meter**3
gamma_0 = 9.81 * unit.meter / unit.second**2
""",
        "python",
    )

    rho_water = 1000 * unit.kilogram / unit.meter**3
    gamma_0 = 9.81 * unit.meter / unit.second**2

    H2("函数转换器")

    "以下函数会被自动转换为数学样式："

    H3("平方根")
    "你可以使用 sqrt(x) 来表示 x 的平方根。"

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

    H3("绝对值")

    "你可以使用 abs(x) 来表示 x 的绝对值。"

    Code(
        """
value = -15 * unit.newton
absValue = abs(value)
""",
        "python",
    )

    value = -15 * unit.newton
    absValue = abs(value)

    H2("表格")

    "你可以调用 Table() 函数来创建表格。"

    "表格中表头的定义可能看起来有些复杂，但实际上非常灵活强大，支持合并单元格等功能。可以参考下面的示例："

    "该规则是基于 HTML 表格的定义方式设计的，可以参考 HTML 表格相关资料了解详细用法。"

    "示例中，rowspan 表示单元格跨越的行数，colspan 表示单元格跨越的列数。"

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
    title="示例表格",
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
        title="示例表格",
    )

    H2("调用 Excel 计算")

    "你可以更新 Excel 中单元格的值并获取计算结果表格"

    "这对于重用现有的 Excel 计算表格非常有用。"

    "P 函数可以将表格内容作为段落输出。"

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

    "默认情况下，若输入值没有变化，Excel 表格会被缓存，以加快下次渲染速度。"

    H2("保存文档")

    H3("保存为 HTML 文件")

    "你可以使用 save() 函数将文档保存为 HTML 文件。"

    Code(
        """
save("../output/example.zh.html")
        """,
        "python",
    )

    H3("打印为 PDF 文件")

    "在浏览器中打开生成的 HTML 文件后，可以使用浏览器的打印功能将文档保存为 PDF 文件。"

    H3("导出为 Word 文档")

    "你可以通过 pandoc 命令将 HTML 文档导出为 Word 文档。"

    H2("未来计划")

    "未来将向 UzonCalc 添加以下功能："

    "1. 添加 UI 与计算书发布功能"
    "2. 添加 AI 支持，当你积累了一定的计算模板后，可以通过 AI 自动生成新的计算书初稿"

    save("../output/example.zh.html")


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    run_sync(sheet)
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
