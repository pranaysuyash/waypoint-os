# EXPLORE #5 — Tamper-Evident Audit Chain: Gap Audit & Closure Map

**Date:** 2026-10-26
**Status:** AUDIT COMPLETE — the finding (FND-0043) is materially stale. Most of the proposed design already exists. This doc records what exists (verified), what's genuinely missing, and the closure path.
**Origin:** Exploration topic 48 next-step #5 (ZizkaDB pattern); FND-0043 (audit-chain gaps); EU AI Act Art. 12 posture (FND-0418 lineage).

---

## TL;DR

FND-0043 claimed "file hash-chain unsigned/unanchored; run-ledger outside chain; no fork/gap detector." The 2026-10-26 audit found **most of that already built**: the SQL audit path carries a RULE_015 hash chain with transaction-scoped advisory-lock serialization (fork-proof, FND-0367-aware), `AuditStore.verify_chain()` verifies both chains (SQL + legacy file) with formula-aware handling, `audit_chain_hash.py` centralizes the hash math, and `execution_event_service.py` carries its own prev-hash chain. **16 chain tests pass green.** The genuine gaps are three: (1) the legacy *file* chain is unanchored (no external anchor / periodic head snapshot), (2) **no causal `why()` query** — the ZizkaDB capability that turns the chain from evidence into a debugging tool, (3) **no trim-safety proof** — the file rotation compaction could theoretically break predecessor links (untested). Closure is a small hardening pass, not a build.

## What exists (verified 2026-10-26)

| Capability | Location | Evidence |
|---|---|---|
| Hash-chained SQL audit events (RULE_015) | `spine_api/persistence.py` (`_persist_sql_event`) | chain formula mirrors `core.audit.AuditContext.log` |
| Fork-proof serialization | transaction-scoped advisory lock (`AUDIT_CHAIN_ADVISORY_KEY = "waypoint_audit_chain_v1"`) | comment block at `persistence.py:257-264` — explicitly FND-0367-aware (database-level, not loop-bound) |
| Dual-chain verifier | `AuditStore.verify_chain()` (`persistence.py:2965`) — SQL + legacy file, formula-aware, never mutates | 16/16 tests green (`test_cryptographic_audit_ledger.py`, `test_audit_log_chain_verify.py`) |
| Centralized hash math | `spine_api/services/audit_chain_hash.py` (`verify_audit_entries`) | single formula authority |
| Second chain: execution events | `spine_api/services/execution_event_service.py` (prev_hash per event) | separate ledger with its own linkage |
| Crash-safe append-only file log | `AuditStore` v2 design (JSONL, atomic rename, rotation) | docstring `persistence.py:2634-2644` |
| Findings-store precedent | `Docs/review/FINDINGS_STORE.jsonl` — append-only CLI-managed lifecycle | operational proof of the pattern |

## Genuine gaps (the closure map)

1. **No external anchoring.** Neither chain's head hash is ever snapshotted anywhere outside the DB/disk. A determined attacker with DB write access could rewrite history AND the chain. Closure: periodic head-hash anchor (cron writes the current head to an append-only local file, or logs it to a second medium). Small: one writer + one verifier addition.
2. **No causal `why()` query.** The chain proves *what* happened in order; it does not answer *why* (which intake fact caused which gate decision which caused which message). ZizkaDB's contribution is `parent_id` linkage. Closure: add optional `caused_by` (parent event_id) to `log_event`, populated at call sites where causality is known (gate decisions, fare-drop signals, disposition transitions). The fare-drop card's audit event already carries `detection_marker` — the pattern exists at call sites.
3. **Trim-safety unproven.** `AuditStore` rotation/compaction rewrites the tail; no test proves the chain verifier still passes post-compaction. Closure: one test — compact, then `verify_chain()`, assert pass.
4. **FND-0043 staleness.** The finding predates the SQL-chain build. Closure: `reverify` with this doc as evidence, or close with pointer.

## Recommended sequence (small, hardening-class)

1. Trim-safety test (30 min, closes a real untested edge).
2. Head-hash anchoring (writer + verifier, ~half day).
3. `caused_by` parent linkage at high-value call sites (gate decisions first; incremental — the chain doesn't change, only payloads gain a field).
4. FND-0043 reverify/close.
5. Optional phase 2: chain-run `why()` reader over `caused_by` (the ZizkaDB capability), once enough call sites populate it.

**Explicitly NOT recommended:** adopting ZizkaDB itself — the existing chain + verifier + advisory-lock design is sound and tested; adding a second audit store would violate the one-canonical-store doctrine. Borrow the `why()` *idea*, not the dependency.

## Artifacts for the next pass

- Trim-safety test target: `AuditStore` compaction path + `verify_chain()`.
- Anchoring target: `_persist_sql_event` head read + a `head_hash()` accessor.
- `caused_by` first call sites: `fare_drop_disposition_updated`, `passenger_rights_claim_disposition_updated`, gate `authoritative_fact_applied` events.

## Sources

- Live code: `spine_api/persistence.py` (AuditStore, `_persist_sql_event`, `verify_chain`), `spine_api/services/audit_chain_hash.py`, `spine_api/services/execution_event_service.py`
- Tests: `tests/test_cryptographic_audit_ledger.py` (16/16), `tests/test_audit_log_chain_verify.py`
- Pattern source: ZizkaDB (topic 48 sweep, commit `90d3ec9d` record)
