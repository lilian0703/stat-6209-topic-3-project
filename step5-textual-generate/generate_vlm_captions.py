"""
Use VLM (GPT-4o-mini via POE API) to generate better captions for all 37 stickers.
Reads flat stickers as reference, generates creative captions, saves to text_captions_vlm.json.
"""

import base64
import requests
import time
import json
from pathlib import Path

# ====================== Config ======================
POE_API_KEY = "sk-poe-Ndtz5ClVIigLwa_QuflL96Cp0RXPAQJVNtJpgxWzyfo"
POE_URL = "https://api.poe.com/v1/chat/completions"
VLM_MODEL = "gpt-4o-mini"

# Updated prompt - more creative, not just adj+animal
VLM_SYSTEM_PROMPT = (
    "You are a sticker caption writer. "
    "Given a sticker image of an animal, output ONLY a two-word caption: one adjective + one noun. "
    "The adjective should describe the animal's mood, personality, or appearance in the image. "
    "The noun should be the animal type or a fun creative nickname. "
    "IMPORTANT: Use diverse nouns — vary between the animal name, nicknames, and playful alternatives. "
    "For cats, rotate among: Cat, Kitty, Whiskers, Furball, Meowster, Paws, Fluffball. "
    "For dogs, rotate among: Dog, Pup, Pupper, Buddy, Woofer, Snoot. "
    "For other animals, use their species name OR a fun nickname. "
    "Good examples: 'Sleepy Whiskers', 'Brave Bear', 'Chill Penguin', 'Sassy Furball', "
    "'Cozy Panda', 'Loyal Pupper', 'Gentle Deer', 'Sneaky Fox', 'Grumpy Turtle', 'Zany Meowster'. "
    "Bad examples: 'Cute Cat' (too generic), 'Purrs & Pouts' (not adj+noun), 'Chillin Like a Penguin' (too long). "
    "Output ONLY two words: adjective + noun. Nothing else."
)

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
# Prefer new 4.19 version, fallback to original
_flat_419 = PROJECT_ROOT / "sticker_results" / "flat 4.19"
_flat_orig = PROJECT_ROOT / "sticker_results" / "flat"
INPUT_DIR = _flat_419 if _flat_419.exists() else _flat_orig
OUTPUT_JSON = SCRIPT_DIR / "text_captions_vlm.json"


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
                        {"type": "text", "text": "Write a short fun caption for this sticker:"},
                    ],
                },
            ],
            "max_tokens": 20,
            "temperature": 0.9,
        }

        resp = requests.post(POE_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            print(f"    Error {resp.status_code}: {resp.text[:200]}")
            return None

        caption = resp.json()["choices"][0]["message"]["content"].strip().strip('"').strip("'")
        # Limit to 4 words max
        words = caption.split()
        if len(words) > 4:
            caption = " ".join(words[:4])
        return caption
    except Exception as e:
        print(f"    Error: {e}")
        return None


def main():
    print("=" * 60)
    print("VLM Creative Caption Generator")
    print("=" * 60)

    # Find all flat stickers (use flat as reference since all 3 styles are same animal)
    images = sorted(
        [f for f in INPUT_DIR.iterdir() if f.suffix.lower() in SUPPORTED_EXTS],
        key=lambda x: int(''.join(filter(str.isdigit, x.stem)) or '0')
    )
    print(f"\nFound {len(images)} images in {INPUT_DIR}\n")

    if not images:
        print("No images found!")
        return

    # Generate captions
    results = []
    for i, img_path in enumerate(images):
        # Extract animal number: flat_animal_1.png -> animal_1.png
        base_name = img_path.name
        for prefix in ["flat_", "cartoon_", "watercolor_"]:
            if base_name.startswith(prefix):
                base_name = base_name[len(prefix):]
                break

        print(f"  [{i+1:2d}/{len(images)}] {img_path.name}...", end=" ", flush=True)
        caption = generate_caption_vlm(str(img_path))

        if caption:
            print(f'-> "{caption}"')
            results.append({"file_name": base_name, "caption": caption})
        else:
            fallback = "Cute Sticker"
            print(f'-> FAILED, using "{fallback}"')
            results.append({"file_name": base_name, "caption": fallback})

        time.sleep(0.5)  # Rate limit

    # Save
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"Done! {len(results)} captions saved to: {OUTPUT_JSON}")
    print(f"{'=' * 60}")

    # Show all captions
    print("\nGenerated captions:")
    for r in results:
        print(f"  {r['file_name']:<20s} -> {r['caption']}")


if __name__ == "__main__":
    main()
