from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple
import math

CAPTION_STYLES = {
    "hormozi": {
        "text_color": (255, 255, 255),
        "highlight_color": (250, 204, 21), # Vibrant Yellow
        "outline_color": (0, 0, 0),
        "bg_box": (0, 0, 0, 180),
        "font_size": 52,
        "uppercase": True
    },
    "cyber_neon": {
        "text_color": (241, 245, 249),
        "highlight_color": (6, 182, 212), # Cyan Glow
        "outline_color": (15, 23, 42),
        "bg_box": (15, 23, 42, 210),
        "font_size": 48,
        "uppercase": True
    },
    "minimal_clean": {
        "text_color": (255, 255, 255),
        "highlight_color": (129, 140, 248), # Indigo Soft
        "outline_color": (0, 0, 0),
        "bg_box": (15, 17, 23, 160),
        "font_size": 46,
        "uppercase": False
    },
    "gold_luxury": {
        "text_color": (248, 250, 252),
        "highlight_color": (245, 158, 11), # Warm Gold
        "outline_color": (20, 10, 0),
        "bg_box": (20, 15, 10, 190),
        "font_size": 48,
        "uppercase": True
    }
}

CAPTION_POSITIONS = {
    "top": 420,
    "center": 960,
    "bottom": 1420
}

def get_caption_font(size=48, bold=True):
    candidates = [
        "C:/Windows/Fonts/impact.ttf" if bold else "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def split_text_into_caption_chunks(text: str, max_words: int = 5) -> List[List[str]]:
    """
    Split narration text into 3-5 word high-impact subtitle chunks for short-form video.
    """
    words = text.strip().split()
    if not words:
        return []
    chunks = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= max_words or w.endswith(('.', '!', '?', ',')):
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks

def draw_animated_caption_box(
    img: Image.Image,
    words: List[str],
    active_word_index: int,
    style_name: str = "hormozi",
    position_name: str = "bottom",
    width: int = 1080
):
    """
    Draws modern animated captions onto the PIL image canvas with word highlighting.
    """
    if not words:
        return

    style_cfg = CAPTION_STYLES.get(style_name.lower(), CAPTION_STYLES["hormozi"])
    font = get_caption_font(style_cfg["font_size"], bold=True)
    draw = ImageDraw.Draw(img, "RGBA")

    display_words = [w.upper() if style_cfg["uppercase"] else w for w in words]
    full_line = " ".join(display_words)

    # Compute bounding box of entire caption line
    bbox = draw.textbbox((0, 0), full_line, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Calculate Position Y
    target_center_y = CAPTION_POSITIONS.get(position_name.lower(), CAPTION_POSITIONS["bottom"])
    top_y = target_center_y - (text_h + 30) // 2
    left_x = (width - text_w) / 2

    # Draw rounded dark backdrop container
    pad_x = 28
    pad_y = 16
    box_rect = [
        left_x - pad_x,
        top_y - pad_y,
        left_x + text_w + pad_x,
        top_y + text_h + pad_y
    ]
    draw.rounded_rectangle(box_rect, radius=18, fill=style_cfg["bg_box"], outline=style_cfg["highlight_color"], width=2)

    # Render each word with individual highlight timing
    cur_x = left_x
    space_w = draw.textbbox((0, 0), " ", font=font)[2] - draw.textbbox((0, 0), " ", font=font)[0]

    for idx, w in enumerate(display_words):
        w_bbox = draw.textbbox((0, 0), w, font=font)
        w_w = w_bbox[2] - w_bbox[0]

        is_active = (idx == active_word_index)
        col = style_cfg["highlight_color"] if is_active else style_cfg["text_color"]

        # Black outline / drop shadow for ultra-high contrast readability
        outline_col = style_cfg["outline_color"]
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2)]:
            draw.text((cur_x + ox, top_y + oy), w, font=font, fill=outline_col)

        # Active word pop highlight
        if is_active:
            # Highlight pill underline or bright glow
            draw.text((cur_x, top_y), w, font=font, fill=col)
        else:
            draw.text((cur_x, top_y), w, font=font, fill=col)

        cur_x += w_w + space_w
