# Landing Page Experiments - 2026-05-09

## Prompt

Explore whether the current public landing page is the strongest possible version, research modern browser and image-generation options, then create experimental landing-page directions without disrupting the current homepage.

## Research Topics

1. Generated raster hero assets for stronger first-viewport brand memory.
2. Canvas overlays for product-relevant motion, such as routes, risk signals, and transformation from messy intake to governed workflow.
3. CSS scroll-driven animations using `animation-timeline: view()` as progressive enhancement.
4. Same-page component transitions and micro-interactions for tabs, product signal cards, and CTA hover states.
5. Accessibility controls for motion, especially `prefers-reduced-motion`.

## Sources Checked

- MDN CSS scroll-driven animation timelines.
- MDN View Transition API.
- MDN OffscreenCanvas.
- Chrome scroll-driven animations guide.

## Implementation

- Added `/v3` as a component experiment lab with three selectable directions:
  - Cinematic Ops
  - Live Console
  - Traveler Bridge
- Added `/v4` as the synthesized candidate direction:
  - full-bleed generated hero image
  - animated canvas route overlay
  - live trip intelligence panel
  - operational proof cards
  - progressive scroll reveal
- Generated and copied the hero asset into:
  - `frontend/public/landing/experiments/waypoint-ops-hero-v3.png`
- Allowed `/v3` and `/v4` through the frontend proxy public route allowlist.

## Decision

The current homepage is competent but visually conservative. The `/v4` direction is stronger because it sells Waypoint's operating judgment in the first viewport: a real agency environment, live risk signals, and visible transformation from messy request to safer trip decision. `/v3` should remain as a lab for comparing component ideas before merging a final direction into `/`.

## Verification

- `curl -L http://localhost:3000/v3` returned `200`.
- `curl -L http://localhost:3000/v4` returned `200`.
- `curl http://localhost:3000/landing/experiments/waypoint-ops-hero-v3.png` returned `200`.
- Browser manually opened `/v3` and `/v4`.
- `npm test -- --run src/lib/__tests__/route-map.test.ts src/__tests__/proxy.test.ts` passed: 27 tests.

## Known Blocker

`npm run build` is currently blocked by parse errors in unrelated modified files:

- `frontend/src/app/v2/page.tsx`
- `frontend/src/app/(agency)/workbench/PacketTab.tsx`

Those files were already modified outside this experiment, so this work did not repair them.
