#!/usr/bin/env python3
"""Batch-generate A4 coloring pages for all animals and merge into a PDF."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import img2pdf

from create_coloring_pages import create_coloring_page
ANIMALS = json.loads((ROOT / "scripts" / "animals.json").read_text())
INPUT_DIR = ROOT / "tiere"
OUTPUT_DIR = ROOT / "ausmalbilder"
PDF_NAME = "alle-ausmalbilder.pdf"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for animal in ANIMALS:
        input_path = INPUT_DIR / animal["file"]
        output_path = OUTPUT_DIR / animal["file"]
        if not input_path.exists():
            print(f"Missing input: {input_path}", file=sys.stderr)
            return 1

        line_strength = animal.get("line_strength", 3)
        create_coloring_page(
            input_path,
            output_path,
            animal["name_de"],
            small=animal.get("small", False),
            line_strength=line_strength,
        )
        generated.append(output_path)
        print(f"Created {output_path.name}")

    pdf_path = OUTPUT_DIR / PDF_NAME
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(img2pdf.convert([str(path) for path in generated]))
    print(f"Created {pdf_path} ({len(generated)} pages)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
