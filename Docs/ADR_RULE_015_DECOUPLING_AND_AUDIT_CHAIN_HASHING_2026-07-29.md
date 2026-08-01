# ADR: Rule 0.15 Decoupling Linter & Cryptographic Audit Chain Hashing

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Third-Layer Decoupling & Tamper-Evident Audit Trails

---

## Context

Allowing LLM prompt outputs to directly mutate decision state gates creates shadow pipeline hazards and bypasses deterministic safety controls (Rule 0.15 in `motto_v4.md`). Furthermore, standard JSON audit logs risk modification if historical event lines are tampered with.

---

## Decision

Implemented Rule 0.15 Linter & Cryptographic Audit Hashing:

1. **Rule 0.15 Decoupling Linter (`scripts/validate_decoupling.py`)**:
   - Automated code scanner verifying that LLM prompts in `src/llm/` and extractors never assign decision states (`PROCEED`, `ESCALATE`) directly without deterministic validation.
2. **Cryptographic SHA-256 Chain Hashing (`spine_api/persistence.py`)**:
   - Upgraded `AuditStore.log_event()` to calculate SHA-256 block hashes (`previous_hash`, `current_hash`) linking events in an append-only, tamper-evident hash chain.

---

## Consequences

- 100% enforcement of Third-Layer Decoupling invariant across all codebase files.
- Immutable, tamper-evident audit provenance chain for regulatory compliance.
