---
name: post-handler
description: 为 handcalc 创建新的 MathML 后处理器（post_handler）
applyTo: uzoncalc/handcalc/post_handlers/**
---

# Post Handler 技能

该技能描述如何在 `uzoncalc/handcalc/post_handlers/` 目录下创建新的后处理器，以对 handcalc 生成的 MathML 字符串做后期变换。

# 架构说明

后处理器管道（pipeline）工作流程：

```
handcalc 输出 MathML 字符串
    → 按 priority 升序依次执行各 PostHandler.handle()
    → 最终输出处理后的 MathML 字符串
```

已有处理器及其优先级（越小越先执行）：

| 优先级 | 类名                  | 作用                                  |
| ------ | --------------------- | ------------------------------------- |
| 10     | `SwapAlias`           | 按 `ctx.options.aliases` 做字符串替换 |
| 20     | `SwapSymbol`          | 将希腊英文名替换为对应数学符号        |
| 30     | `Subscripting`        | 将 `a_b` 渲染为 MathML 下标           |
| 40     | `ParenthesesSimplify` | 去掉 `<mn>` 中多余的括号              |
| 100    | （默认值）            | 无特殊声明时的执行顺序                |

# 实现步骤

## 1. 新建处理器文件

在 `uzoncalc/handcalc/post_handlers/` 下新建 `<handler_name>.py`：

**不需要访问 ctx（上下文）的处理器：**

```python
import re
from .base_post_handler import BasePostHandler


class MyHandler(BasePostHandler):
    """后处理器：（功能描述）"""

    priority = 50  # 根据处理顺序选择合适的优先级

    def handle(self, data: str, ctx=None) -> str:
        # 对 MathML 字符串 data 进行变换
        return data
```

**需要访问 ctx（ContextOptions 等）的处理器：**

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from .base_post_handler import BasePostHandler

if TYPE_CHECKING:
    from ...context import CalcContext


class MyHandler(BasePostHandler):
    """后处理器：（功能描述）"""

    priority = 50

    def handle(self, data: str, ctx: Optional[CalcContext] = None) -> str:
        if ctx is None:
            return data

        # 通过 ctx.options 访问用户配置
        # 例如：ctx.options.aliases、ctx.options.xxx
        return data
```

## 2. 设置优先级

根据处理器的职责和依赖关系选择 `priority`：

- **< 20**：全局字符串替换，应在其他处理前执行（如 SwapAlias、SwapSymbol）
- **20–40**：MathML 结构变换（如下标渲染、括号简化）
- **> 50**：在主要变换完成后执行的收尾处理（如格式化、URL 处理）

如果两个处理器的 `priority` 相同，则按类名字母顺序执行（稳定排序）。

## 3. 注册到管道

编辑 `post_pipeline.py`，执行两步操作：

**① 添加 import：**

```python
from .my_handler import MyHandler  # 按字母顺序排列 import
```

**② 将实例加入 handlers 列表：**

```python
def get_default_post_handlers() -> List[BasePostHandler]:
    handlers: List[BasePostHandler] = [
        ParenthesesSimplify(),
        SwapSymbol(),
        SwapAlias(),
        Subscripting(),
        MyHandler(),  # 添加此行
    ]
    handlers.sort(key=lambda h: (getattr(h, "priority", 100), h.__class__.__name__))
    return handlers
```

> 列表中的顺序不影响实际执行顺序，执行顺序由 `priority` 决定。

# 注意事项

1. **只处理 MathML 标签内的内容**：若需要修改 MathML 元素（如 `<mi>`、`<mn>`、`<mo>`），使用正则匹配对应标签，避免误改普通文本（如 `<p>` 中的说明文字）。

2. **保护引号内容**：若处理器会替换字符串，参考 `SwapSymbol` 的占位符方法，先保护引号中的文字再替换。

3. **快速返回**：在方法开头检查是否需要处理，若不需要直接返回原 `data`，例如：

   ```python
   if "<mi" not in data or "_" not in data:
       return data
   ```

4. **ctx 的使用**：若处理器不依赖上下文，保持 `ctx=None` 签名即可，无需导入 `CalcContext`。

# 示例：完整的简单处理器

以下示例将 MathML 中 `<mo>` 标签内的 `**` 替换为 `^`：

```python
import re
from .base_post_handler import BasePostHandler


class PowerOperator(BasePostHandler):
    """后处理器：将 <mo>**</mo> 替换为 <mo>^</mo>"""

    priority = 45

    _pattern = re.compile(r"<mo([^>]*)>\*\*</mo>")

    def handle(self, data: str, ctx=None) -> str:
        if "**" not in data:
            return data
        return self._pattern.sub(r"<mo\1>^</mo>", data)
```
