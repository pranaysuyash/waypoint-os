# Random Document Audit — Visa & Immigration Deep Dive (2026-09-09)

**Mode**: `random_probe` · **Seed**: 20260909 · **Pool**: 3,283 eligible docs (hash `51673e4c83bd4c51c8051e932a52f9b15b6b7a0eb80711620c3ba87c0f7d96e5`), index 1516
**Selected document**: `Docs/personas_scenarios/AREA_DEEP_DIVE_VISA_IMMIGRATION.md` (56 lines, April-2026 exploration-era proposal)
**Revision**: `cfdf19e` @ `master` (dirty tree: parallel agency-marketplace/execution-event-chain work — treated as parallel-owned, untouched)
**Persona council**: canonical repo `/Users/pranay/Desktop/Understanding_Personas_sept6` (resolver: high confidence). Lead PER-0443 (Agentic Travel Systems Architect); seats PER-0443/0463 (Evidence & Verification), PER-0688 (AI Evaluation Engineer), PER-0468 (Missing-Workflow Red Team), PER-0100 (Launch Readiness); skeptic pass run separately.
**Execution**: this audit's IMPLEMENT items were executed the same session on owner instruction ("do all"), with the findings below. Evidence tiers noted per finding; baseline = full suite 4,161 passed / 0 new failures (2 pre-existing failures in `test_booking_documents.py` + `test_call_capture_e2e.py` attributed to the parallel agent's in-flight `execution_event_service.py` work — MagicMock/async mismatch inside their dirty file).

---

## 1. Document-to-reality verdict

The selected doc is a **partially-landed April proposal** — same pattern as the itinerary-checker wedge: capability claims diverged from implementation, then stalled without formal closure.

| Doc claim | Reality (2026-09-09) | Status |
|---|---|---|
| Live API (Sherpa/VisaCentral) nationality × destination | Hardcoded 7-pair registry + conservative fallback; no external data source in code | Was stale → now honestly badged (VA-02/03) |
| Invitation-letter request/tracking | `DocumentType.INVITATION_LETTER` enum never added to any checklist; all other "invitation" code = workspace invite codes | Missing (VD-03) |
| Courier tracking / embassy appointment manifest | `VisaWorkflowEngine` complete-looking but called only by tests — orphaned engine | Orphaned (VD-01) |
| Early entry-blocker disclosure (health/criminal) | `REGULATORY_HEALTH_VACCINATION` category has tier handling but zero producers — vacuous | Marked dormant (VA-05) |
| VISA-001..006 scenarios | Zero visa scenarios in eval corpus; IDs only in docs | First seeds landed (VA-04/VE-03) |
| (adjacent) visa timeline risk | `rule_visa_timeline_risk` genuinely wired into hybrid engine + D6 lane | Working; now rule-tested |

**Systemic finding**: `Docs/personas_scenarios/` = **415 proposal docs** with no graduation path into the corpus. → protocol proposed in `Docs/exploration/SCENARIO_LIBRARY_GRADUATION_PROTOCOL_2026-09-09.md` (VE-04).

## 2. Findings register (VA/VE/VD)

### IMPLEMENT — executed 2026-09-09 (all verified, tests green)

| ID | Finding | Fix | Evidence |
|---|---|---|---|
| VA-01 (P1) | `VisaCheckRequest.passport_country` defaulted to `"US"` — residual US-nationality assumption; AT-11's abstain fix covered only the trip endpoint | Default removed; field required (validation error on omission) | `spine_api/services/visa_radar.py`; test `test_passport_country_is_required` |
| VA-02 (P2) | "Real-Time Visa Radar" / "official destination visa entry protocols" naming overclaimed a hardcoded sample registry | HEURISTIC SCOPE docstrings on service + router; endpoint docstring de-claimed | `spine_api/services/visa_radar.py`, `spine_api/routers/visa_radar.py` |
| VA-03 (P2) | Unknown passport×destination pairs silently fell back to conservative `requires_visa=True, E_VISA` with no signal | `registry_match: bool` added to `VisaCheckResult` (False = fallback heuristic) | service + tests `test_unknown_pair_is_flagged_as_heuristic` / `test_known_pair_is_flagged_as_registry_match` |
| VA-04 (P2) | Zero visa scenarios in the eval corpus despite three visa engines in the codebase | **SC-960 / SC-961** fixtures seeded, expectations frozen from live pipeline, wired into `tests/test_visa_scenario_seeds.py` (no orphan fixtures) | `data/fixtures/scenarios/SC-96[01]_*.json` |
| VA-05 (P3) | `REGULATORY_HEALTH_VACCINATION` vacuous (no producer) | DORMANT comment on the enum; producer remains a future lane | `src/schemas/constraints.py` |
| VA-06 (P1, discovered during execution) | **Visa extractor negation inversion**: "no visa required" matched the `"required"` substring → classified required/not_applied; "no visas yet" matched `"no visa"` → classified not_required. Both directions wrong | Negation-aware pattern ordering (not_required forms → approved → not_applied forms → unknown) | `src/intake/extractors.py` `_extract_passport_visa`; 6 parametrized pipeline-level regression tests |
| VA-07 (P2, discovered during execution) | **"No" destination leak**: "No visas yet" → `destination_candidates=['Japan','No']` — "No" is a real GeoNames city so geography validation can't filter it; blocklist had "not" but not "no" | `"no"` added to the destination blocklist | same extractor; regression in seed test |

### EXPLORE — researched + documented 2026-09-09

| ID | Item | Artifact |
|---|---|---|
| VE-01 | Visa data-source landscape (Sherpa/Timatic/iVisa/gov portals) | `Docs/exploration/VISA_DATA_SOURCE_LANDSCAPE_2026-09-09.md` (web-researched, source-cited; supersedes `frontend/docs/VISA_01/02_*.md` question lists) |
| VE-02 | Transit-visa inference design (blocked on VD-02; no layover extraction exists) | `Docs/exploration/VISA_TRANSIT_INFERENCE_DESIGN_2026-09-09.md` |
| VE-04 | Scenario-library graduation protocol (415 docs, no triage path) | `Docs/exploration/SCENARIO_LIBRARY_GRADUATION_PROTOCOL_2026-09-09.md` — **owner decision requested** |
| VE-05 | Passport/identity PII flow audit (real posture vs the ZK-vault aspiration) | `Docs/exploration/PASSPORT_PII_FLOW_AUDIT_2026-09-09.md` |

### DECIDE — registered, owner-gated

| ID | Decision | Default leaning |
|---|---|---|
| VD-01 | `visa_workflow.py` orphan: wire into workbench/P3 surface or badge PREVIEW_ONLY in the engine inventory | Badge now; wiring deferred |
| VD-02 | Live visa data source (core claim of the audited doc) | Defer — off marketplace-pilot critical path; VE-01 informs when revisited |
| VD-03 | Invitation-letter workflow | Defer — only if P3 fulfillment lane revives |
| VD-04 | Courier/embassy-appointment manifest | Defer — depends on VD-01 |

### Rejected (council, pre-launch filter: better + money)

ZK identity-vault implementation · courier logistics · e-visa typo-correction flow · reciprocity-fee cash alerting · in-house transit-rules registry.

## 3. Council rulings (condensed)

- **PER-0443 (Lead)**: the visa domain has three disconnected layers (wired-but-shallow timeline rule, mounted-but-static radar, orphaned workflow engine). The architecture question is the compliance layer's contract (deterministic rules vs external data vs abstain), not feature-building. Not on the current critical path.
- **PER-0463**: the honesty surface IS on the critical path — "Real-Time"/"official protocols" overclaims are the same defect family as PA-10 fake-metrics. → executed as VA-01/02/03.
- **PER-0688**: strongest actionable finding = corpus gap; cheapest seeds are visa-timeline scenarios since `visa_status` extraction exists at booking stage. → executed as VA-04.
- **PER-0468**: `visa_workflow.py` is a complete-looking engine nothing calls; INVITATION_LETTER enum documents intent never wired. → VD-01.
- **PER-0100**: do not start Sherpa integration / identity vault / courier work now; only honesty fixes + corpus seeds qualify. → respected; VD-02..04 registered, not built.
- **Skeptic**: checked implementation-under-other-names (corpus IDs `trip_alpha_*`/`ACAD-*`/`REPAT-*` — no visa; no env-flagged API config; no frontend consumption of the radar — confirmed via negative search).

## 4. Review cycles (schema/contract change → 2 cycles per doctrine)

**Cycle 1 (feature-dev:code-reviewer, full diff)** — 3 findings, all fixed same pass:
- **P1**: VA-07 fix only covered the capitalized-regex pass; "No" (a GeoNames alternate name of Ho, Ghana) could still leak via the verbless and verb-gated passes ("No trip booked yet" → resolved destination "No"). Fix: `"no"`/`"not"` added to module-level `_STOP_WORDS` — closes every pass via `_is_valid_destination_candidate`; 3 new cross-pass regression tests.
- **P1**: "visa pending" was classified `not_applied`, which fires the **critical** `visa_not_applied` booking blocker (`src/intake/decision.py:1295`) — a pending-with-consulate traveler has applied. Fix: `pending` is now its own status (the decision engine keys the critical blocker on `not_applied` exactly; `visa_timeline` already handled `pending`).
- **P2**: negated visa-free phrases ("don't have visa-free transit") inverted to `not_required` — confident wrong data. Fix: explicit negation pre-check regex → `required/not_applied`.
- Reviewer verdict on the rest: sound per file (VA-01 callers all verified; VA-03 computed after normalization; fixtures schema-conformant; seed tests real-pipeline, no mocks).

**Cycle 2 (verification pass)** — all `visa_status` consumers re-checked for the new `pending` value: `override_learning` (flag-keyed), `additional_rules` (presence-keyed), `cache_key` (requirement-keyed), `visa_timeline` (explicitly handles pending), `decision.py` critical blocker (`not_applied`-exact). No consumer breaks; semantics correct. Reviewer's P3 note accepted as-is: "no visa necessary" now abstains to `unknown` instead of accidentally-correct `not_required` — conservative direction, consistent with the abstain doctrine.

## 5. Verification record (post-review-fixes final state)

| Check | Result |
|---|---|
| Seed + radar + rule tests | 27/27 pass (`tests/test_visa_scenario_seeds.py` + `tests/test_visa_radar.py`) |
| Extraction/destination blast radius (all `ExtractionPipeline`/`destination_candidates`/`_STOP_WORDS` touching tests) | 1,198/1,198 pass |
| Full suite (excluding 2 parallel-owned failure files) | 4,180+ passed; **0 failures attributable to this audit** |
| Known parallel-attributed failures (NOT this audit) | `test_booking_documents.py` + `test_call_capture_e2e.py` (parallel agent's in-flight `execution_event_service.py` mock/async mismatch); `test_server_route_parity` + `test_server_openapi_path_parity` (parallel agent's 3 new `/api/public-checker/*` routes, snapshots not yet regenerated by them); 8 order/contention transients that pass on rerun |
| Ruff on changed files | clean |
| mypy (`visa_radar.py`, in curated scope) | clean |

## 7. Open questions for the owner

1. **VE-04**: ratify the scenario-graduation banner protocol (opportunistic cadence) vs bulk triage vs archive-only?
2. **VD-01**: badge `visa_workflow.py` PREVIEW_ONLY now (recommended) or leave until the engine inventory pass?
3. **VE-01** research: confirm whether the data-source decision (VD-02) should be revisited after the marketplace pilot gate, or parked longer.

## 8. Files touched (this audit's execution pass)

- `spine_api/services/visa_radar.py` — VA-01/02/03
- `spine_api/routers/visa_radar.py` — VA-02
- `src/intake/extractors.py` — VA-06 (visa negation), VA-07 ("no" blocklist)
- `src/schemas/constraints.py` — VA-05 dormancy comment
- `data/fixtures/scenarios/SC-960_visa_timeline_japan_business.json` — new
- `data/fixtures/scenarios/SC-961_visa_digital_nomad_portugal.json` — new
- `tests/test_visa_scenario_seeds.py` — new (17 tests)
- `tests/test_visa_radar.py` — +3 tests
- `Docs/exploration/VISA_TRANSIT_INFERENCE_DESIGN_2026-09-09.md` — new (VE-02)
- `Docs/exploration/SCENARIO_LIBRARY_GRADUATION_PROTOCOL_2026-09-09.md` — new (VE-04)
- `Docs/exploration/PASSPORT_PII_FLOW_AUDIT_2026-09-09.md` — new (VE-05)
- This report (canonical store for VA/VE/VD rows)
- `Docs/exploration/VISA_DATA_SOURCE_LANDSCAPE_2026-09-09.md` — new (VE-01)
- `Docs/review/OPEN_WORK_ROADMAP_2026-09-08.md` — additive audit addendum appended

Related prior findings (deduped against): F-14 perishable sweep (visas as dated inventory), EX-14 TemporalObligation (visa deadlines as obligations), AT-11 (abstain doctrine — extended by VA-01), DRIFT-2026-09-06 unwired-engines list (`visa_workflow.py` joins it via VD-01).
