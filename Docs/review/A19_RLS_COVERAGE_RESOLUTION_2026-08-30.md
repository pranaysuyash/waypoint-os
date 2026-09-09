# A-19 / RQ-03 Resolution — RLS Coverage & Exempt-Table Verdicts (2026-08-30)

**Closes:** A-19 (RLS coverage gap, Wave 2.2–2.3) · RQ-03 (are the 4 RLS-exempt tables cross-tenant reachable?) · partial A-20 (the 4 unmigrated frontier tables — migration added; CI drift gate remains open)
**Companion:** findings register rows updated; probe suite `tests/test_cross_tenant_router_probe.py`

---

## 1. Live inventory (verified 2026-08-30)

The audit's numbers held exactly: 6 routers used `get_rls_db`, 6 used unscoped `Depends(get_db)`, none mixed. RLS machinery (`spine_api/core/rls.py`) is sound by design: ContextVar populated by `get_current_membership` (auth.py:155/165) on every authenticated request; `get_rls_db` sets transaction-safe session config and resets on exit.

**Honest security posture note — CORRECTED 2026-08-31:** the original note below claimed RLS was dormant (owner bypasses ENABLE-without-FORCE). Live pg_class verification during the F-19/F-20 hunt proved that wrong: `trips` and `booking_collection_tokens` carry **FORCE RLS** (`relforcerowsecurity = true`), so the database is enforcing isolation **right now** — policies are fail-closed (`agency_id = current_setting('app.current_agency_id', true)`: no context ⇒ zero rows). Only `memberships`/`workspace_codes` are ENABLE-without-FORCE (by design, auth chicken-and-egg). Consequence: any router querying a FORCE-RLS table without setting the context sees *nothing* — and endpoints that appeared to work were surviving on stale session context bleeding through pooled connections (the exact hazard `rls.py` documents). The conversions below were therefore correctness-critical, not just posture alignment. See `architecture/TENANCY_ISOLATION_MODELS_LEARNING_2026-08-31.md` addendum.

<details><summary>Original (incorrect) note</summary>

**Honest security posture note (verified):** the app currently connects as the table **owner**, and these tables use ENABLE-without-FORCE RLS — so RLS is currently *dormant defense-in-depth*, and the **active** isolation guard is application-level `agency_id` filtering. Unscoped `get_db` was therefore not a live leak path; it was (a) a correctness gap the moment a non-owner role cutover happens, and (b) an inconsistency that made the security posture unverifiable. The checker (`scripts/check_rls_coverage.py`) validates table posture: **12 protected / 4 exempted / 15 total with agency_id — passed.**

</details>

## 2. Router conversions (Wave 2.2)

| Router | Endpoints w/ db dep | Action | Rationale |
|---|---|---|---|
| `integrations.py` | 2 | **Converted + parallel system retired** | It hand-rolled `set_config(..., false)` — **session-scoped**, the exact pooled-connection bleed hazard `rls.py`'s docstring warns against. Replaced with `get_rls_db`. |
| `team.py` | 6 | Converted | All endpoints already agency-scoped via `membership_service(agency_id=...)`; conversion adds the DB-level guard and consistency. |
| `frontier.py` | 4 | Converted | JWT-sourced agency_id, read path checks ownership; conversion aligns posture for the exempt tables' only gateway. |
| `audit.py` | 1 | Converted | Single tenant-facing read, already filtered (`AuditLog.agency_id == membership.agency_id`); conversion harmless (table RLS-exempt) and consistent. |
| `analytics.py` | 1 | Converted | `TripStore`/`membership_service` calls already agency-scoped. |
| `auth.py` | — | **Documented deviation** | Pre-auth endpoints (signup/login/refresh/reset) cannot be tenant-scoped — the caller has no agency yet; `/me` derives everything from the JWT membership. This matches the RLS design's own `RLS_FORCE_EXEMPT_TABLES` (memberships/workspace_codes queried before the agency is known). |

**Totals: 12 dependencies converted across 5 routers; 1 documented deviation. Residual unscoped: auth.py only.**

## 3. RQ-03 verdict — the four RLS-exempt tables

| Table | Query sites | Verdict |
|---|---|---|
| `audit_logs` | Writer: `core/audit.py` (chain appender, writes all agencies' events by design — no cross-tenant read). Reader: `routers/audit.py:82` — **agency-filtered** (`AuditListResponse.entries` probe passes). Chain verification (`core/audit.py:92`) reads head hash only, no agency semantics. | **SAFE — query-scoped** (exemption rationale now verified true) |
| `ghost_workflows` | Only `routers/frontier.py`: write injects JWT agency; read is `id`-lookup + `agency_id != caller → 404` (existence not confirmed). No list endpoint. Cross-tenant probe passes. | **SAFE — app-scoped; single gateway** |
| `emotional_state_logs` | Only `routers/frontier.py` POST (JWT agency, write-only; no read endpoint exists). | **SAFE — write-only, JWT-scoped** |
| `legacy_aspirations` | **No router endpoints at all** (model only; no read/write path in the request flow). | **SAFE — unreachable** (flag for the negative-space map, EX-05) |

**RQ-03 answer: none of the four tables is cross-tenant reachable.** Each is either agency-filtered at its single read path, write-only with JWT-scoped agency, or entirely unwired. The exemption list's stated rationale is now verified rather than assumed.

## 4. Side effect: A-20 partially resolved (probe caught it live)

The first probe run failed with `relation "ghost_workflows" does not exist` — runtime proof of A-20: the four frontier model tables had **no migration files**, so every frontier endpoint touching them was broken on any properly-migrated database. Fixed with additive migration **`alembic/versions/add_frontier_tables.py`** (head `add_frontier_tables`), creating the four tables exactly per the models (indexes + check constraints + `agency_id → agencies.id` CASCADE FKs). Applied locally; DB verified at new head. **Remaining for A-20:** the CI drift gate (`alembic check`) so this class of drift cannot recur silently.

## 5. New cross-tenant probe suite

`tests/test_cross_tenant_router_probe.py` — 5 tests under the disable-auth two-tenant regime (token agency-claims select the tenant): ghost-workflow read fails closed cross-tenant (404, existence not confirmed) and succeeds for the owner; team-member list/detail scoped; audit list returns only caller-agency entries; integrations smoke post-conversion. Plus the existing suites (`test_tenant_isolation*`, `test_frontier_tenant_isolation`, `test_rls*`) — **74+ tests green in the isolation scope**.

Mutation check (plan 2.2 S3): the policy mechanics are pinned by `tests/test_rls.py` / `test_rls_live_postgres.py`; under the current owner-role regime a removed `set_rls_agency` is not observable in query results (RLS dormant), which is precisely why the probe suite pins the app-level guards that are active today. Re-verify at any non-owner-role cutover.

## 6. Full-suite verification & the live-server caveat

- Ruff clean on all changed files; RLS checker passed (12/4/15).
- Focused suites: probe + isolation + converted-router behavior suites — **all green**.
- Full suite (CI-identical runner): three runs produced three different failure sets (1, then 4, then 13) **correlated with the dev server running on :8000** — with the server up, integration tests execute mid-suite against the shared DB (25-minute runtime vs ~70s clean) and manufacture phantom failures; every failing test passes in isolation, and the probe file itself passed in the run where 13 others failed. The clean-baseline runs (server down) were 3,215–3,219 passed with 0–1 order-flakes.
- **Action taken:** `scripts/run_backend_tests.sh` now warns loudly when it detects a live server on :8000, and its header documents that citable baselines require the server stopped. Registered as **F-19** (full-suite phantom failures under live-server contention) — the systemic fix (per-test DB namespacing or integration-test exclusion by default) is a follow-up.

## Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
