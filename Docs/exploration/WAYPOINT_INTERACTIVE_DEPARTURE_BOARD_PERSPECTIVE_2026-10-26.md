# Waypoint Interactive Departure Board — First-Principles Visual & Engineering Perspective

- **Date:** 2026-10-26
- **Status:** Exploration & Architecture Proposal (Awaiting Owner Alignment Before Build)
- **Reference Assets Imported:**
  - `frontend/public/landing/departure-board/concepts/chatgpt-concept-2026-10-26-1.png` (Frame 1: Default Resolved Hero — "Every inquiry. Under control.")
  - `frontend/public/landing/departure-board/concepts/chatgpt-concept-2026-10-26-2.png` (Frame 2: Live Voice/Text Ingestion & Mid-Flip Motion Blur — "From inquiry to itinerary.")
  - `frontend/public/landing/departure-board/concepts/chatgpt-concept-2026-10-26-3.png` (Frame 3: Provenance Wiring & Structured Brief Drawer — "See how it organizes the request.")
  - `frontend/public/landing/departure-board/concepts/chatgpt-concept-2026-10-26-4.png` (Frame 4: Interactive Inquiry Switcher Dock & Cascade — "Explore different inquiries: Japan / Morocco / Italy")

---

## 1. Key Observation: The 4 Images Are One Unified State Machine

Examining the four `1672×941` concept frames side by side reveals that they are **not** four separate design directions—they are **four sequential keyframes of a single interactive product experience** sharing the exact same camera frustum, lighting, brushed-steel monument, and diagonal cobalt-blue editorial split:

1. **Frame 1 (Settled Hero State):**
   - Left editorial field: Deep cobalt/royal blue (`#0035B8` → `#001D75`) cut at a ~62° diagonal across the sunlit airport terminal lounge.
   - Board state: Settled on `ITALY` / `4 TRAVELERS` / `10 DAYS` / `NEED CONFIRMATION` (signal-yellow hazard flaps) / `CULTURE + COAST`.
2. **Frame 2 (Live Ingestion & Candidate Scanning State):**
   - Floating glassmorphic `Incoming request (10:14 AM)` card with raw client copy plus a playable `0:24` voice-note waveform, feeding the board through a neon-blue spline arrow.
   - Flaps are mid-rotation with **vertical directional motion blur** (`V/A` → `ITALY`), and Row 4 (`DATES`) is actively testing `APR 18 - 3 ?` with an amber glow bezel and floating `Finalizing dates...` pill before locking to `NEED CONFIRMATION`.
3. **Frame 3 (Provenance X-Ray & Brief Drawer State):**
   - Bottom-left: Multi-message WhatsApp/SMS inquiry thread (`9:14 AM – 9:20 AM`) with color-coded entity highlights (`Italy`, `4 of us`, `10 days?`, `food, history`, `Amalfi Coast?`, `guided experiences`).
   - Four color-coded cubic-bezier wires (yellow, cyan, green, purple) visually connect each highlighted phrase to the left bezel of Rows 1, 2, 3, and 5—while Row 4 (`DATES`) visibly lacks a wire because the traveler wrote *"Not sure exact dates yet"*.
   - Right side: Crisp white product drawer (`From message to brief`) displaying the structured Waypoint brief, including `2 couples (inferred)` and `⚠️ Needs confirmation`.
4. **Frame 4 (Multi-Inquiry Switcher Dock & Full-Board Re-Index):**
   - Bottom frosted-glass dock (`Explore different inquiries`: **Japan · Culture + Food**, **Morocco · Adventure**, **Italy · Culture + Coast**).
   - Switching from Italy to Japan cascades the letter tiles (`J _ A P A N`, `2 6 TRAVELERS`, `1 0 4 DAYS`, `CULTURE + F O O D`), flips the **two embedded double-wide photo flaps** (Colosseum/Amalfi → Chureito Pagoda/Mt. Fuji), flips the bottom-right icon tile (`🌴` → `⛩️`), and swaps the **physical hanging IATA baggage tag** on the right side of the steel chassis (`ITA` → `JPN` with the red sun disc).

---

## 2. Why Typical Web Implementations Fail Visually (And How We Beat the Reference)

To make the live web implementation look **exact or better** than the 4 reference frames, we must solve five visual details that standard CSS split-flap demos get wrong:

### 2.1 Exact 2-Point Perspective Homography (`matrix3d`), Not Naive `rotateY()`
- In the artwork, the board is viewed from a low-ish hero camera with the top crown sloping upward left-to-right (`y=188` → `y=125`) while the base plinth is nearly level (`y=790` → `y=805`).
- A naive `transform: perspective(1000px) rotateY(-12deg)` creates a symmetric trapezoid that fights the background architecture.
- **Solution:** Keep the exact photographic lounge, diagonal cobalt-blue cut, brushed-steel outer monument, and foreground Rimowa luggage/table by surgically cleaning the 5 row cavities into an empty dark backplate, and project the live interactive 3D board plane using an **exact 4-corner projective homography (`matrix3d`)** calibrated to the sub-pixel corners of the steel chassis recess (with local 3D `rotateX` flap hinges operating in perspective space).

### 2.2 Heterogeneous Mechanical Modules (Not Just Text Cells)
The reference board is rich because its 5 rows mix four distinct mechanical module types:
1. **Left Category Plates (Col 1):** 5 wide cream plates (`DESTINATION`, `TRAVELERS`, `DURATION`, `DATES`, `TRIP STYLE`) with a signal-yellow left edge, icon, and left-bezel wire anchor points.
2. **Standard & High-Density Split-Flap Character Cells (Col 2):**
   - Cream die-cut flaps (`#EEE8DA` → `#D6CEBC`) with a `3px` corner radius, center horizontal axle split, side hinge pins, top-lip recess shadow, and warm bottom bounce light.
3. **Double-Wide Mechanical Photo Split-Flaps (Rows 1 & 3, right side of Col 2):**
   - Two-cell-wide photographic split-flaps that physically hinge across their horizontal midpoint to reveal destination & vibe photography (Colosseum + Amalfi for Italy; Chureito Pagoda + Mt. Fuji Cherry Blossoms for Japan; Koutoubia Mosque + Erg Chebbi Sahara Dunes for Morocco).
4. **Dual-Mode Epistemic Hazard Flaps (Row 4 `DATES`):**
   - During active scanning (Frame 2), Row 4 cycles single-line candidate characters (`APR 18 - 3 ?`) with an amber scanning halo and `Finalizing dates...` badge.
   - When the epistemic gate determines dates are unconfirmed (Frames 1, 3, 4), the first 7 cells flip into **signal-yellow two-line hazard flaps (`NEED / CONFIRMATION`)** while the remaining 3 cells flip to matte-black blanks.
5. **Right End-Cap Icon Flaps (Col 3) & Hanging Physical Baggage Tags (Right Chassis Rigging):**
   - 5 square mechanical icon tiles on the right edge (with Row 5 flipping contextually between Palm Tree, Torii Gate, and Desert Sun/Dunes) plus the physical hanging IATA luggage tag (`ITA` / `JPN` / `MAR`) on the right steel rigging and matching boarding pass on the foreground table.

### 2.3 Velocity-Driven Vertical Motion Blur & Lighting Physics
- In Frames 2 and 4, mid-flip tiles have realistic vertical shutter blur and mid-swing shading.
- **Solution:** Drive each cell with a deterministic requestAnimationFrame / Web Animations state machine that applies a dynamic vertical-only SVG `<feGaussianBlur stdDeviation="0, 4" />` while stepping at high velocity (`45–65ms` per drum step) and snaps to zero-blur crisp vector glyphs on the final mechanical stop (with a `1.5°` damped settle bounce).

### 2.4 Where Local Headless Blender 5.2.2 LTS Fits Best
- We verified `/Applications/Blender.app/Contents/MacOS/Blender` (`Blender 5.2.2 LTS`) is available locally.
- Rather than replacing the lush photographic airport lounge with a synthetic full-scene 3D render, the highest-leverage use of headless Blender (`bpy` + Cycles) is **targeted physical asset generation**:
  1. Generating clean, high-resolution PBR normal/occlusion/anisotropic-brushed-metal recess layers and empty cavity backplates where needed.
  2. Rendering perspective-matched, physically shaded hanging IATA baggage tags (`ITA`, `JPN`, `MAR`) and mechanical axle/hinge overlays with alpha channels that composite seamlessly onto the chassis.

### 2.5 Procedural Web Audio Solari Acoustics
- Instead of relying on a single repetitive `.mp3` loop, synthesize per-cell mechanical clacks via the Web Audio API (bandpass-filtered transient click + low-mid aluminum cabinet resonance, slight random pitch detune `±5%` and stereo pan mapped to the cell's X position on the board), gated strictly behind explicit user interaction / sound toggle.
