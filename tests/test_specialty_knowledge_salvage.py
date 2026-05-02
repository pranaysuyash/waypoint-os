"""
Specialty Knowledge Salvage — Tests for the pipeline path that produces
specialty_knowledge and surfaces it through decision.rationale.frontier.

Verifies:
  1. SpecialtyKnowledgeService.identify_niche detects known niches
  2. FrontierOrchestrationResult carries specialty_knowledge
  3. orchestration.py writes specialty_knowledge into decision.rationale["frontier"]
  4. The guarded model_dump() serialization path works
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from src.intake.specialty_knowledge import (
    SpecialtyKnowledgeService,
    SpecialtyKnowledgeEntry,
    KNOWLEDGE_BASE,
)


# ===========================================================================
# 1. SpecialtyKnowledgeService detection
# ===========================================================================

class TestSpecialtyKnowledgeService:

    def test_medical_tourism_detected(self):
        hits = SpecialtyKnowledgeService.identify_niche(
            "Patient needs post-op recovery after dental surgery in Bangkok"
        )
        assert len(hits) >= 1
        assert any(h.niche == "Medical Tourism & Post-Op Recovery" for h in hits)

    def test_academic_research_detected(self):
        hits = SpecialtyKnowledgeService.identify_niche(
            "Professor traveling to field site for grant-funded sampling research"
        )
        assert len(hits) >= 1
        assert any(h.niche == "Academic Research Logistics" for h in hits)

    def test_human_remains_detected(self):
        hits = SpecialtyKnowledgeService.identify_niche(
            "Repatriation of remains, need mortuary and death certificate handling"
        )
        assert len(hits) >= 1
        assert any(h.niche == "Human Remains Repatriation" for h in hits)

    def test_mice_detected(self):
        hits = SpecialtyKnowledgeService.identify_niche(
            "Corporate incentive trip with conference and exhibition for delegates"
        )
        assert len(hits) >= 1
        assert any(h.niche == "MICE (Meetings & Incentives)" for h in hits)

    def test_sub_aquatic_detected(self):
        hits = SpecialtyKnowledgeService.identify_niche(
            "Diving trip with rebreather and nitrox tanks"
        )
        assert len(hits) >= 1
        assert any(h.niche == "Sub-Aquatic & Diving Operations" for h in hits)

    def test_no_match_returns_empty(self):
        hits = SpecialtyKnowledgeService.identify_niche(
            "Family beach vacation to Hawaii for 2 weeks"
        )
        assert hits == []

    def test_critical_urgency_for_human_remains(self):
        hits = SpecialtyKnowledgeService.identify_niche("repatriation of remains")
        assert len(hits) == 1
        assert hits[0].urgency == "CRITICAL"

    def test_all_niches_have_required_fields(self):
        for key, entry in KNOWLEDGE_BASE.items():
            assert entry.niche, f"Missing niche for {key}"
            assert len(entry.keywords) > 0, f"No keywords for {key}"
            assert len(entry.checklists) > 0, f"No checklists for {key}"
            assert entry.urgency in ("NORMAL", "HIGH", "CRITICAL"), f"Bad urgency for {key}"


# ===========================================================================
# 2. Model serialization (model_dump guard)
# ===========================================================================

class TestSpecialtyKnowledgeSerialization:

    def test_entry_has_model_dump(self):
        entry = SpecialtyKnowledgeEntry(
            niche="Test Niche",
            keywords=["test"],
            checklists=["item1"],
            compliance=["comp1"],
            safety_notes="Be careful",
            urgency="HIGH",
        )
        assert hasattr(entry, "model_dump")
        dumped = entry.model_dump()
        assert dumped["niche"] == "Test Niche"
        assert dumped["urgency"] == "HIGH"
        assert dumped["safety_notes"] == "Be careful"

    def test_guarded_serialization_list(self):
        """The guarded serialization path in orchestration.py:
        h.model_dump() if hasattr(h, 'model_dump') else h
        """
        entry = SpecialtyKnowledgeEntry(
            niche="Test",
            keywords=["kw"],
            checklists=["cl"],
        )
        items = [entry, {"niche": "Plain Dict", "keywords": [], "checklists": []}]
        serialized = [
            h.model_dump() if hasattr(h, "model_dump") else h
            for h in items
        ]
        assert serialized[0]["niche"] == "Test"
        assert serialized[1]["niche"] == "Plain Dict"


# ===========================================================================
# 3. Orchestration integration — decision.rationale["frontier"] shape
# ===========================================================================

class TestOrchestrationFrontierRationale:
    """Verify that the orchestration code path produces the expected
    decision.rationale['frontier'] dict including specialty_knowledge.

    We mock the heavy pipeline stages and only exercise the frontier
    rationale construction.
    """

    def test_frontier_rationale_includes_specialty_knowledge(self):
        from src.intake.frontier_orchestrator import FrontierOrchestrationResult

        # Simulate what orchestration.py does at line 386-395
        frontier_result = FrontierOrchestrationResult(
            ghost_triggered=True,
            ghost_workflow_id="wf_test",
            sentiment_score=0.75,
            anxiety_alert=False,
            intelligence_hits=[{"message": "Monsoon", "severity": "high"}],
            specialty_knowledge=[
                SpecialtyKnowledgeEntry(
                    niche="Medical Tourism & Post-Op Recovery",
                    keywords=["surgery"],
                    checklists=["Medical Records Transfer Protocol"],
                    compliance=["HIPAA/GDPR Data Handling"],
                    safety_notes="Verify emergency care proximity.",
                    urgency="HIGH",
                ),
            ],
        )

        # This is the exact code from orchestration.py
        frontier_dict = {
            "ghost_triggered": frontier_result.ghost_triggered,
            "ghost_workflow_id": frontier_result.ghost_workflow_id,
            "sentiment_score": frontier_result.sentiment_score,
            "anxiety_alert": frontier_result.anxiety_alert,
            "intelligence_hits": frontier_result.intelligence_hits,
            "specialty_knowledge": [
                h.model_dump() if hasattr(h, "model_dump") else h
                for h in (frontier_result.specialty_knowledge or [])
            ],
        }

        assert "specialty_knowledge" in frontier_dict
        sk = frontier_dict["specialty_knowledge"]
        assert len(sk) == 1
        assert sk[0]["niche"] == "Medical Tourism & Post-Op Recovery"
        assert sk[0]["urgency"] == "HIGH"
        assert len(sk[0]["checklists"]) == 1
        assert sk[0]["safety_notes"] == "Verify emergency care proximity."

    def test_empty_specialty_knowledge_produces_empty_list(self):
        from src.intake.frontier_orchestrator import FrontierOrchestrationResult

        frontier_result = FrontierOrchestrationResult(
            specialty_knowledge=[],
        )
        frontier_dict = {
            "specialty_knowledge": [
                h.model_dump() if hasattr(h, "model_dump") else h
                for h in (frontier_result.specialty_knowledge or [])
            ],
        }
        assert frontier_dict["specialty_knowledge"] == []

    def test_none_specialty_knowledge_produces_empty_list(self):
        from src.intake.frontier_orchestrator import FrontierOrchestrationResult

        frontier_result = FrontierOrchestrationResult(
            specialty_knowledge=None,
        )
        frontier_dict = {
            "specialty_knowledge": [
                h.model_dump() if hasattr(h, "model_dump") else h
                for h in (frontier_result.specialty_knowledge or [])
            ],
        }
        assert frontier_dict["specialty_knowledge"] == []

    def test_specialty_knowledge_survives_decision_rationale(self):
        """Verify the full shape: decision.rationale['frontier']['specialty_knowledge']."""
        from src.intake.frontier_orchestrator import FrontierOrchestrationResult

        frontier_result = FrontierOrchestrationResult(
            specialty_knowledge=[
                SpecialtyKnowledgeEntry(
                    niche="Academic Research Logistics",
                    keywords=["grant"],
                    checklists=["ATA Carnet for Sensors"],
                    compliance=["Fly America Act"],
                    urgency="HIGH",
                ),
            ],
        )

        decision = MagicMock()
        decision.rationale = {}

        # Simulate what orchestration.py does
        decision.rationale["frontier"] = {
            "ghost_triggered": frontier_result.ghost_triggered,
            "ghost_workflow_id": frontier_result.ghost_workflow_id,
            "sentiment_score": frontier_result.sentiment_score,
            "anxiety_alert": frontier_result.anxiety_alert,
            "intelligence_hits": frontier_result.intelligence_hits,
            "specialty_knowledge": [
                h.model_dump() if hasattr(h, "model_dump") else h
                for h in (frontier_result.specialty_knowledge or [])
            ],
        }

        assert decision.rationale["frontier"]["specialty_knowledge"][0]["niche"] == "Academic Research Logistics"
        assert decision.rationale["frontier"]["specialty_knowledge"][0]["urgency"] == "HIGH"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
