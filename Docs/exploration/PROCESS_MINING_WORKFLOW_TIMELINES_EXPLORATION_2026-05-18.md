# Process Mining on Workflow Timelines — Exploration

**Date**: 2026-05-18
**Status**: Exploration draft. Not implemented.
**Parent index**: [../EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)
**Sibling**: [KDD parent §4.4](KDD_KNOWLEDGE_DISCOVERY_EXPLORATION_2026-05-18.md)
**Related**: Priority Scoring (#20), Real-World Validation (#7), Evaluation Framework (#6)

---

## 1. What Process Mining Is (Briefly)

Process mining (van der Aalst, ~2011 onward) treats event logs as the ground truth of how work actually flows, not how someone *thinks* it flows. Three families:

| Family | Question | Output |
|---|---|---|
| Discovery | "What does the process actually look like?" | A process model (Petri net, BPMN, DFG) inferred from event logs |
| Conformance | "Where does reality diverge from the intended process?" | Deviation map + frequencies |
| Enhancement | "Where are the bottlenecks, rework loops, dead ends?" | Annotated model with timing, frequency, cost |

For a travel-agency workflow, all three are useful — but enhancement (bottlenecks/loops/dead ends) delivers the most operational value first.

## 2. Why This Fits Waypoint OS

Every trip already emits a timeline of events: created → intake → validated/gated → drafted → sent → revised → booked → ... The trip timeline IS the event log. No new instrumentation needed.

Compare to KDD override mining (needs labeled corrections) or suitability mining (needs outcomes with sample size): process mining works the **moment trips exist**, including at very low N per agency. Single-trip process traces are still informative because the question is structural, not statistical.

## 3. Concrete Questions Process Mining Answers Here

1. **Where do trips actually slow down?** Time-between-stage distributions per agency. "Median time from `proposal_sent` → `proposal_responded` is 4.2 days, p95 is 17 days."
2. **What's the dominant happy path vs the long tail?** Most trips follow path A; 15% loop back from `proposal_sent` to `draft_revised`; 3% go through a 9-stage rework cycle.
3. **Where do gates actually fire?** Frequency map of escalations by stage of origin.
4. **Are there silent dead ends?** Trips that enter a stage and never leave for N days. These are operationally invisible without mining.
5. **How does workflow shape differ across agencies?** Same product, different actual processes — surface the variance.
6. **What does an agency-level workflow KPI look like?** Cycle time, throughput, rework rate. Real ops metrics, not vanity ones.

## 4. The N Question (Why This Is Cheaper Than the Other Mining Topics)

| Mining type | Min useful N | Why |
|---|---|---|
| Override mining | ~3 per cluster | Pattern-based, single cluster informative |
| Suitability mining | ~20 trips, ~5 per pattern | Lift requires both numerator and denominator |
| Process mining | ~10 trips total | Structural questions answerable with handful of traces |
| Anomaly detection | ~100s of trips | Distribution needed to define "anomalous" |

Process mining hits useful output earliest. This makes it the most viable mining topic for pre-launch or early-customer state.

## 5. Tooling Decision

Three honest options:

**Option A — Roll our own with pandas/networkx**
- Pros: zero new dependency weight; full control; deterministic.
- Cons: reinvents the wheel for DFG discovery, performance binning, etc.

**Option B — pm4py (de facto Python process mining library)**
- Pros: covers discovery, conformance, enhancement; visualization included; well-tested on event logs.
- Cons: heavier dependency; visualization stack pulls graphviz; learning curve.

**Option C — DuckDB + SQL window functions**
- Pros: extremely fast on event tables; SQL is debuggable; no new Python deps if DuckDB already present.
- Cons: only covers timing/frequency analysis cleanly; discovery (process model inference) is awkward in SQL.

**Recommendation**: **C for v0** (timing, frequency, bottleneck surfacing — covers §3 questions 1, 3, 4, 6). Promote to **B** only if §3 questions 2, 5 (model inference, cross-agency variance) become real consumers. Don't take the pm4py dependency cost speculatively.

## 6. v0 Scope (If Pursued)

A minimal v0 answers questions 1, 3, 4, 6 from §3:

1. Materialize a `trip_events` view from existing event sources.
2. Compute per-stage timing (median, p95) per agency, rolling window.
3. Compute per-stage gate-firing rate per agency.
4. Detect "stuck" trips (in a stage > Nx the agency's p95 for that stage).
5. Surface results in a single read-only ops view + alert on stuck trips.

That's it. Model inference (BPMN/Petri net) is v0.5, gated on whether ops actually look at the v0 surface.

## 7. What This Does NOT Help With

- **The unified-state perf issue** — different problem class (frontend/backend latency, not workflow latency). Don't conflate.
- **Why** trips fail — process mining tells you *where*; KDD override mining and gate analysis tell you *why*. Pair them.
- **Predicting** trip success — different problem (supervised learning, possibly time-series). Defer to suitability mining or its successor.
- **Tiny agencies** — useful, but the "stuck trip" thresholds need calibration windows. Use sensible defaults; tune as data accumulates.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Mining surfaces uncomfortable truths about specific operators | This is feature, not bug, but the UI must avoid name-and-shame framing. Aggregate before individual. |
| Events are missing or out of order in the log | Conformance check the log itself first; surface log-quality issues before workflow conclusions. |
| Definition of "stage" drifts as the product evolves | Version the stage taxonomy; process mining queries reference a specific version. |
| Stuck-trip alerts become noise | Per-agency thresholds, not global; respect operator dismissals; track precision over time. |
| Becomes a vanity dashboard | Same kill criterion as KDD: if no operator action follows from the surface after 4 weeks, scrap. |

## 9. Relationship to Existing Systems

- **Priority Scoring (#20)**: Process mining surfaces *systemic* delays; priority scoring surfaces *per-trip* urgency. Complementary; the mining output could become a priority signal ("trip is in a typically-stuck stage").
- **Evaluation Framework (#6)**: Process mining outputs (cycle time, rework rate) are first-class evaluation metrics.
- **KDD override mining**: Process mining identifies *where* humans intervened most; override mining identifies *why*. Stage-of-override is the natural join.
- **Real-World Validation (#7)**: Process mining is the most defensible way to validate that real workflows match the documented scenarios.

## 10. Decision Recommendation

**Ship this in parallel with KDD v0**, not after. Reasoning:
- Lowest N requirement of any mining topic.
- Reuses zero KDD infrastructure (different algorithm class, different output shape).
- Smallest blast radius — pure read + one new view.
- Immediate operational value even before any AI improvement loop matures.
- Tests the "do operators consume mined surfaces" hypothesis cheaply, informing whether KDD v0 will land.

Estimated effort: 1-2 days for v0 (timing/bottleneck/stuck-trip surface). Defer model inference unless v0 is consumed.

## 11. Kill Criteria

If after 4 weeks of operation, no operator references the surface, no stuck-trip alert leads to action, and no agency-level KPI is cited in any decision, scrap. Same standard as KDD v0.

## 12. Open Questions

1. Is there a canonical `trip_events` table or are events scattered across tables (audit, status_history, ...)? Materialize accordingly.
2. What is the "stage" taxonomy of record, and is it versioned?
3. Who is the consumer surface for v0 — same digest as KDD, separate ops dashboard, or both?
4. Cross-agency aggregation: per-agency only in v0, cross-agency benchmark deferred?
5. How does this interact with the existing ops panel work?

---

*Exploration document. Decisions are recommendations until reviewed.*
