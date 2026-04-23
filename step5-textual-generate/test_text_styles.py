"""
Compare 3 text overlay styles on the same sticker:
1. Speech bubble (comic style)
2. Arc banner at bottom
3. Improved current style (better font + shadow + color)
"""

import math
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
STICKER_DIR = PROJECT_ROOT / "sticker_results"
OUTPUT_DIR = SCRIPT_DIR / "style_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_SIZE = (512, 512)

# Use a few test images
TEST_IMAGES = [
    ("cartoon", "cartoon_animal_2.png", "Feline Fine!"),
    ("cartoon", "cartoon_animal_4.png", "Bearly Awake!"),
    ("flat", "flat_animal_1.png", "Stealth Mode!"),
    ("watercolor", "watercolor_animal_5.png", "Chill Vibes"),
]


def get_font(font_name, size):
    candidates = [font_name] if font_name else []
    candidates += ["arialbd.ttf", "arial.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def get_dominant_color(img):
    small = img.copy().resize((50, 50))
    pixels = list(small.convert("RGB").getdata())
    filtered = []
    for r, g, b in pixels:
        brightness = (r + g + b) / 3
        saturation = max(r, g, b) - min(r, g, b)
        if brightness < 40 or brightness > 220:
            continue
        if saturation < 20:
            continue
        filtered.append((r // 32 * 32, g // 32 * 32, b // 32 * 32))
    if not filtered:
        return (80, 140, 200)
    counter = Counter(filtered)
    return counter.most_common(1)[0][0]


# ============================================================
# Style 1: Speech Bubble
# ============================================================
def overlay_speech_bubble(img, caption):
    img = img.convert("RGBA")
    w, h = img.size
    font_size = int(h * 0.055)
    font = get_font("comicbd.ttf", font_size)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Measure text
    bbox = draw.textbbox((0, 0), caption, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Bubble dimensions
    pad_x, pad_y = 18, 12
    bw = tw + pad_x * 2
    bh = th + pad_y * 2
    bx = (w - bw) // 2
    by = h - bh - int(h * 0.06)

    # Draw bubble (rounded rectangle)
    radius = 16
    draw.rounded_rectangle(
        [bx, by, bx + bw, by + bh],
        radius=radius,
        fill=(255, 255, 255, 230),
        outline=(60, 60, 60, 255),
        width=2,
    )

    # Draw tail (triangle pointing up to the character)
    tail_cx = w // 2
    tail_points = [
        (tail_cx - 8, by),       # left base on bubble
        (tail_cx + 8, by),       # right base on bubble
        (tail_cx - 20, by - 18), # tip pointing up
    ]
    draw.polygon(tail_points, fill=(255, 255, 255, 230), outline=(60, 60, 60, 255))
    # Cover the outline inside the bubble
    draw.rectangle([tail_cx - 9, by - 1, tail_cx + 9, by + 2], fill=(255, 255, 255, 230))

    # Draw text
    tx = bx + pad_x
    ty = by + pad_y - 2
    draw.text((tx, ty), caption, font=font, fill=(50, 50, 50, 255))

    return Image.alpha_composite(img, overlay).convert("RGB")


# ============================================================
# Style 2: Arc Banner at bottom
# ============================================================
def overlay_arc_banner(img, caption):
    img = img.convert("RGBA")
    w, h = img.size
    font_size = int(h * 0.06)
    font = get_font("arialbd.ttf", font_size)

    dominant = get_dominant_color(img)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Measure text
    bbox = draw.textbbox((0, 0), caption, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Banner dimensions
    pad_x, pad_y = 24, 10
    bw = tw + pad_x * 2
    bh = th + pad_y * 2
    bx = (w - bw) // 2
    by = h - bh - int(h * 0.02)

    # Draw arc-shaped banner (pill shape)
    radius = bh // 2
    # Banner color based on dominant with some transparency
    banner_color = (*dominant, 210)
    draw.rounded_rectangle(
        [bx, by, bx + bw, by + bh],
        radius=radius,
        fill=banner_color,
    )

    # Draw text centered in banner
    tx = (w - tw) // 2
    ty = by + pad_y - 1
    draw.text((tx, ty), caption, font=font,
              fill=(255, 255, 255, 255),
              stroke_fill=(0, 0, 0, 100),
              stroke_width=1)

    return Image.alpha_composite(img, overlay).convert("RGB")


# ============================================================
# Style 3: Improved overlay (soft glow + better styling)
# ============================================================
def overlay_improved(img, caption):
    img = img.convert("RGBA")
    w, h = img.size
    font_size = int(h * 0.065)
    font = get_font("arialbd.ttf", font_size)

    # Measure text
    tmp = ImageDraw.Draw(img)
    bbox = tmp.textbbox((0, 0), caption, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = h - th - int(h * 0.045)

    # Create soft glow behind text (dark semi-transparent blur)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    # Draw dark background wider area
    glow_draw.rounded_rectangle(
        [x - 12, y - 6, x + tw + 12, y + th + 6],
        radius=10,
        fill=(0, 0, 0, 100),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=8))

    # Composite glow
    img = Image.alpha_composite(img, glow)

    # Draw text with stroke
    draw = ImageDraw.Draw(img)
    draw.text((x, y), caption, font=font,
              fill=(255, 255, 255, 255),
              stroke_fill=(40, 40, 40, 255),
              stroke_width=2)

    return img.convert("RGB")


# ============================================================
# Run all 3 styles on test images
# ============================================================
STYLES = {
    "bubble": overlay_speech_bubble,
    "banner": overlay_arc_banner,
    "improved": overlay_improved,
}

print("=" * 55)
print("Text Style Comparison")
print("=" * 55)

for style_name, filename, caption in TEST_IMAGES:
    img_path = STICKER_DIR / style_name / filename

    if not img_path.exists():
        print(f"  Skip: {filename}")
        continue

    base = Path(filename).stem

    for sname, func in STYLES.items():
        img = Image.open(img_path).convert("RGB").resize(OUTPUT_SIZE)
        result = func(img, caption)
        out_path = OUTPUT_DIR / f"{base}_{sname}.png"
        result.save(out_path, "PNG")
        print(f"  ✅ {base} [{sname:8s}] \"{caption}\"")

print(f"\nDone! Check: {OUTPUT_DIR}")
print(f"Total: {len(TEST_IMAGES) * len(STYLES)} images")
