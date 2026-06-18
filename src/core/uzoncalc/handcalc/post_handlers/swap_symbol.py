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

    def handle(self, data: str, ctx=None) -> str:
        """转换希腊字母英文名称，并移除转义用反斜杠。"""

        def replace_greek_word(match: re.Match[str]) -> str:
            escaped_mark = match.group(1)
            greek_word = match.group(2)
            if escaped_mark:
                return greek_word
            return self._REPLACEMENTS[greek_word]

        return self._GREEK_PATTERN.sub(replace_greek_word, data)
