import re
from dataclasses import dataclass
from typing import Callable

from lxml import etree

from .base_post_handler import BasePostHandler
from .dom_utils import (
    HtmlPart,
    element_tag_name,
    is_tail_in_tag_context,
    is_text_in_tag_context,
    replace_node_tail_with_parts,
    replace_node_text_with_parts,
    replace_node_with_element,
)


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

    _url_pattern = re.compile(
        r"(?<![\w/])"
        r"((?:https?://|www\.)[^\t\n\r\f\v <>'\"\]]+)"
        r"(?=[\s<>'\"\],.;:!?)]|$)",
        re.IGNORECASE,
    )
    _skip_text_tags = {"code", "pre", "script", "style", "math", "latex"}

    def handle(self, node: etree._Element, ctx=None) -> None:
        """执行上下标后处理，统一修正公式与普通 HTML 文本。"""
        self._render_mathml_mi_node(node)
        self._render_html_text_node(node)

    def _render_mathml_mi_node(self, node: etree._Element) -> None:
        """将 MathML mi 节点中的上下标变量转换为 MathML 脚标结构。"""
        if element_tag_name(node) != "mi" or node.text is None or len(node):
            return
        if "_" not in node.text and "^" not in node.text:
            return

        parsed = self._parse_single_script_notation(node.text)
        if parsed is None:
            return
        if parsed.is_escaped_base:
            node.text = parsed.base + self._plain_script_suffix(parsed)
            return
        replace_node_with_element(node, self._build_mathml_script(node, parsed))

    def _render_html_text_node(self, node: etree._Element) -> None:
        """仅转换 HTML 文本节点，避免误改标签属性。"""
        if node.text and not is_text_in_tag_context(node, self._skip_text_tags):
            replace_node_text_with_parts(
                node, self._render_plain_text_script_parts(node.text)
            )
        if node.tail and not is_tail_in_tag_context(node, self._skip_text_tags):
            replace_node_tail_with_parts(
                node, self._render_plain_text_script_parts(node.tail)
            )

    def _render_plain_text_scripts(self, text: str) -> str:
        """将普通文本中的变量上下标转换为 HTML sub/sup 标签。"""
        if "http://" in text or "https://" in text or "www." in text:
            return self._render_plain_text_without_urls(text)

        return self._render_script_notation(text, self._build_html_script)

    def _render_plain_text_script_parts(self, text: str) -> list[HtmlPart]:
        """将普通文本中的变量上下标转换为 HTML 元素片段。"""
        if "_" not in text and "^" not in text:
            return [text]
        if "http://" in text or "https://" in text or "www." in text:
            return self._render_plain_text_without_url_parts(text)
        return self._render_script_notation_parts(text, self._build_html_script_parts)

    def _render_plain_text_without_url_parts(self, text: str) -> list[HtmlPart]:
        """保护 URL 片段，只转换 URL 之外的普通文本。"""
        result: list[HtmlPart] = []
        last_end = 0
        for match in self._url_pattern.finditer(text):
            start, end = match.span(1)
            result.extend(self._render_plain_text_script_parts(text[last_end:start]))
            result.append(match.group(1))
            last_end = end

        if last_end == 0:
            return self._render_script_notation_parts(
                text, self._build_html_script_parts
            )

        result.extend(self._render_plain_text_script_parts(text[last_end:]))
        return result

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
            candidate_start = self._find_next_script_candidate_start(text, cursor)
            if candidate_start > cursor:
                result.append(text[cursor:candidate_start])
                cursor = candidate_start
                continue

            parsed = self._read_script_notation(text, cursor)
            if parsed is None:
                plain_base_end = self._read_plain_base_without_script_end(text, cursor)
                if plain_base_end > cursor:
                    result.append(text[cursor:plain_base_end])
                    cursor = plain_base_end
                else:
                    result.append(text[cursor])
                    cursor += 1
                continue

            if parsed.is_escaped_base:
                result.append(parsed.base + self._plain_script_suffix(parsed))
            else:
                result.append(render(parsed))
            cursor += len(parsed.original)

        return "".join(result)

    def _render_script_notation_parts(
        self,
        text: str,
        render: Callable[[ScriptParseResult], list[HtmlPart]],
    ) -> list[HtmlPart]:
        """按游标扫描文本，将合法变量上下标块替换为 DOM 片段。"""
        result: list[HtmlPart] = []
        cursor = 0
        while cursor < len(text):
            candidate_start = self._find_next_script_candidate_start(text, cursor)
            if candidate_start > cursor:
                result.append(text[cursor:candidate_start])
                cursor = candidate_start
                continue

            parsed = self._read_script_notation(text, cursor)
            if parsed is None:
                plain_base_end = self._read_plain_base_without_script_end(text, cursor)
                if plain_base_end > cursor:
                    result.append(text[cursor:plain_base_end])
                    cursor = plain_base_end
                else:
                    result.append(text[cursor])
                    cursor += 1
                continue

            if parsed.is_escaped_base:
                result.append(parsed.base + self._plain_script_suffix(parsed))
            else:
                result.extend(render(parsed))
            cursor += len(parsed.original)

        return result

    def _parse_single_script_notation(self, text: str) -> ScriptParseResult | None:
        """解析完整 mi 文本，失败时返回 None 以便保持原样。"""
        parsed = self._read_script_notation(text, 0)
        if parsed is None or len(parsed.original) != len(text):
            return None
        return parsed

    def _find_next_script_candidate_start(self, text: str, cursor: int) -> int:
        """查找下一个可能开始上下标解析的安全变量边界。"""
        while cursor < len(text):
            if self._is_script_candidate_start(text, cursor):
                return cursor
            cursor += 1
        return len(text)

    def _is_script_candidate_start(self, text: str, cursor: int) -> bool:
        """判断当前位置是否可能是上下标变量块起点。"""
        if not self._is_base_boundary_before(text, cursor):
            return False
        if text[cursor] == "\\":
            return cursor + 1 < len(text) and self._is_base_start_char(text[cursor + 1])
        return self._is_base_start_char(text[cursor])

    def _read_plain_base_without_script_end(self, text: str, cursor: int) -> int:
        """读取没有紧随脚标标记的普通变量名结束位置。"""
        base_cursor = cursor
        if text[base_cursor] == "\\":
            base_cursor += 1
            if base_cursor >= len(text):
                return cursor

        base_end = self._read_base_name_end(text, base_cursor)
        if base_end == base_cursor:
            return cursor
        if base_end < len(text) and self._is_script_mark_at(text, base_end):
            return cursor
        return base_end

    def _read_script_notation(self, text: str, start: int) -> ScriptParseResult | None:
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

    def _read_script_operand(self, text: str, cursor: int) -> tuple[str | None, int]:
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

    def _read_grouped_operand(self, text: str, cursor: int) -> tuple[str | None, int]:
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

    def _build_html_script_parts(self, parsed: ScriptParseResult) -> list[HtmlPart]:
        """构造普通 HTML 文本中的 sub/sup DOM 片段。"""
        parts: list[HtmlPart] = [parsed.base]
        for subscript in parsed.subscripts:
            sub_element = etree.Element("sub")
            sub_element.text = subscript
            parts.append(sub_element)
        for superscript in parsed.superscripts:
            sup_element = etree.Element("sup")
            sup_element.text = superscript
            parts.append(sup_element)
        return parts

    def _build_mathml_script(
        self, source_node: etree._Element, parsed: ScriptParseResult
    ) -> etree._Element:
        """构造 MathML 上下标结构。"""
        base_xml = etree.Element("mi", attrib=dict(source_node.attrib))
        base_xml.text = parsed.base
        sub_xml_list = [
            self._create_mtext(subscript) for subscript in parsed.subscripts
        ]
        sup_xml_list = [
            self._create_mtext(superscript) for superscript in parsed.superscripts
        ]

        while len(sub_xml_list) > 1:
            base_xml = self._wrap_mathml_script("msub", base_xml, sub_xml_list.pop(0))
        while len(sup_xml_list) > 1:
            base_xml = self._wrap_mathml_script("msup", base_xml, sup_xml_list.pop(0))

        if sub_xml_list and sup_xml_list:
            return self._wrap_mathml_script(
                "msubsup", base_xml, sub_xml_list[0], sup_xml_list[0]
            )
        if sub_xml_list:
            return self._wrap_mathml_script("msub", base_xml, sub_xml_list[0])
        if sup_xml_list:
            return self._wrap_mathml_script("msup", base_xml, sup_xml_list[0])
        return base_xml

    def _create_mtext(self, text: str, *, style: str | None = None) -> etree._Element:
        """Create an mtext element for a parsed MathML script operand."""
        element = etree.Element("mtext")
        if style is not None:
            element.set("style", style)
        element.text = text
        return element

    def _wrap_mathml_script(
        self,
        tag_name: str,
        *children: etree._Element,
    ) -> etree._Element:
        """Create a MathML script wrapper with the provided child elements."""
        element = etree.Element(tag_name)
        for child in children:
            element.append(child)
        return element

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
        return (
            char.isalpha()
            or "\u0370" <= char <= "\u03ff"
            or "\u4e00" <= char <= "\u9fff"
        )

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
