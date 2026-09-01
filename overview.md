# Waypoint living journey landing prototype

## What was done

Built a complete landing prototype at `frontend/design-lab/v9-living-journey/` that treats the customer journey as one spatial narrative rather than four disconnected stages.

The hero contains a real interactive 2D journey map for a representative Kerala trip. It renders and switches between intake, decisions, disagreements, and updates. The same model drives map nodes, route progress, event markers, captions, stage status, and replay.

## Key decisions

- Chose a restrained editorial-cartography direction: dark operational surfaces, Newsreader display type, IBM Plex Sans/Mono UI type, teal route accent, and state-specific blue/teal/coral/amber markers.
- Used one Canvas 2D renderer rather than WebGL or an external map SDK. The map is the landing's explanatory product demo, not an unrelated visual effect.
- Made motion state-driven, explicitly pausable, visibility-gated, and disabled under `prefers-reduced-motion`.
- Kept stage tabs as the canonical keyboard-accessible control; canvas marker clicks are an additional pointer affordance.
- Kept content grounded in the existing Waypoint design-lab/product vocabulary: Kerala, Mumbai, Kumarakom, Marari, missing details, call notes, budget tension, and quote-ready briefs.

## Verification

- `v9-living-journey/verify.mjs`: **25 passed, 0 failed**.
- Browser smoke passed for desktop, mobile, stage changes, pause/replay, reduced motion, responsive canvas sizing, and page errors.
- Added `RATIONALE.md` with architecture, motion, interaction, and production-boundary notes.

## Follow-up

This is a landing prototype, not a production endpoint integration. The next production step is to feed the same `nodes` / `events` / `stageData` rendering contract from a public-safe journey summary endpoint without changing the interaction model.
