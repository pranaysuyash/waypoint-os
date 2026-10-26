# Waypoint Departure Board — 3-Layer CV Segmentation & Gauntlet Verification Pipeline

This directory preserves the durable, reusable computer-vision segmentation, background restoration, asset registration, and Playwright visual verification scripts used to build and audit the Waypoint B2B Departure Board landing page (`/`).

## Scripts

1. **`run_sam31_board.py`**
   - Runs **SAM 3.1** (`sam3.1_multiplex.pt`) + **ViTMatte** (`vitmatte-small-composition-1k`) on the reference concept frames (`frontend/public/landing/departure-board/concepts/chatgpt-concept-2026-10-26-{1..4}.png`) using Apple Silicon MPS acceleration.
   - Extracts concept masks for the brushed-steel departure board monument, foreground carry-on suitcase, wooden coffee table, blue lounge armchair, and hanging IATA luggage tag.

2. **`finalize_three_layers.py`**
   - Combines SAM 3 + SAM 2.1 (`sam2.1-hiera-small`) + ViTMatte soft alpha matting to produce the 3 parallax layers in `frontend/public/landing/departure-board/`:
     - `bg-landscape-clean.png` (Layer 1: clean royal-blue diagonal + sunlit airport terminal lounge with baked-in text/buttons removed)
     - `board-chassis-layer.png` (Layer 2: physical brushed-steel Solari departure board with darkened 3D split-flap row cavities)
     - `fg-luggage-layer.png` (Layer 3: foreground armchair, coffee table with boarding pass & passport, and ribbed carry-on suitcase)
   - Resizes and registers the AI-generated destination photography (`photo-morocco-1.png`, `photo-morocco-2.png`) and baggage tags (`tag-ita.png`, `tag-jpn.png`, `tag-mar.png`).

3. **`fix_window_and_crown.py` & `fix_tags.py`**
   - Restores 100% untouched sky and window mullions above the departure board crown (`y < 245`) and along the right window frame (`x >= 1475`) in `bg-landscape-clean.png`, and feathers the `ITA`/`JPN`/`MAR` hanging tag patches so they blend with zero visible seam.

4. **`capture_after_states.mjs`**
   - Automated Playwright visual capture script that launches headless Chrome at the exact `1672x941` reference viewport, exercises all 4 reference states (`Frame 1: Italy Hero`, `Frame 2: Voice Ingest + Finalizing Dates`, `Frame 3: Provenance Wires + Brief Drawer`, `Frame 4a/4b: Japan & Morocco Switched`), and saves deterministic screenshots for the **Gauntlet Loop** Blind Critic (`Docs/GAUNTLET_LOOP_DOCTRINE.md`).
