from core.uzoncalc.context_options import ContextOptions
from core.uzoncalc.context_utils import doc
from core.uzoncalc.template.utils import generate_custom_heads


class DummyContext:
    def __init__(self):
        self.options = ContextOptions()
        self.contents = []

    def append_content(self, content: str):
        """记录写入正文的 HTML 片段。"""
        self.contents.append(content)


def test_head_hash_is_stable_for_equivalent_content():
    attrs_a = {
        "src": "https://example.com/app.js",
        "integrity": "sha256-abc",
        "crossorigin": "anonymous",
    }
    attrs_b = {
        "crossorigin": "anonymous",
        "integrity": "sha256-abc",
        "src": "https://example.com/app.js",
    }

    assert doc._compute_head_hash("script", attrs_a) == doc._compute_head_hash(
        "SCRIPT", attrs_b
    )


def test_head_stores_normalized_content_under_hash_key(monkeypatch):
    ctx = DummyContext()
    monkeypatch.setattr(doc, "get_current_instance", lambda: ctx)

    doc.head(
        "SCRIPT",
        {
            "src": "https://example.com/app.js",
            "integrity": "sha256-abc",
            "crossorigin": "anonymous",
        },
    )

    assert len(ctx.options.heads) == 1

    head_hash = next(iter(ctx.options.heads))
    assert head_hash == doc._compute_head_hash(
        "script",
        {
            "crossorigin": "anonymous",
            "integrity": "sha256-abc",
            "src": "https://example.com/app.js",
        },
    )
    assert ctx.options.heads[head_hash] == (
        "script",
        {
            "crossorigin": "anonymous",
            "integrity": "sha256-abc",
            "src": "https://example.com/app.js",
        },
    )


def test_generate_custom_heads_renders_hash_based_entries():
    head_hash = doc._compute_head_hash(
        "script",
        {
            "crossorigin": "anonymous",
            "integrity": "sha256-abc",
            "src": "https://example.com/app.js",
        },
    )

    html = generate_custom_heads(
        {
            head_hash: (
                "script",
                {
                    "crossorigin": "anonymous",
                    "integrity": "sha256-abc",
                    "src": "https://example.com/app.js",
                },
            )
        }
    )

    assert (
        html
        == '<script crossorigin="anonymous" integrity="sha256-abc" src="https://example.com/app.js"></script>'
    )


def test_toc_renders_escaped_title_attribute(monkeypatch):
    ctx = DummyContext()
    monkeypatch.setattr(doc, "get_current_instance", lambda: ctx)

    doc.toc('A < B & "C"')

    html = "".join(ctx.contents)
    assert 'data-toc-title="A &lt; B &amp; &quot;C&quot;"' in html
    assert "A &lt; B &amp; &quot;C&quot;" in html
    assert 'A < B & "C"' not in html
