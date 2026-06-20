<div align="center">

# UzonCalc

**面向 AI 的计算报告编写软件 - 企业级品质、原生AI友好、自动计算、自动排版**

[English](README.md) · 中文

</div>

[![UzonCalc](https://oss.uzoncloud.com:2234/public/files/images/image-20260620153738596.png)](https://github.com/user-attachments/assets/04384977-d1c6-4fab-825b-34bcb4b036c2)

UzonCalc 是一款面向 AI 的计算报告编写软件。目标是让 AI 通过 UzonCalc 帮助工程师快速生成和修改计算报告，做到一次编写，一生复用。

使用 UzonCalc，你只需专注计算逻辑，框架将自动代入变量、生成计算过程、渲染数学公式、自动排版，为您输出专业的计算报告文档。

UzonCalc 计算报告采用原生 Python 语法编写，没有任何独有约定，轻松入门，快速上手。

结合 AI，UzonCalc 将助你效率腾飞。

---

## ✨ 特性

- 🤖 **AI 友好** — 自带 SKILL，AI 可以帮你快速生成和修改计算报告
- 🐍 **原生 Python** — 采用原生 Python 语法，轻松入门，快速上手，功能强大，一切皆有可能
- 📐 **公式自动渲染** — 变量自动代入值、计算过程自动展示
- 📌 **自动排版** — 自动根据计算结果排版，无需手动调整
- 📏 **单位计算** — 自动进行单位换算与量纲检查，计算中无需关注单位变化
- 📊 **图表支持** — 可使用 ECharts、svg 和 Matplotlib 绘制各式各样图表
- 📋 **Excel 复用** — 支持自动调用 Excel 进行计算并摘录结果
- 📄 **多格式输出** — 采用标准的 Mathml 格式, 支持转换为 PDF、Word

---

## 📦 安装

```bash
pip install uzoncalc
```

> UzonCalc 需要 Python 3.10+。

---

## 🚀 快速开始

### Windows

1. **软件下载**

   从 [Releases · uyoufu/UzonCalc](https://github.com/uyoufu/UzonCalc/releases) 下载 `win-x64` 版本，解压后，双击 `UzonCalc.exe` 启动。

2. 复制以下代码到新建编辑框内

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

3. 单击执行按钮运行

   ![image-20260527133234259](https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png)

### CLI

若使用 CLI 的方式，可以按下面的步骤操作：

**1. 创建计算报告脚本**

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

**2. 运行**

```bash
python example.py
```

将会出现：`Serving document at: http://127.0.0.1:32180/` 字样，单击通过浏览器打开即可查看效果。

## 🌐 在线示例

| 文档           | 源码                                                                         | 在线预览                                                                |
| -------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 使用说明       | [help.zh.py](examples/zh/help.zh.py)                                         | [查看文档](https://calc.uzoncloud.com/examples/zh/help.zh.html)         |
| T 形截面惯性矩 | [T_section_moment_of_inertia.py](examples/zh/T_section_moment_of_inertia.py) | [查看文档](https://calc.uzoncloud.com/T_section_moment_of_inertia.html) |

---

## 联系方式

李有福：uyoufu@uzoncloud.com

## 更多

[UzonCalc](https://uzoncalc.uzoncloud.com/)

## 📜 许可证

[MIT License](LICENSE)
