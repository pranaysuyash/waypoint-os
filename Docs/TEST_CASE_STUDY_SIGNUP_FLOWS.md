# Waypoint OS — Signup & Onboarding Flow Test Case Study

**Date:** 2026-04-27
**Scope:** Test user (mock data) vs Real user (blank slate) signup flows
**Status:** In Progress — Awaiting User Feedback

---

## 1. Context & Goal

### The Problem We Fixed
Previously, ALL users (test + real) saw the same 514 mock trips on login. Real users like `pranay.suyash@gmail.com` were getting a crowded inbox instead of a clean blank slate.

### What Changed
- Test users (email ending in `@test.com`) → get **mock data seeded automatically**
- Real users (any other email) → get a **blank slate** (0 trips, 0 stats)
- Every user's data is now **scoped to their agency** (no cross-contamination)

### Goal of This Test
Walk through both flows, note EVERYTHING you observe (good, bad, confusing, broken), so we can iterate.

---

## 2. Test Environment

| Component | URL | Status |
|-----------|-----|--------|
| Frontend (Next.js) | `http://localhost:3000` | Start with `cd frontend && npm run dev` |
| Backend (FastAPI) | `http://localhost:8000` | Start with `cd spine_api && uv run uvicorn spine_api.server:app --port 8000` |
| Database | PostgreSQL (`waypoint_os`) | Must be running |

**Pre-check:**
```bash
curl -s http://localhost:8000/health  # Should return {"status":"ok"}
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000  # Should return 200
```

---

## 3. Test Scenarios

### Scenario A: Test User Signup (Mock Data Flow)

**Purpose:** Verify a test user gets pre-populated mock data to play with.

#### Steps

| Step | Action | Expected Input | Expected Output | What I Did | What I Saw |
|------|--------|---------------|-----------------|------------|------------|
| A1 | Navigate to `http://localhost:3000/signup` | Browser | Signup form loads | | |
| A2 | Fill in test email: `newtester@test.com` | Email field | No validation error | | |
| A3 | Fill in password: `TestPass123` | Password field | No validation error (min 8 chars) | | |
| A4 | Click "Sign Up" or submit | Button click | Redirect to workspace/dashboard | | |
| A5 | Observe the dashboard/overview page | Browser | Shows stats cards with numbers > 0 | | |
| A6 | Check `/workspace` or inbox | Browser | Shows ~30 mock trips | | |
| A7 | Click on a trip card | Browser | Trip detail panel opens with mock data | | |
| A8 | Observe the "Unified State" section | Browser | Shows `canonical_total: ~30` | | |
| A9 | Log out | Click logout | Returns to login page | | |

#### Expected Behavior
- Dashboard shows: `active: 3`, `pending_review: ~511`, `needs_attention: ~462`
- Unified state shows: `canonical_total: 514`, stages populated
- Inbox shows ~30 trips (paginated from 514)

---

### Scenario B: Real User Signup (Blank Slate Flow)

**Purpose:** Verify a real user gets a clean, empty workspace to start from scratch.

#### Steps

| Step | Action | Expected Input | Expected Output | What I Did | What I Saw |
|------|--------|---------------|-----------------|------------|------------|
| B1 | Navigate to `http://localhost:3000/signup` | Browser | Signup form loads | | |
| B2 | Fill in real email: `yourname@gmail.com` | Email field | No validation error | | |
| B3 | Fill in password: `YourPass123` | Password field | No validation error | | |
| B4 | Click "Sign Up" or submit | Button click | Redirect to workspace/dashboard | | |
| B5 | Observe the dashboard/overview page | Browser | Shows **all zeros** or empty state | | |
| B6 | Check `/workspace` or inbox | Browser | Shows **"No trips yet"** or empty state | | |
| B7 | Try to create a new trip (if UI allows) | Form/button | New trip appears in inbox | | |
| B8 | Observe stats after creating a trip | Browser | Stats update to show 1 active trip | | |
| B9 | Log out | Click logout | Returns to login page | | |

#### Expected Behavior
- Dashboard shows: `active: 0`, `pending_review: 0`, `ready_to_book: 0`, `needs_attention: 0`
- Unified state shows: `canonical_total: 0`, all stages = 0
- Inbox shows empty state or "Get started" CTA

---

### Scenario C: Existing Real User Login (pranay.suyash@gmail.com)

**Purpose:** Verify your existing real account shows blank state.

#### Steps

| Step | Action | Expected Input | Expected Output | What I Did | What I Saw |
|------|--------|---------------|-----------------|------------|------------|
| C1 | Navigate to `http://localhost:3000/login` | Browser | Login form loads | ✅ | ✅ |
| C2 | Enter email: `pranay.suyash@gmail.com` | Email field | | ✅ | ✅ |
| C3 | Enter password: `Osddeies_12` | Password field | | ✅ | ✅ |
| C4 | Click "Log In" | Button click | Redirect to workspace | ✅ | ⚠️ Redirected to `/workbench` (last visited page?) |
| C5 | Observe dashboard/overview | Browser | **All zeros / empty state** | ✅ | ✅ All zeros |
| C6 | Check for any old mock data leaking | Browser | **No trips from other users** | ✅ | ✅ No trips |
| C7 | Check browser console for errors | DevTools | No "Integrity fetch failed" errors | ✅ | ✅ Clean |
| C8 | Check network tab for `/api/dashboard/stats` | DevTools | Returns `{active:0, pending_review:0, ...}` | ✅ | ✅ `{active:0,pending:0,ready:0,needs_attention:0}` |
| C9 | Check Analytics page | Browser | Loads without 504 timeout | ✅ | ✅ Loads fast |
| C10 | Check pipeline stage timings | Browser | Should show 0/null for empty pipeline | ✅ | ⚠️ Shows fake random timings (fixed in backend)

---

### Scenario D: Existing Test User Login (newuser@test.com)

**Purpose:** Verify your existing test account still has mock data.

#### Steps

| Step | Action | Expected Input | Expected Output | What I Did | What I Saw |
|------|--------|---------------|-----------------|------------|------------|
| D1 | Navigate to `http://localhost:3000/login` | Browser | Login form loads | | |
| D2 | Enter email: `newuser@test.com` | Email field | | | |
| D3 | Enter password: `testpass123` | Password field | | | |
| D4 | Click "Log In" | Button click | Redirect to workspace | | |
| D5 | Observe dashboard/overview | Browser | Stats populated with mock data | | |
| D6 | Check inbox | Browser | Shows ~30 mock trips | | |

---

## 4. Observation Checklist

For EVERY scenario, note the following:

### UI/UX Observations
- [ ] Does the page load without visible errors?
- [ ] Are loading states reasonable (not too slow, not jarring)?
- [ ] Does empty state feel **intentional** or **broken**?
- [ ] Are there any confusing labels, buttons, or navigation?
- [ ] Does the color scheme feel right for the state (empty vs populated)?

### Functional Observations
- [ ] Does signup succeed without errors?
- [ ] Does login succeed without errors?
- [ ] Does logout work cleanly?
- [ ] Are dashboard numbers accurate (match API response)?
- [ ] Do trip cards render correctly?
- [ ] Can you click into a trip detail?

### Console/Network Observations
- [ ] Any red errors in browser console? (Screenshot if yes)
- [ ] Any failed network requests (4xx/5xx)?
- [ ] Is `/api/dashboard/stats` returning correct data?
- [ ] Is `/api/system/unified-state` returning correct data?
- [ ] Is `/api/trips` returning correct data?

### Data Integrity Observations
- [ ] Does a real user see ANY mock trips? (Should be NONE)
- [ ] Does a test user see ONLY mock trips for their agency? (Should be YES)
- [ ] After refresh, does data stay consistent?

---

## 5. Known Issues / Limitations (As of 2026-04-27)

| Issue | Severity | Description | Workaround |
|-------|----------|-------------|------------|
| Dashboard stats may flicker on load | Low | Initial load may show old cached data briefly | Hard refresh (Cmd+Shift+R) |
| Console error "Integrity fetch failed" | Medium | May appear if token expires mid-session | Log out and log back in |
| Agency name derived from email domain | Low | `pranay.suyash@gmail.com` → agency name "Gmail" | Can be changed in settings (future) |
| Test user detection only by `@test.com` | Low | Other test domains won't trigger mock data | Use `@test.com` for test accounts |
| Seed fixture is hardcoded to `scenario_alpha` | Low | All test users get same 514 trips | Can be customized per user (future) |

---

## 6. Feedback Capture Template

Copy this section for each scenario you test. Fill in your observations.

```
## Feedback: Scenario [A/B/C/D] — [Test User / Real User]

**Date/Time:** _______________
**Browser:** _______________
**Screenshots:** [Attach if applicable]

### What I Did
[Describe the exact steps you took]

### What I Expected
[What did you think would happen?]

### What Actually Happened
[What did you see? Be specific. Numbers, states, error messages.]

### Console Errors (if any)
```
[Paste any red console errors here]
```

### Network Failures (if any)
```
[Paste any failed request URLs + status codes]
```

### What Felt Good
[What worked well? What felt smooth?]

### What Felt Confusing/Broken
[What didn't make sense? What felt wrong?]

### Suggestions
[What would you change? What would you add?]
```

---

## 7. API Verification Commands

If you want to verify data independently of the UI, run these:

### Check if backend is healthy
```bash
curl -s http://localhost:8000/health
```

### Check dashboard stats for a logged-in user
```bash
# Replace with actual cookie from your browser
curl -s http://localhost:8000/api/dashboard/stats \
  -b "access_token=YOUR_TOKEN_HERE"
```

### Check unified state
```bash
curl -s http://localhost:8000/api/system/unified-state \
  -b "access_token=YOUR_TOKEN_HERE"
```

### Check trips
```bash
curl -s http://localhost:8000/trips \
  -b "access_token=YOUR_TOKEN_HERE"
```

---

## 8. Next Steps After Your Feedback

1. **You test** → Walk through scenarios A-D, fill feedback templates
2. **You share** → Send back this doc with your observations
3. **We analyze** → Categorize issues by severity (P0 blocker, P1 annoying, P2 nice-to-have)
4. **We fix** → Tackle P0s first, then iterate on P1s
5. **We re-test** → Verify fixes, repeat until smooth

---

**Document version:** 1.0
**Last updated:** 2026-04-27
**Next review:** After user feedback received
