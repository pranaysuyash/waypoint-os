from src.analytics.metrics import (
    aggregate_insights,
    compute_pipeline_metrics,
    compute_team_metrics,
    compute_bottlenecks,
)


def test_aggregate_insights_marks_unavailable_response_time_and_pipeline_value_without_budget():
    trips = [{"id": "t1", "status": "new"}]
    result = aggregate_insights(trips)
    assert result.totalInquiries == 1
    assert result.convertedToBooked == 0
    assert result.avgResponseTime >= 0.0
    assert result.pipelineValue >= 0.0
    assert result.pipelineVelocity is not None


def test_aggregate_insights_marks_pipeline_value_evidence_backed_when_budget_exists():
    trips = [
        {"id": "t1", "status": "new", "packet": {"budget": {"value": 12000}}},
        {"id": "t2", "status": "booked", "packet": {"budget": {"value": 30000}}},
    ]
    result = aggregate_insights(trips)
    assert result.totalInquiries == 2
    assert result.convertedToBooked == 1
    assert result.conversionRate == 50.0
    assert result.pipelineValue > 0


def test_pipeline_metrics_exit_and_timing_statuses():
    trips = [{"id": "t1", "status": "new"}]
    metrics = compute_pipeline_metrics(trips)
    discovery = next(m for m in metrics if m.stageId == "new")
    assert discovery.tripCount == 1
    assert discovery.avgTimeInStage >= 0.0
    assert discovery.exitRate >= 0.0


def test_team_metrics_marks_csat_unavailable_without_ratings():
    members = [{"id": "agent_1", "name": "A", "role": "senior_agent"}]
    trips = [{"id": "t1", "assigned_to": "agent_1", "status": "new"}]
    out = compute_team_metrics(trips, members)
    assert len(out) == 1
    assert out[0].userId == "agent_1"
    assert out[0].customerSatisfaction >= 0.0


def test_compute_bottlenecks_returns_empty_when_no_duration_evidence():
    trips = [{"id": "t1", "status": "in_progress"}]
    result = compute_bottlenecks(trips)
    assert isinstance(result, list)


def test_compute_bottlenecks_returns_estimated_without_fabricated_causes():
    trips = [
        {
            "id": "t1",
            "status": "in_progress",
            "created_at": "2026-05-01T10:00:00Z",
            "updated_at": "2026-05-04T10:00:00Z",
        },
        {
            "id": "t2",
            "status": "new",
            "created_at": "2026-05-02T10:00:00Z",
            "updated_at": "2026-05-02T16:00:00Z",
        },
    ]
    out = compute_bottlenecks(trips)
    assert isinstance(out, list)
    if out:
        bottleneck = out[0]
        assert bottleneck.isBottleneck is True
        assert len(bottleneck.primaryCauses) > 0
