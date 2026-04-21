import pytest
from datetime import datetime, timezone, timedelta
from src.analytics.metrics import compute_revenue_metrics, STAGE_CONVERSION_PROBABILITIES
from src.analytics.models import RevenueMetrics

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

if __name__ == "__main__":
    test_compute_revenue_metrics_empty()
    test_compute_revenue_metrics_booked()
    test_compute_revenue_metrics_near_close()
    test_compute_revenue_metrics_monthly_grouping()
    print("All tests passed!")
