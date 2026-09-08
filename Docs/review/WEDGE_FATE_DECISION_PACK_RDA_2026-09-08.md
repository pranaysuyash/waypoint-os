# Wedge-Fate Decision Pack — Itinerary Checker (RDA EX-01 / D-01, 2026-09-08)

Decision owner: Pranay (product). This pack prepares the D-01 decision; it does **not** make it.

## The decision

Close `Docs/context/DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md` with exactly one of:

- **Option A — Keep as traveler surface** (status quo, minus deception). Checker remains public at `/itinerary-checker`, linked from pricing/marketing nav; agency-first strategy unchanged; Bucket-C items FT-G2/G3 (capability tokens, share page) become worthwhile; email capture can be rebuilt for real (FT-G1).
- **Option B — Invert the wedge: agency-branded checker.** Per `Docs/review/GTM_ANGLE_ASSESSMENT_2026-09-01.md:242-244` (recommended there): the checker becomes a white-label acquisition tool agencies give their own clients — same engine, tenancy per agency instead of one fixed `PUBLIC_CHECKER_AGENCY_ID`, report lands in the *branding* agency's workspace. Consumer wedge framing is retired.
- **Option C — Kill the consumer surface.** Unmount the router, archive the frontend route, redirect `/itinerary-checker` to the marketing site. Bucket-C consumer items become not-worth-doing; the engine (NB pipeline, live checks) stays for the agency product.

## Evidence on record (repo-internal)

- Wedge thesis falsified in practice: 822→1,098 funnel events, all synthetic; north-star `action_packet_shared` fired twice, both fixtures (`GTM_ANGLE_ASSESSMENT_2026-09-01.md:16-18`; verified again 2026-09-08 against `data/product_b_events/events_normalized.jsonl`).
- No distribution: not linked from the live homepage (deliberate, `Docs/FRONTEND_LANDING_REDESIGN_2026-06-28.md:22`); linked from `/pricing` and marketing nav only (corrected finding — the audit's `/n`-404 claim failed verification).
- Launch posture: public/paid launch NO-GO (`Docs/LAUNCH_STATUS.md:9`, 2026-09-04); launch readiness G21 "not-ready-to-decide" (`Docs/review/LAUNCH_READINESS_AUDIT_PER0100_2026-09-02.md:69`).
- Competitive context (as researched 2026-09-01): wedge thesis "contested, not open" — Spotinga, Fortrip and other itinerary checkers already exist (`GTM_ANGLE_ASSESSMENT_2026-09-01.md` §3.1).
- Registry status today: "code-backed surface [C]", never adjudicated (`Docs/CANONICAL_PRODUCT_OPPORTUNITY_AND_ROADMAP_REGISTRY_2026-08-04.md:118-121`).

## Research debt (blocks final ratification, not the decision itself)

**Live competitor refresh could not be run** — web search quota exhausted until 2026-10-06 17:07 IST (both search backends returned limit-exhausted on 2026-09-08). **Kept open as a tracked task for later (Pranay, 2026-09-09): Open Work Roadmap row B9**, which carries the retry queries and merge target. The Sept-1 assessment's competitor table is 7 days old and repo-internal; that is recent enough to decide direction, stale enough to re-verify before any public commitment. Retry queries when quota resets: "AI itinerary checker app", "travel plan risk checker tool", "Spotinga", "Fortrip", "trip stress test tool".

## Recommendation

**Option B (invert the wedge)**, with Option A as the acceptable holding pattern. Reasons: the engine and surface are built and tested (90 checker-stack tests green 2026-09-08); the consumer acquisition thesis has zero supporting evidence after ~5 months and one falsification review; the agency-first strategy (Ravi demo, commission/ops waves) is where real stakeholders are; inversion reuses the largest traveler surface for the audience that actually exists. Option C throws away a working, now-honest surface for negligible savings.

## What each option commits/unblocks

| | A: keep | B: invert | C: kill |
|---|---|---|---|
| FT-G2 capability tokens | yes | yes (per-tenant) | no |
| FT-G1 real email capture | yes | repurposed (agency leads) | no |
| Multi-tenant checker agencies | no | **new work: per-agency checker tenancy** | no |
| Kill switch (FT-05, shipped) | useful | useful | moot |
| Homepage relink decision | needed | needed (agency gallery instead) | not needed |

## Gate

Record the chosen option as an append on the decision memo (R-03) and in the canonical registry; then lift the corresponding Bucket-C gates in `Docs/review/FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_RDOC_AUDIT_2026-09-08.md`.
