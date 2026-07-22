---
title: 开始使用
icon: lightbulb
order: 1
---

## 简介

UzonCalc 是一款面向 AI 的计算报告编写软件。目标是让 AI 通过 UzonCalc 帮助工程师快速生成和修改计算报告，做到一次编写，一生复用。

使用 UzonCalc，你只需专注计算逻辑，框架将自动代入变量、生成计算过程、渲染数学公式、自动排版，为您输出专业的计算报告文档。

UzonCalc 计算报告采用原生 Python 语法编写，没有任何独有约定，轻松入门，快速上手。

结合 AI，UzonCalc 将助你效率腾飞。

## 选择使用方式

UzonCalc 目前主要有两种使用方式：

- Windows 桌面端：适合普通使用者管理计算书、填写 UI 输入并运行报告。
- CLI：适合计算书编写者搭配 VSCode、AI 工具和代码格式化能力进行持续编写。

如果你正在编写计算书，建议优先使用 CLI。CLI 环境更适合自动格式化、语法检查、版本管理和 AI 辅助修改。

## Windows 桌面端

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

## CLI

CLI 方式主要面向计算书编写者。它可以搭配编辑器、AI 和代码格式化工具使用，让计算书像普通 Python 项目一样维护。

### 1. 安装 Python

请先安装 Python 3.11 或更高版本，并确认命令行中可以执行：

```bash
python --version
```

### 2. 安装 UzonCalc

可以使用 `pip` 或 `uv` 安装：

```bash
pip install uzoncalc
```

或：

```bash
uv add uzoncalc
```

### 3. 创建计算报告脚本

新建 `example.py`：

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

### 4. 运行

普通 Python 方式：

```bash
python --serve example.py
```

将会出现：`Serving document at: http://127.0.0.1:32180/` 字样，单击通过浏览器打开即可查看效果。

也可以使用 UzonCalc CLI：

```bash
uzoncalc example.py
```

使用 `python --serve example.py` 时，需要在代码最后调用 `view(sheet)`；使用 `uzoncalc example.py` 时，CLI 会负责启动服务。开发计算书时推荐使用 CLI，它更适合热重载和持续编辑。

## 第一个报告的结构

一个最小计算书通常包含以下部分：

```python
from uzoncalc import *


@uzon_calc()
async def sheet():
    doc_title("example")

    "Hello, UzonCalc!"

    width = 10 * unit.m
    length = 5 * unit.m
    area = width * length
```

- `from uzoncalc import *` 导入常用文档函数、单位和计算能力。
- `@uzon_calc()` 将 `sheet` 标记为计算书入口。
- 字符串会被输出为正文段落。
- 赋值语句会被记录为公式，并渲染变量代入和计算结果。

## 服务器部署

UzonCalc 后续会提供服务器端部署教程。当前建议优先使用 Windows 桌面端或 CLI。

## Docker 方式

Docker 部署教程后续提供。
