# SEO + Next.js GTM Playbook Synthesis (2026-04-14 IST)

## Source Ingested
- `/Users/pranay/Downloads/Thinking-about-agentic-flow (8).html`
- Archived copy:
  - `Archive/context_ingest/meta_design_refs_2026-04-14_1816/Thinking-about-agentic-flow (8).html`

## Executive Read
Direction is strong, but the provided plan is **too broad for first launch**. The right move is:
- ship a focused SEO + upload flow quickly,
- keep rule precision high,
- avoid programmatic page sprawl before conversion signal exists.

## What To Keep (P0)
- Tier-1 intent keywords around itinerary validation.
- Core pages:
  - `/` (homepage + upload)
  - `/review`
  - `/check/[slug]` (destination pages, but only a small starter set)
- Clear CTA funnel:
  - upload -> score/issues -> email capture -> paid fix / quote request.
- Component architecture from the draft (dropzone, processing, scorecard, issues list, capture).

## What To Change Before Building
- Do **not** launch 50 destination pages in month 1.
  - Start with 8 to 12 pages max (highest demand destinations).
- Do **not** keep contradictory thresholds without data.
  - Ensure `CONN_001` threshold is policy-consistent with core NB rules.
- Replace vanity counters unless backed by real telemetry.
- Keep severity language cautious to limit false-confidence and legal risk.

## Recommended 30-Day Execution (Revised)
### Week 1
- Implement Next.js upload + results pipeline to existing backend.
- Publish homepage + 3 destination pages.
- Add schema metadata + basic OG tags + sitemap + robots.

### Week 2
- Expand to 8 to 12 destination pages.
- Publish 3 to 5 problem-intent articles linked to upload CTA.
- Add analytics events for each funnel stage.

### Week 3
- Tune copy/rules from false-positive reviews.
- Add paid-fix handoff workflow and SLA messaging.

### Week 4
- Run small paid test only after organic funnel instrumentation is stable.
- Decide scale-up only if conversion and precision gates are met.

## Next.js Implementation Notes
The component structure is valid for MVP, with these adjustments:
- Keep UI copy deterministic and severity-aware.
- Add upload failure + uncertainty states.
- Add confidence rendering per issue where available.
- Centralize API types so frontend and backend contracts do not drift.

## SEO Scope Decision
### Initial keyword cluster (launch)
- `itinerary checker`
- `check my travel itinerary`
- `itinerary review`
- `is my itinerary good`
- `travel plan validator`

### Expansion criteria
Only expand to larger programmatic set if all are true:
- upload completion >= 20%
- extraction success >= 85%
- critical precision >= 80%
- email capture >= 25%

## Risks
- Over-scaling pages before product-market proof.
- False positives creating trust debt.
- Compliance risk from definitive travel/legal wording.
- Engineering drift between GTM frontend and core NB policy contracts.

## Integration With Existing Docs
- GTM wedge baseline:
  - `Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md`
- Decision guardrails:
  - `Docs/context/DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md`
- Institutional memory linkage:
  - `Docs/context/INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md`

## Date Validation
- Environment date/time validated: `2026-04-14 18:15:54 IST +0530`.
