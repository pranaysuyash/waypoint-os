# Decision Memo: Itinerary Checker Wedge (2026-04-14 IST)

## Decision
Proceed with the itinerary-checker GTM wedge as a **focused acquisition + data layer** for the agency platform.

## Why This Is the Right Direction
- It reuses existing NB01-NB03 architecture (lower build risk).
- It captures high-intent users already holding an itinerary and budget.
- It creates compounding training data for templates, pricing memory, and supplier intelligence.
- It is a narrow entry point, not a distraction from the core agency OS.

## Risks and Countermeasures
- False positives reduce trust.
  - Start with conservative critical rules and confidence gating.
- Scope creep into full trip planner.
  - Keep v1 strictly as validator + recommendations.
- Weak paid conversion.
  - Add human-reviewed paid fix SLA and track conversion by rule/severity bucket.
- Compliance wording risk.
  - Use explicit guidance disclaimers and legal-safe language templates.

## v1 Scope Decision (Locked)
- Start with **10 checks** for precision-first launch:
  - Critical: `CONN_001`, `TRF_001`, `VISA_001`, `INS_001`, `CHK_001`
  - Warning: `HOT_002`, `PACE_001`, `MEAL_001`, `FEE_001`, `BUF_001`
- Keep remaining checks in v1.1 after precision baseline is validated.

## What We Were Missing (Now Included)
- Institutional-memory implications of checker data (template, supplier, pricing feedback loops).
- Operational runbook for post-analysis routing (fix request, quote request, confidence fallback).
- Clear go/no-go metrics and time-bounded decision gates.

## 30-Day Go/No-Go Gates
- Upload completion rate: `>= 20%`
- Valid extraction success: `>= 85%`
- Critical-rule precision (manual sample audit): `>= 80%`
- Email capture from result view: `>= 25%`
- Paid fix conversion (from captured leads): `>= 5%`

If 3 or more gates miss by >20%, pause expansion and fix parser/rules before scaling traffic.

## Operating Cadence
- Daily: ingestion failures, confidence outliers, false-positive reviews.
- Weekly: rule precision tuning, conversion funnel review, top issue buckets.
- Monthly: margin/quote insight extraction into pricing memory roadmap.

## Immediate Next Actions
- P0: lock API contracts and implement 10-rule evaluator.
- P0: add instrumentation for analysis funnel and per-rule outcomes.
- P1: introduce paid-fix handoff workflow with response SLA.
- P1: map checker outputs into template/pricing memory ingestion format.

## References
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md`

## Date Validation
- Environment date/time validated: `2026-04-14 18:09:44 IST +0530`.
