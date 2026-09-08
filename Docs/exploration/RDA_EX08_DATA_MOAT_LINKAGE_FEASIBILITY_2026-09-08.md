# EX-08 — Data-Moat Linkage Feasibility: Checker → Memory/Template/Pricing (2026-09-08)

Status: research. The 2026-04-14 wedge thesis claimed checker traffic would compound into "Template Genome discovery, Pricing Memory baselines, playbook priorities, destination demand signals" (doc :190-196; decision memo P1 "map checker outputs into template/pricing memory ingestion format"). Verified 2026-09-08: **no such ingestion exists** — zero mentions of "lead"/"template"/"pricing memory" in `spine_api/services/public_checker_service.py` or `spine_api/routers/public_checker.py`, and the institutional-memory layer it targeted is itself write-only (PA-18: memory writes but forgetting/reads never execute in any loop).

## Feasibility assessment

**Technically feasible, currently worthless.** The checker already produces structured, typed outputs (`packet` facts, validation, decision state, live-check risks — all schema'd in `spine_api/contract.py`), so a destination-demand extractor over checker runs is a small batch job, not new instrumentation. But three facts make it premature:

1. **No data.** All 1,098 funnel events are synthetic; even trip rows are probe/dev artifacts. Any "moat" built today learns from noise.
2. **No consumer.** PA-18 (PER-0700): the memory store is write-only — nothing reads it back into decisions. Ingesting checker signals into a store no loop reads creates a second write-only silo.
3. **No consent coverage for secondary use.** The consent toggle covers product-improvement storage, not competitive/pricing mining; secondary use needs its own consent line (ties to EX-02).

## Trigger conditions (when this becomes worth building)

- D-01 resolves to Option A/B (surface survives with real traffic), AND
- PA-18 memory-loop resolution gives memory a reader, AND
- EX-02 retention policy defines how long checker-derived aggregates may persist.

Then the build is: destination/season/risk aggregation view over checker trips (SQL read-model, additive), feeding destination-demand signals only — pricing-memory baselines stay out of scope until consented structured quotes exist (they never did; the doc's "extracted competitor pricing points" depended on the never-built quote flow).

## Verdict

Park as EXPLORE with explicit triggers. Record in the decision-memo closure (R-03) that the "data moat" leg of the wedge thesis never activated — no ingestion, no reader, no data.
