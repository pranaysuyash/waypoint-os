# Frontend Landing Redesign 2026-06-28

## Decision

Promote the stronger warm editorial landing direction into the canonical homepage at `frontend/src/app/page.tsx` instead of leaving the better experience hidden behind `/v5`.

## Context

- The root homepage had a lot of product surface coverage, but it read like a dense dark SaaS page instead of a differentiated travel-operations front door.
- The repo already contained a more human, travel-specific direction in `frontend/src/components/marketing/landing-v5.tsx`, but it was isolated as an experiment.
- The requested outcome was to remove slop and redesign the landing page, not create another parallel marketing route.

## Chosen Path

1. Keep one canonical public homepage on `/`.
2. Reuse the warm editorial direction from `landing-v5` as the base.
3. Keep the homepage focused on the agency buyer:
   - messy inquiry to quote-ready brief,
   - faster intake,
   - fewer quote mistakes,
   - less owner time spent on repetitive clarification.
4. Remove the public checker distraction from the homepage so `/` does one job well.
5. Load the intended display/body fonts through `next/font` so the landing page uses real type choices rather than fallback system rendering.

## Files

- `frontend/src/app/page.tsx`
- `frontend/src/app/layout.tsx`
- `frontend/src/components/marketing/landing-v5.tsx`
- `frontend/src/components/marketing/landing-v5.module.css`
- `frontend/src/app/__tests__/public_marketing_pages.test.tsx`

## Verification Plan

- Run the public marketing page tests.
- Run frontend typecheck.
- Start backend and frontend dev servers per repo instructions.
- Verify the homepage in browser/computer tools on desktop and mobile-sized viewports.

## Addendum (2026-06-28)

- The hero motion was replaced with an SVG workflow ribbon rather than the earlier canvas sketch.
- The new animation shows the product translation story directly: incoming note, route to briefing, and the output brief.
- Reduced-motion users get the same composition without the looping motion.
