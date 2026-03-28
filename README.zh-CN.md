<div align="center">

# UzonCalc

**用 Python 写工程计算书 — 专注计算，告别排版**

[English](README.md) · 中文

</div>

UzonCalc 是一个基于 Python 的工程计算书工具。你只需编写计算逻辑，UzonCalc 自动代入变量值、生成数学公式、排版目录与表格，输出精美的 HTML 计算书文档。

---

## ✨ 特性

- 🐍 **纯 Python 编写** — 无需学习新语法，所有操作都是函数调用
- 🤖 **AI 友好** — 自带 SKILL，AI 帮你快速生成计算书初稿
- 📐 **自动公式渲染** — 变量自动代入值、计算过程自动展示，支持希腊字母与下标
- 📏 **单位计算** — 基于 pint，自动进行单位换算与量纲检查
- 📊 **图表支持** — 内置 ECharts 交互式图表和 Matplotlib 静态图表
- 📋 **表格 & Excel** — 支持复杂表格（合并单元格）及调用 Excel 计算模型
- 📄 **多格式输出** — 直接输出 HTML，可通过浏览器打印为 PDF，或通过 pandoc 转换为 Word

---

## 📦 安装

```bash
pip install uzoncalc
```

> UzonCalc 需要 Python 3.10+。

---

## 🚀 快速开始

**1. 创建计算书脚本**

```python
# example.py
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("uzoncalc example")

    "Hello, UzonCalc!"

    save()


if __name__ == "__main__":
    run_sync(sheet)
```

**2. 运行**

```bash
python example.py
```

将在当前目录生成 `example.html`，用浏览器打开即可查看计算书。

---

## 📖 更多示例

### 带单位的工程计算

```python
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("单位计算示例")

    H2("截面应力计算")

    "截面宽度："
    b = 300 * unit.millimeter
    alias("b", "截面宽度 b")

    "截面高度："
    h = 500 * unit.millimeter
    alias("h", "截面高度 h")

    "轴向力："
    N = 100 * unit.kilonewton
    alias("N", "轴向力 N")

    "截面面积："
    A = b * h
    alias("A", "截面面积 A")

    "截面应力："
    sigma = N / A
    alias("sigma", "截面应力 σ")

    save()
```

UzonCalc 会自动渲染为：

> *截面面积* A = *b* × *h* = 300 mm × 500 mm = 150000 mm²
>
> *截面应力* σ = *N* / *A* = 100 kN / 150000 mm² = 0.667 MPa

### T 形截面惯性矩计算

```python
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("T 形截面惯性矩计算")
    page_size("A4")

    H1("T 形截面惯性矩计算")

    H2("截面基本参数")

    "翼缘宽度："
    b_f = 300 * unit.millimeter
    alias("b_f", "翼缘宽度 b_f")

    "翼缘厚度："
    h_f = 50 * unit.millimeter
    alias("h_f", "翼缘厚度 h_f")

    "腹板宽度："
    b_w = 100 * unit.millimeter
    alias("b_w", "腹板宽度 b_w")

    "腹板高度："
    h_w = 200 * unit.millimeter
    alias("h_w", "腹板高度 h_w")

    H2("面积计算")

    "翼缘面积："
    A_f = b_f * h_f

    "腹板面积："
    A_w = b_w * h_w

    "总面积："
    A_total = A_f + A_w

    H2("惯性矩计算（平行轴定理）")

    "翼缘自身惯性矩："
    I_f_self = b_f * h_f**3 / 12

    "腹板自身惯性矩："
    I_w_self = b_w * h_w**3 / 12

    # ... 更多计算逻辑

    save("../output/T_section.html")
```

> 完整源码：[T_section_moment_of_inertia.py](examples/T_section_moment_of_inertia.py)

---

## 🖥 效果预览

![image-20260110162359040](https://oss.uzoncloud.com:2234/public/files/images/image-20260110162359040.png)

---

## 🌐 在线 Demo

| 文档 | 源码 | 在线预览 |
|------|------|----------|
| 使用说明 | [example.zh.py](examples/example.zh.py) | [查看文档](https://calc.uzoncloud.com/example.zh.html) |
| T 形截面惯性矩 | [T_section_moment_of_inertia.py](examples/T_section_moment_of_inertia.py) | [查看文档](https://calc.uzoncloud.com/T_section_moment_of_inertia.html) |

---

## 📄 输出格式

| 格式 | 方式 |
|------|------|
| HTML | `save()` 直接生成 |
| PDF | 浏览器打开 HTML 后打印 |
| Word | `pandoc input.html -o output.docx` |

---

## 📜 许可证

[MIT License](LICENSE)
