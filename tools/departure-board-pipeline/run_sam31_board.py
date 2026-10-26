"""Run SAM 3.1 (sam3.1_multiplex.pt) + ViTMatte on the Waypoint Departure Board reference frames."""
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

# Load HF_TOKEN from adshot/.env.local if needed (never print token)
env_local = Path("/Users/pranay/Projects/adshot/.env.local")
if env_local.exists():
    for line in env_local.read_text().splitlines():
        if line.startswith("HF_TOKEN="):
            os.environ["HF_TOKEN"] = line.split("=", 1)[1].strip().strip('"').strip("'")

import torch  # noqa: E402
import torch._dynamo  # noqa: E402, F401 — must import before triton stub path

QWEN_ROOT = Path("/Users/pranay/Projects/qwen-image-21-local")
sys.path.insert(0, str(QWEN_ROOT / "third_party/sam3"))
sys.path.insert(0, str(QWEN_ROOT / "third_party/sam3-pilot-stubs"))

from huggingface_hub import hf_hub_download  # noqa: E402
from sam3.model_builder import build_sam3_image_model, download_ckpt_from_hf  # noqa: E402
from sam3.model.sam3_image_processor import Sam3Processor  # noqa: E402

OUT_DIR = Path("/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f/scratch/sam31_masks")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMG1_PATH = Path("/Users/pranay/Projects/travel_agency_agent/frontend/public/landing/departure-board/concepts/chatgpt-concept-2026-10-26-1.png")

t0 = time.perf_counter()
ckpt = None
candidates = [
    QWEN_ROOT / "models/sam3.1/sam3.1_multiplex.pt",
]
for c in candidates:
    if c.exists():
        ckpt = str(c)
        break

if ckpt is None:
    try:
        ckpt = hf_hub_download(repo_id="facebook/sam3.1", filename="sam3.1_multiplex.pt", local_files_only=True)
        print("Found cached SAM 3.1 checkpoint:", ckpt, flush=True)
    except Exception as e:
        print("Local cache miss, trying download_ckpt_from_hf(version='sam3.1'):", e, flush=True)
        ckpt = download_ckpt_from_hf(version="sam3.1")
        print("Downloaded SAM 3.1 checkpoint:", ckpt, flush=True)

device = "mps"
model = build_sam3_image_model(device=device, checkpoint_path=ckpt, load_from_HF=False).float()
load_s = round(time.perf_counter() - t0, 2)
print(f"SAM 3.1 (sam3.1_multiplex.pt) loaded on {device} in {load_s}s", flush=True)

processor = Sam3Processor(model)

pil1 = Image.open(IMG1_PATH).convert("RGB")
state1 = processor.set_image(pil1)

CONCEPTS = [
    "departure board",
    "metallic departure board monument",
    "blue suitcase",
    "suitcase",
    "wooden coffee table",
    "blue armchair",
    "potted plant",
    "floor lamp",
    "hanging luggage tag",
]

summary = {"model": "SAM 3.1 (sam3.1_multiplex.pt)", "checkpoint": str(ckpt), "load_s": load_s, "prompts": {}}

for text in CONCEPTS:
    t1 = time.perf_counter()
    with torch.inference_mode():
        out = processor.set_text_prompt(state=state1, prompt=text)
    torch.mps.synchronize()
    dt = round(time.perf_counter() - t1, 3)
    masks = out["masks"]
    scores = [round(float(s), 3) for s in out["scores"][:5]] if len(out["scores"]) else []
    boxes = [[round(float(v), 1) for v in b] for b in out["boxes"][:5]] if len(out["boxes"]) else []
    n = len(masks)
    safe = text.replace(" ", "_")
    if n > 0:
        combined = np.zeros((pil1.height, pil1.width), dtype=bool)
        for idx, m in enumerate(masks):
            m_np = np.asarray(m).squeeze() > 0.5
            if m_np.ndim == 2:
                combined |= m_np
                if idx < 3:
                    Image.fromarray(m_np.astype(np.uint8) * 255).save(OUT_DIR / f"sam31_{safe}_{idx}.png")
        Image.fromarray(combined.astype(np.uint8) * 255).save(OUT_DIR / f"sam31_{safe}_union.png")
    print(f"SAM 3.1 '{text}': {n} mask(s) in {dt}s | scores={scores} | boxes={boxes}", flush=True)
    summary["prompts"][text] = {"count": n, "seconds": dt, "scores": scores, "boxes": boxes}

del model, processor
torch.mps.empty_cache()

from transformers import VitMatteForImageMatting  # noqa: E402

vm = VitMatteForImageMatting.from_pretrained(QWEN_ROOT / "models/vitmatte-small-composition-1k").to(device).eval().float()


def refine_with_vitmatte(pil_img: Image.Image, hard_u8: np.ndarray, band: int = 10) -> np.ndarray:
    m_img = Image.fromarray(hard_u8)
    fg = m_img.filter(ImageFilter.MinFilter(2 * band + 1))
    bg = m_img.filter(ImageFilter.MaxFilter(2 * band + 1))
    trimap = np.zeros(pil_img.size[::-1], dtype=np.uint8)
    trimap[np.asarray(bg) > 127] = 128
    trimap[np.asarray(fg) > 127] = 255
    mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
    img_t = torch.from_numpy(np.asarray(pil_img)).float().permute(2, 0, 1)[None] / 255.0
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


board_mask_path = OUT_DIR / "sam31_departure_board_0.png"
if board_mask_path.exists():
    board_hard = np.asarray(Image.open(board_mask_path).convert("L"))
    board_alpha = refine_with_vitmatte(pil1, board_hard, band=8)
    Image.fromarray(board_alpha).save(OUT_DIR / "sam31_departure_board_vitmatte_alpha.png")
    rgba = np.dstack([np.asarray(pil1), board_alpha])
    Image.fromarray(rgba).save(OUT_DIR / "sam31_departure_board_cutout.png")
    print("Saved ViTMatte refined departure board cutout", flush=True)

(OUT_DIR / "sam31_summary.json").write_text(json.dumps(summary, indent=2))
print("All SAM 3.1 + ViTMatte outputs saved to", OUT_DIR, flush=True)
