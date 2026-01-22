# 带单位
from pint import UnitRegistry

unit = UnitRegistry()
unit.formatter.default_format = "~P"
