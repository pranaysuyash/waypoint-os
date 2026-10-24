from datetime import datetime, timezone, timedelta
from src.analytics.metrics import compute_revenue_metrics


def _receipt(value, timestamp):
    return {
        "total_charged_usd": value,
        "fulfilled_at": timestamp,
        "fulfillment_provider_key": "synthetic-contract-fixture",
        "pnr_locator": "SYNTHETIC",
        "reality_tier": "real",
        "provider_connected": True,
    }


def test_compute_revenue_metrics_empty():
    metrics = compute_revenue_metrics([])
    assert metrics.bookedRevenue is None
    assert metrics.totalPipelineValue is None
    assert metrics.projectedRevenue is None
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
            "packet": {"budget": {"value": 99999, "currency": "USD"}},
            "booking_confirmation": _receipt(10000, month_str),
        },
        {
            "id": "trip_2",
            "created_at": month_str,
            "status": "in_progress",
            "meta": {"stage": "discovery"},
            "packet": {"budget": {"value": 5000, "currency": "USD"}}
        }
    ]
    
    metrics = compute_revenue_metrics(trips)
    
    # Legacy key represents confirmed customer value, never the budget or earnings.
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
            "packet": {"budget": {"value": 20000, "currency": "USD"}}
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
            "packet": {"budget": {"value": 99999, "currency": "USD"}},
            "booking_confirmation": _receipt(5000, lm),
        },
        {
            "id": "trip_new",
            "created_at": tm,
            "status": "booked",
            "packet": {"budget": {"value": 99999, "currency": "USD"}},
            "booking_confirmation": _receipt(7000, tm),
        }
    ]
    
    metrics = compute_revenue_metrics(trips)
    assert len(metrics.revenueByMonth) == 2
    # Groups should be sorted by month
    assert metrics.revenueByMonth[0].revenue == 5000
    assert metrics.revenueByMonth[1].revenue == 7000

def test_compute_revenue_metrics_canonical_booked_equivalents():
    """FND-0122 retained vocabulary coverage, superseded commercial oracle:
    lifecycle aliases do not independently establish an amount or booking."""
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _trip(trip_id: str, status: str, value: int) -> dict:
        return {
            "id": trip_id,
            "created_at": month_str,
            "status": status,
            "packet": {"budget": {"value": value, "currency": "USD"}},
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

    assert metrics.bookedRevenue is None
    # Archive/cancellation are no longer treated as active sales potential.
    assert metrics.totalPipelineValue == 17000
    assert metrics.projectedRevenue == 1700
    assert metrics.revenueByMonth[0].booked == 0


if __name__ == "__main__":
    test_compute_revenue_metrics_empty()
    test_compute_revenue_metrics_booked()
    test_compute_revenue_metrics_near_close()
    test_compute_revenue_metrics_monthly_grouping()
    test_compute_revenue_metrics_canonical_booked_equivalents()
    print("All tests passed!")
