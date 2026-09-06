# Cross-Tenant Isolation & Zero-Trust Security Harness (`PER-SEC-2026-09-03`)

*Status: CANONICAL SECURITY HARDENING RECORD (Tasks S-01…S-11)*\
*Doctrine Reference: `agent-start/doctrines/SECURITY_PRIVACY_SAFETY_DOCTRINE.md`*

---

## 1. Security Architecture & Threat Model Overview

Waypoint OS enforces a **Zero-Trust Multi-Tenant Architecture** designed to withstand:

1. **Cross-Tenant ID Poisoning**: Attacker submitting a foreign `trip_id` or `draft_id` belonging to another agency.
2. **Capability Token Forgery**: Unauthorized manipulation of signed public proposal view tokens.
3. **Delimiter Escape Prompt Injection**: Malicious user notes breaking out of LLM extraction fences.
4. **Unauthenticated Public Checker Resource Exhaustion**: Large payload DoS attacks on public inquiry endpoints.

---

## 2. Invariant Controls & Implemented Protections

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. SIGNING KEY INVARIANT (S-01 / PT-01)                                     │
│    • Mandatory PROPOSAL_SIGNING_KEY enforcement on startup in prod/staging. │
│    • No committed default fallback secret permitted in repository.          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. CROSS-TENANT DRAFT PROMOTION GUARD (S-05 / RT-03)                        │
│    • Draft promotion strictly scoped: TripStore.get_trip_for_agency()       │
│    • Rejects foreign agency trips with 404 to avoid enumeration leaks.      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. PROMPT DELIMITER NONCE ENCAPSULATION (S-06 / RT-01)                      │
│    • Wraps untrusted user content in per-call nonce tags:                   │
│      <user_content nonce=a7f9b2...> ... </user_content nonce=a7f9b2...>     │
│    • Delimiter collisions are redrawn, preventing prompt escape injection.  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. ROW-LEVEL SECURITY (RLS) POSTURE (S-12)                                  │
│    • PostgreSQL table-level FORCE ROW LEVEL SECURITY enabled.               │
│    • Verified via test_multi_tenant_isolation_harness.py in CI.             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Verification & CI Harness

All security invariants are verified on every pull request and build via:

- `tests/test_multi_tenant_isolation_harness.py`
- `tests/test_public_proposals.py`
- `tests/test_llm_egress.py`
- `tests/test_auth_membership_regression.py`
