#!/usr/bin/env python3
"""Process raw animal illustrations into 2048x2048 transparent PNG icons."""

import argparse
import sys
from pathlib import Path

from PIL import Image
from rembg import remove

TARGET_SIZE = 2048
FILL_RATIO = 0.82


def process_icon(input_path: Path, output_path: Path) -> None:
    with open(input_path, "rb") as f:
        raw = f.read()

    cutout = remove(raw)
    img = Image.open(__import__("io").BytesIO(cutout)).convert("RGBA")

    bbox = img.getbbox()
    if not bbox:
        raise ValueError(f"No visible content in {input_path}")

    cropped = img.crop(bbox)
    max_dim = max(cropped.size)
    scale = (TARGET_SIZE * FILL_RATIO) / max_dim
    new_w = max(1, int(cropped.width * scale))
    new_h = max(1, int(cropped.height * scale))
    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    offset_x = (TARGET_SIZE - new_w) // 2
    offset_y = (TARGET_SIZE - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input image path")
    parser.add_argument("output", type=Path, help="Output PNG path")
    args = parser.parse_args()
    process_icon(args.input, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
