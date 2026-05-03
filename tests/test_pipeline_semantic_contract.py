"""
Tests for the semantic pipeline stage/gate contract introduced in Phase 1 of
the pipeline naming refactor.

Covers:
- Backend resolve_stage() / resolve_gate() helpers
- Backend PipelineStage + GateIdentifier enums
- Frontend validationLabelFor() priority order (mirrored in Python for CI)
- Backward compatibility with legacy NB01-NB06 codes

Why a dedicated test file: This contract crosses the frontend/backend boundary
and must survive refactoring of either side. A standalone test file makes
regressions visible immediately.
"""

import pytest

# ---------------------------------------------------------------------------
# Backend imports
# ---------------------------------------------------------------------------
from src.intake.constants import (
    PipelineStage,
    GateIdentifier,
    resolve_stage,
    resolve_gate,
)


# ---------------------------------------------------------------------------
# Backend: resolve_stage
# ---------------------------------------------------------------------------
class TestResolveStage:
    """resolve_stage() must accept both legacy NB codes and semantic keys."""

    def test_legacy_nb01(self):
        assert resolve_stage("NB01") == PipelineStage.INTAKE_EXTRACTION

    def test_legacy_nb02(self):
        assert resolve_stage("NB02") == PipelineStage.DECISION_JUDGMENT

    def test_legacy_nb03(self):
        assert resolve_stage("NB03") == PipelineStage.SESSION_STRATEGY

    def test_legacy_nb04(self):
        assert resolve_stage("NB04") == PipelineStage.TRAVELER_PROPOSAL

    def test_legacy_nb05(self):
        assert resolve_stage("NB05") == PipelineStage.GOLDEN_PATH_EVALUATION

    def test_legacy_nb06(self):
        assert resolve_stage("NB06") == PipelineStage.SHADOW_REPLAY

    def test_semantic_intake_extraction(self):
        assert resolve_stage("intake_extraction") == PipelineStage.INTAKE_EXTRACTION

    def test_semantic_decision_judgment(self):
        assert resolve_stage("decision_judgment") == PipelineStage.DECISION_JUDGMENT

    def test_unknown_returns_none(self):
        assert resolve_stage("unknown_stage") is None

    def test_none_returns_none(self):
        assert resolve_stage(None) is None


# ---------------------------------------------------------------------------
# Backend: resolve_gate
# ---------------------------------------------------------------------------
class TestResolveGate:
    """resolve_gate() must accept both legacy NB codes and semantic keys."""

    def test_legacy_nb01(self):
        assert resolve_gate("NB01") == GateIdentifier.INTAKE_COMPLETION

    def test_legacy_nb02(self):
        assert resolve_gate("NB02") == GateIdentifier.DECISION_READINESS

    def test_semantic_intake_completion(self):
        assert resolve_gate("intake_completion") == GateIdentifier.INTAKE_COMPLETION

    def test_semantic_decision_readiness(self):
        assert resolve_gate("decision_readiness") == GateIdentifier.DECISION_READINESS

    def test_unknown_returns_none(self):
        assert resolve_gate("unknown_gate") is None

    def test_none_returns_none(self):
        assert resolve_gate(None) is None


# ---------------------------------------------------------------------------
# Backend: Gate class attributes
# ---------------------------------------------------------------------------
class TestGateClassAttributes:
    """Gate classes must expose semantic + legacy identifiers as class attrs."""

    def test_nb01_completion_gate(self):
        from src.intake.gates import NB01CompletionGate

        assert NB01CompletionGate.stage == PipelineStage.INTAKE_EXTRACTION
        assert NB01CompletionGate.gate_key == GateIdentifier.INTAKE_COMPLETION
        assert NB01CompletionGate.legacy_code == "NB01"

    def test_nb02_judgment_gate(self):
        from src.intake.gates import NB02JudgmentGate

        assert NB02JudgmentGate.stage == PipelineStage.DECISION_JUDGMENT
        assert NB02JudgmentGate.gate_key == GateIdentifier.DECISION_READINESS
        assert NB02JudgmentGate.legacy_code == "NB02"


# ---------------------------------------------------------------------------
# Frontend: validationLabelFor (imported via Node/TypeScript — tested here
# in Python by keeping the mapping parity contract)
# ---------------------------------------------------------------------------
class TestValidationLabelParity:
    """
    The Python legacy map and the TS LABELS/LEGACY_LABELS maps must stay in
    sync. If they diverge, old drafts will show different labels in the UI
    depending on which side resolves the key.
    """

    def _frontend_label(self, key: str) -> str:
        """Mirror of frontend/src/types/spine.ts validationLabelFor().

        Kept here so CI can catch drift between backend enum values and
        frontend display labels.
        """
        labels = {
            "intake_completion": "Trip Details",
            "decision_readiness": "Ready to Quote",
            "strategy_safety": "Safety Check",
            "proposal_quality": "Proposal Quality",
            "demo_regression": "Demo QA",
            "shadow_quality": "Production QA",
            "intake_extraction": "Trip Details",
            "decision_judgment": "Ready to Quote",
            "session_strategy": "Strategy",
            "traveler_proposal": "Build Proposal",
            "golden_path_evaluation": "Final Review",
            "shadow_replay": "Production QA",
        }
        legacy = {
            "NB01": "Trip Details",
            "NB02": "Ready to Quote",
            "NB03": "Strategy",
            "NB04": "Build Proposal",
            "NB05": "Final Review",
            "NB06": "Production QA",
        }
        return labels.get(key) or legacy.get(key) or key

    def test_all_enum_values_have_frontend_label(self):
        """Every PipelineStage and GateIdentifier must have a frontend label."""
        for stage in PipelineStage:
            label = self._frontend_label(stage.value)
            assert label != stage.value, f"Missing frontend label for stage {stage.value}"

        for gate in GateIdentifier:
            label = self._frontend_label(gate.value)
            assert label != gate.value, f"Missing frontend label for gate {gate.value}"

    def test_legacy_codes_have_frontend_label(self):
        """Legacy NB01-NB06 must have frontend labels (for old draft compat)."""
        for code in ("NB01", "NB02", "NB03", "NB04", "NB05", "NB06"):
            label = self._frontend_label(code)
            assert label != code, f"Missing frontend label for legacy code {code}"

    def test_priority_semantic_over_legacy(self):
        """If a key exists in both maps, semantic label wins.

        This is a structural test: the TS implementation uses
        `LABELS[key] ?? LEGACY_LABELS[key]` which gives LABELS priority.
        """
        # These keys should never collide in practice, but the test documents
        # the contract.
        assert self._frontend_label("intake_completion") == "Trip Details"
        assert self._frontend_label("NB01") == "Trip Details"
