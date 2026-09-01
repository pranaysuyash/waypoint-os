# FieldCanvas interactivity — measured, and why Waypoint shouldn't copy its engine

**Date:** 2026-08-31
**Method:** runtime instrumentation (`requestAnimationFrame`, `addEventListener`,
`IntersectionObserver`, `canvas.getContext` patched *before* page scripts ran), then
rAF throughput sampled while idle / scrolling / hovering. The headline metric is
**rAF calls/sec while IDLE** — a permanent loop means the page is animating even when
nobody touches it.

---

## First, a critical naming collision

There are **two unrelated products called "FieldCanvas"**:

| | Local repo `/Users/pranay/Projects/fieldcanvas` | Public `fieldcanvas.app` |
|---|---|---|
| Product | 3D "semantic spatial canvas" — *paint space, pull structure* | Django **campaign field-ops**: turf, walklists, voter notes |
| Landing | `index.html` (291 KB) on Vite dev `:5183` | Django `public-landing` (`/accounts/login/`) |
| Animation | ~125 rAF/sec loop, 9 canvases, pointer-driven | tiny 300×150 "live turf map" canvas, 60–120 rAF/sec |
| Honors `prefers-reduced-motion` | **yes** | **NO** |

So "the FieldCanvas landing page" is ambiguous. The one you almost certainly mean
(the 3D spatial-canvas toy) is the **local repo**; the public URL is a *different*
product. Any "copy it" decision has to pick which one — and the right model to borrow
from is the local repo's *discipline*, not the live site's engine.

---

## The three-way measurement

| Metric | **3D FieldCanvas** (`:5183`, local repo) | **Live `fieldcanvas.app`** (Django) | **Waypoint landing** (`:3001`, captured earlier this session*) |
|---|---:|---:|---:|
| DOM nodes | 1,144 | 43 | 232 |
| Page height | 15,381 px (17.1 screens) | 1,066 px (1.2 screens) | 3,844 px |
| Transfer | 912 KB | 15 KB | 119 KB |
| `<canvas>` elements | 9 (all `2d`) | 1 (`2d` 300×150) | 0 |
| WebGL contexts (on load) | 0 | 0 | 0 |
| @keyframes blocks | 3 | 0 | 7 |
| Infinite CSS rules | 1 (`sc-shine`) | 0 | 6 |
| Elements animating (computed) | 2 | 0 | 9 |
| Buttons / links / inputs | 57 / 49 / 6 | 0 / 3 / 0 | — / — / — |
| Event listeners | 155 | 2 | 278 |
| **rAF/sec IDLE** | **125.0** | **85.0** | **0.0** |
| **rAF/sec SCROLL** | **683.8** | **366.9** | **0.0** |
| **rAF/sec HOVER** | **1631.0** | **627.9** | **0.0** |
| Honors `prefers-reduced-motion` | **yes** | **NO** | **yes** |

\*Waypoint `:3001` went down before re-probe; figures are from the earlier captured run
this session (DOM 232, 7 keyframes, 6 infinite CSS, animation names `ribbon-dash` /
`ribbon-breathe` / `rise`, 17 gradient elements, 11 glow shadows, rAF idle/scroll/hover
all 0.0).

### What the numbers say
- **Both FieldCanvas surfaces run a permanent animation loop** (idle ≥ 85 rAF/sec). That
  is the "it feels alive" effect. On the 3D repo it's a 17-screen product-demo page
  (you literally play with the canvas). On the live site it's a 300×150 map gimmick.
- **Waypoint's landing runs ZERO rAF** — its motion is pure CSS/SMIL decoration
  (6 infinite CSS animations + 2 SMIL). It reads as "static until you touch it" to a
  frame sampler, even though it visibly shimmers. That shimmer is the "early-2020s"
  feel — not a lack of animation, but the *wrong kind*.
- **The 3D repo honors reduced-motion; the live site does not.** If you ever unify the
  two, that's a regression to fix, not a feature to copy.

---

## Why Waypoint shouldn't copy FieldCanvas's *engine*

1. **Wrong medium for the product.** Waypoint's value is server-side intelligence —
   turning messy trip notes into quote-ready briefs. A 125 rAF/sec always-on loop, 9
   canvases, and 912 KB of transfer would be decoration that says nothing about the
   product and would hurt load speed, accessibility, and the "serious B2B tool"
   perception Waypoint needs.

2. **Waypoint's dated feel was CSS excess, not animation poverty.** The landing had 17
   gradients, 11 glow shadows, 6 infinite CSS animations, 2 SMIL. The fix is
   *restraint* — which `v8-disciplined-dark` already does by deleting that noise — not
   *adding* a render scene. Bolting a permanent rAF loop onto it would just swap one
   gimmick for another.

3. **FieldCanvas escapes the criticism because its animation IS the product demo.**
   You can't "try" Waypoint's intelligence from a hero canvas; its interactivity lives
   in the intake form and the brief generator. Copying the *engine* would celebrate a
   feature Waypoint doesn't have.

---

## What Waypoint SHOULD do — the right kind of "alive"

- **Functional interactivity first.** The intake flow, live brief preview, and step
  transitions are the interactions that matter for a travel-ops product. Make those
  feel instant and responsive; that's the real "interactive."
- **Tasteful, reduced-motion-gated motion.** Scroll-reveal on value props, micro-
  interactions on form fields, a calm (not shimmering) hero — all wrapped in
  `@media (prefers-reduced-motion: reduce)` so they vanish for opted-out users.
  Model this on the 3D FieldCanvas repo's discipline, *not* the live site.
- **Performance budget.** Keep transfer near or below the current 119 KB. Run rAF only
  during active interaction (a 60fps transition), never a permanent idle loop. Target
  rAF idle = ~0, exactly like the current Waypoint landing already is.

---

## Bottom line

You *can* make Waypoint feel more alive — but by adding **functional,
reduced-motion-gated micro-interactions**, not a FieldCanvas-style always-on render
scene. The "dated" problem was decorative CSS excess, already solved by restraint in
`v8-disciplined-dark`. **Borrow FieldCanvas's discipline (reduced-motion, purposeful
motion), not its engine (permanent rAF loop on a playable demo).**

### Open items
- Resolve the two-product naming before any "copy FieldCanvas" work — confirm which
  one is the reference.
- `:3001` (Waypoint landing) died during this session; re-run `inspect-interactivity.py`
  against the live Next.js app (`:3000`) to refresh the Waypoint column.
