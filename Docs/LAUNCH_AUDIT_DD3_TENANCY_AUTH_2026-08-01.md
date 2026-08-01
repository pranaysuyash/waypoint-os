# DD-3: Tenancy & Auth Hardening — Deep-Dive

**Date**: 2026-08-01 · **Parent**: `Docs/LAUNCH_AUDIT_BASELINE_2026-08-01.md` (B4, H4)
**Evidence tier**: Tier 5 — IDORs reproduced against a live instance with a real second agency created via the public signup flow.

## Method

Clean backend instance (port 8010, auth ON, `TRIPSTORE_BACKEND=sql`, local Postgres `waypoint_os`). Created probe agency via the public signup endpoint (`idor-probe-0801@test.com` / agency `2838f049-d4d1-47d9-8db6-78c4c967a864` — additive test data, noted for cleanup in DD-8). Then attempted cross-agency access to agency `d1e3b2b6-…` (the main test agency) resources using only the probe's session cookie. Also ran a full static classification of all 48 `TripStore.get_trip(` call sites.

---

## T1 — Public-checker IDOR is wider than the baseline thought (baseline B4, CONFIRMED Tier 5, severity raised)

Three compounding facts:

1. `GET /api/public-checker/{trip_id}` and `GET .../export` (`spine_api/routers/public_checker.py:101-113`) call `TripStore.get_trip(trip_id)` with **no agency scoping** (`:50`). The only barrier is the AuthMiddleware requirement for *any* valid JWT.
2. **Runtime proof**: probe-agency session → `GET /api/public-checker/trip_db11a60e0fad` → **200 with the full trip record** of agency `d1e3b2b6-…` (run_id, agency_id, status, stage, packet…). Unauthenticated → 401 (verified).
3. **Exposure is not limited to `source='public_checker'` trips**: `_load_public_checker_package_or_404` accepts any trip that has an artifact manifest (`:60-63`), and `save_processed_trip` attaches a public-checker artifact manifest to **every processed trip** (`persistence.py:2849-2857`). In practice nearly every trip in the system is readable by any authenticated user.

The `DELETE` sibling (`:115-134`) hard-deletes using the trip's own agency_id — no comparison with the caller — with no audit event. Not executed (destructive on real test data); the code path is unambiguous and the GET proof establishes the missing guard.

**Verdict: cross-tenant read of ~all trips + cross-tenant hard delete. Blocker.**

## T2 — Timeline IDOR (NEW finding, CONFIRMED Tier 5)

`GET /api/trips/{trip_id}/timeline` (`spine_api/routers/trip_observability.py:54`) has **no `Depends(get_current_agency)`** — the agent-events route directly above it (`:46-47`) does scope. Runtime: probe session → `GET /api/trips/trip_db11a60e0fad/timeline` → **200** (events list; leaks decision/audit history of any agency's trip).

## T3 — Bulk review action: unscoped cross-tenant mutation (NEW finding, CONFIRMED Tier 5)

`POST /analytics/reviews/bulk-action` (`spine_api/routers/analytics.py:169`) has no auth dependency and no agency check; it calls `process_review_action(trip_id=…)` for arbitrary trip_ids. Runtime: probe session submitted an action against an arbitrary trip_id and the backend **executed the mutation path** (failed only because the probe trip didn't exist: `'Trip not found'` — the code ran). Against a real victim trip_id this mutates another agency's review state. **Blocker** (write path).

## T4 — Unscoped override read (NEW, medium)

`GET /overrides/{override_id}` (`spine_api/routers/legacy_ops.py:721-725`) — no auth dep, no agency scoping; reads any override by ID. Needs an override ID to exploit (UUID-guessable only by enumeration), hence medium.

## T5 — The good news: the standard guard pattern holds everywhere else (verified, 48 call sites)

Full classification of all 48 `TripStore.get_trip(` call sites: **31 router/service sites are SCOPED** with an immediate `trip.get("agency_id") != agency_id` check (trust_scorecard, messaging, team_workflows, trip_actions, inbound, trip_observability:46, legacy_ops ×8, yield_arbitrage ×2, followups ×4, trip_lifecycle, analytics:133/162, concierge ×2). **Zero other authenticated IDORs found.** 7 storage-layer primitives are unscoped by design (store layer has no agency context) and not independently exploitable.

**The architectural problem**: the guard is a manually-repeated convention, and every miss is a silent cross-tenant hole. T1–T4 are the four misses. `TripStore.get_trip_for_agency` exists but is used in only one router.

**Recommendation (first-principles, additive)**: make scoping the default, not the convention —
1. Fix T1–T4 directly (add `Depends(get_current_agency)` + `get_trip_for_agency`, or for public-checker: scope artifact reads to a traveler-safe projection + restrict DELETE to the owning agency with permission + audit event).
2. Migrate all router call sites to `get_trip_for_agency` (storage-layer enforcement).
3. Add a contract-surface test per fixed route asserting cross-agency access → 404 (the tests exist as a pattern: `test_frontier_tenant_isolation.py`).
4. Long-term: a CI lint rule (ruff custom or the existing `scripts/validate_decoupling.py` pattern) flagging bare `TripStore.get_trip(` in routers without an adjacent agency check.

## T6 — RLS reset swallow (baseline, re-verified static)

`get_rls_db` finally-block swallows reset failures (`core/rls.py:242-247` — bare `except Exception: pass`). If the reset fails, a pooled connection retains `app.current_agency_id`; a subsequent request on that connection that doesn't set the config inherits the previous tenant. `rls_session` (`:273-277`) does NOT swallow — inconsistent defensive posture (the exact Pattern-6 failure in AGENTS.md). Fix: log +, on reset failure, discard the connection instead of returning it to the pool.

## T7 — Session/token lifecycle gaps (design-level, from security track; folded here)

- Refresh tokens are stateless JWTs with no server-side revocation or rotation; logout only clears the cookie. A stolen refresh token is valid 7 days. Recommendation: refresh-token rotation with a server-side allowlist/denylist table (also enables "log out all sessions").
- Trips are hard-delete only; no soft-delete/recovery, and destructive ops (incl. T1 DELETE) emit no audit event. For a multi-tenant ops tool, soft-delete with a retention sweeper is the launch-safe posture.
- `SPINE_API_DISABLE_AUTH` posture covered in DD-1 F0 (dev server runs with it ON; startup assertion recommended).

## Decisions needed from operator

1. Public-checker GET/export: who is the audience? (a) traveler (→ make truly public but return a traveler-safe projection, no operator notes/internal fields), or (b) operator (→ keep behind auth, scope to agency). Current state is the worst of both.
2. Approve the `get_trip_for_agency` migration + CI lint rule (prevents T1–T4 recurrence class).
3. Soft-delete vs hard-delete policy for trips before launch.

## "Anything else?" (motto §0.1.1)

- The probe signup itself demonstrated baseline B11: ungated self-serve workspace creation worked with a fake email and no verification — a disposable-account vector for abusing any authenticated-but-unscoped endpoint (T1–T3). Tenancy fixes and signup gating interact: either reduces the other's blast radius.
- 18,734 trips on the main test agency (per `Docs/KNOWN_TEST_DATA_ACCUMULATION.md`) means any enumeration-style attack in dev has a huge surface — dev DB hygiene is a launch task too.
- Positive: RLS with FORCE on 12 tenant tables means even if application-layer scoping is missed on SQL-backed reads through `get_rls_db`, the DB denies cross-tenant rows. T1/T2/T3 leak anyway because they go through paths that fetch by primary key (RLS policies on pk lookups still pass when the session has no agency context set). Do not rely on RLS as the only line.
- Not verified: whether FileTripStore backend enforces any of this (it can't — file store has no RLS; another reason TRIPSTORE_BACKEND=sql must be pinned, DD-2 D4).

## Status

T1–T3: **verified Tier 5, unfixed — blockers.** T4–T7: verified static/runtime, fixes proposed. Decisions 1–3 await operator. Next: DD-4 (LLM boundary & PII).
