# Coverage Matrix

**Date:** 2026-04-15  
**Purpose:** Convert the coverage discussion into a working control document that distinguishes what is merely discussed from what is scenario-covered, tested, implemented, and queued for follow-up.

**Planning upgrade:** This document now also carries execution-oriented columns so it can be used as a lightweight build-control artifact, not just a coverage snapshot.

**Related:** `Docs/COVERAGE_ASSESSMENT_2026-04-15.md`

---

## Legend

| Mark | Meaning |
| --- | --- |
| `✅` | Strong / present / materially in place |
| `⚠️` | Partial / fragmented / present but not fully operational |
| `❌` | Missing or not yet represented in a meaningful way |
| `—` | Not applicable or not yet intentionally targeted |

## Column Meanings

- **Documented**: clearly represented in project docs.
- **Scenario-Written**: represented in persona/scenario artifacts or synthetic scenarios.
- **Tested**: explicitly covered by tests, scenario harnesses, or contract checks.
- **Implemented**: meaningfully represented in runtime code / product behavior.
- **Priority**: rough implementation urgency (`P0`, `P1`, `P2`, or `—`).
- **Repo Area / Module**: the most relevant code, docs, or system surface to change.
- **Acceptance Signal**: observable sign that the gap is materially closed.
- **Blocking Dependency**: prerequisite that likely must exist first.
- **Next Action**: the most useful next move, based on current evidence.

---

## 1) Risk Coverage Matrix

| Area | Documented | Scenario-Written | Tested | Implemented | Priority | Repo Area / Module | Acceptance Signal | Blocking Dependency | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Customer-side risk | ✅ | ✅ | ⚠️ | ⚠️ | P0 | `src/intake/*`, `tests/`, `Docs/context/*` | Budget, ambiguity, and document risks change decision outcomes deterministically in tests. | Canonical field semantics + blocker policy clarity | Tighten runtime handling for ambiguity, budget realism, visa/document risk. |
| Vendor-side risk | ✅ | ⚠️ | ❌ | ❌ | P1 | `Docs/`, future supplier-state modules, scenario fixtures | Supplier freshness / availability / execution truth appears in scenario and contract tests. | Supplier truth schema and sourcing policy contract | Add supplier truth / execution-state contracts and related scenarios. |
| Operational risk | ✅ | ⚠️ | ⚠️ | ⚠️ | P0 | `src/intake/decision.py`, `tests/`, `Docs/status/*` | Core state transitions and safety rules are regression-protected. | Stage-aware state machine hardening | Keep hardening deterministic flow, runtime safety, and handoff logic. |
| External risk | ✅ | ✅ | ❌ | ❌ | P1 | scenario docs, lifecycle/disruption policy areas | Disruption scenarios produce explicit escalation or mitigation policies. | Crisis / escalation contract | Add explicit disruption-handling and crisis-oriented policies/tests. |
| SaaS/platform risk | ✅ | ❌ | ⚠️ | ⚠️ | P2 | ops docs, API/service boundaries, ADRs | Platform failure modes have runbook-style responses and observable fallback behavior. | Runtime reliability layer and service monitoring model | Expand beyond general reliability into platform-specific operational runbooks. |
| Security / privacy / compliance | ✅ | ⚠️ | ⚠️ | ⚠️ | P1 | validation layer, policy docs, traveler-safe output tests | Sensitive-field handling and policy boundaries are enforced in tests. | Stronger schema/validation gates | Convert documented policy concerns into stricter runtime and validation gates. |

### Risk Sources

- `Docs/context/RISK_AREA_CATALOG_2026-04-15.md`
- `Docs/RISK_ANALYSIS.md`
- `Docs/context/TRIP_VISA_DOCUMENT_RISK_SCENARIO_2026-04-15.md`
- `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md`

---

## 2) Persona and Stakeholder Coverage Matrix

| Group | Documented | Scenario-Written | Tested | Implemented | Priority | Repo Area / Module | Acceptance Signal | Blocking Dependency | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Agency owner | ✅ | ✅ | ⚠️ | ❌ | P1 | owner-facing frontend specs, commercial policy docs, future dashboards | Owner-specific visibility and review flows exist in tests/specs, not just prose. | Margin + quote-quality logic | Add owner-facing quality / margin / visibility workflows beyond planning core. |
| Senior / solo agent | ✅ | ✅ | ⚠️ | ⚠️ | P0 | intake runtime, prompt policy, lifecycle logic | Faster proceed/follow-up behavior with fewer false blocks in gold scenarios. | Core decision quality improvements | Continue optimizing core planning, memory, and speed-to-decision flows. |
| Junior agent | ✅ | ✅ | ⚠️ | ⚠️ | P1 | question generation, guidance policy, acceptance tests | Guidance outputs reduce unsafe proceed states in junior-agent scenarios. | Stronger blocker and coaching heuristics | Strengthen guardrails, coaching, and mistake-prevention behavior. |
| Individual traveler | ✅ | ✅ | ⚠️ | ⚠️ | P0 | traveler-safe prompt/output boundary, lifecycle communication layer | Traveler-facing outputs pass boundary tests and avoid internal leakage. | Boundary enforcement and proposal controls | Tighten traveler-safe outputs and downstream reassurance flows. |
| Family decision maker | ✅ | ✅ | ⚠️ | ❌ | P1 | packet model, scenario fixtures, group-state logic | Per-subgroup readiness and constraint reconciliation appear in tests. | Subgroup data model | Add multi-party state, per-subgroup readiness, and consensus support. |
| Supplier / partner contact | ⚠️ | ⚠️ | ❌ | ❌ | P2 | supplier memory / sourcing layers, future ops modules | Supplier state is modeled as structured truth, not free text. | Supplier schema and sourcing engine | Model supplier truth, confirmation freshness, and escalation states explicitly. |
| Concierge / service ops | ⚠️ | ❌ | ❌ | ❌ | P2 | future in-trip ops layer | Clear service/escalation workflow exists in runtime or formal spec. | In-trip support scope lock | Add service/escalation workflows if they remain in scope. |
| Finance / refund / collections roles | ⚠️ | ❌ | ❌ | ❌ | P2 | cancellation/refund logic, commercial ops docs | Refund and payment-state rules are represented in scenarios/policies. | Cancellation policy engine | Add refund/cancellation/commercial ops coverage later. |
| Compliance / legal review actors | ⚠️ | ❌ | ❌ | ❌ | P2 | policy docs, privacy/compliance controls | Legal/compliance checkpoints are attached to specific workflow stages. | Operational control-point design | Convert legal/privacy concerns into operational control points. |
| Host-agency / multi-location admin | ⚠️ | ⚠️ | ❌ | ❌ | P2 | GTM docs, org model specs, future admin surfaces | Host/multi-location workflows are explicitly specified and prioritized. | Segment commitment in GTM | Expand market/ops model if host-agency wedge becomes active. |

### Persona and Stakeholder Sources

- `Docs/UX_JOBS_TO_BE_DONE.md`
- `Docs/personas_scenarios/STAKEHOLDER_MAP.md`
- `Docs/personas_scenarios/INDEX.md`

---

## 3) Scenario Family Coverage Matrix

| Scenario Family | Documented | Scenario-Written | Tested | Implemented | Priority | Repo Area / Module | Acceptance Signal | Blocking Dependency | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Core discovery / intake | ✅ | ✅ | ✅ | ✅ | P0 | `src/intake/*`, `tests/` | Existing gold path remains green as new capabilities are added. | None — this is baseline | Keep as baseline regression path. |
| Ambiguity / contradiction | ✅ | ✅ | ⚠️ | ⚠️ | P0 | NB02 decision logic, contradiction tests | Ambiguous values no longer satisfy hard blockers in decision tests. | Canonical ambiguity rules | Move ambiguity handling earlier into NB02 decision logic. |
| Budget realism | ✅ | ✅ | ⚠️ | ⚠️ | P0 | budget decomposition / decision logic / fixtures | Unrealistic budgets trigger deterministic budget-feasibility outcomes. | Cost assumptions / realism model | Add explicit feasibility math and stretch parsing. |
| Visa / document readiness | ✅ | ✅ | ⚠️ | ⚠️ | P0 | extractors, packet model, decision blockers | Passport/visa readiness controls proceed states in booking-stage tests. | Canonical document fields | Promote visa/passport checks into canonical hard-blocker logic. |
| Transfer / route complexity | ✅ | ✅ | ⚠️ | ⚠️ | P1 | route heuristics, scenario fixtures | High-friction routing raises risk / follow-up signals consistently. | Better trip-friction feature extraction | Expand route-friction heuristics into stronger runtime checks. |
| Activity / pacing suitability | ✅ | ✅ | ⚠️ | ⚠️ | P1 | suitability heuristics, composition-aware prompts | Senior/child pacing mismatches surface in decision or prompt policy tests. | Composition-sensitive state extraction | Strengthen suitability reasoning for composition-sensitive itineraries. |
| Multi-party / family coordination | ✅ | ✅ | ❌ | ❌ | P1 | packet model, decision logic, group-state UI/spec | Subgroup-level blockers and readiness are represented in tests. | `sub_groups` / multi-party state model | Add subgroup data structures and readiness logic. |
| Repeat customer memory | ✅ | ✅ | ❌ | ❌ | P1 | packet model, lifecycle module, memory integration | Known customer facts reduce unnecessary re-asking in tests. | Customer identity + memory contract | Add customer identity + history retrieval contract. |
| Emergency / disruption handling | ✅ | ✅ | ❌ | ❌ | P1 | decision outputs, lifecycle/escalation policy | Emergency scenarios return explicit protocol / escalation outputs. | Crisis-state contract | Add formal emergency protocol outputs and crisis-state handling. |
| Scope creep / ghosting / lifecycle | ✅ | ✅ | ⚠️ | ⚠️ | P1 | lifecycle model, policy outputs, tests | Lifecycle signals change policy outputs deterministically. | Lifecycle runtime integration | Integrate lifecycle model more deeply into runtime flows. |
| Cancellation / refund handling | ⚠️ | ✅ | ❌ | ❌ | P2 | future cancellation policy engine | Cancellation scenarios produce policy-guided next-step outputs. | Post-booking policy layer | Add policy engine and scenario-driven rules later. |
| Post-trip review / referral loops | ⚠️ | ✅ | ❌ | ❌ | P2 | lifecycle/post-trip modules, CRM logic | Review/referral events are modeled and actionable in runtime. | Stable post-trip lifecycle state | Add post-trip operational layer after core planning path matures. |

### Scenario Family Sources

- `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md`
- `Docs/context/TRIP_FEASIBILITY_SCENARIO_2026-04-15.md`
- `Docs/context/TRIP_BUDGET_REALITY_SCENARIO_2026-04-15.md`
- `Docs/context/TRIP_TRANSFER_COMPLEXITY_SCENARIO_2026-04-15.md`
- `Docs/context/TRIP_ACTIVITY_PACING_SCENARIO_2026-04-15.md`

---

## 4) Lifecycle Stage Coverage Matrix

| Lifecycle Stage | Documented | Scenario-Written | Tested | Implemented | Priority | Repo Area / Module | Acceptance Signal | Blocking Dependency | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lead capture / intake | ✅ | ✅ | ✅ | ✅ | P0 | intake pipeline, parsers, normalization tests | Stable deterministic extraction/regression behavior remains intact. | None | Keep stable and regression-protected. |
| Clarification / follow-up | ✅ | ✅ | ✅ | ✅ | P0 | blocker policy, question generation, tests | Follow-up behavior is precise, finite, and stage-aware in tests. | State-machine clarity | Continue tuning blocker logic and follow-up precision. |
| Proposal / internal draft | ✅ | ✅ | ⚠️ | ⚠️ | P0 | prompt composer, traveler-safe boundary, acceptance tests | Internal vs traveler-safe outputs are clearly separated and test-enforced. | Boundary enforcement | Improve traveler-safe boundary and proposal quality controls. |
| Booking readiness | ✅ | ✅ | ⚠️ | ⚠️ | P0 | document readiness, commercial gates, decision policy | Booking-stage proceed states require canonical readiness checks. | Canonical blockers + document fields | Tighten passport/visa/doc/commercial gating before proceed states. |
| In-trip support / disruption | ⚠️ | ✅ | ❌ | ❌ | P2 | future ops/disruption layer | Disruption cases route to explicit support/escalation outputs. | Booking-state safety and escalation contract | Add crisis and escalation contracts only after booking-state safety is stronger. |
| Post-booking reassurance | ⚠️ | ✅ | ❌ | ❌ | P2 | lifecycle communications / future UX surfaces | Traveler reassurance and status updates are represented beyond static docs. | Post-booking workflow design | Add structured reassurance / status communications later. |
| Post-trip review / retention | ✅ | ✅ | ⚠️ | ⚠️ | P1 | lifecycle module, retention policy outputs | Retention / review / churn signals alter follow-up policy deterministically. | Stable lifecycle state model | Deepen lifecycle instrumentation after core state machine stabilizes. |
| Reactivation / repeat customer memory | ✅ | ✅ | ❌ | ❌ | P1 | memory integration, lifecycle model, packet fields | Repeat customers reuse prior context in tests without unsafe assumptions. | Customer identity and memory retrieval | Add durable customer memory and reuse of known facts/preferences. |

### Lifecycle Sources

- `Docs/LEAD_LIFECYCLE_AND_RETENTION.md`
- `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md`
- `Docs/PM_EXECUTION_BLUEPRINT_2026-04-14.md`

---

## 5) Market Segment Coverage Matrix

| Market Segment / Lens | Documented | Scenario-Written | Tested | Implemented | Priority | Repo Area / Module | Acceptance Signal | Blocking Dependency | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| India-first small agency wedge | ✅ | ✅ | ⚠️ | ⚠️ | P0 | core product docs, current runtime, build queue | Core wedge scenarios continue to drive implementation decisions. | None — current primary wedge | Keep as the primary execution wedge. |
| Solo / micro agencies | ✅ | ✅ | ⚠️ | ⚠️ | P0 | current intake/lifecycle/product surfaces | Faster single-operator outcomes are visible in scenarios and UI behavior. | Core runtime hardening | Continue optimizing for speed, memory, and low-process operation. |
| Small / medium team agencies | ✅ | ✅ | ⚠️ | ❌ | P1 | owner/team specs, future frontend/admin surfaces | Owner/team workflows move from doc-only to formal product contracts. | Margin + oversight + training primitives | Add owner visibility, training, and coordination layers gradually. |
| Leisure / custom travel | ✅ | ✅ | ⚠️ | ⚠️ | P0 | current planning runtime and scenario bank | Leisure/custom cases remain the strongest validated segment. | None — current core scope | Remains core current scope. |
| Host-agency model | ✅ | ⚠️ | ❌ | ❌ | P2 | GTM docs, org model, pricing docs | Host-agency support gets explicit product and GTM acceptance criteria. | Segment prioritization decision | Expand only if GTM priorities move there. |
| Corporate travel | ⚠️ | ❌ | ❌ | ❌ | P2 | future segment research docs | Separate segment doc and scenarios exist before support is claimed. | Segment research and scope decision | Document separately before claiming support. |
| MICE / events / weddings | ⚠️ | ❌ | ❌ | ❌ | P2 | future vertical docs/scenarios | Vertical-specific constraints are explicitly modeled. | Expansion strategy choice | Add only if chosen as an expansion vertical. |
| Student / education travel | ⚠️ | ❌ | ❌ | ❌ | P2 | future research docs | Distinct scenarios and constraints are documented. | Segment research | Treat as future segment research. |
| Religious / pilgrimage travel | ⚠️ | ❌ | ❌ | ❌ | P2 | India-market depth research | High-relevance India-specific constraints are documented if pursued. | India market deepening decision | Add if needed for India-market depth. |
| Inbound vs outbound regional differences | ⚠️ | ❌ | ❌ | ❌ | P2 | geography / policy / operations docs | Region-specific rules exist as structured constraints, not assumptions. | Geography/policy model maturity | Add region-specific operational constraints later. |

### Market Sources

- `Docs/COMPETITIVE_LANDSCAPE.md`
- `Docs/PRICING_AND_CUSTOMER_ACQUISITION.md`
- `Docs/PILOT_AND_CUSTOMER_DISCOVERY_STRATEGY.md`
- `Docs/GTM_AND_DATA_NETWORK_EFFECTS.md`
- `Docs/PLATFORM_LED_VS_WHITE_LABEL.md`

---

## 6) Commercial and Operating Logic Matrix

| Commercial / Ops Area | Documented | Scenario-Written | Tested | Implemented | Priority | Repo Area / Module | Acceptance Signal | Blocking Dependency | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sourcing hierarchy | ✅ | ⚠️ | ❌ | ❌ | P1 | decision policy, supplier memory vision, sourcing docs | Sourcing path affects runtime decision outputs or proposal logic. | Supplier truth + commercial policy | Convert from strategy concept into runtime decision inputs. |
| Margin protection | ✅ | ✅ | ❌ | ❌ | P1 | commercial policy layer, owner workflows, tests | Margin-risk cases trigger different policy outputs and review paths. | Budget realism + owner review path | Add margin-risk logic and owner review paths. |
| Budget efficiency / audit mode | ✅ | ⚠️ | ❌ | ❌ | P2 | audit engine docs, future comparison logic | Audit mode compares itinerary value against structured assumptions. | Deterministic budget realism | Treat as later wedge after budget realism is deterministic. |
| Quote quality / completeness validation | ✅ | ✅ | ❌ | ❌ | P1 | acceptance tests, proposal/quote policy | Quote completeness becomes a measurable acceptance gate. | Proposal-stage contract and traveler-safe boundary | Add explicit quote-quality acceptance checks. |
| Preferred supplier logic | ✅ | ⚠️ | ❌ | ❌ | P2 | supplier schema, sourcing logic | Preferred supplier availability changes recommendation/order of operations. | Supplier truth schema | Add supplier truth schema and commercial routing later. |
| Change-order / revision economics | ⚠️ | ✅ | ❌ | ❌ | P1 | revision tracking, lifecycle/commercial policy | Repeated changes affect follow-up, boundary, or pricing policy. | Revision/event tracking | Add revision counting and effort-sensitive policy rules. |
| Lead qualification / ghosting / churn | ✅ | ✅ | ⚠️ | ⚠️ | P1 | lifecycle runtime, policy outputs, tests | Lifecycle states alter commercial interventions in regression tests. | Stable lifecycle integration | Continue integrating lifecycle signals into core flow. |

### Commercial and Operating Logic Sources

- `Docs/Sourcing_And_Decision_Policy.md`
- `Docs/PRICING_AND_CUSTOMER_ACQUISITION.md`
- `Docs/LEAD_LIFECYCLE_AND_RETENTION.md`
- `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md`

---

## 7) Highest-Priority Coverage Closure List

These are the items where the gap between documentation and implementation matters most.

### P0 — close first

1. ambiguity handling at decision time  
2. urgency-aware decision behavior  
3. budget feasibility enforcement  
4. visa / passport readiness as canonical blockers  
5. traveler-safe boundary enforcement

### P1 — close next

1. repeat customer memory  
2. multi-party / subgroup handling  
3. commercial / margin / sourcing logic  
4. quote quality / cost completeness  
5. document progress and booking readiness tracking

### P2 — later expansion

1. audit mode / wasted-spend comparison  
2. referral / influencer / post-trip loops  
3. seasonal rush / allocation logic  
4. broader market-segment specialization

---

## 8) Practical Read of the Matrix

The matrix should be read with one important rule:

> `Documented =/= Implemented`

This repo now has enough coverage to reason well and prioritize intelligently. It does **not** yet have enough runtime closure to claim that every major angle is handled end-to-end.

That is acceptable for the current stage, as long as planning and execution continue to use this distinction explicitly.
