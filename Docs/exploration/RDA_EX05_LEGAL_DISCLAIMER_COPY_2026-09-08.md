# EX-05 — Legal Disclaimer Copy Requirements (2026-09-08)

Status: research + draft copy. The 2026-04-14 wedge doc promised "explicit disclaimer ('guidance, not legal travel guarantee'), policy-reviewed copy" (`Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md:177-178`). Verified 2026-09-08: **no disclaimer exists anywhere** on the checker surface (`rg disclaimer|guidance|guarantee|legal` over `PageClient.tsx`, `page.tsx`, `live_checks.py` → only advisory hint strings and marketing copy).

## What the surface says today that raises exposure

- Findings render as imperative advisories: hard/soft blockers derived from `decision.py` risk flags (visa, documents, safety) — traveler could read them as authoritative entry/eligibility claims.
- Live weather/safety signals from Open-Meteo (`src/public_checker/live_checks.py`) — data with freshness and accuracy limits.
- The checker explicitly reaches non-authoritative buckets by design: live-check findings demoted to `advisory_*` unless authority-gated (`spine_api/services/live_checker_service.py:16-73`) — the disclaimer should say what "advisory" means.

## Draft copy (requires owner sign-off before shipping — this is the "policy-reviewed" step the doc itself required)

**Placement 1 — result view, above findings:**

> This report is automated guidance based on the text you provided and public data sources. It is not legal, immigration, safety, or booking advice, and it cannot guarantee entry requirements, schedules, or prices. Always verify visas, health rules, and timings with official sources and your travel advisor before you pay or travel.

**Placement 2 — upload view, footer:**

> Free automated check. Guidance only — not a substitute for professional travel, visa, or legal advice.

**Placement 3 — export header (same text as Placement 1).**

Requirements for the real copy owner:
1. No warranty language ("accurate", "reliable", "guaranteed").
2. Name the failure modes honestly: OCR/extraction errors, stale external data, incomplete input.
3. Jurisdiction-neutral phrasing; no consumer-rights waivers (that's a legal-drafting question, flagged for review, not decided here).
4. Match the D2 free-engine persona rules (`Docs/ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md`) so the disclaimer doesn't contradict the product's own honesty badges.

## Test plan when implemented

- Result view renders disclaimer text (extend `honesty-sweep.test.tsx` with an assertion that the disclaimer string is present — inverse of the removal assertions).
- Export payload includes the disclaimer line.
- Live-check advisory cards render the "advisory, not verified" qualifier.
