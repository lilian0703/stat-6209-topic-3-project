# Step 5: Optional Textual Generate — Final Sticker Productization

**Module Owner**: Step 5 contributor  
**Project**: STAT 6209 Topic 3 — Sticker Design Generation

## Overview

This module handles the **final sticker productization** pipeline:

1. **Data standardization** — Collect generated sticker images from upstream LoRA pipelines (flat, cartoon, watercolor) into a unified directory structure
2. **Caption generation** — Load or auto-generate short text captions for each sticker
3. **Text overlay** — Render captions onto sticker images (white text + dark stroke, bottom-center)
4. **Batch export** — Output production-ready final sticker images at uniform 512×512 resolution

This module does **not** perform LoRA fine-tuning or VLM prompt generation — those are handled by upstream steps.

## Directory Structure

```
step5-textual-generate/
├── input_stickers/               # Sticker images from upstream modules
│   ├── flat/                     # Flat sticker style
│   ├── cartoon/                  # Cartoon style
│   └── watercolor/               # Watercolor style
├── output_final/                 # Final stickers with text overlay
│   ├── flat/                     # (auto-created)
│   ├── cartoon/                  # (auto-created)
│   └── watercolor/               # (auto-created)
├── text_captions.json            # Caption mapping (file_name → caption)
├── final_sticker_pipeline.ipynb  # Main processing notebook
└── README.md
```

## Quick Start

1. **Place sticker images** into `input_stickers/<style>/`  
   - Supported formats: `.png`, `.jpg`, `.jpeg`, `.webp`
   - Images will be resized to 512×512 automatically
2. **(Optional)** Edit `text_captions.json` to customize captions  
   - If a file has no matching caption, a default is auto-generated from the filename
3. **Run** `final_sticker_pipeline.ipynb` top to bottom
4. **Find results** in `output_final/<style>/`

## Caption Rules

| Rule | Default |
|------|---------|
| Language | English |
| Length | 1–3 words |
| Tone | Cute, short, pet-sticker friendly |
| Examples | `Cute Cat`, `Happy Panda`, `Sweet Puppy`, `Little Fox` |
| Position | Bottom-center of image |
| Text style | White fill + dark stroke (width 2) |
| Background | Semi-transparent dark rounded rectangle |
| Font | Arial (Windows) / DejaVu Sans Bold (Linux) / Helvetica (macOS) |

## Caption JSON Format

```json
[
    {"file_name": "animal_1.jpeg", "caption": "Cool Cat"},
    {"file_name": "animal_2.jpeg", "caption": "Double Trouble"}
]
```

- `file_name`: matches the image filename in `input_stickers/<style>/`
- `caption`: the short text to overlay

## Notebook Sections

| Cell | Section | Description |
|------|---------|-------------|
| 1 | Configuration & Imports | Paths, styles, text settings, output size |
| 2 | Load Captions | Read `text_captions.json` into a lookup dict |
| 3 | Default Caption Generator | Auto-generate captions from filenames |
| 4 | Text Overlay Function | PIL-based text rendering with stroke + background |
| 5 | Batch Processing | Scan → load → overlay → save for all images |
| 6 | Sample Output Display | Show a grid of processed results |
| 7 | Summary | Print per-style counts and output path |

## Dependencies

- Python 3.8+
- Pillow (`pip install Pillow`)

No GPU required. No additional ML dependencies.
