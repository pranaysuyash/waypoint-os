from spine_api.routers import settings as settings_router


def test_seasonal_simulation_scenarios_are_distinct(session_client, monkeypatch):
    plan = {
        "plan_id": "season_test_001",
        "name": "Scenario Distinction Check",
        "status": "active",
        "destination": "India / Europe",
        "campaign_window_start_month": 6,
        "campaign_window_end_month": 9,
        "channel_mix": {
            "organic": 0.6,
            "email": 0.4,
        },
        "target_budget_min": 10000,
        "target_budget_max": 18000,
        "notes": "Test plan for scenario differentiation.",
        "blocklist": ["budget_violation"],
    }

    monkeypatch.setattr(
        settings_router.ConfigStore,
        "get_seasonal_campaign",
        lambda agency_id, plan_id: dict(plan),
    )

    baseline = session_client.post(
        "/api/settings/seasonal/campaigns/season_test_001/simulate",
        json={"scenario": "baseline"},
    )
    aggressive = session_client.post(
        "/api/settings/seasonal/campaigns/season_test_001/simulate",
        json={"scenario": "aggressive"},
    )
    conservative = session_client.post(
        "/api/settings/seasonal/campaigns/season_test_001/simulate",
        json={"scenario": "conservative"},
    )

    assert baseline.status_code == 200
    assert aggressive.status_code == 200
    assert conservative.status_code == 200

    baseline_json = baseline.json()
    aggressive_json = aggressive.json()
    conservative_json = conservative.json()

    assert baseline_json["scenario"] == "baseline"
    assert aggressive_json["scenario"] == "aggressive"
    assert conservative_json["scenario"] == "conservative"

    assert aggressive_json["projected_leads"] > baseline_json["projected_leads"] > conservative_json["projected_leads"]
    assert aggressive_json["projected_bookings"] > baseline_json["projected_bookings"] > conservative_json["projected_bookings"]
    assert aggressive_json["projected_margin_pct"] < baseline_json["projected_margin_pct"] < conservative_json["projected_margin_pct"]
    assert conservative_json["confidence"] > baseline_json["confidence"] > aggressive_json["confidence"]
    assert any("Aggressive pacing" in note for note in aggressive_json["notes"])
    assert any("Conservative pacing" in note for note in conservative_json["notes"])
