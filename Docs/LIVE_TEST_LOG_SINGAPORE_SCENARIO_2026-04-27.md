# Live Test Log: Singapore Phone-Inquiry Scenario
## Waypoint OS — Natural Language Extraction Test

**Date:** 2026-04-27
**Tester:** Pranay Suyash (acting as agency owner "Ravi")
**Scenario:** Real phone call from Nov 2024 — Singapore family trip
**Test Goal:** Can AI extract structured data from natural language agent notes?

---

## Test Run 1: Structured Agent Notes (Key-Value Format)

### Input (Exactly as pasted by tester)

**Customer Message:**
```
[Not used — tester put everything in Agent Notes]
```

**Agent Notes:**
```
Call received: Nov 25, 2024
Caller: Pranay Suyash
Referral: Wife's colleague → Divya (Ravi's wife)
Party: 6 pax (2 adults, 1 toddler aged 1.7y, 2 elderly parents)
Pace preference: Relaxed, not rushed
Budget: Not discussed
Interests: Universal Studios, nature parks
Follow-up: Promised draft itinerary in 1-2 days
Toddler needs: Stroller-friendly, nap time considerations
Elderly needs: Accessible transport, moderate walking only
```

### Results (To be filled by tester)

| Field | Expected | AI Extracted | Match? |
|-------|----------|--------------|--------|
| Destination | Singapore | ___ | ✅/❌ |
| Date Window | Jan-Feb 2025 | ___ | ✅/❌ |
| Tentative Dates | Feb 9-14 | ___ | ✅/❌ |
| Duration | 5 days | ___ | ✅/❌ |
| Party Size | 6 | ___ | ✅/❌ |
| Budget | Not discussed / TBD | ___ | ✅/❌ |
| Pace | Relaxed, not rushed | ___ | ✅/❌ |
| Interests | Universal Studios, nature parks | ___ | ✅/❌ |

**Missed entirely:**
- Customer name: Pranay
- Phone: 9910403502
- Referral: Wife's colleague → Divya
- Follow-up promise: Draft in 1-2 days

**Trip card in Inbox shows:**
- Destination: ___
- Party size: ___
- Dates: ___
- Customer name: ___

**Process Trip succeeded?** Yes / No
**Time to process:** ___ seconds
**Any console errors?** ___

**Tester observations:**
```
[Pranay fills this in]
```

---

## Test Run 2: Abbreviated Agent Notes (Bullet-Style)

### Input (Exactly as pasted by tester)

**Customer Message:**
```
[Not used — tester put everything in Agent Notes]
```

**Agent Notes:**
```
call from pranay, number 9910403502
referral - wife colleague of divya
singapore, jan/feb, tentative 9-14 feb, 5d
6 pax - couple + 1.7yo kid + parents
pace: relaxed, not rushed
interests: universal studios, nature parks
budget: tbd
follow up: draft by nov 27
```

### Results (To be filled by tester)

| Field | Expected | AI Extracted | Match? |
|-------|----------|--------------|--------|
| Destination | Singapore | ___ | ✅/❌ |
| Date Window | Jan-Feb 2025 | ___ | ✅/❌ |
| Tentative Dates | Feb 9-14 | ___ | ✅/❌ |
| Duration | 5 days | ___ | ✅/❌ |
| Party Size | 6 | ___ | ✅/❌ |
| Budget | Not discussed / TBD | ___ | ✅/❌ |
| Pace | Relaxed, not rushed | ___ | ✅/❌ |
| Interests | Universal Studios, nature parks | ___ | ✅/❌ |

**Missed entirely:**
- Customer name: Pranay
- Phone: 9910403502
- Referral: Wife's colleague → Divya
- Follow-up promise: Draft in 1-2 days

**Trip card in Inbox shows:**
- Destination: ___
- Party size: ___
- Dates: ___
- Customer name: ___

**Process Trip succeeded?** Yes / No
**Time to process:** ___ seconds
**Any console errors?** ___

**Tester observations:**
```
[Pranay fills this in]
```

---

## Test Run 3: Fully Unstructured (Conversational)

### Input (To be pasted by tester — free-form natural language)

**Customer Message:**
```
[Tester pastes their own unstructured version]
```

**Agent Notes:**
```
[Optional — tester adds if needed]
```

### Results (To be filled by tester)

| Field | Expected | AI Extracted | Match? |
|-------|----------|--------------|--------|
| Destination | Singapore | ___ | ✅/❌ |
| Date Window | Jan-Feb 2025 | ___ | ✅/❌ |
| Tentative Dates | Feb 9-14 | ___ | ✅/❌ |
| Duration | 5 days | ___ | ✅/❌ |
| Party Size | 6 | ___ | ✅/❌ |
| Budget | Not discussed / TBD | ___ | ✅/❌ |
| Pace | Relaxed, not rushed | ___ | ✅/❌ |
| Interests | Universal Studios, nature parks | ___ | ✅/❌ |

**Missed entirely:**
- Customer name: Pranay
- Phone: 9910403502
- Referral: Wife's colleague → Divya
- Follow-up promise: Draft in 1-2 days

**Trip card in Inbox shows:**
- Destination: ___
- Party size: ___
- Dates: ___
- Customer name: ___

**Process Trip succeeded?** Yes / No
**Time to process:** ___ seconds
**Any console errors?** ___

**Tester observations:**
```
[Pranay fills this in]
```

---

## Comparison: Run 1 vs Run 2 vs Run 3

| Aspect | Run 1 (Structured) | Run 2 (Abbreviated) | Run 3 (Unstructured) | Winner |
|--------|-------------------|---------------------|----------------------|--------|
| Destination extraction | ___ | ___ | ___ | ___ |
| Date extraction | ___ | ___ | ___ | ___ |
| Party size extraction | ___ | ___ | ___ | ___ |
| Budget handling | ___ | ___ | ___ | ___ |
| Preference detection | ___ | ___ | ___ | ___ |
| Overall accuracy | ___ | ___ | ___ | ___ |

---

## Key Questions Answered by This Test

1. **Does formatting help the AI?** (Run 1 = structured key-value, Run 2 = abbreviated bullets, Run 3 = free-form)
2. **Does the AI handle missing budget gracefully?**
3. **Does the AI detect "not rushed" as a preference?**
4. **Does the AI understand "tentative dates" ambiguity?**
5. **Does the trip card show useful info at a glance?**
6. **What critical info is ALWAYS lost?** (name, phone, referral)
7. **Which input style gives the best extraction?**

---

## Document History

| Time | Event |
|------|-------|
| 2026-04-27 | Document created, all 3 test run instructions documented |
| 2026-04-27 | Test Run 1 completed — results filled by tester |
| 2026-04-27 | Test Run 2 completed — results filled by tester |
| 2026-04-27 | Test Run 3 completed — results filled by tester |

---

**File:** `Docs/LIVE_TEST_LOG_SINGAPORE_SCENARIO_2026-04-27.md`
**Status:** Test Run 1 FAILED — 504 Gateway Timeout on `POST /api/spine/run`

### UX Feedback Captured During Test

**Tester observation (Pranay):**
> "'Agent Notes' doesn't sound too useful for the agency owner/users"

**Analysis:**
- Label "Agent Notes" implies these are for subordinate agents, not the owner
- In a small agency (1-2 people), the owner IS the agent — the label feels mismatched
- Better alternatives: "Call Notes", "Internal Notes", "My Notes", "Owner Notes"

**Severity:** Low — doesn't block functionality, but affects perceived ownership

### Technical Failure Analysis

**Error:** `POST /api/spine/run 504 (Gateway Timeout)`
**Root cause:** Next.js proxy timeout = 10s, spine pipeline takes 15-60s
**Fix plan:** `Docs/FIX_PLAN_SPINE_RUN_TIMEOUT_2026-04-27.md`
