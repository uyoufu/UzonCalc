import re

from .base_post_handler import BasePostHandler


class Subscripting(BasePostHandler):
    """后处理器：将形如 a_b 的变量名渲染为下标。

    处理 MathML 中的 <mi>name</mi> 形式：
    - a_b -> <msub><mi>a</mi><mi>b</mi></msub>
    - x_1 -> <msub><mi>x</mi><mn>1</mn></msub>
    - x_1_2 -> 嵌套 <msub>( (x_1)_2 )
    - a_b.c -> <mrow><msub><mi>a</mi><mi>b</mi></msub><mo>.</mo><mi>c</mi></mrow>
    - a_b(c) -> 函数调用，保持原样

    同时处理普通 HTML 文本节点：
    - E_j -> E<sub>j</sub>
    - gamma_混凝土 -> gamma<sub>混凝土</sub>

    规则（尽量保守）：
    - 以 '_' 开头/结尾的不处理（如 _tmp / tmp_）
    - 含连续 '_' 的不处理（如 concrete__code）
    """

    priority = 30

    _mi_pattern = re.compile(r"<mi([^>]*)>([^<]+)</mi>")
    _html_tag_pattern = re.compile(r"(<[^>]+>)")
    _tag_name_pattern = re.compile(r"^</?\s*([a-zA-Z][\w:-]*)")
    _text_name_pattern = re.compile(
        r"(?<![\w./:-])"
        r"([A-Za-z\u0370-\u03FF\u4e00-\u9fff]+"
        r"(?:_[A-Za-z0-9\u0370-\u03FF\u4e00-\u9fff]+)+)"
        r"(?![\w/-])"
    )
    _url_pattern = re.compile(
        r"(?<![\w/])"
        r"((?:https?://|www\.)[^\t\n\r\f\v <>'\"\]]+)"
        r"(?=[\s<>'\"\],.;:!?)]|$)",
        re.IGNORECASE,
    )
    _skip_text_tags = {"code", "pre", "script", "style", "math"}

    def handle(self, data: str, ctx=None) -> str:
        """执行下标后处理，统一修正公式与普通 HTML 文本。"""
        if "_" not in data:
            return data

        data = self._render_mathml_mi_subscripts(data)
        return self._render_html_text_subscripts(data)

    def _render_mathml_mi_subscripts(self, data: str) -> str:
        """将 MathML mi 标签中的下划线变量转换为 msub。"""
        if "<mi" not in data:
            return data

        def _repl(m: re.Match[str]) -> str:
            attrs = m.group(1)
            name = m.group(2)
            if "_" not in name:
                return m.group(0)
            if name.startswith("_") or name.endswith("_"):
                return m.group(0)

            parts = name.split("_")
            if len(parts) < 2:
                return m.group(0)
            if any(p == "" for p in parts):
                return m.group(0)

            base_xml = f"<mi{attrs}>{parts[0]}</mi>"
            for sub in parts[1:]:
                sub_xml = f"<mtext>{sub}</mtext>"
                base_xml = f"<msub>{base_xml}{sub_xml}</msub>"

            return base_xml

        return self._mi_pattern.sub(_repl, data)

    def _render_html_text_subscripts(self, data: str) -> str:
        """仅转换 HTML 文本节点，避免误改标签属性。"""
        if "<" not in data:
            return self._render_plain_text_subscripts(data)

        parts = self._html_tag_pattern.split(data)
        result: list[str] = []
        skip_stack: list[str] = []

        for part in parts:
            if not part:
                continue
            if part.startswith("<") and part.endswith(">"):
                self._track_skip_text_tag(part, skip_stack)
                result.append(part)
                continue

            # 跳过代码、脚本、样式和 MathML 区域，避免重复或误转换。
            if skip_stack:
                result.append(part)
            else:
                result.append(self._render_plain_text_subscripts(part))

        return "".join(result)

    def _track_skip_text_tag(self, tag_text: str, skip_stack: list[str]) -> None:
        """根据当前 HTML 标签维护需要跳过文本转换的标签栈。"""
        tag_match = self._tag_name_pattern.match(tag_text)
        if not tag_match:
            return

        tag_name = tag_match.group(1).lower()
        if tag_name not in self._skip_text_tags:
            return

        is_closing_tag = tag_text.startswith("</")
        is_self_closing_tag = tag_text.endswith("/>")
        if is_closing_tag:
            if skip_stack and skip_stack[-1] == tag_name:
                skip_stack.pop()
            return
        if not is_self_closing_tag:
            skip_stack.append(tag_name)

    def _render_plain_text_subscripts(self, text: str) -> str:
        """将普通文本中的下划线变量转换为 HTML sub 标签。"""
        if "http://" in text or "https://" in text or "www." in text:
            return self._render_plain_text_without_urls(text)

        def _repl(match: re.Match[str]) -> str:
            name = match.group(1)
            if name.startswith("_") or name.endswith("_") or "__" in name:
                return name

            parts = name.split("_")
            if len(parts) < 2 or any(part == "" for part in parts):
                return name

            base_text = parts[0]
            for sub_text in parts[1:]:
                base_text = f"{base_text}<sub>{sub_text}</sub>"
            return base_text

        return self._text_name_pattern.sub(_repl, text)

    def _render_plain_text_without_urls(self, text: str) -> str:
        """保护 URL 片段，只转换 URL 之外的普通文本。"""
        result: list[str] = []
        last_end = 0
        for match in self._url_pattern.finditer(text):
            start, end = match.span(1)
            result.append(self._render_plain_text_subscripts(text[last_end:start]))
            result.append(match.group(1))
            last_end = end

        if last_end == 0:
            return self._text_name_pattern.sub(
                lambda match: self._render_plain_text_subscripts(match.group(1)),
                text,
            )

        result.append(self._render_plain_text_subscripts(text[last_end:]))
        return "".join(result)
