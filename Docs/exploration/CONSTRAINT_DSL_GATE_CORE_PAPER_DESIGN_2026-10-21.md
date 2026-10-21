# Constraint-DSL Gate Core — Paper Design (ChinaTravel pattern → Waypoint gates)

**Date:** 2026-10-21
**Status:** Paper design only — no implementation. Answers the topic 48 question: *does a constraint-DSL gate core or the replay/fork harness deliver more launch credibility per effort?*
**Source pattern:** [ChinaTravel](https://github.com/LAMDA-NeSy/ChinaTravel) (ICLR'26; official benchmark of the IJCAI 2025 + 2026 Travel Planning Challenge) — `chinatravel/symbol_verification/{commonsense_constraint,hard_constraint,dsl,preference}.py` and its evaluation readme, read 2026-10-21.

---

## TL;DR

ChinaTravel's contribution is not the dataset — it is a **verification protocol**: a fixed catalog of environment constraints checked against ground truth, personal constraints compiled from the request into executable predicates, evaluated in a strict order (schema → commonsense → hard constraints → preference) where **any validity failure zeroes the preference score** — no "nice itinerary" can outrank a wrong one. Waypoint already has gate scaffolding (`PipelineGate`, `GateVerdict`, canonical `GateIdentifier`s) and a symbolic plan representation (the journey graph), but its correctness checks are prose-coded heuristics scattered across intake gates, suitability rules, fee calculation, and judge rubrics. The transplant is a **Plan Constraint Gate**: a typed catalog of executable constraints evaluated over the journey graph + options packet, with per-constraint evidence written to the audit trail. Recommendation: **do this before the replay/fork harness** — it hardens what operators and travelers actually see, and it is the thing an external reviewer can inspect.

---

## 1. What ChinaTravel actually does (the transferable parts)

| Layer | Mechanism | Transfers to Waypoint? |
|---|---|---|
| **Environment / commonsense constraints** | ~27 fixed checks: entity exists in sandbox; price & duration match source; `cost = price × tickets` / `× rooms` / `× cars` (taxi capacity 4); opening hours; no repeated attractions/restaurants; meal-time windows; hotel required for >1 day; every activity has start<end; chronological order incl. transport arrival; spatial continuity (position change ⇒ a transport leg exists) | **Yes, nearly 1:1** — these are provenance + arithmetic + topology checks on a plan |
| **Personal / hard constraints** | Request → DSL (LLM-translated, rule-audited) → `get_symbolic_concepts(plan)` extracts variables → `evaluate_constraints` runs predicates | **Yes** — Waypoint's intake facts *are* the request; the compilation target changes |
| **DSL execution** | Restricted Python subset: whitelisted `ast` node types + builtins (`abs,len,max,min,sum…`), no I/O, "safe DSL control flow" | **Pattern yes, interpreter maybe** — see §3.2 |
| **Preference scoring** | Only computed for plans that passed validity; "preference scores are not a bypass" | **Yes — the single most important rule to adopt** |
| **FPR metric** | Penalizes over-constraining (rejecting valid plans) | **Yes** — maps to Waypoint's false-escalation concern |
| **Sandbox data** | China-domestic POIs/trains/hotels, bilingual | **No** — India-first, international; the data does not transfer, only the protocol |

## 2. What Waypoint has today (verified 2026-10-21)

- `src/intake/gates.py`: `PipelineGate` protocol; `NB01CompletionGate` (structural validity + QUOTE_READY completeness → PROCEED/DEGRADE/ESCALATE, density heuristic `len(facts)/10`); `NB02JudgmentGate` (decision verdict × agency autonomy policy → `AutonomyOutcome` with `effective_action`, `rule_source`, `safety_invariant_applied`). Canonical ids in `src/intake/constants.py` (`GateIdentifier`), legacy `NB01..NB06`.
- Plan-level correctness is **distributed**: `src/suitability/context_rules.py` + `integration.py`, `src/fees/calculation.py`, `BUDGET_FEASIBILITY_TABLE` (INR-first), `src/evals/judge/{rubrics,scorer}.py`, `src/evals/audit/rules/{extraction,activity}.py`, `src/evals/audit/gates.py` (`CategoryGateDecision`, `EvalGateReport`). None of these is a single "is this plan valid against this traveler's constraints" verdict.
- A symbolic plan exists: the **journey graph** (`spine_api/routers/journey_graph.py`, JDG nodes consumed by `irops_watch_service`) — nodes are flights/transfers/stays with times and positions. This is the analogue of ChinaTravel's `plan_json`, and chronology/spatial constraints evaluate naturally over its edges.
- The KDD lane (`src/analytics/kdd/`, `scripts/run_hybrid_kdd_experiment.py`) gates **extraction quality** (F1 on facts). It is not a plan validator; the two are complementary — KDD guards the inputs, the constraint gate guards the outputs.

## 3. The design

### 3.1 Constraint catalog (two families, typed, versioned)

```
ConstraintSpec
  id: "ENV.COST_ARITHMETIC" | "PER.BUDGET_CAP" | …
  family: ENVIRONMENT | PERSONAL
  severity: HARD | SOFT              # HARD fails validity; SOFT lowers preference
  params_schema: {...}               # e.g. {cap: Money, scope: per_person|total}
  predicate: Callable[[SymbolicPlan, Params], ConstraintResult]
  evidence_fields: [...]             # which plan values are copied into the result

ConstraintResult
  id, passed: bool | None            # None = UNVERIFIED (missing data) — never coerced to pass
  evidence: {field: value}           # the numbers the verdict was made from
  source_facts: [fact_ids]           # provenance back to intake facts / producer rows
  message: str                       # operator-readable
```

**Environment family — initial set, each already motivated by live evidence:**

| id | Check | Evidence from this project |
|---|---|---|
| `ENV.ENTITY_GROUNDED` | every airport/hotel/POI in the plan resolves against the producer result or gazetteer | HN: "AI suggests places that don't exist"; gazetteer collision sweep (FND-0308+) |
| `ENV.PRICE_HAS_SOURCE` | every priced component carries `sources[]` with `retrieved_at`; unpriced ⇒ UNVERIFIED | trvl probe: 48/158 rows unpriced |
| `ENV.PRICE_BASIS_KNOWN` | `price_basis` ∈ {native_quote, converted_estimate, tax_inclusive_total…}; converted ⇒ SOFT flag | trvl probe: 27 fractional converted prices |
| `ENV.CURRENCY_CONSISTENT` | one settlement currency per plan or an explicit FX record (topic 44) | trvl probe: 5 currencies in one result set |
| `ENV.COST_ARITHMETIC` | component total = unit × pax × nights (± rounding), plan total = Σ components | ChinaTravel `cost = price × tickets` |
| `ENV.CHRONOLOGY` | JDG nodes ordered; activity start ≥ arrival of inbound transport | ChinaTravel Time constraints |
| `ENV.SPATIAL_CONTINUITY` | position change between nodes ⇒ a transport edge exists | ChinaTravel Space constraint |
| `ENV.LODGING_FOR_MULTIDAY` | trip > 1 day ⇒ accommodation node per night | ChinaTravel Accommodation |
| `ENV.NO_DUPLICATE_POI` | same attraction not scheduled twice unless flagged intentional | ChinaTravel Attractions |

**Personal family — compiled from intake facts (the existing extractor output is the "request"):** `PER.BUDGET_CAP` (per-person vs total, honoring D-01 trip-duration + D-02 flights-inclusiveness contracts), `PER.PARTY_SIZE_SATISFIED` (rooms/seats cover `travelers[]`), `PER.DATE_WINDOW` (season/explicit dates), `PER.MUST_INCLUDE` / `PER.MUST_AVOID` (destinations, red-eye, overnight transit), `PER.ACCESSIBILITY` / `PER.DIETARY` (from traveler facts), `PER.PACE` (SOFT: max activities/day). Each personal constraint records the fact ids it was compiled from — so a failing constraint points back to the exact traveler statement.

### 3.2 Execution: typed predicates first, DSL interpreter only if needed

ChinaTravel needs a DSL because *arbitrary* NL requests must become executable checks at benchmark scale. Waypoint's constraint vocabulary is bounded by its intake ontology (states/events/actions, `required_for` — intake ontology v2). So: **phase 1 = a registry of Python predicates with declarative instances** (`{id, params, source_facts}` stored on the trip), fully testable, no `eval`, no AST interpreter — the fact → constraint compilation is a deterministic mapping, not LLM translation. **Phase 2 (only on demand):** adopt the restricted-AST interpreter pattern (`dsl.py`'s whitelist approach) so agencies can author custom constraints; keep the whitelist, add a static analyzer pass, and sandbox-test against the adversarial corpus (prompt-injection lane) before any agency can submit one.

### 3.3 Where it sits: a Plan Constraint Gate

New gate implementing `PipelineGate`, canonical `GateIdentifier.PLAN_CONSTRAINTS`, evaluated after options/strategy and **before** anything becomes a quote or proposal:

- all HARD pass → `PROCEED` (score = SOFT pass ratio)
- HARD pass, SOFT failures → `DEGRADE` with the SOFT list as reasons (operator sees trade-offs)
- any ENVIRONMENT HARD fail → `ESCALATE` (a wrong plan never reaches a traveler)
- any PERSONAL HARD fail → `DEGRADE` + an ask (the existing T1 ask loop) when the failure is a missing fact, `ESCALATE` when it is a contradiction
- any `UNVERIFIED` on a HARD constraint → `DEGRADE`, never silently PROCEED (honesty rule)

**The zero-out rule:** suitability/preference scores are **not computed or displayed** for plans that fail a HARD constraint. This is the one behavior change with product consequences and should be an explicit owner decision.

### 3.4 Evidence and audit

Every `ConstraintResult` is appended to the trip's audit record with `gate_id`, `constraint_id`, `passed`, `evidence`, `source_facts`. Combined with the causal-chain idea from topic 48 (ZizkaDB's `why()`), an operator can go from "this proposal was blocked" → the constraint → the numbers → the traveler sentence that produced the constraint, in one query. This is also exactly the artifact an EU AI Act Art. 12 record-keeping posture needs.

### 3.5 Metrics (borrowed protocol, Waypoint-native data)

Do **not** run the ChinaTravel sandbox — wrong geography, wrong inventory. Borrow the protocol and point it at existing corpora: the 50 raw-input fixtures, the 30-scenario GATING lane (30/30 @ 1.0), the 21-record adversarial lane, and the persona sims. Report per plan: `schema_valid`, `commonsense_pass_rate`, `hard_constraint_pass_rate`, **FPR** (valid plans wrongly rejected — the over-constraint guard), and preference only on valid plans. Add this as a lane beside the KDD gate in CI; the KDD gate stays the input guard.

## 4. Verdict on the topic-48 question

**Constraint gate first, replay/fork second.** The gate changes what ships to travelers and what an operator can audit; the replay harness changes how fast we debug. Both are worth doing, but only one of them is launch credibility. Suggested sequence: (1) catalog + `ENV.*` predicates over the JDG with tests (small, deterministic, pairs with the producer clamps from the trvl probe); (2) `PER.*` compiled from intake facts; (3) the gate wiring + zero-out decision; (4) CI lane; (5) replay/fork harness as the next infrastructure item.

## 5. Open questions / DECIDE

1. **Zero-out rule** — suppress suitability scores on HARD-failed plans? (Recommend yes; it is the ChinaTravel insight and the honest UX.)
2. **Gate position** — after options/strategy (recommended) vs also re-run at proposal time (cheap; recommended as a re-check when producer data refreshes).
3. **Phase-2 DSL** — only if an agency asks for custom constraints; default no.
4. **Risk:** over-constraint. The FPR lane exists specifically to catch a gate that escalates valid plans; ship the metric with the gate, not after.
