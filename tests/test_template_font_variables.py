from core.uzoncalc.context_options import ContextOptions
from core.uzoncalc.template.utils import render_html_template


def test_rendered_template_sets_body_font_variable_from_page_options():
    options = ContextOptions()
    options.page_info.font_family = "Arial, sans-serif"

    html = render_html_template("<p>content</p>", options)

    assert "--uz-font-body-option: Arial, sans-serif;" in html
    assert "font-family: var(--uz-font-body);" in html
    assert "font-family: Arial, sans-serif;" not in html
