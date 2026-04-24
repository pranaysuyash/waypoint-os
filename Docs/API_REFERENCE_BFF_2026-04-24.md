# API Reference — Frontend BFF Routes

**Date**: 2026-04-24
**Scope**: Complete reference for all 62 BFF (Backend-for-Frontend) API routes
**Status**: ✅ All 43 backend endpoints have BFF coverage

---

## Quick Reference

| BFF Route | Method | Backend Endpoint | Cached? | Description |
|-----------|--------|------------------|---------|-------------|
| `/api/auth/login` | POST | `POST /api/auth/login` | ❌ | User login, sets cookies |
| `/api/auth/logout` | POST | `POST /api/auth/logout` | ❌ | Clear auth cookies |
| `/api/auth/me` | GET | `GET /api/auth/me` | ❌ | Get current user info |
| `/api/auth/refresh` | POST | `POST /api/auth/refresh` | ❌ | Refresh access token |
| `/api/auth/signup` | POST | `POST /api/auth/signup` | ❌ | Create new account |
| `/api/auth/confirm-password-reset` | POST | `POST /api/auth/confirm-password-reset` | ❌ | Confirm password reset |
| `/api/auth/request-password-reset` | POST | `POST /api/auth/request-password-reset` | ❌ | Request password reset |
| `/api/health` | GET | `GET /health` | ✅ 10s | Health check |
| `/api/items` | GET | `GET /items` | ✅ 60s | List items |
| `/api/assignments` | GET | `GET /assignments` | ✅ 30s | List assignments |
| `/api/settings` | GET | `GET /api/settings` | ✅ 300s | Get agency settings |
| `/api/settings/autonomy` | GET/POST | `GET/POST /api/settings/autonomy` | ✅ 300s / ❌ | Autonomy policy |
| `/api/settings/operational` | POST | `POST /api/settings/operational` | ❌ | Update operational settings |
| `/api/settings/pipeline` | GET | `GET /api/settings/pipeline` | ❌ | Pipeline settings |
| `/api/settings/approvals` | GET/POST | `GET/POST /api/settings/approvals` | ❌ | Approval settings |
| `/api/trips` | GET/PATCH | `GET/PATCH /trips` | ❌ | List/update trips |
| `/api/trips/[id]` | GET/PATCH | `GET/PATCH /trips/{id}` | ❌ | Get/update specific trip |
| `/api/trips/[id]/overrides` | GET | `GET /trips/{id}/overrides` | ❌ | List trip overrides |
| `/api/trips/[id]/review/action` | POST | `POST /trips/{id}/review/action` | ❌ | Submit review action |
| `/api/trips/[id]/snooze` | POST | `POST /trips/{id}/snooze` | ❌ | Snooze trip |
| `/api/trips/[id]/assign` | POST | `POST /trips/{id}/assign` | ❌ | Assign trip |
| `/api/trips/[id]/unassign` | POST | `POST /trips/{id}/unassign` | ❌ | Unassign trip |
| `/api/trips/[id]/suitability/acknowledge` | POST | `POST /trips/{id}/suitability/acknowledge` | ❌ | Acknowledge flags |
| `/api/trips/[id]/overrides` | GET | `GET /trips/{id}/overrides` | ❌ | List overrides |
| `/api/trips/[id]/timeline` | GET | `GET /api/trips/{id}/timeline` | ❌ | Get trip timeling |
| `/api/inbox` | GET | `GET /trips` | ❌ | Inbox with query params |
| `/api/inbox/stats` | GET | `GET /trips?limit=1000` | ❌ | Inbox statistics |
| `/api/inbox/assign` | POST | `POST /trips/{id}/assign` | ❌ | Bulk assign trips |
| `/api/inbox/bulk` | POST | `POST /inbox/bulk` | ❌ | Bulk inbox actions |
| `/api/inbox/reassign` | POST | `POST /trips/{id}/reassign` | ❌ | Reassign trip |
| `/api/insights/agent-trips` | GET | `GET /analytics/agent/{id}/drill-down` | ❌ | Agent trip drill-down |
| `/api/insights/alerts` | GET/POST | `GET/POST /analytics/alerts` | ❌ | Analytics alerts |
| `/api/insights/alerts/[alertId]/dismiss` | POST | `POST /analytics/alerts/{id}/dismiss` | ❌ | Dismiss alert |
| `/api/insights/bottlenecks` | GET | `GET /analytics/bottlenecks` | ❌ | Bottleneck analysis |
| `/api/insights/pipeline` | GET | `GET /analytics/pipeline` | ❌ | Pipeline metrics |
| `/api/insights/revenue` | GET | `GET /analytics/revenue` | ❌ | Revenue metrics |
| `/api/insights/summary` | GET | `GET /analytics/summary` | ❌ | Insights summary |
| `/api/insights/team` | GET | `GET /analytics/team` | ❌ | Team metrics |
| `/api/insights/escalations` | GET | `GET /analytics/escalations` | ❌ | Escalation analysis |
| `/api/insights/export` | GET | `GET /analytics/export` | ❌ | Export analytics |
| `/api/insights/funnel` | GET | `GET /analytics/funnel` | ❌ | Funnel analysis |
| `/api/pipeline` | GET | `GET /analytics/pipeline` | ❌ | Pipeline (alias) |
| `/api/reviews` | GET | `GET /analytics/reviews` | ❌ | Reviews list |
| `/api/reviews/[id]` | GET | `GET /analytics/reviews/{id}` | ❌ | Specific review |
| `/api/reviews/action` | POST | `POST /trips/{id}/review/action` | ❌ | Submit review |
| `/api/reviews/bulk-action` | POST | `POST /reviews/bulk-action` | ❌ | Bulk review actions |
| `/api/runs` | GET | `GET /runs` | ❌ | List runs |
| `/api/runs/[id]` | GET | `GET /runs/{id}` | ❌ | Run status |
| `/api/runs/[id]/events` | GET | `GET /runs/{id}/events` | ❌ | Run events |
| `/api/runs/[id]/steps/[step_name]` | GET | `GET /runs/{id}/steps/{step}` | ❌ | Run step details |
| `/api/scenarios` | GET | `GET /scenarios` | ❌ | List scenarios |
| `/api/scenarios/[id]` | GET | `GET /scenarios/{id}` | ❌ | Specific scenario |
| `/api/scenarios/alpha` | GET | `GET /scenarios/alpha` | ❌ | Alpha scenario |
| `/api/audit` | GET | `GET /audit` | ❌ | Audit events |
| `/api/audit/trip/[tripId]` | GET | `GET /audit?trip_id={id}` | ❌ | Trip audit trail |
| `/api/team/invite` | POST | `POST /api/team/invite` | ❌ | Invite team member |
| `/api/team/members` | GET | `GET /api/team/members` | ✅ 60s | List team members |
| `/api/team/members/[id]` | GET/PATCH/DELETE | `GET/PATCH/DELETE /api/team/members/{id}` | ❌ | Manage member |
| `/api/team/workload` | GET | `GET /api/team/workload` | ❌ | Team workload |
| `/api/spine/run` | POST | `POST /run` | ❌ | Trigger spine run |
| `/api/stats` | GET | `GET /api/dashboard/stats` | ❌ | Dashboard stats |
| `/api/system/unified-state` | GET | `GET /api/system/unified-state` | ❌ | Unified state aggregator |
| `/api/version` | GET | (frontend-only) | ❌ | App version info |

---

## Authentication Pattern

All auth routes use HTTP-only cookies:
```typescript
// Login sets both cookies
nextResponse.cookies.set('access_token', data.access_token, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',
  path: '/',
  maxAge: 60 * 60 * 24 * 7, // 7 days
});

// Refresh token forwarded from backend
const backendRefreshToken = response.headers.get('set-cookie');
if (backendRefreshToken) {
  const match = backendRefreshToken.match(/refresh_token=([^;]+)/);
  if (match) {
    nextResponse.cookies.set('refresh_token', match[1], {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/api/auth',
      maxAge: 60 * 60 * 24 * 7,
    });
  }
}
```

---

## Error Handling Pattern

ALL routes use consistent error handling:
```typescript
if (!response.ok) {
  const errorData = await response.json().catch(() => ({}));
  return NextResponse.json(
    { error: errorData.detail || `Spine API returned ${response.status}` },
    { status: response.status }
  );
}

const data = await response.json();
return NextResponse.json(data);
```

**Key points:**
- ✅ Uses `response.json().catch(() => ({}))` to handle non-JSON errors
- ✅ Extracts `detail` field from FastAPI error responses
- ✅ Returns the original HTTP status code from backend
- ✅ Falls back to a generic error message if parsing fails

---

## URL Encoding

ALL path parameters are encoded with `encodeURIComponent()`:
```typescript
const response = await fetch(
  `${SPINE_API_URL}/trips/${encodeURIComponent(tripId)}/action`,
  { ... }
);
```

**Env variable**: All routes use `process.env.SPINE_API_URL || "http://127.0.0.1:8000"`

---

## Cache Headers (Read-Only Endpoints)

| Endpoint | Cache-Control | Duration |
|-----------|---------------|----------|
| `GET /health` | `public, max-age=10, s-maxage=10` | 10 seconds |
| `GET /items` | `public, max-age=60, s-maxage=60` | 1 minute |
| `GET /assignments` | `public, max-age=30, s-maxage=30` | 30 seconds |
| `GET /api/settings` | `public, max-age=300, s-maxage=300` | 5 minutes |
| `GET /api/team/members` | `public, max-age=60, s-maxage=60` | 1 minute |

**Note**: Real-time endpoints (`/analytics/*`, `/trips`, `/runs`) use `cache: "no-store"` in the outgoing fetch request.

---

## Example Usage

### Login:
```typescript
// Frontend call
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password }),
});
const data = await response.json();
// data.access_token available, cookie set automatically
```

### Fetch trips with filters:
```typescript
const response = await fetch('/api/trips?status=new&limit=20');
const data = await response.json();
// data.items = [...], data.total = N
```

### Error response:
```typescript
const response = await fetch('/api/trips/nonexistent-id');
if (!response.ok) {
  const error = await response.json();
  // error.detail = "Trip not found"
  // error.error = "Failed to fetch trip"
}
```

---

## Related Docs

| Doc | Path |
|-----|------|
| Implementation Plan | `Docs/API_ROUTE_FIX_PLAN_2026-04-24.md` |
| Audit Report | `Docs/API_ROUTE_AUDIT_2026-04-23.md` |
| Handoff Document | `Docs/HANDOFF_API_ROUTE_FIX_2026-04-24.md` |
| BFF Review Checklist | `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md` |
| Vercel Best Practices | `~/.agents/skills/vercel-react-best-practices/` |
