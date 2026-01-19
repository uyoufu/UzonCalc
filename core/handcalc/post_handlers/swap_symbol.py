"""后处理器：将希腊英文替换为数学符号"""

import re
from .base_post_handler import BasePostHandler


class SwapSymbol(BasePostHandler):
    """后处理器：将希腊英文替换为数学符号，跳过引号内的内容"""

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

    # 匹配引号内容的正则（包括HTML实体编码的引号）
    _QUOTE_PATTERN = re.compile(
        r"'[^']*'|"  # 单引号
        r'"[^"]*"|'  # 双引号
        r"&#x27;.*?&#x27;|"  # HTML编码单引号
        r"&quot;.*?&quot;|"  # HTML编码双引号
        r"&#34;.*?&#34;"  # HTML编码双引号(数字形式)
    )

    # 匹配希腊字母的正则（按长度降序避免部分匹配）
    _greek_words = sorted(_REPLACEMENTS.keys(), key=len, reverse=True)
    _GREEK_PATTERN = re.compile(
        r"\b(" + "|".join(re.escape(w) for w in _greek_words) + r")(?=[_\s\W]|$)"
    )

    def handle(self, data: str, ctx=None) -> str:
        """使用占位符方法替换希腊字母，保护引号内的内容"""
        # 步骤1：用占位符临时替换所有引号内容
        quotes = []

        def save_quote(match):
            quotes.append(match.group(0))
            return f"\x00QUOTE_{len(quotes)-1}\x00"

        data = self._QUOTE_PATTERN.sub(save_quote, data)

        # 步骤2：替换所有希腊字母
        data = self._GREEK_PATTERN.sub(lambda m: self._REPLACEMENTS[m.group(1)], data)

        # 步骤3：一次性还原所有引号内容（避免多次 replace 扫描）
        def restore_quote(match):
            index = int(match.group(1))
            return quotes[index]

        data = re.sub(r"\x00QUOTE_(\d+)\x00", restore_quote, data)

        return data
