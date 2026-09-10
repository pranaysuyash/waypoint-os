"""Analytics truth hardening: every metric is either real or explicitly None.

Guards against the fabrication class found in the 2026-09-10 Mimosa
remediation wave: random.uniform response times, invented stage timings,
the 4.5 CSAT baseline, the trips×15000 pipeline value, and the hardcoded
bottleneck card.
"""

from src.analytics.metrics import (
    aggregate_insights,
    compute_pipeline_metrics,
    compute_team_metrics,
    compute_bottlenecks,
)


def _history_trip(trip_id, created, events):
    """Build a trip with a durable status_history of (from, to, at) events."""
    return {
        "id": trip_id,
        "status": events[-1][1],
        "created_at": created,
        "updated_at": events[-1][2],
        "status_history": [
            {"from": f, "to": t, "at": at} for f, t, at in events
        ],
    }


def test_aggregate_insights_marks_response_time_none_without_timing_evidence():
    trips = [{"id": "t1", "status": "new"}]
    result = aggregate_insights(trips)
    assert result.totalInquiries == 1
    assert result.convertedToBooked == 0
    assert result.avgResponseTime is None
    assert result.pipelineValue == 0.0
    assert result.pipelineVelocity is not None


def test_aggregate_insights_computes_response_time_from_first_transition():
    trips = [
        _history_trip(
            "t1",
            "2026-05-01T10:00:00Z",
            [("new", "assigned", "2026-05-01T14:00:00Z")],
        ),
        _history_trip(
            "t2",
            "2026-05-02T10:00:00Z",
            [("new", "assigned", "2026-05-02T11:00:00Z")],
        ),
    ]
    result = aggregate_insights(trips)
    # 4h and 1h → mean 2.5h
    assert result.avgResponseTime == 2.5


def test_aggregate_insights_handles_null_analytics_payloads():
    trips = [{"id": "t1", "status": "new", "analytics": None}]
    result = aggregate_insights(trips)
    assert result.totalInquiries == 1
    assert result.convertedToBooked == 0


def test_aggregate_insights_pipeline_value_sums_real_budgets_not_multiplier():
    trips = [
        {"id": "t1", "status": "new", "packet": {"budget": {"value": 12000}}},
        {"id": "t2", "status": "booked", "packet": {"budget": {"value": 30000}}},
    ]
    result = aggregate_insights(trips)
    assert result.totalInquiries == 2
    assert result.convertedToBooked == 1
    assert result.conversionRate == 50.0
    # Only the non-terminal trip's budget counts (the old code said 2*15000).
    assert result.pipelineValue == 12000


def test_aggregate_insights_velocity_uses_real_dwell_and_never_fabricated_fallbacks():
    trips = [
        _history_trip(
            "t1",
            "2026-05-01T10:00:00Z",
            [("new", "assigned", "2026-05-02T10:00:00Z")],  # 24h in new
        ),
    ]
    result = aggregate_insights(trips)
    v = result.pipelineVelocity
    # 24h dwell in "new" = 1.0 day; no fabricated 1.2/2.4/4.1 defaults.
    assert v.stage1To2 == 1.0
    assert v.stage2To3 == 0.0
    assert v.stage3To4 == 0.0
    assert v.averageTotal == 1.0


def test_pipeline_metrics_none_without_history_and_real_with_history():
    trips = [{"id": "t1", "status": "new"}]
    metrics = compute_pipeline_metrics(trips)
    discovery = next(m for m in metrics if m.stageId == "new")
    assert discovery.tripCount == 1
    assert discovery.avgTimeInStage is None
    assert discovery.exitRate is None
    assert discovery.avgTimeToExit is None

    rich = [
        _history_trip(
            "t1",
            "2026-05-01T10:00:00Z",
            [
                ("new", "assigned", "2026-05-01T22:00:00Z"),  # 12h in new, exited
            ],
        ),
        _history_trip(
            "t2",
            "2026-05-02T10:00:00Z",
            [("new", "assigned", "2026-05-02T13:00:00Z")],  # 3h in new, exited
        ),
    ]
    metrics2 = compute_pipeline_metrics(rich)
    discovery2 = next(m for m in metrics2 if m.stageId == "new")
    assert discovery2.avgTimeInStage == 7.5  # mean(12, 3)
    assert discovery2.exitRate == 100.0
    assert discovery2.avgTimeToExit == 7.5


def test_team_metrics_marks_csat_none_without_ratings():
    members = [{"id": "agent_1", "name": "A", "role": "senior_agent"}]
    trips = [{"id": "t1", "assigned_to": "agent_1", "status": "new"}]
    out = compute_team_metrics(trips, members)
    assert len(out) == 1
    assert out[0].userId == "agent_1"
    assert out[0].customerSatisfaction is None


def test_team_metrics_computes_csat_from_real_ratings():
    members = [{"id": "agent_1", "name": "A", "role": "senior_agent"}]
    trips = [
        {
            "id": "t1",
            "assigned_to": "agent_1",
            "status": "completed",
            "packet": {"feedback": {"rating": 5}},
        },
        {
            "id": "t2",
            "assigned_to": "agent_1",
            "status": "completed",
            "analytics": {"latest_feedback": {"rating": 4}},
        },
    ]
    out = compute_team_metrics(trips, members)
    assert out[0].customerSatisfaction == 4.5


def test_team_metrics_handles_null_payloads_on_assigned_trip():
    members = [{"id": "agent_1", "name": "A", "role": "senior_agent"}]
    trips = [
        {
            "id": "t1",
            "assigned_to": "agent_1",
            "status": "new",
            "extracted": None,
            "packet": None,
            "analytics": None,
        }
    ]
    out = compute_team_metrics(trips, members)
    assert len(out) == 1
    assert out[0].activeTrips == 1


def test_operational_alerts_handles_null_analytics_payloads():
    from src.analytics.metrics import compute_alerts

    assert compute_alerts([{"id": "t1", "analytics": None}]) == []


def test_compute_bottlenecks_empty_without_dwell_evidence():
    trips = [{"id": "t1", "status": "in_progress"}]
    result = compute_bottlenecks(trips)
    assert result == []


def test_compute_bottlenecks_reports_slowest_real_stage_without_fabricated_causes():
    trips = [
        _history_trip(
            "t1",
            "2026-05-01T10:00:00Z",
            [
                ("new", "assigned", "2026-05-01T11:00:00Z"),  # 1h in new
                ("assigned", "in_progress", "2026-05-04T15:00:00Z"),  # 76h in assigned
            ],
        ),
    ]
    out = compute_bottlenecks(trips)
    assert len(out) == 1
    bottleneck = out[0]
    assert bottleneck.stageId == "assigned"
    assert bottleneck.avgTimeInStage == 76.0
    assert bottleneck.isBottleneck is True
    assert bottleneck.severity == "high"
    # Causes are never fabricated — only measured dwell is reported.
    assert bottleneck.primaryCauses == []
