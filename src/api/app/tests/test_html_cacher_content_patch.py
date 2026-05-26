from pathlib import Path

from app.service.html_cache.html_cacher import HtmlCacher


def build_html(content: str, title: str = "报告") -> str:
    """构造带正文标记的测试 HTML"""
    return f"""
<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
  <div class="content">
    <!--CONTENT_START_MARK-->
    {content}
    <!--CONTENT_END_MARK-->
  </div>
</body>
</html>
"""


def test_build_content_patch_when_only_marked_content_changed(tmp_path: Path):
    """仅正文区域变化时返回可发送到 iframe 的内容补丁"""
    html_cacher = HtmlCacher()
    html_cacher.public_dir = tmp_path / "public"
    old_html_path = html_cacher.public_dir / "calcs" / "1" / "old.html"
    old_html_path.parent.mkdir(parents=True)
    old_html_path.write_text(build_html("<p>旧结果</p>"), encoding="utf-8")

    patch = html_cacher.build_content_patch(
        build_html("<p>新结果</p>"),
        "public/calcs/1/old.html",
        "public/calcs/1/new.html",
    )

    assert patch == "\n    <p>新结果</p>\n    "


def test_build_content_patch_returns_none_when_outer_html_changed(tmp_path: Path):
    """正文外结构变化时不能增量更新，避免样式和标题等信息不同步"""
    html_cacher = HtmlCacher()
    html_cacher.public_dir = tmp_path / "public"
    old_html_path = html_cacher.public_dir / "calcs" / "1" / "old.html"
    old_html_path.parent.mkdir(parents=True)
    old_html_path.write_text(build_html("<p>旧结果</p>", title="旧标题"), encoding="utf-8")

    patch = html_cacher.build_content_patch(
        build_html("<p>新结果</p>", title="新标题"),
        "public/calcs/1/old.html",
        "public/calcs/1/new.html",
    )

    assert patch is None


def test_build_content_patch_rejects_unsafe_previous_path(tmp_path: Path):
    """旧 HTML 路径越界时安全降级为完整 iframe 切换"""
    html_cacher = HtmlCacher()
    html_cacher.public_dir = tmp_path / "public"

    patch = html_cacher.build_content_patch(
        build_html("<p>新结果</p>"),
        "../private/old.html",
        "public/calcs/1/new.html",
    )

    assert patch is None
