import base64
import io
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from django.conf import settings




FONT_MAP = {
    'Impact':      'Impact.ttf',
    'Arial Black': 'arialbd.ttf',
    'Comic Sans MS': 'comic.ttf',
    'Georgia':     'georgia.ttf',
}


SYSTEM_FONT_DIRS = [
    '/usr/share/fonts/truetype/',
    '/usr/share/fonts/',
    'C:/Windows/Fonts/',
    '/Library/Fonts/',
    '/System/Library/Fonts/',
]


def _find_font(font_name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Try to load a TrueType font by name.
    Falls back to PIL's built-in bitmap font if nothing is found.
    """
    filename = FONT_MAP.get(font_name, 'Impact.ttf')
    for font_dir in SYSTEM_FONT_DIRS:
        path = os.path.join(font_dir, filename)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()




def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines, current = [], ''
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or ['']


def _draw_text_on_image(
    draw:        ImageDraw.Draw,
    img_width:   int,
    img_height:  int,
    text:        str,
    position:    str,         
    font_name:   str,
    font_size:   int,
    fill_color:  str,
    stroke_color: str,
    stroke_width: int,
    is_bold:     bool,
    is_italic:   bool,
    is_uppercase: bool,
) -> None:
    """Draw meme text (with outline) on an ImageDraw context."""
    if not text.strip():
        return

    display_text = text.upper() if is_uppercase else text


    scaled_size = max(12, int(font_size * img_width / 600))
    font = _find_font(font_name, scaled_size)

    max_width  = int(img_width * 0.92)
    padding    = int(scaled_size * 0.4)
    line_height = int(scaled_size * 1.25)

    lines      = _wrap_text(display_text, font, max_width, draw)
    total_h    = len(lines) * line_height

    if position == 'top':
        y = padding
    else:
        y = img_height - total_h - padding

    x_center = img_width // 2

    for line in lines:
        if stroke_width > 0:

            offsets = [
                (-stroke_width, -stroke_width), (0, -stroke_width), (stroke_width, -stroke_width),
                (-stroke_width, 0),                                   (stroke_width, 0),
                (-stroke_width,  stroke_width), (0,  stroke_width), (stroke_width,  stroke_width),
            ]
            for dx, dy in offsets:
                draw.text(
                    (x_center + dx, y + dy),
                    line, font=font, fill=stroke_color, anchor='mt',
                )
        draw.text((x_center, y), line, font=font, fill=fill_color, anchor='mt')
        y += line_height




def generate_meme_from_upload(
    image_file,
    top_text:    str  = '',
    bottom_text: str  = '',
    font_name:   str  = 'Impact',
    font_size_top: int = 42,
    font_size_bot: int = 42,
    color_top:   str  = '#ffffff',
    color_bottom: str = '#ffffff',
    stroke_color_top: str = '#000000',
    stroke_color_bot: str = '#000000',
    stroke_width: int = 3,
    is_bold:     bool = True,
    is_italic:   bool = False,
    is_uppercase: bool = True,
) -> io.BytesIO:
    """
    Open an uploaded image, draw text overlays, and return a BytesIO PNG.
    """
    img = Image.open(image_file).convert('RGBA')


    max_w = getattr(settings, 'MEME_MAX_WIDTH',  1200)
    max_h = getattr(settings, 'MEME_MAX_HEIGHT', 1200)
    img.thumbnail((max_w, max_h), Image.LANCZOS)

    draw = ImageDraw.Draw(img)
    w, h = img.size

    if top_text:
        _draw_text_on_image(
            draw, w, h, top_text, 'top',
            font_name, font_size_top, color_top,
            stroke_color_top, stroke_width, is_bold, is_italic, is_uppercase,
        )
    if bottom_text:
        _draw_text_on_image(
            draw, w, h, bottom_text, 'bottom',
            font_name, font_size_bot, color_bottom,
            stroke_color_bot, stroke_width, is_bold, is_italic, is_uppercase,
        )


    output_img = img.convert('RGB')
    buffer = io.BytesIO()
    quality = getattr(settings, 'MEME_QUALITY', 90)
    output_img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer


def generate_meme_from_base64(
    data_url: str,
    **kwargs,
) -> io.BytesIO:

    if ',' not in data_url:
        raise ValueError("Invalid data URL format")
    header, b64_data = data_url.split(',', 1)
    image_bytes = base64.b64decode(b64_data)
    image_file  = io.BytesIO(image_bytes)
    return generate_meme_from_upload(image_file, **kwargs)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#rrggbb' to (r, g, b)."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))