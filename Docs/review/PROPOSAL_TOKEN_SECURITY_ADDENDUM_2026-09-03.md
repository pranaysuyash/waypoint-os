# Proposal-token security addendum — 2026-09-03

**Scope:** `spine_api/routers/public_proposals.py` and
`tests/test_public_proposals.py` only. This addendum records the focused
hardening performed against S-01/S-02/S-03/S-11 and PT-01..PT-06. It does not
claim that deployment-wide security or real proposal persistence is complete.

## Security contract

A public proposal capability is accepted only when all of these conditions
hold:

1. The service has a non-empty, non-placeholder signing secret of at least 32
   characters. No committed or import-time fallback secret is permitted.
2. The token has the canonical `prop_{trip}_{agency}_{expiry}_{signature}`
   shape. The agency field uses the repository's delimiter-safe `~XX` codec,
   and the verifier rejects alternate raw encodings.
3. The HMAC-SHA256 digest is complete (64 hexadecimal characters), and the
   signature covers the trip, decoded agency, and expiry together.
4. The expiry is strictly in the future (`now >= expiry` is expired).
5. The revocation store is available and does not contain the token. A missing
   store is treated as empty; malformed or unreadable state fails closed.
6. Revocation writes are atomically replaced and serialized with an OS lock on
   a shared single-host filesystem. Read/merge/replace prevents concurrent
   workers from losing separate revocations.

## Findings resolved in this slice

| Finding | Evidence in implementation | Verification |
|---|---|---|
| S-01/PT-01 | `_require_signing_key()` rejects missing, known-default, placeholder, and short keys; `_SECRET_KEY` is initialized from the environment only | missing-import subprocess and weak/placeholder parameterized tests |
| S-02/PT-02 | Length-based legacy acceptance is absent; only the three explicitly named demo fixtures are allowlisted | four forged-junk rejection cases plus exact allowlist tests |
| S-03/PT-03 | No agency guess-loop; the token's own encoded agency is decoded and used to rebuild the signed payload | five non-default agency round trips and HTTP round trip |
| PT-04 | Agency is part of the HMAC payload and must match the canonical wire representation | underscore, Unicode, percent, tilde, and non-canonical encoding tests |
| S-11/PT-05 | Revocations are persisted as JSON using atomic replacement, read/merge/write locking, and live reload before every verification | restart simulation, cross-worker merge, post-import reload, and corrupt-store fail-closed tests |
| S-11/PT-06 | HMAC-SHA256 is not truncated; digest length is checked before constant-time comparison | full 64-character digest test |

## Evidence

Executed from the repository root on 2026-09-03:

```text
PROPOSAL_SIGNING_KEY=test-proposal-signing-key-0123456789 \
DATABASE_URL=postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os \
.venv/bin/python -m pytest -q tests/test_public_proposals.py
40 passed in 1.57s

.venv/bin/ruff check spine_api/routers/public_proposals.py tests/test_public_proposals.py
All checks passed!

git diff --check -- spine_api/routers/public_proposals.py tests/test_public_proposals.py
pass
```

The two P1 price-lock failures observed when `tests/test_p1_findings_hardening.py`
was included with a SQLite URL (`no such function: set_config`) are unrelated
to this slice; the proposal suite itself passed against the configured
PostgreSQL URL.

## Remaining boundary and follow-up

The JSON backend is restart-safe and worker-safe when workers share one host
filesystem whose locking semantics are preserved. It is **not** a substitute
for a database-backed revocation table in a multi-replica deployment. The
launch gate LR-B07 remains open until the deployment either promotes
revocations to PostgreSQL or ratifies and provisions a durable shared volume.

The explicit demo-token allowlist remains a simulation compatibility seam. It
must be removed or isolated behind a development/demo environment gate before
public production exposure. The in-memory proposal registry still fabricates
proposal data and does not prove that a signed agency matches a persisted trip;
real proposal issuance and tenant/resource binding are separate follow-up work.
