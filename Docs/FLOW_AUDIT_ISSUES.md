# Flow Audit — Issues & Gaps

**Date**: 2026-04-30
**Source**: 10-scenario live API test
**Documentation**: `E2E_FLOW_AUDIT_2026-04-30.md`

---

## Issue 1: No Inquiry Ever Passes Cleanly

**Severity**: HIGH
**Status**: All 10 test scenarios resulted in either DEGRADED or ESCALATED validation. Zero PASSED results.

**What happens**:
- Best case: DEGRADED + ASK_FOLLOWUP (needs more info before proceeding)
- Worst case: ESCALATED + STOP_NEEDS_REVIEW (completely blocked)

**Impact**: You cannot demo a "successful" inquiry processing without explaining "it needs more info." Every single inquiry requires human follow-up.

**Likely cause**: The extraction quality threshold for PASSED is set too high, or the required fields for a "complete" inquiry are too many.

## Issue 2: Same Block Message for Everything

**Severity**: MEDIUM
**Status**: Every blocked inquiry shows: *"Trip details are incomplete. Please add the missing information and try again."*

**What happens**: A vague "Europe maybe December" inquiry and an impossible budget request both get the same message. The user gets no guidance on what specifically is wrong.

**Impact**: Poor user experience. Users don't know what to fix.

## Issue 3: Budget Gap Not Detected

**Severity**: MEDIUM
**Status**: Scenario 5 (₹3L for family of 6 to Switzerland, 2 weeks) was blocked for "extraction_quality" -- not budget feasibility.

**What should happen**: The system should flag "Your budget of ₹3L appears too low for a family trip to Switzerland. Would you like to explore alternative destinations or adjust the budget?"

**Impact**: Missed opportunity to show the system's intelligence. Budget feasibility is a core value prop of Waypoint OS.

## Issue 4: Blocked Inquiries Return No Guidance

**Severity**: MEDIUM
**Status**: 60% of inquiries (6 of 10) ended in blocked state.

**What happens**: Users hit a wall with no next step. The system blocks but doesn't tell them how to unblock.

**Fix needed**: Either guide the user ("We need: destination, dates, number of travelers") or provide a template they can fill in.

## Issue 5: Corporate/Business Trip Not Differentiated

**Severity**: LOW
**Status**: Corporate trip inquiry got blocked same as any vague inquiry.

**What's missing**: Corporate travel has different fields (client name, billing info, GST). No persona detection for B2B vs leisure.

## Issue 6: Non-Travel Correctly Blocked (But Not Flagged)

**Severity**: LOW
**Status**: Spam inquiry correctly blocked, but no flag or logging.

**Enhancement**: Non-travel inquiries should be flagged for review, not silently blocked.

---

## Summary

| # | Issue | Severity | Type |
|---|-------|----------|------|
| 1 | No inquiry ever passes cleanly | HIGH | Pipeline threshold |
| 2 | Same block message for everything | MEDIUM | UX |
| 3 | Budget gap not detected | MEDIUM | Missing feature |
| 4 | 60% blocked rate, no guidance | MEDIUM | UX |
| 5 | Corporate trips not differentiated | LOW | Feature gap |
| 6 | Spam blocked but not flagged | LOW | Enhancement |

**Root cause analysis**: The extraction threshold appears to be the bottleneck. Improving extraction quality or relaxing the threshold for initial demos would fix issues 1, 2, and 4 simultaneously.
