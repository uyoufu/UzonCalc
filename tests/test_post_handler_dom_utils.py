from core.uzoncalc.handcalc.post_handlers.dom_utils import (
    FRAGMENT_ROOT_TAG,
    PostHandlerNode,
    parse_html_fragment,
    serialize_html_fragment,
)


def test_parse_html_fragment_uses_fixed_temporary_root():
    """HTML 片段应包在固定临时根中，序列化结果不包含临时根。"""
    root = parse_html_fragment("<p>x</p><p>y</p>")

    assert root.tag == FRAGMENT_ROOT_TAG
    assert serialize_html_fragment(root) == "<p>x</p><p>y</p>"


def test_serialize_html_fragment_uses_lxml_native_html_output():
    """原生 HTML 序列化不再强制转义普通文本引号。"""
    assert serialize_html_fragment(parse_html_fragment("'a' \"b\"")) == "'a' \"b\""
    assert (
        serialize_html_fragment(parse_html_fragment("<option selected>One</option>"))
        == "<option selected>One</option>"
    )


def test_post_handler_node_text_context_includes_node_and_ancestors():
    """封装节点应延迟记录 text 所属节点和祖先标签。"""
    root = parse_html_fragment("<pre><span>E_j</span></pre>")
    span = root.xpath(".//span")[0]
    post_node = PostHandlerNode(span)

    assert post_node.tag_name == "span"
    assert post_node.is_text_in_tag_context({"span"})
    assert post_node.is_text_in_tag_context({"pre"})
    assert not post_node.is_text_in_tag_context({"code"})


def test_post_handler_node_tail_context_uses_parent_not_current_node():
    """tail 文本属于父节点上下文，不能误用当前节点标签。"""
    root = parse_html_fragment("<p><span>E_j</span> tail</p>")
    span = root.xpath(".//span")[0]
    post_node = PostHandlerNode(span)

    assert post_node.is_tail_in_tag_context({"p"})
    assert not post_node.is_tail_in_tag_context({"span"})


def test_post_handler_node_context_tags_are_cached():
    """首次获取后的上下文标签应复用缓存，避免重复遍历父链。"""
    root = parse_html_fragment("<pre><span>E_j</span></pre>")
    span = root.xpath(".//span")[0]
    post_node = PostHandlerNode(span)

    first_context = post_node.text_context_tag_names
    span.getparent().remove(span)

    assert post_node.text_context_tag_names is first_context
    assert post_node.is_text_in_tag_context({"pre"})
