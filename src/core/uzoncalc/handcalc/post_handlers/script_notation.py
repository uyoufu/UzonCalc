import re
from dataclasses import dataclass
from typing import Callable

from .base_post_handler import BasePostHandler


@dataclass(frozen=True)
class ScriptParseResult:
    """变量上下标解析结果，包含原始块边界和解析后的脚标。"""

    original: str
    base: str
    subscripts: list[str]
    superscripts: list[str]
    is_escaped_base: bool


class ScriptNotation(BasePostHandler):
    """后处理器：将约定形式的变量名渲染为上下标。

    处理 MathML 中的 <mi>name</mi> 形式：
    - a_b -> <msub><mi>a</mi><mtext>b</mtext></msub>
    - x^2 -> <msup><mi>x</mi><mtext>2</mtext></msup>
    - x_i^2 -> <msubsup><mi>x</mi><mtext>i</mtext><mtext>2</mtext></msubsup>

    同时处理普通 HTML 文本节点：
    - E_j -> E<sub>j</sub>
    - x^{n+1} -> x<sup>n+1</sup>

    规则（尽量保守）：
    - 使用游标扫描和花括号深度计数解析分组，不支持完整 LaTeX 语法
    - 被反斜杠转义的变量块只移除转义反斜杠，不生成上下标
    - 空分组、未闭合分组和连续脚标符号保持原样
    """

    priority = 30

    _mi_pattern = re.compile(r"<mi([^>]*)>([^<]+)</mi>")
    _html_tag_pattern = re.compile(r"(<[^>]+>)")
    _tag_name_pattern = re.compile(r"^</?\s*([a-zA-Z][\w:-]*)")
    _url_pattern = re.compile(
        r"(?<![\w/])"
        r"((?:https?://|www\.)[^\t\n\r\f\v <>'\"\]]+)"
        r"(?=[\s<>'\"\],.;:!?)]|$)",
        re.IGNORECASE,
    )
    _skip_text_tags = {"code", "pre", "script", "style", "math", "latex"}

    def handle(self, data: str, ctx=None) -> str:
        """执行上下标后处理，统一修正公式与普通 HTML 文本。"""
        if "_" not in data and "^" not in data:
            return data

        data = self._render_mathml_mi_scripts(data)
        return self._render_html_text_scripts(data)

    def _render_mathml_mi_scripts(self, data: str) -> str:
        """将 MathML mi 标签中的上下标变量转换为 MathML 脚标结构。"""
        if "<mi" not in data:
            return data

        def _repl(m: re.Match[str]) -> str:
            attrs = m.group(1)
            name = m.group(2)
            if "_" not in name and "^" not in name:
                return m.group(0)

            parsed = self._parse_single_script_notation(name)
            if parsed is None:
                return m.group(0)
            if parsed.is_escaped_base:
                return f"<mi{attrs}>{parsed.base}{self._plain_script_suffix(parsed)}</mi>"
            return self._build_mathml_script(attrs, parsed)

        return self._mi_pattern.sub(_repl, data)

    def _render_html_text_scripts(self, data: str) -> str:
        """仅转换 HTML 文本节点，避免误改标签属性。"""
        if "<" not in data:
            return self._render_plain_text_scripts(data)

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
                result.append(self._render_plain_text_scripts(part))

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

    def _render_plain_text_scripts(self, text: str) -> str:
        """将普通文本中的变量上下标转换为 HTML sub/sup 标签。"""
        if "http://" in text or "https://" in text or "www." in text:
            return self._render_plain_text_without_urls(text)

        return self._render_script_notation(text, self._build_html_script)

    def _render_plain_text_without_urls(self, text: str) -> str:
        """保护 URL 片段，只转换 URL 之外的普通文本。"""
        result: list[str] = []
        last_end = 0
        for match in self._url_pattern.finditer(text):
            start, end = match.span(1)
            result.append(self._render_plain_text_scripts(text[last_end:start]))
            result.append(match.group(1))
            last_end = end

        if last_end == 0:
            return self._render_script_notation(text, self._build_html_script)

        result.append(self._render_plain_text_scripts(text[last_end:]))
        return "".join(result)

    def _render_script_notation(
        self,
        text: str,
        render: Callable[[ScriptParseResult], str],
    ) -> str:
        """按游标扫描文本，将合法变量上下标块替换为目标格式。"""
        result: list[str] = []
        cursor = 0
        while cursor < len(text):
            parsed = self._read_script_notation(text, cursor)
            if parsed is None:
                result.append(text[cursor])
                cursor += 1
                continue

            if parsed.is_escaped_base:
                result.append(parsed.base + self._plain_script_suffix(parsed))
            else:
                result.append(render(parsed))
            cursor += len(parsed.original)

        return "".join(result)

    def _parse_single_script_notation(self, text: str) -> ScriptParseResult | None:
        """解析完整 mi 文本，失败时返回 None 以便保持原样。"""
        parsed = self._read_script_notation(text, 0)
        if parsed is None or len(parsed.original) != len(text):
            return None
        return parsed

    def _read_script_notation(
        self, text: str, start: int
    ) -> ScriptParseResult | None:
        """从指定游标读取一个变量上下标块。"""
        if not self._is_base_boundary_before(text, start):
            return None

        cursor = start
        is_escaped_base = False
        if text[cursor] == "\\":
            is_escaped_base = True
            cursor += 1
            if cursor >= len(text):
                return None

        base_end = self._read_base_name_end(text, cursor)
        if base_end == cursor:
            return None

        base = text[cursor:base_end]
        cursor = base_end
        subscripts: list[str] = []
        superscripts: list[str] = []

        while cursor < len(text) and self._is_script_mark_at(text, cursor):
            is_escaped_mark = text[cursor] == "\\"
            script_mark = text[cursor + 1] if is_escaped_mark else text[cursor]
            mark_end = cursor + 2 if is_escaped_mark else cursor + 1
            if is_escaped_mark or self._is_escaped_char(text, cursor):
                if not subscripts and not superscripts:
                    operand, next_cursor = self._read_script_operand(text, mark_end)
                    if operand is None:
                        operand = ""
                        next_cursor = mark_end
                    plain_suffix = script_mark + operand
                    return ScriptParseResult(
                        original=text[start:next_cursor],
                        base=base + plain_suffix,
                        subscripts=[],
                        superscripts=[],
                        is_escaped_base=True,
                    )
                break

            operand, next_cursor = self._read_script_operand(text, mark_end)
            if operand is None:
                return None
            if script_mark == "_":
                subscripts.append(operand)
            else:
                superscripts.append(operand)
            cursor = next_cursor

        if not subscripts and not superscripts:
            return None

        if not self._is_boundary_after(text, cursor):
            return None

        return ScriptParseResult(
            original=text[start:cursor],
            base=base,
            subscripts=subscripts,
            superscripts=superscripts,
            is_escaped_base=is_escaped_base,
        )

    def _read_base_name_end(self, text: str, cursor: int) -> int:
        """读取变量底数名称结束位置。"""
        if cursor >= len(text) or not self._is_base_start_char(text[cursor]):
            return cursor

        cursor += 1
        while cursor < len(text) and self._is_base_part_char(text[cursor]):
            cursor += 1
        return cursor

    def _read_script_operand(
        self, text: str, cursor: int
    ) -> tuple[str | None, int]:
        """读取 _/^ 后的操作数，支持单 token 和花括号分组。"""
        if cursor >= len(text):
            return None, cursor

        if text[cursor] == "{":
            return self._read_grouped_operand(text, cursor)

        if text[cursor] in {"_", "^"}:
            return None, cursor

        operand_start = cursor
        while cursor < len(text) and self._is_operand_char(text[cursor]):
            cursor += 1

        if cursor == operand_start:
            return None, operand_start
        return text[operand_start:cursor], cursor

    def _read_grouped_operand(
        self, text: str, cursor: int
    ) -> tuple[str | None, int]:
        """用深度计数器读取花括号分组操作数。"""
        group_start = cursor + 1
        cursor += 1
        depth = 1
        while cursor < len(text):
            char = text[cursor]
            if char == "\\" and cursor + 1 < len(text):
                cursor += 2
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    operand = text[group_start:cursor]
                    if operand == "":
                        return None, group_start - 1
                    return operand, cursor + 1
            cursor += 1

        return None, group_start - 1

    def _build_html_script(self, parsed: ScriptParseResult) -> str:
        """构造普通 HTML 文本中的 sub/sup 标签输出。"""
        rendered = parsed.base
        for subscript in parsed.subscripts:
            rendered += f"<sub>{subscript}</sub>"
        for superscript in parsed.superscripts:
            rendered += f"<sup>{superscript}</sup>"
        return rendered

    def _build_mathml_script(self, attrs: str, parsed: ScriptParseResult) -> str:
        """构造 MathML 上下标结构。"""
        base_xml = f"<mi{attrs}>{parsed.base}</mi>"
        sub_xml_list = [f"<mtext>{subscript}</mtext>" for subscript in parsed.subscripts]
        sup_xml_list = [
            f"<mtext>{superscript}</mtext>" for superscript in parsed.superscripts
        ]

        while len(sub_xml_list) > 1:
            base_xml = f"<msub>{base_xml}{sub_xml_list.pop(0)}</msub>"
        while len(sup_xml_list) > 1:
            base_xml = f"<msup>{base_xml}{sup_xml_list.pop(0)}</msup>"

        if sub_xml_list and sup_xml_list:
            return f"<msubsup>{base_xml}{sub_xml_list[0]}{sup_xml_list[0]}</msubsup>"
        if sub_xml_list:
            return f"<msub>{base_xml}{sub_xml_list[0]}</msub>"
        if sup_xml_list:
            return f"<msup>{base_xml}{sup_xml_list[0]}</msup>"
        return base_xml

    def _plain_script_suffix(self, parsed: ScriptParseResult) -> str:
        """把解析结果还原为无转义、无标签的脚标文本。"""
        suffix = ""
        for subscript in parsed.subscripts:
            suffix += f"_{subscript}"
        for superscript in parsed.superscripts:
            suffix += f"^{superscript}"
        return suffix

    def _is_base_boundary_before(self, text: str, start: int) -> bool:
        """判断变量底数前是否是安全边界。"""
        if start == 0:
            return True
        if text[start] == "\\":
            return start == 0 or not self._is_name_like_char(text[start - 1])
        previous = text[start - 1]
        return not self._is_name_like_char(previous) and previous not in {"/", ".", "-"}

    def _is_boundary_after(self, text: str, cursor: int) -> bool:
        """判断上下标块后是否是安全边界。"""
        if cursor >= len(text):
            return True
        return text[cursor] not in {"/", "-"} and not self._is_name_like_char(
            text[cursor]
        )

    def _is_escaped_char(self, text: str, cursor: int) -> bool:
        """判断当前字符是否被奇数个连续反斜杠转义。"""
        slash_count = 0
        check_cursor = cursor - 1
        while check_cursor >= 0 and text[check_cursor] == "\\":
            slash_count += 1
            check_cursor -= 1
        return slash_count % 2 == 1

    def _is_base_start_char(self, char: str) -> bool:
        """判断字符是否可作为变量底数开头。"""
        return char.isalpha() or "\u0370" <= char <= "\u03ff" or "\u4e00" <= char <= "\u9fff"

    def _is_base_part_char(self, char: str) -> bool:
        """判断字符是否可作为变量底数的非首字符。"""
        return self._is_base_start_char(char) or char.isdigit()

    def _is_operand_char(self, char: str) -> bool:
        """判断字符是否可作为未分组脚标操作数。"""
        return self._is_base_part_char(char) or char == "'"

    def _is_name_like_char(self, char: str) -> bool:
        """判断字符是否属于变量或路径片段，避免二次匹配。"""
        return self._is_base_part_char(char) or char in {"_", "^", "\\", ":"}

    def _is_script_mark_at(self, text: str, cursor: int) -> bool:
        """判断当前位置是否是脚标标记或被转义的脚标标记。"""
        if text[cursor] in {"_", "^"}:
            return True
        return (
            text[cursor] == "\\"
            and cursor + 1 < len(text)
            and text[cursor + 1] in {"_", "^"}
        )
