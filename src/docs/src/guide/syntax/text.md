---
title: 文本与标题
icon: circle-info
order: 1
---

## 普通文本

在 UzonCalc 中，单引号、双引号或三引号包裹的字符串会作为正文段落输出：

```python
'单引号文本'

"双引号文本"

"""
三引号文本,
这是第 1 行,
这是第 2 行
"""
```

单引号和双引号适合单行文本；三引号适合较长段落。三引号中的换行会被合并为一个段落，不会按源代码中的每一行强制换行。

::: info
所有正文都需要用引号包裹，这是 Python 语法要求，也是 UzonCalc 记录文档内容的方式。
:::

## 换行

需要主动增加空行时，可以使用 `Br()`：

```python
"第一段"
Br()
"第二段"
```

## 标题

UzonCalc 内置 `Title()` 和 `H1()` 到 `H6()` 标题函数：

```python
Title("UzonCalc 使用说明")

H2("安装使用")
H3("CLI 安装")
```

通常建议：

- `Title()` 用于封面或文档主标题。
- `H2()` 用于章节标题。
- `H3()` 用于小节标题。
- 更低级标题只在层级确实复杂时使用。

标题会参与目录生成，也会影响章节层级。

## Markdown

复杂文本可以使用 `Markdown()` 输出，例如列表、链接、强调文本：

```python
Markdown("""
- **AI 友好**：计算过程就是 Python 代码
- **自动排版**：章节号、图号自动生成
- **多格式输出**：支持转换为 PDF、Word 等文档
""")
```

## 代码块

使用 `Code()` 输出代码块：

```python
Code(
    """
from uzoncalc import *

@uzon_calc()
async def sheet():
    doc_title("example")
    "Hello, UzonCalc!"
""",
    "python",
)
```

第二个参数用于指定代码语言，便于文档站或浏览器进行语法高亮。
