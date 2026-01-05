# 带单位
from pint import UnitRegistry

unit = UnitRegistry()

import pint
from pint.delegates.formatter import Formatter
from pint.delegates.formatter.plain import DefaultFormatter


# class MyFormatter(DefaultFormatter):
#     def __init__(self, registry: UnitRegistry | None = None):
#         super().__init__(registry)
#         self._formatter = Formatter(registry)

#     def format_unit(self, unit, uspec, sort_func, **babel_kwds) -> str:
#         print(
#             f"Formatting unit: {unit}, uspec: {uspec}, sort_func: {sort_func}, babel_kwds: {babel_kwds}"
#         )
#         formatted = self._formatter.format_unit(unit, uspec, sort_func, **babel_kwds)

#         if "H" not in uspec:
#             return formatted

#         # 将空格转换成点号
#         return f"<i class='unit'>{formatted.replace(" ", "·")}</i>"


# 自定义格式化器
# 参考 https://pint.readthedocs.io/en/stable/user/formatting.html
@pint.register_unit_format("html")
def format_unit_html(unit, registry, **options) -> str:
    uspec = "H"
    formatted = registry.formatter.get_formatter(uspec).format_unit(
        unit, uspec, registry.formatter.default_sort_func, **options
    )
    # 将空格转换成点号
    return f"<i class='unit'>{formatted.replace(" ", "·")}</i>"


# unit.formatter = MyFormatter(unit)
unit.formatter.default_format = "~html"

if __name__ == "__main__":
    q = 2.3e-6 * unit.m**8 / (unit.s**2 * unit.kg)
    print(q)
    print(100 * unit.m * unit.s**2 / (unit.kg * unit.m**2))
    speed2 = 1000 * unit.m / unit.second + (2 * unit.m / unit.second)
    print(speed2)
