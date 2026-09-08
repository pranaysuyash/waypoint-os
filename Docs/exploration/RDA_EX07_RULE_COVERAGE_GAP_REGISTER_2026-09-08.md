# EX-07 — Rule-Coverage Semantic Gap Register: Wedge Doc vs Shipped Checker (2026-09-08)

Status: research register. Feeds D-04 (which gaps matter for a precision-first public checker). The 2026-04-14 doc named 15 rules; none exist under those IDs. This maps each to shipped equivalents, internal-only equivalents, or true gaps.

## Mapping

| Doc rule | Sev | Shipped equivalent (public path) | Internal equivalent (not wired to checker) | Verdict |
|---|---|---|---|---|
| CONN_001/002 tight connections | Critical | — | `POST /api/v1/logistics/connection-risk` (MCT/transfer risk, `spine_api/routers/logistics.py:226-227`) | Gap (internal exists) |
| TRF_001 missing transfer | Critical | — (packet facts may mention transfers; no check) | — | Gap |
| TRF_002 prolonged transfer | Warning | — | — | Gap |
| VISA_001 visa required/unclear | Critical | `visa_timeline_risk` (high) always; `visa_not_applied` (critical) only at `stage: booking` — unreachable, checker pins `discovery` (`decision.py:1283-1298`) | document_risk (critical, `decision.py:1287-1291`) | Partial |
| INS_001 insurance missing | Critical | — (insurance only as budget bucket, `decision.py:206`) | — | Gap |
| CHK_001 check-in/out buffer | Critical | — | `POST /api/v1/logistics/timed-entry-audit` (`logistics.py:197-198`) | Gap (internal exists) |
| HOT_001 hotel location risk | Warning | — | — | Gap |
| HOT_002 excessive hotel changes | Warning | `coordination_risk` (medium) partially (`decision.py:1338-1342`) | — | Partial |
| PACE_001 over-packed cadence | Warning | `toddler_pacing_risk`, `elderly_mobility_risk` (composition-conditioned, `decision.py:1262-1276`) | suitability pacing dimensions | Partial (not cadence-based) |
| MEAL_001 meal coverage ambiguity | Warning | — | — | Gap |
| FEE_001 hidden fees | Warning | — | margin_risk (internal margin logic, `decision.py:1316-1321`) | Gap |
| BUF_001 event/cruise buffer | Warning | — | `timed-entry-audit` (see CHK_001) | Gap (internal exists) |
| WEATHER_001 season/weather mismatch | Warning | **Shipped**: climate/current-conditions/safety live checks (`src/public_checker/live_checks.py:38-514`) with structured severities | — | Done |
| Info: route optimization | Info | — | — | Not built (was "paid emphasis") |
| Info: hotel optimization | Info | — | — | Not built |
| Info: cost optimization | Info | — | — | Not built |

Plus shipped checks with no doc counterpart: `traveler_safe_leakage_risk`, `unacknowledged_critical_assumption`, `margin_risk`, validation codes (`MVB_MISSING`, `LOW_CONFIDENCE_FACT`, `HIGH_AMBIGUITY`).

## Reading

The shipped checker is strongest exactly where it takes *structured, verifiable* input (weather/safety from live data; composition risks from declared traveler profile) and weakest where the doc's rules needed *parsed itinerary structure* (times, connections, hotels, meals) — the same extraction depth the intake pipeline doesn't produce for freeform text. Wiring the internal logistics endpoints to the public checker would silently widen the false-positive surface the wedge doc itself warned about ("conservative critical rules first"), because connection/hotel checks need reliable structured facts the public path rarely has.

## Recommendation for D-04

1. Accept the gap register as the honest scope statement of the public checker ("text + profile + live-data checks"), not a deficient version of the doc's 15.
2. Wire `timed-entry-audit`/`connection-risk` into the public path only after capability-gated structured input exists (upload of a real itinerary file with parseable legs), and gate them as `advisory_*` initially.
3. Fix the one cheap asymmetry now (D-04 fast path): stage-awareness — let users declare "already booked" so `visa_not_applied` can fire for the users who most need it.
4. Retire the doc's rule taxonomy as a tracking unit; track by this register instead.
