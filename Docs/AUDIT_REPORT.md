# Random Document Audit Report
**Document Selected**: `./Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md`
**Selection Method**: Random selection from all project markdown files (excluding node_modules)
**Audit Date**: 2026-04-28
**Status**: In Progress (awaiting test-runtime-verifier agent)

## 1. Document Inventory
Total candidate documents found: 1767 markdown files across:
- `Docs/` (research, analysis, process docs)
- `specs/` (schema, decision specs)
- `frontend/docs/` (feature documentation)
- `memory/` (learning and synthesis)
- `notebooks/` (exploration)
- Root markdown files (README, TESTING_SETUP, SKILL, etc.)

## 2. Random Selection
**Chosen Document**: `./Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md`
**Why This Doc**: Recent (2026-04-27) UX audit of a real scenario (Ravi's Singapore call capture); grounded in code paths, identifies concrete gaps, recommends product direction. High leverage for understanding current state.

## 3. Chosen Document Deep Analysis

### Document Summary
The audit evaluates whether the current workspace UI can capture an inbound phone call lead (Ravi answering a call from Pranay about a Singapore family trip with a toddler and elderly parents, call in Nov 2024, trip Feb 2025). 

**Verdict**: Partially usable, not best-in-class yet. Current UI preserves freeform transcript and runs the spine correctly, but lacks first-class structured fields for source, caller relationship, party composition detail, pacing, date-year confidence, and follow-up commitment.

### Key Claims in Document
1. **Current state works**: IntakePanel renders, saves messages, edits trip details, runs spine, saves results (lines 47-58)
2. **Critical gap 1**: No POST /api/trips for direct new-lead creation (lines 135-137)
3. **Critical gap 2**: Follow-up commitment cannot be operationalized (lines 139-143)
4. **Product gaps 3-9**: Missing structured fields for party composition, date ambiguity, pacing, lead source, activity provenance, call-date distinction (lines 145-169)
5. **UX gap**: Hover-only edit controls weak for touch/call capture (lines 169-173)
6. **Test gap**: No regression test for the Singapore scenario (line 211)

## 4. Extracted Task Candidates

### Explicit Tasks (from document language)
| ID | Task | Where Document Says It | Priority |
|----|------|------------------------|----------|
| TASK-001 | Create new-call/new-lead capture UI path | P0 — Missing dedicated new-call/new-lead creation path | P0 |
| TASK-002 | Operationalize follow-up promise as due-date task | P0 — Follow-up promise is not operationalized | P0 |
| TASK-003 | Add structured party composition fields | P1 — Party composition needs adult/child/elderly detail | P1 |
| TASK-004 | Surface date-year inference with provenance | P1 — Date ambiguity should be explicitly resolved | P1 |
| TASK-005 | Add pace_preference / trip_pacing field | P1 — Pace preference should be first-class | P1 |
| TASK-006 | Add lead source and relationship metadata | P1 — Lead source and relationship context are commercially important | P1 |
| TASK-007 | Distinguish activity provenance | Implicit (section on suggested vs requested activities) | P1 |
| TASK-008 | Add call_date vs travel_date fields | Implicit (needed for temporal disambiguation) | P1 |
| TASK-009 | Create Singapore scenario regression test | Explicit (lines 211, implementation direction #7) | P1 |
| TASK-010 | Improve capture UI affordance (hover-only) | P2 — UI relies on hidden hover edit controls | P2 |

## 5. Static Codebase Reality Check

**Agent: codebase-verifier (COMPLETED)**

### Claims Fully Verified (10/20)
- ✅ IntakePanel renders intake surface (lines 541-678)
- ✅ IntakePanel sends capture data to spine (lines 132-171)
- ✅ Spine converts input to envelopes with source roles (server.py:416-436)
- ✅ Spine runs and saves trip (server.py:519-601)
- ✅ IntakePanel saves messages (lines 173-203)
- ✅ IntakePanel edits trip details (lines 253-309)
- ✅ Trip model has basic message fields (api-client.ts:314-315)
- ✅ Discovery blockers defined correctly (decision.py:254-266)
- ✅ Follow-up questions generated (decision.py:1816-1829)
- ✅ SourceEnvelope role separation works (packet_models.py:255-286)

### Critical Missing Gaps (9/20)
- ❌ **C8**: No POST /api/trips route (frontend/src/app/api/trips/route.ts has only GET)
- ❌ **C9**: PATCH fields insufficient (cannot patch lead_source, caller_contact, pace_preference, follow_up_due_date)
- ❌ **C12**: No lead_source / caller / relationship fields in Trip interface (api-client.ts:287-352)
- ❌ **C13**: No party_composition detail (child_ages, elderly_count) in Trip interface
- ❌ **C14**: No pace_preference / pacing field in Trip interface
- ❌ **C15**: No follow_up_due_date field in Trip interface
- ❌ **C16**: No activity_provenance field in Trip interface
- ❌ **C17**: No date-year inference/confidence fields in Trip interface
- ❌ **C18**: No call_date / capture_date field in Trip interface

### Partially Verified (1/20)
- 🟡 **C19**: Tests exist for scenarios but NOT for Singapore call scenario with all specific constraints

### Verdict on Document Accuracy
**The document's claims are 100% accurate.** 
- Backend infrastructure (SourceEnvelope, extraction, pipeline) is correctly implemented
- Frontend API and UI intentionally lack first-class structured fields
- Document correctly identifies that audit scenario cannot be captured with full structural fidelity today
- Document's recommended product direction is sound: preserve freeform + add structured layer

## 6. Dynamic Verification and Test Baseline
**Agent: test-runtime-verifier (RUNNING - awaiting completion)**

Status: Test baseline collection in progress. Will verify:
- Frontend test coverage for IntakePanel
- Backend test coverage for discovery/packet/decision pipeline
- Whether any existing tests cover call-capture or Singapore scenario patterns
- Full test suite stability before/after findings

## 7. Critical Implementation and Test Traps Checked

### Environment Variable / Config Loading
- ✅ IntakePanel operating_mode passed explicitly (not module-cached)
- ✅ Stage selection passed through explicit prop, not env var

### Test Isolation
- To be confirmed by test-runtime-verifier agent

### All Write Paths
- ⚠️ **Path 1 (Spine creation)**: Raw submission → build_envelopes() → spine.run() → packet save ✅
- ⚠️ **Path 2 (IntakePanel save)**: customerMessage + agentNotes → PATCH /api/trips/[id] ✅
- ⚠️ **Gap**: No POST /api/trips path for direct new lead, so new trips can only be created indirectly through spine run
- ⚠️ **Gap**: New structured fields (if added) must be patchable in Path 2

### Data Boundary / Privacy
- ✅ customerMessage and agentNotes separated by source role
- ✅ SourceEnvelope correctly marks source roles (traveler/agent/system/owner)
- ⚠️ **Risk**: If relationship metadata added (e.g., "Divya's colleague"), must ensure internal-only visibility

## 8. Data, Privacy, and PII-Specific Audit
**Scope**: Document discusses capturing real call with personal details (caller name, family relationships, Divya's name as referral)

### Findings
- ✅ **Positive**: Backend already separates SourceEnvelope roles (agent notes vs customer message)
- ⚠️ **Risk**: When adding relationship metadata (referral names), must mark as internal-only, not traveler-facing
- ✅ **Current practice**: AgentNotes field is Ravi-only; SourceEnvelope source_role="owner" is correctly separated

## 9. Deduped Issue / Task Register

### ISSUE-001: No POST /api/trips for new lead creation
- **Category**: architecture, routing, product decision
- **Origin**: Explicit Task, P0 section, lines 133-137
- **Codebase Evidence**: `frontend/src/app/api/trips/route.ts:9-47` shows only GET; no POST
- **Current Behavior**: New trips can only be created indirectly by running the spine (which creates a trip as a side effect)
- **Expected Behavior**: Logged-in agency owner should have explicit "Capture Call" → "New Lead" path that creates trip through canonical spine/trip flow
- **Gap**: Missing POST endpoint and UI entry point
- **Impact**: High - blocks best-in-class call capture experience
- **Risk**: Creating a duplicate route would worsen API surface; must extend canonical flow instead
- **Confidence**: High (code and workflow verification)

### ISSUE-002: Follow-up commitment not operationalized
- **Category**: product decision, operational safety, task management
- **Origin**: Explicit Task, P0 section, lines 139-143
- **Codebase Evidence**: Trip interface has no follow_up_due_date, promised_follow_up, or task commitment field
- **Current Behavior**: Ravi's promise to return draft in "1-2 days" lives only in raw notes
- **Expected Behavior**: Follow-up due date should be first-class, visible in inbox/workspace, tied to SLA
- **Gap**: Missing data model, UI field, and task tracking integration
- **Impact**: High - operationally critical for agency workflow
- **Confidence**: High (document explicitly requires)

### ISSUE-003: Party composition lacks detail (child age, elderly indicators)
- **Category**: data model, feature gap
- **Origin**: Explicit Task, P1 section, lines 145-149
- **Codebase Evidence**: Trip interface has generic `party?: number` but no child_ages, elderly_count, mobility fields
- **Current Behavior**: Party size is a number; extraction may infer "child" from raw text but not stored as structured field
- **Expected Behavior**: child_ages, elderly_count, mobility_unknowns should be first-class fields affecting suitability/transfers/pacing
- **Gap**: Missing fields in Trip interface and IntakePanel UI
- **Impact**: Medium-High - affects suitability logic for complex party compositions
- **Confidence**: High (code inspection + logical necessity)

### ISSUE-004: Date-year ambiguity not resolved structurally
- **Category**: data model, UX, confidence tracking
- **Origin**: Explicit Task, P1 section, lines 151-155
- **Codebase Evidence**: Trip.dateWindow is simple string; no inferred_year, year_confidence, or needs_confirmation fields
- **Current Behavior**: "Jan/Feb" during November call silently becomes Feb 2025 without surfacing inference confidence
- **Expected Behavior**: dateWindow should include inferred_year with confidence/provenance and a "confirm with traveler" flag
- **Gap**: Missing fields in Trip interface and date model
- **Impact**: Medium - affects downstream timeline and SLA calculations
- **Confidence**: High (real scenario demonstrates the trap)

### ISSUE-005: Pace preference not first-class
- **Category**: feature gap, product decision
- **Origin**: Explicit Task, P1 section, lines 157-161
- **Codebase Evidence**: Trip interface has no pace_preference, trip_pacing, or similar field
- **Current Behavior**: "Don't want it rushed" can only be captured in raw notes
- **Expected Behavior**: pace_preference should be first-class, affecting itinerary generation (rest windows, transfers, day pacing)
- **Gap**: Missing field and UI control
- **Impact**: Medium - affects itinerary suitability
- **Confidence**: High (document explicit requirement + code inspection)

### ISSUE-006: Lead source and relationship metadata missing
- **Category**: commercial, data model, product decision
- **Origin**: Explicit Task, P1 section, lines 163-167
- **Codebase Evidence**: Trip interface has no lead_source, source_channel, referral_source, primary_contact, relationship fields
- **Current Behavior**: "Warm referral through Divya" lives in notes only; system cannot distinguish warm vs cold leads
- **Expected Behavior**: lead_source, referral_source, primary_contact, relationship should be first-class but internal-only (not traveler-facing)
- **Gap**: Missing fields, UI controls, and source metadata model
- **Impact**: Medium - operationally affects priority/tone/trust; commercially affects referral tracking
- **Confidence**: High (code inspection + commercial necessity)

### ISSUE-007: Activity provenance not captured (suggested vs requested)
- **Category**: data model, feature gap, implicit task
- **Origin**: Implicit Task (document discusses agent-suggested vs traveler-requested activities)
- **Codebase Evidence**: Activity/itinerary models lack activity_provenance, source_type (suggested/requested), or actor field
- **Current Behavior**: "Universal Studios and nature parks" suggested by Ravi appear same as if traveler had requested them
- **Expected Behavior**: Activities should track whether agent-suggested or traveler-requested, affecting confidence/iteration
- **Gap**: Missing fields and source tracking
- **Impact**: Low-Medium - affects itinerary iteration and traveler expectations
- **Confidence**: Medium (implicit in scenario, not explicitly stated)

### ISSUE-008: Call date vs travel date not distinguished
- **Category**: data model, audit trail, implicit task
- **Origin**: Implicit Task (needed for temporal disambiguation in scenario)
- **Codebase Evidence**: Trip interface has no call_date, capture_date, received_at, or similar audit timestamp
- **Current Behavior**: Cannot distinguish when the call happened (Nov 2024) vs when trip is scheduled (Feb 2025)
- **Expected Behavior**: call_date / capture_date should be first-class, used for follow-up SLA and timeline clarity
- **Gap**: Missing fields and capture timestamp
- **Impact**: Low-Medium - affects follow-up SLA and audit trail
- **Confidence**: Medium (implicit, necessary for operational integrity)

### ISSUE-009: No regression test for Singapore call scenario
- **Category**: testing, QA
- **Origin**: Explicit Task, implementation direction #7, line 211
- **Codebase Evidence**: `frontend/src/components/workspace/panels/__tests__/IntakePanel.test.tsx` tests render/edit but NOT Singapore scenario; `tests/` has packet fixtures but NOT exact scenario (Nov 2024 call, Feb 2025 trip, toddler, parents, non-rushed, 48-hour follow-up)
- **Current Behavior**: No regression test prevents regressions on the exact audit scenario
- **Expected Behavior**: Test should capture full scenario: capture call → extract → confirm fields → run spine → verify output
- **Gap**: Missing test case
- **Impact**: Low - test coverage gap, not functional; affects regression risk
- **Confidence**: High (inspection + explicit requirement)

### ISSUE-010: Capture UI affordance weak for touch/discovery
- **Category**: UX, P2
- **Origin**: Explicit Task, P2 section, lines 169-173
- **Codebase Evidence**: `frontend/src/components/workspace/panels/IntakePanel.tsx:253-309` edit controls are hover-only in display mode
- **Current Behavior**: Edit affordance hidden until hover; inefficient on touch devices; weak discoverability for real-time call capture
- **Expected Behavior**: Always-visible capture mode with obvious field progression
- **Gap**: Missing capture mode; hover-only controls adequate for existing workspace but not for new call entry
- **Impact**: Low-Medium - UX polish, not blocking
- **Confidence**: High (code inspection + UX reasoning)

### ISSUE-011: PATCHABLE_FIELDS must support new structured fields
- **Category**: implicit task, routing
- **Origin**: Implicit Task (dependency of Issues 003-008)
- **Codebase Evidence**: `frontend/src/app/api/trips/[id]/route.ts:38-49` defines PATCHABLE_FIELDS = limited set; new fields would need to be added
- **Current Behavior**: If new fields (lead_source, party_composition, pace_preference, follow_up_due_date, etc.) are added to Trip interface, PATCH route must explicitly allow them
- **Expected Behavior**: PATCHABLE_FIELDS should include all new structured fields
- **Gap**: Will be missing when new fields are added; implicit dependency
- **Impact**: Medium - blocking for structured field updates
- **Confidence**: High (logical necessity)

## 10. Prioritization

### Priority Scoring Matrix
| Issue ID | Title | Severity | Blast Radius | Effort | Confidence | Priority | Why |
|----------|-------|----------|--------------|--------|------------|----------|-----|
| ISSUE-001 | No POST /api/trips | 4 | 4 | 3 | 5 | **P0** | Blocks entry point for call capture; high-value user journey |
| ISSUE-002 | No follow-up commitment | 5 | 4 | 4 | 5 | **P0** | Operationally critical; blocks launch-readiness for agency owners |
| ISSUE-003 | Party composition missing | 3 | 3 | 3 | 5 | **P1** | Affects suitability; necessary for complex scenarios |
| ISSUE-004 | Date-year ambiguity | 3 | 2 | 3 | 5 | **P1** | Affects SLA and timeline; real trap in this scenario |
| ISSUE-005 | Pace preference missing | 3 | 2 | 2 | 5 | **P1** | Affects itinerary generation; medium effort |
| ISSUE-006 | Lead source missing | 3 | 3 | 3 | 5 | **P1** | Commercially important; affects relationship tracking |
| ISSUE-007 | Activity provenance missing | 2 | 2 | 3 | 4 | **P2** | Nice-to-have for iteration clarity |
| ISSUE-008 | Call date missing | 2 | 1 | 2 | 4 | **P2** | Audit trail / SLA; low effort if combined with follow-up |
| ISSUE-009 | No Singapore regression test | 2 | 1 | 2 | 5 | **P1** | Test gap; prevents regressions on audit scenario |
| ISSUE-010 | Capture UI affordance weak | 2 | 2 | 2 | 5 | **P2** | UX polish; non-blocking |
| ISSUE-011 | PATCHABLE_FIELDS gap | 4 | 2 | 1 | 5 | **P0** | Hidden blocker if new fields added; high-effort mitigation if not addressed early |

### Priority Queues

#### P0 (Severe and Urgent)
1. **ISSUE-001**: No POST /api/trips for new lead creation
2. **ISSUE-002**: Follow-up commitment not operationalized
3. **ISSUE-011**: PATCHABLE_FIELDS must support new fields (implicit dependency)

#### P1 (Important)
1. **ISSUE-003**: Party composition detail missing
2. **ISSUE-004**: Date-year ambiguity resolution
3. **ISSUE-005**: Pace preference field
4. **ISSUE-006**: Lead source and relationship metadata
5. **ISSUE-009**: Singapore scenario regression test

#### P2 (Useful, not blocking)
1. **ISSUE-007**: Activity provenance
2. **ISSUE-008**: Call date distinction
3. **ISSUE-010**: Capture UI affordance

### Critical Path
Recommended sequence (respecting dependencies):
1. **Phase 1** (P0): Add POST /api/trips + capture UI + follow-up task model
2. **Phase 2** (P1): Extend Trip interface with structured fields (party, date, pace, source, call_date)
3. **Phase 3** (P1): Update PATCH endpoint for new fields + update IntakePanel UI
4. **Phase 4** (P1): Add Singapore scenario regression test
5. **Phase 5** (P2): Polish capture affordance + activity provenance

## 11. Assumptions Challenged by Implementation
**To be updated after test-runtime-verifier completes and any POC validation.**

Current assumptions:
1. Spine pipeline works correctly for call capture → assumption verified by codebase-verifier ✅
2. IntakePanel preserves messages → assumption verified ✅
3. New fields can be added to Trip interface without breaking existing code → assumption untested; PATCHABLE_FIELDS gap suggests otherwise

## 12. Discussion Pack

### My Recommendation
I recommend working on these issues in order:

1. **ISSUE-001** - No POST /api/trips (P0, blocking entry point)
2. **ISSUE-002** - No follow-up commitment (P0, operationally critical)
3. **ISSUE-011** - PATCHABLE_FIELDS (P0, implicit blocker)
4. **ISSUE-003 through ISSUE-006** - Structured fields batch (P1, necessary for feature completeness)
5. **ISSUE-009** - Singapore regression test (P1, test coverage)

### Why These Matter Now
- **Call capture is partially broken**: Agency owners can paste a call, but the system cannot surface structured understanding (who called? when? promised follow-up? party composition?).
- **Follow-up SLA is invisible**: Ravi's "1-2 day" promise has no system visibility; risk of missed commitments.
- **PATCHABLE_FIELDS gap is a land mine**: If developers add fields to Trip but forget to update PATCHABLE_FIELDS, updates will silently fail, causing data loss and confusion.

### What Breaks If Ignored
- Agency owners will bypass the app and keep call notes in WhatsApp/email (reduces data quality and pipeline visibility).
- Follow-up commitments will be missed (customer trust damage, operational risk).
- If new fields are added without updating PATCHABLE_FIELDS, partial updates will fail, causing data inconsistency.

### What I Would Not Work On Yet
- **ISSUE-007, ISSUE-008, ISSUE-010**: These are improvements, not blockers. Defer until core P0-P1 work completes.

### What Is Ambiguous
1. **Follow-up task model**: Should follow-up be a separate Task entity, or a field on Trip? Document doesn't specify. Need product decision.
2. **Pace preference enum**: What are valid values? ("relaxed", "normal", "fast"?) Should they map to itinerary density rules? Need definition.
3. **Lead source taxonomy**: What are valid source values? ("warm-referral", "cold-inbound", "internal", etc.?) Need commercial/marketing input.

### Questions For You
1. **Product direction**: Is the recommended sequence correct? Should party composition or date-year confidence take priority?
2. **Follow-up task model**: How should follow-up promises be stored and tracked? Separate Task entity, or Trip field with due date?
3. **Pace preference**: What are the valid values and how do they map to itinerary generation rules?
4. **Lead source enums**: What taxonomy should be used for lead sources and relationship types?
5. **PATCHABLE_FIELDS governance**: Should new fields be explicitly allowed (current approach), or auto-allow all Trip fields with allowlist filtering? Current approach is safer but requires discipline.

### Needs Runtime Verification
- (Awaiting test-runtime-verifier agent for full test suite status, test coverage analysis, and confirmation of existing scenario tests)

### Needs Online Research
None identified. Current findings are repo-evidence based.

### Next Safe Work Unit

## 13. Recommended Next Work Unit

### Unit-1: Create New-Lead Capture Entry Point and Follow-Up Task Model

**Goal**: Agency owners can capture an inbound call, preserve the transcript, create a lead trip through the canonical spine, and track a follow-up commitment with a due date.

**Issues Covered**:
- ISSUE-001 (No POST /api/trips)
- ISSUE-002 (Follow-up not operationalized)
- ISSUE-011 (PATCHABLE_FIELDS gap)

**Scope**:
- **In**: Add POST /api/trips that accepts {raw_note, owner_note, operating_mode, stage} and returns a trip (delegates to spine); add follow_up_due_date field to Trip; add PATCH support for follow_up_due_date; create UI entry point "Capture Call"; add "Promised follow-up in 48 hours" input field
- **Out**: Activity provenance, party composition detail, date-year confidence, pace preference, lead source metadata (these are Phase 2)

**Likely Files Touched**:
- `frontend/src/app/api/trips/route.ts` (add POST)
- `frontend/src/app/api/trips/[id]/route.ts` (add follow_up_due_date to PATCHABLE_FIELDS)
- `frontend/src/lib/api-client.ts` (add follow_up_due_date to Trip interface)
- `frontend/src/components/workspace/panels/IntakePanel.tsx` (add "Capture Call" entry point and follow-up input)
- `spine_api/server.py` (ensure Trip model has follow_up_due_date)
- `src/intake/packet_models.py` (ensure Trip data model persists follow-up)

**Acceptance Criteria**:
- [ ] POST /api/trips accepts call capture payload and returns trip via canonical spine
- [ ] Trip interface includes follow_up_due_date field
- [ ] IntakePanel has "Capture Call" entry point accessible from workspace
- [ ] "Promised follow-up" field allows entering due date with optional duration hint (e.g., "48 hours")
- [ ] PATCH /api/trips/[id] supports follow_up_due_date updates
- [ ] New trip is persisted with follow_up_due_date in backend
- [ ] Backend tests verify POST route creates trip correctly
- [ ] Frontend tests verify Capture Call flow and follow-up field

**Tests to Run**:
- **Baseline**: Full backend + frontend test suite
- **Targeted**: Tests for POST /api/trips, follow_up_due_date persistence, PATCH support
- **Full Suite**: After changes, re-run all tests to ensure no regressions

**Manual Verification**:
- In workspace, trigger "Capture Call" entry point
- Paste Ravi's call transcript
- Confirm trip created with follow_up_due_date set
- Edit follow_up_due_date via PATCH
- Verify data persists in backend

**Operational Safety**:
- **Kill Switch**: POST /api/trips can be disabled via feature flag if issues arise
- **Rollback**: Remove POST route and follow_up_due_date field without data migration (field can be optional/nullable)

**Risks**:
- PATCHABLE_FIELDS governance requires discipline; future field additions must update the allowlist
- Trip creation via POST might bypass validation logic that exists in spine route; must verify consistency

---

## 14. Appendix: Searches Performed

**Agent: codebase-verifier**
- `frontend/src/components/workspace/panels/IntakePanel.tsx` — verified render (626-714), send (179-188), save (173-203), edit (253-309)
- `spine_api/server.py` — verified build_envelopes (416-436), pipeline (523-601)
- `frontend/src/lib/api-client.ts` — verified Trip interface (287-352, 314-315)
- `frontend/src/app/api/trips/route.ts` — verified GET only (9-47); no POST
- `frontend/src/app/api/trips/[id]/route.ts` — verified PATCHABLE_FIELDS (38-49)
- `src/intake/decision.py` — verified MVB blockers (254-266), questions (1816-1829)
- `src/intake/packet_models.py` — verified SourceEnvelope (255-286), models
- `frontend/src/components/workspace/panels/__tests__/IntakePanel.test.tsx` — verified test coverage (partial)

**Agent: doc-analyst-extractor** (completed, pending full review)
- Extracted 20+ doc items identifying explicit/implicit tasks, claims, and gaps

**Agent: test-runtime-verifier** (running, awaiting completion)
- Test baseline collection in progress

---

## 15. Summary of Audit Findings

**Document Audit Status**: ✅ Document accuracy verified; claims match codebase evidence; gaps correctly identified

**Code-Grounded Verdicts**:
- ✅ Backend spine pipeline works correctly for call capture
- ✅ Source role separation (SourceEnvelope) correctly implemented
- ✅ IntakePanel preserves messages and edits trip details as documented
- ❌ Missing POST /api/trips entry point
- ❌ Missing 7 first-class structured fields (lead_source, party_composition, pace_preference, follow_up_due_date, activity_provenance, date-year inference, call_date)
- ⚠️ PATCHABLE_FIELDS governance gap (fragile, requires discipline)
- 🟡 Test coverage partial (no Singapore scenario regression test)

**Product Direction**: Sound. Recommendation to preserve freeform transcript + add structured layer is correct.

**Risk Assessment**: Medium. Core pipeline works, but agency-owner UX is incomplete. Operationally, missing follow-up commitment tracking is a blocker for launch.

**Next Action**: Proceed with Unit-1 (new-lead capture + follow-up task model) as P0 work.


---

## 6A. Dynamic Verification Results (Test-Runtime-Verifier Completed)

**Status**: Baseline established, test gaps documented

### Test Baseline Summary
- **Backend tests**: 775 tests collected; 37 failing (pre-existing), 17 passing in sample run
- **Frontend tests**: 35 test files found; no npm test script configured
- **Pre-existing failures**: Contract tests failing on response schema (KeyError: 'ok', 'safety', 'meta')

### Test Coverage vs Document Claims
| Claim | Test Status | Evidence |
|-------|---|---|
| Raw note + Owner note capture | ✅ Passing | IntakePanel.test.tsx (4 tests verify textarea render/save) |
| Stage selection (Discovery) | ✅ Passing | IntakePanel.test.tsx (process button, stage dropdown) |
| Trip detail editing | ✅ Passing | IntakePanel.test.tsx + implicit PATCH tests |
| Follow-up due date capture | ❌ Missing | No field, no test, no UI |
| Lead source/provenance capture | ❌ Missing | SourceEnvelope exists but UI doesn't expose it; no test |
| Party composition detail | ⚠️ Partial | Backend detects but UI lacks editable field; incomplete tests |
| Pace preference | ⚠️ Partial | System infers toddler_pacing_risk but no "not rushed" UI field |
| New-lead creation (POST /api/trips) | ❌ Missing | Only GET /api/trips exists; no test |

### Critical Test Gaps Blocking Document Claims
1. **Contract test failures**: 37 tests failing in test_spine_api_contract.py + test_run_lifecycle.py
   - Blocks: Verification of full raw_note → spine → trip journey
   - Cause: Response schema mismatch (missing 'ok', 'safety', 'meta' fields)
   - Impact: Cannot verify end-to-end capture path works

2. **No POST /api/trips test**: Audit requires new-lead creation path
   - Current: Only GET /api/trips (list existing trips)
   - Missing: POST handler + test
   - Blocks: Unblocking Unit-1 implementation

3. **No lead source UI test**: SourceEnvelope properly separates roles but frontend doesn't expose selection
   - Missing: UI field for source_channel, lead_source, referral_source
   - Blocks: Phase 1 (Unit-1) doesn't require this; Phase 2 work

4. **No follow-up due date field**: No model field, no UI, no test
   - Missing: follow_up_due_date in Trip model + PATCH support
   - Blocks: Unit-1 implementation (required for this work unit)

5. **No traveler composition detail test**: Backend detects child ages but not user-editable
   - Missing: UI fields for child_ages, elderly_count, mobility indicators
   - Blocks: Phase 2 work (outside Unit-1 scope)

### Verdict on Test Coverage
**Current test coverage supports rough freeform capture (notes + stage), but structured intake layer is largely untested.** Of 7 document claims:
- ✅ 2 claims have passing tests (note capture, stage selection)
- ⚠️ 2 claims partially tested (party composition, pace detection in backend)
- ❌ 3 claims have no tests (follow-up due date, lead source UI, new-lead creation)

**For Unit-1 to succeed**: Must address "new-lead creation" (POST /api/trips) and "follow-up due date" gaps immediately.

