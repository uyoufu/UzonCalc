---
name: uzoncalc-writer
description: 使用 uzoncalc 以编写 python 代码的方式创建工程计算书，实现公式自动计算、自动排版、自动渲染 HTML 文档等功能
---

# uzoncalc-writer skill

UzonCalc 是一个基于 Python 的工程计算书生成工具。通过在 `async def` 函数中编写计算逻辑，UzonCalc 能自动捕获变量赋值、公式推导过程，并渲染为带目录、数学公式、表格、图表的 HTML 计算书。

## 最小模板示例

```python
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("计算书标题")

    H1("示例章节")
    "这是一段说明文字。"

    a = 10 * unit.meter
    b = 5 * unit.meter
    c = a + b # 自动渲染公式：c = a + b = 15 m

if __name__ == "__main__":
    view(sheet)
```

## 核心规则

| 规则                           | 说明                                                      |
| ------------------------------ | --------------------------------------------------------- |
| 函数必须为异步 `async def`     | `@uzon_calc()` 仅支持异步函数                             |
| 字符串字面量即段落             | 函数体内裸字符串 `"文本"` / `"""多行"""` 作为段落输出     |
| 变量赋值自动渲染               | `x = expr` 被捕获并渲染为数学公式 `x = expr = 值`         |
| 变量名用 camelCase             | `_` / `^` 会被解析为下标/上标，普通变量命名避免使用下划线 |
| 希腊字母自动转换               | `alpha`→α，`Beta`→Β，首字母大写转换为大写希腊字母         |
| 纯函数调用不会插桩输出调用过程 | 如 `f(x)` 不会渲染为 `f(x)`，而是直接调用                 |

## 编写要求

1. 以手写计算书的方式组织代码逻辑
2. 除了不向用户展示过程的计算逻辑外，其它逻辑都在 `async def` 函数中编写
3. 非展示的计算逻辑可以封装为纯函数调用
4. 所有逻辑都在单文件中实现，方便用户分发
5. 变量命名优先使用缩写，提升最终结果的可读性

## 可用规则文档

### 文档结构

用于定义文档的结构和布局。

```python
doc_title("页眉标题")      # 设置页面/打印页眉标题 [可选]
page_size("A4")            # 页面大小：A4、A3、Letter 等 [可选]
toc("目录")                # 在当前位置插入目录（自动编号）[可选]
font_family("Arial")       # 设置字体 [可选]
head("meta", {"name": "author", "content": "UzonCalc"})  # 添加去重后的 head 标签 [可选]
style("body", {"line-height": "1.8"})                    # 添加全局 CSS 样式 [可选]

H1("一级标题")             # H1~H6 对应六级标题，自动带有编号
H2("二级标题")
H3("三级标题")

Br()                       # 插入空行
Info("提示信息")           # 蓝色信息框
Code("代码", "python")     # 代码块，支持语法高亮
P("段落")                  # 显式段落（等价于裸字符串）
```

### HTML 元素

可以使用以下预定义的函数，简化 HTML 内容的生成。其中，以小写字母开头的函数会返回 HTML 结果，而以大写字母开头的函数会直接渲染到文档中。

```python
# 小写函数：返回 HTML 字符串，适合组合嵌套内容
content = div(
    [
        h2("截面参数"),
        p("以下参数用于承载力验算。"),
        span("重要", classes="text-red-600 font-bold"),
    ],
    classes="border p-2",
)
P(content)

# 大写函数：直接追加到当前文档
H1("设计依据")
P("本节列出主要设计参数。")
Div(
    [
        h3("材料"),
        p("混凝土强度等级为 C50。"),
    ],
    classes="bg-gray-50 p-3",
)
```

常用 HTML 元素如下：

| 函数                    | 说明                                                   |
| ----------------------- | ------------------------------------------------------ |
| `h(tag, children, ...)` | 通用 HTML 构造器，`children` 支持字符串或字符串列表    |
| `h1`~`h6` / `H1`~`H6`   | 标题元素，小写返回字符串，大写直接渲染                 |
| `title` / `Title`       | 文档大标题，默认居中、加粗、大字号                     |
| `subtitle` / `Subtitle` | 文档副标题，默认居中、加粗                             |
| `p` / `P`               | 段落                                                   |
| `div` / `Div`           | 块级容器                                               |
| `span` / `Span`         | 行内容器                                               |
| `row` / `Row`           | 行容器，默认渲染为 `div`，可通过 `tag` 指定标签        |
| `br` / `Br`             | 换行，自闭合元素                                       |
| `img` / `Img`           | 图片，支持 `alt`、`width`、`height`                    |
| `input` / `Input`       | 输入元素，当前主要用于生成带 `value` 的 HTML 输入标签  |
| `code` / `Code`         | 代码块，`language` 会生成 `language-python` 等高亮类名 |
| `info` / `Info`         | 蓝色提示框                                             |
| `laTex` / `LaTex`       | 原始 LaTeX 内容标签                                    |
| `plot` / `Plot`         | Matplotlib 图像或 PNG 二进制内容转为内嵌 base64 图片   |

属性与样式使用 `classes` 和 `props()`：

```python
# classes 会写入 HTML class 属性，适合 Tailwind/页面样式类
P("控制性参数", props=props(id="control-params"))
Div("验算通过", classes="text-green-700 font-bold")

# props 支持 id、classes、styles，并将自定义属性中的下划线转为短横线
P(
    "带自定义属性的段落",
    props=props(
        id="note-1",
        classes="text-sm",
        styles={"color": "#444", "margin-top": "8px"},
        data_value="section-note",
        aria_label="说明段落",
    ),
)

# 当同时传入 classes 和 props.classes 时，函数参数 classes 优先
Div(
    "最终使用 text-blue-700",
    classes="text-blue-700",
    props=props(classes="text-red-700"),
)
```

复杂内容建议先用小写函数组合，再用大写函数渲染：

```python
parameterPanel = div(
    [
        h3("几何参数"),
        p(f"梁高：{beamHeight}"),
        p(f"梁宽：{beamWidth}"),
        info("单位统一采用 SI 制。"),
    ],
    classes="my-3 p-3 border",
)
P(parameterPanel)
```

插入图片、代码、LaTeX 与 Matplotlib 图：

```python
Img("assets/section.png", alt="截面示意图", width=480)
Code(
    """
    stress = force / area
    """,
    language="python",
)
LaTex(r"\sigma = \frac{N}{A}")

import matplotlib.pyplot as plt

hide()
fig, ax = plt.subplots()
ax.plot([0, 1, 2], [0, 1, 4])
show()
Plot(fig, width=520)
```

注意：

- HTML 内容不会自动转义 `children`，用户输入或外部文本应先自行清洗后再拼入 HTML。
- `children` 列表会按顺序直接拼接，适合嵌套由 `p()`、`div()`、`span()` 等返回的 HTML 片段。
- `img()` 会额外包一层居中容器；设置 `alt` 时会在图片下方显示说明文字。
- `Plot()` 支持 Matplotlib `savefig` 对象，也支持 PNG 二进制数据；普通文件路径图片使用 `Img()`。

### 变量与公式

变量名参考 linux 风格缩写，变量名不宜过长。普通 Python 变量优先使用 camelCase；需要工程符号、中文、上下标时，用 `alias()` 设置展示名。

```python
# 普通变量赋值（自动渲染公式）
force = 100 * unit.newton
area = 2 * unit.meter**2
stress = force / area

# 别名（用于中文变量名、工程符号或复杂上下标）
alias("rhoWater", "rho_水")        # _ 表示下标
rhoWater = 1000 * unit.kilogram / unit.meter**3

alias("sigmaMax", "sigma_{max}^2") # ^ 表示上标，{} 用于复杂脚标分组
sigmaMax = 30 * unit.MPa

alias("aPrimeP0", "a^'_p0")        # 可组合上标和下标
aPrimeP0 = 12 * unit.meter

alias("rhoWater", None)            # 传 None 移除别名

# f-string：默认只显示结果
f"应力为 {stress}。"

# 启用后同时显示公式和结果
enable_fstring_equation()
f"应力为 {stress}。"
disable_fstring_equation()

# 海象运算符在 f-string 中赋值
f"面积 = {(A := 3 * unit.meter**2)}"
```

`alias("变量名", "别名")` 只替换展示名称；替换后的 `_` 和 `^` 会继续由上下标后处理器渲染。未分组脚标读取一个连续 token，复杂脚标使用 `{}` 分组，例如 `M_{max}`、`x^{n+1}`、`x_i^2`。若需要保留原始 `_`、`^` 或希腊字母名称，在字符前加反斜杠转义，例如 `r"\alpha"`、`r"x\_raw"`。

### 单位

```python
from uzoncalc import unit

l = 5 * unit.meter
f = 100 * unit.newton
p = f / (l * l)              # 自动单位运算
v = l.to(unit.centimeter)    # 单位换算

# 常用单位：meter/m、kilogram/kg、newton/N、MPa、kN、second/s、hour、kilometer/km 等
# 完整列表见 pint 文档
```

### 控制渲染

```python
hide()                       # 后续内容不输出到文档
def helper(): ...            # 辅助函数定义，不渲染
show()                       # 恢复渲染

inline()                     # 后续元素内联排列
x = 1; y = 2
end_inline()                    # 结束内联

enable_substitution()        # 开启变量值代入（默认开启）
disable_substitution()       # 关闭代入（仅显示符号公式）
decimal(2)                   # 设置小数显示位数
figure_prefix("图")          # 设置后续图片/图表编号前缀
table_prefix("表")           # 设置后续表格编号前缀
```

### 表格

```python
Table(
    headers=[                           # 表头支持多行、th 合并单元格
        [
            th("构件", rowspan=2),
            th("材料", rowspan=2),
            th("弹性模量 (MPa)", colspan=2),
        ],
        ["Ec", "Es"],
    ],
    rows=[                              # 二维列表表示多行
        ["盖梁", "C60", 36000, 34500],
        ["墩柱", "C50", 34500, 32500],
    ],
    title="材料参数",
)

# Td 可设置单元格样式；Tr 可设置整行样式
Table(
    headers=["项目", "数值", "备注"],
    rows=[
        Tr(
            [
                Td("梁高", classes="font-bold"),
                1.8 * unit.meter,       # 任意值会通过 str() 渲染
                Td("控制参数", classes="text-red-600"),
            ],
            classes="bg-yellow-50",
        ),
        Tr(["混凝土等级", "C50", None]), # None 会显示为 "None"
    ],
)

# 扁平 rows 表示单行；Td 列表也会作为单行处理
Table(
    headers=["名称", "值"],
    rows=[Td("宽度", classes="font-bold"), 2.5 * unit.meter],
)
```

### 图表

生成图表的过程不需要显示过程，若图表复杂，在单独的函数中定义。
静态图首先使用 svg 方式，交互式图表使用 echarts 方式。

**配色**

进行图表配色时，优先选择以下配色方案：

- primary: #7367f0;
- secondary: #42b883;
- dark-page: #e0e0e0;
- positive: #42b883;
- negative: #ff7a7a;
- info: #65a0bb;

**echarts 图表**

通过 echarts 生成交互式图表， 在使用中，若对 echarts 中的参数不确定，读取 https://echarts.apache.org/zh/option.html 读取文档

```python
# ECharts 交互式图表（推荐）
from uzoncalc.extension.echarts import use_echarts, EChart, Javascript

EChart({
    "xAxis": {"type": "category", "data": ["Mon", "Tue", "Wed"]},
    "yAxis": {"type": "value"},
    "series": [{"type": "bar", "data": [120, 200, 150]}],
})

# use_gl=True 时，渲染 ECharts GL 3D 图表
EChart({...}, use_gl=True)

```

**svg**

对于一般图示，建议使用 svg.py, 示例如下:

```python
import svg
canvas = svg.SVG(
    width=60,
    height=60,
    elements=[
        svg.Circle(
            cx=30, cy=30, r=20,
            stroke="red",
            fill="white",
            stroke_width=5,
        ),
    ],
)
P(canvas)
```

**Matplotlib 图表**

也可以使用 Matplotlib 生成静态图表

```python
# Matplotlib 静态图（适合打印）
import matplotlib.pyplot as plt
hide()
def make_fig():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    return plt
show()
Plot(make_fig())
```

### UI 输入（交互模式）

用 `UI()` 定义输入窗口，用 `Field()` 定义字段。计算脚本不需要写前端代码；前端会把字段定义交给 `LowCodeForm` 渲染，并在用户确认后把当前窗口的输入值返回给 Python。

```python
from uzoncalc import UI, Field, FieldType

inputs = await UI(
    "结构参数",
    [
        Field("width",  "宽度",   FieldType.number, value=10),
        Field("height", "高度",   FieldType.number, value=5),
        Field("mat",    "材料",   FieldType.selectOne, options=["C30", "C40", "C50"]),
    ],
)
width = inputs.width * unit.meter
```

`FieldType` 可选值：`text`、`number`、`selectOne`、`selectMany`、`boolean`、`textarea`。当前 Python `Field` 只暴露以下控制项：

| 参数        | 说明                                                                 |
| ----------- | -------------------------------------------------------------------- |
| `name`      | 返回值字段名，必须是适合属性访问的标识符，例如 `inputs.width`        |
| `label`     | 前端显示标签                                                         |
| `type`      | 输入类型，默认 `FieldType.text`                                      |
| `placeholder` | 占位提示文本                                                      |
| `value`     | 默认值；静默执行时直接作为输入值                                     |
| `options`   | `selectOne` / `selectMany` 的选项，当前优先使用字符串列表            |
| `visible`   | JS 函数字符串，控制字段是否显示                                      |
| `onChanged` | JS 函数字符串，字段值变化时执行，可联动修改其它字段值                 |

字段类型选择规则：

- 数值输入用 `FieldType.number`，前端会按数字处理；进入工程计算时仍要显式乘单位。
- 单选用 `FieldType.selectOne`，多选用 `FieldType.selectMany`，通过 `options=["C30", "C40"]` 给选项。
- 开关/是否类输入用 `FieldType.boolean`。
- 长文本输入用 `FieldType.textarea`。

字段联动通过 `visible` 和 `onChanged` 完成，二者必须写成完整的 JS 函数字符串：

```python
inputs = await UI(
    "截面参数",
    [
        Field("useAdvanced", "启用高级参数", FieldType.boolean, value=False),
        Field(
            "extraDepth",
            "附加高度",
            FieldType.number,
            value=0,
            visible="(values) => values.useAdvanced === true",
        ),
        Field("width", "宽度", FieldType.number, value=2.0),
        Field("height", "高度", FieldType.number, value=1.5),
        Field(
            "area",
            "面积",
            FieldType.number,
            value=3.0,
            onChanged="(value, oldValue, values) => { values.area = values.width * values.height }",
        ),
    ],
)
```

`visible` 的参数 `values` 是当前输入窗口的表单值对象，key 来自每个 `Field.name`，例如 `values.useAdvanced`、`values.width`。`visible` 应只读取 `values` 并返回真假值，不要写副作用。

`onChanged` 的参数依次为 `value`、`oldValue`、`values`、`fields`：

- `value` 是当前字段的新值。
- `oldValue` 是当前字段变化前的旧值。
- `values` 是当前输入窗口的表单值对象，可通过 `values.xxx = ...` 联动修改其它字段值。
- `fields` 是当前窗口的字段定义列表，通常不需要使用。

注意：

- 不要把 `visible` / `onChanged` 写成表达式片段，例如不要写 `"values.enabled === true"`；应写成 `"(values) => values.enabled === true"`。
- `visible` 编译失败时前端会默认显示该字段；`onChanged` 编译失败时前端会移除该回调。
- 多个 `await UI(...)` 会按执行顺序生成多个输入窗口，每个窗口返回自己的字段值。
- 前端 `LowCodeForm` 还支持更多属性，但 Python `Field` 当前未暴露 `required`、`validate`、`parser`、`optionLabel`、`optionValue`、`emitValue`、`tooltip`、`disable`、`classes` 等参数，编写计算书时不要使用这些未暴露接口。

### Excel 集成

```python
from uzoncalc.extension.excel import get_excel_table

P(get_excel_table(
    excel_path="examples/calc.xlsx",
    values={
        "Sheet1!A2": 6,
        "Sheet1!B2": 10,
    },
    range="Sheet1!A1:C3",
))
```

### 保存文档

```python
# 推荐在函数外部保存
ctx = run_sync(sheet)
ctx.save("output/result.html")
```

生成的 HTML 可用浏览器打印为 PDF，或用 pandoc 转为 Word。

### 运行方式

```python
if __name__ == "__main__":
    ctx = run_sync(sheet)          # 同步执行（静默模式，UI 用默认值）
    ctx.save("output.html")

# 多个计算书
ctx1 = run_sync(sheet1)
ctx2 = run_sync(sheet2)
ctx1.save("out1.html")
ctx2.save("out2.html")
```

## 注意要点

- 函数体内所有顶层赋值语句均被拦截渲染，若不希望某段代码渲染，用 `hide()` / `show()` 包裹
- 除 `@uzon_calc()` 函数外，其他函数均不被渲染
- 变量名、别名和普通文本中的 `_` / `^` 会渲染为下标/上标，命名时应使用 camelCase
- 复杂上下标使用 `{}` 分组，组合脚标可写成 `x_i^2`、`M_{max}^{n+1}`
- 数组下标 `arr[0, 1]` 自动渲染为下标形式
- `@uzon_calc()` 函数支持相互嵌套调用，内层函数的内容合并到当前上下文
- 单位计算依赖 pint，量纲不匹配时会抛出错误
