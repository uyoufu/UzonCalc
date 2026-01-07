from core.handcalc.post_handlers.base_post_handler import BasePostHandler


class SwapSymbol(BasePostHandler):
    """
    后处理器：将希腊英文替换为数学符号
    """

    def handle(self, data: str) -> str:
        replacements = {
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

        for old, new in replacements.items():
            data = data.replace(old, new)

        return data
