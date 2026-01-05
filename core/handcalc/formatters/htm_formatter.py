class HTMLFormatter:
    """
    对于单位，使用 mathml 进行格式化
    """

    def format_variable(self, name: str) -> str:
        parts = name.split("_")
        if len(parts) == 1:
            return f"<var class='variable'>{name}</var>"
        main = parts[0]
        sub = "".join(parts[1:])
        return f"<var class='variable'>{main}<sub>{sub}</sub></var>"

    def format_pow(self, base: str, exponent: str) -> str:
        return f"<span class='power'>{base}<sup>{exponent}</sup></span>"

    def format_frac(self, numerator: str, denominator: str) -> str:
        return f"<span class='fraction'><span class='numerator'>{numerator}</span>/<span class='denominator'>{denominator}</span></span>"

    def format_sqrt(self, radicand: str) -> str:
        return f"<span class='sqrt'>&radic;({radicand})</span>"

    def format_integral(self, integrand: str, variable: str) -> str:
        return f"<span class='integral'>∫ {integrand} d{variable}</span>"

    # region Unit Formatting
    def format_unit(self, unit: str) -> str:
        return f"<i class='unit'>{unit}</i>"

    def format_unit_pow(self, unit: str, exponent: str) -> str:
        return f"<i class='unit power'>{unit}<sup>{exponent}</sup></i>"

    def format_unit_frac(self, numerator: str, denominator: str) -> str:
        return f"<i class='unit fraction'>{numerator}/{denominator}</i>"

    def format_unit_mult(self, left: str, right: str) -> str:
        return f"<i class='unit multiplication'>{left}·{right}</i>"


# endregion
