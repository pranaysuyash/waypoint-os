# The Gauntlet Loop Doctrine

**Canonical Workspace Path:** `/Users/pranay/Projects/GAUNTLET_LOOP_DOCTRINE.md`  
**Companion Skill:** `/Users/pranay/Projects/skills/gauntlet-loop/SKILL.md` (mirrored at `.agents/skills/gauntlet-loop/SKILL.md`)  
**Companion Eval Rules:** `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md`

---

## 1. Core Principle: Never Grade Your Own Homework Alone

When an AI agent builds a complex system or visual interface and then evaluates its own work in the same context window, **self-grading inflation** ("looks good to me" bias) is almost guaranteed:
- The builder remembers *how hard* a step was and excuses visual or geometric compromises.
- The builder pattern-matches on its own intent ("I wrote a `<ProvenanceAndBriefOverlay />` component, so Frame 3 is done") rather than inspecting pixel-level reality against the reference frame.

**The Gauntlet Loop** replaces single-pass self-congratulation with a closed, adversarial feedback loop:
1. **Honest Baseline Self-Audit (Iteration 0)** — The Builder loads the ground-truth references and its own live rendered screenshots side-by-side, scores every frame honestly (`1.0–10.0`), and fixes all self-evident gaps.
2. **Deterministic Live Evidence Capture** — Automated Playwright scripts capture every interactive state at the exact reference aspect ratio and viewport (`1672x941` or target dimensions), alongside unit/integration tests and static typechecks.
3. **Fresh-Context Blind Critic Subagent** — A separate, read-only critic subagent is launched with a **fresh context window** (zero builder memory, zero sunk-cost sympathy). It is given *only* the ground-truth reference frames/specs, the live rendered screenshots, and the source files, with explicit orders to hunt down every visual, geometric, typographic, color, layout, and behavioral discrepancy.
4. **Work-Item Promotion & Fix Pass** — Every defect found by the Blind Critic is promoted into a concrete work item per `AGENTIC_EVAL_RULES.md` (failure signature, affected layer, proposed fix, regression check) and fixed.
5. **Re-Capture & Re-Audit Until Gate Passes** — The loop repeats (`Fix → Live Screenshot Capture → Fresh Blind Critic Audit`) until **every frame and rubric dimension scores ≥ 9.5 / 10.0 with zero `P0` or `P1` defects** and all automated test suites pass.

---

## 2. The 6-Dimension Gauntlet Rubric

| Dimension | What the Blind Critic Audits | Pass Threshold |
| :--- | :--- | :--- |
| **1. Layout & Geometric Registration** | Do overlay coordinates, bounding boxes, aspect ratios, perspective skews (`skewY`), and element positions match the reference frames within sub-pixel/percentage tolerance? | `≥ 9.5 / 10` |
| **2. Typography, Hierarchy & Copy Fidelity** | Do headlines, eyebrows (including decorative flanking lines), subcopy, condensed/display glyph proportions, and multi-line cell splits match the exact copy and typographic feel of the reference? | `≥ 9.5 / 10` |
| **3. Color, Surface & Materiality** | Do glassmorphic cards, surface opacities, borders, shadows, neon glows, and light/dark contrast match the reference art direction (e.g., light frosted chat bubbles vs. dark navy cards, yellow pills vs. dark pills)? | `≥ 9.5 / 10` |
| **4. Asset & Segmentation Cleanliness** | Are multi-layer cutouts (SAM 3 / SAM 2.1 / ViTMatte), background plates, and AI-generated photographic assets free of blur patches, ghost halos, clipped corners, or procedural placeholders? | `≥ 9.5 / 10` |
| **5. Interactive Choreography & State Completeness** | Does every interactive state (hero, voice ingest scanning, provenance wires + brief drawer, inquiry switcher dock, 3D parallax, mechanical audio) transition cleanly and preserve primary CTAs? | `≥ 9.5 / 10` |
| **6. Engineering & Contract Hygiene** | Do TypeScript (`tsc --noEmit`), linter (`ruff` / `eslint`), unit tests, and accessibility selectors pass with zero regressions or brittle hacks? | `10.0 / 10` |
