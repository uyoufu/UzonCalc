"""Render archive entry metadata as fixed-size PNG thumbnail images."""

from io import BytesIO
import os
from pathlib import Path
import warnings

from PIL import Image, ImageDraw, ImageFont

from .cli_archive_analysis import ArchiveEntryPreview


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


def _wrap_title_text(
    draw: ImageDraw.ImageDraw,
    title: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    """Wrap a title by measured glyph width for both CJK and Latin text.

    Args:
        draw: Pillow drawing context used for text measurement.
        title: Report title to wrap.
        font: Title font.
        max_width: Maximum line width in pixels.
        max_lines: Maximum number of returned lines.

    Returns:
        One or more display lines, with the last line ellipsized when needed.

    Raises:
        None.
    """
    lines: list[str] = []
    current = ""
    normalized_title = " ".join(title.split())
    was_truncated = False
    for character in normalized_title:
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
    draw.rectangle((0, 0, THUMBNAIL_WIDTH, 12), fill="#16835F")
    draw.text((72, 48), "UzonCalc", font=metadata_font, fill="#16835F")

    title_lines = _wrap_title_text(draw, preview.title, title_font, 1136, 2)
    title_y = 82
    for line in title_lines:
        draw.text((72, title_y), line, font=title_font, fill="#17211D")
        title_y += 62

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
    for line_number, source_line in enumerate(preview.source_excerpt.splitlines(), 1):
        line_y = code_y + (line_number - 1) * line_height
        draw.text(
            (panel_left + 28, line_y),
            f"{line_number:>2}",
            font=code_font,
            fill="#73817B",
        )
        display_line = _ellipsize_text(draw, source_line, code_font, code_width)
        draw.text((code_x, line_y), display_line, font=code_font, fill="#E8EEEB")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True, compress_level=9)
    return output.getvalue()
