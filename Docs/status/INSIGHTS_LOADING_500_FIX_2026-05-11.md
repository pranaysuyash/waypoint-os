# Insights Loading 500 Fix

Date: 2026-05-11
Scope: `/insights` loading state and `GET /api/insights/summary?range=30d`

## Reported Symptom

- Browser stayed on the `/insights` loading animation.
- Console showed `GET http://localhost:3000/api/insights/summary?range=30d 500`.

## Instruction / Workflow Notes

- Loaded `/Users/pranay/AGENTS.md`, `/Users/pranay/Projects/AGENTS.md`, repo `AGENTS.md`, repo `CLAUDE.md`, `frontend/AGENTS.md`, `frontend/CLAUDE.md`, and the canonical context pack under `Docs/context/agent-start/`.
- Applied relevant skills/workflows: `investigate`, `systematic-debugging`, `search-first`, `tdd-workflow`, `python-testing`, and `verification-before-completion`.
- Used read-only git inspection only.

## Root Cause

Authenticated runtime reproduction confirmed the failure was backend-side:

```text
GET /analytics/summary?range=30d -> 500 Internal Server Error
AttributeError: 'NoneType' object has no attribute 'get'
src/analytics/metrics.py:33
```

`aggregate_insights()` assumed every trip had a dict-shaped `analytics` payload. Real SQL trip records can have `analytics = null`, so the endpoint crashed before returning a summary. The frontend BFF correctly mapped `/api/insights/summary` to backend `/analytics/summary`; this was not a duplicate-route or route-map issue.

## Fix

- Added dict-shape normalization helpers in `src/analytics/metrics.py`:
  - `_dict_payload()`
  - `_trip_analytics()`
  - `_trip_packet()`
- Updated analytics summary, team metrics, revenue metrics, and alerts reads to treat null/malformed optional JSON as absent evidence instead of crashing.
- Added regression coverage in `tests/test_analytics_truth_hardening.py` for null analytics and null nested payloads.

## Verification

Regression-first check:

```bash
.venv/bin/python -m pytest tests/test_analytics_truth_hardening.py -q
# failed before fix on null analytics / null payload tests
```

Post-fix focused tests:

```bash
.venv/bin/python -m pytest tests/test_analytics_truth_hardening.py tests/test_revenue_analytics.py tests/test_team_metrics_contract.py -q
# 20 passed in 8.19s
```

Runtime checks after backend reload:

```bash
curl -sS -i -c .runtime/insights_cookies.txt \
  -X POST http://localhost:3000/api/auth/login \
  -H 'Content-Type: application/json' \
  --data '{"email":"newuser@test.com","password":"testpass123"}'
# HTTP/1.1 200 OK

curl -sS -i -b .runtime/insights_cookies.txt \
  'http://localhost:3000/api/insights/summary?range=30d'
# HTTP/1.1 200 OK
```

Sibling insights endpoint checks:

```text
pipeline 200
team 200
revenue 200
bottlenecks 200
escalations 200
funnel 200
alerts 200
```

Page route check:

```bash
curl -sS -o .runtime/insights_page.html -w '%{http_code}\n' \
  -b .runtime/insights_cookies.txt http://localhost:3000/insights
# 200
```

## Runtime Note

During backend reload, startup initially hung behind a stale Postgres `idle in transaction` session that held an `agencies` relation lock. The lock blocked the app's existing additive startup compatibility checks:

```sql
ALTER TABLE agencies ADD COLUMN IF NOT EXISTS is_test BOOLEAN DEFAULT false
```

The stale blocker cleared before termination was needed. After that, backend startup completed and `/health` returned `200`. This is a separate dev-runtime issue worth tracking if startup hangs recur: startup schema compatibility checks should avoid indefinite lock waits or use a short `lock_timeout` with a clear log/error.

## Follow-Up

- Consider adding a startup hardening task: set bounded Postgres `lock_timeout` around additive compatibility checks so a stale transaction cannot silently hold the local API offline.
- Consider replacing random placeholder analytics values with evidence-state fields so operators can distinguish measured values from unavailable/estimated values.
