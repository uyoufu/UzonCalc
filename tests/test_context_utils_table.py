from core.uzoncalc.context import CalcContext
from core.uzoncalc.context_utils.table import Table, Td, Tr, table, td, th
from core.uzoncalc.globals import _calc_instance


def test_table_rows_accept_flat_values_as_one_row():
    """扁平 rows 应渲染为单行表格。"""
    html = table(["Name", "Value"], ["A", 1.5])

    assert html.count("<tr") == 2
    assert "<td>A</td><td>1.5</td>" in html


def test_table_rows_accept_nested_values_as_multiple_rows():
    """二维 rows 应渲染为多行表格。"""
    html = table(["Name", "Value"], [["A", 1.5], ["B", 2.5]])

    assert html.count("<tbody><tr") == 1
    assert html.count("<tr") == 3
    assert "<td>B</td><td>2.5</td>" in html


def test_table_rows_accept_td_list_as_one_row():
    """Td 列表应被视为一行。"""
    html = table(["Name", "Value"], [Td("A", classes="name-cell"), Td(1.5)])

    assert '<td class="name-cell">A</td><td>1.5</td>' in html
    assert html.count("<tr") == 2


def test_table_rows_accept_tr_list_as_multiple_rows():
    """Tr 列表应被视为多行。"""
    html = table(
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
    html = table([[th("Name", rowspan=2), th("Value", colspan=2)]], [["A", 1.5]])

    assert '<th rowspan="2" colspan="1">Name</th>' in html
    assert '<th rowspan="1" colspan="2">Value</th>' in html


def test_table_keeps_rendered_td_body_cells():
    """已渲染 td 表体单元格应保持原有属性。"""
    html = table(["Name"], [td("A", classes="name-cell")])

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
