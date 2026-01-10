# 带单位
from pint import UnitRegistry

unit = UnitRegistry()

import pint
from pint.delegates.formatter import Formatter
from pint.delegates.formatter.plain import DefaultFormatter
from pint.delegates.formatter.html import HTMLFormatter

unit.formatter.default_format = "~P"

# 添加自定义单位

if __name__ == "__main__":
    print(unit.parse_units("meter**1*second**-2*kg**-1"))
