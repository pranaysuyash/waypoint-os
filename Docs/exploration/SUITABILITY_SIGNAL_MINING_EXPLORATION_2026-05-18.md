# Suitability Signal Mining — Exploration

**Date**: 2026-05-18
**Status**: Exploration draft. Not implemented. Tied directly to a launch blocker.
**Parent index**: [../EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)
**Sibling**: [KDD parent §4.3](KDD_KNOWLEDGE_DISCOVERY_EXPLORATION_2026-05-18.md)
**Related**: AGENTS.md "AI override controls" launch blocker; Timeline schema fix worklog (2026-04-23); Priority Scoring #20

---

## 1. Why This Is Different From the Other Mining Topics

KDD v0 mines **failure** (overrides). This mines **success** (booked trips that stuck). Same pipeline architecture, opposite signal direction. The two complement each other:

```diagram
╭────────────────────╮     ╭──────────────────────╮     ╭────────────────────╮
│ Override mining    │     │ Suitability mining   │     │ Together           │
│ "where AI is       │  +  │ "what combinations   │  =  │ a closed feedback  │
│  systematically    │     │  consistently        │     │ loop on the AI's   │
│  wrong"            │     │  succeed"            │     │ decision surface   │
╰────────────────────╯     ╰──────────────────────╯     ╰────────────────────╯
```

The suitability renderer is currently blocked because suitability *signals* don't exist as a curated dataset. The two ways to produce them are: (a) have a human curate them, (b) have an LLM invent them, (c) mine them from history. Only (c) is grounded, agency-specific, and improves with N.

## 2. The Launch-Blocker Tie-In

AGENTS.md repeatedly cites a real production case (Timeline schema fix, 2026-04-23) where the feature was code-ready but not feature-ready because "suitability signals" + "override controls" were missing. Override controls is being addressed by KDD v0. Suitability signals is this doc. Together they remove the launch blocker.

## 3. What a Suitability Signal Actually Is

A statement of the form:

> "For agency A, trips with attributes (X = value, Y in range, Z = category) book successfully N times out of M attempts (confidence C, sample size M)."

Examples (illustrative, not real data):
- "Multi-gen family + Greek island cruise in shoulder season → 12/14 booked, no churn-back."
- "Solo traveler + remote Patagonia trek in winter → 1/9 booked." (suitability **counter-signal**)
- "Honeymoon + Bali villa in August → 28/30 booked, average margin within agency norm."

A signal is **never** a recommendation; it is an **observation with sample size**. The renderer's job is to surface signals; the operator's job is to act on them.

## 4. KDD Framing

| Step | Activity |
|---|---|
| Selection | All trips that reached `booked` and remained booked (no churn-back / no late escalation) within window. Exclude very recent trips where outcome is still unknown. |
| Preprocessing | Normalize destinations to a canonical taxonomy; bucket dates into seasons; canonicalize traveler shape (solo, couple, family-with-young-kids, multi-gen, group); bucket budget into agency-relative bands. |
| Transformation | Build a feature vector per trip. Reuse extracted intake slots where possible — don't add new extraction. |
| Mining | Frequent-pattern mining (FP-Growth or Apriori) over feature combinations → outcome. Filter by support threshold *and* sample size floor. |
| Interpretation | Each surviving pattern is a candidate suitability signal, ranked by lift = P(success | combination) / P(success). |

## 5. Algorithm Choice

- **Default**: FP-Growth on discrete features. Well understood, fast, deterministic, interpretable. mlxtend has a clean implementation; sklearn does not.
- **Counter-signals**: Run the same algorithm against the *unsuccessful* trip set; surface high-lift counter-patterns as warnings.
- **Why not embeddings + clustering**: Embeddings hide *which* features explain the success. Operators need legible signals, not opaque clusters.

## 6. Critical Honesty: The N Problem (Worse Than KDD Override Mining)

Override mining works at N=3 because a cluster of three identical overrides is already informative. Suitability mining does **not** work at N=3, because you need both the numerator (successes) and denominator (attempts) per combination, and lift becomes meaningless with tiny denominators.

Concrete minimum: do not surface a signal unless:
- combination support ≥ 5 trips in the window, **and**
- combination has at least 3 successful outcomes, **and**
- agency has at least 20 booked trips in the window total.

Below these thresholds, surface "insufficient data" honestly. Do not invent signals.

## 7. Ranked Applications

1. **Direct feed to suitability renderer** (highest, ties to launch blocker).
2. **Counter-signals as escalation hints**: when intake matches a known high-failure pattern, surface a warning at intake time, not at gate-failure time.
3. **Agency benchmarking** (later): "your booking rate on X combinations is N% vs sibling agencies' Y%." Requires cross-agency permission and is downstream.
4. **Template seeding**: high-lift patterns become draft itinerary templates. Crosses into recommendation territory; defer.
5. **Operator coaching**: junior agents see what their peers' successful combinations look like. Defer until UI for #1 is real.

## 8. What This Does NOT Help With

- Cold-start agencies (first 6 months) — too little data. Use curated defaults; switch to mined signals when thresholds hit.
- Trips with truly novel combinations — by definition no historical signal exists. Operator judgment + override mining covers this gap.
- Pricing or margin decisions — different mining problem (regression, not frequent-pattern). Keep scope tight.
- Real-time scoring at intake — v0 is batch only; real-time comes later if and only if the batch loop proves consumed.

## 9. Privacy and Cross-Agency Guardrails

- All mining is **per-agency by default**. No cross-agency mixing in v0.
- Representative samples surfaced to the UI are aggregated, not single-trip, to prevent inferring specific customer identities.
- Cross-agency benchmarking (§7.3) requires explicit opt-in and only aggregate statistics cross the boundary, never raw trips.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Spurious patterns at low support | Hard thresholds in §6; honest "insufficient data" surface. |
| Outdated patterns (e.g., destination became unsafe) | Rolling window (default 12 months); concept-drift hook into the eval framework. |
| Operators treat signals as recommendations | UI must show sample size and confidence prominently; never a single "recommended" label. |
| Suitability mining races the renderer team | Ship the data layer first; render against a stable contract; do not couple schedules. |
| Combinatorial explosion in feature space | Cap feature cardinality (e.g., top-N destinations, fixed season bucket, capped budget bands); document the cap. |

## 11. Pipeline Sketch

```diagram
╭────────────────────────╮    ╭──────────────────────────╮    ╭───────────────────────╮
│ Trips at outcome=      │───▶│ Per-trip feature vector   │───▶│ FP-Growth per agency │
│ {booked, churned,      │    │ (destination, season,     │    │ on rolling window     │
│  escalated_late}       │    │  traveler_shape,          │    ╰────────┬──────────────╯
╰────────────────────────╯    │  budget_band, ...)        │             │
                              ╰──────────────────────────╯             ▼
                                                     ╭───────────────────────────────╮
                                                     │ kdd_suitability_signals       │
                                                     │ (versioned, with support /    │
                                                     │  confidence / lift / N)       │
                                                     ╰──────┬────────────────────────╯
                                                            │
                                                            ▼
                                                     ╭────────────────────────────────╮
                                                     │ Suitability renderer (consumer)│
                                                     │ Counter-signal at intake       │
                                                     ╰────────────────────────────────╯
```

## 12. Decision Recommendation

**Defer one cycle behind KDD v0**, not because the topic is less valuable, but because:
- Suitability mining has a harder N problem and needs more data to be honest.
- KDD v0 proves the mining-pipeline infrastructure pattern; suitability mining reuses it directly.
- The renderer team can develop against a stub signal feed in parallel without blocking on mining quality.

When KDD v0 ships and is consumed for 2-4 weeks, start suitability mining as v0.5 reusing the same pattern-store, job runner, and review surface. Estimated effort if KDD v0 lands cleanly: 1-2 days additional.

## 13. Kill Criteria

If after 4 weeks of operation with above-threshold data, mined suitability signals do not change a single intake-time hint or operator decision, scrap and revisit. Mining without consumption is theater.

## 14. Open Questions

1. What is the destination taxonomy? Existing field, new dimension, or external (e.g., Amadeus locations)?
2. What is the canonical definition of "successful trip"? Booked-and-not-churned within X days? Within trip departure date?
3. Does counter-signal surfacing at intake time conflict with the existing gate system? Coordinate with validators.
4. Cross-agency benchmarking: who owns the opt-in flow?
5. How does the renderer consume signals — direct DB read, API, materialized view?

---

*Exploration document. Decisions are recommendations until reviewed.*
