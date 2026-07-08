#!/usr/bin/env python3
"""Batch-process all raw animal images into final 2048x2048 icons."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANIMALS = json.loads((ROOT / "scripts" / "animals.json").read_text())
RAW_DIR = ROOT / "tiere" / "_raw"
OUT_DIR = ROOT / "tiere"
PROCESS_SCRIPT = ROOT / "scripts" / "process_icon.py"


def main() -> int:
  missing = []
  for animal in ANIMALS:
    raw = RAW_DIR / animal["file"]
    out = OUT_DIR / animal["file"]
    if not raw.exists():
      missing.append(animal["file"])
      continue
  if missing:
    print(f"Missing raw files ({len(missing)}):", ", ".join(missing))
    return 1

  for animal in ANIMALS:
    raw = RAW_DIR / animal["file"]
    out = OUT_DIR / animal["file"]
    subprocess.run([sys.executable, str(PROCESS_SCRIPT), str(raw), str(out)], check=True)
    print(f"Processed {animal['file']}")

  return 0


if __name__ == "__main__":
  sys.exit(main())
