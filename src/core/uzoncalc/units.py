# 带单位
from pint import UnitRegistry

unit = UnitRegistry()
unit.formatter.default_format = "~P"
# Pint 的 FullFormatter 默认 default_sort_func = sort_by_unit_name，并且 format_unit() 会把未传
# 入的 sort_func 替换成 self.default_sort_func。这就是 N·m 被重排为 m·N 的原因。
# https://github.com/hgrecco/pint/blob/master/pint/delegates/formatter/full.py
unit.formatter.default_sort_func = None
