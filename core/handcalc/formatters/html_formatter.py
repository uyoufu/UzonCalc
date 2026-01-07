class HTMLFormatter:
    """
    输出 mathml 格式化代码
    """

    def wrap_math(self, content: str) -> str:
        return f"<math xmlns='http://www.w3.org/1998/Math/MathML'>{content}</math>"

    def format_variable(self, name: str) -> str:
        parts = name.split("_")
        if len(parts) == 1:
            return f"<mi class='variable'>{name}</mi>"

        main = parts[0]
        sub = "".join(parts[1:])
        return f"<msub><mi class='variable'>{main}</mi><mn>{sub}</mn></msub>"

    def format_pow(self, base: str, exponent: str) -> str:
        return f"<span class='power'>{base}<sup>{exponent}</sup></span>"

    def format_frac(self, numerator: str, denominator: str) -> str:
        return f"<mfrac><mi><mrow>{numerator}</mrow></mi><mi><mrow>{denominator}</mrow></mi></mfrac>"

    def format_abs(self, value: str) -> str:
        return f"<mo>|</mo><mi>{value}</mi><mo>|</mo>"

    def format_sqrt(self, radicand: str) -> str:
        return f"<span class='sqrt'>&radic;({radicand})</span>"

    def format_integral(self, integrand: str, variable: str) -> str:
        return f"<span class='integral'>∫ {integrand} d{variable}</span>"

    # region Unit Formatting
    def format_unit(self, unit: str) -> str:
        return f"<mtext class='unit'>{unit}</mtext>"

    def format_unit_pow(self, unit: str, exponent: str) -> str:
        return f"<msup>{self.format_unit(unit)}</mi><mrow>{exponent}</mrow></msup>"

    def format_unit_frac(self, numerator: str, denominator: str) -> str:
        return f"<mfrac><mrow>{numerator}</mrow><mrow>{denominator}</mrow></mfrac>"

    def format_unit_mult(self, left: str, right: str) -> str:
        return f"<mrow>{left}<mo>·</mo>{right}</mrow>"

    # endregion

    # region 积分相关
    # endregion
