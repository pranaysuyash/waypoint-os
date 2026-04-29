# Predictive Health & Medical Logistics Audit

- Date: 2026-04-29
- Reviewed doc: [Docs/product_features/PREDICTIVE_HEALTH_AND_MEDICAL_LOGISTICS.md](../product_features/PREDICTIVE_HEALTH_AND_MEDICAL_LOGISTICS.md)

## Scope

This review stays on the selected feature doc and the direct implementation surfaces it depends on.
It does not expand into unrelated future features.

## Findings

- The document is a forward-looking spec, not an implemented feature.
- The repo currently exposes no medical-logistics API surface in `spine_api/server.py`.
- The canonical API contract in `spine_api/contract.py` has no medical-summary, insurance, or medevac model.
- `src/security/privacy_guard.py` blocks medical/health indicators in dogfood mode.
- `src/intake/extractors.py` and `src/decision/rules/elderly_mobility.py` only cover a narrow mobility-risk overlap.

## Immediate next step

Define the privacy-safe medical-logistics contract before any implementation work:

1. Decide whether traveler medical history is persisted.
2. If yes, define the storage boundary and access roles.
3. Reuse or explicitly exclude the current mobility-risk primitives.
4. Keep the scope limited to this feature until the contract is settled.

## References

- `Docs/product_features/PREDICTIVE_HEALTH_AND_MEDICAL_LOGISTICS.md`
- `README.md`
- `spine_api/server.py`
- `spine_api/contract.py`
- `src/security/privacy_guard.py`
- `src/intake/extractors.py`
- `src/decision/rules/elderly_mobility.py`
