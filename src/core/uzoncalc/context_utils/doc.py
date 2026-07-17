import hashlib
import html
import json
import os
from typing import Any
from ..globals import get_current_instance

# 环境变量名，与 cli.py 保持一致
_CLI_MODE_ENV = "UZONCALC_CLI_MODE"


def _is_cli_mode() -> bool:
    """是否处于 CLI 模式（由 uzoncalc CLI 启动时设置）"""
    return os.environ.get(_CLI_MODE_ENV) == "1"


def doc_title(title: str):
    """
    设置页面标题
    :param title: 页面标题
    """
    ctx = get_current_instance()
    ctx.options.doc_title = title


def font_family(family: str):
    """
    设置页面字体
    :param family: 字体名称，如 'Arial', 'Times New Roman' 等
    """
    ctx = get_current_instance()
    ctx.options.page_info.font_family = family


def page_size(size: str):
    """
    设置页面大小
    :param size: 页面大小，如 'A4', 'Letter' 等
    """
    ctx = get_current_instance()
    ctx.options.page_info.size = size


def head(tag: str, attrs: dict[str, str]):
    """
    添加自定义 HTML 头部内容
    内部会自动去重，确保相同内容只添加一次。
    :param tag: 标签名称，如 'meta', 'link', 'style' 等
    :param attrs: 属性字典，键值对形式
    """
    ctx = get_current_instance()

    if not tag or not isinstance(attrs, dict):
        raise ValueError(
            "Invalid head content: tag must be a non-empty string and attrs must be a dictionary"
        )

    normalized_tag, normalized_attrs = _normalize_head(tag, attrs)
    head_hash = _compute_head_hash(normalized_tag, normalized_attrs)
    ctx.options.heads[head_hash] = (normalized_tag, normalized_attrs)


def _normalize_head(tag: str, attrs: dict[str, str]) -> tuple[str, dict[str, str]]:
    """标准化 head 标签，保证相同内容生成相同 hash。"""
    normalized_tag = tag.strip().lower()
    normalized_attrs = {
        attr_name.strip().lower(): str(attr_value)
        for attr_name, attr_value in sorted(
            attrs.items(), key=lambda item: item[0].lower()
        )
        if attr_value is not None
    }
    return normalized_tag, normalized_attrs


def _compute_head_hash(tag: str, attrs: dict[str, str]) -> str:
    """计算 head 标签的稳定 hash。"""
    normalized_tag, normalized_attrs = _normalize_head(tag, attrs)
    payload = json.dumps({"tag": normalized_tag, "normalized_attrs": normalized_attrs})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def style(name: str, value: dict[str, Any]):
    """
    设置页面样式
    :param name: 样式名称
    :param value: 样式内容，字典形式
    """
    ctx = get_current_instance()
    ctx.options.styles[name] = dict(value)


def toc(title: str = "Table of Contents"):
    """
    插入目录
    :param title: 目录标题
    """
    ctx = get_current_instance()
    safe_title = html.escape(title, quote=True)
    # 在当前位置插入目录占位符，JavaScript 会自动填充内容
    toc_html = f"""
<div id="toc" data-toc-title="{safe_title}" style="page-break-before:always;page-break-after:always;">
    <div class="text-center text-2xl font-semibold">{safe_title}</div>
    <div id='toc-container'></div>
</div>
"""
    ctx.append_content(toc_html)


__all__ = ["doc_title", "font_family", "head", "page_size", "style", "toc"]
