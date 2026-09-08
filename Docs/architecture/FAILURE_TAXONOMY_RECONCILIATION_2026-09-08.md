# E-B Reconciliation — Failure taxonomy: one enum ratified (2026-09-08)

**Exploration package E-B close-out.** Contested since 09-07: the E-B design doc proposed seven classes (`TRANSIENT / PROVIDER / INPUT / STATE / POLICY / VERIFICATION / AUTHORITY`); the shipped live enum (`spine_api/failure_taxonomy.py`, `FailureClass`) is **eight classes, differently named**: `model / tool / environment / state / verification / authority / policy_block / unclassified`.

## Decision (reconciliation)

**The live 8-class enum is canonical.** The design doc's 7-class vocabulary is superseded. Rationale:

1. The live enum is already wired: `failure_class` + `stage_at_failure` persist on ledger meta (since `6c7c824`'s tree), the classification choke point exists, and REQUEUEABLE_CLASSES drives retry policy — code, tests, and docs all reference these names.
2. Rename-mapping to the design's nouns is churn with zero behavioral gain; the design's *intent* is fully expressible in the live set.
3. Doctrine §5: canonical paths win; the design doc itself says "one enum in code+doc" — this document is that doc.

## Crosswalk (design noun → live class)

| E-B design noun | Live `FailureClass` | Note |
|---|---|---|
| TRANSIENT | `environment` | timeouts/infra; retryable (in REQUEUEABLE_CLASSES) |
| PROVIDER | `tool` | HTTP/provider/network tool errors |
| INPUT | `policy_block` | validation/leakage policy refusals — system working, route to operator, never retry-budgeted |
| STATE | `state` | persistence/TripStore divergence |
| POLICY | `authority` | authorization/permission (distinct from input validation) |
| VERIFICATION | `verification` | assertion-style failures |
| AUTHORITY | `authority` | merged with POLICY row above — live enum splits input-validation from authority, which the design conflated |
| — | `model` | live enum is *richer*: LLM/model errors are their own class (design folded them into TRANSIENT/PROVIDER; the split matters for routing: model errors → fallback model, provider HTTP → retry/backoff) |
| — | `unclassified` | explicit escape hatch; monitored, never a retry target |

## Corrections to the E-B design doc

`Docs/architecture/FAILURE_TAXONOMY_DESIGN_2026-09-07.md` remains valid for: per-class recovery ladders, POLICY-failures-are-the-system-working routing, lease-aware stale-run sweep (PA-17 race), and operator escalation queues. Where it names the seven-class vocabulary, substitute per this crosswalk. A one-line pointer is added to that doc rather than rewriting history.

## Action items (small)

1. ~~Rename~~ none — no code change. ✓
2. Update `FAILURE_TAXONOMY_DESIGN_2026-09-07.md` header: "superseded vocabulary; see FAILURE_TAXONOMY_RECONCILIATION_2026-09-08" (done with this doc).
3. `unclassified` rate is a tracked metric — if it exceeds a small percentage, the mapping table (not the enum) grows.

## Status

Contested row closed. One enum: live 8-class `FailureClass`.
