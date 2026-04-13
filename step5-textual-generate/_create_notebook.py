"""Helper script to create final_sticker_pipeline.ipynb. Run once, then delete this file."""
import json, os

cells = []

def md(source):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": source.split("\n")})

def code(source):
    cells.append({"cell_type": "code", "metadata": {}, "source": source.split("\n"), "outputs": [], "execution_count": None})

# ── Cell 0: Title ──
md("""# Step 5: Final Sticker Productization — Optional Textual Generate

**STAT 6209 Topic 3 — Sticker Design Generation**

This notebook takes generated sticker images from upstream LoRA pipelines (flat, cartoon, watercolor),
overlays short text captions, and outputs production-ready final sticker images.

**Pipeline**: `input_stickers/<style>/` → load captions → overlay text → `output_final/<style>/`""")

# ── Cell 1: Configuration & Imports ──
md("## 1. Configuration & Imports")

code("""import os
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from IPython.display import display, HTML

# ====================== Path Configuration ======================
BASE_DIR = Path(".")
INPUT_DIR = BASE_DIR / "input_stickers"
OUTPUT_DIR = BASE_DIR / "output_final"
CAPTIONS_FILE = BASE_DIR / "text_captions.json"

# Sticker styles to process
STYLES = ["flat", "cartoon", "watercolor"]

# Supported image formats
SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# ====================== Text Overlay Settings ======================
TEXT_CONFIG = {
    "font_size_ratio": 0.08,      # font size as fraction of image height
    "margin_bottom_ratio": 0.05,  # bottom margin as fraction of image height
    "fill": (255, 255, 255),      # white text
    "stroke_fill": (30, 30, 30),  # dark stroke for readability
    "stroke_width": 2,
    "max_width_ratio": 0.9,       # max text width as fraction of image width
}

# ====================== Output Settings ======================
OUTPUT_SIZE = (512, 512)
OUTPUT_FORMAT = "PNG"

# Ensure output directories exist
for style in STYLES:
    (OUTPUT_DIR / style).mkdir(parents=True, exist_ok=True)

print("=== Configuration ===")
print(f"  Input directory:  {INPUT_DIR.resolve()}")
print(f"  Output directory: {OUTPUT_DIR.resolve()}")
print(f"  Captions file:    {CAPTIONS_FILE.resolve()}")
print(f"  Styles:           {STYLES}")
print(f"  Output size:      {OUTPUT_SIZE}")
print("Configuration loaded.")""")

# ── Cell 2: Load captions ──
md("## 2. Load Captions")

code("""def load_captions(captions_file: Path) -> dict:
    \"\"\"Load caption mapping from JSON file. Returns dict: filename -> caption.\"\"\"
    if not captions_file.exists():
        print(f"Warning: {captions_file} not found. Will use auto-generated captions.")
        return {}

    with open(captions_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    caption_map = {}
    for item in data:
        fname = item.get("file_name", "")
        caption = item.get("caption", "")
        if fname and caption:
            # Store with and without extension for flexible matching
            caption_map[fname] = caption
            caption_map[Path(fname).stem] = caption

    print(f"Loaded {len(data)} captions from {captions_file.name}")
    return caption_map


# Load
caption_map = load_captions(CAPTIONS_FILE)

# Preview first 5
for i, (k, v) in enumerate(caption_map.items()):
    if i >= 10:
        break
    print(f"  {k:25s} -> {v}")
print("  ...")""")

# ── Cell 3: Auto-generate default caption ──
md("## 3. Default Caption Generator")

code("""# Common animal keywords for fallback caption generation
ANIMAL_KEYWORDS = [
    "cat", "dog", "rabbit", "bunny", "bear", "fox", "panda", "lion",
    "tiger", "elephant", "giraffe", "monkey", "bird", "fish", "deer",
    "penguin", "cow", "turtle", "llama", "kangaroo", "capybara", "wolf",
    "koala", "owl", "hamster", "puppy", "kitten",
]

CUTE_PREFIXES = ["Cute", "Happy", "Little", "Sweet", "Lovely"]


def generate_default_caption(filename: str) -> str:
    \"\"\"Generate a short cute caption from the filename.

    Rules:
    - Extract animal name from filename if possible
    - Prepend a cute adjective
    - Fallback to 'Cute Sticker' if no animal found
    \"\"\"
    stem = Path(filename).stem.lower()
    # Remove common prefixes like 'animal_1', numbers, underscores
    cleaned = re.sub(r"[_\\-]", " ", stem)
    cleaned = re.sub(r"\\d+", "", cleaned).strip()

    for animal in ANIMAL_KEYWORDS:
        if animal in cleaned:
            import random
            prefix = random.choice(CUTE_PREFIXES)
            return f"{prefix} {animal.capitalize()}"

    return "Cute Sticker"


def get_caption(filename: str, caption_map: dict) -> str:
    \"\"\"Get caption for a file: lookup in map first, then auto-generate.\"\"\"
    stem = Path(filename).stem
    # Try exact match, then stem match
    if filename in caption_map:
        return caption_map[filename]
    if stem in caption_map:
        return caption_map[stem]
    return generate_default_caption(filename)


# Quick test
test_files = ["animal_1.jpeg", "cat_sticker_003.png", "unknown_image.jpg"]
for tf in test_files:
    print(f"  {tf:30s} -> \\"{get_caption(tf, caption_map)}\\"")""")

# ── Cell 4: Text overlay function ──
md("## 4. Text Overlay Function")

code("""def get_font(size: int):
    \"\"\"Try to load a nice font; fall back to PIL default.\"\"\"
    # Common font paths across platforms
    font_candidates = [
        "arial.ttf",
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
    ]
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except (IOError, OSError):
            continue
    # Fallback to default bitmap font
    print("  Warning: No TrueType font found, using default bitmap font.")
    return ImageFont.load_default()


def overlay_text_on_sticker(
    image: Image.Image,
    caption: str,
    config: dict = TEXT_CONFIG,
) -> Image.Image:
    \"\"\"Overlay caption text at the bottom-center of the sticker image.

    - White text with dark stroke for readability
    - Positioned at bottom with margin
    - Font size scales with image height
    - Does not obscure the main subject (text at bottom edge)
    \"\"\"
    img = image.copy().convert("RGBA")
    w, h = img.size

    # Calculate font size
    font_size = max(16, int(h * config["font_size_ratio"]))
    font = get_font(font_size)

    # Create a transparent overlay for the text
    txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Measure text
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # If text is too wide, reduce font size
    max_text_w = int(w * config["max_width_ratio"])
    while text_w > max_text_w and font_size > 12:
        font_size -= 1
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), caption, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

    # Position: bottom center with margin
    margin_bottom = int(h * config["margin_bottom_ratio"])
    x = (w - text_w) // 2
    y = h - text_h - margin_bottom

    # Draw semi-transparent background strip behind text for extra readability
    pad = 6
    draw.rounded_rectangle(
        [x - pad, y - pad, x + text_w + pad, y + text_h + pad],
        radius=8,
        fill=(0, 0, 0, 100),
    )

    # Draw text with stroke
    draw.text(
        (x, y),
        caption,
        font=font,
        fill=config["fill"],
        stroke_width=config["stroke_width"],
        stroke_fill=config["stroke_fill"],
    )

    # Composite
    result = Image.alpha_composite(img, txt_layer)
    return result.convert("RGB")


print("Text overlay function defined.")""")

# ── Cell 5: Batch processing ──
md("## 5. Batch Processing")

code("""def collect_images(input_dir: Path, styles: list) -> list:
    \"\"\"Scan input directories and collect all image paths with their style labels.\"\"\"
    images = []
    for style in styles:
        style_dir = input_dir / style
        if not style_dir.exists():
            print(f"  Warning: {style_dir} does not exist, skipping.")
            continue
        for f in sorted(style_dir.iterdir()):
            if f.suffix.lower() in SUPPORTED_EXTS:
                images.append({"path": f, "style": style, "filename": f.name})
    return images


def process_all_stickers(
    input_dir: Path = INPUT_DIR,
    output_dir: Path = OUTPUT_DIR,
    caption_map: dict = caption_map,
    styles: list = STYLES,
    output_size: tuple = OUTPUT_SIZE,
    config: dict = TEXT_CONFIG,
) -> list:
    \"\"\"Main batch processing function.

    For each sticker image:
    1. Load and resize to uniform size
    2. Look up or generate caption
    3. Overlay text
    4. Save to output directory
    \"\"\"
    images = collect_images(input_dir, styles)

    if not images:
        print("No input images found!")
        print(f"Please place sticker images into: {input_dir.resolve()}")
        print("Expected subdirectories: flat/, cartoon/, watercolor/")
        return []

    print(f"Found {len(images)} images across {len(styles)} styles.")
    results = []

    for item in images:
        img_path = item["path"]
        style = item["style"]
        fname = item["filename"]

        # Load image
        img = Image.open(img_path).convert("RGB")
        img = img.resize(output_size, Image.LANCZOS)

        # Get caption
        caption = get_caption(fname, caption_map)

        # Overlay text
        final_img = overlay_text_on_sticker(img, caption, config)

        # Save
        out_path = output_dir / style / f"final_{Path(fname).stem}.png"
        final_img.save(str(out_path), OUTPUT_FORMAT)

        results.append({
            "input": str(img_path),
            "output": str(out_path),
            "style": style,
            "caption": caption,
        })
        print(f"  [{style:12s}] {fname:25s} -> \\"{caption}\\"")

    print(f"\\nDone! {len(results)} final stickers saved to {output_dir.resolve()}")
    return results


# Run batch processing
results = process_all_stickers()""")

# ── Cell 6: Display sample results ──
md("## 6. Sample Output Display")

code("""def show_results(results: list, max_show: int = 6):
    \"\"\"Display a grid of processed sticker results.\"\"\"
    if not results:
        print("No results to display.")
        print("Tip: place sticker images into input_stickers/<style>/ and re-run.")
        return

    shown = results[:max_show]
    print(f"Showing {len(shown)} of {len(results)} results:\\n")

    for r in shown:
        out_path = r["output"]
        if os.path.exists(out_path):
            print(f"[{r['style']}] {r['caption']}")
            img = Image.open(out_path)
            # Resize for display
            display_img = img.copy()
            display_img.thumbnail((300, 300))
            display(display_img)
            print()


show_results(results)""")

# ── Cell 7: Summary statistics ──
md("## 7. Summary")

code("""def print_summary(results: list):
    \"\"\"Print a summary of the batch processing run.\"\"\"
    if not results:
        print("No images were processed.")
        print()
        print("=== Quick Start ===")
        print("1. Copy your generated sticker images into:")
        print(f"   {(INPUT_DIR / 'flat').resolve()}")
        print(f"   {(INPUT_DIR / 'cartoon').resolve()}")
        print(f"   {(INPUT_DIR / 'watercolor').resolve()}")
        print("2. (Optional) Edit text_captions.json to customize captions")
        print("3. Re-run this notebook from the top")
        return

    # Count per style
    style_counts = {}
    for r in results:
        s = r["style"]
        style_counts[s] = style_counts.get(s, 0) + 1

    print("=== Processing Summary ===")
    print(f"  Total stickers processed: {len(results)}")
    for style, count in style_counts.items():
        print(f"    {style:12s}: {count} images")
    print(f"  Output directory: {OUTPUT_DIR.resolve()}")
    print(f"  Output format:    {OUTPUT_FORMAT}")
    print(f"  Output size:      {OUTPUT_SIZE}")
    print()
    print("All final stickers are ready for submission!")


print_summary(results)""")

# ── Assemble notebook ──
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.8.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

# Fix cell sources: each line needs a trailing \n except the last
for cell in notebook["cells"]:
    lines = cell["source"]
    new_lines = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            new_lines.append(line + "\n")
        else:
            new_lines.append(line)
    cell["source"] = new_lines

out_path = r"c:\Users\93480\Desktop\开学\学习\下学期\6209\大作业\stat-6209-topic-3-project\step5-textual-generate\final_sticker_pipeline.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Notebook created at: {out_path}")
