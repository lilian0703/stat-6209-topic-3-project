"""Standalone VLM batch test — runs POE API on all 18 sticker images."""
import base64
import requests
import time
import json
import re
import random
from pathlib import Path

# ====================== Config ======================
POE_API_KEY = "sk-poe-dItPPGjJPTNXWa4fznXgHQxh7eIx4dbxfs0eqp9gO_8"
POE_URL = "https://api.poe.com/v1/chat/completions"
VLM_MODEL = "gpt-4o-mini"

VLM_SYSTEM_PROMPT = (
    "You are a sticker caption writer. "
    "Given a sticker image, output ONLY a short cute caption (1 to 3 English words). "
    "Style: cute, fun, pet-friendly. "
    "Examples: Cool Cat, Happy Panda, Big Bear, Little Fox, Meow!, Hop Hop. "
    "Output ONLY the caption, nothing else."
)

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# Find images
BASE_DIR = Path(".")
img_dir = BASE_DIR / ".." / "Flat_results" / "test_output"
if not img_dir.exists():
    print(f"Image directory not found: {img_dir}")
    exit(1)

images = sorted([f for f in img_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTS])
print(f"Found {len(images)} images in {img_dir}\n")

# Load JSON captions
caption_map = {}
captions_file = BASE_DIR / "text_captions.json"
if captions_file.exists():
    with open(captions_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        fname = item.get("file_name", "")
        caption = item.get("caption", "")
        if fname and caption:
            caption_map[fname] = caption

# VLM function
def generate_caption_vlm(image_path: str) -> str:
    try:
        with open(image_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        ext = Path(image_path).suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"

        headers = {
            "Authorization": f"Bearer {POE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": VLM_MODEL,
            "messages": [
                {"role": "system", "content": VLM_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{b64_image}"}},
                        {"type": "text", "text": "What is a good short cute caption for this sticker?"},
                    ],
                },
            ],
            "max_tokens": 20,
            "temperature": 0.7,
        }

        resp = requests.post(POE_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            print(f"    Error {resp.status_code}: {resp.text[:200]}")
            return None

        caption = resp.json()["choices"][0]["message"]["content"].strip().strip('"').strip("'")
        words = caption.split()
        if len(words) > 3:
            caption = " ".join(words[:3])
        return caption
    except Exception as e:
        print(f"    Error: {e}")
        return None


# Run VLM on all images
print("Running VLM on all images...\n")
vlm_results = {}
for img_path in images:
    print(f"  [{len(vlm_results)+1:2d}/{len(images)}] {img_path.name}...", end=" ", flush=True)
    caption = generate_caption_vlm(str(img_path))
    vlm_results[img_path.name] = caption or "(failed)"
    print(f'-> "{vlm_results[img_path.name]}"')
    time.sleep(0.5)

# Comparison table
print("\n" + "=" * 70)
print(f"  {'Filename':<25s} | {'JSON Caption':<16s} | {'VLM Caption':<16s}")
print("  " + "-" * 66)
differ = 0
for fname, vlm_cap in vlm_results.items():
    json_cap = caption_map.get(fname, "(none)")
    marker = " *" if json_cap != vlm_cap else ""
    if json_cap != vlm_cap:
        differ += 1
    print(f"  {fname:<25s} | {json_cap:<16s} | {vlm_cap:<16s}{marker}")

print("  " + "-" * 66)
print(f"  {len(vlm_results)} images, {differ} captions differ (* marked)")
print("=" * 70)
