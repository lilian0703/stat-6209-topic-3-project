import shutil
from pathlib import Path

src = Path(__file__).resolve().parent / "report_figures"
dst = Path(__file__).resolve().parent / "ppt_materials"
dst.mkdir(exist_ok=True)

shutil.copy2(src / "text_overlay_3styles_animal_1.png", dst / "three_styles_comparison.png")
shutil.copy2(src / "text_overlay_grid.png", dst / "multi_animal_grid.png")

print("Done! Files in ppt_materials:")
for f in dst.iterdir():
    print(f"  {f.name}  ({f.stat().st_size // 1024} KB)")
