# EX-06 + EX-09 — Scoring Model Documentation, Calibration Plan & Live-Run Trace (2026-09-08)

Status: documented from code + one live probe. Closes two Unknowns from the audit's code-verification pass.

## The shipped scoring model (formalized)

The wedge doc's model (`clamp(10 − critical·2.0 − warning·1.0 − info·0.3, 0, 10)`) was never implemented. What ships (`spine_api/services/live_checker_service.py:8-13,106-156`, `src/public_checker/live_checks.py`):

1. **Base score resolution chain:** `validation.overall_score` → `validation.quality_score` → `packet.quality_score` → `packet.score` → decision-state baseline `{PROCEED_TRAVELER_SAFE: 82, PROCEED_INTERNAL_DRAFT: 74, ASK_FOLLOWUP: 64, STOP_NEEDS_REVIEW: 42}` → default 70.
2. **Subtractive live-check penalty (0–100 scale):** climate risk (precipitation/wind/heat) capped +30, current conditions capped +15, regional safety advisory +8, grand total capped +35. `adjusted = clamp(round(base − penalty), 0, 100)`.
3. **Rendering:** frontend "Itinerary Health Score" x/100 with its own clamp (`PageClient.tsx`, `Math.max(0, Math.min(100, …))`).

## Unknown resolved by live probe (EX-09, 2026-09-08 23:2x IST, dev server)

A real `POST /api/public-checker/run` (Tokyo April text itinerary, `stage: discovery`, no retention consent):

- `validation.overall_score` = **61** — **the producer exists**; the audit Unknown "overall_score is never populated upstream, public runs always use the baseline map" is **falsified**. Baseline map is a genuine fallback only.
- `decision_state = ASK_FOLLOWUP`, `soft_blockers = ["incomplete_intake"]`, `hard_blockers = []`, `packet.score = 61`, live checks present in `validation.public_checker_live_checks`.
- Second Unknown also resolved: consented-artifact persistence happens via `PublicCheckerArtifactStore` save inside `save_processed_trip` (`persistence.py:2548+`); run was consent-free so no artifact was written (correct negative).

## Calibration plan (the doc's promise, made actionable)

The doc promised calibration "after first 100-300 analyzed itineraries" — impossible to date (all 1,098 funnel events are synthetic). Calibration is gated on real traffic, which is gated on D-01. When real traffic exists:

1. Log `base`, `penalty_breakdown`, `final` per run (fields already separable server-side).
2. After N≥100 runs with advisor-review outcomes, fit penalty weights against human severity ratings (the per-rule precision audit the decision memo wanted, but on the *shipped* taxonomy).
3. Until then: no calibration changes — the caps (30/15/35) are arbitrary but documented, which beats silent drift.

## Residual notes

- `visa_not_applied` (critical) remains unreachable from the public checker while it pins `stage: 'discovery'` (`decision.py:1283-1298` + `PageClient.tsx:2871`); only `visa_timeline_risk` (high) can fire. Stage-awareness is EX-07/D-04 material.
- Score is presentation-only: it gates nothing downstream (decision gates use blockers/state, not the number) — recalibrating is therefore user-trust work, not correctness work.
