# 带单位
from pint import UnitRegistry

unit = UnitRegistry()

import pint
from pint.delegates.formatter import Formatter
from pint.delegates.formatter.plain import DefaultFormatter
from pint.delegates.formatter.html import HTMLFormatter


class MathmlFormatter(DefaultFormatter):
    def __init__(self, registry: UnitRegistry | None = None):
        super().__init__(registry)
        self.__formatter = Formatter(registry)

    def format_unit(self, unit, uspec, sort_func=None, **babel_kwds) -> str:
        formatted = self.__formatter.format_unit(unit, uspec, sort_func, **babel_kwds)

        if "H" not in uspec:
            return formatted

        # 将空格转换成点号
        return f"<mtext class='unit'>{formatted.replace(" ", "·")}</mtext>"

    def format_quantity(
        self,
        quantity,
        qspec: str = "",
        sort_func=None,
        **babel_kwds,
    ) -> str:
        # 调用父级的格式化器
        formatted = super().format_quantity(quantity, qspec, sort_func, **babel_kwds)
        formatter = self.__formatter.get_formatter("H")

        return f"<mn>{formatted}</mn>"


# 自定义格式化器
# 参考 https://pint.readthedocs.io/en/stable/user/formatting.html
# @pint.register_unit_format("html")
# def format_unit_html(unit, registry, **options) -> str:
#     uspec = "H"
#     formatted = registry.formatter.get_formatter(uspec).format_unit(
#         unit, uspec, registry.formatter.default_sort_func, **options
#     )
#     # 将空格转换成点号
#     return f"<mtext class='unit'>{formatted.replace(" ", "·")}</mtext>"


# unit.formatter = MathmlFormatter(unit)
unit.formatter.default_format = "~P"

if __name__ == "__main__":
    print(unit.parse_units("meter**1*second**-2*kg**-1"))
