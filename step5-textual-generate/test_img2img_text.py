"""
Test: Use SDXL img2img to add text to existing stickers.
Low denoising strength to preserve original image while adding text.
RTX 3060 6GB - uses float16 + attention slicing to fit in VRAM.
"""

import torch
import os
from pathlib import Path
from PIL import Image
from diffusers import AutoPipelineForImage2Image

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sd_text_test")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Use one of the existing flat stickers as input
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_IMAGE = PROJECT_ROOT / "sticker_results" / "flat" / "flat_animal_1.png"

print("=" * 60)
print("SDXL img2img Text Fusion Test")
print("=" * 60)

# Load input image
print(f"\n📷 Input image: {INPUT_IMAGE}")
init_image = Image.open(INPUT_IMAGE).convert("RGB").resize((512, 512))
init_image.save(os.path.join(OUTPUT_DIR, "img2img_input.png"))

# Load SDXL img2img pipeline
print("\n📥 Loading SDXL img2img pipeline (first time will download ~6GB)...")
pipe = AutoPipelineForImage2Image.from_pretrained(
    "stabilityai/sdxl-turbo",  # Smaller & faster variant of SDXL
    torch_dtype=torch.float16,
    variant="fp16",
)
pipe = pipe.to("cuda")
pipe.enable_attention_slicing()
print("✅ Model loaded!")

# Test with different denoising strengths
tests = [
    {
        "name": "img2img_strength02",
        "prompt": 'A cute cat sticker with text "Cool Cat" at the bottom, sticker style',
        "strength": 0.2,
        "desc": "Low strength (0.2) - mostly preserve original",
    },
    {
        "name": "img2img_strength04",
        "prompt": 'A cute cat sticker with text "Cool Cat" at the bottom, sticker style',
        "strength": 0.4,
        "desc": "Medium strength (0.4) - balance original + text",
    },
    {
        "name": "img2img_strength06",
        "prompt": 'A cute cat sticker with bold text "Cool Cat" written below, typography, sticker style',
        "strength": 0.6,
        "desc": "Higher strength (0.6) - more text, less original",
    },
]

for i, t in enumerate(tests):
    print(f"\n[{i+1}/{len(tests)}] {t['desc']}")
    print(f"  Prompt: {t['prompt']}")
    print(f"  Strength: {t['strength']}")
    print("  Generating...")

    image = pipe(
        prompt=t["prompt"],
        image=init_image,
        strength=t["strength"],
        guidance_scale=7.5,
        num_inference_steps=20,
    ).images[0]

    path = os.path.join(OUTPUT_DIR, f"{t['name']}.png")
    image.save(path)
    print(f"  ✅ Saved: {path}")

print("\n" + "=" * 60)
print(f"Done! Check results in: {OUTPUT_DIR}")
print("=" * 60)
