<div align="center">

# UzonCalc

**Write Engineering Calculation Documents in Python — Focus on Calculations, Not Layout**

English · [中文](README.zh-CN.md)

</div>

UzonCalc is a Python-based engineering calculation document tool. You only need to write calculation logic, and UzonCalc automatically substitutes variable values, generates math formulas, lays out tables of contents and tables, and outputs beautiful HTML calculation documents.

---

## ✨ Features

- 🐍 **Pure Python** — No new syntax to learn; everything is function calls
- 🤖 **AI Friendly** — Comes with SKILLs, AI helps you quickly generate calculation drafts
- 📐 **Automatic Formula Rendering** — Variable values are automatically substituted, calculation steps are automatically displayed, with support for Greek letters and subscripts
- 📏 **Unit Calculations** — Based on pint, automatic unit conversion and dimensional checking
- 📊 **Chart Support** — Built-in ECharts interactive charts and Matplotlib static charts
- 📋 **Tables & Excel** — Supports complex tables (merged cells) and calling Excel calculation models
- 📄 **Multi-format Output** — Direct HTML output, printable to PDF via browser, or convertible to Word via pandoc

---

## 📦 Installation

```bash
pip install uzoncalc
```

> UzonCalc requires Python 3.10+.

---

## 🚀 Quick Start

**1. Create a calculation script**

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

**2. Run**

```bash
python example.py
```

This will generate `example.html` in the current directory. Open it in a browser to view the calculation document.

---

## 🖥 Preview

![image-20260329002252229](https://oss.uzoncloud.com:2234/public/files/images/image-20260329002252229.png)

## 📖 More Examples

### Engineering Calculations with Units

```python
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("Cross-Section Stress Calculation")

    H2("Cross-Section Stress Calculation")

    "Section width:"
    b = 300 * unit.millimeter
    alias("b", "Section width b")

    "Section height:"
    h = 500 * unit.millimeter
    alias("h", "Section height h")

    "Axial force:"
    N = 100 * unit.kilonewton
    alias("N", "Axial force N")

    "Section area:"
    A = b * h
    alias("A", "Section area A")

    "Section stress:"
    sigma = N / A
    alias("sigma", "Section stress σ")

    save()
```

UzonCalc will automatically render:

![image-20260329001904932](https://oss.uzoncloud.com:2234/public/files/images/image-20260329001904932.png)

### T-Section Moment of Inertia Calculation

```python
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("T-Section Moment of Inertia Calculation")
    page_size("A4")

    H1("T-Section Moment of Inertia Calculation")

    H2("Basic Section Parameters")

    "Flange width:"
    b_f = 300 * unit.millimeter
    alias("b_f", "Flange width b_f")

    "Flange thickness:"
    h_f = 50 * unit.millimeter
    alias("h_f", "Flange thickness h_f")

    "Web width:"
    b_w = 100 * unit.millimeter
    alias("b_w", "Web width b_w")

    "Web height:"
    h_w = 200 * unit.millimeter
    alias("h_w", "Web height h_w")

    H2("Area Calculation")

    "Flange area:"
    A_f = b_f * h_f

    "Web area:"
    A_w = b_w * h_w

    "Total area:"
    A_total = A_f + A_w

    H2("Moment of Inertia Calculation (Parallel Axis Theorem)")

    "Flange self moment of inertia:"
    I_f_self = b_f * h_f**3 / 12

    "Web self moment of inertia:"
    I_w_self = b_w * h_w**3 / 12

    # ... more calculation logic

    save("../output/T_section.html")
```

> Full source: [T_section_moment_of_inertia.py](examples/T_section_moment_of_inertia.py)

---

## 🌐 Online Demo

| Document | Source | Online Preview |
|----------|--------|----------------|
| Usage Guide | [example.en.py](examples/example.en.py) | [View Document](https://calc.uzoncloud.com/example.en.html) |
| T-Section Moment of Inertia | [T_section_moment_of_inertia.py](examples/T_section_moment_of_inertia.py) | [View Document](https://calc.uzoncloud.com/T_section_moment_of_inertia.html) |

---

## 📄 Output Formats

| Format | Method |
|--------|--------|
| HTML | `save()` generates directly |
| PDF | Print from browser after opening HTML |
| Word | `pandoc input.html -o output.docx` |

---

## 📜 License

[MIT License](LICENSE)