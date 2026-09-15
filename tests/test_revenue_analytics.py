from datetime import datetime, timezone, timedelta
from src.analytics.metrics import compute_revenue_metrics

def test_compute_revenue_metrics_empty():
    metrics = compute_revenue_metrics([])
    assert metrics.bookedRevenue == 0
    assert metrics.totalPipelineValue == 0
    assert metrics.projectedRevenue == 0
    assert len(metrics.revenueByMonth) == 0

def test_compute_revenue_metrics_booked():
    # Setup - trips created in the same month
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    trips = [
        {
            "id": "trip_1",
            "created_at": month_str,
            "status": "booked",
            "packet": {"budget": {"value": 10000}}
        },
        {
            "id": "trip_2",
            "created_at": month_str,
            "status": "in_progress",
            "meta": {"stage": "discovery"},
            "packet": {"budget": {"value": 5000}}
        }
    ]
    
    metrics = compute_revenue_metrics(trips)
    
    # Booked revenue should be 10000
    assert metrics.bookedRevenue == 10000
    # Pipeline value should be 5000 (trip_2)
    assert metrics.totalPipelineValue == 5000
    # Projected revenue = 10000 (booked) + 5000 * 0.10 (discovery) = 10500
    assert metrics.projectedRevenue == 10500
    
    assert len(metrics.revenueByMonth) == 1
    assert metrics.revenueByMonth[0].revenue == 10000
    assert metrics.revenueByMonth[0].inquiries == 2
    assert metrics.revenueByMonth[0].booked == 1

def test_compute_revenue_metrics_near_close():
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    trips = [
        {
            "id": "trip_1",
            "created_at": month_str,
            "status": "in_progress",
            "meta": {"stage": "output"},
            "packet": {"budget": {"value": 20000}}
        }
    ]
    
    metrics = compute_revenue_metrics(trips)
    assert metrics.nearCloseRevenue == 20000
    # Prob for output is 0.90
    assert metrics.projectedRevenue == 18000

def test_compute_revenue_metrics_monthly_grouping():
    # Last month
    lm = (datetime.now(timezone.utc).replace(day=1) - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # This month
    tm = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    trips = [
        {
            "id": "trip_old",
            "created_at": lm,
            "status": "booked",
            "packet": {"budget": {"value": 5000}}
        },
        {
            "id": "trip_new",
            "created_at": tm,
            "status": "booked",
            "packet": {"budget": {"value": 7000}}
        }
    ]
    
    metrics = compute_revenue_metrics(trips)
    assert len(metrics.revenueByMonth) == 2
    # Groups should be sorted by month
    assert metrics.revenueByMonth[0].revenue == 5000
    assert metrics.revenueByMonth[1].revenue == 7000

def test_compute_revenue_metrics_canonical_booked_equivalents():
    """FND-0122: the metric counts the canonical booked-equivalent states the
    write gate classifies (spine_api/core/trip_lifecycle.py), not just the
    literal "booked" no writer emits; audit-gated/ambiguous statuses stay in
    the pipeline instead of fabricating revenue."""
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _trip(trip_id: str, status: str, value: int) -> dict:
        return {
            "id": trip_id,
            "created_at": month_str,
            "status": status,
            "packet": {"budget": {"value": value}},
        }

    trips = [
        # Booked-equivalent: commitment + post-commitment + real terminal writers.
        _trip("trip_booked", "booked", 1000),
        _trip("trip_change", "change_requested", 2000),
        _trip("trip_in_trip", "in_trip", 3000),
        _trip("trip_returned", "returned", 4000),
        _trip("trip_completed", "completed", 5000),
        _trip("trip_delivered", "delivered", 6000),
        # NOT booked-equivalent: audit-gated alias (semantics pending the
        # persisted-distribution audit) and inbox lead-archival — revenue must
        # not be fabricated from these.
        _trip("trip_active", "active", 7000),
        _trip("trip_archived", "archived", 8000),
        _trip("trip_cancelled", "cancelled", 9000),
        _trip("trip_pipeline", "in_progress", 10000),
    ]

    metrics = compute_revenue_metrics(trips)

    # 1000+2000+3000+4000+5000+6000 — the six booked-equivalent rows.
    assert metrics.bookedRevenue == 21000
    # Excluded statuses (active/archived/cancelled/in_progress) remain in the
    # pipeline bucket per the metric's existing non-booked branch.
    assert metrics.totalPipelineValue == 34000
    # Projected = 21000 (booked at 100%) + 34000 * 0.10 (all excluded rows
    # default to the "discovery" stage probability).
    assert metrics.projectedRevenue == 24400
    assert metrics.revenueByMonth[0].booked == 6


if __name__ == "__main__":
    test_compute_revenue_metrics_empty()
    test_compute_revenue_metrics_booked()
    test_compute_revenue_metrics_near_close()
    test_compute_revenue_metrics_monthly_grouping()
    test_compute_revenue_metrics_canonical_booked_equivalents()
    print("All tests passed!")
