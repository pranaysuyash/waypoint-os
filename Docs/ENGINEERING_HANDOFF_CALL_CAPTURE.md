# Engineering Handoff: Call Capture & Follow-Up Task Model (Unit-1)

**Date**: 2026-04-28  
**Status**: Ready for Implementation  
**Phase**: P0 (Blocker for Agency-Owner Launch Readiness)  
**Effort Estimate**: Medium (3-4 sprints, 2 engineers)  

---

## Executive Summary

Ravi (an agency owner) cannot currently capture an inbound phone call as a new lead in the workspace UI. The current app requires trips to be created indirectly through the spine run, which works but is not discoverable or agency-owner-friendly.

**This unit unblocks the core workflow** by:
1. Adding `POST /api/trips` to create new leads directly through the canonical spine
2. Adding `follow_up_due_date` field to track promised follow-ups with due dates
3. Creating a "Capture Call" entry point in the workspace
4. Ensuring `PATCHABLE_FIELDS` includes new operational fields

**Out of scope for this unit**: Party composition detail, date-year confidence, pace preference, lead source metadata (Phase 2 work).

---

## Current State Evidence

### What Works Today
- IntakePanel renders and saves messages (customerMessage, agentNotes): `frontend/src/components/workspace/panels/IntakePanel.tsx:173-203`
- Spine pipeline runs correctly: `spine_api/server.py:519-601`
- SourceEnvelope correctly separates source roles: `spine_api/server.py:416-436`
- Trip details can be edited: `frontend/src/components/workspace/panels/IntakePanel.tsx:253-309`

### What's Missing
- No `POST /api/trips` route: `frontend/src/app/api/trips/route.ts` (lines 9-47) has only GET
- No `follow_up_due_date` in Trip interface: `frontend/src/lib/api-client.ts:287-352`
- No "Capture Call" entry point in workspace UI
- No `follow_up_due_date` in PATCHABLE_FIELDS: `frontend/src/app/api/trips/[id]/route.ts:38-49`

### Verified Code Paths
- **Create path**: SpineRunRequest → build_envelopes() → spine.run() → trip persisted
- **Save path**: IntakePanel → PATCH /api/trips/[id] → backend updates message fields
- **Backend models**: Trip in spine_api, CanonicalPacket in src/intake, SourceEnvelope correctly typed

---

## Design Decisions

### 1. New-Lead Creation Route (POST /api/trips)

**Decision**: POST /api/trips delegates to the canonical spine pipeline, not a separate route.

**Why**: Reuses proven code path, prevents duplicate validation logic, maintains consistency.

**Implementation**:
```typescript
// frontend/src/app/api/trips/route.ts - ADD THIS
export async function POST(req: Request) {
  const body = await req.json();
  
  const spinRequest: SpineRunRequest = {
    raw_note: body.raw_note,           // Required: raw call transcript
    owner_note: body.owner_note ?? "",  // Optional: Ravi's internal notes
    structured_json: body.structured_json ?? null,
    itinerary_text: body.itinerary_text ?? null,
    stage: body.stage ?? "discovery",   // Default to discovery for new leads
    operating_mode: body.operating_mode ?? "normal_intake",
    strict_leakage: body.strict_leakage ?? false,
    scenario_id: body.scenario_id ?? null,
  };

  // Delegate to spine pipeline (existing logic)
  const result = await executeSpinePipeline(spinRequest);
  
  // Pipeline returns trip; POST should return it
  return new Response(JSON.stringify(result.trip), { 
    status: 201,
    headers: { "Content-Type": "application/json" },
  });
}
```

**Request Payload**:
```json
{
  "raw_note": "Caller says... [verbatim transcript]",
  "owner_note": "Ravi's context... [internal only]",
  "stage": "discovery",
  "operating_mode": "normal_intake",
  "follow_up_due_date": "2024-11-28T12:00:00Z"
}
```

**Response** (201 Created):
```json
{
  "id": "trip-uuid",
  "destination": null,
  "origin": null,
  "type": "request",
  "party": null,
  "dateWindow": null,
  "budget": null,
  "stage": "discovery",
  "status": "open",
  "customerMessage": "...",
  "agentNotes": "...",
  "rawInput": "...",
  "follow_up_due_date": "2024-11-28T12:00:00Z",
  "createdAt": "2024-11-22T10:15:00Z",
  "updatedAt": "2024-11-22T10:15:00Z"
}
```

### 2. Follow-Up Due Date Field

**Decision**: Store as ISO 8601 timestamp, optional, user-settable during capture or edit.

**Why**: Standard timestamp format; optional allows backward compatibility; user-settable gives agency control.

**Backend Model** (`spine_api/server.py`):
```python
class Trip:
    id: str
    destination: str | None
    # ... existing fields ...
    follow_up_due_date: datetime | None = None  # NEW
    created_at: datetime
    updated_at: datetime
```

**Frontend Model** (`frontend/src/lib/api-client.ts`):
```typescript
export interface Trip {
  id: string;
  destination?: string;
  // ... existing fields ...
  followUpDueDate?: string; // ISO 8601 timestamp
  createdAt: string;
  updatedAt: string;
}
```

### 3. Capture Call Entry Point

**Decision**: New "Capture Call" button in workspace, opens a side panel with raw_note + owner_note input, then delegates to POST /api/trips.

**Why**: Discoverable, clearly labeled, guides Ravi's workflow (call → capture → results).

**UI Location**: `frontend/src/components/workspace/panels/IntakePanel.tsx` (add new section or modal).

**UX Flow**:
1. Workspace shows "Capture Call" button (always visible, not hover-only)
2. Click → side panel opens with:
   - "Call Transcript" text area (placeholder: "Paste or type what the caller said")
   - "Internal Notes" text area (placeholder: "Your assumptions, follow-up commitment, questions to ask")
   - "Follow-Up Due" datetime input (optional, default to 48 hours from now)
   - "Stage" selector (default: "discovery")
   - "Create Lead" button
3. Submit → POST /api/trips
4. On success → redirect to trip details (same as spine-run flow)
5. On error → show error message in side panel

### 4. PATCHABLE_FIELDS Update

**Decision**: Explicitly add `follow_up_due_date` to PATCHABLE_FIELDS; document the governance pattern.

**Why**: Prevents silent failures if field is omitted; explicit allowlist is safer than blocklist.

**Implementation** (`frontend/src/app/api/trips/[id]/route.ts`):
```typescript
const PATCHABLE_FIELDS = [
  "customerMessage",
  "agentNotes",
  "budget",
  "party",
  "dateWindow",
  "origin",
  "destination",
  "type",
  "state",
  "status",
  "follow_up_due_date",  // NEW
] as const;
```

**Governance Note** (add comment):
```typescript
// IMPORTANT: When adding new Trip fields, update PATCHABLE_FIELDS explicitly.
// This list is an allowlist to prevent accidental PATCH of immutable fields (id, createdAt, etc).
// If a new field should be patchable, add it here AND ensure backend validation is in place.
```

---

## Implementation Sequence

### Phase A: Backend Models & Routes (Week 1)

**Files to Modify**:
1. `spine_api/server.py`
   - Add `follow_up_due_date: Optional[datetime]` to Trip model
   - Ensure Trip persists this field to database
   - Add logging for follow_up_due_date in pipeline

2. `src/intake/packet_models.py`
   - Update Trip dataclass to include follow_up_due_date if stored at spine level

3. Database schema (if needed)
   - Add `follow_up_due_date` column to trips table (nullable)
   - Verify migration runs correctly

4. `frontend/src/app/api/trips/route.ts`
   - Add POST handler that accepts raw_note, owner_note, follow_up_due_date
   - Delegates to canonical spine pipeline
   - Returns Trip with 201 Created status

5. `frontend/src/app/api/trips/[id]/route.ts`
   - Add "follow_up_due_date" to PATCHABLE_FIELDS
   - Add comment on governance pattern

**Tests** (write before or alongside code):
- `tests/test_api_trips_post.py`: POST /api/trips creates trip via spine
- `tests/test_api_trips_patch.py`: PATCH follow_up_due_date updates correctly
- Backend: Verify follow_up_due_date persists and is readable

### Phase B: Frontend Models & Types (Week 1)

**Files to Modify**:
1. `frontend/src/lib/api-client.ts`
   - Add `followUpDueDate?: string` to Trip interface
   - Update TypeScript types for consistency

**Tests**:
- Type check: TypeScript should compile without errors
- API client tests: Mock API returns followUpDueDate and types correctly

### Phase C: UI - Capture Call Entry Point (Week 2)

**Files to Modify**:
1. `frontend/src/components/workspace/panels/IntakePanel.tsx`
   - Add "Capture Call" button (visible, not hover-only)
   - Create CapturCallPanel or CapturCallModal component
   - Implement form: raw_note, owner_note, follow_up_due (with "48 hours from now" default)
   - On submit: POST /api/trips with spinRequest
   - On success: navigate to new trip details
   - On error: show error toast/message

2. `frontend/src/components/workspace/panels/CaptureCallPanel.tsx` (NEW)
   - Reusable capture panel (can be modal or sidebar)
   - Accepts callbacks: onSuccess(trip), onError(error)
   - Shows loading state during submit
   - Validates raw_note is not empty

**Tests**:
- `frontend/src/components/workspace/panels/__tests__/CaptureCallPanel.test.tsx`
  - Test render of form fields
  - Test submit with valid data
  - Test error handling
  - Test 48-hour default for follow_up_due_date

### Phase D: Integration & Verification (Week 2)

**Files to Verify**:
1. Run existing IntakePanel tests to ensure no regressions
2. Run new POST /api/trips tests
3. Run new PATCH /api/trips tests
4. Full backend test suite
5. Full frontend test suite
6. Manual workflow test: Capture call → view trip → edit follow_up_due_date → persist

---

## Acceptance Criteria

### Backend
- [ ] POST /api/trips accepts {raw_note, owner_note, stage, operating_mode, follow_up_due_date}
- [ ] POST returns 201 Created with Trip object including follow_up_due_date
- [ ] Trip model includes follow_up_due_date: Optional[datetime]
- [ ] follow_up_due_date persists to database
- [ ] PATCH /api/trips/[id] with follow_up_due_date updates correctly
- [ ] follow_up_due_date in PATCHABLE_FIELDS
- [ ] Error handling: POST returns 400 if raw_note missing, 401 if unauthorized, 500 if spine fails
- [ ] Database migration runs without errors
- [ ] All backend tests pass (pre-existing + new)

### Frontend
- [ ] Trip interface includes followUpDueDate?: string
- [ ] POST /api/trips sends raw_note, owner_note, follow_up_due_date
- [ ] "Capture Call" button visible in workspace (not hover-only)
- [ ] Capture panel opens with raw_note, owner_note, follow_up_due inputs
- [ ] follow_up_due_date defaults to 48 hours from now (optional)
- [ ] Submit POST /api/trips, handles 201 response
- [ ] On success: navigate to trip details
- [ ] On error: show error message (e.g., "Failed to create lead. Please try again.")
- [ ] IntakePanel existing tests still pass
- [ ] New CaptureCallPanel tests pass
- [ ] Full frontend test suite passes
- [ ] TypeScript compiles without errors
- [ ] No console errors or warnings in capture flow

### Manual Verification
- [ ] Capture a call: "Caller says they want Singapore..."
- [ ] Verify trip created with stage=discovery
- [ ] Verify follow_up_due_date set to 48 hours from capture
- [ ] Navigate to trip details
- [ ] Edit follow_up_due_date in details panel
- [ ] Verify update via PATCH
- [ ] Refresh page; verify changes persisted

### Integration
- [ ] Full test suite passes (backend + frontend)
- [ ] No regressions in existing workspace workflows
- [ ] Capture flow works end-to-end: call → trip created → follow_up_due visible → can edit

---

## Risk Mitigation

### Risk 1: PATCHABLE_FIELDS Governance
**Risk**: Developers add new Trip fields but forget to update PATCHABLE_FIELDS → silent failures.

**Mitigation**:
- Add explicit code comment on governance pattern
- Document in DEVELOPMENT.md or CONTRIBUTING.md
- Test that new fields fail to PATCH if not in allowlist (intentional validation)
- Code review checklist: "If Trip fields changed, verify PATCHABLE_FIELDS updated"

### Risk 2: Spine Pipeline Delegation
**Risk**: POST /api/trips delegates to spine; if spine fails, user sees error but trip may be partially created.

**Mitigation**:
- Verify spine transaction semantics: does it create Trip before running, or after?
- If Trip created before pipeline success, ensure rollback on failure
- Test failure cases: invalid raw_note, spine crashes, database fails
- Error messages should indicate what failed

### Risk 3: Follow-Up Due Date Persistence
**Risk**: follow_up_due_date column added but migration fails on production data.

**Mitigation**:
- Migration must make column nullable (no NOT NULL constraint)
- Test migration on staging with real data volume
- Rollback procedure: Drop column if deployment fails
- Verify PATCH endpoint gracefully handles null values

### Risk 4: Backward Compatibility
**Risk**: POST /api/trips breaks existing code that uses GET /api/trips.

**Mitigation**:
- GET /api/trips unchanged (list existing trips)
- POST /api/trips is new, doesn't break GET
- Verify no code calls POST /api/trips expecting different behavior

---

## Test Plan

### Unit Tests (Backend)
**File**: `tests/test_api_trips_post.py`
```python
def test_post_trips_creates_trip_via_spine():
    """POST /api/trips with raw_note creates trip through canonical spine."""
    response = POST("/api/trips", {
        "raw_note": "Caller wants Singapore...",
        "owner_note": "Follow-up in 48 hours",
        "follow_up_due_date": "2024-11-28T12:00:00Z"
    })
    assert response.status_code == 201
    assert response.json()["destination"] is None  # Spine extracts later
    assert response.json()["follow_up_due_date"] == "2024-11-28T12:00:00Z"

def test_post_trips_missing_raw_note_returns_400():
    """POST without raw_note returns 400 Bad Request."""
    response = POST("/api/trips", {"owner_note": "..."})
    assert response.status_code == 400

def test_patch_trips_follow_up_due_date():
    """PATCH follow_up_due_date updates correctly."""
    trip_id = "trip-123"
    response = PATCH(f"/api/trips/{trip_id}", {
        "follow_up_due_date": "2024-11-29T12:00:00Z"
    })
    assert response.status_code == 200
    assert response.json()["follow_up_due_date"] == "2024-11-29T12:00:00Z"
```

### Unit Tests (Frontend)
**File**: `frontend/src/components/workspace/panels/__tests__/CaptureCallPanel.test.tsx`
```typescript
describe("CaptureCallPanel", () => {
  it("renders form fields: raw_note, owner_note, follow_up_due", () => {
    // Test form renders
  });

  it("defaults follow_up_due_date to 48 hours from now", () => {
    // Test default calculation
  });

  it("submits POST /api/trips on form submit", async () => {
    // Mock POST, verify payload
  });

  it("calls onSuccess(trip) on 201 response", () => {
    // Verify callback
  });

  it("shows error message on POST failure", () => {
    // Test error handling
  });
});
```

### Integration Tests
**File**: `tests/test_capture_call_integration.py`
```python
def test_capture_call_flow_end_to_end():
    """Full workflow: POST call → verify trip created → PATCH follow_up → verify persisted."""
    # 1. POST /api/trips with call data
    post_response = POST("/api/trips", {...})
    trip_id = post_response.json()["id"]
    
    # 2. Verify trip created
    get_response = GET(f"/api/trips/{trip_id}")
    assert get_response.status_code == 200
    
    # 3. PATCH follow_up_due_date
    patch_response = PATCH(f"/api/trips/{trip_id}", {
        "follow_up_due_date": "2024-11-29T15:00:00Z"
    })
    assert patch_response.status_code == 200
    
    # 4. Verify persistence
    verify_response = GET(f"/api/trips/{trip_id}")
    assert verify_response.json()["follow_up_due_date"] == "2024-11-29T15:00:00Z"
```

### Manual Test Scenarios
1. **Happy path**: Capture call → Trip created → Follow-up visible
2. **Error path**: Capture with empty raw_note → Shows error message
3. **Edit path**: Create trip → Edit follow_up_due_date → Verify persisted
4. **Integration**: Capture call → Verify spine extracts trip details (destination, party, etc.)

---

## Rollback & Kill Switch

### Rollback Procedure
If this unit is released but causes issues:

1. **Immediate**: Feature flag to disable POST /api/trips (if framework supports)
   - Return 405 Method Not Allowed if flag disabled
   - Existing trips still readable

2. **Short term**: Remove POST handler from route.ts
   - Revert commit, redeploy
   - No data loss; follow_up_due_date field persists but unused

3. **Data**: follow_up_due_date column in database
   - If rollback needed, column can be left (nullable, harmless)
   - Or drop via migration

### Kill Switch
Add environment variable to disable POST:
```typescript
const allowPostTrips = process.env.ALLOW_POST_TRIPS !== 'false';

export async function POST(req: Request) {
  if (!allowPostTrips) {
    return new Response(JSON.stringify({ error: "POST disabled" }), { 
      status: 405 
    });
  }
  // ... implementation
}
```

---

## Documentation Updates

### For Developers
- **DEVELOPMENT.md**: Add section on "Adding New Trip Fields" with PATCHABLE_FIELDS governance
- **API.md** (if exists): Document POST /api/trips endpoint
- **Code comments**: Add governance note in route handlers

### For Agency Owners / Users
- **In-app help**: Add tooltip on "Capture Call" button explaining the workflow
- **Onboarding**: Video or walkthrough showing how to capture a call
- **Release notes**: Highlight new "Capture Call" feature

---

## Success Metrics

### Code Quality
- [ ] TypeScript compiles without errors
- [ ] All tests pass (backend + frontend)
- [ ] No console errors or warnings
- [ ] Code review approved by 2 reviewers

### Functionality
- [ ] Capture Call workflow is discoverable and intuitive
- [ ] follow_up_due_date persists and is editable
- [ ] Error messages are clear and actionable

### Performance
- [ ] POST /api/trips completes in <2 seconds (same as spine run)
- [ ] PATCH /api/trips with follow_up_due_date completes in <500ms

### User Experience
- [ ] Agency owner can capture a call without referring to documentation
- [ ] follow_up_due_date defaults to reasonable value (48 hours)
- [ ] Errors are shown as user-friendly messages, not stack traces

---

## Open Questions & Product Decisions

### Q1: Should "Capture Call" be a separate page, modal, or sidebar panel?
**Current recommendation**: Sidebar panel (non-blocking, can be dismissed, user can reference call transcript while filling form).

### Q2: Should follow_up_due_date be tied to a Task entity, or just a Trip field?
**Current recommendation**: Trip field (simpler, unblocks this unit). Task tying can be Phase 2 work.

### Q3: Should follow_up_due_date have a user-facing label like "Promise to follow up by:" or just "Follow-up due date"?
**Current recommendation**: "Promise to follow up by:" (matches business language; UX-forward).

### Q4: Should POST /api/trips auto-set stage to "discovery", or require user to select?
**Current recommendation**: Default to "discovery" but allow override (most calls are discovery; advanced users can change).

---

## References

**Related Documents**:
- Audit: `./Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md`
- Session Audit Report: `/Users/pranay/.copilot/session-state/eb416035-55dd-4e0f-9af1-1b1c851925a3/files/AUDIT_REPORT.md`

**Code References**:
- IntakePanel: `frontend/src/components/workspace/panels/IntakePanel.tsx:541-678` (render)
- POST endpoint location: `frontend/src/app/api/trips/route.ts:9-47` (add POST here)
- PATCHABLE_FIELDS: `frontend/src/app/api/trips/[id]/route.ts:38-49` (update allowlist)
- Trip interface: `frontend/src/lib/api-client.ts:287-352` (add followUpDueDate)
- Spine delegation: `spine_api/server.py:519-601` (already works)

---

## Approval & Sign-Off

**Handoff created by**: Random Document Audit (2026-04-28)  
**Ready for implementation**: Yes  
**Estimated effort**: 3-4 sprints, 2 engineers  
**Dependency blockers**: None (can start immediately)  
**Phase**: P0 (unblocks agency-owner launch readiness)

**Engineering lead review**: [ ] Approved / [ ] Needs clarification / [ ] Concerns

