from numpy import sqrt
from pathlib import Path
from uzoncalc import *
from uzoncalc.extension.excel import get_excel_table
from uzoncalc.extension.echarts import use_echarts, EChart, Javascript
import numpy as np


@uzon_calc()
async def sheet():
    # 定义 UI

    # 设置 title: 打印 pdf 时, 将在页眉左侧显示
    doc_title("UzonCalc 使用说明")

    # 设置页面大小, 如 A3, A4, Letter 等
    page_size("A4")

    # MARK: 一级标题, 一般用于封面的标题
    Title("UzonCalc 使用说明")

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

    "功能特色:"

    Markdown("""
- 🤖 **AI 友好** — 自带 SKILL, 计算过程就是 Python 代码，便于 AI 生成、审查和修改
- 🐍 **原生 Python** — 采用原生 Python 语法，上手简单，扩展性强
- 📐 **公式自动渲染** — 变量自动代入值，公式自动计算，计算过程自动展示
- 📌 **自动排版** — 章节号、图号自动生成，自适应排版
- 📏 **单位计算** — 可带单位计算，自动进行单位换算与量纲检查，无需关心单位一致性问题
- 📊 **图表支持** — 可使用 ECharts、svg 和 Matplotlib 绘制各式各样图表
- 📋 **Excel 复用** — 支持自动调用 Excel 进行计算并摘录结果
- 📄 **多格式输出** — 采用标准的 Mathml 格式, 支持转换为 PDF、Word 等文档
    """)

    Br()

    """
    使用 UzonCalc 非常简单, 不需要你精通 Python, 只要有使用 Excel 的公式的经验即可上手使用, 你可以把所有的操作都当成函数使用。
    """

    Info(
        "不要认为它使用了 python，涉及到编程，就觉得很难，重要的事情说三遍：很简单！很简单！很简单！"
    )

    # 通过调用 toc() 函数自动在此处生成目录
    toc("目录")

    # MARK: 安装使用说明
    H2("安装使用")

    # MARK: Windows
    H3("Windows 桌面端安装")

    "桌面端提供了计算书管理、UI 输入等额外功能，它是面向使用者。若您是计算书编写者，建议使用下方的 CLI 方式，可以搭配 VSCode 软件，实现自动格式化、语法检查等功能，提升编写效率。"

    "桌面端按以下步骤安装："

    "1. 软件下载"

    Markdown(
        "从 [Releases · uyoufu/UzonCalc](https://github.com/uyoufu/UzonCalc/releases) 下载 `win-x64` 版本，解压后，双击 `UzonCalc.exe` 启动。 "
    )

    "2. 复制以下代码到新建编辑框内"

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

    "3. 单击执行按钮运行"

    Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
        alt="UzonCalc 运行结果",
    )

    # MARK: CLI
    H3("CLI 安装")

    """
CLI 方式主要面向计算书编写者，它提供了自动格式化、语法检查等功能，可以提升编写效率。
在编辑计算书，建议使用 AI 辅助编写，特别是图表、某些复杂的计算逻辑，都可以让 AI 来完成。
    """

    "安装步骤如下："

    "1. 保证 Python 环境已安装"

    Markdown("2. 使用 `pip install uzoncalc` 或者 `uv add uzoncalc` 安装 UzonCalc")

    "3. 创建计算报告脚本"

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

    "4. 运行"

    Markdown("""
在 CLI 模式下有两种方式运行计算书：
- 使用 `python example.py`
- 使用 `uzoncalc example.py`
            """)

    Markdown("""
这两种方式的区别在于，使用前者，需要在代码最后使用 `view(sheet)` 来启动计算书服务,
而后者则不需要 `if __name__ == "__main__"` 语句            
        """)

    "当执行如下命令时："

    Code(
        """
python example.py
""",
        "python",
    )

    "将会出现：`Serving document at: http://127.0.0.1:32180/` 字样，单击通过浏览器打开即可查看效果。"

    "这种方式启动的计算书服务不会热重载，当计算书代码发生变化时，需要手动重启服务。"

    Markdown(
        "为了方便开发，建议使用 `uzoncalc example.py` 来运行计算书，当计算书代码发生变化时，会自动重载服务。"
    )

    # MARK: Python 基础语法
    H2("基础语法")

    "UzonCalc 基于 python 实现，没有引入额外的定义，因此，编写计算即为使用 python 编写代码。"

    "若你之前没有接触过 Python 编程语言, 下面是一些基础语法介绍, 帮助你快速上手。"

    Markdown("""
1. 文本: 使用单引号 ' 、双引号 " 或 三引号 \""" 包围的字符串表达文本内容
2. 数字: 可以直接使用整数和浮点数, 例如 `42` 或 `3.14`
3. 布尔值: 使用 `True` 和 `False` 表示布尔值, 例如 `isValid = True`
4. 列表: 使用方括号 [] 创建列表, 例如 `myList = [1, 2, 3, 4, 5]`
5. `=` 号: 用于赋值操作, 例如 `a = 5` 将数字 5 赋值给变量 a
6. `+, -, *, /, **` 运算符: 用于基本的数学运算, 例如 + 用于加法, - 用于减法, * 用于乘法, / 用于除法, ** 用于幂运算
7. `>, <, >=, <=, ==, !=` 比较运算符: 用于比较两个值的大小或相等性, 例如 `a > b` 判断 a 是否大于 b, `a == b` 判断 a 是否等于 b
8. 变量名可以包含字母、数字和下划线, 但不能以数字开头。在 UzonCalc 中, 推荐使用 camelCase 命名法, 例如 `myVariableName`。因为 _ 下划线会被用作下标符号        
9. 缩进: Python 使用缩进来表示代码块的层级关系, 通常使用 4 个空格进行缩进
10. 注释: 以 # 开头的内容为注释。注释不会被执行, 仅用于解释代码
11. 函数定义: 使用 def 关键字定义函数, 例如 `def myFunction(param1, param2):` 用于定义一个名为 `myFunction` 的函数, 接受两个参数 param1 和 param2。通过 `myFunction(5, 10)` 调用该函数, 并传入参数值 5 和 10。      
12. 模块导入: 使用 import 语句导入模块, 例如 `from numpy import sqrt` 导入 sqrt 函数, 通过 `sqrt(16)` 调用该模块中的 sqrt 函数计算平方根。
""")

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

    Markdown("""
你可以通过调用 `toc('目录名')` 函数自动在调用的位置生成文档目录。
本文的目录即为通过 `toc('目录')` 函数生成。
目录会根据文档中的标题层级自动生成, 并自动计算页码。
生成效果见上面实际目录部分。
""")

    # MARK: 自动图表编号
    H2("自动图表编号")

    "在使用 UzonCalc 时，你不需要单独对图表设置编号，系统会自动生成编号，在增删图表时，维护工作量将大大降低。"

    "在调用 Img、Table、Echarts、Plot 函数时，系统会返回一个图表占位字符串，你可以在后续的文档中使用该占位字符串来引用图表。"

    "下面以图片为例, 代码如下："

    Code(
        """
imgNo = Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
        alt="UzonCalc 运行结果",
    )

f"现在你可以使用 imgNo 引用这张图片了：见 {imgNo} 所示"
""",
        "python",
    )

    "实际效果："

    imgNo = Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
        alt="UzonCalc 运行结果",
    )

    f"现在你可以使用 imgNo 引用这张图片了：见 {imgNo} 所示"

    "从上面的示例中，还可以看到，占位符最终会替换图片的编号，且可以单击该编号跳转到对应的图片位置。"

    "图表的编号支持在后续代码任意位置使用"

    Markdown("""
图表编号的前缀，可以使用 `figure_prefix("Figure")` 和 `table_prefix("Table")` 来设置。
该设置会对后续的图表生效，默认前缀分别为 "图" 和 "表"。
""")

    figure_prefix("Figure")

    imgNo2 = Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
        alt="UzonCalc 运行结果",
    )

    f"现在引用上面的图片：如 {imgNo2} 所示。可以看到，前缀已经变成了 Figure。"

    # 切回默认前缀
    figure_prefix("图")

    H2("标题")

    Markdown("""
系统内置了两种标题函数: `Title()` 和 `H1()`, 通过 `H1('标题名')` 来使用。             
标题有 1~6 级, 分别对应 H1, H2, H3, H4, H5, H6 函数。             

一般来说, H1 用于文档的主标题, H2 用于章节标题, H3 用于小节标题, 依此类推。
""")

    H2("文本类型")

    Markdown(
        '可以通过单引号(`\'`)、双引号(`"`)、三引号(`"""`) 表示将要输出的内容作为段落输出。'
    )

    "示例如下:"

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

    "上述代码输出结果为："

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

    Info(
        "这与日常使用 Word 文档时的输入样式有些区别，在 UzonCalc 中，所有的文本都需要用引号包裹。这其实是 python 语法的要求"
    )

    H2("数值类型")

    "数值类型不需要用引号包裹，直接输入即可。"

    "示例如下:"

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

    H2("运算与比较")

    Markdown(
        "你可以使用标准的算术运算符 `+`、`-`、`*`、`/` 和 `**`(表示幂) 对数值进行计算。"
    )
    Markdown("还可以使用 `>=`、`<=`、`==`、`!=` 值进行比较。")

    "示例如下:"

    Code(
        """
operatorResult = (5 + 3) * 2 - 4 / 2**2
comparisonResult = (5 > 3) and (2 == 2) or (4 != 5)
        """,
        "python",
    )
    operatorResult = (5 + 3) * 2 - 4 / 2**2
    comparisonResult = (5 > 3) and (2 == 2) or (4 != 5)

    H2("使用变量")

    "变量顾名思义，就是在程序中定义的用于存储数据的容器，它的作用是在程序中重复使用同一数据时，避免重复输入。"

    Markdown("你也可以将变量理解成公式中的各个参数符号, 如 `f_c`、`E`、`I` 等。")

    "以下面的代码为例："

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

    H3("变量命名规则")

    "变量名可以包含字母、数字和下划线, 但不能以数字开头"

    Markdown(
        "在 UzonCalc 中, 推荐使用 camelCase 命名法, 例如 myVariableName。因为 `_` 下划线会被用作下标符号。"
    )

    H3("变量别名")

    "由于 python 变量名的限制, 你无法直接使用非 ASCII 字符作为变量名, 但有时候你可能希望在文档中使用更友好的名称来表示变量, 这时可以使用别名功能。"

    Markdown('别名通过 alias("变量名", "别名")` 函数定义:')

    "示例如下:"

    Code(
        """
# 混凝土强度等级
f_c = 30 * unit.MPa
alias("f_c", "混凝土强度等级")

# 别名定义后, 变量在文档中将以别名形式显示, 直到别名被移除
f"现在将会输出别名: {f_c}"

# 可以定义一个 None 值的别名来移除别名
alias("f_c", None)

# 别名已移除, f_c 变量恢复原名
f"别名已经取消，现在将会输出原名: {f_c}"
""",
        "python",
    )

    # 混凝土强度等级
    f_c = 30 * unit.MPa
    alias("f_c", "混凝土强度等级")

    # 别名定义后, 变量在文档中将以别名形式显示, 直到别名被移除
    f"现在将会输出别名: {f_c}"

    # 可以定义一个 None 值的别名来移除别名
    alias("f_c", None)

    # 别名已移除, f_c 变量恢复原名
    f"别名已经取消，现在将会输出原名: {f_c}"

    # MARK: 输入变量
    H3("输入变量")

    Markdown("""
该功能仅在 UI 模式下可用, 通过调用 `UI()` 函数可以创建一个输入窗体, 
该窗体会在用户界面渲染出输入框供用户输入, 当程序检测到 UI 后，会暂停等待用户输入，
输入完成后继续执行程序，并将用户输入的值作为函数的返回值。
             
UI 函数的参数有 3 个，前两个是必须的，最后一个参数是可选的：

- `title`: 窗口标题
- `fields`: 字段列表，每个字段包含字段名、字段说明、字段类型和默认值， 使用 `Field()` 函数定义。
- `caption`: 窗口底部说明文字
             
代码如下：
    """)

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

f"用户输入的宽度为 {inputs.width}，长度为 {inputs.length}，高度为 {inputs.height}。"
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

    "上述代码在 UI 上的效果如下图所示："

    inputImg = Img(
        "https://oss.uzoncloud.com:2234/public/files/images/image-20260615090832320.png",
        "输入变量演示",
    )

    f"从 {inputImg} 中可以看出, 系统会将你定义的输入代码转换为可视化 UI，用户可以在 UI 上输入值与程序进行交互"

    "上述代码输出结果："

    f"用户输入的宽度为 {inputs.width}，长度为 {inputs.length}，高度为 {inputs.height}。"

    # MARK: 变量下标
    H2("变量下标")

    H3("默认下标规则")

    "如果你想让一个词成为下标, 可以在它后面使用下划线。例如, H_2 将被渲染为 H₂。"

    "示例如下:"

    Code(
        """
a_x = 10 * unit.meter / unit.second**2
speed_car = a_x * 2 * unit.second
""",
        "python",
    )

    a_x = 10 * unit.meter / unit.second**2
    speed_car = a_x * 2 * unit.second

    H3("非 ASCII 字符下标")

    "由于 python 字段名限制, 无法使用非 ASCII 字符作为变量名, 若想使用非 ASCII 字符作为下标, 可以使用别名功能。"

    "你可以使用别名来表示非 ASCII 字符作为下标。"

    "示例如下:"

    Code("""
alias("speed_car", "speed_汽车")
f"现在将会输出别名下标: {speed_car}"
distance = speed_car * 5 * unit.second
alias("speed_car", None)
f"别名已移除, speed_car 变量恢复原名: {speed_car}"
""")

    alias("speed_car", "speed_汽车")
    f"现在将会输出别名下标: {speed_car}"
    distance = speed_car * 5 * unit.second
    alias("speed_car", None)
    f"别名已移除, speed_car 变量恢复原名: {speed_car}"

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

    H2("多维数组")

    "多维数组的通用表示一般叫做张量，它可以表示标量（0维张量）、向量（1维张量）、矩阵（2维张量）以及更高维度的数组。"

    "UzonCalc 支持使用 NumPy 库进行张量计算。"

    "下面是一些张量的示例："

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

    "在 UzonCalc 中，变量使用斜体表示，大于 1 维的张量使用加粗正体表示，与论文中的表示一致。"

    # MARK: 单位
    H2("单位")

    "UzonCalc 在进行公式计算时，支持带单位进行计算，同一量纲不同的单位，不需要换算，可以直接进行计算。如："

    totalLength = 10 * unit.m + 20 * unit.cm

    H3("使用单位")

    Markdown("""
UzonCalc 使用 pint 作为单位计算引擎。你可以通过 `unit.*` 的方式使用单位, `*` 表示具体单位符号，如 `unit.m` 表示米。
具体的单位列表请参考文档：https://github.com/hgrecco/pint/blob/master/pint/default_en.txt ，
下面是一些单位计算的示例。
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

    "同一量纲不同的单位，不需要换算，可以直接进行计算。如："

    totalLength = 10 * unit.m + 20 * unit.cm

    H3("单位转换")

    Markdown("你可以使用 `to()` 方法将带单位的量转换为其他单位。")

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

    H2("希腊字母转换")

    "你可以直接使用希腊字母的英文名称如 \\alpha (alpha), \\beta (beta), \\gamma (gamma), \\delta (delta), 系统会自动将其渲染为对应的希腊字母。"

    "以小写字母开头的名称会被渲染为小写希腊字母, 以大写字母开头的名称会被渲染为大写希腊字母。"

    "若不需要让字母被转义为希腊字母, 可以在名称前添加 \\, 例如 、\\\\alpha"

    Code(
        """
rho_water = 1000 * unit.kilogram / unit.meter**3
gamma_0 = 9.81 * unit.meter / unit.second**2
""",
        "python",
    )

    rho_water = 1000 * unit.kilogram / unit.meter**3
    gamma_0 = 9.81 * unit.meter / unit.second**2

    H2("函数样式")

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
这时可以使用 \\enable_fstring_equation() 函数启用该功能, 启用后 f-string 中的表达式将同时显示公式和计算结果,
直到调用 \\disable_fstring_equation() 函数关闭该功能。
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

    H2("字符串转义")

    Markdown(
        "前面章节提到，字符的英文名、以 `_` 连接的变量名会将其渲染为希腊字母和下标形式。如果要保持原始字符, 可以在字符前添加 \\, 例如 、`\\alpha`"
    )

    # MARK: 图表
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
        caption="3D 地球示例",
    )
""",
        "python",
    )

    # 参考：https://echarts.apache.org/examples/zh/editor.html?c=globe-layers&gl=1
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
        caption="3D 地球示例",
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
Plot(get_contour3d_plot(), caption="3D 等高线示例")
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
    Plot(get_contour3d_plot(), caption="3D 等高线示例")

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
        title="示例表格",
    )

    f"Table() 函数返回表格的引用，你可以直接在后续中使用，例如：上表的引用为 {table_name}"

    H2("调用 Excel 既有计算表格")

    "你可以在计算书中更新 Excel 中单元格的值，执行 Excel 中的计算公式, 然后获取计算结果并输出到计算书中。"

    "这对于重用现有的 Excel 计算表格非常有用。"

    "P 函数可以将表格内容作为段落输出。"

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

    "默认情况下, 若输入值没有变化, Excel 表格会被缓存, 以加快下次渲染速度。"

    H2("保存文档")

    H3("保存为 HTML 文件")

    "在 uzoncalc 定义的函数中，你可以使用 save() 函数将文档保存为 HTML 文件。"

    "你可以通过 run_sync() 函数的返回值获取计算上下文对象, 然后调用该对象的 save() 方法保存文档。"

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

    "你可以通过 pandoc 命令将 HTML 文档转换为 Word 文档。具体使用方法见 pandoc 官方文档。"

    H2("未来规划")

    "未来将向 UzonCalc 添加以下功能："

    "1. 添加 UI 与计算书发布功能"
    "2. 添加 AI 支持, 当你积累了一定的计算模板后, 可以通过 AI 自动生成新的计算书初稿"

    H2("结语")

    "AI 已至，不进则退，让我们拥抱 AI，开启新的计算之旅！"


if __name__ == "__main__":
    view(sheet)
