# EX-04 — Capability-Token Design: Anonymous Result Access & Sharing (2026-09-08)

Status: design exploration. Gate: D-01 (moot if the consumer surface is killed). Implements AUD-04 + AUD-08 properly. Related: FT-G2/FT-G3.

## Problem (live-probed 2026-09-08)

`AuthMiddleware` allowlists only `/api/public-checker/run` and `/events` (`spine_api/core/middleware.py:32-39`), while the router is documented "public-by-design" (`spine_api/server.py:1483-1485`). Result: `GET`/`export`/`DELETE /api/public-checker/{trip_id}` return 401 for anonymous users — the exact consumer the surface serves. The result view still renders from the run response, but "Manage your saved data" (export/delete) is dead, and the GDPR-style erasure path cannot be exercised. Adding the trip routes to `PUBLIC_PREFIXES` would fix UX but make any trip readable/deletable by anyone holding the ~48-bit id (`trip_{uuid4().hex[:12]}`, `persistence.py:407`) — enumeration-impractical but wrong-shaped authorization (any authenticated agency user could also read any checker trip today; that agency-agnostic read is its own finding).

## Design: capability token on the run response

The repo already has this pattern: proposal share tokens (`/api/v1/proposals/token/`, signed, revocable — rebuilt in the 2026-09-02 security wave with required `PROPOSAL_SIGNING_KEY`, durable revocations). Reuse that machinery's shape, not a new one:

1. **Issue:** successful `/run` response gains `access_token` (random 256-bit, stored hashed against `trip_id` in a `public_checker_access_tokens` table, or reuse the proposal-token table with a scope column — decision during implementation).
2. **Use:** `GET`/`export`/`DELETE` accept `Authorization: Bearer <access_token>` or `?t=<token>`; middleware allows the routes but the *router* enforces token↔trip binding. No agency auth involved.
3. **Delete-after-read option:** the token grants exactly `delete` once and `get`/`export` repeatedly — matching the one-time-analyst mental model.
4. **Sharing (replaces dead `/shared/` routes):** optional `share_token`, separately revocable, resolves to a read-only `/itinerary-checker/shared/[token]` page (FT-G3) — this time the route and the allowlist entry ship together, so the dead-allowlist class of defect cannot recur.
5. **Kill-switch interplay:** disabled checker (FT-05) returns 503 on token routes too.
6. **Retention interplay:** when the D-03 TTL deletes the trip, cascade-delete tokens.

## Invariants / tests

- Token required for GET/export/DELETE; wrong token → 404 (not 403 — no existence leak).
- Token bound to trip; cross-trip use → 404.
- Revocation durable (no in-memory-only registry — PT finding from the token rebuild applies).
- Anonymous result view works end-to-end in a browser E2E (the current 401 regression gets a test that would have caught it — FT-04 noted the fetch path had zero coverage).
- Existing agency dashboards still cannot list checker trips (isolation unchanged).

## Sizing

Backend: token table + issue/verify helpers + router guards ≈ 1 focused unit. Frontend: token capture from run response, attach to fetches, share-link construction ≈ 1 unit. Tests: ~10–15 cases. Reversible; no schema change to trips.
