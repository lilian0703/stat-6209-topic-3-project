"""Copy colored text images from styled_test_output to output_final, overwriting old white-text versions."""
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC = SCRIPT_DIR / "styled_test_output"
DST = SCRIPT_DIR / "output_final"

styles = ["flat", "cartoon", "watercolor"]
count = 0

for src_img in sorted(SRC.glob("*.png")):
    name = src_img.name  # e.g. final_flat_animal_1.png
    # Determine style subfolder
    style_found = None
    for s in styles:
        if f"_{s}_" in name:
            style_found = s
            break
    if not style_found:
        print(f"  Skipped (unknown style): {name}")
        continue

    dst_dir = DST / style_found
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_path = dst_dir / name
    shutil.copy2(src_img, dst_path)
    count += 1

print(f"Done! Copied {count} colored images to output_final/")
for s in styles:
    n = len(list((DST / s).glob("*.png")))
    print(f"  {s}: {n} images")
