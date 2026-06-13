from core.uzoncalc.context import CalcContext
from core.uzoncalc.context_utils.elements import Img, LabelKind, Plot, create_auto_label
from core.uzoncalc.context_utils.options import figure_prefix
from core.uzoncalc.extension.echarts import EChart
from core.uzoncalc.globals import _calc_instance


class FakeFigure:
    """最小 savefig 协议实现，用于 Plot 测试。"""

    def savefig(self, buffer, *args, **kwargs):
        buffer.write(b"fake-png-bytes")


def test_img_returns_reference_placeholder_and_persists_label_source():
    """Img 应返回可复用引用占位符，并在正文写入图号源标记。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        placeholder = Img("/assets/demo.png", alt="示例图片")
    finally:
        _calc_instance.reset(token)

    assert (
        placeholder
        == '<span data-uzoncalc-label-ref="figure-1" data-uzoncalc-label-kind="figure" data-uzoncalc-label-prefix="图"></span>'
    )
    assert 'data-uzoncalc-label-source="figure-1"' in context.contents[-1]
    assert 'data-uzoncalc-label-prefix="图"' in context.contents[-1]
    assert 'class="uzoncalc-figure-wrapper"' in context.contents[-1]
    assert 'class="uzoncalc-label-caption uzoncalc-label-caption-figure"' in context.contents[-1]
    assert "示例图片" in context.contents[-1]


def test_plot_returns_reference_placeholder_for_binary_content():
    """Plot 传入二进制图片时应沿用 Img 的标签行为。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        placeholder = Plot(b"png-bytes")
    finally:
        _calc_instance.reset(token)

    assert 'data-uzoncalc-label-ref="figure-1"' in placeholder
    assert 'data-uzoncalc-label-source="figure-1"' in context.contents[-1]


def test_plot_returns_reference_placeholder_for_figure_object():
    """Plot 传入 Figure 对象时也应返回图号引用占位符。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        placeholder = Plot(FakeFigure())
    finally:
        _calc_instance.reset(token)

    assert 'data-uzoncalc-label-ref="figure-1"' in placeholder
    assert 'data-uzoncalc-label-source="figure-1"' in context.contents[-1]


def test_echart_returns_reference_placeholder_and_persists_label_source():
    """EChart 应返回引用占位符，并在图表后写入图号源标记。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        placeholder = EChart({"xAxis": {}, "yAxis": {}, "series": []})
    finally:
        _calc_instance.reset(token)

    assert 'data-uzoncalc-label-ref="figure-1"' in placeholder
    assert 'data-uzoncalc-label-source="figure-1"' in context.contents[-1]
    assert 'data-uzoncalc-label-prefix="图"' in context.contents[-1]


def test_figure_prefix_is_serialized_into_new_placeholders():
    """figure_prefix 设置应在占位符生成时固化到新图表。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        figure_prefix("Figure")
        placeholder = Img("/assets/demo.png")
    finally:
        _calc_instance.reset(token)

    assert 'data-uzoncalc-label-prefix="Figure"' in placeholder
    assert 'data-uzoncalc-label-prefix="Figure"' in context.contents[-1]


def test_label_kind_uses_string_enum_values():
    """LabelKind 应使用字符串枚举，避免调用方手写裸字符串。"""
    assert LabelKind.FIGURE.value == "figure"
    assert LabelKind.TABLE.value == "table"


def test_create_auto_label_accepts_label_kind_enum():
    """create_auto_label 应接收 LabelKind 枚举并输出稳定 data-kind。"""
    context = CalcContext()
    token = _calc_instance.set(context)
    try:
        label = create_auto_label(LabelKind.FIGURE)
    finally:
        _calc_instance.reset(token)

    assert label.kind is LabelKind.FIGURE
    assert label.label_id == "figure-1"
    assert 'data-uzoncalc-label-kind="figure"' in label.reference_html()
