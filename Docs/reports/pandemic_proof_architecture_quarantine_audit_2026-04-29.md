# Pandemic-Proof Architecture & Quarantine Audit

- Date: 2026-04-29
- Reviewed doc: [Docs/industry_domain/regulatory_compliance/PANDEMIC_PROOF_ARCHITECTURE_AND_QUARANTINE.md](../industry_domain/regulatory_compliance/PANDEMIC_PROOF_ARCHITECTURE_AND_QUARANTINE.md)

## Scope

This review stays on the selected quarantine doc and the immediate code/docs it touches.

## Findings

- The document is frontier policy/spec text, not an implemented quarantine workflow.
- `spine_api/server.py` has no quarantine-specific endpoints or corridor orchestration.
- `spine_api/contract.py` has no health-token, bio-bubble, or quarantine-clearance contract.
- `src/security/privacy_guard.py` treats medical/health data as sensitive and blocks it in dogfood mode.
- The closest runtime overlaps are advisory only:
  - `src/intake/specialty_knowledge.py` includes `medical_tourism`
  - `src/intake/checker_agent.py` flags medical/repatriation/urgent cases for manual review

## Immediate next step

Decide whether this is:

1. a research-only future concept, or
2. a product workflow that needs a concrete API/data contract.

If it is meant to ship, define the storage boundary, consent model, and the exact public endpoints first.

## References

- `Docs/industry_domain/regulatory_compliance/PANDEMIC_PROOF_ARCHITECTURE_AND_QUARANTINE.md`
- `Docs/industry_domain/INDEX.md`
- `spine_api/server.py`
- `spine_api/contract.py`
- `src/security/privacy_guard.py`
- `src/intake/specialty_knowledge.py`
- `src/intake/checker_agent.py`
