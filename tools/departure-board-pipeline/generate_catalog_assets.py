#!/usr/bin/env python3
"""
Slices the two photorealistic 4x3 contact sheets into 24 distinct destination
photography plates (Row 1 Destination photo flap & Row 3 Duration photo flap)
under `frontend/public/landing/departure-board/catalog/`.
"""

from pathlib import Path
from PIL import Image

OUT_DIR = Path("/Users/pranay/Projects/travel_agency_agent/frontend/public/landing/departure-board/catalog")
OUT_DIR.mkdir(parents=True, exist_ok=True)

GRID_1 = Path("/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f/catalog_grid_1_1794043086204.jpg")
GRID_2 = Path("/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f/catalog_grid_2_1794043112443.jpg")

GRID_1_MAP = [
    # (row, col, filename)
    (0, 0, "photo-dubai-1.png"),
    (0, 1, "photo-dubai-2.png"),
    (0, 2, "photo-greece-1.png"),
    (0, 3, "photo-greece-2.png"),
    (1, 0, "photo-switzerland-1.png"),
    (1, 1, "photo-switzerland-2.png"),
    (1, 2, "photo-peru-1.png"),
    (1, 3, "photo-peru-2.png"),
    (2, 0, "photo-iceland-1.png"),
    (2, 1, "photo-iceland-2.png"),
    (2, 2, "photo-kenya-1.png"),
    (2, 3, "photo-kenya-2.png"),
]

GRID_2_MAP = [
    (0, 0, "photo-portugal-1.png"),
    (0, 1, "photo-portugal-2.png"),
    (0, 2, "photo-bali-1.png"),
    (0, 3, "photo-bali-2.png"),
    (1, 0, "photo-patagonia-1.png"),
    (1, 1, "photo-patagonia-2.png"),
    (1, 2, "photo-norway-1.png"),
    (1, 3, "photo-norway-2.png"),
    (2, 0, "photo-maldives-1.png"),
    (2, 1, "photo-maldives-2.png"),
    (2, 2, "photo-france-1.png"),
    (2, 3, "photo-france-2.png"),
]


def slice_grid(grid_path: Path, mapping: list[tuple[int, int, str]]) -> None:
    im = Image.open(grid_path).convert("RGB")
    w, h = im.size
    cell_w = w / 4.0
    cell_h = h / 3.0
    inset = 3
    for row, col, fname in mapping:
        x0 = int(round(col * cell_w)) + inset
        y0 = int(round(row * cell_h)) + inset
        x1 = int(round((col + 1) * cell_w)) - inset
        y1 = int(round((row + 1) * cell_h)) - inset
        crop = im.crop((x0, y0, x1, y1)).resize((480, 270), Image.Resampling.LANCZOS)
        crop.save(OUT_DIR / fname, optimize=True)


def main() -> None:
    slice_grid(GRID_1, GRID_1_MAP)
    slice_grid(GRID_2, GRID_2_MAP)
    print(f"Sliced 24 photorealistic destination plates into {OUT_DIR}")


if __name__ == "__main__":
    main()
