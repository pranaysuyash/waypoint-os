# Knowledge Discovery from Data (KDD) — Exploration

**Date**: 2026-05-18
**Status**: Exploration draft. Not implemented. Pre-decision.
**Owner**: TBD
**Parent index**: [../EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) §6b
**Related**: Evaluation Framework (#6), LLM Strategy & Cost (#4), Advanced Learning & Optimization (#15), Multi-Dimensional Priority Scoring (#20), AI override controls launch blocker (AGENTS.md / Timeline schema fix example)

---

## 1. What KDD Means Here

KDD (Fayyad, Piatetsky-Shapiro, Smyth, 1996) is the umbrella process:

```diagram
╭──────────╮   ╭───────────────╮   ╭───────────────╮   ╭─────────────╮   ╭────────────────────╮
│Selection │──▶│ Preprocessing │──▶│ Transformation│──▶│ Data Mining │──▶│ Interpretation /   │
│(target   │   │ (clean, fill, │   │ (features,    │   │ (cluster,   │   │ Evaluation         │
│ dataset) │   │  dedupe)      │   │  reduction)   │   │  rules,     │   │ (knowledge,        │
╰──────────╯   ╰───────────────╯   ╰───────────────╯   │  sequence)  │   │  feedback loop)    │
                                                       ╰─────────────╯   ╰────────────────────╯
```

Data mining is one step inside KDD, not the whole thing. The "knowledge" output is what we can act on — usually a pattern, rule, cluster, anomaly, or prediction that changes a downstream decision.

## 2. Why This Fits Waypoint OS Specifically

The app already persists the four data streams KDD needs. This is the critical fact that distinguishes "real opportunity" from "buzzword fit":

| Stream | Source | Use in KDD |
|---|---|---|
| Operator overrides | `spine_api/routers/audit.py`, override events on trips | Labeled correction signal for AI failure modes |
| Gate decisions | `Validation.gate`, `Validation.reasons` on run status | Failure cause association rules |
| Lifecycle events | Trip event timeline, status transitions | Process mining, time-to-stage |
| Intake corpus | Raw notes + extracted slots | Cluster intake phrasings, find systematic miss patterns |

We are not proposing to add instrumentation; we are proposing to mine instrumentation that already exists.

## 3. Honest Volume / Maturity Check

KDD value scales with N. Pre-launch, N per agency is small. This is the strongest argument *against* premature implementation, and we want to address it head-on rather than wave it away:

- **Works at low N**: process mining (per-trip), single-agency override review, gate-failure tagging, manual pattern surfacing.
- **Needs medium N**: association rule mining over intake → escalation patterns, override clustering, suitability signal mining from successful trips.
- **Needs large N**: cross-agency anomaly detection, model-quality drift detection, agency benchmarking.

**Conclusion**: build the pipeline now (selection + preprocessing + storage), enable the low-N applications now, gate the medium/large-N applications behind explicit data-volume thresholds rather than ship-when-ready dates.

## 4. Ranked Applications

### 4.1 Override Mining → Continuous Improvement Loop (HIGHEST LEVERAGE)

**Problem this solves**: AGENTS.md flags "AI override controls" as a launch blocker. Today, when an operator overrides an AI decision, the correction is captured but not systematically learned from.

**KDD framing**:
- **Selection**: all `(trip, ai_decision, operator_decision, override_reason, intake_features)` tuples where decision ≠ override.
- **Preprocessing**: normalize override reason free text; align decision schema versions.
- **Transformation**: feature-engineer intake (length, slot completeness, destination class, traveler shape, season); encode decision deltas.
- **Mining**: cluster overrides by (decision_delta × intake_features). Look for tight clusters = systematic failure modes.
- **Interpretation**: each tight cluster becomes either (a) a prompt/extractor patch candidate, (b) a new validation rule, or (c) a training example for fine-tuning.

**Output artifact**: weekly digest "this week the AI was systematically wrong about X, Y, Z" surfaced into the same surface as the suitability renderer.

**Why this beats generic eval**: evaluation tells you the score went down. Override mining tells you *why* and *what to change*.

### 4.2 Escalation Cause Discovery (HIGH)

**Problem**: Gate failures (NB01, NB02, etc.) escalate trips. Today the failure is logged with reasons but cross-cutting patterns are invisible.

**KDD framing**: Apriori / FP-Growth association rule mining over `(intake_features) → (gate_failure)`. Surface rules like "destination=cruise AND travelers≥6 → NB02 with 73% support, 81% confidence."

**Acts on**: validator improvements, extractor prompt edits, UI hints at intake time ("this combination usually requires extra info").

### 4.3 Suitability Signal Mining (HIGH, ties to launch blocker)

**Problem**: Suitability renderer is blocked because the suitability signals don't exist as a curated dataset.

**KDD framing**: Mine *successful* trip outcomes (booked, no churn-back, no late escalation) for repeatable (destination × season × traveler-shape × budget-band) tuples. Each tuple with sufficient support becomes a discovered suitability rule.

**Why KDD instead of having an LLM invent them**: discovered signals are grounded in agency-specific historical truth. LLM-invented signals are plausible but untraceable.

### 4.4 Process Mining on Workflow Timelines (MEDIUM)

**Problem**: We have no systematic view of where trips slow down.

**KDD framing**: classical process mining on trip event sequences. Output: average time-to-stage per agency, drop-off probabilities at each stage, common variant paths.

**Cheap** because event data already exists. Operational rather than AI value.

### 4.5 Cross-Agency Anomaly Detection (DEFER)

Only useful at high N. Defer until at least 5-10 agencies with meaningful trip volume. Worth listing so we don't forget; not worth building now.

## 5. What KDD Does NOT Help With

Honest scope discipline:
- Performance issues (e.g. unified-state slowness) — orthogonal.
- Auth / security gaps — orthogonal.
- UI/UX gaps — orthogonal except where KDD outputs become new UI surfaces.
- Anything where the underlying data is too sparse to mine honestly.

We will not ship a "KDD dashboard" for the sake of having one. KDD outputs only ship if they change a real decision somewhere.

## 6. Relationship to Existing Systems

| Existing system | Relationship |
|---|---|
| Evaluation Framework (#6) | Complementary. Eval measures *whether* the system improved; KDD produces the patterns that suggest *what to change*. |
| LLM Strategy (#4) | Override-mining outputs feed prompt versioning and (eventually) fine-tuning datasets. |
| Multi-Dimensional Priority Scoring (#20) | KDD-discovered features can become priority signals. |
| `audit.py` / `analytics.py` / `product_b_analytics.py` | Source data layer. KDD reads, does not duplicate. |
| Override controls (launch blocker) | KDD provides the corpus that makes override controls a learning loop instead of a logging surface. |

Critically: KDD must **not** become a parallel analytics stack. It reuses the existing audit/analytics persistence layer and adds a mining/interpretation layer on top.

## 7. Pipeline Design (Minimal First Version)

```diagram
╭──────────────────╮     ╭──────────────────╮     ╭──────────────────╮
│ Source tables    │────▶│ KDD feature view │────▶│ Mining jobs      │
│ - audit events   │     │ (materialized,   │     │ (scheduled,      │
│ - validations    │     │  versioned)      │     │  per-pattern)    │
│ - trips/events   │     ╰──────────────────╯     ╰────────┬─────────╯
╰──────────────────╯                                       │
                                                           ▼
                              ╭──────────────────────────────────╮
                              │ Discovered patterns store        │
                              │ (versioned, with support /       │
                              │  confidence / sample size)       │
                              ╰────────┬─────────────────────────╯
                                       │
                                       ▼
                              ╭──────────────────────────────────╮
                              │ Consumers:                       │
                              │ - weekly digest                  │
                              │ - prompt/validator update PRs    │
                              │ - suitability renderer feed      │
                              │ - ops anomaly alerts             │
                              ╰──────────────────────────────────╯
```

**Key design choices**:
- Feature view is materialized + versioned so mining is reproducible.
- Patterns store includes support/confidence/sample size so consumers know what to trust.
- No "live" mining at request time — all mining is batch and the consumer surfaces read precomputed patterns.

## 8. Risks and Failure Modes

- **Low N**: discovered patterns are noise. Mitigation: enforce minimum support thresholds; surface "insufficient data" instead of fake patterns.
- **Cross-agency leakage**: mining across agencies risks PII or competitive data leaks. Mitigation: per-agency scope by default; cross-agency only on aggregated, anonymized features.
- **Pattern drift**: a rule that was true last quarter may not hold now. Mitigation: re-mine on rolling window; version patterns; expire stale ones.
- **Over-trust**: operators may treat patterns as ground truth. Mitigation: always surface support / sample size next to the pattern.
- **Duplicates the eval framework**: real risk if scope creeps. Mitigation: hard boundary — KDD produces patterns, eval measures outcomes. No overlap.

## 9. Open Questions Before We Build

1. What is the agency-volume threshold below which we suppress mined patterns entirely?
2. Do we need a separate `patterns` table or can we extend `audit`?
3. Who consumes the weekly digest — operators, agency owners, internal team?
4. How are mined suitability signals reconciled with operator-curated ones?
5. Where does this run — same backend, separate worker, or notebook-only for v0?
6. What's the kill criterion if mined patterns aren't producing actionable changes after N weeks?

## 10. Decision Recommendation

**Proceed to a small v0 prototype gated on override-corpus mining only**, because:
- The override corpus is the highest-leverage stream.
- It directly feeds a known launch blocker.
- It's the only application where even single-digit N is informative (a cluster of 3 identical overrides is already actionable).
- It avoids the volume problem that kills the other applications at this stage.

Defer everything else (rules mining, process mining, anomaly) until v0 proves the loop works end-to-end and is consumed.

**Kill criteria for v0**: if after 4 weeks of operation, zero mined patterns have led to a concrete prompt/validator/UI change, scrap and revisit. KDD that doesn't change downstream decisions is theater.

## 11. v0 Scope (Handoff-Ready)

A locked, implementation-ready scope for the override-mining v0 lives at [KDD_V0_OVERRIDE_MINING_SCOPE_2026-05-18.md](KDD_V0_OVERRIDE_MINING_SCOPE_2026-05-18.md). It covers file plan, one-table schema, acceptance criteria, kill conditions, and what is explicitly out of scope. Any expansion beyond v0 returns here first, not inline in the scope doc.

## 12. Next Actions (if pursued)

1. Confirm override audit schema is sufficient (likely needs structured `decision_delta` field).
2. Define feature view spec (intake features × decision schema).
3. Pick first mining algorithm (k-means on encoded overrides as cheapest start, or HDBSCAN if intake feature space is high-dim).
4. Build the patterns store (versioned, with support / confidence / sample size).
5. Wire one consumer: the weekly digest. Skip the prompt-update PR pipeline until digest proves useful.

---

*This is an exploration document. Decisions captured here are recommendations, not commitments. Update with evidence as work progresses.*
