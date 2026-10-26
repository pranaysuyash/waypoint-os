"""Rebuild bg-landscape-clean.png (fixing [P0-1] lower-left blue smudge while preserving 100% original crown sky, right window mullion, and lounge armchairs),
and generate bg-landscape-frame3-clean.png + board-chassis-frame3-layer.png for Frame 3 (provenance_brief mode)."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BRAIN_DIR = Path("/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f")
PUBLIC_DIR = Path("/Users/pranay/Projects/travel_agency_agent/frontend/public/landing/departure-board")

im1 = Image.open(PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-1.png").convert("RGBA")
im2 = Image.open(PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-2.png").convert("RGBA")
im3 = Image.open(PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-3.png").convert("RGBA")
im4 = Image.open(PUBLIC_DIR / "concepts/chatgpt-concept-2026-10-26-4.png").convert("RGBA")

W, H = im1.size
px1 = im1.load()
px2 = im2.load()
px3 = im3.load()
px4 = im4.load()

# ---------------------------------------------------------------------------
# 1. Build Clean Background Landscape Layer (`bg-landscape-clean.png`)
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

# 1b. Mask top-left nav (y: 22..76, x: 118..925) and eyebrow + headline (y: 145..538, x: 120..535)
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

# 1c. Clean the 3-line subcopy using each line's exact vertical band and immediately adjacent unoccluded rows:
# - Line 1 ("Turn scattered travel requests"): y=552..574, x=124..446 -> interpolate between clean rows y=550 and y=576
# - Line 2 ("into quote-ready briefs your team"): y=580..601, x=124..482 -> interpolate between clean rows y=578 and y=603
# - Line 3 ("can actually use."): y=607..628, x=124..304 -> interpolate between clean rows y=605 and y=630
SUBCOPY_BANDS = [
    (550, 576, 124, 446),
    (578, 603, 124, 482),
    (605, 630, 124, 304),
]
for y_top, y_bot, x_left, x_right in SUBCOPY_BANDS:
    span = y_bot - y_top
    for x in range(x_left, x_right + 1):
        c_top = bpx[x, y_top]
        c_bot = bpx[x, y_bot]
        for y in range(y_top + 1, y_bot):
            t = (y - y_top) / span
            st = t * t * (3 - 2 * t)
            bpx[x, y] = (
                int(c_top[0] * (1 - st) + c_bot[0] * st),
                int(c_top[1] * (1 - st) + c_bot[1] * st),
                int(c_top[2] * (1 - st) + c_bot[2] * st),
            )

# 1d. Clean CTA button region (y: 653..728, x: 128..556):
# - For x=472..556 (where the right side of "Book a demo" sits over the dark leather armchair in `im1`),
#   only mask the thin white outline/text of "Book a demo" and interpolate vertically across the 3px border,
#   preserving 100% of `im1`'s real leather armchair!
btn_r_mask = Image.new("L", (W, H), 0)
br_px = btn_r_mask.load()
for y in range(648, 722):
    for x in range(472, 556):
        r, g, b, _ = px1[x, y]
        if b > 72 or (r > 110 and g > 100 and b > 65):
            br_px[x, y] = 255
btn_r_mask = btn_r_mask.filter(ImageFilter.MaxFilter(5))
br_px = btn_r_mask.load()

for x in range(472, 556):
    y = 646
    while y < 724:
        if br_px[x, y] > 0:
            y_start = y
            while y < 724 and br_px[x, y] > 0:
                y += 1
            y_end = y
            c_top = bpx[x, max(644, y_start - 1)]
            c_bot = bpx[x, min(726, y_end)]
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

# - For x=128..475, y=702..729: copy `im2`'s real unoccluded dark ambient lounge shadow below `im2`'s buttons!
for y in range(702, 729):
    for x in range(128, 476):
        r2, g2, b2, _ = px2[x, y]
        bpx[x, y] = (r2, g2, b2)

# - For x=128..475, y=654..702: vertically interpolate between clean row y=653 (`im1`) and clean row y=702 (`im2`)
for x in range(128, 476):
    c_top = bpx[x, 653]
    c_bot = bpx[x, 702]
    span = 702 - 653
    for y in range(654, 702):
        t = (y - 653) / span
        st = t * t * (3 - 2 * t)
        bpx[x, y] = (
            int(c_top[0] * (1 - st) + c_bot[0] * st),
            int(c_top[1] * (1 - st) + c_bot[1] * st),
            int(c_top[2] * (1 - st) + c_bot[2] * st),
        )

# Feather horizontal transition at x=468..480, y=654..728
for y in range(654, 728):
    c_l = bpx[467, y]
    c_r = bpx[481, y]
    for x in range(468, 481):
        t = (x - 467) / 14.0
        bpx[x, y] = (
            int(c_l[0] * (1 - t) + c_r[0] * t),
            int(c_l[1] * (1 - t) + c_r[1] * t),
            int(c_l[2] * (1 - t) + c_r[2] * t),
        )

# 1e. Keep 100% untouched right window mullion on `bg-landscape-clean.png` and ensure `tag-ita.png`, `tag-jpn.png`, and `tag-mar.png`
# are 100% opaque 122x305 patches whose right edge matches `im1`'s window mullion with zero seam!
bg.save(PUBLIC_DIR / "bg-landscape-clean.png")

tag_box = (1480, 230, 1602, 535)
tw, th = 122, 305
crop1 = im1.crop(tag_box).convert("RGB")
crop4 = im4.crop(tag_box).convert("RGB")
crop1.convert("RGBA").save(PUBLIC_DIR / "tag-ita.png")

c1_np = np.asarray(crop1, dtype=np.float32)
c4_np = np.asarray(crop4, dtype=np.float32)
jpn_np = c4_np.copy()
for x_c in range(112, tw):
    t = (x_c - 112) / (tw - 1 - 112)
    jpn_np[:, x_c, :] = c4_np[:, x_c, :] * (1 - t) + c1_np[:, x_c, :] * t
Image.fromarray(np.clip(jpn_np, 0, 255).astype(np.uint8)).convert("RGBA").save(PUBLIC_DIR / "tag-jpn.png")

mar_gen = Image.open(BRAIN_DIR / "tag_morocco_1793016566454.jpg").convert("RGB")
ref_top = c1_np[5:85, 10:105, :]
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
    for x_c in range(18, 114):
        wy = min(1.0, (y_c - 30) / 25.0) * min(1.0, (275 - y_c) / 20.0)
        wx = min(1.0, (x_c - 18) / 10.0) * min(1.0, (114 - x_c) / 10.0)
        bm_px[x_c, y_c] = int(255 * wy * wx)
tag_mar_rgb.paste(best_crop, (0, 0), blend_mask)
tag_mar_rgb.convert("RGBA").save(PUBLIC_DIR / "tag-mar.png")

# ---------------------------------------------------------------------------
# 2. Build Frame 3 Background (`bg-landscape-frame3-clean.png`) & Chassis (`board-chassis-frame3-layer.png`)
# ---------------------------------------------------------------------------
bg3_arr = np.array(im3.convert("RGB"), dtype=np.float32)
bg1_arr = np.array(bg, dtype=np.float32)
im1_rgb_arr = np.array(im1.convert("RGB"), dtype=np.float32)

# 2a. Clean top-right "Sign in" and "Book a demo ->" on bg3 (x: 1275..1575, y: 16..83)
for x in range(1275, 1575):
    c_top = bg3_arr[14, x]
    c_bot = bg3_arr[84, x]
    for y in range(16, 83):
        t = (y - 16) / (83 - 16)
        st = t * t * (3 - 2 * t)
        bg3_arr[y, x] = c_top * (1 - st) + c_bot * st

# 2b. Copy top navbar clean royal-blue wall (y: 0..95, x: 0..945) from bg1_arr
for y in range(0, 95):
    for x in range(0, 945):
        w = 1.0 if x < 925 else (945 - x) / 20.0
        bg3_arr[y, x] = bg1_arr[y, x] * w + bg3_arr[y, x] * (1.0 - w)

# 2c. Copy left side (y: 95..728, x: 0..576) from bg1_arr (covers all curved provenance wires up to the Frame 3 left rigging!)
for y in range(95, 728):
    x_lim = 562 if y < 355 else 576
    for x in range(0, x_lim):
        w = 1.0 if x < x_lim - 5 else (x_lim - x) / 5.0
        bg3_arr[y, x] = bg1_arr[y, x] * w + bg3_arr[y, x] * (1.0 - w)

# 2d. Copy lower-left floor & armchair (y: 728..905, x: 0..565) from unoccluded im1_rgb_arr
for y in range(728, 905):
    for x in range(0, 565):
        w = 1.0 if x < 555 else (565 - x) / 10.0
        bg3_arr[y, x] = im1_rgb_arr[y, x] * w + bg3_arr[y, x] * (1.0 - w)

# 2e. Clean the 4 wire tips on the left rigging & category plate bevel (x: 558..624, y: 332..678) using a dilated mask
wire_mask = Image.new("L", (W, H), 0)
wm_px = wire_mask.load()
for y in range(332, 678):
    for x in range(558, 624):
        r, g, b = bg3_arr[y, x]
        is_wire = (
            (r > 130 and g > 110 and b < 115 and 334 <= y <= 362)
            or (b > 115 and g > 105 and r < 130 and 408 <= y <= 438)
            or (g > 115 and g - r > 15 and 486 <= y <= 516)
            or (r > 110 and b > 120 and r - g > 12 and 648 <= y <= 678)
        )
        if is_wire:
            wm_px[x, y] = 255
wire_mask = wire_mask.filter(ImageFilter.MaxFilter(7))
wm_px = wire_mask.load()

for x in range(556, 625):
    y = 330
    while y < 680:
        if wm_px[x, y] > 0:
            y_s = y
            while y < 680 and wm_px[x, y] > 0:
                y += 1
            y_e = y
            c_t = bg3_arr[max(328, y_s - 1), x]
            c_b = bg3_arr[min(682, y_e), x]
            span = max(1, y_e - y_s)
            for yi in range(y_s, y_e):
                t = (yi - y_s) / span
                bg3_arr[yi, x] = c_t * (1 - t) + c_b * t
        else:
            y += 1

# 2f. Darken the 5 split-flap row cavities on bg3_pil (x: 777..1168) so our dynamic DOM split-flaps sit inside dark mechanical recesses
bg3_pil = Image.fromarray(np.clip(bg3_arr, 0, 255).astype(np.uint8))
draw3 = ImageDraw.Draw(bg3_pil)
FRAME3_CAVITIES = [
    [(777, 297), (1168, 278), (1168, 365), (777, 371)],
    [(777, 375), (1168, 368), (1168, 450), (777, 456)],
    [(777, 460), (1168, 453), (1168, 538), (777, 540)],
    [(777, 543), (1168, 541), (1168, 624), (777, 619)],
    [(777, 623), (1168, 627), (1168, 714), (777, 704)],
]
for poly in FRAME3_CAVITIES:
    draw3.polygon(poly, fill=(13, 18, 26))

bg3_pil.save(PUBLIC_DIR / "bg-landscape-frame3-clean.png")

# Build `board-chassis-frame3-layer.png` with soft alpha around the Frame 3 board (x: 558..1268, y: 165..845)
ch3_rgba = np.zeros((H, W, 4), dtype=np.uint8)
bg3_final_np = np.asarray(bg3_pil)
ch3_rgba[165:845, 558:1268, :3] = bg3_final_np[165:845, 558:1268, :]
mask3 = Image.new("L", (W, H), 0)
d_m3 = ImageDraw.Draw(mask3)
d_m3.polygon(
    [(605, 195), (1258, 165), (1268, 250), (1268, 825), (558, 815), (562, 290)],
    fill=255,
)
mask3 = mask3.filter(ImageFilter.GaussianBlur(radius=1.5))
ch3_rgba[:, :, 3] = np.asarray(mask3)
Image.fromarray(ch3_rgba).save(PUBLIC_DIR / "board-chassis-frame3-layer.png")

print("Successfully rebuilt clean bg-landscape-clean.png, bg-landscape-frame3-clean.png, and board-chassis-frame3-layer.png!")
