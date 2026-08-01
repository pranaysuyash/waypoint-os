"""
tests/test_ai_governance_registry.py — Test suite for AI Workforce Governance Registry.
"""

from src.governance.registry import AIWorkforceRegistry, AgentTier


def test_ai_governance_registry_bootstrap():
    registry = AIWorkforceRegistry()
    intake_agent = registry.get_agent("agent_intake_01")
    assert intake_agent is not None
    assert intake_agent.tier == AgentTier.DETERMINISTIC_GATED
    assert "parse_freeform_text" in intake_agent.allowed_actions


def test_ai_governance_action_validation():
    registry = AIWorkforceRegistry()
    
    # Authorized action
    assert registry.validate_action("agent_intake_01", "parse_freeform_text") is True
    
    # Unauthorized action
    assert registry.validate_action("agent_intake_01", "unauthorized_action") is False
    
    # Non-existent agent
    assert registry.validate_action("non_existent_agent", "parse_freeform_text") is False
