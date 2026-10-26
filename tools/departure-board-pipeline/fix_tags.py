"""Cleanly segment tag-ita.png, tag-jpn.png, and tag-mar.png in 1 second so the top black rigging box and bottom tag corners are 100% intact and only the right-edge blue window glass is transparent."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

BRAIN_DIR = Path("/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f")
PUBLIC_DIR = Path("/Users/pranay/Projects/travel_agency_agent/frontend/public/landing/departure-board")
im1 = Image.open(PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-1.png").convert("RGBA")
im4 = Image.open(PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-4.png").convert("RGBA")

tag_box = (1480, 230, 1602, 535)
tw, th = 122, 305

crop1 = im1.crop(tag_box).convert("RGB")
crop4 = im4.crop(tag_box).convert("RGB")


def build_clean_tag_alpha(crop_rgb: Image.Image) -> Image.Image:
    arr = np.asarray(crop_rgb, dtype=np.float32)
    r, _g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    # Only pixels near the right side of the crop that have distinct cool blue window color (b - r > 16) are background window glass!
    # Flood-fill from the right boundary (x = tw - 1) so no interior pixels of the rigging or tag are ever touched.
    is_window = (b - r) > 15.0
    bg_mask = np.zeros((th, tw), dtype=bool)
    for y in range(th):
        # Scan inward from right edge x = tw - 1 while is_window is True
        for x in range(tw - 1, 35, -1):
            if is_window[y, x]:
                bg_mask[y, x] = True
            else:
                break
    alpha = (~bg_mask).astype(np.uint8) * 255
    return Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(radius=0.8))


alpha1 = build_clean_tag_alpha(crop1)
alpha4 = build_clean_tag_alpha(crop4)

# 1. Save tag-ita.png
tag_ita = crop1.convert("RGBA")
tag_ita.putalpha(alpha1)
tag_ita.save(PUBLIC_DIR / "tag-ita.png")

# 2. Save tag-jpn.png
tag_jpn = crop4.convert("RGBA")
tag_jpn.putalpha(alpha4)
tag_jpn.save(PUBLIC_DIR / "tag-jpn.png")

# 3. Save tag-mar.png from AI-generated `tag_morocco_1793016566454.jpg`
mar_gen = Image.open(BRAIN_DIR / "tag_morocco_1793016566454.jpg").convert("RGB")
crop1_arr = np.asarray(crop1, dtype=np.float32)
ref_top = crop1_arr[5:85, 10:105, :]
best_score = 1e18
best_crop = None
for target_h in range(305, 326, 2):
    target_w = int(round(mar_gen.width * (target_h / mar_gen.height)))
    cand_img = mar_gen.resize((target_w, target_h), Image.Resampling.LANCZOS)
    cand_arr = np.asarray(cand_img, dtype=np.float32)
    for dy in range(0, target_h - th + 1, 2):
        for dx in range(0, target_w - tw + 1, 2):
            patch = cand_arr[dy + 5 : dy + 85, dx + 10 : dx + 105, :]
            score = np.mean((patch - ref_top) ** 2)
            if score < best_score:
                best_score = score
                best_crop = cand_img.crop((dx, dy, dx + tw, dy + th))

tag_mar_rgb = crop1.copy()
blend_mask = Image.new("L", (tw, th), 0)
bm_px = blend_mask.load()
for y_c in range(30, 275):
    for x_c in range(18, 118):
        wy = min(1.0, (y_c - 30) / 25.0) * min(1.0, (275 - y_c) / 20.0)
        wx = min(1.0, (x_c - 18) / 10.0)
        bm_px[x_c, y_c] = int(255 * wy * wx)
tag_mar_rgb.paste(best_crop, (0, 0), blend_mask)
tag_mar = tag_mar_rgb.convert("RGBA")
tag_mar.putalpha(alpha1)
tag_mar.save(PUBLIC_DIR / "tag-mar.png")
print("Cleaned tag-ita.png, tag-jpn.png, and tag-mar.png!")
