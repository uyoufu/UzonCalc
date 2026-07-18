import pytest

from uzoncalc.context_options import ContextOptions
from uzoncalc.template.utils import load_template, render_html_template


def test_rendered_template_sets_body_font_variable_from_page_options():
    """模板只注入字体变量值，body 字体规则由 template.js 样式提供。"""
    options = ContextOptions()
    options.page_info.font_family = "Arial, sans-serif"

    html = render_html_template("<p>content</p>", options)

    assert "--uz-font-body-option: Arial, sans-serif;" in html
    assert "font-family: var(--uz-font-body);" not in html
    assert "font-family: Arial, sans-serif;" not in html


def test_load_template_uses_dynamic_script_source(monkeypatch):
    """模板脚本地址应在每次加载时读取环境变量并安全转义。"""
    monkeypatch.delenv("UZONCALC_TEMPLATE_SCRIPT_SRC", raising=False)
    assert 'src="https://calc.uzoncloud.com/scripts/template.js"' in load_template()

    monkeypatch.setenv(
        "UZONCALC_TEMPLATE_SCRIPT_SRC",
        "https://assets.example.com/template.js?a=1&b=2",
    )
    assert (
        'src="https://assets.example.com/template.js?a=1&amp;b=2"'
        in load_template()
    )


def test_load_template_rejects_non_http_script_source(monkeypatch):
    """模板脚本地址应拒绝非 HTTP(S) 协议。"""
    monkeypatch.setenv("UZONCALC_TEMPLATE_SCRIPT_SRC", "javascript:alert(1)")
    with pytest.raises(ValueError, match="absolute HTTP"):
        load_template()
