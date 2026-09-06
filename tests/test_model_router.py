"""
tests/test_model_router.py — Tests for Dynamic Model Capability Router (Task C-03).
"""

from src.orchestration.model_router import ModelCapabilityRouter, ModelTier


def test_model_router_standard_inquiry_flash():
    """Verify simple traveler inquiries route to Tier-1 Flash."""
    text = "We want a 5-day vacation in Rome for 2 adults with budget around $3000."
    decision = ModelCapabilityRouter.classify_and_route(text)
    assert decision.tier == ModelTier.TIER_1_FLASH
    assert "gemini-1.5-flash" in decision.model_name
    assert decision.target_latency_ms < 1000
    assert decision.cost_per_1m_tokens_usd < 0.10


def test_model_router_multi_party_pro():
    """Verify large groups and multi-party inquiries route to Tier-2 Pro."""
    text = "Planning an alumni trip for 8 friends with varying budget limits."
    decision = ModelCapabilityRouter.classify_and_route(text, context={"pax_count": 8, "subgroups_count": 2})
    assert decision.tier == ModelTier.TIER_2_PRO_REASONING
    assert "gemini-1.5-pro" in decision.model_name
    assert "multi-party group" in decision.routing_reason


def test_model_router_legal_dispute_pro():
    """Verify statutory EU261 compensation and dispute inquiries route to Tier-2 Pro."""
    text = "Flight was cancelled due to crew shortage, need to file for EU 261 compensation claim."
    decision = ModelCapabilityRouter.classify_and_route(text)
    assert decision.tier == ModelTier.TIER_2_PRO_REASONING
    assert "high-complexity semantic trigger" in decision.routing_reason


def test_model_router_edge_slm_drafting():
    """Verify client-side PII redaction and pre-filters route to Tier-0 Edge SLM."""
    decision = ModelCapabilityRouter.classify_and_route(
        text="John Doe passport A12345678",
        context={"task_type": "pii_redaction"},
    )
    assert decision.tier == ModelTier.TIER_0_EDGE_SLM
    assert "gemma" in decision.model_name or "llama" in decision.model_name
    assert decision.cost_per_1m_tokens_usd == 0.0
