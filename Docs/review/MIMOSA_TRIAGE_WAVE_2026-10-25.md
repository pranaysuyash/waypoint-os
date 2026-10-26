# Mimosa Triage Wave — 2026-10-25 (FND-0374 closure record)

**Scan:** `scan-2026-10-24T19-17-28.459Z-e60324843059` (deep, sealed sha256:9a799cf7…b5e8), 128 findings.
**Method:** per the historical MITIGATED bar (FND-0292 lineage) — every candidate verified against the
actual runtime architecture (FastAPI DI auth, RLS/GUC session scoping, capability-token surfaces)
with file:line evidence; static "inconclusive" verdicts resolved by code reading, not bulk dismissal.
**Outcome:** 128/128 adjudicated. 2 real hygiene defects fixed in-pass, 1 invariant-3 completion,
1 real CVE fixed, 1 hardening note registered. Zero CRITICAL/SERVING-PATH exploitable found.

## Triage ledger

| Class | n | Verdict | Evidence |
|---|---|---|---|
| path-traversal (HIGH) | 40 | **MITIGATED — dev tooling** | All in `generate_scenario.py`, `inspect_page.py`, `scripts/*`, `frontend/design-lab/*`; zero imports from `spine_api/`/`src/` serving path (verified by grep). Operator-run local scripts, never network-reachable. |
| insecure-randomness (LOW) | 23 | **MITIGATED — dev tooling** | Same files as above; no security-token use in serving path. |
| ssrf (HIGH) | 10 | **MITIGATED — dev tooling** | Screenshot/inspection scripts (`capture_nav_screenshots.py`, design-lab); not serving code. |
| business-logic-risk | 45 | **MITIGATED — auth verified** | 29 verified in handler windows (`get_current_agency/membership/user`, `verify_capability_token`, `require_platform_role("super_admin")`); the remaining 26 individually: password-reset (public-by-design, reset token = credential, rate-limited + audited), `/test-token` (env-gated 404 in prod), public_asks (`_verify` HMAC gate), public_proposals (FND-0219 opaque 256-bit tokens, hash-addressed), public_collection (`validate_token` + RLS + 20/min), trust_scorecard (signed links, traveler-safe projection), group_booking (invite-token capability, 404 on invalid), corporate-policy approve (PA-26 dual control, principal identity, owner/admin role), DSR erasure + payment-mandate CRUD + drafts + claims + timeline + analytics drill-down (all agency-DI + tenant-scoped). |
| other-security (SQL) | 3 | **FALSE POSITIVE** | `auth.py:303/355` → `refresh_access_token`/`confirm_password_reset`: input must decode + type-check as a signed JWT before any DB work; sinks are parameterized ORM (`select(User).where(User.id == user_id)`). `collection_service.py:29` "env → SQL" is `int(os.getenv(...TTL_HOURS))` — an integer config, not a sink. |
| other-security (env path) | 6 | **MITIGATED — operator config** | Sources are environment variables (`EXPOSE_RESET_TOKEN`, scenario seeds) — operator-controlled config, not request input. Same class as the FND-0374 note's weak-class determination. |
| hardcoded-credential | 1 | **MITIGATED — test fixture** | `tools/sim3_runner.py:44 TEST_PASSWORD="testpass123"` — the documented local test user's credential (`newuser@test.com`), local-only runner. |

## Real actionables (fixed this wave)

1. **DEBUG print block removed** — `spine_api/server.py` collection-link handler logged
   `trip_id`, `agency.id`, and the RLS GUC context to stdout via a leftover `print("DEBUG …")`
   block (incl. a duplicate `SELECT … FROM trips` probe). Info-leak hygiene; removed.
2. **`violations_detail` invariant-3 completion** — `corporate_policy.py` declared the
   machine-readable provenance field (FND-0338 comment: "input provenance travels WITH each
   finding") and computed it, but never wired it into the response — the interrupted-tranche
   class. Completed (`violations_detail=violations_detail`), model widened to `Dict[str, Any]`
   (the tranche's own `Dict[str, str]` rejected its boolean `enforceable`). Pinned by
   `tests/test_nl_corporate_policy.py::test_audit_route_populates_violations_detail`.
3. **Real dependency CVE** — live `pip-audit` (FND-0292 playbook) vs the scan's 42 offline
   matches: **1 real** (`opentelemetry-api 1.41.1`, CVE-2026-114603; floor bumped to 1.45.1 in
   pyproject incl. exporter), 41 stale-offline-DB. Re-audit: **No known vulnerabilities found.**

## Hardening notes registered (not fixed this wave)

- **`group_booking.py` raw-token storage**: invite records keep `raw_token` beside `token_hash`
  and match on either (`inv.get("token_hash") == h or inv.get("raw_token") == token`) — weaker
  than the FND-0219 hash-only discipline; a trip-JSON leak would expose usable capabilities.
  Fix needs a supersession pass over invite creation + both persistence match sites → opened as
  FND-0382 (P3) rather than ripped out mid-wave.

## Cross-references

- FND-0375 (IVR call_sid): verified green — validators wired at `ivr_gateway.py:165/226/261`,
  honesty tests 6/6. Fix+tests are the concurrent session's in-flight work (contested-tree
  discipline: left untouched).
- FND-0376 (destination precedence): DECIDED+SHIPPED by the concurrent session —
  `Docs/adr/DECISION_REC_FND0376_DESTINATION_TOMBSTONES_2026-10-25.md`, tombstone filter in
  `persistence.py::_preserve_authoritative_facts`. Finding closure on their side.
- FND-0378 (supplier fallback): fixed same wave — honest `None` at both sites; 28/28 tests.
- FND-0379 (gate vocabulary drift): fixed same wave — cross-stack parity pin
  (`tests/test_planning_gate_parity.py`) caught `trip_purpose` missing from the FE gate on its
  first run; FE gate now demands Trip purpose; FE suite 15/15; tsc clean. Follow-up (noted):
  derive the FE gate from a served contract endpoint to kill the mirror entirely.

**Verification:** backend suites touched this wave all green (corporate policy 18/18,
confirmations 28/28, parity 2/2, IVR 6/6); FE planning-status 15/15; tsc clean; pip-audit clean.
