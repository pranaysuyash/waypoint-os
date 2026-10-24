"""Determinism audit remediation — regression gates for FND-0352..0357.

Audit record: Docs/review/DETERMINISM_AUDIT_2026-10-21.md. Every finding in
that audit shares one failure class — deterministic code faking probabilism
(hardcoded confidence, wrong provenance, dropped verdicts). These tests pin
the honest behaviour so the class cannot silently return.

Sensitivity (OPERATING_DOCTRINE §3): each test asserts the invariant that the
pre-fix code violated, so re-introducing the defect (the mutation IS the old
code) makes it fail — S2/S3 evidence is recorded in the audit's remediation
section. Tier 2 (targeted) unless stated; no provider calls are made.
"""

from __future__ import annotations

import logging
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")


# =============================================================================
# FND-0352 — ambiguity rule fallback: confidence is data, not decoration
# =============================================================================


def _mock_jev(decision=None, raise_exc=None):
    from src.llm.typesafe_client import TypesafeJevClient

    client = MagicMock(spec=TypesafeJevClient)
    client.is_available.return_value = True
    if raise_exc is not None:
        client.decide.side_effect = raise_exc
    else:
        client.decide.return_value = decision or {}
    return client


def test_fnd0352_rule_fallback_reports_no_confidence_with_provenance():
    """The keyword scan has no calibration → confidence None, method labeled,
    and the reason it served (lane unconfigured) is recorded."""
    from src.intake.ambiguity_classifier import (
        CONFIDENCE_METHOD_RULE,
        FALLBACK_MODEL_LANE_UNCONFIGURED,
        IntakeAmbiguityClassifier,
    )

    report = IntakeAmbiguityClassifier(client=None).evaluate(
        "trip to Paris in June 2027 for a family of 4, budget 10,000 EUR"
    )
    assert report.source == "deterministic_fallback"
    assert report.confidence is None
    assert report.confidence_method == CONFIDENCE_METHOD_RULE
    assert report.fallback_reason == FALLBACK_MODEL_LANE_UNCONFIGURED
    as_dict = report.to_dict()
    assert as_dict["confidence"] is None
    assert as_dict["confidence_method"] == CONFIDENCE_METHOD_RULE
    assert as_dict["fallback_reason"] == FALLBACK_MODEL_LANE_UNCONFIGURED


def test_fnd0352_empty_input_escalates_without_fabricated_certainty():
    from src.intake.ambiguity_classifier import (
        FALLBACK_EMPTY_INPUT,
        IntakeAmbiguityClassifier,
    )

    report = IntakeAmbiguityClassifier(client=None).evaluate("   ")
    assert report.is_escalate
    assert report.confidence is None
    assert report.fallback_reason == FALLBACK_EMPTY_INPUT


def test_fnd0352_model_call_failure_is_distinguished_from_unconfigured_lane():
    from src.intake.ambiguity_classifier import (
        FALLBACK_MODEL_CALL_FAILED,
        IntakeAmbiguityClassifier,
    )

    classifier = IntakeAmbiguityClassifier(client=_mock_jev(raise_exc=RuntimeError("jev down")))
    report = classifier.evaluate("trip to Paris in June for 4 people")
    assert report.source == "deterministic_fallback"
    assert report.confidence is None
    assert report.fallback_reason == FALLBACK_MODEL_CALL_FAILED


def test_fnd0352_model_path_is_labeled_model_calibrated():
    from src.intake.ambiguity_classifier import (
        CONFIDENCE_METHOD_MODEL,
        IntakeAmbiguityClassifier,
    )

    client = _mock_jev({
        "destination_clarity": True,
        "dates_clarity": True,
        "party_clarity": True,
        "budget_clarity": False,
        "intake_action": "PROCEED",
        "jev_confidence": 0.92,
    })
    report = IntakeAmbiguityClassifier(client=client).evaluate("Paris in June for 4")
    assert report.confidence == 0.92
    assert report.confidence_method == CONFIDENCE_METHOD_MODEL
    assert report.fallback_reason is None


def _packet_for_decision(text: str):
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope

    env = SourceEnvelope.from_freeform(text=text, source="customer_message", actor="customer")
    return ExtractionPipeline().extract([env])


def _ambiguity_flags(packet):
    from src.intake.decision import run_gap_and_decision

    decision = run_gap_and_decision(packet)
    return [f for f in decision.risk_flags if f.get("flag") == "low_confidence_semantic_ambiguity"]


_DECISION_TEXT = (
    "we want kerala in october, 6 nights, flying from pune, 2 adults, budget 1.5 lakh."
)


@pytest.mark.parametrize(
    "semantic_ambiguity, expect_flag, expected_source",
    [
        # Calibrated-low → advisory (unchanged behaviour).
        ({"confidence": 0.41, "confidence_method": "model_calibrated"}, True, "semantic_ambiguity:model_calibrated"),
        # Calibrated-high → no advisory (unchanged behaviour).
        ({"confidence": 0.90, "confidence_method": "model_calibrated"}, False, None),
        # Model answered without calibration → advisory.
        ({"confidence": None, "confidence_method": "model_calibrated"}, True, "semantic_ambiguity:model_calibrated"),
        # Model lane configured but FAILED → advisory (ops must see degradation).
        (
            {"confidence": None, "confidence_method": "rule_heuristic", "fallback_reason": "model_call_failed"},
            True,
            "semantic_ambiguity:rule_heuristic",
        ),
        # Lane deliberately unconfigured (ADR-008 posture) → rule mode by
        # design: provenance recorded, no per-run nag.
        (
            {"confidence": None, "confidence_method": "rule_heuristic", "fallback_reason": "model_lane_unconfigured"},
            False,
            None,
        ),
    ],
)
def test_fnd0352_decision_advisory_policy(semantic_ambiguity, expect_flag, expected_source):
    """The pre-fix rule path reported a hardcoded 0.85 which silently passed
    the 0.60 gate on every fallback; the policy is now explicit per method
    and fallback reason."""
    packet = _packet_for_decision(_DECISION_TEXT)
    packet.metadata["semantic_ambiguity"] = dict(semantic_ambiguity, action="PROCEED")
    flags = _ambiguity_flags(packet)
    assert bool(flags) is expect_flag
    if expect_flag:
        assert flags[0]["source"] == expected_source
        assert flags[0]["severity"] == "medium"


def test_fnd0352_mutation_hardcoded_confidence_would_suppress_advisory():
    """S3 sensitivity: the old behaviour (rule path claiming 0.85) must NOT
    raise the advisory — proving the policy test above is sensitive to the
    exact defect, and that a model-failed fallback is caught by it."""
    packet = _packet_for_decision(_DECISION_TEXT)
    packet.metadata["semantic_ambiguity"] = {
        "action": "PROCEED",
        "confidence": 0.85,  # the pre-fix fabricated constant
        "confidence_method": "rule_heuristic",
        "fallback_reason": "model_call_failed",
    }
    assert _ambiguity_flags(packet) == []  # 0.85 silences the gate → the lie
    packet.metadata["semantic_ambiguity"]["confidence"] = None  # the fix
    assert len(_ambiguity_flags(packet)) == 1


# =============================================================================
# FND-0353 — context resolver may narrow, never invent
# =============================================================================


def test_fnd0353_validator_rejects_model_invented_candidate():
    from src.intake import context_resolver

    outcome = context_resolver.validate_resolver_response(
        {
            "destination_candidates": ["Nice", "Lisbon"],
            "destination_status": "definite",
            "reasoning": "model decided Lisbon",
        },
        ["Nice"],
    )
    assert outcome is None


def test_fnd0353_validator_narrows_and_keeps_deterministic_casing():
    from src.intake import context_resolver

    outcome = context_resolver.validate_resolver_response(
        {"destination_candidates": ["nice"], "destination_status": "definite", "reasoning": "x"},
        ["Reading", "Nice"],
    )
    assert outcome is not None
    assert outcome["candidates"] == ["Nice"]
    assert outcome["status"] == "definite"


def test_fnd0353_validator_rejects_any_name_when_deterministic_set_is_empty():
    from src.intake import context_resolver

    assert (
        context_resolver.validate_resolver_response(
            {"destination_candidates": ["Goa"], "destination_status": "definite"}, []
        )
        is None
    )
    # Empty-for-empty (status open/undecided) remains a valid honest outcome.
    assert (
        context_resolver.validate_resolver_response(
            {"destination_candidates": [], "destination_status": "open"}, []
        )
        is not None
    )


def test_fnd0353_resolver_rejects_invented_candidate_end_to_end(monkeypatch):
    """A model inventing a destination violates the contract → deterministic
    semi_open stands (operator confirms); never an asserted fact."""
    from src.intake import context_resolver

    class _InventingClient:
        model = "test-model"

        def decide(self, prompt, schema, temperature=None):
            return {
                "destination_candidates": ["Kerala", "Lisbon"],
                "destination_status": "definite",
                "reasoning": "invented",
            }

    monkeypatch.delenv("EXTRACTION_CONTEXT_RESOLVER", raising=False)
    monkeypatch.setattr(context_resolver, "get_default_client", lambda: _InventingClient())
    outcome = context_resolver.resolve_destination_from_context(
        "scrap coorg, just kerala please", ["Kerala", "Coorg"], "semi_open"
    )
    assert outcome["available"] is False
    assert outcome["reason"].startswith("resolver_response_violated_contract")


def test_fnd0353_resolver_requests_temperature_zero_for_closed_set_decision(monkeypatch):
    from src.intake import context_resolver

    seen = {}

    class _Client:
        model = "test-model"

        def decide(self, prompt, schema, temperature=None):
            seen["temperature"] = temperature
            seen["prompt"] = prompt
            return {"destination_candidates": ["Kerala"], "destination_status": "definite", "reasoning": "ok"}

    monkeypatch.delenv("EXTRACTION_CONTEXT_RESOLVER", raising=False)
    monkeypatch.setattr(context_resolver, "get_default_client", lambda: _Client())
    outcome = context_resolver.resolve_destination_from_context(
        "scrap coorg, just kerala please", ["Kerala", "Coorg"], "semi_open"
    )
    assert outcome["available"] is True
    assert outcome["candidates"] == ["Kerala"]
    assert seen["temperature"] == 0.0
    assert "NEVER add a name" in seen["prompt"]


def _slot_excerpts(slot) -> str:
    return " | ".join(getattr(ref, "excerpt", "") or "" for ref in (slot.evidence_refs or []))


def test_fnd0353_narrowed_candidates_fact_carries_resolver_provenance(monkeypatch):
    """When the resolver narrows the collision set, the stored fact still holds
    only traveler-written gazetteer names, and its evidence names the model
    that chose them (Tier 3: through the real extraction pipeline)."""
    from src.intake import context_resolver
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import AuthorityLevel, SourceEnvelope

    monkeypatch.setenv("EXTRACTION_CONTEXT_RESOLVER", "1")
    monkeypatch.setattr(
        context_resolver,
        "resolve_destination_from_context",
        lambda text, cands, status: {
            "available": True,
            "candidates": ["Kerala"],
            "status": "definite",
            "reasoning": "coorg was scrapped in context",
            "provider": "FakeProvider",
            "model": "fake-model",
        },
    )
    env = SourceEnvelope.from_freeform(
        text="scrap coorg, the kids are too young for that drive. just kerala please.",
        source="customer_message",
        actor="customer",
    )
    packet = ExtractionPipeline().extract([env])

    slot = packet.facts["destination_candidates"]
    assert slot.value == ["Kerala"]
    assert slot.authority_level == AuthorityLevel.EXPLICIT_USER
    excerpts = _slot_excerpts(slot)
    assert "context-resolver [FakeProvider:fake-model] disambiguated" in excerpts
    assert "['Kerala', 'Coorg']" in excerpts and "['Kerala']" in excerpts
    # Status stays a labeled hypothesis, never a silent fact.
    assert "destination_status" in packet.hypotheses
    assert "destination_status" not in packet.facts


def test_fnd0309_reprocess_merge_provenance_now_reaches_the_slot():
    """In-blast-radius fix: ``final_raw`` carried the FND-0309 merge note but
    the bare ``dest_raw`` was passed as evidence, so the note never reached
    the slot. A second envelope naming a new city must carry the earlier
    gazetteer-confirmed city forward WITH the merge record."""
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope

    env1 = SourceEnvelope.from_freeform(
        text="need 3 nights in jaipur in mid-february for 2 adults.",
        source="customer_message",
        actor="customer",
    )
    env2 = SourceEnvelope.from_freeform(
        text="they want varanasi for their 45th anniversary on november 18th, 3 nights",
        source="customer_message",
        actor="customer",
    )
    packet = ExtractionPipeline().extract([env1, env2])
    slot = packet.facts["destination_candidates"]
    assert "Jaipur" in slot.value and "Varanasi" in slot.value
    assert "reprocess merge: carried forward" in _slot_excerpts(slot)


# =============================================================================
# FND-0354 — failure-triage Jev branch is reachable (credential-gated)
# =============================================================================


def test_fnd0354_recovery_agent_triage_engine_is_wired_with_canonical_jev_client(monkeypatch):
    from src.agents import recovery_agent
    from src.llm.typesafe_client import TypesafeJevClient

    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.delenv("ENABLE_LIVE_JEV_SERVING", raising=False)

    engine = recovery_agent._get_failure_triage_engine()
    assert engine is not None
    assert isinstance(engine.jev_client, TypesafeJevClient)
    # No credential → honest heuristic, exactly today's behaviour.
    assert engine.jev_client.is_available() is False
    opinion = engine.evaluate_failure(error_message="KeyError: 'x'", traceback_text="", stage="strategy")
    assert opinion.model == "heuristic"


def test_fnd0354_jev_branch_runs_when_client_available():
    from src.decision.failure_triage import FailureTriageEngine

    client = MagicMock()
    client.is_available.return_value = True
    client.model = "jev-test"
    client.raw_query.return_value = {
        "model": "jev-test",
        "answers": {
            "failure_class": {"choice": "tool", "confidence": 0.9, "probabilities": {"tool": 0.9}},
            "severity": {"score": 1.0},
        },
    }
    opinion = FailureTriageEngine(jev_client=client).evaluate_failure("boom", "tb", stage="x")
    client.raw_query.assert_called_once()
    assert opinion.model == "jev-test"
    assert opinion.confidence == 0.9


# =============================================================================
# FND-0355 — contextual heuristic must not claim a model ran
# =============================================================================


def test_fnd0355_heuristic_fallback_is_labeled_rule_and_inherits_rule_confidence():
    from src.suitability.llm_scorer import LLMContextualScorer
    from src.suitability.models import ActivityDefinition, ParticipantRef, SuitabilityContext
    from src.suitability.scoring import evaluate_activity

    activity = ActivityDefinition(
        activity_id="temple_walk", canonical_name="Temple Stair Walk", source="static",
        intensity="moderate", duration_hours=3.0,
    )
    participant = ParticipantRef(kind="person", ref_id="e1", label="elderly", age=75)
    context = SuitabilityContext(
        destination_keys=["kyoto"],
        day_activities=[
            ActivityDefinition(activity_id="h1", canonical_name="Hike", source="static", duration_hours=4.0),
            ActivityDefinition(activity_id="h2", canonical_name="Garden", source="static", duration_hours=4.0),
            activity,
        ],
    )
    baseline = evaluate_activity(activity, participant, context)
    result = LLMContextualScorer(cache_storage=None, llm_client=None)._contextual_heuristic_fallback(
        activity, participant, context, baseline
    )
    assert result.source == "rule"
    assert result.confidence == baseline.confidence
    assert result.confidence != 0.85 or baseline.confidence == 0.85  # never the old constant by fiat


# =============================================================================
# FND-0356 — checker verdict reaches the result and the operator surface
# =============================================================================


def _frontier_fixtures():
    from src.intake.decision import DecisionResult
    from src.intake.packet_models import CanonicalPacket, Slot

    packet = CanonicalPacket(packet_id="fnd0356-packet")
    packet.raw_note = "Emergency trip, something went very wrong"
    packet.facts["resolved_destination"] = Slot(value="Bali", authority_level="imported_structured", confidence=0.9)
    packet.operating_mode = "emergency"
    decision = DecisionResult(
        packet_id="fnd0356-packet", current_stage="discovery",
        operating_mode="emergency", decision_state="STOP_NEEDS_REVIEW",
    )
    return packet, decision


def test_fnd0356_frontier_result_records_checker_status_and_delta():
    from src.intake.checker_agent import CheckerAuditResult
    from src.intake.frontier_orchestrator import run_frontier_orchestration

    packet, decision = _frontier_fixtures()
    with patch("src.intake.frontier_orchestrator.checker_agent") as mock_checker:
        mock_checker.audit.return_value = CheckerAuditResult(
            is_valid=False, requires_manual=True, reason="High-stakes purpose detected", confidence_delta=0.0
        )
        result = run_frontier_orchestration(packet, decision, agency_settings=None)
    assert result.ghost_triggered is True
    assert result.checker_status == "flagged"
    assert result.requires_manual_audit is True
    assert result.audit_reason == "High-stakes purpose detected"
    assert result.checker_confidence_delta == 0.0


def test_fnd0356_frontier_result_default_status_is_not_triggered():
    from src.intake.frontier_orchestrator import FrontierOrchestrationResult

    assert FrontierOrchestrationResult().checker_status == "not_triggered"


def test_fnd0356_verdict_rides_rationale_and_risk_flags_through_the_spine():
    """Tier 3: through run_spine_once, a flagged checker verdict must land in
    decision.rationale['frontier'] AND in the strategy's operator-facing
    risk flags via the canonical decision.risk_flags path."""
    from src.intake.config.agency_settings import AgencySettings, AgencyTier, AiAgentSettings
    from src.intake.frontier_orchestrator import FrontierOrchestrationResult
    from src.intake.orchestration import run_spine_once
    from src.intake.packet_models import SourceEnvelope

    flagged = FrontierOrchestrationResult(
        ghost_triggered=True, ghost_workflow_id="ghost_test",
        requires_manual_audit=True, audit_reason="Missing budget data in non-followup state.",
        checker_status="flagged", checker_confidence_delta=0.0,
    )
    # Same rich envelope tests/test_feature_gates.py uses: it reliably passes
    # the NB01 completion gate so the pipeline reaches phase 3.2 (frontier).
    env = SourceEnvelope.from_freeform(
        text=(
            "We are planning a family leisure trip from Bangalore to Singapore "
            "around 9th to 14th Feb 2026. We are 2 adults with budget around 3L "
            "and do not want a rushed itinerary."
        ),
        source="customer_message", actor="customer",
    )
    # Frontier orchestration is tier-gated (starter off); PRO + explicit gate on.
    settings = AgencySettings(
        agency_id="fnd0356-agency", tier=AgencyTier.PRO,
        ai_agent=AiAgentSettings(enable_frontier_orchestration=True),
    )
    with patch("src.intake.orchestration.run_frontier_orchestration", return_value=flagged):
        result = run_spine_once([env], agency_settings=settings)

    frontier = result.decision.rationale["frontier"]
    assert frontier["checker_status"] == "flagged"
    assert frontier["requires_manual_audit"] is True
    assert frontier["audit_reason"] == "Missing budget data in non-followup state."
    assert "checker_confidence_delta" in frontier
    checker_flags = [f for f in result.decision.risk_flags if f.get("flag") == "checker_manual_audit_required"]
    assert len(checker_flags) == 1
    assert checker_flags[0]["severity"] == "high"
    assert checker_flags[0]["source"] == "checker_agent:flagged"
    assert any("manual audit" in f.lower() for f in result.strategy.risk_flags)


# =============================================================================
# FND-0357 — no transcription, no transcription confidence
# =============================================================================


def test_fnd0357_supplied_transcript_has_no_fabricated_confidence():
    from src.intake.audio_intake import TRANSCRIPTION_METHOD_SUPPLIED, VoiceBriefingIntakeEngine

    result = VoiceBriefingIntakeEngine.process_voice_memo(
        audio_file_name="briefing_01.m4a",
        simulated_transcript="uh we want, like, goa for 4 nights in december",
    )
    assert result.confidence_score is None
    assert result.transcription_method == TRANSCRIPTION_METHOD_SUPPLIED
    assert result.to_dict()["confidence_score"] is None


# =============================================================================
# Sampling forensics — per-call record, hashes only
# =============================================================================


def test_llm_call_record_emits_hashes_and_never_content(caplog):
    from src.llm.base import content_sha256, record_llm_call

    class _Client:
        pass

    client = _Client()
    secret_prompt = "passport number P1234567 for Asha"
    with caplog.at_level(logging.INFO, logger="llm.calls"):
        record = record_llm_call(
            provider="openai", model="gpt-4.1-nano", prompt=secret_prompt,
            response_text='{"ok": true}', temperature_requested=0.3,
            temperature_effective=0.3, latency_ms=12.34, client=client,
        )
    assert record["prompt_sha256"] == content_sha256(secret_prompt)
    assert record["response_sha256"] == content_sha256('{"ok": true}')
    assert record["temperature_effective"] == 0.3
    assert record["latency_ms"] == 12.3
    assert client.last_call_record is record
    joined = " ".join(r.getMessage() for r in caplog.records)
    assert record["prompt_sha256"] in joined
    assert "P1234567" not in joined and "Asha" not in joined


def test_llm_call_record_never_raises_on_odd_input():
    from src.llm.base import record_llm_call

    record = record_llm_call(
        provider="x", model="y", prompt=None, response_text=object(),
        temperature_requested=None, temperature_effective=None, latency_ms=None,
    )
    assert record["prompt_chars"] == 0
    assert record["latency_ms"] is None


def test_typesafe_post_records_call_without_sampling_temperature(monkeypatch):
    from src.llm.typesafe_client import TypesafeJevClient

    client = TypesafeJevClient(api_key="test-key")

    class _Resp:
        status_code = 200
        text = '{"answers": {}}'

        def json(self):
            return {"answers": {}}

    class _HttpClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, headers=None):
            return _Resp()

    monkeypatch.setattr("src.llm.typesafe_client.httpx.Client", _HttpClient)
    client.raw_query(state="failure state", questions={"q": {"type": "noul", "instructions": "x"}})
    rec = client.last_call_record
    assert rec["provider"] == "typesafe"
    assert rec["temperature_effective"] is None and rec["temperature_requested"] is None
    assert rec["prompt_sha256"]
