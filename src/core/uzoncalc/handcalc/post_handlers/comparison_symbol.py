"""后处理器：将比较运算文本替换为数学比较符号。"""

from __future__ import annotations

from html.parser import HTMLParser

from .base_post_handler import BasePostHandler


class ComparisonSymbol(BasePostHandler):
    """后处理器：将可见文本中的比较运算符替换为数学符号。

    该处理器只转换 HTML 文本节点，跳过标签、属性和代码/LaTeX 内容。
    """

    priority = 20

    _REPLACEMENTS = {
        "&lt;=": "≤",
        "&#60;=": "≤",
        "&#x3c;=": "≤",
        "&#X3C;=": "≤",
        "<=": "≤",
        "&gt;=": "≥",
        "&#62;=": "≥",
        "&#x3e;=": "≥",
        "&#X3E;=": "≥",
        ">=": "≥",
        "!=": "≠",
        "==": "≡",
    }
    _SKIP_TEXT_TAGS = {"code", "pre", "script", "style", "latex"}

    def handle(self, data: str, ctx=None) -> str:
        """转换可见文本中的比较运算符。

        Args:
            data: 已渲染出的 HTML 或普通文本。
            ctx: 当前计算上下文，本处理器不使用。

        Returns:
            转换后的 HTML 或普通文本。
        """
        if not any(source in data for source in self._REPLACEMENTS):
            return data

        parser = _ComparisonSymbolParser(
            replacements=self._REPLACEMENTS,
            skip_text_tags=self._SKIP_TEXT_TAGS,
        )
        parser.feed(data)
        parser.close()
        return parser.render()


class _ComparisonSymbolParser(HTMLParser):
    """流式扫描 HTML，并只替换可见文本中的比较运算符。"""

    def __init__(self, *, replacements: dict[str, str], skip_text_tags: set[str]):
        """初始化比较符号 HTML 扫描器。

        Args:
            replacements: 源文本到目标数学符号的映射。
            skip_text_tags: 内容需要保持原样的标签名集合。
        """
        super().__init__(convert_charrefs=False)
        self._replacements = replacements
        self._skip_text_tags = skip_text_tags
        self._output_parts: list[str] = []
        self._text_parts: list[str] = []
        self._skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """记录开始标签，并在进入标签前转换已累计文本。"""
        self._flush_text_parts()
        self._output_parts.append(
            self.get_starttag_text() or self._render_start_tag(tag, attrs)
        )

        normalized_tag = tag.lower()
        if normalized_tag in self._skip_text_tags:
            self._skip_stack.append(normalized_tag)

    def handle_endtag(self, tag: str) -> None:
        """记录结束标签，并维护跳过转换的标签栈。"""
        self._flush_text_parts()

        normalized_tag = tag.lower()
        if self._skip_stack and self._skip_stack[-1] == normalized_tag:
            self._skip_stack.pop()

        self._output_parts.append(f"</{tag}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """记录自闭合标签。"""
        self._flush_text_parts()
        self._output_parts.append(
            self.get_starttag_text() or self._render_start_tag(tag, attrs, True)
        )

    def handle_data(self, data: str) -> None:
        """累计或原样输出文本。"""
        self._append_text_part(data)

    def handle_entityref(self, name: str) -> None:
        """累计或原样输出命名实体。"""
        self._append_text_part(f"&{name};")

    def handle_charref(self, name: str) -> None:
        """累计或原样输出数字实体。"""
        self._append_text_part(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        """保留 HTML 注释。"""
        self._flush_text_parts()
        self._output_parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        """保留 HTML 声明。"""
        self._flush_text_parts()
        self._output_parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        """保留处理指令。"""
        self._flush_text_parts()
        self._output_parts.append(f"<?{data}>")

    def unknown_decl(self, data: str) -> None:
        """保留未知声明。"""
        self._flush_text_parts()
        self._output_parts.append(f"<![{data}]>")

    def render(self) -> str:
        """返回替换后的完整文本。"""
        self._flush_text_parts()
        return "".join(self._output_parts)

    def _append_text_part(self, text: str) -> None:
        """根据当前跳过状态累计或原样输出文本片段。"""
        if self._skip_stack:
            self._output_parts.append(text)
            return

        self._text_parts.append(text)

    def _flush_text_parts(self) -> None:
        """将累计文本统一替换后写入输出。"""
        if not self._text_parts:
            return

        text = "".join(self._text_parts)
        for source, target in self._replacements.items():
            text = text.replace(source, target)
        self._output_parts.append(text)
        self._text_parts.clear()

    def _render_start_tag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
        is_self_closing: bool = False,
    ) -> str:
        """按解析结果回退渲染开始标签。"""
        attr_text = "".join(
            f" {name}" if value is None else f' {name}="{value}"'
            for name, value in attrs
        )
        suffix = " /" if is_self_closing else ""
        return f"<{tag}{attr_text}{suffix}>"
