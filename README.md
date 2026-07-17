<div align="center">

# UzonCalc

**AI-oriented calculation report authoring software - enterprise quality, AI-native, automatic calculation, automatic layout**

English · [中文](README.zh-CN.md)

</div>

[![UzonCalc](https://oss.uzoncloud.com:2234/public/files/images/image-20260620153738596.png)](https://github.com/user-attachments/assets/04384977-d1c6-4fab-825b-34bcb4b036c2)

UzonCalc is AI-oriented calculation report authoring software. Its goal is to let AI help engineers quickly generate and modify calculation reports through UzonCalc, so one report can be written once and reused for life.

With UzonCalc, you only need to focus on the calculation logic. The framework automatically substitutes variables, generates calculation steps, renders mathematical formulas, and lays out the document to produce professional calculation reports.

UzonCalc calculation reports are written in native Python syntax without any proprietary conventions, so they are easy to learn and quick to use.

Combined with AI, UzonCalc helps you work much more efficiently.

---

## ✨ Features

- 🤖 **AI-friendly** — Comes with a SKILL so AI can help you quickly generate and modify calculation reports
- 🐍 **Native Python** — Uses native Python syntax, easy to learn, quick to use, powerful, and flexible
- 📐 **Automatic formula rendering** — Variables are automatically substituted with values, and calculation steps are displayed automatically
- 📌 **Automatic layout** — Automatically lays out content according to calculation results, with no manual adjustment required
- 📏 **Unit calculation** — Automatically performs unit conversion and dimensional checks, so you do not need to worry about units during calculation
- 📊 **Chart support** — Draw many kinds of charts with ECharts, SVG, and Matplotlib
- 📋 **Excel reuse** — Automatically call Excel for calculation and extract results
- 📄 **Multiple output formats** — Uses standard MathML and supports conversion to PDF and Word

---

## 📦 Installation

```bash
pip install uzoncalc
```

> UzonCalc requires Python 3.13+.

---

## 🚀 Quick Start

### Windows

1. **Download the software**

   Download the `win-x64` version from [Releases · uyoufu/UzonCalc](https://github.com/uyoufu/UzonCalc/releases), extract it, and double-click `UzonCalc.exe` to start.

2. Copy the following code into the new editor box

   ```python
   from uzoncalc import *

   @uzon_calc()
   async def sheet():
       doc_title("example")

       "Hello, UzonCalc!"

       w = 10*unit.m
       l = 5*unit.m
       A = w * l
   ```

3. Click the run button

   ![image-20260527133234259](https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png)

### CLI

If you use the CLI, follow these steps:

**1. Create a calculation report script**

```python
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
```

**2. Run**

```bash
python example.py
```

You will see `Serving document at: http://127.0.0.1:32180/`. Click it or open it in a browser to view the result.

**3. Package as a `.uzc` archive**

```bash
uzoncalc zip -p example.py
python example.uzc
```

The zip command validates that the script contains an `@uzon_calc` entry. If the script does not define an `if __name__ == "__main__"` block, the archive automatically calls `view()` for the single calculation entry.

## 🌐 Online Examples

| Document                  | Source                                                                       | Online Preview                                                         |
| ------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| User Guide                | [help.en.py](examples/en/help.en.py)                                         | [View Document](https://calc.uzoncloud.com/examples/en/help.en.html)   |
| T-section Moment of Inertia | [T_section_moment_of_inertia.py](examples/zh/T_section_moment_of_inertia.py) | [View Document](https://calc.uzoncloud.com/T_section_moment_of_inertia.html) |

---

## Contact

Li Youfu: uyoufu@uzoncloud.com

## More

[UzonCalc](https://uzoncalc.uzoncloud.com/)

## 📜 License

[MIT License](LICENSE)
