# Mimosa Full-Scan Record — post-push seal (2026-09-10)

**Trigger:** the git-push hook flagged that the pre-push scan had no complete conclusion (scanner ENOBUFS); per the hook's own directive this re-run was required before any safety claim.
**Scan:** job `scan-job-mtvtlbrl-e13c0ec0d0591376`, depth **deep**, completed 2026-09-10T17:48:34Z.
**Seal:** `sha256:552c250575730c1056bf87dc504412f066c0ef3088009b6e316521964444f24f`
**Scan dir:** `~/.mimosa/security-scans/project-1a789e004350b2e32cc42e24/scan-2026-09-10T17-48-34.547Z-bd1e62f67fbb`
**Evidence boundary:** static only, no runtime execution (scanner's own label). Dependency audit completed: 825 packages, 21 matched packages against 91 advisories (offline advisory DB).

## Counts

- **Total findings: 113** (59 high / 31 medium / 23 low).
- **Prior sealed scan** (2026-09-10T06:37Z, the remediation-wave baseline): 74 — the documented noise floor.
- **Delta: 45 new** (16 high / 29 medium), all in the deep-scan's business-logic hypothesis classes, all verdict `inconclusive/candidate`.
- **Overlap with commit `1ceaf91` (TS wave): ZERO findings** on `src/decision/constraint_engine.py`, `spine_api/services/field_merge.py`, `src/orchestration/proposal_compiler.py`, or their tests.

## New-finding triage (English translation of scanner classes)

1. **"Resource identifier from request without observed ownership/tenant binding" — 16 HIGH, all `spine_api/routers/drafts.py`.** **Verified FALSE POSITIVE by code inspection:** every flagged endpoint performs the tenant guard `if not draft or draft.agency_id != agency.id: → 404` (drafts.py:139, 153, 196, 213, 230, 248, 273 — covers all flagged ranges incl. the duplicate at 223-238). The binding exists as a post-fetch comparison; the static scanner only recognizes fetch-by-tenant call shapes. Same class as the documented name-based/false-positive pattern from prior waves.
2. **"Sensitive operation without observed role/permission check" — 29 MEDIUM across `auth.py`, `boundaries.py`, `corporate_policy.py`, `financial_ops.py`, `group_booking.py`, `product_b_analytics.py`, `public_collection.py`, etc.** These endpoints carry authentication dependencies (`get_current_agency`/`get_current_user`) but not always a *role* check — the known platform posture (role granularity rides ADR-008 autonomy rungs / DECIDE C1; corporate_policy no-JWT-auth is already a registered finding from the TPM wave). **Registered as a triage follow-up, not new code defects:** the correct disposition is per-router role-check audit once C1 is ratified, folded with the existing F-register rows rather than duplicated.

## Disposition

- The hook's requirement is satisfied: a complete, sealed, deep scan now exists post-push. **No claim beyond the evidence boundary: this is static analysis; it is not a runtime or penetration verdict.**
- 16 highs closed as verified false positives (evidence above). 29 mediums registered as the role-check audit follow-up (owner-gated on C1). 74 pre-existing findings remain the documented noise floor per the remediation-wave record.
- Zero remediation required from the TS wave.

**Committed state at scan time:** `1ceaf91` (pushed). Parallel scenario-series work was dirty-in-tree during the scan; if that wave commits code, the next deep scan should re-baseline against this seal.
