# FND-0219 — Durable Public Proposal Capability Token Store (2026-09-14)

Status: **CLOSED (fixed)** — see `Docs/review/FINDINGS_STORE.jsonl` /
`FINDINGS_LIVE.md` for the lifecycle row and full evidence string.
Implementing session: `zcode-impl-2026-09-14`.

## Problem (as still true at implementation time)

Prior hardening rounds (PT-01…PT-06) had already made proposal tokens
HMAC-signed, TTL'd, and agency-bound, but three FND-0219 defects remained:

1. `_PROPOSAL_REGISTRY` — an unbounded, process-local dict of full
   `PublicProposalView`s keyed by raw token. No size bound, no entry TTL; it
   also served as the only store for option-selection state.
2. The durable revocation file stored **raw token material** as plaintext
   keys — a capability credential sitting in a JSON file next to trips.
3. No consent artifact: nothing recorded *who* authorized external sharing
   of a trip's proposal when a token was minted, and no durable (SQL,
   multi-replica) credential store existed.

## Design (first principles: a public token is a capability URL — a real credential)

### Storage

`spine_api/services/proposal_token_store.py` models the repo's canonical
durable-backend pattern (`src/agents/idempotency.py`):

- Backends: `memory` (tests / single worker), `sql` (durable
  `proposal_access_tokens` table on the app async engine via
  `spine_api.persistence._run_async_blocking`), `auto` (sql when
  `DATABASE_URL` is set). Selected by `SPINE_API_PROPOSAL_TOKEN_BACKEND`.
- Issue is idempotent per `token_hash`: concurrent INSERTs race one unique
  conflict; the loser replays the stored row. Replay never refreshes TTL or
  overwrites the consent artifact (replaying cannot extend a credential).
- The backend lazily `create_all(checkfirst)`s its table (additive-only
  safety net); the canonical schema path is alembic
  `add_proposal_access_tokens` (additive create-table only,
  `down_revision=add_audit_logs_seq`).

### Token security

- v3 wire format `propv3_<secrets.token_urlsafe(32)>`: 256-bit opaque
  material; the URL leaks nothing about the trip. All binding lives in the
  durable row.
- Durable storage keeps only `sha256(token)` (unique key) + a 16-hex
  `lookup_prefix` for operator diagnosis. Raw material is never stored or
  used as a lookup key anywhere.
- Legacy v2 `prop_{trip}_{agency}_{exp}_{hmac}` tokens keep verifying via
  the stateless path (signature → TTL → file revocation → resource
  binding). Pre-hardening 16-hex tokens fail closed (demo allowlist only,
  `PUBLIC_PROPOSAL_DEMO_MODE=1`). No silent upgrades.

### Row schema (spine_api/models/proposal_tokens.py)

`id, token_hash (unique), lookup_prefix, format_version, agency_id,
trip_id, proposal_id (nullable), issued_at, expires_at, revoked_at
(nullable), consented_by, consented_at, purpose`.

- `format_version` makes replay explicitly versioned (`v3` opaque vs `v2`
  signed).
- `consented_by` / `consented_at` / `purpose` are the consent artifact —
  the authenticated principal who authorized external sharing.
- Not RLS-scoped (documented in model + migration): traveler verification
  runs outside any tenant session; rows are addressed only by the opaque
  credential hash. Precedent: `idempotency_keys`. The table IS explicitly
  registered in `spine_api/core/rls.py::RLS_EXCLUDED_AGENCY_TABLES` (the
  live-Postgres RLS coverage test enforces that every `agency_id`-bearing
  table is either RLS-protected or deliberately excluded with rationale).

### Verification order (no oracle)

hash match → TTL not elapsed → not revoked → resource binding from the row.
All v3 failures (expired / revoked / unknown) return the identical reason
string and therefore the identical HTTP 410 + detail. Store outage fails
closed (503), never open. The v2 401 (malformed/bad signature) vs 410 split
is pre-existing, deliberate, and test-pinned.

### Bounded projection cache

`_PROPOSAL_VIEW_CACHE` replaces the unbounded registry: 4096 entries max
(FIFO eviction), 1-hour entry TTL, and it is **never** consulted for
authorization — every request re-verifies the credential; revocation evicts
the entry.

### Revocation

- v3: `revoked_at` on the durable SQL row (multi-replica safe).
- v2: the PT-05 JSON file, now **hash-keyed**; legacy raw-key entries are
  normalized (re-keyed by hashing) on load and on merge-write, so old
  revocations keep working and raw material leaves the file at the next
  write.
- Both paths evict the view cache.

### Issuance & consent

`issue_proposal_capability(trip_id, agency_id, consented_by, purpose,
proposal_id=None, ttl_hours=None)` — requires the consent principal; keeps
issuance behind the existing authenticated compile flow.
`proposal_compiler` mints share tokens through it (recording the consent
artifact, `purpose="compiled_proposal_share"`) and now binds the credential
to `agency_scope` instead of the legacy hardcoded `"system"` (which could
never resolve a persisted proposal for non-system agencies).
`journey_graph` resolves the issuing agency via `_verified_agency_for_token`
(v3 → durable row; v2 → signed field).

## Files

New: `spine_api/models/proposal_tokens.py`,
`spine_api/services/proposal_token_store.py`,
`alembic/versions/add_proposal_access_tokens.py`,
`tests/test_public_proposal_token_store.py`,
`tools/verify_proposal_token_sql_backend.py`.
Modified: `spine_api/routers/public_proposals.py`,
`spine_api/routers/journey_graph.py`,
`src/orchestration/proposal_compiler.py`, `spine_api/models/__init__.py`,
`spine_api/core/rls.py` (RLS exclusion registration, see above),
`tests/test_public_proposals.py`,
`tests/test_booking_fulfillment_lifecycle.py`, `.env.example`.

## Verification receipts (2026-09-14)

- Focused tests: `tests/test_public_proposal_token_store.py` — 15 passed
  (roundtrip + traveler response-shape key-set parity, expired, revoked +
  restart durability + uniform errors, trip binding incl. journey-graph
  cross-trip 404, hashed-at-rest on memory and aiosqlite SQL table,
  idempotent replay, explicit versioning, legacy raw-key normalization,
  backend env selection).
- Regression: `tests/test_public_proposals.py` 44 passed; affected suites
  (booking fulfillment lifecycle, journey graph hydration, P1 hardening,
  payment mandate ledger, PA authority enforcement, PA wave 2, proposal
  compiler e2e) 68 passed; proposal-name sweep 129 passed.
- Real Postgres runtime proof: `tools/verify_proposal_token_sql_backend.py`
  — 5/5 checks (issue → VALID, idempotent replay without TTL/consent
  refresh, hash+prefix only in the durable row, durable revocation)
  against `waypoint_os`.
- `ruff check` clean on all changed files.
- Traveler contract: `PublicProposalView` unchanged; frontend consumer
  `frontend/src/app/p/[token]/page.tsx` unaffected (route map unchanged).

## Operational notes / follow-ups

- Production / multi-worker deployments MUST run with
  `SPINE_API_PROPOSAL_TOKEN_BACKEND=sql` (or `auto` + `DATABASE_URL`), same
  as the idempotency backend. Guidance in `.env.example`.
- Default v3 TTL is 30 days (`PROPOSAL_TOKEN_TTL_HOURS` to override);
  document any deviation in agency ops runbooks.
- `tools/verify_proposal_token_sql_backend.py` leaves one revoked,
  test-scoped row (`trip_id=trip_sql_verify_fnd0219`) per run — audit
  noise by design, additive only.
- Un-actioned by design: v2 tokens minted before this change have no
  consent row; they remain verifiable via the stateless legacy path until
  they expire (≤7 days).
