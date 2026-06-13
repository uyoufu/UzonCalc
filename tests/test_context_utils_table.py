from importlib import import_module
from typing import Any, get_type_hints

from core.uzoncalc.context import CalcContext
from core.uzoncalc.context_utils.elements import HtmlFragment
from core.uzoncalc.context_utils.table import Table, Td, Tr, table, td, th
from core.uzoncalc.globals import _calc_instance
from core.uzoncalc.units import unit

table_module = import_module("core.uzoncalc.context_utils.table")


def render_table_in_context(*args, **kwargs) -> str:
    """在显式 CalcContext 中渲染表格，匹配当前值格式化依赖。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        return table(*args, **kwargs)
    finally:
        _calc_instance.reset(token)


class DemoCellValue:
    """测试用自定义表格值。"""

    def __str__(self):
        """返回可预测的单元格显示文本。"""
        # 模拟项目中可能传入的业务对象。
        return "custom-cell-value"


def test_table_cell_value_type_accepts_any_value():
    """表格单元格公开类型应支持任意值。"""
    assert table_module.TableCellValue is Any
    assert get_type_hints(Td)["value"] is Any


def test_table_rows_accept_flat_values_as_one_row():
    """扁平 rows 应渲染为单行表格。"""
    html = render_table_in_context(["Name", "Value"], ["A", 1.5])

    assert html.count("<tr") == 2
    assert "<td>A</td><td>1.5</td>" in html


def test_table_rows_accept_nested_values_as_multiple_rows():
    """二维 rows 应渲染为多行表格。"""
    html = render_table_in_context(["Name", "Value"], [["A", 1.5], ["B", 2.5]])

    assert html.count("<tbody><tr") == 1
    assert html.count("<tr") == 3
    assert "<td>B</td><td>2.5</td>" in html


def test_table_rows_accept_unit_quantities_as_cell_values():
    """带单位量值应作为普通单元格渲染。"""
    html = render_table_in_context(["Name", "Value"], [["长度", 1.5 * unit.meter]])

    assert "<td>长度</td>" in html
    assert "<td>1.5 m</td>" in html


def test_table_rows_accept_arbitrary_objects_as_cell_values():
    """任意对象值应通过 str() 作为普通单元格渲染。"""
    html = render_table_in_context(
        ["Enabled", "Value", "Empty"], [[True, DemoCellValue(), None]]
    )

    assert "<td>True</td>" in html
    assert "<td>custom-cell-value</td>" in html
    assert "<td></td>" in html


def test_table_rows_accept_td_list_as_one_row():
    """Td 列表应被视为一行。"""
    html = render_table_in_context(
        ["Name", "Value"], [Td("A", classes="name-cell"), Td(1.5)]
    )

    assert '<td class="name-cell">A</td><td>1.5</td>' in html
    assert html.count("<tr") == 2


def test_table_td_formats_float_precision():
    """Td 浮点值应按当前上下文精度显示，避免暴露浮点误差。"""
    html = render_table_in_context(["Value"], [Td(0.1 + 0.2), Td(3.1415926535)])

    # 默认保留 3 位小数，并移除多余尾零。
    assert "<td>0.3</td><td>3.142</td>" in html


def test_table_td_formats_float_with_context_precision():
    """Td 浮点值应遵循当前上下文的小数精度配置。"""
    context = CalcContext()
    context.options.float_precision = 2
    token = _calc_instance.set(context)
    try:
        html = table(["Value"], [Td(3.1415926535)])
    finally:
        _calc_instance.reset(token)

    assert "<td>3.14</td>" in html


def test_table_rows_accept_tr_list_as_multiple_rows():
    """Tr 列表应被视为多行。"""
    html = render_table_in_context(
        ["Name", "Value"],
        [
            Tr([Td("A", classes="name-cell"), 1.5], classes="first-row"),
            Tr(["B", 2.5]),
        ],
    )

    assert (
        '<tr class="first-row"><td class="name-cell">A</td><td>1.5</td></tr>'
        in html
    )
    assert "<tr><td>B</td><td>2.5</td></tr>" in html


def test_table_keeps_rendered_th_header_cells():
    """已渲染 th 表头应保持原有属性。"""
    html = render_table_in_context(
        [[th("Name", rowspan=2), th("Value", colspan=2)]], [["A", 1.5]]
    )

    assert '<th rowspan="2" colspan="1">Name</th>' in html
    assert '<th rowspan="1" colspan="2">Value</th>' in html


def test_table_keeps_rendered_td_body_cells():
    """已渲染 td 表体单元格应保持原有属性。"""
    html = render_table_in_context(["Name"], [td("A", classes="name-cell")])

    assert '<td class="name-cell">A</td>' in html
    assert "<td><td" not in html


def test_table_function_persists_content():
    """Table 函数应将表格写入当前上下文。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        Table(["Name"], [Td("A", classes="name-cell")])
    finally:
        _calc_instance.reset(token)

    assert context.contents
    assert '<td class="name-cell">A</td>' in context.contents[-1]


def test_table_function_applies_subscript_post_handler():
    """Table 写入上下文时应自动转换单元格中的下标文本。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        Table(["项目"], [["单位宽度静土压力 E_j"]])
    finally:
        _calc_instance.reset(token)

    assert "单位宽度静土压力 E<sub>j</sub>" in context.contents[-1]


def test_table_returns_reference_placeholder_and_persists_label_source():
    """Table 应返回可复用引用占位符，并在标题中写入表号源标记。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        placeholder = Table(["Name"], [["A"]], title="示例表")
    finally:
        _calc_instance.reset(token)

    assert (
        placeholder
        == '<span data-uzoncalc-label-ref="table-1" data-uzoncalc-label-kind="table" data-uzoncalc-label-prefix="表"></span>'
    )
    assert isinstance(placeholder, str)
    assert isinstance(placeholder, HtmlFragment)
    assert placeholder.__html__() == str(placeholder)
    assert 'data-uzoncalc-label-source="table-1"' in context.contents[-1]
    assert 'data-uzoncalc-label-prefix="表"' in context.contents[-1]
    assert 'class="uzoncalc-label-caption uzoncalc-label-caption-table"' in context.contents[-1]
    assert "示例表" in context.contents[-1]


def test_table_without_title_still_persists_caption_label_source():
    """无标题 Table 也应生成 caption 以承载自动编号。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        Table(["Name"], [["A"]])
    finally:
        _calc_instance.reset(token)

    assert "<caption" in context.contents[-1]
    assert 'class="uzoncalc-label-caption uzoncalc-label-caption-table"' in context.contents[-1]
    assert 'data-uzoncalc-label-source="table-1"' in context.contents[-1]
