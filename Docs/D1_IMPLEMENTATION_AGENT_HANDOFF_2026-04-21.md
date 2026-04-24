# D1 Implementation Agent Handoff — Real Upgrade, Not Cosmetic

**Date**: 2026-04-21  
**Scope**: D1 Autonomy Gradient implementation plan from current partial state to a real ADR-aligned foundation  
**Reviewer mode**: Evidence-first handoff for implementation agent

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

---

## A. Review Verdict

**Verdict:** **B foundation, architecture upgrade required.**

D1 is not missing; it already has a working threshold-based precursor. But it is still architecturally incomplete and currently implemented in a way that conflates NB02 judgment with the post-judgment autonomy gate. The next implementation pass must be a real upgrade that preserves the raw system verdict, introduces a first-class autonomy outcome, and prepares the owner settings / review path without prematurely jumping to adaptive autonomy.

---

## B. What Is Verified

### Verified implemented

- The D1 ADR is explicitly defined in [Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md](file:///Users/pranay/Projects/travel_agency_agent/Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md).
- A precursor `AgencyAutonomyPolicy` already exists in [src/intake/config/agency_settings.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py).
- The current autonomy gate is already enforced in [src/intake/gates.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/gates.py).
- The gate is already executed in orchestration in [src/intake/orchestration.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py).
- `DecisionResult` already has a structured confidence scorecard in [src/intake/decision.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/decision.py).
- `AgencySettingsStore` already persists settings in the current file-backed model in [src/intake/config/agency_settings.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py).
- The API server already loads agency settings before running the pipeline in [spine_api/server.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/server.py#L335-L342).

### Verified partially implemented

- Current policy only supports confidence thresholds and two booleans; it does **not** implement the ADR’s `approval_gates`, `mode_overrides`, `auto/review/block`, or `auto_proceed_with_warnings` shape.
- Current orchestration mutates `decision.decision_state` after the gate, which means the raw NB02 verdict is not preserved as a first-class concept.
- Current frontend has placeholder settings/read APIs in [frontend/src/lib/governance-api.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/governance-api.ts#L243-L259), but no real D1 settings contract behind them.
- Current frontend workbench settings panel in [frontend/src/app/workbench/SettingsPanel.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/SettingsPanel.tsx) is operational-debug oriented, not agency-autonomy-policy oriented.

### Claimed but unverified / not implemented

- No canonical autonomy settings API route exists in `spine_api/server.py`.
- No owner-facing autonomy settings UI exists.
- No explicit override event capture loop for D1 exists yet.
- No adaptive customer+trip classification exists yet.

### Fresh evidence

Targeted verification command run successfully:

```bash
uv run pytest tests/test_settings_behavioral.py tests/test_nb02_v02.py -q
```

Result:

- **25 passed in 0.49s**

This verifies the current settings behavior and core decision-state logic are stable enough to upgrade rather than replace.

---

## C. Gaps To Close Next

### 1. Raw system verdict is not preserved after the autonomy gate

**Risk:** high

Current orchestration downgrades or escalates by mutating `decision.decision_state` directly in [src/intake/orchestration.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py#L144-L159).

Why this matters:

- The D1 ADR says autonomy is a layer **on top of** NB02 judgment, not part of NB02 itself.
- D5 override learning needs a clean distinction between:
  - what the system originally concluded
  - what policy allowed
  - what the human overrode
- D2 consumer/agency presentation split will also need the raw judgment separate from the presentation/approval outcome.

If the implementer keeps rewriting `decision_state` in place, D1 will remain architecturally muddy even if new fields are added.

### 2. `AgencyAutonomyPolicy` is still the wrong shape

**Risk:** high

The ADR contract in [Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md](file:///Users/pranay/Projects/travel_agency_agent/Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md#L52-L79) is fundamentally different from the current threshold-only dataclass in [src/intake/config/agency_settings.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py#L12-L18).

The missing contract is not cosmetic. It is the core of D1.

### 3. No canonical autonomy outcome object exists

**Risk:** high

The repo needs a first-class representation of the result of policy evaluation. Right now `GateResult` exists, but it is too generic and does not preserve the decision-state-specific autonomy semantics the rest of the system will need.

At minimum, the system needs to know for each run:

- raw NB02 verdict
- effective gate action
- approval requirement
- whether the outcome is `auto`, `review`, or `block`
- which rule produced that result
- whether the safety invariant forced the block

### 4. No real owner-configurable API/UI path for D1 exists

**Risk:** medium

Current file-backed settings are usable for backend plumbing, but there is no canonical route or UI that lets the owner inspect and change autonomy policy.

The frontend already has misleading placeholder approval APIs and types in [frontend/src/lib/governance-api.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/governance-api.ts#L243-L259) and [frontend/src/types/governance.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/types/governance.ts#L317-L326), but they model value/risk thresholds, not the D1 per-`decision_state` approval policy.

If the implementer ignores this, D1 will remain backend-only and operationally incomplete.

### 5. `spine_api` settings binding is still single-agency and hardcoded

**Risk:** medium

[spine_api/server.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/server.py#L335-L342) currently loads `AgencySettingsStore.load("waypoint-hq")` directly.

This is acceptable for the current single-tenant state, but the implementer should not deepen that assumption. D1 should be implemented in a way that makes later request/auth-based agency resolution straightforward.

### 6. Adaptive autonomy is still intentionally deferred

**Risk:** low if deferred properly, high if attempted prematurely

The ADR is explicit that customer+trip classification is a later layer gated on pilot data. That means the implementer should prepare interfaces and telemetry hooks, but should **not** try to solve adaptive autonomy now.

---

## D. Architecture Guardrails For The Implementer

These are the non-negotiable D1 implementation rules.

### Guardrail 1: Do not treat D1 as "just thresholds"

The threshold logic is a useful precursor, not the finished policy model.

### Guardrail 2: Preserve the raw NB02 judgment

The autonomy layer must not destroy the original `decision_state`.

Long-term D1/D5/D2 all get worse if the system cannot answer:

- What did NB02 originally decide?
- What did agency policy allow?
- What did the human ultimately do?

### Guardrail 3: Autonomy belongs at the NB02/NB03 boundary

Do not move approval policy deeper into [src/intake/decision.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/decision.py). NB02 should keep producing the underlying judgment.

### Guardrail 4: `STOP_NEEDS_REVIEW` must be an unbreakable invariant

No settings update, no mode override, and no threshold logic may allow this to become `auto`.

### Guardrail 5: Build for D5 and D2 even if they are not implemented now

D1 should emit structured outputs that future D5 override learning and D2 presentation split can consume.

### Guardrail 6: Use one canonical settings route/resource

Do not leave placeholder approval settings and a second autonomy settings endpoint drifting in parallel.

If the implementer chooses to reuse `/api/settings/approvals`, that route must be upgraded to the D1 contract and the old threshold type must be retired.

If the implementer chooses `/api/settings/autonomy`, then the old placeholder approvals route/client must be replaced in the same change. Do not keep both alive as competing sources of truth.

---

## E. Task Package For Implementation Agent

The tasks below are atomic enough to execute independently, but together they make D1 real.

### Task 1 — Upgrade `AgencyAutonomyPolicy` to the ADR shape with compatibility loading

**Objective**

Replace the threshold-only policy model with an ADR-aligned policy contract while preserving compatibility with existing saved JSON settings and existing callers.

**Scope In**

- Add ADR-native fields to `AgencyAutonomyPolicy`
- keep threshold fields only as a compatibility layer if still needed internally
- implement safe defaults matching the ADR
- validate the `STOP_NEEDS_REVIEW -> block` invariant at load/save time
- make old JSON files load without crashing

**Scope Out**

- DB-backed settings storage
- adaptive autonomy
- per-agent or per-trip policy branching

**Expected Files To Edit**

- [src/intake/config/agency_settings.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/config/agency_settings.py)
- [tests/test_agency_settings.py](file:///Users/pranay/Projects/travel_agency_agent/tests/test_agency_settings.py)
- [tests/test_settings_behavioral.py](file:///Users/pranay/Projects/travel_agency_agent/tests/test_settings_behavioral.py)

**Acceptance Criteria**

- `AgencyAutonomyPolicy` includes at least:
  - `approval_gates`
  - `mode_overrides`
  - `auto_proceed_with_warnings`
  - `learn_from_overrides`
- Default gates match the ADR.
- `STOP_NEEDS_REVIEW` always loads/saves as `block` even if invalid input tries to override it.
- Existing saved settings files from the old shape still load successfully.
- Existing brand tone and margin settings still work.

**Verification Commands**

```bash
uv run pytest tests/test_agency_settings.py tests/test_settings_behavioral.py -q
```

**Non-Goals**

- No UI work here
- No approval queue yet

---

### Task 2 — Introduce a first-class autonomy outcome model and stop mutating away the raw system verdict

**Objective**

Refactor the gate/orchestration path so the system preserves the raw NB02 decision and separately records the autonomy gate outcome that determines what NB03 may do.

**Scope In**

- Add a D1-specific autonomy outcome object or equivalent structured fields
- preserve the raw decision state from [src/intake/decision.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/decision.py)
- compute the effective gate action (`auto` / `review` / `block`)
- record why the gate made that decision
- handle mode overrides and warning overrides

**Scope Out**

- override learning
- owner review UI
- adaptive classification

**Expected Files To Edit**

- [src/intake/gates.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/gates.py)
- [src/intake/orchestration.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py)
- [src/intake/decision.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/decision.py)
- [tests/test_nb02_v02.py](file:///Users/pranay/Projects/travel_agency_agent/tests/test_nb02_v02.py)
- add dedicated D1 gate tests if needed

**Acceptance Criteria**

- The raw NB02 verdict remains inspectable after policy evaluation.
- The system also emits an effective autonomy outcome for downstream consumers.
- `PROCEED_TRAVELER_SAFE` can become review-gated without pretending NB02 never said it.
- `STOP_NEEDS_REVIEW` is always blocked.
- `audit` and `emergency` mode overrides work per policy.
- Existing traveler-safe vs internal-draft behavior remains functionally correct.

**Verification Commands**

```bash
uv run pytest tests/test_nb02_v02.py tests/test_settings_behavioral.py -q
```

Add or extend tests to explicitly verify:

- raw verdict preserved
- effective gate outcome emitted
- `STOP_NEEDS_REVIEW` invariant
- review downgrade path for `PROCEED_TRAVELER_SAFE`

**Non-Goals**

- No frontend changes required in this task

---

### Task 3 — Wire D1 into the runtime/API contract so downstream systems can reason about approval state

**Objective**

Expose the autonomy outcome through the runtime/API contract so workbench, owner review flows, D2 presentation logic, and future D5 learning can consume it.

**Scope In**

- include autonomy metadata in the spine result / API response
- define the canonical fields for downstream use
- keep current consumers working or update them in the same change
- make the distinction between raw verdict and effective autonomy result explicit

**Scope Out**

- consumer/public audit surface
- D5 override analytics

**Expected Files To Edit**

- [src/intake/orchestration.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py)
- [spine_api/server.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/server.py)
- [frontend/src/types/spine.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/types/spine.ts)
- relevant API contract tests

**Acceptance Criteria**

- API response includes enough autonomy information for a UI to answer:
  - what NB02 said
  - what policy required
  - whether human review is mandatory
- no ambiguity remains between traveler-safe system judgment and approval-gated delivery state
- contract tests remain green after the change

**Verification Commands**

```bash
uv run pytest tests/test_api_contract_v02.py tests/test_nb02_v02.py -q
```

If frontend contract touched:

```bash
cd frontend && npx tsc --noEmit
```

**Non-Goals**

- no owner settings UI yet

---

### Task 4 — Implement the owner-facing D1 settings path with one canonical resource

**Objective**

Give the owner a real way to read and update the autonomy policy instead of leaving D1 as backend-only hidden config.

**Scope In**

- backend read/update endpoint(s) for D1 policy
- frontend type/client updates to the canonical D1 shape
- a basic owner/workbench settings surface to inspect and modify D1 settings
- persistence through the current file-backed store

**Scope Out**

- RBAC/auth hardening
- multi-agency resolution from auth context
- full owner review queue implementation

**Expected Files To Edit**

- [spine_api/server.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/server.py)
- [frontend/src/lib/governance-api.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/governance-api.ts)
- [frontend/src/types/governance.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/types/governance.ts)
- either:
  - [frontend/src/app/workbench/SettingsPanel.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/SettingsPanel.tsx)
  - or the owner-facing settings surface if one already exists / is introduced

**Acceptance Criteria**

- There is one canonical settings resource for D1.
- The owner can inspect current per-`decision_state` gates.
- The owner can update them and see them persist.
- Invalid updates that violate the `STOP_NEEDS_REVIEW -> block` invariant are rejected.
- Frontend types and backend response shapes match.

**Verification Commands**

Backend:

```bash
uv run pytest tests/test_agency_settings.py tests/test_api_contract_v02.py -q
```

Frontend:

```bash
cd frontend && npx tsc --noEmit
```

Add UI tests if new interactive settings UI is introduced.

**Non-Goals**

- no full auth or role enforcement yet
- no duplicate route set for approvals/autonomy

---

### Task 5 — Add D5/D2-ready hooks without implementing D5/D2 fully

**Objective**

Prepare D1 outputs so later D5 override learning and D2 presentation split can build on them without refactoring D1 again.

**Scope In**

- structured reason codes for autonomy outcomes
- explicit place to record future override events / policy-origin metadata
- clear separation between raw verdict and delivery approval state

**Scope Out**

- actual override event storage
- actual adaptive autonomy / trip classification
- consumer/public report builder

**Expected Files To Edit**

- [src/intake/gates.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/gates.py)
- [src/intake/orchestration.py](file:///Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py)
- possibly API/types touched in Task 3

**Acceptance Criteria**

- Autonomy results include machine-readable reason codes, not only prose strings.
- Future D5 implementation can compare system verdict vs autonomy outcome vs human override without schema surgery.

**Verification Commands**

Covered by the task-specific tests above.

**Non-Goals**

- no analytics dashboards
- no suggestion engine

---

## F. Recommended Implementation Sequence

Do the work in this order:

1. **Task 1** — policy contract upgrade
2. **Task 2** — raw verdict preservation + autonomy outcome model
3. **Task 3** — runtime/API contract wiring
4. **Task 4** — owner-facing settings path
5. **Task 5** — future hooks / reason-code cleanup

Why this order:

- Task 1 gives the policy a real shape.
- Task 2 fixes the core architectural flaw.
- Task 3 makes the new semantics visible to downstream systems.
- Task 4 makes D1 operational.
- Task 5 keeps the upgrade forward-compatible.

---

## G. Long-Term Perspective The Implementer Must Keep In Mind

### D1 is not an isolated backend settings tweak

It is the governance layer that will later connect to:

- D2 consumer vs agency presentation surfaces
- D3 sourcing escalation/approval behavior
- D4 suitability warning handling
- D5 override learning
- owner review queues
- junior-agent approval controls

### The correct long-term model is three layers, not one

The system should eventually be able to distinguish:

1. **Judgment layer** — what NB02 concluded
2. **Policy layer** — what the agency allows automatically
3. **Human action layer** — what the agent/owner actually approved, rejected, or overrode

If the current implementation compresses those into one mutated field, the system will keep paying for it later.

### The current file-backed config is acceptable for now

Do not block D1 on the perfect persistence architecture. The current file-backed settings store is enough to land the governance model correctly while Gap #02 remains unresolved.

### Adaptive autonomy is later, not now

Do not use this task to invent a classifier. The right work now is to create a clean static policy layer with the right interfaces and telemetry hooks.

---

## H. Decision Gate

**Recommendation:** **GO**, but only as a real multi-step architectural upgrade.

### Go for

- upgrading the D1 policy contract
- preserving raw NB02 verdicts
- introducing an explicit autonomy outcome
- adding canonical settings API/UI support
- preparing D5/D2-compatible hooks

### No-go for this pass

- adaptive customer+trip classification
- DB-backed multi-tenant settings
- full owner review workflow / RBAC system
- D5 override learning implementation

If the implementer only adds `approval_gates` to the dataclass and keeps mutating `decision_state` in place, that is **not** a successful D1 completion.

The success bar is: **D1 becomes a real policy layer at the NB02/NB03 boundary, with a preserved raw verdict, a first-class autonomy outcome, and an owner-configurable contract.**
