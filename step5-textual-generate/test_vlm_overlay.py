"""Quick test: overlay VLM captions on 5 stickers to see the final effect."""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_DIR = PROJECT_ROOT / "sticker_results" / "flat"
OUTPUT_DIR = SCRIPT_DIR / "vlm_test_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load VLM captions
with open(SCRIPT_DIR / "text_captions_vlm.json", "r", encoding="utf-8") as f:
    vlm_data = json.load(f)
caption_map = {item["file_name"]: item["caption"] for item in vlm_data}

OUTPUT_SIZE = (512, 512)


def get_font(size):
    for font_name in ["arial.ttf", "Arial.ttf", "DejaVuSans-Bold.ttf", "Helvetica.ttf"]:
        try:
            return ImageFont.truetype(font_name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def overlay_text(img, caption):
    """Overlay caption on sticker - improved style without rectangle background."""
    draw = ImageDraw.Draw(img)
    w, h = img.size

    font_size = int(h * 0.07)
    font = get_font(font_size)

    # Measure text
    bbox = draw.textbbox((0, 0), caption, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Position: bottom center
    x = (w - tw) // 2
    y = h - th - int(h * 0.06)

    # Draw text with thick stroke (no rectangle background)
    draw.text(
        (x, y), caption, font=font,
        fill=(255, 255, 255),
        stroke_fill=(30, 30, 30),
        stroke_width=3,
    )
    return img


print("=" * 50)
print("VLM Caption Overlay Test")
print("=" * 50)

for base_name, caption in caption_map.items():
    flat_name = f"flat_{base_name}"
    img_path = INPUT_DIR / flat_name
    if not img_path.exists():
        print(f"  Skip: {flat_name} not found")
        continue

    img = Image.open(img_path).convert("RGB").resize(OUTPUT_SIZE)
    img = overlay_text(img, caption)

    out_path = OUTPUT_DIR / f"final_{flat_name}"
    img.save(out_path, "PNG")
    print(f"  ✅ {flat_name} + \"{caption}\" -> {out_path.name}")

print(f"\nDone! Check: {OUTPUT_DIR}")
