"""Produce the final 3 parallax layers (bg-landscape-clean.png, board-chassis-layer.png, fg-luggage-layer.png)
plus photorealistic Morocco photo flaps and registered ITA/JPN/MAR baggage tags."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import torch
from transformers import Sam2Model, Sam2Processor, VitMatteForImageMatting

QWEN_ROOT = Path("/Users/pranay/Projects/qwen-image-21-local")
BRAIN_DIR = Path("/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f")
SCRATCH = BRAIN_DIR / "scratch"
MASKS_DIR = SCRATCH / "sam31_masks"
PUBLIC_DIR = Path("/Users/pranay/Projects/travel_agency_agent/frontend/public/landing/departure-board")
IMG1_PATH = PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-1.png"
IMG2_PATH = PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-2.png"
IMG3_PATH = PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-3.png"
IMG4_PATH = PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-4.png"

device = "mps"
im1 = Image.open(IMG1_PATH).convert("RGBA")
im2 = Image.open(IMG2_PATH).convert("RGBA")
im3 = Image.open(IMG3_PATH).convert("RGBA")
im4 = Image.open(IMG4_PATH).convert("RGBA")
pil1 = im1.convert("RGB")
W, H = im1.size
px1 = im1.load()
px2 = im2.load()
px3 = im3.load()

# ---------------------------------------------------------------------------
# 1. Clean Background Landscape Layer (bg-landscape-clean.png)
# ---------------------------------------------------------------------------
bg = im1.convert("RGB")
bpx = bg.load()

# 1a. Clean top-right "Sign in" and "Book a demo ->" (x: 1275..1575, y: 18..78)
for x in range(1275, 1575):
    c_top = px1[x, 14]
    c_bot = px1[x, 84]
    for y in range(16, 83):
        t = (y - 16) / (83 - 16)
        st = t * t * (3 - 2 * t)
        bpx[x, y] = (
            int(c_top[0] * (1 - st) + c_bot[0] * st),
            int(c_top[1] * (1 - st) + c_bot[1] * st),
            int(c_top[2] * (1 - st) + c_bot[2] * st),
        )

# 1b. Mask ONLY top-left nav (y: 22..76) and eyebrow + headline (y: 145..538, x: 120..535)
# NEVER inject bright y=245 cobalt blue below y=538!
mask = Image.new("L", (W, H), 0)
mpx = mask.load()

for y in range(22, 76):
    for x in range(118, 925):
        r, g, b, _ = px1[x, y]
        if r > 25 or g > 85:
            mpx[x, y] = 255

for y in range(145, 538):
    for x in range(120, 535):
        r, g, b, _ = px1[x, y]
        if r > 35 or g > 92:
            mpx[x, y] = 255

mask = mask.filter(ImageFilter.MaxFilter(7))
mpx = mask.load()

for y in range(20, 542):
    x = 115
    while x < 935:
        if mpx[x, y] > 0:
            x_start = x
            while x < 935 and mpx[x, y] > 0:
                x += 1
            x_end = x
            c_left = bpx[x_start - 1, y]
            # Only above y=535 where olive leaves touch x=120, fallback to clean blue wall at (118, 245)
            if c_left[2] < 120 and x_start < 150 and y < 535:
                c_left = bpx[x_start - 1, 245]
            c_right = bpx[x_end, y]
            span = max(1, x_end - x_start)
            for xi in range(x_start, x_end):
                t = (xi - x_start) / span
                bpx[xi, y] = (
                    int(c_left[0] * (1 - t) + c_right[0] * t),
                    int(c_left[1] * (1 - t) + c_right[1] * t),
                    int(c_left[2] * (1 - t) + c_right[2] * t),
                )
        else:
            x += 1

for _ in range(6):
    blurred = bg.filter(ImageFilter.BoxBlur(4))
    bl_px = blurred.load()
    for y in range(20, 542):
        for x in range(115, 935):
            if mpx[x, y] > 0:
                bpx[x, y] = bl_px[x, y]

# 1c. Clean the 3-line subcopy (y: 542..635, x: 122..446) using per-column VERTICAL interpolation
# across each ~22px text line so the ambient wall & lounge chair at x>=450 are 100% untouched!
sub_mask = Image.new("L", (W, H), 0)
sm_px = sub_mask.load()
for y in range(544, 634):
    for x in range(122, 446):
        r, g, b, _ = px1[x, y]
        if r > 32 or g > 82:
            sm_px[x, y] = 255
sub_mask = sub_mask.filter(ImageFilter.MaxFilter(5))
sm_px = sub_mask.load()

for x in range(120, 448):
    y = 542
    while y < 636:
        if sm_px[x, y] > 0:
            y_start = y
            while y < 636 and sm_px[x, y] > 0:
                y += 1
            y_end = y
            c_top = bpx[x, max(540, y_start - 1)]
            c_bot = bpx[x, min(638, y_end)]
            span = max(1, y_end - y_start)
            for yi in range(y_start, y_end):
                t = (yi - y_start) / span
                bpx[x, yi] = (
                    int(c_top[0] * (1 - t) + c_bot[0] * t),
                    int(c_top[1] * (1 - t) + c_bot[1] * t),
                    int(c_top[2] * (1 - t) + c_bot[2] * t),
                )
        else:
            y += 1

# 1d. Clean CTA button region (y: 638..728, x: 115..556) using multi-frame ground truth:
# - In `im3`, x=498..560, y=638..728 has the 100% unoccluded leather lounge armchair!
# - In `im2`, the CTA buttons sit higher (ending at y=699), so y=702..728 has the 100% real brass side-table edge & ambient shadow!
# - Between y=640 and y=702 (x=115..498), vertically interpolate between clean row y=639 (`bpx`) and clean row y=703 (`im2`)!
for y in range(638, 728):
    for x in range(498, 560):
        r3, g3, b3, _ = px3[x, y]
        bpx[x, y] = (r3, g3, b3)

for y in range(702, 729):
    for x in range(115, 498):
        r2, g2, b2, _ = px2[x, y]
        bpx[x, y] = (r2, g2, b2)

for x in range(115, 498):
    c_top = bpx[x, 639]
    c_bot = bpx[x, 703]
    span = 703 - 639
    for y in range(640, 703):
        t = (y - 639) / span
        st = t * t * (3 - 2 * t)
        bpx[x, y] = (
            int(c_top[0] * (1 - st) + c_bot[0] * st),
            int(c_top[1] * (1 - st) + c_bot[1] * st),
            int(c_top[2] * (1 - st) + c_bot[2] * st),
        )

# Lightly feather the seam at x=496..500, y=640..704
for y in range(640, 704):
    c_l = bpx[492, y]
    c_r = bpx[504, y]
    for x in range(493, 504):
        t = (x - 492) / 12.0
        bpx[x, y] = (
            int(c_l[0] * (1 - t) + c_r[0] * t),
            int(c_l[1] * (1 - t) + c_r[1] * t),
            int(c_l[2] * (1 - t) + c_r[2] * t),
        )


# ---------------------------------------------------------------------------
# 2. SAM 3 + SAM 2.1 + ViTMatte Soft-Alpha Layers
# ---------------------------------------------------------------------------
sam3_board = np.asarray(Image.open(MASKS_DIR / "sam3_departure_board.png").convert("L")) > 127
sam3_suitcase = np.asarray(Image.open(MASKS_DIR / "sam3_suitcase.png").convert("L")) > 127
sam3_table = np.asarray(Image.open(MASKS_DIR / "sam3_coffee_table.png").convert("L")) > 127
sam3_chair = np.asarray(Image.open(MASKS_DIR / "sam3_armchair.png").convert("L")) > 127
sam3_tag = np.asarray(Image.open(MASKS_DIR / "sam3_tag_ita.png").convert("L")) > 127

sam2_model = Sam2Model.from_pretrained(QWEN_ROOT / "models/sam2.1-hiera-small").to(device).eval()
sam2_proc = Sam2Processor.from_pretrained(QWEN_ROOT / "models/sam2.1-hiera-small")

board_box = [700, 125, 1605, 865]
inputs2 = sam2_proc(images=pil1, input_boxes=[[board_box]], return_tensors="pt").to(device)
with torch.inference_mode():
    out_b = sam2_model(**inputs2)
masks_b = sam2_proc.post_process_masks(out_b.pred_masks.cpu(), inputs2["original_sizes"].cpu())[0]
scores_b = out_b.iou_scores[0, 0].cpu().tolist()
sam2_board_mask = masks_b[0, int(np.argmax(scores_b))].numpy() > 0.5

del sam2_model, sam2_proc
torch.mps.empty_cache()

vm = VitMatteForImageMatting.from_pretrained(QWEN_ROOT / "models/vitmatte-small-composition-1k").to(device).eval().float()


def vitmatte_soft_alpha(pil_img: Image.Image, hard_bool: np.ndarray, band: int = 6) -> np.ndarray:
    target_w, target_h = 1664, 960
    pil_32 = pil_img.resize((target_w, target_h), Image.Resampling.BILINEAR)
    hard_u8 = (hard_bool.astype(np.uint8)) * 255
    m_img = Image.fromarray(hard_u8).resize((target_w, target_h), Image.Resampling.NEAREST)
    fg = m_img.filter(ImageFilter.MinFilter(2 * band + 1))
    bg_f = m_img.filter(ImageFilter.MaxFilter(2 * band + 1))
    trimap = np.zeros((target_h, target_w), dtype=np.uint8)
    trimap[np.asarray(bg_f) > 127] = 128
    trimap[np.asarray(fg) > 127] = 255

    mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
    img_t = torch.from_numpy(np.array(pil_32, copy=True)).float().permute(2, 0, 1)[None] / 255.0
    rgb_norm = (img_t - mean) / std
    trim_f = torch.from_numpy(np.asarray(trimap).astype(np.float32) / 255.0)[None, None]
    trim_norm = (trim_f - mean[:, :1]) / std[:, :1]
    pixel_values = torch.cat([rgb_norm, trim_norm], dim=1)
    with torch.inference_mode():
        alpha = vm(pixel_values=pixel_values.to(device)).alphas[0, 0].float().cpu()
    a = np.asarray(
        Image.fromarray((alpha.numpy() * 255).clip(0, 255).astype(np.uint8)).resize(
            pil_img.size, Image.Resampling.BILINEAR
        )
    )
    return a


yy, xx = np.mgrid[0:H, 0:W]
table_ellipse = (((xx - 1140) / 320.0) ** 2 + ((yy - 925) / 68.0) ** 2) <= 1.0
sofa_fg = sam3_chair & (xx < 470) & (yy > 740)
suitcase_fg = sam3_suitcase & (yy > 680)
fg_hard = suitcase_fg | sam3_table | table_ellipse | sofa_fg
fg_alpha = vitmatte_soft_alpha(pil1, fg_hard, band=5)
fg_rgba = np.dstack([np.asarray(pil1), fg_alpha])
Image.fromarray(fg_rgba).save(PUBLIC_DIR / "fg-luggage-layer.png")

# Board hard mask: SAM 3 + SAM 2.1 consensus + right hanging tag minus foreground suitcase/table
board_with_tag_hard = (sam3_board | sam2_board_mask | (sam3_tag & (xx > 1470))) & (~suitcase_fg) & (~table_ellipse)
board_with_tag_alpha = vitmatte_soft_alpha(pil1, board_with_tag_hard, band=5)

# For `board-chassis-layer.png`, exclude the hanging tag rectangle (x: 1480..1604, y: 230..535)
# because `SplitFlapBoard.tsx` renders the active destination's tag (`tag-ita.png` / `tag-jpn.png` / `tag-mar.png`)
# directly at `(1480, 230, 1602, 535)`! That way `ITA` never peeks out behind `JPN` or `MAR`!
board_alpha = board_with_tag_alpha.copy()
board_alpha[230:535, 1480:1604] = 0

# Darken the 5 center split-flap row cavities in board-chassis-layer.png so dynamic 3D flaps sit over a dark mechanical recess
board_rgb = Image.fromarray(np.asarray(pil1).copy())
draw = ImageDraw.Draw(board_rgb)
ROW_CAVITIES = [
    [(874, 267), (1358, 241), (1358, 334), (874, 354)],
    [(874, 360), (1358, 343), (1358, 429), (874, 443)],
    [(874, 448), (1358, 437), (1358, 524), (874, 530)],
    [(874, 535), (1358, 532), (1358, 620), (874, 619)],
    [(874, 623), (1359, 626), (1359, 718), (874, 709)],
    [(1368, 623), (1469, 625), (1469, 720), (1368, 716)],
]
for poly in ROW_CAVITIES:
    draw.polygon(poly, fill=(13, 18, 26))

board_rgba = np.dstack([np.asarray(board_rgb), board_alpha])
Image.fromarray(board_rgba).save(PUBLIC_DIR / "board-chassis-layer.png")

# ---------------------------------------------------------------------------
# 3. Build Registered ITA / JPN / MAR Tag Assets (`122x305` at `1480, 230, 1602, 535`)
# ---------------------------------------------------------------------------
tag_box = (1480, 230, 1602, 535)
tw, th = tag_box[2] - tag_box[0], tag_box[3] - tag_box[1]  # 122 x 305
tag_alpha_ita = Image.fromarray(board_with_tag_alpha[230:535, 1480:1602])

# Save `tag-ita.png`
tag_ita_rgba = im1.crop(tag_box)
tag_ita_rgba.putalpha(tag_alpha_ita)
tag_ita_rgba.save(PUBLIC_DIR / "tag-ita.png")

# For `tag-jpn.png`, compute a tight alpha mask for `im4` in `(1480, 230, 1602, 535)`
# where the right window glass (blue sky/blur at x > 65 in crop) is transparent
crop4_rgb = np.asarray(im4.crop(tag_box).convert("RGB"), dtype=np.float32)
crop1_rgb = np.asarray(im1.crop(tag_box).convert("RGB"), dtype=np.float32)
# Window background color at the right edge of the crop (`x=118..121`)
win_col = crop4_rgb[:, 116:122, :].mean(axis=1, keepdims=True)
dist_to_win4 = np.linalg.norm(crop4_rgb - win_col, axis=2)
jpn_alpha_np = np.asarray(tag_alpha_ita).copy()
# Where `im4` shows window glass (x > 75 in crop and color close to window glass), make transparent
for y_c in range(70, 290):
    for x_c in range(75, tw):
        if dist_to_win4[y_c, x_c] < 24.0:
            jpn_alpha_np[y_c, x_c] = 0
jpn_alpha_img = Image.fromarray(jpn_alpha_np).filter(ImageFilter.GaussianBlur(radius=0.6))
tag_jpn_rgba = im4.crop(tag_box)
tag_jpn_rgba.putalpha(jpn_alpha_img)
tag_jpn_rgba.save(PUBLIC_DIR / "tag-jpn.png")

# For `tag-mar.png`, align the AI-generated `tag_morocco_1793016566454.jpg` to `im1.crop(tag_box)`!
mar_gen = Image.open(BRAIN_DIR / "tag_morocco_1793016566454.jpg").convert("RGB")
# Find the crop inside `mar_gen` that best matches `im1.crop(tag_box)` on the top rigging (y=0..85)
# `tag_ita` has aspect ratio 122 / 305 = 0.400. `mar_gen` is 768 x 1376 (aspect 0.558).
# Let's resize `mar_gen` so its height is 312, then search horizontal offset `dx` and vertical offset `dy`
best_score = 1e18
best_crop = None
ref_top = crop1_rgb[5:85, 10:105, :]
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

# Composite the aligned Moroccan crimson-and-cream tag card onto `tag_ita`'s exact top rigging for 100% pixel-locked steel seam
tag_mar_rgb = im1.crop(tag_box).convert("RGB")
best_crop_rgba = best_crop.convert("RGBA")
# Soft blend from y=32..100 so top steel seam is 100% identical to `im1` while the crimson strap & `MAR` tag come from `best_crop`
blend_mask = Image.new("L", (tw, th), 0)
bm_px = blend_mask.load()
for y_c in range(30, 275):
    for x_c in range(18, 118):
        wy = min(1.0, (y_c - 30) / 25.0) * min(1.0, (275 - y_c) / 20.0)
        wx = min(1.0, (x_c - 18) / 10.0)
        bm_px[x_c, y_c] = int(255 * wy * wx)
tag_mar_rgb.paste(best_crop, (0, 0), blend_mask)
tag_mar_rgba = tag_mar_rgb.convert("RGBA")
tag_mar_rgba.putalpha(tag_alpha_ita)
tag_mar_rgba.save(PUBLIC_DIR / "tag-mar.png")

# ---------------------------------------------------------------------------
# 4. Save Photorealistic AI-Generated Morocco Split-Flap Photos (`640x360`)
# ---------------------------------------------------------------------------
m1 = Image.open(BRAIN_DIR / "photo_morocco_1_1793016471540.jpg").convert("RGB")
m1.resize((640, 360), Image.Resampling.LANCZOS).save(PUBLIC_DIR / "photo-morocco-1.png")

m2 = Image.open(BRAIN_DIR / "photo_morocco_2_1793016492318.jpg").convert("RGB")
m2.resize((640, 360), Image.Resampling.LANCZOS).save(PUBLIC_DIR / "photo-morocco-2.png")

# ---------------------------------------------------------------------------
# 5. Clean Background Halo & Hanging Tag Footprint on `bg-landscape-clean.png`
# ---------------------------------------------------------------------------
bg_arr = np.array(bg, dtype=np.float32)

# Clean the hanging tag area on `bg_arr` (y: 230..538, x: 1478..1606) using the clean window glass at x=1610..1655
for y in range(230, 538):
    c_win = bg_arr[y, 1612:1650].mean(axis=0)
    for x in range(1478, 1606):
        bg_arr[y, x] = c_win

# Also clean a 16px interior margin along the left diagonal edge of the board on `bg_arr`
# (ONLY inside `board_with_tag_hard`, NEVER outside/above the crown!) so 3D parallax shifting never shows a double edge
board_inner = np.asarray(
    Image.fromarray((board_with_tag_hard.astype(np.uint8)) * 255).filter(ImageFilter.MinFilter(29))
) > 127
inner_rim = board_with_tag_hard & (~board_inner)

for y in range(130, 865):
    x_diag = int(1044 - 0.578 * y)
    hx_left = np.where(inner_rim[y, :x_diag])[0]
    if len(hx_left) > 0:
        bg_arr[y, hx_left] = bg_arr[y, 575:605].mean(axis=0)
    hx_right = np.where(inner_rim[y, x_diag:])[0] + x_diag
    for x in hx_right:
        if y < 220:
            # Sample clean sky/window 8px above the crown edge at this x
            top_y_at_x = int(np.where(board_with_tag_hard[:, x])[0].min()) if board_with_tag_hard[:, x].any() else y
            bg_arr[y, x] = bg_arr[max(8, top_y_at_x - 6), x]
        elif x > 1420:
            bg_arr[y, x] = bg_arr[y, min(W - 1, 1612 + (x - 1420) // 3)]

Image.fromarray(np.clip(bg_arr, 0, 255).astype(np.uint8)).save(PUBLIC_DIR / "bg-landscape-clean.png")
print("Successfully finalized all layers, photorealistic Morocco photos, and registered baggage tags!")
