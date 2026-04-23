# Step 5: Textual Generate — PPT Outline

## Image Files in This Folder:
| File Name | Description | Used In |
|-----------|-------------|---------|
| `94ecd218c0698bdec6f0f32733f404c3.png` | SD failed text example: "CLAL COOL COL COol" cat | Slide 3 (left) |
| `594ff19129847207cf309c58da97c566.png` | SD failed text example: "Col" garbled black cat | Slide 3 (right) |
| `three_styles_comparison.png` | Same animal with Flat/Cartoon/Watercolor text overlay | Slide 6 |
| `multi_animal_grid.png` | 3×3 grid: 3 animals × 3 styles with text | Slide 7 |

---

## Slide 1: Section Title
- Title: **Step 5: (Optional) Textual Generate**
- Subtitle: Adding Creative Text Captions to Generated Stickers
- No image needed

---

## Slide 2: Overview
- Goal: Add short, creative text captions to enhance sticker personality
- Challenge: SD 1.5 cannot generate legible text in images
- Solution: Post-processing pipeline with VLM + PIL overlay
- Three-Stage Pipeline:
  1. Attempt direct text generation with SD → Failed
  2. Use VLM (GPT-4o-mini) to auto-generate captions
  3. Apply style-aware text rendering with contrast detection
- Flow: Sticker Image → VLM Caption → Style-Aware Overlay → Final Sticker
- No image needed (use text boxes / flow diagram)

---

## Slide 3: Initial Attempt — SD Text Generation Failed
- What we tried: We first attempted to include text directly in SD prompts (e.g., "a cat sticker with text 'Cool Cat'")
- Result: Completely illegible text, garbled characters
- Root Cause: SD 1.5 lacks dedicated text rendering modules
- Decision: Switch to post-processing approach

**Images (place side by side):**
- LEFT: `94ecd218c0698bdec6f0f32733f404c3.png` — SD tried to write "Cool Cat" but output "CLAL COOL COL COol"
- RIGHT: `594ff19129847207cf309c58da97c566.png` — SD tried to write text but output garbled "Col" with random characters

---

## Slide 4: VLM Caption Generation
- Model: GPT-4o-mini via POE API
- Output Format: Adjective + Noun (e.g., "Sleepy Whiskers", "Brave Bear")
- Diversity Constraints: Rotate among Cat/Kitty/Whiskers/Furball/Meowster/Paws/Fluffball
- Caching: Results saved to JSON for reproducibility
- Caption examples:
  - animal_1.png → "Cheerful Paws"
  - animal_5.png → "Happy Penguin"
  - animal_10.png → "Fluffy Meowster"
  - animal_15.png → "Gentle Giraffe"
  - animal_24.png → "Cheerful Capybara"
  - animal_30.png → "Chill Furball"
  - animal_37.png → "Charming Bear"
- No image needed (use text layout)

---

## Slide 5: Style-Aware Text Rendering
- Three techniques:
  1. Dominant Color Extraction: Downsample to 50×50, find most frequent saturated color
  2. Local Background Brightness Sampling: Sample region behind text bounding box
  3. Contrast Adjustment: If difference < 60/255, auto-swap colors
- Three rendering styles:
  - Flat: Arial Bold + dominant color fill + white stroke + shadow
  - Cartoon: Comic Sans Bold + white fill + 4px colored outline
  - Watercolor: Segoe Script + handwritten font + Gaussian glow
- No image needed (use diagram / text boxes)

---

## Slide 6: Results — Three-Style Comparison

**Image:** `three_styles_comparison.png` — Place this image large and centered

Caption: Left: Flat (dominant color + shadow). Center: Cartoon (white fill + colored outline). Right: Watercolor (handwritten font + glow).

---

## Slide 7: Results — Batch Output (3 Animals × 3 Styles)

**Image:** `multi_animal_grid.png` — Place this image large and centered

Caption: 37 stickers × 3 styles = 111 final sticker images with VLM-generated captions.

---

## Slide 8: Summary
- Problem: SD 1.5 cannot generate readable text → Post-processing with VLM + PIL
- VLM: GPT-4o-mini generates adjective + noun captions with diversity constraints
- Rendering: Dominant color + brightness sampling + contrast adjustment
- Styles: Flat / Cartoon / Watercolor
- Output: 37 × 3 = 111 final images
- No image needed
