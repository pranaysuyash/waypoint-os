# Determinism Audit — Waypoint OS Runtime

- **Date:** 2026-10-21
- **Scope:** every seam in the backend where behavior could be nondeterministic — LLM call sites, sampling parameters, heuristic fallbacks, fabricated confidence, and the gates that separate them. Working tree as of 2026-10-21 (uncommitted SIM4 wave included).
- **Method:** runtime truth over code reading. Every claim cites `file:line`. Live posture verified against the actual `.env` variable names present in this deployment. Three parallel evidence sweeps (intake LLM consumers, decision-side consumers, model-touching surfaces) plus first-hand verification of the load-bearing findings.
- **Companion findings:** FND-0352 … FND-0357 (registered via `scripts/findings.py`).

---

## 1. Executive summary

The architecture is **deterministic-by-default with narrow, labeled, gated probabilistic seams** — and the honesty doctrine is real, not cosmetic: the noop extractor says "nothing was extracted," unavailable resolvers abstain with recorded reasons, message dispatch never fabricates SENT, and LLM output carries provenance through the packet's hypothesis authority system.

But the audit found a consistent failure mode at the edges of that doctrine: **when the system falls back from probabilistic to deterministic, the fallback sometimes *fakes probabilism*** — hardcoded confidence numbers, wrong `source` labels, and verdicts computed then dropped. Deterministic code pretending to be probabilistic is exactly as corrosive as probabilistic code pretending to be deterministic, because both destroy the operator's ability to know when to trust the machine. All six instances found are registered as findings.

**The single most important structural fact:** the serving pipeline (`run_spine_once`, phases 1–10) is ~100% deterministic code. The only live LLM surface *inside the pipeline* today is (a) the ambiguity classifier's JEV lane and (b) the destination context resolver on `semi_open` collisions. Everything else probabilistic is either env-gated off (hybrid decision engine, vision extraction), disabled pending ratification (ask-loop services), credential-gated (live triage), or wired-dead (failure triage JEV).

---

## 2. Taxonomy used

| Tier | Meaning |
|---|---|
| **T1** | Is deterministic, and should be |
| **T2** | Is probabilistic, and must be (genuinely open-ended task) |
| **T3** | Is probabilistic where a deterministic rule of equal shape already exists (LLM is a quality upgrade, not a capability add) |
| **T4** | Deterministic code that fakes probabilism (fabricated confidence / mislabeled provenance / dropped verdicts) |
| **T5** | Probabilistic infrastructure wired but switched off (latent probabilism — posture, not defect) |

---

## 3. What actually IS what (per seam, runtime truth)

### 3.1 The serving pipeline — T1 (deterministic), with two live T2 seams

`POST /api/v1/inbound/parse` → `run_spine_once` (`src/intake/orchestration.py:187`, called from `spine_api/routers/inbound.py:203`):

| Phase | Behavior | Tier | Evidence |
|---|---|---|---|
| 1 Extraction | Regex + gazetteer (590k-city set, O(1) lookups) + normalizer heuristics. Only LLM seam: context resolver, `semi_open` only | T1 + narrow T2 | `extractors.py:3497-3514` |
| 2 Validation | Deterministic rules | T1 | `src/intake/validation.py` |
| 3 Decision | Deterministic scoring; hybrid engine call resolves to `None` when `USE_HYBRID_DECISION_ENGINE` unset (default `"0"`) | T1 (+T5) | `src/intake/decision.py:46-48, 99-121, 1394-1401` |
| 3.5 Suitability | `evaluate_activity` deterministic rules; tier3 flag is a pacing heuristic, not the LLM scorer | T1 (+T5) | `src/suitability/integration.py:238,336,372` |
| 3.2 Frontier panel | Heuristic "simulated" sentiment + ghost/trigger + specialty — labeled advisory, tier-gated | T1 (labeled simulation) | `frontier_orchestrator.py:222-226`, `orchestration.py:539-543` |
| 4 Strategy | Deterministic scoring + memory slots in **shadow mode** (`MEMORY_SLOT_READ_MODE=shadow` default: computed/audited, not applied) | T1 | `strategy.py:270-279, 299, 381-384` |
| 4.5 Fees | `MarginPolicy` — longest-prefix config resolution, fail-safe platform defaults | T1 | `src/fees/margin_policy.py:131-143` |
| 4.6–8 Bundles, sanitized view, leakage check | Deterministic | T1 | `orchestration.py:608-680` |
| 9.6 Readiness / 10 Fixture compare | Deterministic | T1 | `orchestration.py:680-694` |
| Gates NB01/NB02 | Deterministic policy gates; the JEV ambiguity action **never** sets `decision_state` | T1 | `src/intake/gates.py:101-171`, `orchestration.py:341, 300-314` |

### 3.2 Every LLM consumer and its true state

| Seam | Task | Tier | Live today? | Failure behavior | Labeled? |
|---|---|---|---|---|---|
| `intake/ambiguity_classifier.py` | 3-label clarity classification + 4 booleans | **T3** | **YES** (JEV keys present in this deployment) | Deterministic fallback of identical output shape — but fabricates `confidence=0.85` (FND-0352) | Yes: `source: jev\|deterministic_fallback`; coherence guards FND-0316 downgrade PROCEED on blocking unknowns |
| `intake/context_resolver.py` | Destination disambiguation on place-name collisions ("reading", "nice") | **T2** | YES, only on `semi_open`; kill switch `EXTRACTION_CONTEXT_RESOLVER` | Abstains with `{"available": false, reason}`; deterministic result stands | Status: SOFT_HYPOTHESIS + ASSUMED + `provider:model` provenance. **Candidates list leaks into EXPLICIT_USER facts (FND-0353)** |
| `intake/ask_reply_router.py` | Map traveler reply → packet field | T3 | NO — `JEV_ASK_LOOP_ENABLED` default off (ADR-008); only tests import | Honest abstain (`source=disabled/unavailable`, `needs_review=true`) | Exemplary (proposal-only dataclass, 0.60 act gate) |
| `intake/question_render_selector.py` | Grade question renderings | T3 | NO — same gate; verbatim question is the deterministic floor | Falls back to verbatim engine question | Yes (`selected_origin`) |
| `decision/hybrid_engine.py` | 5 risk types (mobility, pacing, budget, visa, composition) | T2-quality-add on T1 rules | **NO** — wired end-to-end, `USE_HYBRID_DECISION_ENGINE=0` in prod envelopes, pending X-09 PII-egress gate | Cache→rules→LLM→default; fact-presence gate prevents spurious LLM flags; `source=="default"` results dropped | Fully labeled (`source`, confidence constants, `llm_model`, cost) |
| `decision/model_policy.py` | Model ladder resolution | T1 (config) | Resolves only when lane ON | Blacklisted overrides rejected loudly; terminal local rung | Rung log at boot (`server.py:1288-1314`) |
| `decision/failure_triage.py` | Classify failed runs | T3 | **EFFECTIVELY NEVER** — `recovery_agent.py:66` passes `jev_client=None`, so JEV branch is dead (FND-0354) | Deterministic keyword classification | Advisory, labeled |
| `decision/live_triage.py` | Inbound message intent/urgency | T3 | YES via `POST /api/triage/message` when creds present; keyword fallback otherwise | Labeled keyword fallback | Calibrated probabilities from P(yes); advisory chips only |
| `corporate_policy/nl_evaluator.py` | Prose policy audit | **T2** (prose) with T1 regex for numeric lead-time clauses | YES when JEV available | Honest: `evaluated=false` + `unevaluated_clauses` for clauses the heuristic can't judge (FND-0322 fix) | Confidence + provenance + low-confidence list |
| `extraction/gemini_vision_client.py` (+ chain in `spine_api/services/extraction_service.py`) | Document/passport vision | **T2** | **NO in this deployment** — `EXTRACTION_MODEL_CHAIN` unset → `NoopExtractor`: honest empty, `confidence_method="noop"`, `extracted_by="noop_extractor"` | Chain fall-through → `status="failed"`; mock is opt-in with DO_NOT_LOG sentinels | Per-field confidence + `confidence_method`; apply gated on review acceptance |
| `evals/judge/scorer.py` + KDD/scenario/adversarial lanes | Grading | T2 by design | Offline/eval only — CI-gated, never serving | n/a | Eval-lane truth doctrine |
| `suitability/llm_scorer.py` | Contextual suitability verdict | T5 | Deliberately unwired (ADR-008 §4.2; ≥50-verdict corpus + shadow +0.05 F1 preconditions) | Tier-1 fallback → heuristic — **but tags `source="llm"` (FND-0355)** | Would be labeled |
| `rag/` embeddings | Retrieval | T5 | **Orphaned** — `rag` router never registered (`server.py:1575-1689`); sole live call site (`specialty_knowledge.py:61-100`) passes no rag_service → keyword fallback always | Swallows to keyword fallback | n/a |

### 3.3 Surfaces that are pure T1 (often assumed probabilistic, aren't)

- **Memory** (`src/memory/`): plain SQL/JSONL + lexical token-overlap + temporal decay. No embeddings, no LLM. Shadow-first slot promotion.
- **Group consensus / Pareto** (`group_consensus.py`): arithmetic; labeled `reality_tier="deterministic_preview"`.
- **Override learning / pattern matching**: exact/fuzzy signature matching with full provenance.
- **Agent runtime / work coordinator / requeue worker**: SQL lease + `FOR UPDATE`, status machines, poison-and-DLQ, redacted-payload replay refused.
- **Quotes read model** (`routers/quotes.py`): *derived* from persisted strategy/decision data; `quote_ready=false` + `missing` list when inputs absent — the fabricated-quotes-page defect stays dead.
- **Public checker**: external HTTP (Open-Meteo, OSM Nominatim), advisory confidence "weak by design," abstains on lookup failure.
- **Followups `/generate`**: hardcoded f-string templates despite the name (honest, if misleadingly named).
- **Message dispatch**: `SENT|FAILED|NOT_CONFIGURED|UNSUPPORTED` — never fabricates SENT.
- **Egress guard**: `prepare_egress_payload` sanitization runs before every LLM call (`openai_client.py:272-276`) — deterministic preprocessing wrapping the probabilistic seam.

### 3.4 Sampling posture (the "even when ON, is it reproducible?" question)

- All clients default `temperature=0.3` (`base.py:24`, `openai_client.py:184`, `gemini_client.py:79`) → sampled, non-reproducible output even on classification lanes.
- Reasoning models (gpt-5+/o-series) reject `temperature≠1`; handled by model-aware params (`openai_client.py:279-303`) — those models are effectively always-sampled and there is **no seed/recording** of sampling parameters in the serving path's rung log.
- The model policy blacklist correctly bars flagships (`model_policy.py:54-66`); prod posture is `"0"` pending X-09 (`model_policy.py:9-11`).

---

## 4. Findings (registered)

| ID | P | Summary | File |
|---|---|---|---|
| **FND-0352** | P1 | Deterministic ambiguity fallback fabricates `confidence=0.85`, silencing the `<0.60` review flag — a fake number changing real operator behavior | `ambiguity_classifier.py:285`, `decision.py:2667-2676` |
| **FND-0353** | P1 | Resolver-revised `destination_candidates` enter facts as `EXPLICIT_USER` with raw-span evidence while only *status* is hypothesized — LLM-invented place names cross the fact/hypothesis boundary | `extractors.py:3506-3508, 3538-3544` |
| **FND-0354** | P2 | Failure-triage JEV branch can never run (bare constructor, `jev_client=None`) — dead probabilistic wiring | `recovery_agent.py:66`, `failure_triage.py:66-68` |
| **FND-0355** | P2 | `llm_scorer` heuristic fallback tags `source="llm"` — latent provenance lie for when the module activates | `llm_scorer.py:282` |
| **FND-0356** | P2 | Checker's `requires_manual_audit` verdict computed then dropped; `confidence_delta` has zero consumers — operator-relevant safety output lost | `frontier_orchestrator.py:95,109`, `orchestration.py:547-557` |
| **FND-0357** | P3 | `audio_intake` hardcoded `confidence_score=0.96` on a pure-regex path (orphaned, but fabricated-by-construction) | `audio_intake.py:75` |

**Positive findings worth protecting** (the honesty doctrine is load-bearing — do not regress these): noop-extractor honesty with `confidence_method="noop"`; resolver/ask-loop abstain-with-reason; fact-presence gate that stops spurious LLM risk flags; `source=="default"` drop; NB02 gate owning `decision_state` exclusively; memory shadow mode; fail-safe margin defaults; never-fabricate-SENT dispatch; quotes derived-read-model; boot-time rung log.

---

## 5. What we should do / could do (ranked)

### Should do (small, high-integrity)

1. **Kill every fabricated confidence number** (FND-0352, -0355, -0357). Rule: a confidence value must be *derived* (calibrated from eval data) or absent. Rule-engine fallbacks should emit `confidence_method="rule"` and either omit confidence or emit a conservative value below the review threshold. This is a ~3-file fix and the highest integrity-per-line change available.
2. **Close the fact/hypothesis boundary leak** (FND-0353): route resolver-revised candidates through `set_hypothesis` like the status, or introduce a provenance-tagged authority level (e.g., `MODEL_PROPOSED`) that renders as user-editable suggestion, not fact.
3. **Wire the checker verdict into the result or rename it** (FND-0356): `requires_manual_audit` reaching no surface is a silent safety loss; either copy it into `decision.rationale` + operator surface, or rename the module honestly (it currently "simulates a checker" per its own docstring).
4. **Decide failure-triage** (FND-0354): pass a policy client in `recovery_agent` per ADR-008, or supersede the JEV branch (supersession workflow) so the code matches reality.

### Could do (structural, when gates open)

5. **Sampling reproducibility forensics**: log `(model, temperature, request-hash)` per LLM call alongside the existing rung log, so any serving-path LLM decision can be replayed/diffed. Cheap now, invaluable when hybrid goes live.
6. **Temperature=0 for finite-label lanes** (ambiguity, triage, failure classification): classification over closed label sets doesn't need sampling diversity; temperature=0 collapses T3 seams toward determinism without losing the LLM. (Reasoning models ignore this — handled by the existing model-aware params.)
7. **When X-09 closes and hybrid flips to 1**: keep the fact-presence gate and `source` drop; add an eval gate (the KDD F1 ladder pattern) as the flip precondition — the infrastructure for both already exists.
8. **Ask-loop services**: keep disabled until the reply-routing lane passes an eval gate at parity with the KDD bar; when enabled, `needs_review` must stay mandatory below the 0.60 act gate.
9. **Name simulations as simulations everywhere**: "frontier panel" and "checker agent" are deterministic heuristic panels. The labels exist but the names don't carry it; a naming pass (`*_heuristic_panel`) would prevent future operators from mistaking them for model-backed services.
10. **RAG**: either mount the router and wire `rag_service` into `identify_niche`, or archive the embeddings path (wire-or-archive ADR discipline already exists) — T5 code that stays unowned will rot.

---

## 6. Verdict

- **Architecture:** sound. Deterministic spine, narrow labeled probabilistic seams, honest degradation, correct gating posture. The T5 posture (hybrid off, vision off, ask-loop off, RAG orphaned) is *deliberate* and documented — that is the right posture until X-09 and the eval-gate preconditions close.
- **Integrity:** six defects, all in the same class — *deterministic code faking probabilism* — none of which the honesty doctrine's existing machinery was applied to. All registered; all small, mechanical fixes.
- **The principle this audit ratifies:** *confidence is data, not decoration.* Every number that looks like a probability must trace to a model output, a calibration, or an explicit rule-contract — never to a hardcoded constant chosen to feel right.

---

## 7. Remediation record (2026-10-22)

**Scope executed:** all six findings fixed and closed (FND-0352…0357, disposition `fixed`), plus the two structural "should/could" items from §5 that were safely in-envelope: sampling forensics (rec 5) and temperature=0 on the finite-label lane (rec 6). Recorded follow-on: FND-0358 (integration.py hardcoded confidences — same defect class, outside this tranche's blast radius) and FND-0359 (see §7.6 — registered during implementation). FND-0360 documents 20 pre-existing full-suite failures on the dirty tree with attribution evidence.

### 7.1 What changed (file-level)

| Finding | File(s) | Change |
|---|---|---|
| FND-0352 | `src/intake/ambiguity_classifier.py`, `src/intake/decision.py` | Rule fallback: `confidence=None` + new `confidence_method` (`model_calibrated`\|`rule_heuristic`) + `fallback_reason` (`model_lane_unconfigured`\|`model_call_failed`\|`empty_input`), all carried through `to_dict()`. Advisory policy in `run_gap_and_decision` is now explicit: flag on calibrated <0.60, on a model verdict with no calibration, and when the configured lane FAILED; a deliberately unconfigured lane (ADR-008 posture) is rule mode by design — provenance recorded, no per-run nag (avoids alert fatigue; the `critical/high/medium` vocabulary has no informational tier). |
| FND-0353 | `src/intake/context_resolver.py`, `src/intake/extractors.py` | Resolver contract narrowed to its documented purpose: `validate_resolver_response(payload, current_candidates)` enforces candidates ⊆ deterministic set (case-insensitive; deterministic casing wins; empty-set forbids names); prompt tightened ("never add a name"); `temperature=0.0` (closed-set classification). Narrowed candidates' fact evidence now carries `[provider:model] disambiguated X → Y`. **In-blast-radius defect fixed:** `final_raw` carried the FND-0309 reprocess-merge note but the bare `dest_raw` was passed to `_make_slot` — the merge provenance the FND-0309 comment promises never reached the slot; now it does. Authority design unchanged (`EXPLICIT_USER` is now true by construction — the resolver can only narrow traveler-written, gazetteer-confirmed names). |
| FND-0354 | `src/agents/recovery_agent.py`, `src/decision/failure_triage.py` | §6.1 verdict: last-mile missing → **completed, not deleted**. Engine now receives `TypesafeJevClient()` (the credential-gated pattern every other Jev lane uses). No key → heuristic unchanged; key → Jev classifies the PII-stripped, delimited failure state (`raw_query` egress guard `typesafe_client.py:293`). The opinion can only move recovery toward escalation, never away. The JEV-path default confidence (0.5 when the model omits it) is documented as a deliberately sub-threshold conservative contract. |
| FND-0355 | `src/suitability/llm_scorer.py`, `tests/test_suitability_tier3.py` | Heuristic fallback: `source="rule"` (closed Literal vocabulary) + `confidence=baseline.confidence` (inherited computed value, not a constant). Two hostile test assertions that pinned `source=="llm"` on the no-client path corrected to `"rule"`. |
| FND-0356 | `src/intake/frontier_orchestrator.py`, `src/intake/orchestration.py`, `src/intake/checker_agent.py` | `FrontierOrchestrationResult` gains `checker_status` (`not_triggered\|skipped_gate_disabled\|skipped_confidence_above_threshold\|verified\|flagged\|failed`) + `checker_confidence_delta`. Orchestration copies the verdict into `decision.rationale["frontier"]` **and** appends `checker_manual_audit_required` (severity high) to `decision.risk_flags`, which phase 4 routes into the operator-facing `strategy.risk_flags`. `confidence_delta` deliberately **parked**: recorded, never applied — a heuristic may not nudge a calibrated number (the original "+0.05 boost" intent died at the confidence-is-data principle). Checker docstring now states its rule-heuristic nature and the model-checker entry contract. |
| FND-0357 | `src/intake/audio_intake.py` | §6.1 verdict: unfinished scaffold preserved; `confidence_score=None` + `transcription_method="supplied_transcript"`; docstring corrected (it never transcribed anything). A future STT provider enters through the same contract with `stt:<provider>` and its own calibration. Lane completion listed as DECIDE (§8). |
| Rec 5 (forensics) | `src/llm/base.py` + all four clients | New canonical `record_llm_call()` in the shared contract module — emits ONE structured line per successful call to logger `llm.calls`: provider, model, requested+effective temperature (`None` when provider controls sampling: reasoning models, Jev), prompt/response **sha256 only** (privacy contract: content never logged; egress guard runs before), char counts, latency. Wired in `openai_client`, `gemini_client`, `local_llm`, and `typesafe_client._post` (one seam covers `decide` + `raw_query`). Also kept on `client.last_call_record` for callers to attach to their own telemetry. **Blast-radius catch:** `local_llm` passed temperature with `do_sample=True` — HF rejects temperature=0 under sampling, so the resolver's temperature=0 would have gone dark on the local rung; temperature≤0 now switches to greedy decoding. |
| Rec 6 (temp=0) | `src/intake/context_resolver.py` | Applied (closed-set classification). The other finite-label lanes (ambiguity, live-triage, failure-triage) run on Jev, which exposes no sampling knob — nothing to set; forensics records `temperature_effective=None` honestly. Hybrid-engine lanes remain OFF (X-09); rec 7 (eval-gated flip) unchanged and pending. |

### 7.2 Review cycles (doctrine Phase 2 — schema/contract change ⇒ 2 cycles)

- **Cycle 1 (logic/data-loss/breaking contracts):** checked every caller of `validate_resolver_response` (all updated; serving path enforces, tests updated); every consumer of `AmbiguityReport.confidence`/`semantic_ambiguity` (orchestration FND-0316 guard reads `action` only; frontend itinerary-checker consumes the *normalizer* `ambiguities` list (`field`/`raw_value`), not the semantic report — `confidence: null` reaches no traveler surface); `decision.risk_flags` append safety (DecisionResult mutable; phase-4 `_extract_risk_flags` dedupes; verified end-to-end by the spine-level test); set_fact list-merge with the longer evidence (verified empirically — FND-0309 test); stale pins on old values (`jev_calibrated_confidence`, `0.96`, fallback `source="llm"`) — zero remain; typesafe forensics records the **sanitized** state (record happens after `_strip_pii_for_egress` inside `_post`); openai `temperature_requested` semantics for reasoning models correct (intent recorded, effective `None`).
- **Cycle 2 (defensive/edges):** disabled-kill-switch paths unchanged (`resolver_candidate_note=""`); `dest_raw` empty → `"not specified"` behavior preserved; JEV answers without `jev_confidence` now correctly flagged (previously silently trusted); retry loop records once on eventual success, never on failures; forensics is best-effort (never raises; `last_call_record` setattr guarded); recovery-agent lazy import has no cycle; MagicMock-spec'd clients tolerate the new `confidence_delta` attribute; feature-gates suite (35/35) re-verified after the risk-flag addition.
- Reviewer-agent dispatch hit a session usage limit; both cycles were executed directly with the checks above recorded as evidence.

### 7.3 Test evidence (Tiers + sensitivity)

- **New:** `tests/test_determinism_audit_remediation.py` — 27 tests, one section per finding, each asserting the invariant the pre-fix code violated (S2: the mutation *is* the old code; explicit S3 mutation test for FND-0352 proves hardcoded 0.85 silences the advisory while `None` raises it). All 27 pass.
- **Blast radius:** 20 modules — 296 passed, 8 skipped (honest Tier-5 live-provider skips): ambiguity, context_resolver, suitability tier3, sim4 destination, sim3 followup wiring, concierge/audio, failure_triage, recovery_agent, llm clients ×4, live_triage, nl_corporate_policy, pa_agentic_remediations, ask_loop, specialty salvage, agent requeue/factory, feature gates (35/35), D6 golden gate, extraction rule gate. Ruff clean on all touched files; module import sweep clean.
- **Full suite:** 855 passed before the 20-failure cutoff. **Attribution:** the identical 20 failures occur with the remediation module excluded (`/tmp/full_suite_2026-10-22.log` vs `/tmp/suite_minus_remediation.log`) — registered as FND-0360 with evidence (pre-existing parallel SIM4-wave state: `pending_booking_data` in `SQLTripStore._to_dict` — whose `_to_dict` the pre-session diff modifies — plus order-dependent `booking_collection_tokens`→`trips` FK violations on the persistent test DB). Not in this tranche's blast radius; not silently skipped.

### 7.4 Behavior changes an operator will notice

1. When the JEV lane is configured but a call fails, runs now carry a medium `low_confidence_semantic_ambiguity` advisory ("model lane failed; rule heuristic served") — previously invisible behind the fake 0.85.
2. When the checker flags a ghost workflow for manual audit, operators now see it: rationale + a high-severity `checker_manual_audit_required` risk flag (previously computed and dropped).
3. Destination-collision facts resolved by the model now carry the resolver's provenance in the slot evidence; a model-inventing destination is rejected and the operator-confirmable `semi_open` stands (previously the invention was stored as an explicit-user fact).
4. `llm.calls` log lines exist per model call (hashes only).

### 7.5 Audit assessment (11-dimension, scoped to this tranche)

Code ✅ (296+27 tests, ruff clean, zero regressions attributable — FND-0360 attribution documented) · Operational ✅ (checker verdict + lane-failure advisories now reach operator surfaces) · UX ✅/🟡 (new advisories are honest noise; the unconfigured-lane nag was deliberately avoided) · Logical consistency ✅ (confidence is now either calibrated or absent, everywhere this tranche reaches) · Commercial ✅ (trust surface: no more fabricated numbers on operator views) · Data integrity ✅ (fact/hypothesis boundary restored for resolver output; merge provenance now actually persisted) · Quality/Reliability ✅ (fallback labeling consistent across all lanes; hostile assertions fixed) · Compliance ✅ (forensics records hashes only; egress guard unchanged and upstream of recording) · Operational readiness ✅ (no deploy steps; additive fields) · Critical path N/A (no schema migration; packet metadata is additive) · **Verdict: code-ready ✅, feature-ready ✅ for the remediation scope, launch-readiness unchanged** (governed by the launch council's open items, not this tranche).

### 7.6 Follow-ups registered during implementation

- **FND-0361** — `src/suitability/integration.py:375,387` hardcodes `confidence=0.85/0.90` on deterministic tier3/tier4 advisory flags in the *serving* suitability path. Same defect class as FND-0352 but a module this tranche does not touch (llm_scorer is deliberately unwired from it); registered, not fixed here — the serving flag confidences are operator-visible and deserve their own calibrated-or-absent pass.
- **FND-0360 → closed superseded** — the 20 pre-existing full-suite failures on the dirty tree (see §7.3) turned out to be already tracked by the parallel `zcode-sim4` session as **FND-0358** (booking GET exposes `booking_data` via `_to_dict`) and **FND-0359** (suite-composition pollution). My row was closed superseded with the independent attribution evidence preserved in the closure event. Owner disposition: sim4's rows.
- **DECIDE (owner)** — the items from §5 that were deliberately NOT executed in this tranche, listed for discussion rather than chosen unilaterally:
  1. **Audio lane (FND-0357 follow-up):** integrate a real STT provider through the now-honest `audio_intake` contract (`stt:<provider>` + calibrated confidence), or formally park the module with a revive trigger.
  2. **RAG wire-or-archive (§5 item 10):** mount `spine_api/routers/rag.py` and pass `rag_service` into `SpecialtyKnowledgeService.identify_niche`, or archive the embeddings path under the existing wire-or-archive ADR discipline.
  3. **Naming pass for simulated panels (§5 item 9):** rename `frontier_orchestrator`/`checker_agent` surfaces (or their badges) so the deterministic-heuristic nature is visible in the name — deliberately not done here because module renames are a wide-blast-radius change touching imports, tests, and docs.
  4. **Hybrid-engine flip (§5 items 7–8):** unchanged — stays gated on X-09 closing, then an eval gate (KDD-ladder pattern) as the flip precondition.

### 7.7 Handoff verdicts

- **Merge:** recommended — additive, tested, zero attributable regressions. (Commit only on owner approval per git safety.)
- **Feature-ready:** yes for the remediation scope.
- **Launch-ready:** unchanged from the 2026-09-29 council verdict; this tranche removes six honesty defects from the operator surface but does not by itself flip any launch gate.
