---
name: uzoncalc-writer
description: 使用 uzoncalc 以编写 python 代码的方式创建工程计算书，实现公式自动计算、自动排版、自动渲染 HTML 文档等功能
---

# uzoncalc-writer skill

## 概述

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
    ctx = run_sync(sheet)
    ctx.save("output.html")   # 也可在函数外保存
```

## 核心规则

| 规则                 | 说明                                                  |
| -------------------- | ----------------------------------------------------- |
| 函数必须 `async def` | `@uzon_calc()` 仅支持异步函数                         |
| 字符串字面量即段落   | 函数体内裸字符串 `"文本"` / `"""多行"""` 作为段落输出 |
| 变量赋值自动渲染     | `x = expr` 被捕获并渲染为数学公式 `x = expr = 值`     |
| 变量名用 camelCase   | `_` 被解析为下标（`H_2` → H₂），避免用下划线命名变量  |
| 希腊字母自动转换     | `alpha`→α，`Beta`→Β，首字母大写得大写希腊字母         |

## 文档结构 API

```python
doc_title("页眉标题")      # 设置页面/打印页眉标题
page_size("A4")            # 页面大小：A4、A3、Letter 等
toc("目录")                # 在当前位置插入目录（自动编号）
font_family("Arial")       # 设置字体

H1("一级标题")             # H1~H6 对应六级标题，自动带有编号
H2("二级标题")
H3("三级标题")

Br()                       # 插入空行
Info("提示信息")           # 蓝色信息框
Code("代码", "python")     # 代码块，支持语法高亮
P("段落")                  # 显式段落（等价于裸字符串）
```

## 变量与公式

```python
# 普通变量赋值（自动渲染公式）
force = 100 * unit.newton
area = 2 * unit.meter**2
stress = force / area

# 别名（用于中文变量名或复杂下标）
alias("rhoWater", "ρ_水")
rhoWater = 1000 * unit.kilogram / unit.meter**3
alias("rhoWater", None)    # 传 None 移除别名

# f-string：默认只显示结果
f"应力为 {stress}。"

# 启用后同时显示公式和结果
enable_fstring_equation()
f"应力为 {stress}。"
disable_fstring_equation()

# 海象运算符在 f-string 中赋值
f"面积 = {(A := 3 * unit.meter**2)}"
```

## 单位

```python
from uzoncalc import unit

l = 5 * unit.meter
f = 100 * unit.newton
p = f / (l * l)              # 自动单位运算
v = l.to(unit.centimeter)    # 单位换算

# 常用单位：meter/m、kilogram/kg、newton/N、MPa、kN、second/s、hour、kilometer/km 等
# 完整列表见 pint 文档
```

## 控制渲染

```python
hide()                       # 后续内容不输出到文档
def helper(): ...            # 辅助函数定义，不渲染
show()                       # 恢复渲染

inline()                     # 后续元素内联排列
x = 1; y = 2
endInline()                    # 结束内联

enable_substitution()        # 开启变量值代入（默认开启）
disable_substitution()       # 关闭代入（仅显示符号公式）
```

## 表格

```python
Table(
    headers=[                           # 表头（支持多行、合并单元格）
        [
            th("构件", rowspan=2),
            th("材料", rowspan=2),
            th("弹性模量 (MPa)", colspan=2),
        ],
        ["Ec", "Es"],
    ],
    rows=[
        ["盖梁", "C60", 36000, 34500],
    ],
    title="材料参数",
)
```

## 图表

```python
# ECharts 交互式图表（推荐）
from uzoncalc.extension.echarts import use_echarts, EChart, Javascript

EChart({
    "xAxis": {"type": "category", "data": ["Mon", "Tue", "Wed"]},
    "yAxis": {"type": "value"},
    "series": [{"type": "bar", "data": [120, 200, 150]}],
})

# ECharts GL 3D 图表
EChart({...}, use_gl=True)

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

## UI 输入（交互模式）

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

`FieldType` 可选值：`text`、`number`、`selectOne`、`selectMany`、`checkbox`、`textarea`

## Excel 集成

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

## 保存文档

```python
# 在函数内部保存
save("output/result.html")

# 在函数外部保存
ctx = run_sync(sheet)
ctx.save("output/result.html")
```

生成的 HTML 可用浏览器打印为 PDF，或用 pandoc 转为 Word。

## 运行方式

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

## 注意事项

- 函数体内所有顶层赋值语句均被拦截渲染，若不希望某段代码渲染，用 `hide()` / `show()` 包裹
- 变量名中的 `_` 渲染为下标，命名时应使用 camelCase
- 数组下标 `arr[0, 1]` 自动渲染为下标形式
- `@uzon_calc()` 函数支持相互嵌套调用，内层函数的内容合并到当前上下文
- 单位计算依赖 pint，量纲不匹配时会抛出错误
