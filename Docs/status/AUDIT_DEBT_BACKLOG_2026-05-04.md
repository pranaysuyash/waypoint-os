# Audit Debts — Deferred / Backlog

Generated 2026-05-04 from random document audit of `Docs/ARCHITECTURE_DECISION_SPINE_API_2026-04-15.md`.

## P2 — Worth Doing, No Pressure

| Item | Issue | What | Why Deferred |
|------|-------|------|-------------|
| ADR open questions | ISSUE-007 | Decide containerization strategy, load metrics for worker scaling, audit graceful shutdown | Not near prod. These become urgent when deploying. |
| Overview page test failure | Pre-existing | `page.test.tsx:210` — `getByText('No trips in planning yet')` not found | Unrelated to audited area. Likely a mocking gap in the test setup. |

## P3 — Cleanup When Convenient

| Item | Issue | What | Why Deferred |
|------|-------|------|-------------|
| `_agent_work_coordinator` env var | ISSUE-001 deferred | Still reads TRIPSTORE_BACKEND at import time | Singleton pattern makes it a larger refactor. Backend type never changes mid-process. |
| `field_validator` unused import | T09 | Imported at `server.py:64`, never used | Trivial cleanup, zero impact. |

## Not Worth Doing

| Item | Reason |
|------|--------|
| ISSUE-005 — Checkpoint consent filtering | Reframed during discussion: checkpoint saves AI outputs, not raw PII. Structured data is always stored for the agency's workflow. |
| Renaming `retention_consent` field | Too widely referenced across backend, frontend, generated types, and tests. Would touch 20+ files for cosmetic gain. |

## Audit Scope

**Source document:** `Docs/ARCHITECTURE_DECISION_SPINE_API_2026-04-15.md`
**Selection method:** Pseudo-random (SHA-256 hash → 143 feature-related documents → random pick)
**Scope:** Full deep audit — explicit tasks, implicit tasks, claims, stale docs, env var patterns, test gaps, privacy boundaries, and write-path coverage.

## Key Discussions That Shaped the Work

1. **retention_consent reframing** — Initially proposed a consent checkbox for the agency UI. Pranay pushed back: the agency is the data controller, consent belongs between traveler and agency, not agency and us. We reframed `retention_consent` from a legal consent gate to an "audit trail toggle" — the agency's consent to us is via ToS at signup, same as any B2B SaaS. This simplified the fix to just sending `retention_consent: true` with a code comment.

2. **Admin panel / analytics concern** — Pranay noted that even with consent reframed, we (the product builder) might want aggregated non-PII data for product analytics. We documented the tiered data model (raw text vs structured data vs file artifacts) as a future design consideration.

3. **Supersession workflow** — Applied the AGENTS.md protocol to remove `spine-client.ts` and `api-client.ts:runSpine()`. Confirmed zero call sites, verified replacements are strict supersets, and passed post-removal builds.

4. **Env var call-time pattern** — Moved from import-time `os.environ.get()` to call-time function wrappers, with the key architectural change being `_auth_or_skip` — a FastAPI dependency that checks `SPINE_API_DISABLE_AUTH` per-request instead of freezing the decision at module import time.

## Cleared This Session

| Item | What Was Done |
|------|---------------|
| ISSUE-003 — Frontend contract drift (retention_consent) | Agency IntakePanel + workbench send `retention_consent: true`. Discussion doc reframes consent as ToS-level, not per-submission. |
| Dead file cleanup | `spine-client.ts` removed (133 lines, zero imports). |
| Dead function cleanup | `api-client.ts:runSpine()` removed (36 lines, zero imports). |
| ISSUE-001 — Env var import-time caching | `_auth_or_skip` call-time dependency. `_is_cookie_secure()` call-time. `_ENVIRONMENT` dead code removed. `server.py` router deps always registered. |
| ISSUE-002 — Pipeline unit tests | 13 tests covering every code path in `_execute_spine_pipeline`. |
| ISSUE-004 — Stale ADR response contract | Added note at top of ADR pointing to `contract.py` as canonical source. |
