# Runtime Contract Version Matrix

Date: 2026-05-12 (Asia/Kolkata)

This file exists to prevent spec/code split-brain after parallel-agent updates.

## Current Source Of Truth

| Layer | Canonical artifact | Current version | Notes |
| --- | --- | --- | --- |
| Packet runtime model | `/Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py` | `CanonicalPacket.schema_version = "0.3"` | Runtime source of truth for packet fields and event semantics. |
| Packet JSON schema | `/Users/pranay/Projects/travel_agency_agent/specs/canonical_packet.schema.json` | `0.3` | Mirrors `CanonicalPacket.to_dict()`, not the raw dataclass object. |
| Source envelope runtime model | `/Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py` | runtime contract | `SourceEnvelope` has no runtime `schema_version`; schema mirrors the dataclass fields. |
| Source envelope JSON schema | `/Users/pranay/Projects/travel_agency_agent/specs/source_envelope.schema.json` | runtime contract | Supersedes older v0.1 envelope shape. |
| Decision states | `/Users/pranay/Projects/travel_agency_agent/src/intake/constants.py` | frozen enum set | `ASK_FOLLOWUP`, `PROCEED_INTERNAL_DRAFT`, `PROCEED_TRAVELER_SAFE`, `BRANCH_OPTIONS`, `STOP_NEEDS_REVIEW`. |
| Decision policy | `/Users/pranay/Projects/travel_agency_agent/specs/decision_policy.md` | v0.2 runtime policy | Still valid for NB02 behavior; policy version is separate from packet schema version. |
| NB01 notebook | `/Users/pranay/Projects/travel_agency_agent/notebooks/01_intake_and_normalization.ipynb` | v0.2 notebook label | Demo wrapper around runtime `src/intake` code. Runtime packet output is v0.3. |
| NB02 notebook | `/Users/pranay/Projects/travel_agency_agent/notebooks/02_gap_and_decision.ipynb` | v0.2 notebook label | Demo wrapper around runtime `src/intake/decision.py`. |

## Compatibility Notes

- `notebooks/02_gap_and_decision_contract.md` is historical and now starts with a deprecation notice.
- Legacy field names such as `destination_city`, `travel_dates`, `budget_range`, and `traveler_count` may appear in older docs and compatibility tests. Current runtime uses canonical field names such as `destination_candidates`, `date_window`, `budget_min`, and `party_size`.
- Do not create a parallel packet model to resolve version drift. Update the canonical model, schema, and tests together.

## Rule For Future Updates

When changing packet shape or decision-state behavior:

1. Update the runtime source first.
2. Update the corresponding schema in `/Users/pranay/Projects/travel_agency_agent/specs/`.
3. Update this matrix.
4. Run targeted NB01/NB02/NB03 contract tests.
5. Add or update a dated review/status doc under `/Users/pranay/Projects/travel_agency_agent/Docs/`.
