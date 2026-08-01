# DD-1: Public Surface Integrity — Proposals, Stage-Advance, Waitlist, SSE

**Date**: 2026-08-01 · **Parent**: `Docs/LAUNCH_AUDIT_BASELINE_2026-08-01.md` (B1, B2, B5, B12, H9, H13)
**Evidence tier**: Tier 4 (runtime reproduction on a clean instance, port 8010, `.env` loaded, auth ON) + Tier 4 on the operator's dev server (port 8000, `SPINE_API_DISABLE_AUTH=1`).
**Method note**: first reproduction attempt hit a pre-existing dev server on :8000 running with `SPINE_API_DISABLE_AUTH=1`; all conclusions re-verified on a clean instance. This itself produced Finding F0.

---

## F0 — The dev server runs with auth globally disabled (live instance of baseline H4)

- The operator's long-running dev server (PID 71047, started Fri 6PM) has `SPINE_API_DISABLE_AUTH=1` in its process environment (set twice; not from `.env`, not from `dev.sh` — most likely a shell export).
- Effect: the **entire API is unauthenticated and cross-tenant** on that process. Any local process/browser tab can read and mutate every agency's data. This is exactly the env-var safety-posture theme (baseline Theme 2).
- Decision needed: kill the habit, not just the flag — add a startup assertion: if `ENVIRONMENT=production` and `SPINE_API_DISABLE_AUTH` set → refuse to boot. Also unset it in the dev shell and use per-test toggling instead (the codebase already supports call-time toggling, `server.py:1114-1115`).

## F1 — Proposal links are dead in any correctly-configured environment (baseline B2, CONFIRMED Tier 4)

- `GET /api/v1/proposals/token/{token}` and `POST .../accept` (`spine_api/routers/trust_scorecard.py:142,215`) are documented "Does not require agency JWT", but the router is mounted with `Depends(_auth_or_skip)` (`server.py:1145`) and `/api/v1/proposals/*` is not in `PUBLIC_PREFIXES` (`core/middleware.py:26`).
- Runtime: `GET /api/v1/proposals/token/prop_test123` → **401**; `POST .../accept` → **401**; `GET /api/v1/messaging/webhook/whatsapp?...` → **401** on the clean instance.
- Consequence: the ADR_INTERACTIVE_PROPOSAL_WEB_LINK feature cannot work for a traveler. It only "works" on the auth-disabled dev server — which is why nobody noticed.

## F2 — Garbage tokens serve a fabricated proposal (baseline B1, CONFIRMED Tier 4)

- On the auth-disabled server: `GET /api/v1/proposals/token/prop_randomtoken999` → **200** with a hardcoded "Taj Exotica Resort & Spa, $4,200, Goa" proposal, fake `transparency_badges` ("VERIFIED_PARTNER — direct supplier agreement", "PRICE_LOCK_72H — guaranteed"), and `suitability_match_pct: 95.0` (`trust_scorecard.py:159-183`).
- `POST /token/{token}/accept` on an unknown token returns `ok: true`, "Proposal accepted!", `trip_id: "trip_demo123"` (`:234-243`) — a fake acceptance of a nonexistent trip.
- The frontend mirrors this: `proposals/[proposalId]/page.tsx:30-50,69-90` seeds the same fake data and silently substitutes it on fetch failure.
- **This is a motto §0.11 customer-facing-claims violation**: "Full refund eligibility per contract terms" and "Guaranteed price lock for 72 hours" are legal/financial claims shown to travelers with zero backing data. Add to the launch-claim registry as prohibited until data-backed.
- Related: the trust-scorecard endpoint itself fabricates — `safety_score = 96.0` hardcoded, highlights like "2.5h connection buffer" and "resort fees included" invented (`trust_scorecard.py:58-86`).

## F3 — Even if F1/F2 were fixed, the generated link 404s on the frontend

- Backend generates `web_url = f"https://waypoint-os.com/p/{token}"` (`trust_scorecard.py:121`). Frontend has **no `/p` route** — the proposal page lives at `/proposals/[proposalId]`. Hardcoded production domain also ignores environment.
- Token weaknesses (baseline H13, confirmed): 16-hex token, `expires_at` set to *now* and never enforced (`:119`, only two "expires" references in the file), no rate limit on `/token/*`, and lookup scans `TripStore.list_trips()` across **all** agencies per request (`:152,221`) — O(n) cross-tenant scan and perf-DoS vector.

## F4 — Stage-advance button is dead in production (baseline B5, CONFIRMED)

- Backend route exists and is mounted: `PATCH /trips/{trip_id}/stage` (`spine_api/routers/trip_lifecycle.py:88-89`, router has no prefix; runtime → 401 not 404, so the route resolves).
- Frontend calls `api.patch(`/trips/${tripId}/stage`)` (`frontend/src/lib/api-client.ts:995`) — missing the `/api` prefix every other call uses → hits the Next.js page router, not the BFF.
- Even with the prefix fixed, `trips/{id}/stage` has **no entry in `route-map.ts`** (deny-by-default proxy → 404). Two independent breaks on one operator action.
- Only mocked unit tests cover this path — the documented 2026-04-29 failure class repeating itself.

## F5 — Waitlist captures leads into the void (baseline B12, CONFIRMED)

- `marketing-client.tsx:78,85`: both Enter-key and button handlers just call `setSubmitted(true)`. Repo-wide grep: no waitlist endpoint, table, or store anywhere. Launch-traffic emails are silently discarded while the UI says "You're in."
- Simultaneously the live landing (`landing-v5.tsx`) pushes "Create workspace" — so the site makes two contradictory acquisition promises, one of which is fake (baseline: conflicting CTA finding).

## F6 — SSE route can never work (baseline H9, CONFIRMED)

- `frontend/src/app/api/stream-events/[runId]/route.ts`: reads cookie `spine_auth_token` (`:29`) while the whole stack issues `access_token`; requires runId to match `^run_…` (`:48`) while backend run IDs are bare UUIDs; proxies to `/runs/{id}/stream`, which does not exist in the backend (grep: no stream route in `run_status.py`/`server.py`). Triple-dead; frontend silently falls back to polling forever.

---

## Root-Cause Pattern

Every DD-1 failure sits on a **public/unauthenticated boundary that was only ever tested on an auth-disabled dev server**. The dev loop (F0) masked F1–F3; mocked tests masked F4; no backend masked F5/F6. None of these surfaces has a single runtime-verified pass through a correctly-configured stack.

## Options & Recommendations (decision-grade, per motto §0.12)

**F1/F3 proposal links — Option A (recommended): dedicated public router.** Move `/token/{token}` + `/accept` into a separate `APIRouter` mounted without `_auth_or_skip`, add `/api/v1/proposals/token` to `PUBLIC_PREFIXES`, enforce token expiry + rate limit, fix `web_url` to use the real frontend route + env-driven base URL. Option B: signed-URL scheme (HMAC token, no DB lookup) — better long-term, larger change; recommend as follow-up ADR.
**F2 — delete the demo fallback entirely.** A dead link must 404, never fabricate. Remove the frontend fake-seed + silent-substitute in the same pass. Non-negotiable before any customer sees this surface.
**Trust scorecard claims —** strip fabricated scores/badges to only what packet data supports, or gate the feature off until it is data-backed. Register remaining claims in the launch-claim registry (motto §0.11.1).
**F4 —** add `/api` prefix in `api-client.ts:995` + add `trips/{id}/stage` to `route-map.ts` + one contract-surface test. Small, surgical.
**F5 — decide acquisition posture first** (the open P0 question): if open signup → delete the waitlist widget; if waitlist → wire it to a real store (one table + endpoint, or an external list tool). Do not ship a fake form.
**F6 —** either implement `/runs/{id}/stream` properly (backend SSE endpoint + cookie name + UUID regex) or delete the route and keep honest polling. Deleting is the launch-cheap option; SSE is a post-launch enhancement.
**F0 —** startup assertion + unset the flag in the dev shell.

## "Anything else?" (motto §0.1.1)

- The `accept` endpoint mutates stage to `booking` with no payment, no notification to the agency, and no audit event — even for real tokens. When F1 is fixed, acceptance must emit an audit event + agency notification, or "Proposal accepted!" is another broken promise.
- `docs`/`redoc`/`openapi.json` are in `PUBLIC_PATHS` — fine for dev, should be env-gated for production (API schema is an attack map).
- Verified-but-not-fixed: no code was changed in this deep-dive; all fixes above are proposals awaiting operator decision.
- Not verified: the full proposal flow with a real authenticated agency (needs a logged-in session + real trip); recommended as the first e2e test when DD-7 lands.

## Status

Findings F0–F6: **verified, unfixed, awaiting decisions**. Next: DD-2 (deployment path).
