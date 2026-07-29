"""
src/analytics/kdd — Knowledge-Driven Discovery v0.

Override-mining pipeline prototype. The smallest end-to-end loop that reads
enriched override events from the OverrideStore + AuditLog, extracts structured
features, clusters similar overrides, and surfaces a digest for human review.

See Docs/exploration/KDD_V0_OVERRIDE_MINING_SCOPE_2026-05-18.md for full scope.

Sub-modules:
    override_features — pure-function feature extraction from override + decision_delta
    clustering — group similar overrides by flag/decision_type/trip_context
    jobs — orchestration: extract → cluster → persist
    models — Pydantic models for the pipeline
"""
