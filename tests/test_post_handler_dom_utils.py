from lxml import etree

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


def test_post_handler_node_tail_context_uses_text_context_slice():
    """tail 上下文应从已缓存 text 上下文切片派生。"""
    root = parse_html_fragment("<p><span>E_j</span> tail</p>")
    span = root.xpath(".//span")[0]
    post_node = PostHandlerNode(span)

    text_context = post_node.text_context_tag_names
    span.getparent().remove(span)

    assert text_context[0] == "span"
    assert post_node.tail_context_tag_names == text_context[1:]
    assert post_node.is_tail_in_tag_context({"p"})


def test_post_handler_node_tail_context_reuses_text_context_for_non_element_node():
    """非元素节点没有自身 tag，tail 上下文可直接复用 text 上下文。"""
    root = parse_html_fragment("<p><!--marker--> tail</p>")
    comment = root.xpath(".//comment()")[0]
    post_node = PostHandlerNode(comment)

    text_context = post_node.text_context_tag_names

    assert post_node.tag_name == ""
    assert post_node.tail_context_tag_names is text_context
    assert post_node.is_tail_in_tag_context({"p"})


def test_post_handler_node_root_tail_context_is_empty():
    """临时根节点的 tail 上下文应为空。"""
    root = parse_html_fragment("<p>x</p>")
    post_node = PostHandlerNode(root)

    assert post_node.tail_context_tag_names == ()


def test_post_handler_node_replaces_text_with_parts_before_children():
    """文本片段替换应保留既有子节点顺序。"""
    root = parse_html_fragment("<p>x<span>child</span></p>")
    paragraph = root.xpath(".//p")[0]
    emphasis = etree.Element("em")
    emphasis.text = "y"

    PostHandlerNode(paragraph).replace_text_with_parts(["a", emphasis, "b"])

    assert serialize_html_fragment(root) == "<p>a<em>y</em>b<span>child</span></p>"


def test_post_handler_node_replaces_tail_with_parts_after_node():
    """tail 片段替换应插入到当前节点之后。"""
    root = parse_html_fragment("<p><span>x</span> old</p>")
    span = root.xpath(".//span")[0]
    emphasis = etree.Element("em")
    emphasis.text = "y"

    PostHandlerNode(span).replace_tail_with_parts([" a", emphasis, " b"])

    assert serialize_html_fragment(root) == "<p><span>x</span> a<em>y</em> b</p>"
