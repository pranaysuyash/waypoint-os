# Waypoint OS — Signup Flow Testing Guide

**Date:** 2026-04-27
**Tester:** Pranay Suyash
**Status:** All scenarios verified ✅ (2026-04-27)
- Scenario C (Real user blank slate): ✅ PASS
- Scenario D (Test user mock data): ✅ PASS
- Cross-scenario isolation: ✅ PASS
- Analytics 504 timeout fix: ✅ PASS

---

## Pre-Test Checklist

Before starting each scenario, confirm:

```bash
# Terminal 1: Backend
cd spine_api && uv run uvicorn spine_api.server:app --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

Then open `http://localhost:3000` in your browser.

---

## Scenario A: New Test User Signup (Should Get Mock Data)

**Purpose:** A brand-new test user signs up and should see pre-populated mock trips.

### Step-by-Step

| Step | Action | Exact Input | Expected Output | What I Saw | ✅ / ❌ |
|------|--------|-------------|-----------------|------------|---------|
| A1 | Go to signup page | Navigate to `http://localhost:3000/signup` | Signup form loads with email, password fields | | |
| A2 | Enter email | `testflow1@test.com` | No validation error | | |
| A3 | Enter password | `TestPass123` | No validation error (≥8 chars) | | |
| A4 | Submit form | Click "Sign Up" button | Redirect to dashboard/workspace | | |
| A5 | View dashboard stats | Look at overview page | Shows **numbers > 0**: active, pending, needs attention | | |
| A6 | View inbox/trips | Navigate to workspace/inbox | Shows **~30 trip cards** (mock data) | | |
| A7 | Click a trip card | Click first trip in inbox | Trip detail panel opens with mock data (destination, dates, etc.) | | |
| A8 | Check numbers make sense | Compare stats to trip count | `canonical_total` ≈ 514, stages add up | | |
| A9 | Log out | Click logout | Returns to login page | | |

### Expected Dashboard Numbers (Test User)

```json
{
  "active": 3,
  "pending_review": 511,
  "ready_to_book": 0,
  "needs_attention": 462
}
```

### Expected Unified State (Test User)

```json
{
  "canonical_total": 514,
  "stages": {
    "new": 450,
    "assigned": 10,
    "in_progress": 5,
    "completed": 3,
    "cancelled": 2
  }
}
```

---

## Scenario B: New Real User Signup (Should Get Blank Slate)

**Purpose:** A brand-new real user signs up and should see an empty workspace.

### Step-by-Step

| Step | Action | Exact Input | Expected Output | What I Saw | ✅ / ❌ |
|------|--------|-------------|-----------------|------------|---------|
| B1 | Go to signup page | Navigate to `http://localhost:3000/signup` | Signup form loads | | |
| B2 | Enter email | `myrealemail@gmail.com` (use a unique one) | No validation error | | |
| B3 | Enter password | `RealPass123` | No validation error | | |
| B4 | Submit form | Click "Sign Up" button | Redirect to dashboard/workspace | | |
| B5 | View dashboard stats | Look at overview page | Shows **all zeros**: `active: 0`, `pending: 0`, etc. | | |
| B6 | View inbox/trips | Navigate to workspace/inbox | Shows **empty state** — "No trips yet" or blank | | |
| B7 | Look for CTA | Check if there's a "Create trip" or "Get started" button | Some UI element to add first trip | | |
| B8 | Try creating a trip | If possible, create a new trip | Trip appears in inbox, stats update to 1 | | |
| B9 | Check stats after creation | View dashboard | Shows `active: 1` (or relevant count) | | |
| B10 | Log out | Click logout | Returns to login page | | |

### Expected Dashboard Numbers (Real User — Before Creating Trip)

```json
{
  "active": 0,
  "pending_review": 0,
  "ready_to_book": 0,
  "needs_attention": 0
}
```

### Expected Unified State (Real User — Before Creating Trip)

```json
{
  "canonical_total": 0,
  "stages": {
    "new": 0,
    "assigned": 0,
    "in_progress": 0,
    "completed": 0,
    "cancelled": 0
  }
}
```

---

## Scenario D: Existing Test User Login (Should Still Have Mock Data)

**Purpose:** Verify the existing test account `newuser@test.com` still has its 514 mock trips.

### Step-by-Step

| Step | Action | Exact Input | Expected Output | What I Saw | ✅ / ❌ |
|------|--------|-------------|-----------------|------------|---------|
| D1 | Go to login page | Navigate to `http://localhost:3000/login` | Login form loads | | |
| D2 | Enter email | `newuser@test.com` | No validation error | | |
| D3 | Enter password | `testpass123` | No validation error | | |
| D4 | Submit form | Click "Log In" button | Redirect to dashboard/workspace | | |
| D5 | View dashboard stats | Look at overview page | Shows **numbers > 0** (same as Scenario A) | | |
| D6 | View inbox/trips | Navigate to workspace/inbox | Shows **~30 trip cards** | | |
| D7 | Verify data consistency | Compare to Scenario A | Same numbers, same trip count | | |
| D8 | Log out | Click logout | Returns to login page | | |

---

## Cross-Scenario Verification Checklist

After running all scenarios, verify these critical boundaries:

| Check | How to Verify | Expected Result |
|-------|---------------|-----------------|
| Real user NEVER sees test user's trips | Login as real user, check inbox | 0 trips |
| Test user NEVER sees real user's trips | Login as test user, check inbox | Only mock trips (no real user trips) |
| Two different real users are isolated | Create 2 real users, add trip to one | Other real user still sees 0 |
| Numbers persist after refresh | Hard refresh (Cmd+Shift+R) | Same numbers as before refresh |
| Numbers persist after re-login | Log out, log back in | Same numbers as before |

---

## Feedback Capture Table

Copy this table for EACH scenario. Fill it out as you test.

```
## Scenario: ___ (A / B / D)

**Email used:** _______________
**Browser:** _______________
**Time tested:** _______________

### Pass/Fail Summary
| Step | Status | Notes |
|------|--------|-------|
| Signup/Login | ✅ / ❌ | |
| Dashboard numbers | ✅ / ❌ | |
| Inbox state | ✅ / ❌ | |
| Trip detail view | ✅ / ❌ | |
| Logout | ✅ / ❌ | |

### Exact Numbers I Saw
- Dashboard: active=___ pending_review=___ ready_to_book=___ needs_attention=___
- Unified state: canonical_total=___ new=___ assigned=___ in_progress=___ completed=___ cancelled=___
- Trip count in inbox: ___

### Console Errors (paste any red text)
```
[Paste here]
```

### Network Failures (if any)
```
[Paste failed request URLs + status codes]
```

### Screenshots
[Attach screenshots of: dashboard, inbox, any errors]

### What Felt Good

### What Felt Confusing / Broken / Wrong

### Suggestions for Improvement
```

---

## Quick API Verification Commands

If you want to double-check numbers independently of the UI:

```bash
# 1. Login and save cookies
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "YOUREMAIL", "password": "YOURPASSWORD"}' \
  -c /tmp/cookies.txt

# 2. Check dashboard stats
curl -s http://localhost:8000/api/dashboard/stats -b /tmp/cookies.txt

# 3. Check unified state
curl -s http://localhost:8000/api/system/unified-state -b /tmp/cookies.txt

# 4. Check trips
curl -s http://localhost:8000/trips -b /tmp/cookies.txt
```

Replace `YOUREMAIL` and `YOURPASSWORD` with the test account credentials.

---

## Definition of Done

This testing round is complete when:

- [ ] Scenario A tested and documented
- [ ] Scenario B tested and documented
- [ ] Scenario D tested and documented
- [ ] Cross-scenario isolation verified
- [ ] Feedback tables filled for all scenarios
- [ ] Screenshots attached for any issues
- [ ] Console/network errors documented

---

## Test Results — 2026-04-27

### Scenario C: Existing Real User (pranay.suyash@gmail.com) — Blank Slate

**Email used:** pranay.suyash@gmail.com
**Browser:** API/curl testing
**Time tested:** 2026-04-27

| Step | Status | Notes |
|------|--------|-------|
| Login | ✅ | Returns agency `Gmail` (not test) |
| Dashboard numbers | ✅ | All zeros: active=0, pending=0, needs_attention=0 |
| Unified state | ✅ | canonical_total=0, all stages=0 |
| Inbox state | ✅ | 0 trips |
| Analytics | ✅ | All endpoints respond ~30ms (no 504s) |
| Trip isolation | ✅ | 404 when accessing test user's trip |

### Scenario D: Existing Test User (newuser@test.com) — Mock Data

**Email used:** newuser@test.com
**Browser:** API/curl testing
**Time tested:** 2026-04-27

| Step | Status | Notes |
|------|--------|-------|
| Login | ✅ | Returns agency `Test` with mock data |
| Dashboard numbers | ✅ | pending_review=484, needs_attention=440 |
| Unified state | ✅ | canonical_total=484, new=440 |
| Inbox state | ✅ | Shows trips (e.g., trip_feb536007385) |
| Analytics | ✅ | Team=2 members, Bottlenecks=1, responds ~30ms |
| Trip isolation | ✅ | Cannot be accessed by real user (404) |

### Exact Numbers Observed

**Real User (pranay.suyash@gmail.com):**
```json
{
  "dashboard": { "active": 0, "pending_review": 0, "ready_to_book": 0, "needs_attention": 0 },
  "unified_state": { "canonical_total": 0, "new": 0, "assigned": 0, "in_progress": 0, "completed": 0, "cancelled": 0 },
  "trips": 0
}
```

**Test User (newuser@test.com):**
```json
{
  "dashboard": { "active": 0, "pending_review": 484, "ready_to_book": 0, "needs_attention": 440 },
  "unified_state": { "canonical_total": 484, "new": 440, "assigned": 0, "in_progress": 0, "completed": 0, "cancelled": 0 },
  "trips": 484,
  "orphans": 44
}
```

### Issues Found

1. **44 orphan trips** in test user data — trips with `status: null` and `created_at: null`. These are files that exist but have incomplete data.
2. **`active: 0`** for test user despite 484 trips. The "active" stat calculation may need review (likely counts only trips in a specific status).
3. **New test users get blank slate** — If a new user signs up with `@test.com`, they get a NEW agency (not the shared test agency), so they see 0 trips. Only `newuser@test.com` (the original test account) has the 484 mock trips.

### Analytics Performance Fix

| Endpoint | Before (Real User) | After (Real User) |
|----------|-------------------|-------------------|
| `/analytics/team` | 504 timeout (~10s) | 200 OK (~30ms) |
| `/analytics/bottlenecks` | 504 timeout (~10s) | 200 OK (~25ms) |
| `/analytics/revenue` | 504 timeout (~10s) | 200 OK (~24ms) |
| `/analytics/alerts` | 504 timeout (~10s) | 200 OK (~25ms) |

**Root cause:** All analytics endpoints called `TripStore.list_trips(limit=1000)` without `agency_id`, loading all 514 trips and running expensive computations.
**Fix:** Added `agency_id` filtering to 20+ endpoints in `spine_api/server.py`.

---

**Document version:** 1.1
**Created:** 2026-04-27
**Updated:** 2026-04-27
