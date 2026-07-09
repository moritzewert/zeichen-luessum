#!/usr/bin/env python3
"""Convert a colored animal illustration into an A4 coloring page."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

A4_WIDTH = 2480
A4_HEIGHT = 3508
DPI = 300
FILL_RATIO = 0.78
SMALL_FILL_RATIO = 0.85
TEXT_AREA_HEIGHT = 200
FONT_SIZE = 88
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _load_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, FONT_SIZE)
    return ImageFont.load_default()


def _flatten_on_white(rgba: Image.Image) -> Image.Image:
    background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(background, rgba.convert("RGBA")).convert("RGB")


def _crop_to_content(rgba: Image.Image) -> Image.Image:
    alpha = rgba.split()[-1]
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError("Image has no visible content")
    return rgba.crop(bbox)


def _alpha_outline(rgba: Image.Image, thickness: int = 3) -> np.ndarray:
    alpha = np.array(rgba.split()[-1])
    _, binary = cv2.threshold(alpha, 16, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (thickness, thickness))
    eroded = cv2.erode(binary, kernel, iterations=1)
    return cv2.subtract(binary, eroded)


def _major_region_boundaries(rgb: np.ndarray, color_count: int = 4) -> np.ndarray:
    """Boundaries between large color areas (eyes, patches) — not fur texture."""
    h, w = rgb.shape[:2]
    scale = 8
    small = cv2.resize(rgb, (max(1, w // scale), max(1, h // scale)), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(small, (9, 9), 0)

    pixels = blurred.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, _ = cv2.kmeans(
        pixels, color_count, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )
    labels = labels.reshape(small.shape[:2]).astype(np.uint8)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    boundaries = cv2.morphologyEx(labels, cv2.MORPH_GRADIENT, kernel)
    boundaries = (boundaries > 0).astype(np.uint8) * 255

    boundaries = cv2.resize(boundaries, (w, h), interpolation=cv2.INTER_NEAREST)
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    boundaries = cv2.morphologyEx(boundaries, cv2.MORPH_OPEN, open_kernel, iterations=1)
    return boundaries


def _remove_fine_details(binary: np.ndarray, min_area: int) -> np.ndarray:
    """Drop small scattered strokes (fur, shading noise)."""
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    cleaned = np.zeros_like(binary)
    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] >= min_area:
            cleaned[labels == label] = 255
    return cleaned


def _extract_line_art(rgba: Image.Image, rgb: np.ndarray, line_strength: int = 3) -> np.ndarray:
    h, w = rgb.shape[:2]
    min_area = max(250, int(h * w * 0.0008))

    outline = _alpha_outline(rgba, thickness=max(2, line_strength))
    regions = _major_region_boundaries(rgb, color_count=4)

    alpha_mask = np.array(rgba.split()[-1]) > 16
    regions = regions.copy()
    regions[~alpha_mask] = 0

    combined = cv2.bitwise_or(outline, regions)
    combined = _remove_fine_details(combined, min_area)

    kernel_size = max(1, line_strength)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    thickened = cv2.dilate(combined, kernel, iterations=1)

    return 255 - thickened


def _fit_on_canvas(
    line_art: np.ndarray,
    canvas_w: int,
    canvas_h: int,
    fill_ratio: float,
) -> tuple[np.ndarray, int, int]:
    h, w = line_art.shape[:2]
    target_w = int(canvas_w * fill_ratio)
    target_h = int(canvas_h * fill_ratio)
    scale = min(target_w / w, target_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    resized = cv2.resize(line_art, (new_w, new_h), interpolation=cv2.INTER_AREA)

    offset_x = (canvas_w - new_w) // 2
    offset_y = (canvas_h - new_h) // 2
    return resized, offset_x, offset_y


def _draw_name(page: Image.Image, name: str) -> Image.Image:
    draw = ImageDraw.Draw(page)
    font = _load_font()
    text_bbox = draw.textbbox((0, 0), name, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    x = (A4_WIDTH - text_w) // 2
    y = A4_HEIGHT - TEXT_AREA_HEIGHT + (TEXT_AREA_HEIGHT - text_h) // 2
    draw.text((x, y), name, fill=0, font=font)
    return page


def create_coloring_page(
    input_path: Path,
    output_path: Path,
    name_de: str,
    *,
    small: bool = False,
    line_strength: int = 2,
) -> None:
    rgba = Image.open(input_path).convert("RGBA")
    cropped = _crop_to_content(rgba)
    rgb = _flatten_on_white(cropped)
    line_art = _extract_line_art(cropped, np.array(rgb), line_strength=line_strength)

    drawing_h = A4_HEIGHT - TEXT_AREA_HEIGHT
    fill_ratio = SMALL_FILL_RATIO if small else FILL_RATIO
    resized, offset_x, offset_y = _fit_on_canvas(line_art, A4_WIDTH, drawing_h, fill_ratio)

    page_arr = np.full((A4_HEIGHT, A4_WIDTH), 255, dtype=np.uint8)
    h, w = resized.shape[:2]
    page_arr[offset_y : offset_y + h, offset_x : offset_x + w] = resized
    page = Image.fromarray(page_arr, mode="L").convert("RGB")
    page = _draw_name(page, name_de)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path, "PNG", dpi=(DPI, DPI))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input animal PNG path")
    parser.add_argument("output", type=Path, help="Output coloring page PNG path")
    parser.add_argument("--name", required=True, help="German animal name for the page")
    parser.add_argument("--small", action="store_true", help="Use larger fill ratio for small animals")
    parser.add_argument("--line-strength", type=int, default=3, help="Line thickness (1-4)")
    args = parser.parse_args()

    create_coloring_page(
        args.input,
        args.output,
        args.name,
        small=args.small,
        line_strength=args.line_strength,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
