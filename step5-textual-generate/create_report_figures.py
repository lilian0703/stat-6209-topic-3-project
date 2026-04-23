"""Create comparison figures for the report."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FINAL = SCRIPT_DIR / "styled_test_output"
REPORT_FIG_DIR = SCRIPT_DIR / "report_figures"
REPORT_FIG_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size):
    for name in ["arialbd.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def create_3style_comparison(animal_num=1):
    """Create a side-by-side comparison of flat/cartoon/watercolor for one animal."""
    flat_path = OUTPUT_FINAL / f"final_flat_animal_{animal_num}.png"
    cartoon_path = OUTPUT_FINAL / f"final_cartoon_animal_{animal_num}.png"
    watercolor_path = OUTPUT_FINAL / f"final_watercolor_animal_{animal_num}.png"

    paths = [flat_path, cartoon_path, watercolor_path]
    labels = ["Flat", "Cartoon", "Watercolor"]

    # Check which exist
    existing = [(p, l) for p, l in zip(paths, labels) if p.exists()]
    if len(existing) < 3:
        print(f"  Skipping animal_{animal_num}: only {len(existing)}/3 styles found")
        return None

    # Load images
    imgs = [Image.open(p).convert("RGB") for p, _ in existing]
    labels_used = [l for _, l in existing]

    # Create combined image with labels
    img_w, img_h = imgs[0].size
    label_h = 30
    gap = 10
    total_w = img_w * 3 + gap * 2
    total_h = img_h + label_h

    canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    font = get_font(20)

    for i, (img, label) in enumerate(zip(imgs, labels_used)):
        x_offset = i * (img_w + gap)
        canvas.paste(img, (x_offset, label_h))
        # Draw label
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x_offset + (img_w - tw) // 2, 4), label, font=font, fill=(0, 0, 0))

    out_path = REPORT_FIG_DIR / f"text_overlay_3styles_animal_{animal_num}.png"
    canvas.save(out_path, "PNG")
    print(f"  Saved: {out_path.name} ({total_w}x{total_h})")
    return out_path


def create_multi_example_grid(animal_nums=[1, 4, 5]):
    """Create a 3x3 grid: rows=animals, cols=styles."""
    styles = ["flat", "cartoon", "watercolor"]
    style_labels = ["Flat", "Cartoon", "Watercolor"]

    cell_size = 256
    label_h = 30
    gap = 6
    cols = 3
    rows = len(animal_nums)
    total_w = cols * cell_size + (cols - 1) * gap
    total_h = rows * cell_size + (rows - 1) * gap + label_h

    canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    font = get_font(18)

    # Column headers
    for c, label in enumerate(style_labels):
        x = c * (cell_size + gap)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x + (cell_size - tw) // 2, 4), label, font=font, fill=(0, 0, 0))

    # Fill grid
    for r, anum in enumerate(animal_nums):
        for c, style in enumerate(styles):
            img_path = OUTPUT_FINAL / f"final_{style}_animal_{anum}.png"
            if not img_path.exists():
                print(f"  Missing: {img_path.name}")
                continue
            img = Image.open(img_path).convert("RGB").resize((cell_size, cell_size), Image.LANCZOS)
            x = c * (cell_size + gap)
            y = r * (cell_size + gap) + label_h
            canvas.paste(img, (x, y))

    out_path = REPORT_FIG_DIR / "text_overlay_grid.png"
    canvas.save(out_path, "PNG")
    print(f"  Saved: {out_path.name} ({total_w}x{total_h})")
    return out_path


if __name__ == "__main__":
    print("Creating report figures...")
    print()

    # Figure 1: 3-style comparison for animal 1
    print("Figure 1: Three-style comparison")
    create_3style_comparison(1)
    print()

    # Figure 2: 3x3 grid with multiple animals
    print("Figure 2: Multi-animal grid (3 animals x 3 styles)")
    create_multi_example_grid([1, 4, 5])
    print()

    print(f"Done! Figures saved to: {REPORT_FIG_DIR}")
