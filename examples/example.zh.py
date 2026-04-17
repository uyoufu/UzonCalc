from numpy import sqrt
from pathlib import Path
import sys

# 使用 pip 包时, 不需要该行；仅在从 core 目录运行该脚本时需要
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from uzoncalc import *
from uzoncalc.extension.excel import get_excel_table
from uzoncalc.extension.echarts import use_echarts, EChart, Javascript
import numpy as np


@uzon_calc()
async def sheet2():
    # 定义 UI

    # 设置 title: 打印 pdf 时, 将在页眉左侧显示
    doc_title("UzonCalc 使用说明")

    # 设置页面大小, 如 A3, A4, Letter 等
    page_size("A4")

    # 一级标题, 一般用于封面的标题
    H1("UzonCalc 使用说明")

    Info("本文档使用 UzonCalc 生成。")

    # 作用双引号或者双三引号字符串作为段落
    """
    UzonCalc 是一个基于 Python 的手写工程计算书工具。
    你只需专注于内容和计算逻辑的编写, 而不必关心计算结果、排版等细节,
    UzonCalc 会自动帮你代入值计算结果, 自动生成漂亮的计算书文档, 包括目录、数学公式、表格、图表等。
    UzonCalc 支持单位计算、Excel 表格计算调用等功能, 非常适合工程计算书的编写需求, 
    通过调用 Excel 中的计算公式, 可以复用已有的 Excel 计算模型, 减少迁移成本。
    """

    Br()

    "功能特色"

    "1. 使用 python 语言编写计算书, 语法简单易学"
    "2. AI 友好, 自带 SKILL, 可以帮助你快速编写计算书"
    "3. 所有的操作均为函数, 易于理解和使用"
    "4. 自动代入变量值计算结果, 减少手动计算错误"
    "5. 只需要专注于内容和计算逻辑, 其它脏活 UzonCalc 会自动帮你搞定"
    "6. 支持单位计算, 自动进行单位换算和检查"
    "7. 支持调用 Excel 计算表格, 实现计算模型复用"
    "8. 兼容 MathML, 可转换为 PDF、Word 等多种格式"
    "9. 高度可定制化, 支持自定义样式和模板"
    "10. 开源免费, 基于 MIT 许可证发布"

    Br()

    """
    使用 UzonCalc 非常简单, 不需要你精通 Python, 具有 Excel 的公式使用经验即可上手使用, 你可以把所有的操作都当成函数使用。
    """

    # 通过调用 toc() 函数自动在此处生成目录
    toc("目录")

    H2("安装使用")

    "你可以通过 pip 安装 UzonCalc："
    Code("pip install uzoncalc", "bash")

    "安装完成后, 复制以下模板保存为 example.py："
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

    "然后运行该脚本即可生成计算书文档："
    Code("python example.py", "bash")

    H2("Python 基础语法")

    "若你之前没有接触过 Python 编程语言, 下面是一些基础语法介绍, 帮助你快速上手。"

    '1. 字符串: 使用单引号 \' 或双引号 " 或 三引号 """ 包围文本表示字符串'
    "2. 数字: 可以直接使用整数和浮点数, 例如 42 或 3.14"
    "3. 布尔值: 使用 True 和 False 表示布尔值, 例如 isValid = True"
    "4. 列表: 使用方括号 [] 创建列表, 例如 myList = [1, 2, 3, 4, 5]"
    "5. = 号: 用于赋值操作, 例如 a = 5 将数字 5 赋值给变量 a"
    "6. +, -, *, /, ** 运算符: 用于基本的数学运算, 例如 + 用于加法, - 用于减法, * 用于乘法, / 用于除法, ** 用于幂运算"
    "7. >, <, >=, <=, ==, != 比较运算符: 用于比较两个值的大小或相等性, 例如 a > b 判断 a 是否大于 b, a == b 判断 a 是否等于 b"
    "8. 变量名可以包含字母、数字和下划线, 但不能以数字开头。在 UzonCalc 中, 推荐使用 camelCase 命名法, 例如 myVariableName。因为 _ 下划线会被用作下标符号"
    "9. 缩进: Python 使用缩进来表示代码块的层级关系, 通常使用 4 个空格进行缩进"
    "10. 注释: 以 # 开头的内容为注释。注释不会被执行, 仅用于解释代码"

    """
    11. 函数定义: 使用 def 关键字定义函数, 例如 def myFunction(param1, param2): 
    用于定义一个名为 myFunction 的函数, 接受两个参数 param1 和 param2。
    通过 myFunction(5, 10) 调用该函数, 并传入参数值 5 和 10。   
    """

    """
    12. 模块导入: 使用 import 语句导入模块, 例如 from numpy import sqrt 导入 sqrt 函数, 
    通过 sqrt(16) 调用该模块中的 sqrt 函数计算平方根。
    """

    "目前, 你只需要了解这些基础语法, 就可以开始使用 UzonCalc 进行计算书编写了。建议在使用过程中逐步学习更多 Python 语法和功能, 以便更好地使用 UzonCalc。"

    Br()

    "对于初学者, 关于代码规范有以下建议："

    "1. 尽量使用英文进行命名, 避免使用拼音, 英语更能表达含义, 方便阅读"
    "2. 变量命名使用 camelCase 风格, 避免使用下划线 _, 因为 _ 被用作下标符号"
    "3. 适当添加注释, 帮助理解代码逻辑"
    "4. 保持代码简洁, 将复杂逻辑拆分为多个函数, 将不同职责的代码放到多个文件中"

    # H2 函数表示二级标题
    # 二级标题, 一般用于章节标题
    H2("自动目录")

    "你可以通过调用 toc() 函数自动在调用的位置生成文档目录。"
    "本文的目录即为通过 toc('目录') 函数生成。"
    "目录会根据文档中的标题层级自动生成, 并添加页码。"
    "生成效果见上面实际目录部分。"

    H2("标题")

    "标题有多级, 分别对应 H1, H2, H3, H4, H5, H6 函数。"
    "一般来说, H1 用于文档的主标题, H2 用于章节标题, H3 用于小节标题, 依此类推。"

    H2("变量")

    H3("变量命名规则")

    "变量名可以包含字母、数字和下划线, 但不能以数字开头"

    "在 UzonCalc 中, 推荐使用 camelCase 命名法, 例如 myVariableName。因为 _ 下划线会被用作下标符号。"

    H3("变量别名")

    "由于 python 变量名的限制, 你无法直接使用非 ASCII 字符作为变量名, 但有时候你可能希望在文档中使用更友好的名称来表示变量, 这时可以使用别名功能。"

    "别名通过 alias() 函数定义:"

    Code(
        """
# 混凝土强度等级
f_c = 30 * unit.MPa
alias("f_c", "混凝土强度等级")

# 别名定义后, 变量在文档中将以别名形式显示, 直到别名被移除
f_c

# 可以定义一个 None 值的别名来移除别名
alias("f_c", None)

# 别名已移除, f_c 变量恢复原名
f_c
""",
        "python",
    )

    # 混凝土强度等级
    f_c = 30 * unit.MPa
    alias("f_c", "混凝土强度等级")

    # 别名定义后, 变量在文档中将以别名形式显示, 直到别名被移除
    f_c

    # 可以定义一个 None 值的别名来移除别名
    alias("f_c", None)

    # 别名已移除, f_c 变量恢复原名
    f_c

    H3("输入变量")

    """
    该功能仅在 UI 模式下可用, 通过调用 UI() 函数可以创建一个输入窗体, 
    该窗体会在用户界面渲染出输入框供用户输入, 当程序检测到 UI 后，会暂停等待用户输入，
    输入完成后继续执行程序，并将用户输入的值作为函数的返回值。
    """

    Code(
        """
inputs = await UI(
    "结构参数输入",
    [
        Field("width", "宽度", FieldType.number, value=10),
        Field("length", "长度", FieldType.number, value=30),
        Field("height", "高度", FieldType.number, value=20),
    ],
)

f"用户输入的宽度为 {inputs['width']}，长度为 {inputs['length']}，高度为 {inputs['height']}。"
""",
        "python",
    )

    inputs = await UI(
        "结构参数输入",
        [
            Field("width", "宽度", FieldType.number, value=10),
            Field("length", "长度", FieldType.number, value=30),
            Field("height", "高度", FieldType.number, value=20),
        ],
    )

    "上述代码输出结果："

    f"用户输入的宽度为 {inputs['width']}，长度为 {inputs['length']}，高度为 {inputs['height']}。"

    # sub
    H2("变量下标")

    H3("默认下标规则")

    "如果你想让一个词成为下标, 可以在它后面使用下划线。例如, H_2 将被渲染为 H₂。"

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

    "由于 python 字段名限制, 无法使用非 ASCII 字符作为变量名, 若想使用非 ASCII 字符作为下标, 可以使用别名功能。"

    "你可以使用别名"

    alias("speed_car", "speed_汽车")
    speed_car
    distance = speed_car * 5 * unit.second
    alias("speed_car", None)
    "别名已移除, speed_car 变量恢复原名"
    speed_car

    H3("数组下标")

    "对于数组, 会自动将 [] 内的内容作为下标处理。"

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

    "输出效果如下："

    "单引号文本"

    "双引号文本"

    """
    三引号文本,
    这是第 1 行,
    这是第 2 行
    """

    # 换行
    Br()

    """
    单引号与双引号方式适合输出单行文本, 三引号方式适合输出多行文本。
    在三引号中可以换行, 但是实际渲染时会合并为一个段落, 并不会保留换行。
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

    "输出效果如下："

    integerNumber = 100
    floatNumber = 3.1415
    scientificNumber = 1.2e3
    complexNumber = 2 + 3j

    H2("张量")

    "张量是多维数组的通用表示, 它可以表示标量（0维张量）、向量（1维张量）、矩阵（2维张量）以及更高维度的数组。"

    "UzonCalc 支持使用 NumPy 库进行张量计算。"

    "下面是一些张量的示例："

    arr = np.array([[1, 2, 3], [4, 5, 6]])
    firstRow = arr[0, :]
    secondColumn = arr[:, 1]
    firstCell = arr[0, 0]

    "在 UzonCalc 中，变量使用斜体表示，张量使用加粗正体表示，以便区分。"

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
speedMPerS = 18 * unit.meter / unit.second
speedKmPerH = speedMPerS.to(unit.kilometer / unit.hour)
"单位转换前，速度 (m/s):"
speedMPerS
"单位转换后，速度 (km/h):"
speedKmPerH
""",
        "python",
    )

    speedMPerS = 18 * unit.meter / unit.second
    speedKmPerH = speedMPerS.to(unit.kilometer / unit.hour)
    "单位转换前，速度 (m/s):"
    speedMPerS

    "单位转换后，速度 (km/h):"
    speedKmPerH

    H2("字符串高级应用")

    H3("f-string")

    "f-string, 也被称为格式化字符串常量。它允许你在字符串中直接嵌入表达式，并在运行时计算这些表达式的值。"
    "要创建 f-string，你只需要在字符串的开头引号前添加一个 f 或 F"

    Code(
        """
 name = "Uzon"
 f"Hello, {name}! Welcome to UzonCalc."
 pi = 3.1415926535
 f"Value of pi up to 3 decimal places: {pi:.3f}"
""",
        "python",
    )

    "运行效果如下:"

    name = "Uzon"
    f"Hello, {name}! Welcome to UzonCalc."
    pi = 3.1415926535
    f"Value of pi up to 3 decimal places: {pi:.3f}"

    H3("f-string 中显示公式")

    """
默认情况下, f-string 中的表达式只会显示计算结果, 但有时候你可能希望在文档中同时显示公式和计算过程,
这时可以使用 enable_fstring_equation() 函数启用该功能, 启用后 f-string 中的表达式将同时显示公式和计算结果,
直到调用 disable_fstring_equation() 函数关闭该功能。
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

    H3("f-string 计算结果赋值")
    "你可以使用 := 海象运算符将 f-string 中表达式的计算结果赋值给一个变量, 以便在后续的计算中使用。"

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

    "运行效果如下："

    f"Area is calculated as {(tempArea := width * length)}."
    enable_fstring_equation()
    f"Area is calculated as {(tempArea := width * length)}."
    disable_fstring_equation()
    tempArea

    H2("操作符")

    "你可以使用标准的算术运算符 +、-、*、/ 和 **(幂) 进行计算。"
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
    H2("图表")

    "你可以使用 echarts、Matplotlib 在 UzonCalc 中创建图表。"

    "你也可以根据自己的喜好，使用其他绘图库, 如 Plotly、Seaborn 等"

    "使用 js 图表具有交互效果，使用 matplotlib 图表会将图表渲染为静态图片，适合打印输出。"

    H3("ECharts 示例")

    "可以使用 echarts 库创建丰富的交互式图表, 更多内容请参考官方文档和示例: https://echarts.apache.org/examples/zh/index.html#chart-type-line"

    Code(
        """
# 创建 echarts 图表
EChart(options)
""",
        "python",
    )

    "示例中的 options 参数参考：https://echarts.apache.org/examples/zh/editor.html?c=area-stack"

    # 参数参考：https://echarts.apache.org/examples/zh/editor.html?c=area-stack
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

    H3("ECharts 3D 示例")

    "可以使用 ECharts GL 创建 3D 图表。可以使用鼠标旋转、缩放图表以查看不同的角度和细节。"

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
                        "z": Javascript(
                            \"\"\"
function (x, y) {
  if (Math.abs(x) < 0.1 && Math.abs(y) < 0.1) {
    return '-';
  }
  return Math.sin(x * Math.PI) * Math.sin(y * Math.PI);
}
\"\"\"
                        ),
                    },
                }
            ],
        },
        use_gl=True,
    )
""",
        "python",
    )

    # 参数参考：https://echarts.apache.org/examples/zh/editor.html?c=simple-surface&gl=1
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

    H3("Matplotlib 示例")

    Code(
        """
hide()

def get_contour3d_plot():
    '''
    创建一个 3D 等高线图的示例函数
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
        创建一个 3D 等高线图的示例函数
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

    H2("希腊字母转换")

    "你可以直接使用希腊字母的英文名称如 'alpha' (α), 'beta' (β), 'gamma' (γ), 'delta' (δ), 系统会自动将其渲染为对应的希腊字母。"

    "以小写字母开头的名称会被渲染为小写希腊字母, 以大写字母开头的名称会被渲染为大写希腊字母。"

    "若不需要让字母被转义为希腊字母, 可以将名称使用引号包围, 例如 'alpha'"

    Code(
        """
rho_water = 1000 * unit.kilogram / unit.meter**3
gamma_0 = 9.81 * unit.meter / unit.second**2
""",
        "python",
    )

    rho_water = 1000 * unit.kilogram / unit.meter**3
    gamma_0 = 9.81 * unit.meter / unit.second**2

    H2("函数转换")

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

    "表格中表头的定义可能看起来有些复杂, 但实际上非常灵活强大, 支持合并单元格等功能。可以参考下面的示例："

    "该规则是基于 HTML 表格的定义方式设计的, 可以参考 HTML 表格相关资料了解详细用法。"

    "示例中, rowspan 表示单元格跨越的行数, colspan 表示单元格跨越的列数。"

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

    H2("调用 Excel 既有计算表格")

    "你可以在计算书中更新 Excel 中单元格的值，执行 Excel 中的计算公式, 然后获取计算结果并输出到计算书中。"

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

    "默认情况下, 若输入值没有变化, Excel 表格会被缓存, 以加快下次渲染速度。"

    H2("保存文档")

    H3("保存为 HTML 文件")

    H4("函数内部")

    "在 uzoncalc 定义的函数中，你可以使用 save() 函数将文档保存为 HTML 文件。"

    Code(
        """
save("../output/example.zh.html")
        """,
        "python",
    )

    H4("函数外部")

    "在函数外部, 你可以通过 run_sync() 函数的返回值获取计算上下文对象, 然后调用该对象的 save() 方法保存文档。"
    Code(
        """
ctx = run_sync(sheet2)
ctx.save("../output/example.zh.html")
        """,
        "python",
    )

    H3("打印为 PDF 文件")

    "使用浏览器打开生成的 HTML 文件, 然后使用浏览器自带的打印功能可以将文档保存为 PDF 文件。"

    H3("转换为 Word 文档")

    "你可以通过 pandoc 命令将 HTML 文档转换为 Word 文档。"

    H2("未来计划")

    "未来将向 UzonCalc 添加以下功能："

    "1. 添加 UI 与计算书发布功能"
    "2. 添加 AI 支持, 当你积累了一定的计算模板后, 可以通过 AI 自动生成新的计算书初稿"


if __name__ == "__main__":
    import time

    t0 = time.perf_counter()
    ctx = run_sync(sheet2)
    ctx.save("../output/example.zh.html")
    t1 = time.perf_counter()
    print(f"Execution time: {t1 - t0} seconds")
