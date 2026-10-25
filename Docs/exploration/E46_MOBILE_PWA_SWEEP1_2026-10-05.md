# E46 — Mobile / Responsive + PWA Audit (bounded sweep 1, 2026-10-05)

**Status:** Bounded sweep 1 complete (browser-based, Tier 4 on tested surfaces).
**Origin:** Launch-readiness council E5; registered as topic 46.
**Scope of this pass:** the traveler ask loop (the T1/T11b surface) at phone
viewport + PWA manifest presence. NOT a full app sweep — remaining surfaces
queued for sweep 2.

## Findings (evidence: live Playwright, 390×844, 2026-10-05)

1. **Traveler ask page (`/a/[token]`) renders cleanly at 390px** — single
   column, honest copy ("nothing here is mandatory"), textboxes + send button
   reachable, submission succeeds through the real UI at phone width
   (falsifier browser leg, see T11b pack §12). No horizontal overflow
   observed on the ask surface.
2. **PWA manifest exists and is served** — `frontend/public/manifest.json`
   ("Waypoint Companion", itinerary-access description) served at
   `/manifest.json` with `application/json` (200). `/manifest.webmanifest`
   404s (fine — JSON variant suffices).
3. **Manifest is NOT linked from the root layout** — no `<link rel="manifest">`
   in `frontend/src/app/layout.tsx`, so browsers never discover it; the PWA
   install path is dead code today. It appears intended for the traveler
   companion surface (`(traveler)/companion`), suggesting the link belongs on
   the traveler layout, not necessarily the root.
4. **Responsive evidence is otherwise unverified** — workbench, trips, and
   operator surfaces were not part of this bounded pass.

## Recommendation

Small additive task: link the manifest from the **traveler-facing layout**
(`(traveler)/layout.tsx` or the ask/companion pages) rather than the root, so
the companion PWA intent is discovered where it applies. Full sweep 2
(workbench + operator surfaces at phone width, touch targets, iOS safe areas)
remains queued.

## Falsifier

If linking the manifest from the traveler layout still yields no install
prompt in Chrome (Lighthouse PWA audit), the manifest content itself needs
review (icons, start_url scope) before any further PWA work.
