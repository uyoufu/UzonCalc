from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .elements import Props


# 表格单元格支持任意值，渲染时统一通过 str() 转为显示文本。
TableCellValue = Any
TableHeaderRows = list[list[TableCellValue]] | list[TableCellValue]
TableBodyRows = (
    list[list[TableCellValue]] | list[TableCellValue] | list["Td"] | list["Tr"]
)


@dataclass
class Td:
    """表格单元格模型，可单独设置 class。"""

    value: TableCellValue
    classes: str | None = None

    def to_html(self) -> str:
        """渲染 td HTML 字符串。"""
        # 复用通用 HTML 渲染函数，避免属性拼接逻辑重复。
        from .elements import h

        return h("td", children=_format_td_cell_value(self.value), classes=self.classes)


@dataclass
class Tr:
    """表格行模型，可单独设置 class。"""

    cells: list[TableCellValue | Td]
    classes: str | None = None

    def to_html(self) -> str:
        """渲染 tr HTML 字符串。"""
        from .elements import h

        # 统一渲染单元格，同时兼容旧版已渲染 td 字符串。
        cells_html = "".join(_render_body_cell(cell) for cell in self.cells)
        return h("tr", children=cells_html, classes=self.classes)


def table(
    headers: TableHeaderRows,
    rows: TableBodyRows,
    classes: str | None = None,
    *,
    title: str | None = None,
    props: Props | None = None,
    persist: bool = False,
) -> str:
    """渲染表格 HTML，rows 会统一转换为 Tr/Td 模型处理。"""
    from .elements import h

    children: list[str] = []
    header_rows = _normalize_header_rows(headers)
    body_rows = _normalize_body_rows(rows)

    if title:
        children.append(h("caption", children=title))

    if header_rows:
        thead_rows = []
        for header_row in header_rows:
            cells = "".join(_wrap_header_cell(cell) for cell in header_row)
            thead_rows.append(tr(cells))
        children.append(h("thead", children="".join(thead_rows)))

    if body_rows:
        tbody_rows = [body_row.to_html() for body_row in body_rows]
        children.append(h("tbody", children="".join(tbody_rows)))

    return h("table", children=children, classes=classes, props=props, persist=persist)


def Table(
    headers: TableHeaderRows,
    rows: TableBodyRows,
    classes: str | None = None,
    *,
    title: str | None = None,
    props: Props | None = None,
) -> None:
    """渲染并记录表格 HTML。"""
    table(
        headers=headers,
        rows=rows,
        title=title,
        classes=classes,
        props=props,
        persist=True,
    )


def th(
    value: TableCellValue,
    classes: str | None = None,
    *,
    rowspan: int = 1,
    colspan: int = 1,
) -> str:
    """渲染表头单元格 HTML。"""
    from .elements import h, props

    return h(
        "th",
        children=str(value),
        classes=classes,
        props=props(rowspan=rowspan, colspan=colspan),
    )


def tr(value: str, classes: str | None = None) -> str:
    """渲染表格行 HTML。"""
    from .elements import h

    return h("tr", children=value, classes=classes)


def td(value: TableCellValue, classes: str | None = None) -> str:
    """渲染表格单元格 HTML。"""
    # 任意单元格值交由 Td 统一转换，避免入口之间行为不一致。
    return Td(value=value, classes=classes).to_html()


def _normalize_header_rows(values: TableHeaderRows) -> list[list[Any]]:
    """将表头输入统一转换为二维行数组。"""
    if not values:
        return []
    if isinstance(values[0], list):  # type: ignore[index]
        return values  # type: ignore[return-value]
    return [values]  # type: ignore[list-item]


def _normalize_body_rows(values: TableBodyRows) -> list[Tr]:
    """将表体输入统一转换为 Tr 模型列表。"""
    if not values:
        return []

    first_value = values[0]
    if isinstance(first_value, Tr):
        return values  # type: ignore[return-value]
    if isinstance(first_value, Td):
        return [Tr(cells=values)]  # type: ignore[list-item]
    if isinstance(first_value, list):
        return [Tr(cells=row) for row in values]  # type: ignore[arg-type]
    return [Tr(cells=values)]  # type: ignore[list-item]


def _render_body_cell(value: TableCellValue | Td) -> str:
    """将表体单元格统一渲染为 td HTML。"""
    if isinstance(value, Td):
        return value.to_html()

    text = str(value)
    if text.startswith("<td"):
        return text
    return Td(value=value).to_html()


def _format_td_cell_value(value: TableCellValue) -> str:
    """格式化 td 单元格显示文本。"""

    from ..handcalc.rendering.value_renderer import render_value_text

    return render_value_text(value)


def _wrap_header_cell(value: Any) -> str:
    """兼容已渲染 th HTML 与普通表头值。"""
    text = str(value)
    if text.startswith("<th"):
        return text
    return th(text)
