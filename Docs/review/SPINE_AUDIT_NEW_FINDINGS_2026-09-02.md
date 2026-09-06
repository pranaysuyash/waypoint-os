# Spine Audit — New Findings (Diff-Level, 2026-09-02)

*Author: ZCode session audit (independent of the Gemini wave; findings arise from line-level review of the shared files Gemini modified — per the all-tree-work-is-shared doctrine).*
*Scope: `spine_api/routers/public_proposals.py` (proposal token system), frontend VCC fetch fix, `IdempotencyRegistry` seam, plus confirmations. Companion: `GEMINI_WAVE_FINDINGS_FOR_REVIEW_2026-09-02.md` (Section B maps GM-04 to PT-01…PT-06 below).*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## New findings (mine, PT series)

### PT-01 — Hardcoded fallback signing secret (P0-adjacent, security)

`spine_api/routers/public_proposals.py:87` — `_SECRET_KEY = os.environ.get("PROPOSAL_SIGNING_KEY", "waypoint_secret_proposal_key_2026")` (`public_proposals.py:86`). Any deployment that has not set `PROPOSAL_SIGNING_KEY` signs proposal capability tokens with a public, committed constant: anyone can forge a valid token for **any trip id**. The database credential got exactly this treatment fixed today (A-18: `database.py` now hard-fails without `DATABASE_URL`) — the signing key needs the same posture: required, no default, startup assertion.
**Fix:** mirror the `database.py` pattern — fail at import/startup when unset (or generate an ephemeral key with a loud warning in dev only).

### PT-02 — "Legacy" token bypass: arbitrary junk ≥16 chars authorizes `trip_legacy` (P0-adjacent, security)

`verify_proposal_token` (`public_proposals.py:117` and `:132`, the `len(token) >= 16 → return True, "legacy_ok", "trip_legacy"` branches, two sites): any attacker-supplied string of ≥16 characters that fails the signed-shape parse is accepted as valid and resolves to the demo proposal `trip_legacy`. This is an unauthenticated-access path to whatever `trip_legacy` maps to, and — worse for the security posture — it makes the "Invalid cryptographic token signature" branch dead code for all junk input (verification silently succeeds instead). Verified by reading both legacy branches; the reconciliation audit's GM-04 flagged the bypass generically — these are the exact lines and the exact reachable trip.
**Fix:** delete both legacy branches; if demo tokens must keep working, allowlist the specific known demo token strings explicitly instead of a length heuristic.

### PT-03 — Verify loop hardcodes fallback agencies incl. the test-agency UUID (P1, security + correctness)

The signature check reconstructs the payload with `:system:` and, on mismatch, retries a hardcoded list `["system", "default", "agency_test", "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"]` — the last being the shared test agency id from `AGENTS.md`. Two problems: (a) a production agency id absent from this list cannot verify its own tokens (functional breakage the day a real agency uses the feature); (b) the test agency is a permanent verification scope in production code.
**Fix:** store the issuing `agency_id` in the signed payload (it already is, at generation) and in the token itself, or persist tokens server-side so verification reads rather than guesses.

### PT-04 — Agency id is signed but never used in verification (P1, design)

`generate_signed_proposal_token(trip_id, agency_id)` signs `{trip_id}:{agency_id}:{exp_ts}`, but `verify_proposal_token` reconstructs `{trip_id}:system:{exp_ts}` — the actual `agency_id` never participates in verification except via the PT-03 guess-list. The parameter is decorative. This is the root cause of PT-03.
**Fix:** encode agency into the token (`prop_{trip_id}_{agency_id}_{exp_ts}_{sig}`) and verify against it.

### PT-05 — Token revocation is an in-memory set (P2)

`_REVOKED_TOKENS: set[str] = set()` — advisor-initiated revocations are lost on every process restart and invisible across workers. Revocation is a trust control; as implemented it is advisory only.
**Fix:** persist revocations (TripStore/DraftStore pattern or the proposal registry row status it already touches).

### PT-06 — HMAC signature truncated to 16 hex chars = 64 bits (P2)

`hexdigest()[:16]` — 64-bit truncation of SHA-256. Not trivially brute-forceable remotely with TTL + rate limits, but below modern guidance (128-bit) for a capability token that grants booking actions on a public route.
**Fix:** use the full hex digest (or ≥32 chars). Trivial change; tokens get longer, which is fine.

### PT-07 — Frontend VCC "fix" hardcodes `http://127.0.0.1:8000` (P1, deployment)

The chronicle's GF-05 fix replaces the failing relative `/api/v1` fetch with an explicit `http://127.0.0.1:8000` backend URL in frontend code. This re-introduces the exact class of bug the BFF proxy exists to prevent: every non-local deployment (staging, prod, any other browser origin) gets a cross-origin call to `127.0.0.1`, which fails. "Graceful fallback" does not make the feature work; it makes it silently absent.
**Fix:** fix the proxy rewrite for that path in `next.config` / BFF route map (the repo's canonical pattern), revert the hardcoded URL.

### PT-08 — `IdempotencyRegistry` is in-process; multi-worker deployments silently lose duplicate protection (P2, latent prod)

`spine_api/routers/inbound.py` comments admit the seam ("In-process backend — see IdempotencyRegistry docstring for the multi-worker seam"). With >1 uvicorn worker or multiple replicas, retried intake mints duplicate trips again — the exact bug N-1 was built to kill. The register N-1 work is good; the seam is a deployment cliff.
**Fix:** back the registry with the DB (unique constraint on idempotency key) before multi-worker/replica deployment; meanwhile document the single-worker constraint in the deployment doc (which the new Dockerfiles make imminent — the default Docker/uvicorn story must pin workers=1 or use the DB backend).

### PT-09 — Twelve new routers rely on global AuthMiddleware ordering (P2, hardening consistency)

Already flagged as GM-07; my addition after reading the diffs: the new routers' security posture is invisible at the router level — a future refactor of middleware ordering silently publicizes them. The existing `_auth_or_skip` pattern makes the security posture per-route and greppable.
**Fix:** add explicit auth dependencies when landing the hardening commit (GM-01 (A)).

## Confirmations (good work in the same diffs — recorded so the reviewer doesn't re-litigate)

- **PT-OK-1**: `database.py` A-18 fix is correct and matches the doctrine — no committed credential defaults, hard fail with actionable message, and the NullPool experiment note honestly documents why it was rejected plus the flush→refresh→commit RLS fix it exposed (applied in `collection_service`/`document_service`).
- **PT-OK-2**: `startup_assertions.py` staging kill-switch extension closes a real gap (staging previously passed with auth disabled).
- **PT-OK-3**: inbound idempotency (N-1) and merge-precedence conflicts (N-3) implementations read correctly, including 409-on-in-flight-duplicate semantics and conflict-with-kept-value responses.

## Priority order for the reviewer

1. PT-01 + PT-02 (public-route forgery/bypass — small diffs, big impact)
2. GM-03 (fake Stripe verify) — same class
3. PT-03/PT-04 (token design) — fold into the PT-01/PT-02 fix
4. PT-07 (VCC URL) + PT-08 (idempotency seam) before any Docker/deploy step
5. PT-05/PT-06/PT-09 — hardening pass
