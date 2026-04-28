# Phase 3+ Roadmap: Call Capture → Decision Management & Operator Controls

**Status:** Research Complete  
**Date:** 2026-04-28  
**Based On:** DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md + codebase exploration

---

## Executive Summary

Unit-1 and Phase 2 implemented the **call capture layer** (7 audit findings: raw note, owner notes, follow-up date, party composition, pace preference, date confidence, lead source). 

The audit revealed **4 major gaps** that Phase 3-5 must address:

1. **Suitability Signals** (Why was this decision made?) — Operators can't see decision reasoning
2. **Override Controls** (Can I change this?) — Operators can't modify system decisions  
3. **Follow-up Workflow** (Did I follow up?) — No reminders or tracking
4. **Activity Provenance** (Agent vs Traveler?) — Suggested vs requested activities mixed

This roadmap prioritizes these gaps by **business impact** and **effort**, with **no blocking dependencies**.

---

## Phase 3: Suitability Signal Rendering (P0 - Critical)

### Problem
When the spine generates a trip recommendation, operators can't see *why* destinations were chosen or what risks were flagged. The system produces decisions but not explanations.

**Impact:** Operators lose trust; they can't confidently present itineraries to travelers.

### Existing Code
- `frontend/src/app/workspace/[tripId]/suitability/page.tsx` exists (stub)
- `frontend/src/components/workspace/panels/SuitabilitySignal.tsx` exists (170 lines)
- Backend returns `suitability_signals` in trip response

### What Phase 3 Delivers

**Suitability Signal Renderer:**
- Display all confidence/suitability flags from spine decisions
- Tier 1 (red): Critical risks blocking the trip
- Tier 2 (yellow/gray): Medium/low concerns, informational
- Confidence scores per flag
- Drill-down to "why this flag was raised"

**Timeline Integration:**
- Show when suitability flags were set
- Show confidence score evolution
- Allow operators to see decision progression

**Example UI:**
```
🔴 CRITICAL: Elderly Mobility Risk
   Confidence: 85%
   Reason: Parent age >70 + trip includes trekking
   Source: Extracted from party_composition="2 adults, 2 parents age 70+"

🟡 HIGH: Visa Processing Risk
   Confidence: 60%
   Reason: 5 nationalities, Feb travel window (8 weeks)
   Source: Inferred from origin diversity

🟢 LOW: Child Nap Conflict
   Confidence: 40%
   Reason: 1.7-year-old may need afternoon naps; 2+ daily activities
   Source: Detected in party_composition
```

### Acceptance Criteria

- ✅ All spine-generated suitability signals displayed
- ✅ Color-coded by severity (red/yellow/green)
- ✅ Confidence scores visible
- ✅ Drill-down shows decision reasoning
- ✅ Timeline view shows signal history
- ✅ Dark mode support
- ✅ Mobile responsive
- ✅ Tests: 10+ unit tests, 5+ E2E tests

### Effort Estimate

- **Backend:** 1-2 hours (ensure signals are being returned from spine)
- **Frontend:** 3-4 hours (component + timeline integration + tests)
- **Testing:** 2-3 hours
- **Total:** 6-9 hours (~1 day)

### Dependencies

- ✅ None — spiney already generates suitability_signals
- ✅ Phase 1 call capture provides context

### Success Metrics

- Operators can see at least 3 suitability flags per typical trip
- Confidence scores are visible and understandable
- Signal history shows in timeline
- No errors in console

---

## Phase 4: Override Controls & Decision Modification (P0 - Critical)

### Problem
When suitability flags are displayed, operators have **no way to change them**. If the system says "elderly mobility risk" but the client confirmed they want to trek, the operator is stuck. They can't override the system's decision.

**Impact:** Features become blockers instead of helpers. Operators work around the system instead of through it.

### Existing Code
- `frontend/src/components/workspace/panels/OverrideTimelineEvent.tsx` exists (component ready)
- Backend API endpoints not yet implemented
- No UI buttons to trigger overrides

### What Phase 4 Delivers

**Override UI:**
- "Override" button next to each suitability flag
- Modal dialog asking for:
  - Action: Suppress / Downgrade / Acknowledge
  - Reason: Why are you overriding? (required)
  - Confirmation: "This will be logged and visible to safety review"

**Backend Endpoints:**
- `POST /api/trips/{id}/overrides` — Create override
- `GET /api/trips/{id}/overrides` — Fetch all overrides
- `DELETE /api/trips/{id}/overrides/{override_id}` — Revert override (admins only)

**Timeline Entry:**
- New "Override" event in TimelinePanel
- Shows: time, flag, action, reason, who overrode

**Example:**
```
User clicks "Override" on "Elderly Mobility Risk"
↓
Modal appears:
  "Why are you overriding this flag?"
  Action: [Downgrade from CRITICAL to HIGH]
  Reason: [Client confirmed they want to trek. Parents are experienced hikers.]
  [Cancel] [Override]
↓
Backend logs override event:
  timestamp: 2026-04-28T12:30:00Z
  stage: override
  flag: elderly_mobility_risk
  action: downgrade
  original_severity: critical
  new_severity: high
  reason: Client confirmed they want to trek. Parents are experienced hikers.
  overridden_by: agent_ravi
↓
Timeline shows:
  12:30 | Override | elderly_mobility_risk downgraded from CRITICAL to HIGH
         | Reason: Client confirmed they want to trek. Parents are experienced hikers.
```

### Acceptance Criteria

- ✅ Override button visible next to each suitability flag
- ✅ Override modal captures action + reason + confirmation
- ✅ Backend stores override with audit trail
- ✅ Override event appears in timeline
- ✅ Overrides persist across sessions
- ✅ Admins can revert overrides
- ✅ Dark mode support
- ✅ Tests: 15+ unit tests, 8+ E2E tests

### Effort Estimate

- **Backend:** 3-4 hours (override endpoints, database schema, audit trail)
- **Frontend:** 4-5 hours (UI + modal + timeline integration)
- **Testing:** 3-4 hours
- **Database Migration:** 1-2 hours
- **Total:** 11-15 hours (~2 days)

### Dependencies

- ✅ Phase 3 (suitability rendering) should be complete first
- ✅ No blocking dependencies otherwise

### Success Metrics

- Operators can override at least 3 typical suitability flags
- Override reason is captured and auditable
- Overrides show in timeline with full details
- Admin can view override audit log
- No data loss on database migration

---

## Phase 5: Follow-up Workflow & Reminders (P1 - High)

### Problem
When Ravi says "I'll follow up in 2 days", the system doesn't remind him. The call capture captures `follow_up_due_date`, but there's no notification system.

**Impact:** Promises to travelers are broken. Agency loses trust.

### What Phase 5 Delivers

**Follow-up Dashboard:**
- List of all trips with follow-up due dates
- Color-coded: Green (due in 3+ days), Yellow (due today), Red (overdue)
- Quick "Mark Done" button when follow-up is completed
- Email/Slack notifications when follow-up is due

**Notification System:**
- 24 hours before due date: "Friendly reminder: 1 day until follow-up on Singapore trip"
- On due date: "Follow-up due today: Singapore trip"
- Every day overdue: "Overdue: Singapore trip (1 day late)"

**Follow-up Event Logging:**
- When operator clicks "Mark Done", log the completion
- Capture: date completed, status (completed/escalated/cancelled)
- Timeline shows follow-up completion event

**Email Template:**
```
Hi Ravi,

You promised to follow up with Pranay about the Singapore family trip by tomorrow (April 29).

Trip Details:
  - Destination: Singapore
  - Travelers: 5 (2 adults, 1 toddler, 2 parents)
  - Travel Dates: ~Feb 9-14, 2025
  - Pace: Relaxed
  - Status: Awaiting draft itinerary

[View Trip in Workspace] [Mark as Done] [Reschedule]

Thanks,
Waypoint OS
```

### Acceptance Criteria

- ✅ Follow-up dashboard shows all due trips
- ✅ Color-coding by urgency (green/yellow/red)
- ✅ Email notifications 24h before, on due date, daily if overdue
- ✅ "Mark Done" button logs completion
- ✅ Follow-up events visible in timeline
- ✅ Can reschedule follow-up to new date
- ✅ Tests: 10+ unit tests, 5+ E2E tests
- ✅ Email templates in code

### Effort Estimate

- **Backend:** 4-5 hours (notification system, email templates, endpoints)
- **Frontend:** 3-4 hours (follow-up dashboard + UI)
- **Testing:** 2-3 hours
- **Email Integration:** 1-2 hours (Sendgrid/Resend setup)
- **Total:** 10-14 hours (~2 days)

### Dependencies

- ✅ Phase 1 (follow_up_due_date field) must be complete
- ✅ No blocking dependencies otherwise

### Success Metrics

- Follow-up dashboard shows correct trips with correct dates
- Email notifications arrive on time
- Operators can mark follow-ups as done
- Timeline captures follow-up completion

---

## Phase 6: Activity Provenance & Distinction (P1 - High)

### Problem
When Ravi mentions "Universal Studios and nature parks", the system doesn't distinguish between:
- **Traveler-requested:** "We definitely want Universal Studios"
- **Agent-suggested:** "Have you considered nature parks?"

This distinction matters for itinerary confidence and traveler satisfaction.

### Existing Code
- `activity_provenance` field added in Phase 2 (backend + frontend)
- No UI distinction between suggested vs requested

### What Phase 6 Delivers

**Activity Capture UI:**
- Separate inputs for traveler-requested and agent-suggested activities
- Requested: "What specific activities did the travelers mention?"
- Suggested: "What did you suggest that they seemed interested in?"
- Allow manual editing if extraction misses the distinction

**Activity Display in Itinerary:**
- Traveler-requested activities: Bold, high priority
- Agent-suggested activities: Lighter, labeled "(suggested)"
- Confidence score for each activity

**Example:**
```
MUST-HAVE ACTIVITIES (Traveler-Requested):
  ✓ Universal Studios Singapore
    Confidence: 90% (mentioned by caller)

RECOMMENDED ACTIVITIES (Agent-Suggested):
  • Singapore Botanic Gardens
    Confidence: 60% (suggested by Ravi, positive response)
  • Night Safari
    Confidence: 40% (suggested by Ravi, no explicit response)
```

### Acceptance Criteria

- ✅ Separate input fields for requested vs suggested activities
- ✅ Activity display shows source (requested vs suggested)
- ✅ Confidence scores visible
- ✅ Can edit activities in trip edit mode
- ✅ Tests: 8+ unit tests, 4+ E2E tests

### Effort Estimate

- **Backend:** 2-3 hours (update activity_provenance schema to include source)
- **Frontend:** 3-4 hours (UI + display logic)
- **Testing:** 2-3 hours
- **Total:** 7-10 hours (~1 day)

### Dependencies

- ✅ Phase 2 (activity_provenance field) must be complete
- ✅ No blocking dependencies otherwise

### Success Metrics

- Activities show with correct source label (requested vs suggested)
- Confidence scores visible and accurate
- Operators can distinguish high-confidence from exploratory activities

---

## Phase 7: Advanced Features (P2 - Nice to Have)

### 7.1 Activity Recommendation Engine
**Effort:** 8-10 hours  
**Impact:** High (increases itinerary quality)

When a trip arrives with activity_provenance, suggest additional activities based on:
- Destination + party_composition + pace_preference + activity_provenance
- Similar past trips
- Regional events/seasonality

### 7.2 Follow-up Automation
**Effort:** 6-8 hours  
**Impact:** Medium (reduces manual work)

Auto-suggest follow-up questions based on missing fields:
- "Budget not mentioned — ask client"
- "Visa status unknown — confirm nationalities"
- "Date still uncertain — lock in Feb 9-14?"

### 7.3 Smart Suitability Scores
**Effort:** 10-12 hours  
**Impact:** High (reduces risk)

Improve spine confidence scoring for edge cases:
- Toddler + trekking (high risk vs low risk?  depends on trek difficulty)
- Senior mobility + schedule (high risk vs low risk? depends on pace)

### 7.4 Operator Performance Insights
**Effort:** 6-8 hours  
**Impact:** Medium (helps with hiring/training)

Dashboard showing:
- Average follow-up delay
- Override rate (how often do they override?)
- Traveler satisfaction correlation

---

## Timeline & Sequencing

```
Unit-1 ✅ (Done: 2 hours)
  └─ Raw note + owner notes + follow-up due date

Phase 2 ✅ (Done: 1 hour)
  └─ Structured fields (party, pace, date_confidence, lead_source, activity)

Phase 3 (P0): Suitability Rendering
  └─ Time: 1 day
  └─ Blocking: Nothing
  └─ Unblocks: Phase 4

Phase 4 (P0): Override Controls
  └─ Time: 2 days
  └─ Blocking: Phase 3
  └─ Unblocks: Phase 5-7

Phase 5 (P1): Follow-up Workflow
  └─ Time: 2 days
  └─ Blocking: Nothing (Unit-1 provides follow_up_due_date)
  └─ Unblocks: Phase 7.2

Phase 6 (P1): Activity Provenance
  └─ Time: 1 day
  └─ Blocking: Nothing (Phase 2 provides activity_provenance field)
  └─ Unblocks: Phase 7.1

Phase 7 (P2): Advanced Features
  └─ Time: 3-4 days total (pick 2-3 based on priority)
  └─ Blocking: Depends on which features chosen

Parallel Path Recommendation:
  Phase 3 + Phase 5 + Phase 6 can run in parallel
  Phase 4 should start after Phase 3 is testable
```

---

## Priority Ranking

| Phase | Priority | Impact | Effort | Sequence | Reason |
|-------|----------|--------|--------|----------|--------|
| **3** | P0 | High | 1 day | 1st | Operators need to understand decisions |
| **4** | P0 | High | 2 days | 2nd (after 3) | Operators need to change decisions |
| **5** | P1 | High | 2 days | 1st (parallel) | Prevents broken promises |
| **6** | P1 | Medium | 1 day | 1st (parallel) | Improves itinerary quality |
| **7** | P2 | Medium | 3-4 days | Last | Nice-to-have features |

**Recommended Execution Order:**
1. Complete Phase 3 (Suitability) — 1 day
2. Start Phase 4, 5, 6 in parallel — 2-3 days total
3. Complete Phase 7 based on business priorities — 3-4 days

**Total Remaining Work:** 9-12 days of development

---

## Open Questions for Product Decision

1. **Follow-up Notifications:** Email, Slack, in-app, or all three?
2. **Override Permissions:** Can any operator override, or only leads/admins?
3. **Activity Recommendations:** Use simple rules or ML?
4. **Suitability Scoring:** Show raw confidence % or simplified (High/Med/Low)?

---

## Next Immediate Actions

**Option A: Start Phase 3 now** (1 day)
- Render existing suitability signals
- Add timeline integration
- Test with real trip data

**Option B: Batch Phase 3-4** (3 days)
- Suitability + Overrides together
- Better UX (see decision → change decision)
- More complete feature launch

**Option C: Parallel Phase 3, 5, 6** (2-3 days)
- Suitability (decision visibility)
- Follow-up workflow (operational)
- Activity provenance (itinerary quality)
- Maximize throughput

---

## Files That Will Be Created/Modified

### Phase 3
- `frontend/src/app/workspace/[tripId]/suitability/page.tsx` (redesign)
- `frontend/src/components/workspace/panels/SuitabilitySignal.tsx` (enhance)
- `frontend/src/components/workspace/panels/TimelinePanel.tsx` (integrate)
- `tests/test_suitability_rendering.py`

### Phase 4
- `frontend/src/app/api/trips/[id]/overrides/route.ts` (NEW)
- `spine_api/persistence.py` (add override schema)
- `alembic/versions/add_overrides_table.py` (NEW)
- `frontend/src/components/workspace/modals/OverrideModal.tsx` (NEW)
- `tests/test_override_controls.py`

### Phase 5
- `frontend/src/components/workspace/dashboard/FollowUpDashboard.tsx` (NEW)
- `frontend/src/app/api/trips/follow-ups/route.ts` (NEW)
- `spine_api/notifications.py` (NEW - email/notification logic)
- `tests/test_followup_workflow.py`

### Phase 6
- `frontend/src/components/workspace/panels/CaptureCallPanel.tsx` (enhance activity section)
- `frontend/src/components/workspace/panels/ActivityDisplay.tsx` (NEW)
- `tests/test_activity_provenance.py`

---

## Success Criteria for Entire Roadmap

**After Phase 6 (All P0/P1 complete):**

✅ Operators can see why decisions were made (suitability signals)  
✅ Operators can change decisions when appropriate (overrides)  
✅ Operators don't break promises (follow-up reminders)  
✅ Itineraries distinguish high-confidence from exploratory activities  
✅ All changes are auditable and reversible  
✅ 50+ new tests, all passing  
✅ Zero regressions in Phase 1-2 code  

**Call Capture Feature:** Feature-complete and launch-ready ✅

---

**Prepared by:** Audit Follow-up Team  
**Date:** 2026-04-28  
**Next Review:** Before starting Phase 3
