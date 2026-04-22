"""
Test: Style-matched text overlay.
- Flat: bold clean font, color extracted from image
- Cartoon: bubbly font with colored outline
- Watercolor: soft shadow, script-like font
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat
from collections import Counter


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
STICKER_DIR = PROJECT_ROOT / "sticker_results"
OUTPUT_DIR = SCRIPT_DIR / "styled_test_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_SIZE = (512, 512)

# Load VLM captions
with open(SCRIPT_DIR / "text_captions_vlm.json", "r", encoding="utf-8") as f:
    vlm_data = json.load(f)
caption_map = {item["file_name"]: item["caption"] for item in vlm_data}


def get_font(font_name, size):
    """Try to load a font, fallback to default."""
    candidates = [font_name] if font_name else []
    candidates += ["arialbd.ttf", "arial.ttf", "segoeui.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# Windows font map per style
STYLE_FONTS = {
    "flat": "arialbd.ttf",        # Arial Bold - clean & modern
    "cartoon": "comicbd.ttf",      # Comic Sans Bold - bubbly cartoon feel
    "watercolor": "segoesc.ttf",   # Segoe Script - handwritten feel
}


def get_dominant_color(img, exclude_dark=True, exclude_light=True):
    """Extract the most prominent color from the image (not too dark, not too white)."""
    small = img.resize((50, 50))
    pixels = list(small.getdata())

    filtered = []
    for r, g, b in pixels:
        brightness = (r + g + b) / 3
        saturation = max(r, g, b) - min(r, g, b)
        if exclude_dark and brightness < 40:
            continue
        if exclude_light and brightness > 220:
            continue
        if saturation < 20:  # skip grays
            continue
        # Quantize to reduce variations
        filtered.append((r // 32 * 32, g // 32 * 32, b // 32 * 32))

    if not filtered:
        return (100, 150, 200)  # fallback blue

    counter = Counter(filtered)
    dominant = counter.most_common(1)[0][0]
    # Boost saturation a bit for text visibility
    r, g, b = dominant
    return (min(r + 30, 255), min(g + 30, 255), min(b + 30, 255))


def get_local_bg_brightness(img, x, y, tw, th):
    """Sample the average brightness of the image in the text area."""
    w, h = img.size
    left = max(0, x - 10)
    top = max(0, y - 5)
    right = min(w, x + tw + 10)
    bottom = min(h, y + th + 5)
    region = img.crop((left, top, right, bottom))
    stat = ImageStat.Stat(region)
    return sum(stat.mean[:3]) / 3  # average brightness


def ensure_contrast(fill_color, stroke_color, bg_brightness):
    """Adjust fill and stroke colors to ensure readability against local background."""
    fill_r, fill_g, fill_b = fill_color
    fill_brightness = (fill_r + fill_g + fill_b) / 3

    # If fill is too close to background, flip to high-contrast
    if abs(fill_brightness - bg_brightness) < 60:
        if bg_brightness > 128:
            # Dark background area → use white fill, dark stroke
            return (255, 255, 255), (30, 30, 30)
        else:
            # Light background area → use dark fill, white stroke
            return (30, 30, 30), (255, 255, 255)

    # Also make sure stroke contrasts with fill
    stroke_brightness = sum(stroke_color) / 3
    if abs(stroke_brightness - fill_brightness) < 80:
        if fill_brightness > 128:
            stroke_color = (30, 30, 30)
        else:
            stroke_color = (255, 255, 255)

    return fill_color, stroke_color


def overlay_flat(img, caption):
    """Flat style: clean bold text with subtle shadow, color from image."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    font_size = int(h * 0.075)
    font = get_font("arialbd.ttf", font_size)

    bbox = draw.textbbox((0, 0), caption, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = h - th - int(h * 0.05)

    dominant = get_dominant_color(img)
    bg_bright = get_local_bg_brightness(img, x, y, tw, th)
    fill_color, stroke_color = ensure_contrast(dominant, (255, 255, 255), bg_bright)

    # Shadow
    draw.text((x + 2, y + 2), caption, font=font, fill=(0, 0, 0, 180))
    # Main text
    draw.text((x, y), caption, font=font, fill=fill_color,
              stroke_fill=stroke_color, stroke_width=2)
    return img


def overlay_cartoon(img, caption):
    """Cartoon style: bubbly font, colored outline, playful positioning."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    font_size = int(h * 0.08)
    font = get_font("comicbd.ttf", font_size)

    bbox = draw.textbbox((0, 0), caption, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = h - th - int(h * 0.04)

    dominant = get_dominant_color(img)
    bg_bright = get_local_bg_brightness(img, x, y, tw, th)
    fill_color, stroke_color = ensure_contrast((255, 255, 255), dominant, bg_bright)

    # Thick colored outline + white fill (comic book style)
    draw.text((x, y), caption, font=font,
              fill=fill_color,
              stroke_fill=stroke_color,
              stroke_width=4)
    return img


def overlay_watercolor(img, caption):
    """Watercolor style: soft glow effect, script font, gentle colors."""
    w, h = img.size
    font_size = int(h * 0.07)
    font = get_font("segoesc.ttf", font_size)

    # Create text layer with glow
    txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    bbox = draw.textbbox((0, 0), caption, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = h - th - int(h * 0.05)

    dominant = get_dominant_color(img)
    dark = (max(dominant[0] - 60, 0), max(dominant[1] - 60, 0), max(dominant[2] - 60, 0))
    bg_bright = get_local_bg_brightness(img, x, y, tw, th)
    fill_color, stroke_color = ensure_contrast(dark, (255, 255, 255), bg_bright)

    # Glow layer (blurred text behind for soft background)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    # Glow color opposite to fill for visibility
    glow_fill = (255, 255, 255, 160) if sum(fill_color) < 384 else (0, 0, 0, 120)
    glow_draw.text((x, y), caption, font=font, fill=glow_fill)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=4))

    # Composite: glow + text
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, glow)
    draw2 = ImageDraw.Draw(img)
    draw2.text((x, y), caption, font=font, fill=fill_color,
               stroke_fill=stroke_color, stroke_width=1)
    return img.convert("RGB")


STYLE_OVERLAY = {
    "flat": overlay_flat,
    "cartoon": overlay_cartoon,
    "watercolor": overlay_watercolor,
}


print("=" * 55)
print("Styled Text Overlay Test (5 images x 3 styles)")
print("=" * 55)

for base_name, caption in caption_map.items():
    for style in ["flat", "cartoon", "watercolor"]:
        styled_name = f"{style}_{base_name}"
        # Prefer 4.19 version, fallback to original
        img_path = STICKER_DIR / f"{style} 4.19" / styled_name
        if not img_path.exists():
            img_path = STICKER_DIR / style / styled_name

        if not img_path.exists():
            print(f"  Skip: {styled_name}")
            continue

        img = Image.open(img_path).convert("RGB").resize(OUTPUT_SIZE)
        img = STYLE_OVERLAY[style](img, caption)

        out_path = OUTPUT_DIR / f"final_{styled_name}"
        img.save(out_path, "PNG")
        print(f"  ✅ [{style:10s}] {base_name} + \"{caption}\"")

print(f"\nDone! Check: {OUTPUT_DIR}")
