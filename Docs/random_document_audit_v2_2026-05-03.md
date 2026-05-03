# Random Document Audit Report

## 1. Document Inventory

Candidate pool: 65 actionable documents (specs, status reports, issue reviews, audits, implementation plans, architecture docs). Excluded: ~200 `Docs/research/` frontier vision specs (no code), Archive/, memory/ chat logs, notebook/ chat exports.

| Doc ID | Path | Type | Why it may matter |
| ------ | ---- | ---- | ----------------- |
| DOC-001 | `specs/decision_policy.md` | Spec | Decision engine rules |
| DOC-002 | `specs/INDEX.md` | Spec index | Project specification hub |
| DOC-003 | `Docs/travel_agency_process_issue_review_2026-05-01.md` | Issue review | Recent issue audit |
| DOC-004 | `Docs/INTAKE_ACTIONABLE_MISSING_DETAILS_2026-04-30.md` | Implementation summary | Intake UX changes |
| DOC-005 | `Docs/PII_GUARD_RAILS_IMPLEMENTATION_2026-04-26.md` | Security impl | PII guardrail details |
| ... | ... | ... | ... |

Full list: 65 files across `specs/`, `Docs/validation/`, `Docs/status/`, `Docs/context/`, root `TODO.md`, and selected actionable `Docs/` files.

## 2. Random Selection

```
Chosen document: Docs/INTAKE_ACTIONABLE_MISSING_DETAILS_2026-04-30.md
Selection method: SHA256("2026-05-03-audit-v2" + sorted_candidates) mod 65 = index 7
Why this doc is worth auditing: Recently implemented UX change (dated 6 days ago from audit). Claims specific UI behaviors, persistence strategies, and architectural gaps that can be verified directly against both frontend and backend code.
```

## 3. Chosen Document Deep Analysis

**File**: `Docs/INTAKE_ACTIONABLE_MISSING_DETAILS_2026-04-30.md` (56 lines)

### 3A. Extracted Doc Items

| Doc Item ID | Type | Short quote / evidence | Location | Interpretation | Confidence |
|------------|------|------------------------|----------|---------------|------------|
| DI-01 | Explicit Task | "Missing Customer Details now splits unresolved items into Required missing fields and Recommended details" | L11 | Completed: frontend renders split detail categories | High |
| DI-02 | Explicit Task | "Every unresolved row now has direct actions on the row: Add ... / Ask traveler" | L12-13 | Completed: inline action buttons | High |
| DI-03 | Explicit Task | "Inline editors now exist on the blocker panel for: budget, origin city, trip priorities / must-haves, date flexibility" | L15-19 | Completed: inline editing UI | High |
| DI-04 | Explicit Task | "Suggested Follow-up is now generated from the remaining unresolved rows only" | L20 | Completed: dynamic follow-up draft | High |
| DI-05 | Explicit Task | "Primary CTA now changes by state: required gaps present -> Draft follow-up, resolved -> Continue to options or Build trip options" | L21-23 | Completed: state-dependent CTA | High |
| DI-06 | Explicit Task | "Notes is now collapsible when the screen is in missing-details mode" | L24 | Completed: collapsible notes | High |
| DI-07 | Explicit Task | "Trip Details and Known Trip Details now surface origin and the newly captured planning inputs more clearly" | L25 | Completed: display improvements | High |
| DI-08 | Explicit Task | "Footer actions on this screen now use the shared button primitive instead of a one-off treatment" | L26 | Completed: button consolidation | High |
| DI-09 | Current-State Claim | "budget and origin persist through canonical trip fields" | L30 | Claim: PATCH /trips syncs budget/origin to extracted.facts | High |
| DI-10 | Current-State Claim | "trip priorities / must-haves and date flexibility are currently persisted through tagged lines in agentNotes" | L31 | Claim: tagged note fallback pattern | High |
| DI-11 | Current-State Claim | "Tagged note format: Trip priorities: ... / Date flexibility: ..." | L35-38 | Claim: specific text format in agentNotes | High |
| DI-12 | Architecture Claim | "This keeps the screen actionable immediately without inventing a duplicate route or shadow persistence path" | L40 | Claim: architectural restraint | Medium |
| DI-13 | Implicit Task | "The trip model still lacks dedicated first-class fields for trip priorities / must-haves and date flexibility" | L44-47 | Gap: trip model missing columns | High |
| DI-14 | Implicit Task | "If these inputs need downstream policy, search, or analytics ownership beyond intake UX, the next correct step is a canonical model/API addition" | L49 | Future work: model/API expansion | High |
| DI-15 | Current-State Claim | "Verification: tsc --noEmit, npm test IntakePanel, curl health, curl frontend" | L53-56 | Claim: verification steps were run | High |

## 4. Extracted Task Candidates

| Task Candidate ID | Source Doc Item IDs | Task | Explicit or Implicit | Why this is a task | Expected repo area | Initial priority guess |
|-------------------|---------------------|------|---------------------|-------------------|---------------------|----------------------|
| TC-01 | DI-13, DI-14 | Add first-class `trip_priorities` and `date_flexibility` fields to Trip model | Implicit | Tagged-note fallback blocks downstream policy/search/analytics | `spine_api/models/trips.py`, `spine_api/contract.py` | P1 |
| TC-02 | DI-13 | Add extraction of `trip_priorities` and `date_flexibility` to extraction pipeline | Implicit | `PROPOSAL_READY_DELTA` requires these fields but pipeline never sets them | `src/intake/extractors.py` | P1 |
| TC-03 | DI-13, DI-14 | Add `trip_priorities` and `date_flexibility` to PATCH /trips sync logic | Implicit | Frontend saves these through agentNotes but backend PATCH doesn't sync them | `spine_api/server.py:2141-2187` | P1 |
| TC-04 | DI-10, DI-11 | Verify `agentNotes` field is covered by privacy guard | Implicit | `agentNotes` not in `_FREEFORM_FIELD_NAMES` — freeform content passes undetected | `src/security/privacy_guard.py:91-107` | P0 |
| TC-05 | DI-09 | Verify budget/origin sync works end-to-end (frontend → BFF → backend PATCH → persistence) | Implicit | Claimed persistence path needs verification across all layers | `spine_api/server.py`, frontend BFF | P2 |
| TC-06 | DI-08 | Verify shared button primitive is used consistently across all footer actions | Implicit | Claim: "shared button primitive" — verify no one-off buttons remain | `frontend/src/components/workspace/panels/IntakePanel.tsx` | P3 |
| TC-07 | DI-01, DI-02, DI-03, DI-04, DI-05, DI-06 | Verify all claimed intake UX behaviors render correctly | Implicit | Doc claims completed work — verify against actual UI | `IntakePanel.tsx`, `planning-status.ts` | P2 |
| TC-08 | DI-15 | Verify doc-stated verification commands work | Implicit | `npm test -- --run` uses vitest, not jest — flag compatibility | frontend test infra | P3 |
| TC-09 | DI-12 | Audit for duplicate routes or shadow persistence paths | Implicit | Doc claims no duplicate routes were created — verify | `spine_api/server.py`, frontend BFF | P2 |

## 5. Static Codebase Reality Check

### TC-01: First-class fields for trip_priorities and date_flexibility

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Missing |
| **Evidence** | `spine_api/models/trips.py:15-73`: Trip model has no `trip_priorities` or `date_flexibility` columns. These values exist only in `extracted` JSON (line 46: `extracted: Mapped[dict]`) |
| **What exists today** | `src/intake/readiness.py:30-33`: `PROPOSAL_READY_DELTA = ["trip_priorities", "date_flexibility"]` — the fields ARE defined as readiness requirements but CANNOT be populated by the extraction pipeline |
| **Gap** | Trip model lacks first-class columns; extraction pipeline (`extractors.py`, searched for `set_fact.*priorit|set_fact.*flexib`) never sets these facts; PATCH /trips (server.py:2141-2187) only syncs `origin` and `budget` |
| **Actual work needed** | (a) Add columns to Trip model, (b) Add extraction rules, (c) Add PATCH sync logic, (d) Add API contract fields |

### TC-02: Extraction pipeline missing trip_priorities/date_flexibility

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Missing |
| **Evidence** | `src/intake/extractors.py:1246-1548`: Full extraction pipeline. `set_fact("budget_flexibility", ...)` exists at line 1359, but zero occurrences of `trip_priorities` or `date_flexibility` |
| **What exists today** | `src/intake/validation.py:52-59`: `QUOTE_READY` includes `budget_raw_text`. `src/intake/readiness.py:30-33`: `PROPOSAL_READY_DELTA` lists these two missing fields |
| **Gap** | `proposal_ready` tier (tier 2 of 4) is unreachable through fact-based extraction alone. Frontend tests mock these fields (`bff-trip-adapters.test.ts:230`, `DecisionPanel.readiness.test.tsx:49`) but real pipeline never produces them |
| **Actual work needed** | Add regex patterns in `extractors.py` to detect trip priorities preferences and date flexibility signals from raw_note/owner_note |

### TC-03: PATCH /trips sync logic for new fields

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Missing |
| **Evidence** | `spine_api/server.py:2141-2187`: `_sync_manual_trip_fields` only handles `origin` (lines 2151-2159) and `budget` (lines 2161-2176). No handling for `trip_priorities` or `date_flexibility` |
| **What exists today** | Frontend PATCH route at `frontend/src/app/api/trips/[id]/route.ts:40-58`: `PATCHABLE_FIELDS` includes `agentNotes` (line 42) but not `trip_priorities` or `date_flexibility` as first-class fields |
| **Gap** | Frontend saves trip_priorities and date_flexibility into `agentNotes` as tagged lines. Backend PATCH never deserializes these into `extracted.facts` |
| **Actual work needed** | Extend `_sync_manual_trip_fields` to parse `trip_priorities` and `date_flexibility` from either dedicated fields or tagged agentNotes |

### TC-04: agentNotes privacy guard coverage

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Partially Done — email/phone/medical covered, freeform not covered |
| **Evidence** | `src/security/privacy_guard.py:91-107`: `_FREEFORM_FIELD_NAMES` includes `"note"` and `"notes"` but NOT `"agent_notes"` or `"agentNotes"`. `_extract_strings` (line 120-139) scans 5 levels deep and catches email/phone/medical keywords regardless of field name |
| **What exists today** | `spine_api/persistence.py:199-201`: `check_trip_data(trip_data)` called on save. `spine_api/persistence.py:276-278`: called on update. Both paths scan the full dict |
| **Gap** | `agentNotes` containing freeform text like "Customer wants luxury hotels, 3 kids under 10, allergic to peanuts, budget 5L" (no email/phone/medical keywords) passes through undetected. Tagged notes (`trip_priorities`, `date_flexibility`, `Contact name`) are essentially freeform text in a non-scanned field name |
| **Actual work needed** | Add `"agent_notes"` and `"agentNotes"` (camelCase from frontend) to `_FREEFORM_FIELD_NAMES` |

### TC-05: Budget/origin persistence path

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Already Done — verified |
| **Evidence** | `spine_api/server.py:2151-2176`: `_sync_manual_trip_fields` writes `origin_city` and `budget_raw_text`/`budget` into `extracted.facts` with `authority_level: "explicit_user"`. Frontend `IntakePanel.tsx:476-490`: sends `budget` and `origin` in updateData. BFF `route.ts:40-58`: `PATCHABLE_FIELDS` includes both |
| **Gap** | None found. Path is: IntakePanel → saveTrip → BFF PATCH → backend PATCH → _sync_manual_trip_fields → TripStore.update_trip |
| **Actual work needed** | None |

### TC-06: Shared button primitive usage

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Already Done — verified |
| **Evidence** | `frontend/src/components/ui/button.tsx:42-53`: Canonical `Button` component with `cva` variants. `IntakePanel.tsx` line 52: imports Button. Lines 1035, 1058, 1112, 1312, 1399, 1440, 1592, 1616, 1669, 1695: all use the shared Button |
| **Gap** | None found. No one-off button implementations remain in IntakePanel |
| **Actual work needed** | None |

### TC-07: Intake UX behavior verification (static)

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Already Done — all claims verified |
| **Evidence** | DI-01: `planning-status.ts:79-105` (required) + `:107-121` (recommended) + `IntakePanel.tsx:1289-1333` (rendering). DI-02: `IntakePanel.tsx:1112-1123` (Add/Ask traveler buttons). DI-03: `IntakePanel.tsx:983-1096` (budget editor), `:1049-1096` (text editors). DI-04: `IntakePanel.tsx:156-173` (`buildFollowUpDraftFromRows`). DI-05: `planning-status.ts:320-325` (`getPlanningPrimaryActionLabel`). DI-06: `IntakePanel.tsx:1383-1446` (collapsible notes) |
| **Gap** | None found. Implementation matches all claims |
| **Actual work needed** | None |

### TC-08: Verification commands accuracy

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Partially Done — `npm test` flag `--run` is vitest-compatible |
| **Evidence** | `frontend/package.json:11`: `"test": "vitest"`. Vitest supports `--run` flag. Run result: 15/15 tests pass |
| **Gap** | `npm test -- --run` works but verbose. Project uses vitest directly. Backend `curl` verification URLs valid but backend was not running during audit |
| **Actual work needed** | None critical. Could document that vitest is the framework, not jest |

### TC-09: No duplicate routes created

| Aspect | Evidence |
|--------|----------|
| **Codebase Status** | Already Done — verified |
| **Evidence** | `spine_api/server.py`: Single `POST /run` (line 1433), single `PATCH /trips/{trip_id}` (line 2075), single `PATCH /trips/{trip_id}/stage` (line 2037). Frontend BFF has single PATCH at `api/trips/[id]/route.ts` |
| **Gap** | None found. No duplicate routes exist for intake or trip update |
| **Actual work needed** | None |

## 6. Dynamic Verification and Test Baseline

### Baseline Before Audit

```
Frontend:  67 test files, 618 tests — ALL PASSING
Backend:   611 passed, 1 failed (pre-existing: missing openai pip package), 10 skipped, 4 warnings
TypeScript: tsc --noEmit — CLEAN (zero errors)
```

### Targeted Test Results

```
IntakePanel.test.tsx:  15/15 passed (685ms)
planning-status.test.ts: 5/5 passed
bff-trip-adapters.test.ts: 9/9 passed
```

### Pre-existing Failures

```
tests/test_llm_clients.py::test_openai_decide — FAILED (openai package not installed)
This is pre-existing, unrelated to the audited doc.
```

### Verification Steps from Document

```
.tsc --noEmit          → PASS (zero errors)
.npm test IntakePanel   → 15/15 PASS
.curl health :8000      → NOT RUNNING (backend not started)
.curl frontend :3000    → 200 OK
```

## 7. Critical Implementation and Test Traps Checked

### 7A. Environment Variable Loading

| Pattern | Files Affected | Risk |
|---------|---------------|------|
| 11+ module-level `os.getenv` calls at import time | `decision.py:31`, `hybrid_engine.py:29`, `recovery_agent.py:42-53`, `security.py:21`, `database.py:22`, `encryption.py:13-26`, `audit_bridge.py:34-36`, `rate_limiter.py:22`, `auth.py:48-49` | HIGH — monkeypatch can't affect already-imported modules |
| Call-time reads (good pattern) | `privacy_guard.py:32`, `safety.py:241`, `llm/__init__.py:94` | SAFE |

**Finding**: `src/security/encryption.py:13-26` reads `ENCRYPTION_KEY` and `DATA_PRIVACY_MODE` at import, deciding whether to raise. If tests monkeypatch `DATA_PRIVACY_MODE` after import, the encryption module already decided. The conftest workaround (pre-setting `JWT_SECRET` at conftest import, line 30-32) proves this pattern is already known as fragile.

### 7B. Test Isolation

| Issue | Detail |
|-------|--------|
| `reset_data_privacy_mode` autouse fixture | `tests/conftest.py:96-104`: Cannot undo module-level env-var caching |
| 3 global singletons without reset | `telemetry.py:302-310`, `health.py:268-275`, `decision.py:34` |
| `LLMUsageGuard` has reset but not called in conftest | `usage_guard.py:321` has `reset_usage_guard()` but conftest never calls it |

### 7C. Full Suite Coverage

Full suite run is feasible and was executed for this audit. Both frontend (618 tests) and backend (611/612 tests) suite results are recorded above.

## 8. Data, Privacy, and PII Boundary Checks

### 8A. agentNotes in Privacy Guard Scope

`src/security/privacy_guard.py:91-107`: `_FREEFORM_FIELD_NAMES` does NOT include `"agent_notes"` or `"agentNotes"`. Email/phone/medical regex scanning (depth 5) still catches explicit PII in agentNotes content, but general freeform text passes through undetected.

**Write paths checked**: `save_trip` (persistence.py:191-201), `update_trip` (persistence.py:276-278). Both call `check_trip_data`.

### 8B. Scan Depth Analysis

| Check | Depth | AgentNotes Coverage |
|-------|-------|---------------------|
| `_extract_strings` (email/phone/medical) | max_depth=5 | YES — scans all nested strings |
| `_has_freeform_user_input` (field name match) | max_depth=2 | NO — agentNotes not in freeform field set |

### 8C. Content Threshold

`privacy_guard.py:239`: Freeform strings must be >10 chars. This means short PII content like `"Dr. Smith"` (9 chars) or labels in agentNotes tagged format are safe from false positives. Email/phone detection has no length threshold.

### 8D. Fixture Data Detection

`privacy_guard.py:162-182`: Checks `fixture_id` in known set AND `source` field patterns. Two-marker detection, not single-marker. Adequate.

### 8E. Heuristic Detection Limits

For `_MEDICAL_KEYWORD_PATTERN` (privacy_guard.py:83-86):
- Catches: diabetic, diabetes, wheelchair, mobility, medical, health, allerg*, disabil*, chronic, insulin, epilepsy, asthma, heart, bp, blood pressure, pregnant, pregnancy
- Misses: many conditions (cancer, HIV, mental health conditions, specific medications)
- False positives: "health" matches "healthy", "heart" matches "heart of the city"
- Tests: `tests/test_privacy_guard.py` covers known scenarios

## 9. Deduped Issue / Task Register

### ISSUE-001: trip_priorities and date_flexibility never extracted, blocking proposal_ready tier

**Category**: bug
**Origin**: Implicit (DI-13, DI-14). Source doc: `Docs/INTAKE_ACTIONABLE_MISSING_DETAILS_2026-04-30.md:44-49`
**Codebase Evidence**:
- `src/intake/readiness.py:30-33`: `PROPOSAL_READY_DELTA = ["trip_priorities", "date_flexibility"]` — these are required for tier 2 readiness
- `src/intake/extractors.py:1246-1548`: Entire extraction pipeline — zero occurrences of `set_fact("trip_priorities"...)` or `set_fact("date_flexibility"...)`
- `tests/test_readiness_engine.py:54-55`: Test fixtures DO populate these fields, so tests pass but real pipeline never reaches this tier
**Current Behavior**: `proposal_ready` tier is unreachable through normal extraction. Only reachable through test fixtures or manual PATCH to `extracted.facts`
**Gap**: Pipeline extracts `budget_flexibility` (line 1359) and `trip_purpose`/`trip_style` (line 1484) but never `trip_priorities` or `date_flexibility`
**Confidence**: High
**Acceptance Criteria**:
- [ ] `extractors.py` sets `trip_priorities` fact from patterns like "looking for kid-friendly activities", "honeymoon must-have beach resort"
- [ ] `extractors.py` sets `date_flexibility` fact from patterns like "dates are flexible +/- 2 days", "must travel on exact dates"
- [ ] Test adds scenario where raw_note contains trip priorities → extracted facts include `trip_priorities`
- [ ] Full backend suite passes (no regressions)
**Test Plan**: Automated: unit test in `test_extraction_fixes.py` with raw_note containing priorities/flexibility. Integration: verify `readiness.py` reaches `proposal_ready` in integration test

### ISSUE-002: agentNotes missing from privacy guard freeform field names

**Category**: security
**Origin**: Implicit (TC-04). Source doc: `Docs/INTAKE_ACTIONABLE_MISSING_DETAILS_2026-04-30.md:31-38`
**Codebase Evidence**:
- `src/security/privacy_guard.py:91-107`: `_FREEFORM_FIELD_NAMES` excludes `"agent_notes"` and `"agentNotes"`
- `spine_api/persistence.py:199-201`: `check_trip_data` called on save path — agentNotes passes freeform check
- `spine_api/persistence.py:276-278`: `check_trip_data` called on update path — same gap
- `spine_api/server.py:2141-2187`: PATCH /trips — agentNotes flows through to persistence unchecked
- `frontend/src/app/api/trips/[id]/route.ts:42`: `agentNotes` is in `PATCHABLE_FIELDS` and is forwarded
**Current Behavior**: `agentNotes` content passes the freeform heuristic undetected. Email/phone/medical regex still catches explicit PII (depth=5 string scan). Freeform text like "Customer: John Smith, prefers early check-in due to back pain" passes through — `John Smith` (no regex match for name), `back pain` (not in medical keywords)
**Gap**: Tagged notes format stores user-supplied freeform text in a field invisible to the freeform heuristic
**Risk**: Medium — email/phone still caught; medical keywords partially caught (limited set); general PII-like freeform bypassed
**Confidence**: High
**Acceptance Criteria**:
- [ ] Add `"agent_notes"` and `"agentNotes"` to `_FREEFORM_FIELD_NAMES` in privacy_guard.py
- [ ] Test: saving trip with `agentNotes: "Customer medical condition: severe asthma"` is blocked in dogfood mode
- [ ] Test: saving trip with fixture `agentNotes` passes (no false positive for synthetic data)
- [ ] Full backend test suite passes (no regressions)
**Rollback / Kill Switch**: Remove the field name from the set (one-line revert). Env var `DATA_PRIVACY_MODE=production` bypasses all privacy guards

### ISSUE-003: Trip model lacks first-class columns for trip_priorities and date_flexibility

**Category**: architecture
**Origin**: Explicit (DI-13). Source doc: `Docs/INTAKE_ACTIONABLE_MISSING_DETAILS_2026-04-30.md:44-47`
**Codebase Evidence**:
- `spine_api/models/trips.py:15-73`: Full Trip model — no `trip_priorities` or `date_flexibility` columns
- `spine_api/contract.py:98-115`: `SpineRunRequest` — no dedicated fields
- `frontend/src/lib/api-client.ts:288-366`: Frontend Trip interface — no dedicated fields for priorities/flexibility (only `agentNotes` at line 318, `activityProvenance` at line 324)
**Current Behavior**: These values live ONLY in agentNotes as tagged text strings. Not queryable, not searchable, not usable by policy/analytics
**Gap**: Doc states: "If these inputs need downstream policy, search, or analytics ownership beyond intake UX, the next correct step is a canonical model/API addition" (line 49)
**Confidence**: High
**Acceptance Criteria**:
- [ ] Add `trip_priorities: Mapped[Optional[str]]` and `date_flexibility: Mapped[Optional[str]]` to Trip model
- [ ] Alembic migration created
- [ ] Add to `SpineRunRequest` contract
- [ ] Add to frontend Trip type
- [ ] Add to PATCH sync logic in `_sync_manual_trip_fields`
- [ ] Migrate existing tagged-note values to first-class columns (data migration)
**Test Plan**: Automated: model test, migration test, PATCH test. Manual: verify existing trips with tagged notes are migrated correctly

### ISSUE-004: Module-level env var caching prevents test-time configuration changes

**Category**: tooling
**Origin**: Implicit (found during trap checks). Source doc: N/A (discovered during audit)
**Codebase Evidence**:
- `src/security/encryption.py:13-26`: Reads `ENCRYPTION_KEY`, `DATA_PRIVACY_MODE` at import → raises if missing
- `src/intake/decision.py:31`: `_HYBRID_ENGINE_ENABLED` cached at import
- `src/decision/hybrid_engine.py:29`: `LLM_GUARD_ENABLED` cached at import
- `src/agents/recovery_agent.py:42-53`: 6 env vars cached at import
- `tests/conftest.py:30-32`: Workaround pre-sets `JWT_SECRET` before imports
**Current Behavior**: Tests that `monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "true")` have no effect on already-imported modules. conftest.py at lines 30-32 already uses a workaround pattern for `JWT_SECRET`
**Gap**: Inconsistent approach — some modules read at call time (privacy_guard.py, safety.py), others at import time (decision.py, hybrid_engine.py)
**Confidence**: High
**Acceptance Criteria**:
- [ ] Refactor `encryption.py` to use lazy initialization (call-time read, not import-time)
- [ ] Refactor `decision.py:31` to use function-level read (or provide explicit reset for tests)
- [ ] Refactor `hybrid_engine.py:29` similarly
- [ ] Document convention in conftest.py comments: env vars should be read at call time unless caching is intentional and resettable
- [ ] Full test suite passes
**Test Plan**: Verify that monkeypatching `USE_HYBRID_DECISION_ENGINE` after import now works

### ISSUE-005: verification command uses `npm test` with vitest-specific `--run` flag

**Category**: docs
**Origin**: Implicit (DI-15). Source doc: `Docs/INTAKE_ACTIONABLE_MISSING_DETAILS_2026-04-30.md:54`
**Codebase Evidence**: `frontend/package.json:11`: `"test": "vitest"`. Not jest. Vitest accepts `--run`. The documented command `npm test -- --run src/components/workspace/panels/__tests__/IntakePanel.test.tsx` works correctly.
**Current Behavior**: Command works. No functional issue.
**Gap**: Doc doesn't mention that vitest (not jest) is the framework. A new developer running `npx jest` would fail.
**Confidence**: Medium
**Acceptance Criteria**: N/A (minor documentation note)
**Not Worth Doing** actively — low priority documentation polish

### ISSUE-006: Three global singletons without test reset functions

**Category**: tooling
**Origin**: Implicit (found during trap checks). Source doc: N/A (discovered during audit)
**Codebase Evidence**:
- `src/decision/telemetry.py:302-310`: `DecisionTelemetry` — no reset
- `src/decision/health.py:268-275`: `HybridEngineHealth` — no reset
- `src/intake/decision.py:34`: `_hybrid_engine_instance` — no reset
**Current Behavior**: State accumulates across tests. Metrics from one test leak into the next. Not causing test failures today but creates order-dependent fragility
**Gap**: No reset mechanism for accumulated telemetry/health metrics
**Confidence**: Medium
**Acceptance Criteria**:
- [ ] Add `reset_telemetry()` to `DecisionTelemetry`
- [ ] Add `reset_health()` to `HybridEngineHealth`
- [ ] Call both in conftest.py cleanup or provide explicit reset fixtures
- [ ] Full test suite passes (no regressions)

## 10. Prioritization

| ID | Title | Severity | Blast Radius | Effort | Confidence | Priority | Why |
|----|-------|---------:|------------:|------:|----------:|----------|-----|
| ISSUE-002 | agentNotes privacy guard gap | 4 | 3 | 1 | 5 | **P0** | Security gap: freeform text bypass. One-line fix. |
| ISSUE-001 | trip_priorities/date_flexibility never extracted | 4 | 4 | 4 | 5 | **P1** | Blocks proposal_ready tier. Core feature gap. |
| ISSUE-003 | Trip model missing first-class columns | 3 | 3 | 4 | 5 | **P1** | Architectural debt documented in source doc. |
| ISSUE-004 | Module-level env var caching | 2 | 3 | 3 | 5 | **P2** | Test fragility, not production issue. |
| ISSUE-006 | Singleton reset functions missing | 2 | 2 | 2 | 3 | **P3** | Latent test isolation risk. |
| ISSUE-005 | Verification command docs | 1 | 1 | 1 | 4 | **P3** | Documentation polish only. |

### Priority Queues

#### P0
- **ISSUE-002**: Add `agent_notes`/`agentNotes` to `_FREEFORM_FIELD_NAMES` in privacy_guard.py

#### P1
- **ISSUE-001**: Add extraction of `trip_priorities` and `date_flexibility` to pipeline
- **ISSUE-003**: Add first-class trip model columns for priorities and flexibility

#### P2
- **ISSUE-004**: Refactor module-level env var reads to call-time

#### P3
- **ISSUE-006**: Add singleton reset functions to telemetry/health/engine
- **ISSUE-005**: Minor documentation polish (not worth acting on now)

#### Quick Wins
- **ISSUE-002**: One-line addition to a set. Immediate security improvement.

#### Risky Changes
- **ISSUE-003**: Schema migration — requires Alembic migration, data migration from tagged notes, coordination with frontend types

#### Not Worth Doing
- **ISSUE-005**: Verification command docs are accurate; framework difference is minor documentation polish

## 11. Proof-of-Concept Validation

No proof-of-concept probe was needed. Static and existing dynamic evidence were sufficient. All claims in the document were verifiable through source inspection and existing test execution.

## 12. Assumptions Challenged by Implementation

| Assumption | Why it seemed true | What disproved it | Evidence | How recommendation changed |
|------------|-------------------|-------------------|----------|---------------------------|
| "trip_priorities and date_flexibility are properly extracted" | Doc says the intake screen is "actionable"; these fields are in `PROPOSAL_READY_DELTA` | Grep of extractors.py shows zero `set_fact` calls for either field | `src/intake/extractors.py` — searched for `trip_priorities`, `date_flexibility`, `set_fact.*priorit`, `set_fact.*flexib` — only `budget_flexibility` exists | ISSUE-001 raised from P3 to P1 — this is a real feature gap, not just a model gap |
| "agentNotes would be covered by privacy guard since it's user input" | Notes/note fields are in the freeform set; agentNotes seems like a variant | `agentNotes` is NOT in `_FREEFORM_FIELD_NAMES` | `privacy_guard.py:91-107` — set includes `note` and `notes` but not `agentNotes` or `agent_notes` | ISSUE-002 raised to P0 — security gap found |

## 13. Parallel Agent / Multi-Model Findings

Four parallel exploration agents were used:

| Agent | Role | Key Finding |
|-------|------|-------------|
| Agent A (Frontend code) | Found all IntakePanel source, tests, tagged note helpers, shared button usage | All frontend claims verified; 15 tests passing |
| Agent B (Backend model/API) | Found trip model, API contracts, extraction pipeline | `trip_priorities`/`date_flexibility` never extracted; PATCH doesn't sync them |
| Agent C (Tests/verification) | Found test framework (vitest), coverage gaps, 15 IntakePanel tests | IntakeTab.tsx has no dedicated tests; backend has 15 dedicated intake tests |
| Agent D (Security/traps) | Found env-var caching, privacy guard gap, singleton leaks | 11+ module-level env reads; agentNotes not in freeform fields; 3 singletons without reset |

All findings reconciled into the single deduped register above. No contradictions between agents.

## 14. Discussion Pack

### My Recommendation

I recommend working on:

1. **ISSUE-002** — agentNotes privacy guard gap (P0, one-line fix)
2. **ISSUE-001** — trip_priorities/date_flexibility extraction (P1, core feature gap)
3. **ISSUE-003** — First-class trip model columns (P1, architectural debt)

**Reason**: ISSUE-002 is the highest-severity actionable item with the lowest effort. ISSUE-001 directly prevents the `proposal_ready` readiness tier from working. ISSUE-003 is the documented long-term fix for the tagged-note fallback that blocks downstream policy/analytics.

### Why These Matter Now

- ISSUE-002: Every trip save with agentNotes content bypasses the freeform privacy check. This is active on every save/update in dogfood mode.
- ISSUE-001: The intake pipeline has a documented gap — `proposal_ready` tier is defined but unreachable through normal intake. This means the readiness system has a dead tier.
- ISSUE-003: Tagged-note persistence blocks downstream policy, search, and analytics. The doc itself acknowledges this is a temporary fallback.

### What Breaks If Ignored

- ISSUE-002: Real PII in agentNotes passes through undetected in dogfood mode (email/phone still caught by regex)
- ISSUE-001: `proposal_ready` readiness tier remains dead code — can never be reached through normal extraction
- ISSUE-003: Tagged-note fallback becomes permanent technical debt; analytics/policy can't query trip priorities or date flexibility

### What I Would Not Work On Yet

- ISSUE-004 (env var caching): Existing test patterns work; refactoring 11+ modules is high-effort for medium benefit
- ISSUE-006 (singleton resets): No current test failures from this; address when they cause issues
- ISSUE-005 (docs): Trivial; address when docs are next updated

### What Is Ambiguous

None — all findings have direct codebase evidence.

### Questions For You

1. Should `trip_priorities` and `date_flexibility` be extracted from raw_note by the extraction pipeline (ISSUE-001), or should they be captured only through the IntakePanel inline editors (which already work)?
2. For ISSUE-003 (first-class columns), should we migrate existing tagged-note values into the new columns, or leave them in agentNotes and only use new columns for future trips?
3. Should the privacy guard block ALL agentNotes content in dogfood mode, or should it allow structured tagged notes (Trip priorities: ..., Date flexibility: ...) since those are system-generated format?

## 15. Online Research

No online research needed. Current findings are repo-evidence based.

## 16. ChatGPT / External Review Escalation Writeup

No escalation needed. All findings have direct codebase evidence and clear remediation paths.

## 17. Recommended Next Work Unit

### Unit-1: Fix agentNotes privacy guard and trip_priorities/date_flexibility extraction

**Goal**: Close the privacy guard gap for agentNotes and add extraction of trip_priorities and date_flexibility to the pipeline so proposal_ready tier becomes reachable.

**Issues covered**: ISSUE-002, ISSUE-001

**Scope**:
- In: `src/security/privacy_guard.py` (add field names), `src/intake/extractors.py` (add regex extraction)
- Out: Trip model schema changes (ISSUE-003 — separate unit), env var refactoring (ISSUE-004 — defer)

**Likely files touched**:
- `src/security/privacy_guard.py:91-107` — add `"agent_notes"`, `"agentNotes"` to `_FREEFORM_FIELD_NAMES`
- `src/intake/extractors.py` — add `set_fact("trip_priorities", ...)` and `set_fact("date_flexibility", ...)` in `_extract_from_freeform`
- `tests/test_privacy_guard.py` — add test for agentNotes blocking
- `tests/test_extraction_fixes.py` — add test for priorities/flexibility extraction

**Acceptance criteria**:
- [ ] Saving trip with `agentNotes: "Customer: John Doe, prefers early check-in"` is blocked in dogfood mode
- [ ] Saving trip with fixture agentNotes (synthetic data) passes
- [ ] raw_note "looking for kid-friendly activities, dates flexible +/- 2 days" extracts `trip_priorities` and `date_flexibility`
- [ ] Backend test suite: 611+ tests pass (no regressions)

**Tests to run**:
- Baseline: `uv run python -m pytest tests/ -x -q` (current: 611 passed, 1 pre-existing failure)
- Targeted: `uv run python -m pytest tests/test_privacy_guard.py tests/test_extraction_fixes.py -v`
- Full suite: `uv run python -m pytest tests/ -x -q`

**Operational safety**:
- Kill switch: Remove the two field names from `_FREEFORM_FIELD_NAMES` (one-line revert for ISSUE-002)
- Rollback: Both changes are additive (add extraction rules, add field names to a set). Rollback is trivial

**Risks**: Low. Both changes are additive. Extraction regex changes may need tuning to avoid false positives on trip_priorities detection, but pattern matching is gated by `set_fact` which requires confidence thresholds.

## 18. Appendix: Searches Performed

| Search | Scope | Purpose |
|--------|-------|---------|
| `glob **/*.md` | Entire repo (excl node_modules, .venv, archive) | Document inventory |
| `grep trip_priorities\|date_flexibility` | `src/intake/extractors.py` | Verify extraction coverage |
| `grep set_fact.*priorit\|set_fact.*flexib` | `src/` | Find any fact-setting for these fields |
| `grep agent_notes\|agentNotes` | `src/security/privacy_guard.py` | Check privacy guard field coverage |
| `grep check_trip_data\|check_privacy` | `spine_api/` | Find all privacy guard call sites |
| `grep agent_note\|agentNote\|owner_note\|ownernote` | `spine_api/` | Trace agentNotes flow through backend |
| `grep os.getenv\|os.environ` | `src/` + `spine_api/` | Module-level env var audit |
| `grep lru_cache` | `src/` | Env var caching via decorator |
| `grep \.skip\(\|\.todo\(\|xit\(\|xdescribe\(` | `frontend/src/` | Skipped/disabled test audit |
| `read IntakePanel.tsx` | Multiple offsets | Verify all claimed UI behaviors |
| `read server.py:2075-2199` | PATCH /trips handler | Verify budget/origin sync logic |
| `read privacy_guard.py:85-114` | Freeform field names | Verify agentNotes gap |
| `read persistence.py:180-280` | Save and update paths | Verify privacy guard call sites |
| `run npm test IntakePanel` | Frontend | Dynamic verification |
| `run tsc --noEmit` | Frontend | Static type check |
| `run pytest tests/` | Backend | Full suite baseline |
| `run curl health :8000` | Backend | Runtime health check |
| `run curl :3000` | Frontend | Runtime availability check |

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
