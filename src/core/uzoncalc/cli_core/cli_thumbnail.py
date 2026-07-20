"""Render archive entry metadata as fixed-size PNG thumbnail images."""

from collections.abc import Mapping
from dataclasses import replace
from io import BytesIO
import os
from pathlib import Path
import tempfile
from typing import Any
import warnings

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
)

from .cli_archive_analysis import ArchiveEntryPreview, analyze_archive_script


THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720
_TITLE_FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "msyh.ttc",
    "simhei.ttf",
    "DejaVuSans.ttf",
)
_CODE_FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansMonoCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "msyh.ttc",
    "consola.ttf",
    "DejaVuSansMono.ttf",
)
_CODE_COLOR_DEFAULT = "#E8EEEB"
_CODE_COLOR_COMMENT = "#73817B"
_CODE_COLOR_KEYWORD = "#FFCB6B"
_CODE_COLOR_STRING = "#C3E88D"
_CODE_COLOR_NUMBER = "#F78C6C"
_CODE_COLOR_NAME = "#82AAFF"
_CODE_COLOR_OPERATOR = "#89DDFF"


def _resolve_font_source(candidates: tuple[str, ...], font_role: str) -> str | None:
    """Resolve the first usable system font from platform-aware candidates.

    Args:
        candidates: Absolute paths or font filenames in preference order.
        font_role: Human-readable role included in fallback warnings.

    Returns:
        Usable path or font filename, otherwise ``None``.

    Raises:
        None.
    """
    windows_font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for candidate in candidates:
        paths = (candidate, str(windows_font_dir / Path(candidate).name))
        for font_path in paths:
            try:
                ImageFont.truetype(font_path, 16)
            except OSError:
                continue
            return font_path
    warnings.warn(
        f"未找到可用的{font_role}系统字体，缩略图将使用 Pillow 默认字体",
        RuntimeWarning,
        stacklevel=2,
    )
    return None


def _load_thumbnail_font(
    font_source: str | None,
    size: int,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a resolved font at one thumbnail size.

    Args:
        font_source: Resolved font path or filename, if available.
        size: Requested font size in pixels.

    Returns:
        Pillow font object suitable for drawing.

    Raises:
        OSError: When a previously resolved font can no longer be opened.
    """
    if font_source is not None:
        return ImageFont.truetype(font_source, size)
    return ImageFont.load_default(size=size)


def _ellipsize_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> str:
    """Shorten one text line until it fits the requested pixel width.

    Args:
        draw: Pillow drawing context used for text measurement.
        text: Text line to fit.
        font: Font used for both measurement and later rendering.
        max_width: Maximum allowed line width in pixels.

    Returns:
        Original text when it fits, otherwise a shortened line ending in dots.

    Raises:
        None.
    """
    if draw.textlength(text, font=font) <= max_width:
        return text
    suffix = "..."
    shortened = text
    while shortened and draw.textlength(shortened + suffix, font=font) > max_width:
        shortened = shortened[:-1]
    return shortened.rstrip() + suffix


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    """Wrap text by measured glyph width for both CJK and Latin text.

    Args:
        draw: Pillow drawing context used for text measurement.
        text: Report title or description to wrap.
        font: Font used to measure the text.
        max_width: Maximum line width in pixels.
        max_lines: Maximum number of returned lines.

    Returns:
        One or more display lines, with the last line ellipsized when needed.

    Raises:
        None.
    """
    lines: list[str] = []
    current = ""
    normalized_text = " ".join(text.split())
    was_truncated = False
    for character in normalized_text:
        candidate = current + character
        if not current or draw.textlength(candidate, font=font) <= max_width:
            current = candidate
            continue
        lines.append(current.rstrip())
        current = character.lstrip()
        if len(lines) == max_lines:
            was_truncated = True
            break
    else:
        if current:
            lines.append(current.rstrip())

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        was_truncated = True
    if was_truncated and lines:
        lines[-1] = _ellipsize_text(draw, lines[-1] + "...", font, max_width)
    return lines or [""]


def _python_token_color(token_type: Any) -> str:
    """Resolve one Pygments Python token to the thumbnail code palette.

    Args:
        token_type: Pygments token category returned by the Python lexer.

    Returns:
        Hexadecimal RGB color for the token category.

    Raises:
        None.
    """
    if token_type in Comment:
        return _CODE_COLOR_COMMENT
    if token_type in Keyword:
        return _CODE_COLOR_KEYWORD
    if token_type in String:
        return _CODE_COLOR_STRING
    if token_type in Number:
        return _CODE_COLOR_NUMBER
    if (
        token_type in Name.Function
        or token_type in Name.Class
        or token_type in Name.Decorator
    ):
        return _CODE_COLOR_NAME
    if token_type in Operator or token_type in Punctuation:
        return _CODE_COLOR_OPERATOR
    return _CODE_COLOR_DEFAULT


def _highlight_python_source(source: str) -> list[list[tuple[str, str]]]:
    """Split Python source into lines of colored Pygments token segments.

    Args:
        source: Python source excerpt to highlight without executing it.

    Returns:
        Lines containing ordered ``(text, color)`` segments.

    Raises:
        None.
    """
    highlighted_lines: list[list[tuple[str, str]]] = [[]]
    lexer = PythonLexer(stripnl=False, ensurenl=False)
    for token_type, token_text in lex(source, lexer):
        color = _python_token_color(token_type)
        chunks = token_text.split("\n")
        for index, chunk in enumerate(chunks):
            if chunk:
                highlighted_lines[-1].append((chunk, color))
            if index < len(chunks) - 1:
                highlighted_lines.append([])
    return highlighted_lines


def _fit_code_segments(
    draw: ImageDraw.ImageDraw,
    segments: list[tuple[str, str]],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[tuple[str, str]]:
    """Trim highlighted code segments to one measured display line.

    Args:
        draw: Pillow drawing context used for text measurement.
        segments: Ordered highlighted text and color pairs.
        font: Code font used for measurement and rendering.
        max_width: Maximum display width in pixels.

    Returns:
        Original segments when they fit, otherwise a truncated colored prefix
        followed by an ellipsis.

    Raises:
        None.
    """
    if draw.textlength("".join(text for text, _ in segments), font=font) <= max_width:
        return segments

    suffix = "..."
    available_width = max_width - draw.textlength(suffix, font=font)
    fitted_segments: list[tuple[str, str]] = []
    used_width = 0.0
    for segment_text, color in segments:
        fitted_text = ""
        for character in segment_text:
            character_width = draw.textlength(character, font=font)
            if used_width + character_width > available_width:
                if fitted_text:
                    fitted_segments.append((fitted_text, color))
                fitted_segments.append((suffix, _CODE_COLOR_DEFAULT))
                return fitted_segments
            fitted_text += character
            used_width += character_width
        if fitted_text:
            fitted_segments.append((fitted_text, color))
    fitted_segments.append((suffix, _CODE_COLOR_DEFAULT))
    return fitted_segments


def render_archive_thumbnail(preview: ArchiveEntryPreview) -> bytes:
    """Render a deterministic 1280 by 720 report thumbnail as PNG bytes.

    Args:
        preview: Static title, entry name, and source excerpt to display.

    Returns:
        Complete PNG image bytes ending in an ``IEND`` chunk.

    Raises:
        OSError: When Pillow cannot load a selected font or encode the image.
    """
    title_source = _resolve_font_source(_TITLE_FONT_CANDIDATES, "标题")
    code_source = _resolve_font_source(_CODE_FONT_CANDIDATES, "代码")
    title_font = _load_thumbnail_font(title_source, 52)
    metadata_font = _load_thumbnail_font(title_source, 22)
    code_font = _load_thumbnail_font(code_source, 24)

    image = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), "#F3F5F4")
    draw = ImageDraw.Draw(image)
    draw.text((72, 48), "UzonCalc", font=metadata_font, fill="#16835F")

    title_lines = _wrap_text(
        draw,
        preview.title,
        title_font,
        1136,
        1 if preview.description else 2,
    )
    title_y = 82
    for line in title_lines:
        draw.text((72, title_y), line, font=title_font, fill="#17211D")
        title_y += 62
    if preview.description:
        description_y = title_y + 4
        for line in _wrap_text(
            draw, preview.description, metadata_font, 1136, 2
        ):
            draw.text((72, description_y), line, font=metadata_font, fill="#5A6862")
            description_y += 28

    panel_left = 64
    panel_top = 224
    panel_right = THUMBNAIL_WIDTH - 64
    panel_bottom = THUMBNAIL_HEIGHT - 52
    draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=8,
        fill="#202724",
    )
    draw.text(
        (panel_left + 28, panel_top + 20),
        f"entry: {preview.entry_name}",
        font=metadata_font,
        fill="#8FD6BC",
    )
    draw.line(
        (panel_left + 24, panel_top + 58, panel_right - 24, panel_top + 58),
        fill="#35413C",
        width=1,
    )

    code_x = panel_left + 86
    code_y = panel_top + 76
    code_width = panel_right - code_x - 28
    line_height = 26
    highlighted_lines = _highlight_python_source(preview.source_excerpt)
    for line_number, source_segments in enumerate(highlighted_lines, 1):
        line_y = code_y + (line_number - 1) * line_height
        draw.text(
            (panel_left + 28, line_y),
            f"{line_number:>2}",
            font=code_font,
            fill="#73817B",
        )
        display_segments = _fit_code_segments(
            draw, source_segments, code_font, code_width
        )
        segment_x = code_x
        for segment_text, color in display_segments:
            draw.text((segment_x, line_y), segment_text, font=code_font, fill=color)
            segment_x += draw.textlength(segment_text, font=code_font)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True, compress_level=9)
    return output.getvalue()


def render_workspace_archive_thumbnail(
    files: Mapping[str, bytes],
    entry_path: str,
    *,
    title: str | None = None,
    description: str | None = None,
) -> tuple[bytes, str | None]:
    """Render a thumbnail and resolve the automatic entry for workspace files.

    Args:
        files: Workspace files keyed by normalized report-relative paths.
        entry_path: Python entry path declared by ``calcbook.json``.
        title: Optional report title overriding the statically analyzed title.
        description: Optional report description displayed below the title.

    Returns:
        PNG thumbnail bytes and the entry name to pass to ``view``. The entry name
        is ``None`` when the script owns an explicit ``__main__`` guard.

    Raises:
        ValueError: If the entry is missing, invalid UTF-8, lacks ``@uzon_calc``,
            or declares ambiguous entries without an explicit main guard.
        OSError: If temporary source or thumbnail output cannot be written.
        SyntaxError: If the entry source is invalid Python.
    """
    source_bytes = files.get(entry_path)
    if source_bytes is None:
        raise ValueError("工作区入口文件不存在")
    try:
        source = source_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("工作区入口文件不是 UTF-8 Python 源码") from error
    with tempfile.TemporaryDirectory(prefix="uzoncalc-thumbnail-") as temp_dir:
        script_path = Path(temp_dir) / Path(entry_path).name
        script_path.write_text(source, encoding="utf-8")
        analysis = analyze_archive_script(script_path)
    first_entry_name = next(iter(analysis.entry_names), None)
    if first_entry_name is None or analysis.preview is None:
        raise ValueError("工作区入口未找到 @uzon_calc 装饰器")
    if not analysis.has_main_guard and len(analysis.entry_names) > 1:
        raise ValueError("工作区入口包含多个 @uzon_calc，请添加显式 __main__ 入口")
    auto_view_entry = None if analysis.has_main_guard else first_entry_name
    preview = replace(
        analysis.preview,
        title=title.strip() if title and title.strip() else analysis.preview.title,
        description=(" ".join(description.split()) if description else None),
    )
    return render_archive_thumbnail(preview), auto_view_entry
