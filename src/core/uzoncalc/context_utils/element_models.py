from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
import html
from typing import Any, Protocol


class HtmlFragment(str):
    """可信 HTML 片段，可在 f-string 渲染时跳过文本转义。"""

    def __new__(cls, value: str) -> "HtmlFragment":
        return super().__new__(cls, value)

    def __html__(self) -> str:
        """返回原始 HTML 字符串，供渲染器识别可信片段。"""
        return str(self)


class LabelKind(StrEnum):
    """自动编号标签类型。"""

    FIGURE = "figure"
    TABLE = "table"


class ISavefig(Protocol):
    """
    支持保存为图片的 Matplotlib 绘图对象协议。
    """

    def savefig(self, *args: Any, **kwargs: Any) -> Any:
        """
        保存当前绘图内容到目标缓冲区或文件。
        """
        ...


@dataclass
class Props:
    """
    HTML element properties class.

    Supports standard HTML attributes and custom attributes.

    Example:
        Props(id="my-id", classes="foo bar", styles={"color": "red"})
        Props(id="my-id", data_value="123")
    """

    class_str: str | None = None
    style: dict[str, str] | None = None
    id: str | None = None
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str]:
        """
        Convert Props to a dictionary of HTML attributes.

        :return: Dictionary mapping attribute names to their string values.
        """
        attrs: dict[str, str] = {}

        # Handle id
        if self.id:
            attrs["id"] = self.id

        # Handle classes
        if self.class_str:
            attrs["class"] = self.class_str

        # Handle styles
        if self.style:
            attrs["style"] = "; ".join(f"{k}: {v}" for k, v in self.style.items())

        # Handle custom attributes
        for key, value in self.custom.items():
            if value is not None:
                # Convert underscores to hyphens for HTML attributes
                # e.g. data_value -> data-value
                attrs[key.replace("_", "-")] = str(value)
        return attrs

    def to_html_attrs(self) -> str:
        """将属性字典渲染为 HTML 属性字符串。"""
        attrs = self.to_dict()
        if not attrs:
            return ""
        attr_text = " ".join(
            f'{key}="{html.escape(value, quote=True)}"' for key, value in attrs.items()
        )
        return f" {attr_text}"


@dataclass(frozen=True)
class AutoLabel:
    """自动编号标签信息，同时承载本体标记与正文引用占位符。"""

    kind: LabelKind
    label_id: str
    prefix: str

    def reference_html(self) -> HtmlFragment:
        """渲染正文引用占位符。"""
        return _span_html(self.reference_props())

    def source_html(self) -> HtmlFragment:
        """渲染图表本体的编号源占位符。"""
        source_props = replace(
            self.source_props(),
            class_str=f"uzoncalc-label-source uzoncalc-label-source-{self.kind.value}",
        )
        return _span_html(source_props)

    def reference_props(self) -> Props:
        """生成正文引用占位符属性。"""
        return Props(
            custom={
                "data_uzoncalc_label_ref": self.label_id,
                "data_uzoncalc_label_kind": self.kind.value,
                "data_uzoncalc_label_prefix": self.prefix,
            }
        )

    def source_props(self) -> Props:
        """生成图表本体编号源占位符属性。"""
        return Props(
            custom={
                "data_uzoncalc_label_source": self.label_id,
                "data_uzoncalc_label_kind": self.kind.value,
                "data_uzoncalc_label_prefix": self.prefix,
            }
        )


def _span_html(element_props: Props) -> HtmlFragment:
    """渲染无内容 span，并保留可信 HTML 类型。"""
    return HtmlFragment(f"<span{element_props.to_html_attrs()}></span>")
