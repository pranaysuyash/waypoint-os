from types import SimpleNamespace

from spine_api import server


def test_inbox_stats_handles_non_dict_analytics(monkeypatch):
    monkeypatch.setattr(server.TripStore, "count_trips", lambda **kwargs: 4)
    monkeypatch.setattr(
        server.TripStore,
        "list_trips",
        lambda **kwargs: [
            {"assigned_to": None, "analytics": None},
            {"assigned_to": "agent-1", "analytics": "bad"},
            {"assigned_to": "agent-2", "analytics": {"escalation_severity": "critical"}},
            {"assigned_to": "agent-3", "analytics": {"sla_status": "at_risk"}},
        ],
    )

    stats = server.get_inbox_stats(agency=SimpleNamespace(id="agency-1"))

    assert stats["total"] == 4
    assert stats["unassigned"] == 1
    assert stats["critical"] == 1
    assert stats["atRisk"] == 1


def test_escalation_heatmap_handles_non_dict_analytics(monkeypatch):
    monkeypatch.setattr(
        server.TripStore,
        "list_trips",
        lambda **kwargs: [
            {"assigned_to": "agent-a", "analytics": "legacy-string"},
            {"assigned_to": "agent-a", "analytics": {"escalation_severity": "high"}},
            {"assigned_to": "agent-b", "analytics": None},
            {"assigned_to": "agent-b", "analytics": {"escalation_severity": "critical"}},
        ],
    )

    result = server.get_escalation_heatmap(agency=SimpleNamespace(id="agency-1"))

    by_agent = {item["agent_id"]: item for item in result["items"]}
    assert by_agent["agent-a"]["total"] == 2
    assert by_agent["agent-a"]["escalated"] == 1
    assert by_agent["agent-b"]["total"] == 2
    assert by_agent["agent-b"]["escalated"] == 1
