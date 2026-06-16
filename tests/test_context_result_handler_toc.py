from core.uzoncalc.context import CalcContext
from core.uzoncalc.context_utils import doc


def test_html_content_generates_toc_from_placeholder():
    """目录占位符应在最终 HTML 内容中自动生成目录项。"""
    ctx = CalcContext()
    ctx.append_content(
        """
<div id="toc" data-toc-title="目录">
    <div id='toc-container'></div>
</div>
<h2>总则</h2>
<h3 id="material">材料</h3>
<h2>计算</h2>
"""
    )

    html = ctx.html_content()

    assert '<div class="toc-list">' in html
    assert 'href="#heading-0"' in html
    assert '<span class="toc-number">1</span>' in html
    assert '<span class="toc-text">总则</span>' in html
    assert (
        '<span class="toc-page" data-heading-id="heading-0" '
        'data-page-placeholder="true">&nbsp;</span>'
    ) in html
    assert 'href="#material"' in html
    assert '<span class="toc-number">1.1</span>' in html
    assert 'id="heading-0"' in html
    assert '<h3 id="material">材料</h3>' in html


def test_html_content_keeps_content_without_toc_placeholder_unchanged():
    """没有目录占位符时不应改写正文 HTML。"""
    ctx = CalcContext()
    ctx.append_content('<h2>A</h2><p>正文</p>')

    assert ctx.html_content() == '<h2>A</h2><p>正文</p>'


def test_html_content_does_not_regenerate_existing_toc():
    """已有目录内容时保持原样，避免重复生成目录。"""
    ctx = CalcContext()
    ctx.append_content(
        """
<div id="toc">
    <div id="toc-container"><div class="toc-list">existing</div></div>
</div>
<h2>总则</h2>
"""
    )

    html = ctx.html_content()

    assert html.count('class="toc-list"') == 1
    assert "existing" in html
    assert 'href="#heading-0"' not in html


def test_html_content_treats_toc_container_child_as_existing_content():
    """目录容器中已有子元素时不应再次注入目录。"""
    ctx = CalcContext()
    ctx.append_content(
        '<div id="toc"><div id="toc-container"><span></span></div></div>'
        "<h2>总则</h2>"
    )

    html = ctx.html_content()

    assert '<span></span>' in html
    assert '<div class="toc-list">' not in html


def test_html_content_skips_headings_inside_toc():
    """目录内部标题不应被收集为正文目录项。"""
    ctx = CalcContext()
    ctx.append_content(
        """
<div id="toc">
    <h2>目录标题</h2>
    <div id="toc-container"></div>
</div>
<h1>文档标题</h1>
<h2>正文标题</h2>
<h6>细节</h6>
"""
    )

    html = ctx.html_content()

    assert '<span class="toc-text">目录标题</span>' not in html
    assert '<span class="toc-text">文档标题</span>' not in html
    assert '<span class="toc-text">正文标题</span>' in html
    assert '<span class="toc-text">细节</span>' in html


def test_html_content_escapes_toc_heading_text():
    """目录项文本按纯文本转义输出。"""
    ctx = CalcContext()
    ctx.append_content(
        '<div id="toc"><div id="toc-container"></div></div>'
        '<h2>A &lt; B &amp; "C"</h2>'
    )

    html = ctx.html_content()

    assert '<span class="toc-text">A &lt; B &amp; &quot;C&quot;</span>' in html


def test_doc_toc_placeholder_is_filled_by_html_content(monkeypatch):
    """doc.toc() 插入的占位符应由 html_content 自动填充。"""
    ctx = CalcContext()
    monkeypatch.setattr(doc, "get_current_instance", lambda: ctx)

    doc.toc("目录")
    ctx.append_content("<h2>正文标题</h2>")

    html = ctx.html_content()

    assert 'data-toc-title="目录"' in html
    assert '<span class="toc-text">正文标题</span>' in html
