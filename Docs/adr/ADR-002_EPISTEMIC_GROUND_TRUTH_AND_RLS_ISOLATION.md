# ADR-002: Epistemic Ground Truth Taxonomy & Multi-Tenant RLS Isolation

*Status: ACCEPTED*  
*Date: 2026-09-03*  
*Decision Makers: Core Platform Architecture*  
*Reference: `PER-SEC-2026-09-03` / Tasks S-01…S-12*

---

## Context & Problem Statement
Autonomous travel operations require strict boundaries between verified facts, extracted inferences, and synthetic assumptions. Unpartitioned caches or unverified tokens risk cross-tenant data leakage or forged authorization.

## Decision
1. **Epistemic Classification**: Every data slot is tagged with explicit epistemic status (`FACT`, `INFERRED`, `ASSUMED`, `UNKNOWN`).
2. **Multi-Tenant Isolation**: PostgreSQL tables enforce `FORCE ROW LEVEL SECURITY` keyed by `agency_id`.
3. **Capability Token Integrity**: All proposal tokens embed agency scope and are HMAC-signed with mandatory environment secret `PROPOSAL_SIGNING_KEY`.

## Consequences & Evidence
- **Zero Cross-Tenant Leakage**: Validated across `test_multi_tenant_isolation_harness.py`.
- **DoS & Token Hardening**: Validated by `test_security_hardening_s07_s11.py` and `test_public_proposals.py`.
