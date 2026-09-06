# C-03 — Real Model-Routing Policy Design for Waypoint OS

**Date:** 2026-09-02
**Persona:** PER-0882 Model-Routing Optimization Engineer (central question: *which model handles this case, and what evidence makes the routing policy better than one-model-for-everything?*)
**Scope:** DESIGN ONLY — read-only on code; no implementation, no commits. Builds on `BROWSER_LLM_SLM_RESEARCH_2026-08-31.md` §5 sketch and the now-live eval ground truth.
**Companions:** `C02_WIRE_OR_ARCHIVE_DOSSIERS_2026-09-02.md` (hybrid engine is now wired default-ON), `C04_SLM_BENCHMARK_PROTOCOL_2026-09-02.md` (tier-0.5 admission evidence).

---

## 0. Ground truth this design stands on

### 0.1 What exists today (verified 2026-09-02)

| Component | State | Evidence |
|---|---|---|
| Tier-0 deterministic extraction | Live, serving path | `src/intake/extractors.py` (22 `_extract*` passes, ~30 fact fields), `src/intake/geography.py` (590k-city set), gates |
| **Hybrid decision engine (rules→LLM)** | **Wired, flag default-ON** — this is already a de-facto tier-1 for *risk flags* | `src/intake/decision.py:36,1192,2166`; `src/decision/hybrid_engine.py:336-477`; `.env.example:65` |
| `checker_model` knob | **Stored, editable in UI, never consumed at runtime** | Defined `src/intake/config/agency_settings.py:304` (`"gemini-2.0-flash"`), contract `spine_api/contract.py:436`, settings routes `spine_api/routers/settings.py:762,805-806`, frontend `frontend/src/lib/api-client.ts:809`, `AiAgentTab.tsx:343-344`. No call site passes it to any client. `spine_api/services/public_checker_service.py` is deterministic |
| `routing_health` metrics | Reduce `ExecutionEvent.event_metadata`; today they grade eval-harness events, real values `null` | `src/evals/agentic_feedback.py:509-560` (`fallback_trigger_reason`, `fallback_result`, `review_outcome`, `escalation_outcome`, `latency_ms`, `cost_estimate_usd`); thresholds `agentic_feedback.py:778-786`; D6 snapshot shows `correct_escalation_count: null` (`data/evals/d6_audit_gate_snapshot.json`) |
| Egress/guard rails per decision type | Live and **mandatory** — every egress payload must have a registered policy | `spine_api/core/llm_egress.py:94-141` (`_EGRESS_POLICIES` keyed by `DecisionType`; raises if a type lacks one, `llm_egress.py:245-251`); per-agency usage guard `src/llm/usage_guard.py:1-31` (SQLite budgets, feature `hybrid_engine`) |
| Eval lanes (ground truth) | Budget lane **live**: F1 0.9524 / 20 fixtures (`d6_audit_gate_snapshot.json` `budget_health`); colloquial lane live (15 fixtures, `data/fixtures/extraction/colloquial_golden.json`); scenario lane live w/ drift (`scenario_health.baseline_drifted: true`; N-01: 13 drifting scenarios, composite 0.5667); extraction lane blocked on missing `raw_input` (N-02, 50 fixtures); pipeline lane missing producer (N-03, 7 fixtures); journey smoke in CI (`tests/test_journey_smoke.py`, `_e2e.py`) | `src/evals/audit/snapshot.py:92-263` (`_collect_live_budget_results`, `_collect_live_colloquial_results`, …) |
| Gate signals usable as router inputs | `INTAKE_MINIMUM = [destination_candidates, date_window]` → ESCALATE when missing; `QUOTE_READY_INCOMPLETE` warning → DEGRADE | `src/intake/validation.py:50-66,119-126`; `src/intake/gates.py:101-153` |
| Human-gated LLM precedent | Vision extraction: provider fallback chain, confidence, `pending_review` states | `spine_api/services/extraction_service.py:63-117,271,527`; `spine_api/routers/trip_documents.py:492,527` |

### 0.2 The design gap (G-02, restated precisely)

There is no runtime component that decides *which model* handles a case, records that decision, or can be evaluated as a policy. Two artifacts *pretend*: (a) `checker_model` is an agency-visible knob wired to nothing; (b) `routing_health` thresholds exist with real-null inputs. The policy below makes both real without inventing a parallel system — it extends the tier-0 pipeline and the hybrid engine's existing guard/egress/telemetry rails.

---

## 1. Policy: tier ladder

| Tier | What | Cost/latency | Status |
|---|---|---|---|
| **T0 — Deterministic extractors** | `ExtractionPipeline`, geography, route analysis, decision rules, not-applicable rules | $0, ms | **Live. Always runs first. Always authoritative for anything it captures with confidence ≥ threshold.** |
| **T0.5 — On-device/browser SLM draft** | Gemini Nano (Chrome `responseConstraint`) or WebLLM/XGrammar draft → server re-extracts canonically; server remains authority | $0 + device time | **Opt-in experiment, gated on C-04 benchmark + disagreement telemetry.** Not in this policy's first release. |
| **T1 — Cloud small** | `checker_model` class (default `gemini-2.0-flash`), restricted to the first justified insertion point: **NB01 colloquial extraction**, and (already live) hybrid-engine risk-flag LLM fallback | ~$0.001–0.01/note | **First release target.** |
| **T2 — Cloud large** | Escalation-only re-attempt on T1 validation failure or high-stakes conflict | ~10–50x T1 | **Same release as T1; expected to fire rarely (target <10% of escalations).** |
| Deterministic-forever | Gates (NB01/NB02), leakage policy, autonomy/approval policy, persistence, fees | — | Models may inform, never be. (Deep map §5.2; `gates.py:47-68` D1 separation.) |

---

## 2. Task classification — post-T0 evidence, never prompt length

The classifier runs **after tier 0**, from artifacts the pipeline already produces. No text-statistics heuristics.

| Signal | Source (all existing) | Routes to |
|---|---|---|
| `INTAKE_MINIMUM` unmet (missing `destination_candidates` or `date_window`) | `validation.py:50-53`; NB01 ESCALATE verdict `gates.py:101-153` | **T1** (before the lead is persisted as incomplete, one bounded attempt to recover the missing minimum fields; ESCALATE still persists the lead if T1 also fails — ADR_ESCALATE_LEAD_PERSISTENCE semantics unchanged) |
| `QUOTE_READY_INCOMPLETE` warning (missing origin/party/budget/purpose) | `validation.py:119-126`; NB01 DEGRADE | **T1** for missing follow-up fields only |
| Colloquial-pattern miss (known verb-object/party/date patterns absent but free-text present) — measured as **field coverage delta vs the colloquial corpus baseline**, not prompt length | colloquial lane features; `extractors.py` pattern families | **T1** |
| Ambiguity/contradiction/unknown counts above thresholds | `CanonicalPacket.ambiguities/contradictions/unknowns` (`packet_models.py:452-454`) | **T1**; contradictions on high-stakes fields → **T2** |
| Confidence below threshold on any `INTAKE_MINIMUM`/`QUOTE_READY` slot | `Slot.confidence` (`packet_models.py:154`) | **T1** |
| T1 output fails `validate_packet` or degrades gate score | `validation.py`; `gates.py` | **T2** (bounded retries, default 1) |
| Hybrid-engine rule miss on a risk-flag decision type | `hybrid_engine.py:419-477` LLM tier is already exactly this pattern | Already wired (T1-by-construction); its telemetry becomes router telemetry (§6) |

**Router contract (new module, extends — not forks — the intake path):**

```text
classify(packet, validation_report, gate_result) -> RouteDecision{
  tier: T1|T2, reason: enum, fields_targeted: [..], budget: INR cap from usage_guard,
  authority: "advisory" | "suggestion_pending_review"
}
```

Fields targeted are the *missing/low-confidence* fields only — a T1 call never re-litigates what T0 already captured (this is the vision-extraction service shape: propose, validate, record authority; `extraction_service.py:63-117`).

---

## 3. Per-tier quality profiles — what evidence each tier must produce

Each tier gets a **quality profile**: the eval lane(s) whose numbers define it, refreshed per model-version change. Ties directly to the live lanes.

| Tier | Required evidence profile (lane → bar) | Current anchor |
|---|---|---|
| T0 | Budget lane F1 ≥ 0.95 (anchor 0.9524); colloquial lane F1 trend; scenario lane drift triaged (N-01) | `snapshot.py` baselines: `EXPECTED_BUDGET_BASELINE_F1`, `EXPECTED_COLLOQUIAL_BASELINE_F1` (both 1.0 constants are the *expected-as-actual* flags — replace with measured bars as lanes go live) |
| T1 | Field-level P/R **on exactly the fixtures T0 fails** (the colloquial + holdout corpora, C-04 §2); valid-JSON rate; hallucinated-field rate; **net field gain = fields T1 adds that validate − fields T1 corrupts that T0 had right** | None yet — this is what C-04 + the T1 shadow mode produce |
| T2 | **Escalation-fix rate**: of T1 validation failures escalated, fraction that produce a validating packet (else T2 is paying 10–50x for the same wrong answer — PER-0882 failure mode) | None yet |
| T0.5 | C-04 admission criteria (parity ≥85% vs T1 on golden set; device coverage; consent; disagreement telemetry) | `BROWSER_LLM_SLM_RESEARCH` §4d/§5 |

A model is admitted to a tier only if it meets that tier's profile on the frozen golden set, and a model/policy change re-runs the **router regression suite** (§5) before promotion.

## 4. Escalation, failover, budgets

- **Escalation triggers** (T0→T1): the classification table in §2; (T1→T2): validation failure after T1, or INTAKE_MINIMUM still unmet, or high-stakes field conflict. Every escalation writes `before/after field diff` metadata.
- **Failover:** provider chain per tier exactly as vision extraction already does (`ModelChain`, `MAX_PROVIDER_RETRIES` via `extraction_service.py:13,110-149`); hybrid engine's Gemini-primary/OpenAI-fallback (`hybrid_engine` LLM clients) is the in-path instance. On total LLM failure: **fall back to T0 output + existing gates** — the system must remain correct with all tiers dark (today's behavior proves this).
- **Budgets & kill switches:** per-agency `usage_guard` (SQLite budgets, hot-reloadable, `usage_guard.py:1-31`) is the spend authority for T1/T2; `LLM_GUARD_ENABLED` kill switch; egress policy per `DecisionType` is mandatory (`llm_egress.py:245-251`) — every new router decision type registers a policy *before* its first call (CI-enforceable).

## 5. Router-level regression suite + promotion gate

1. **Frozen request bundles:** golden corpora (budget 20, colloquial 15, golden_dataset 50 once N-02 lands, hidden holdout per G-06) replayed through the full T0→classify→T1→T2 chain with the policy version stamped.
2. **Shadow-mode replay** for any policy/model change: replay decides routes, but production output stays T0-only until the shadow run proves net field gain ≥ 0 at cost ≤ current.
3. **Promotion rule:** a new policy version ships only if task-success (accepted-packet rate on the suite) ≥ current policy at ≤ current cost-per-accepted-packet. This is the same CI philosophy as the D6 snapshot gate (`scripts/verify_d6_gate_snapshot.py`), extended from snapshot-drift to policy-drift.
4. **CI parity with prod (closes C-02 H-01):** the suite runs the same `USE_HYBRID_DECISION_ENGINE` value prod runs; the `snapshot.py:706-716` forced-OFF block is removed once the hybrid path has its own lane.

## 6. Making `routing_health` REAL

The reducer already accepts exactly the right metadata; the router (and the hybrid engine, already live) must *emit* it into `ExecutionEvent.event_metadata`:

| Metric today (null) | Real input once wired | Emitter |
|---|---|---|
| `fallback_trigger_reason` / `fallback_result` | T1/T2 call attempted → `succeeded_after_fallback` if the escalated tier produced a validating packet; `exhausted` when the retry bound is hit | Router wrapper around each LLM call (and hybrid `_call_llm`, which already knows source/cost/latency — `hybrid_engine.py:423-437,537-600`) |
| `review_outcome` / `escalation_outcome` | Advisor accept/reject on T1-proposed fields (vision-extraction's `applied/rejected/pending_review` states, `extraction_service.py:271`) = ground truth for false-escalation tracking | Field-proposal review loop (copy `extraction_service.py` review states) |
| `latency_ms`, `cost_estimate_usd` | Already computed by hybrid telemetry & usage guard | Bridge `src/decision/telemetry.py` → `ExecutionEvent` |
| **New: tier attribution** | `route_tier`, `route_reason`, `fields_targeted`, `checker_model` (the knob finally consumed) | Router |

Thresholds (`fallback_trigger_rate` warn 0.3/critical 0.5 etc., `agentic_feedback.py:778-786`) then measure a real population. **Cost metric upgrade:** track *cost per accepted packet*, not per token (PER-0882 "savings without task success" guard).

## 7. What the `checker_model` knob becomes

`checker_model` (`agency_settings.py:304`) becomes the **agency-scoped T1 model id** consumed by the router wrapper (and by the public-checker T1 path when enabled). Until the T1 path ships, the settings UI copy should say "applies once AI extraction is enabled" rather than implying an active model choice — same honesty rule as IMP-03's sample-profile gating.

## 8. Release plan (dependency-ordered)

| Step | Deliverable | Precondition |
|---|---|---|
| R1 | Ratify C-02 H-01 (hybrid flag posture) + CI/prod parity | Owner decision |
| R2 | Router module: `classify()` from existing artifacts + telemetry emission; zero behavior change (T0-only mode) | none |
| R3 | routing_health fed by hybrid telemetry bridge → D6 shows real counts | R1, R2 |
| R4 | C-04 benchmark run → T1 tier profile (candidate models, corpus) | R2; colloquial+holdout corpora finalized |
| R5 | T1 behind NB01 escalation, `authority: suggestion_pending_review` (vision-extraction pattern), agency-gated by a new `enable_ai_extraction`-style setting | R4 evidence |
| R6 | T2 escalation + escalation-fix-rate metric | R5 |
| R7 | Router regression suite in CI (policy-versioned) | R5 |
| R8 | T0.5 opt-in on-device experiment | C-04 admission criteria all green |

## 9. Open questions

1. Ratify first insertion point: NB01 extraction only, or NB01 + suitability Tier-3 (C-02 §2.2) in the same release? (Recommend extraction only — one LLM entry point until its eval lane is stable.)
2. Should T1 outputs auto-populate with recorded confidence/authority, or land as advisor-confirmable suggestions? (Recommend suggestions for `INTAKE_MINIMUM`-critical fields, auto-populate for low-stakes fields — mirrors the Level-1-vs-2 question in the deep map §7.5.)
3. PII policy for cloud tiers: full-text vs pseudonymize-reattach (open in browser research §6.7) — needs a DPA answer before T1 default-on.
4. Is `checker_model` per-agency variance actually wanted at T1, or should agencies control only on/off and the platform pin the model (regression surface shrinks dramatically)?
5. Budget units: usage_guard is INR-denominated (`hybrid_engine` cost 0.15 INR example) while `routing_health` is USD — unify before real numbers land.
