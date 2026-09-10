# ADR: PII Guard Posture — Layered Fail-Closed/Fail-Open Matrix (R-15 2.6)

**Date:** 2026-09-09 · **Status:** Accepted · **Supersedes:** the informal "Layer 2 fail-closed vs Layer 1 fail-open disagreement" flagged in `FINDINGS_REGISTER_2026-08-29.md` (R-15)

## Context

`src/security/privacy_guard.py` guards trip persistence against real-user PII landing in storage. The 2026-08-29 audit (R-15) flagged an apparent contradiction:

- The **trip-data gate** (Layer 1, deterministic regex heuristics) **fails open** outside dogfood — PII-shaped data is persisted, unblocked.
- The **SpaCy NER layer** (Layer 2) is **fail-closed** in production — missing model ⇒ treated as detection.

Two layers of the same guard holding opposite failure postures looked like a defect. The register required "one PII posture, explicitly chosen."

## Decision

The postures are **not** in disagreement — they are different functions of one guard, and each is now explicit:

| Mode | Store | Layer 1 (regex) | Layer 2 (SpaCy NER) | Rationale |
|---|---|---|---|---|
| dogfood | plaintext file | **fail-closed** (block) | active, blocks | No encryption boundary exists; the guard IS the boundary. Developer data is synthetic; real-user PII must never land. |
| beta / production | SQL/Postgres (FORCE RLS + encryption) | **fail-open + audit event** | latency-bounded, non-blocking | The database (FORCE RLS, `trips` verified 2026-08-31) and field encryption are the confidentiality boundary. The guard is *observability* — a tripwire over the boundary — and must not become a false-positive outage on the write path. |
| production | plaintext file store (misconfiguration) | **fail-closed** (block) + audit event | active | The boundary is absent AND the posture claims production: exactly what the guard exists to prevent. |

Additional decisions:

1. **The fail-open admission is audit-chained, not log-only.** When Layer 1 detects PII-shaped data that is *not* blocked (beta/prod+SQL), the guard emits `privacy_guard_admitted_pii_shape` into the AuditStore hash chain (`blocked: false`, mode, findings). When the misconfiguration block fires, it emits `privacy_guard_blocked`. Silent fail-open is no longer possible to miss (R-15 2.5). Emission is best-effort and lazy-imported — the observer must never become the outage.
2. **Clean passes emit nothing.** Per-save audit events for every write would be noise; only the interesting transitions (admission, block) enter the chain.
3. **Layer 2 remains dogfood-only and fail-closed there.** NER latency on the hot write path is not acceptable in production; Layer 1's deterministic heuristics bound latency (2000-char cap) and run everywhere.

## Consequences

- Operators MUST treat `privacy_guard_admitted_pii_shape` events as signals to investigate the data source, not as incidents in themselves — admission is the designed behavior in safe configs.
- The production+plaintext combination is now doubly defended (boot-time TRIPSTORE_BACKEND assertions + write-time block + audit chain event).
- Staleness: this ADR assumes FORCE RLS on `trips` (verified 2026-08-31, `pg_class`). If a deployment downgrades to a non-FORCE posture, the "SQL is the boundary" premise fails and Layer 1 must return to fail-closed.

## Verification

- `tests/test_privacy_guard.py` — 58 passing, including the audit-emission tests: admission emits `privacy_guard_admitted_pii_shape` (`blocked: false`), clean passes emit nothing, production+plaintext block raises.
- Emission goes to the AuditStore hash chain (`AuditStore.log_event`), preserving the tamper-evident property.
