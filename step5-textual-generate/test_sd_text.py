"""
Quick test: Can SD 1.5 generate readable text in sticker images?
RTX 3060 (6GB) - should take ~1-2 min per image.
"""

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sd_text_test")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("SD 1.5 Text Generation Test")
print("=" * 60)

# Load SD 1.5
print("\n📥 Loading Stable Diffusion v1.5 (this may take a few minutes first time)...")
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    safety_checker=None,
)
pipe = pipe.to("cuda")
pipe.enable_attention_slicing()  # Save VRAM on 6GB card
print("✅ Model loaded!")

# Test prompts
tests = [
    {
        "name": "test1_no_text",
        "prompt": "A sleek black cat sitting, sticker style, white background",
        "desc": "Baseline: no text in prompt",
    },
    {
        "name": "test2_with_text",
        "prompt": 'A cute black cat sticker with the text "Cool Cat" written at the bottom, sticker style, white background',
        "desc": "Test: text in prompt",
    },
    {
        "name": "test3_text_emphasis",
        "prompt": 'A cute cat sticker, bold text "Cool Cat" below the cat, typography, sticker style, white background',
        "desc": "Test: emphasized text in prompt",
    },
]

for i, t in enumerate(tests):
    print(f"\n[{i+1}/{len(tests)}] {t['desc']}")
    print(f"  Prompt: {t['prompt']}")
    print("  Generating...")
    
    image = pipe(
        t["prompt"],
        num_inference_steps=30,
        guidance_scale=7.5,
        width=512,
        height=512,
    ).images[0]
    
    path = os.path.join(OUTPUT_DIR, f"{t['name']}.png")
    image.save(path)
    print(f"  ✅ Saved: {path}")

print("\n" + "=" * 60)
print(f"Done! Check results in: {OUTPUT_DIR}")
print("=" * 60)
