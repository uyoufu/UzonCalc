"""后处理器：将希腊英文替换为数学符号。"""

import re
from .base_post_handler import BasePostHandler


class SwapSymbol(BasePostHandler):
    """后处理器：将未转义的希腊英文替换为数学符号。"""

    priority = 20

    # 希腊字母映射表
    _REPLACEMENTS = {
        "alpha": "α",
        "Alpha": "Α",
        "beta": "β",
        "Beta": "Β",
        "gamma": "γ",
        "Gamma": "Γ",
        "delta": "δ",
        "Delta": "Δ",
        "epsilon": "ε",
        "Epsilon": "Ε",
        "zeta": "ζ",
        "Zeta": "Ζ",
        "eta": "η",
        "Eta": "Η",
        "theta": "θ",
        "Theta": "Θ",
        "iota": "ι",
        "Iota": "Ι",
        "kappa": "κ",
        "Kappa": "Κ",
        "lambda": "λ",
        "Lambda": "Λ",
        "mu": "μ",
        "Mu": "Μ",
        "nu": "ν",
        "Nu": "Ν",
        "xi": "ξ",
        "Xi": "Ξ",
        "omicron": "ο",
        "Omicron": "Ο",
        "pi": "π",
        "Pi": "Π",
        "rho": "ρ",
        "Rho": "Ρ",
        "sigma": "σ",
        "Sigma": "Σ",
        "tau": "τ",
        "Tau": "Τ",
        "upsilon": "υ",
        "Upsilon": "Υ",
        "phi": "φ",
        "Phi": "Φ",
        "chi": "χ",
        "Chi": "Χ",
        "psi": "ψ",
        "Psi": "Ψ",
        "omega": "ω",
        "Omega": "Ω",
    }

    # 匹配希腊字母的正则（按长度降序避免部分匹配）
    _greek_words = sorted(_REPLACEMENTS.keys(), key=len, reverse=True)
    _GREEK_PATTERN = re.compile(
        r"(?<![A-Za-z0-9_\\])"
        r"(\\?)"
        r"(" + "|".join(re.escape(w) for w in _greek_words) + r")"
        r"(?=[_\s\W]|$)"
    )
    _html_tag_pattern = re.compile(r"(<[^>]+>)")
    _tag_name_pattern = re.compile(r"^</?\s*([a-zA-Z][\w:-]*)")
    _skip_text_tags = {"code", "pre", "script", "style"}

    def handle(self, data: str, ctx=None) -> str:
        """转换希腊字母英文名称，并移除转义用反斜杠。"""
        if "<" in data:
            return self._replace_html_text_greek_words(data)

        return self._replace_plain_text_greek_words(data)

    def _replace_html_text_greek_words(self, data: str) -> str:
        """仅转换 HTML 普通文本，跳过代码类标签内容。"""
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

            if skip_stack:
                result.append(part)
            else:
                result.append(self._replace_plain_text_greek_words(part))

        return "".join(result)

    def _track_skip_text_tag(self, tag_text: str, skip_stack: list[str]) -> None:
        """根据当前 HTML 标签维护需要跳过转换的标签栈。"""
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

    def _replace_plain_text_greek_words(self, text: str) -> str:
        """转换普通文本中的希腊字母英文名称。"""
        def replace_greek_word(match: re.Match[str]) -> str:
            escaped_mark = match.group(1)
            greek_word = match.group(2)
            if escaped_mark:
                return greek_word
            return self._REPLACEMENTS[greek_word]

        return self._GREEK_PATTERN.sub(replace_greek_word, text)
