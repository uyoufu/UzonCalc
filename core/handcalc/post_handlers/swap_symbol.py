"""后处理器：将希腊英文替换为数学符号 - 优化版本使用单次正则替换"""

import re
from core.handcalc.post_handlers.base_post_handler import BasePostHandler


class SwapSymbol(BasePostHandler):
    """后处理器：将希腊英文替换为数学符号"""

    # 构建替换映射
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

    # 编译正则表达式：匹配所有希腊字母（单词边界）
    _PATTERN = re.compile(
        r"\b(" + "|".join(re.escape(k) for k in _REPLACEMENTS.keys()) + r")\b"
    )

    def handle(self, data: str) -> str:
        """使用单次正则替换优化性能"""
        return self._PATTERN.sub(lambda m: self._REPLACEMENTS[m.group(0)], data)
