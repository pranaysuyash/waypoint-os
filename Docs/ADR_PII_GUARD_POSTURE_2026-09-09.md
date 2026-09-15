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

---

## Addendum 2026-09-15 — Egress direction: redact-before-enrich (ADR-008 §7 promotion gate condition)

**Scope:** this ADR governed the *persistence* direction (data at rest). The
hybrid decision engine (ADR-008 §4.1/§7 item 2) introduces the *egress*
direction: traveler intake text flowing to an external LLM provider for risk
enrichment. This addendum fixes the posture; implementation is the next
increment and is a precondition of the D6 `promotion_gate` condition
`pii_egress_authorized`.

**Principle (owner-confirmed 2026-09-15):** the egress standard is the *same*
standard as the booking-counterparty flow — purpose-scoped, minimized,
contractually bounded — not "PII never leaves." Traveler PII legitimately
flows to GDS/suppliers because that is the consented fulfillment purpose.
Inference enrichment is a *different* purpose and needs its own scoping, not a
blanket prohibition.

**Design — pseudonymize-reattach:**

1. **Minimize before the call.** Extend the Layer-1 detection vocabulary to an
   *egress action*: deterministic redaction of direct identifiers (names,
   phones, emails, passport/MRZ, addresses) into placeholder tokens
   (`[[PERSON_1]]`, `[[PHONE_1]]`), keeping an in-process reattachment map
   keyed by `decision_id` and discarded after the decision. The enrichment
   task needs age bands, health context, and trip shape — not identities.
2. **One authorized seam.** The hybrid engine's enrichment call site is the
   only sanctioned egress point. A gate at that seam fails closed: if
   redaction has not run for the payload, no provider call is made. An audit
   event (`pii_egress_redacted`, redaction counts only) lands in the
   AuditStore chain at the seam.
3. **Contractual layer.** Provider terms must be zero-retention /
   no-training (enterprise or equivalent tier). Venue selection is now a
   first-order quality variable (KDD 2026-09-15: llama-3.1-8b graded F1 0.800
   via one venue, 0.340 via another — same weights), so provider choice is a
   joint quality-terms decision, recorded per envelope.
4. **Notice.** The traveler privacy notice gains the enrichment purpose
   (DPDP-consistent) before the posture activates on real traveler data.

**Status: DESIGN, not wired.** The redaction filter, the fail-closed seam
gate, and the audit event are the implementation increment; the promotion
gate stays closed until they land and the terms are ratified.
