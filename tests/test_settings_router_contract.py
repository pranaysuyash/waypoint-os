from __future__ import annotations


def test_settings_router_returns_frontend_consumed_settings_shape(session_client):
    response = session_client.get("/api/settings")

    assert response.status_code == 200
    payload = response.json()

    assert payload["agency_id"]
    assert "tier" in payload
    assert payload["tier"] in ("starter", "pro", "enterprise")
    assert set(payload["profile"]) >= {
        "agency_name",
        "sub_brand",
        "plan_label",
        "contact_email",
        "contact_phone",
        "logo_url",
        "website",
    }
    assert set(payload["operational"]) >= {
        "target_margin_pct",
        "default_currency",
        "operating_hours",
        "operating_days",
        "preferred_channels",
        "brand_tone",
    }
    assert set(payload["operational"]["operating_hours"]) >= {"start", "end"}
    assert set(payload["autonomy"]) >= {
        "approval_gates",
        "mode_overrides",
        "auto_proceed_with_warnings",
        "learn_from_overrides",
        "auto_reprocess_on_edit",
        "allow_explicit_reassess",
        "auto_reprocess_stages",
        "min_proceed_confidence",
        "min_draft_confidence",
    }


def test_settings_router_llm_guard_state_shape(session_client):
    response = session_client.get("/api/settings/llm-guard")

    assert response.status_code == 200
    payload = response.json()

    assert set(payload) >= {
        "enabled",
        "agency_id",
        "max_calls_per_hour",
        "max_calls_per_model",
        "daily_budget",
        "budget_mode",
        "current_hourly_calls",
        "current_daily_cost",
    }
    assert isinstance(payload["enabled"], bool)
    assert isinstance(payload["max_calls_per_model"], dict)
    assert isinstance(payload["current_hourly_calls"], int)
    assert isinstance(payload["current_daily_cost"], (int, float))


def test_settings_router_returns_autonomy_shape(session_client):
    response = session_client.get("/api/settings/autonomy")

    assert response.status_code == 200
    payload = response.json()

    assert payload["agency_id"]
    assert set(payload) >= {
        "approval_gates",
        "mode_overrides",
        "auto_proceed_with_warnings",
        "learn_from_overrides",
        "auto_reprocess_on_edit",
        "allow_explicit_reassess",
        "auto_reprocess_stages",
        "min_proceed_confidence",
        "min_draft_confidence",
    }


def test_settings_router_returns_pipeline_and_approval_collections(session_client):
    pipeline_response = session_client.get("/api/settings/pipeline")
    approvals_response = session_client.get("/api/settings/approvals")

    assert pipeline_response.status_code == 200
    assert approvals_response.status_code == 200
    assert isinstance(pipeline_response.json()["items"], list)
    assert isinstance(approvals_response.json()["items"], list)


def test_settings_router_operational_update_returns_frontend_settings_shape(session_client):
    response = session_client.post(
        "/api/settings/operational",
        json={"target_margin_pct": 24.5, "agency_name": "Waypoint HQ"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert set(payload) >= {"agency_id", "seasonal", "profile", "operational", "autonomy"}
    assert payload["agency_id"]
    assert set(payload["profile"]) >= {
        "agency_name",
        "sub_brand",
        "plan_label",
        "contact_email",
        "contact_phone",
        "logo_url",
        "website",
    }
    assert set(payload["operational"]) >= {
        "target_margin_pct",
        "default_currency",
        "operating_hours",
        "operating_days",
        "preferred_channels",
        "brand_tone",
    }
    assert set(payload["autonomy"]) >= {
        "approval_gates",
        "mode_overrides",
        "auto_proceed_with_warnings",
        "learn_from_overrides",
        "auto_reprocess_on_edit",
        "allow_explicit_reassess",
        "auto_reprocess_stages",
        "min_proceed_confidence",
        "min_draft_confidence",
    }


def test_settings_router_autonomy_update_returns_frontend_settings_shape(session_client):
    response = session_client.post(
        "/api/settings/autonomy",
        json={"allow_explicit_reassess": False, "approval_gates": {"DRAFT": "auto"}},
    )
    payload = response.json()

    assert response.status_code == 200
    assert set(payload) >= {"agency_id", "seasonal", "profile", "operational", "autonomy"}
    assert set(payload["autonomy"]) >= {
        "approval_gates",
        "mode_overrides",
        "auto_proceed_with_warnings",
        "learn_from_overrides",
        "auto_reprocess_on_edit",
        "allow_explicit_reassess",
        "auto_reprocess_stages",
        "min_proceed_confidence",
        "min_draft_confidence",
    }


def test_settings_router_rejects_invalid_autonomy_action(session_client):
    response = session_client.post(
        "/api/settings/autonomy",
        json={"approval_gates": {"STOP_NEEDS_REVIEW": "auto"}},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["detail"] == "Safety invariant: STOP_NEEDS_REVIEW must always be 'block'"

    post_reject_response = session_client.get("/api/settings/autonomy")
    assert post_reject_response.status_code == 200
    post_payload = post_reject_response.json()
    assert post_payload["approval_gates"]["STOP_NEEDS_REVIEW"] == "block"


def test_settings_router_rejects_unknown_autonomy_action_type(session_client):
    response = session_client.post(
        "/api/settings/autonomy",
        json={"approval_gates": {"DRAFT": "escalate"}},
    )

    assert response.status_code == 400
    payload = response.json()
    assert "Invalid action 'escalate' for state 'DRAFT'. Must be auto|review|block." in payload["detail"]


def test_settings_router_seasonal_update_returns_frontend_settings_shape(session_client):
    response = session_client.put(
        "/api/settings/seasonal",
        json={"quarterly_recalibration_enabled": False},
    )
    payload = response.json()

    assert response.status_code == 200
    assert set(payload) >= {"agency_id", "seasonal", "profile", "operational", "autonomy"}
    assert set(payload["seasonal"]) >= {
        "active_seasons_enabled",
        "default_quarter_window_months",
        "channel_mix",
        "weather_risk_threshold",
        "budget_guardrail_multiplier",
        "micro_seasonality_window_days",
        "quarterly_recalibration_enabled",
        "prelaunch_blocklist",
    }


def test_settings_router_seasonal_campaign_crud_returns_canonical_shapes(session_client):
    create_response = session_client.post(
        "/api/settings/seasonal/campaigns",
        json={"name": "Regression Campaign"},
    )
    assert create_response.status_code == 200
    created = create_response.json()

    assert created["plan_id"]
    assert created["name"] == "Regression Campaign"
    assert created["status"] == "draft"
    assert set(created) >= {
        "plan_id",
        "name",
        "status",
        "channel_mix",
        "blocklist",
    }

    plan_id = created["plan_id"]

    list_response = session_client.get("/api/settings/seasonal/campaigns")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert isinstance(list_payload["items"], list)
    assert isinstance(list_payload["total"], int)
    assert any(item["plan_id"] == plan_id for item in list_payload["items"])

    get_response = session_client.get(f"/api/settings/seasonal/campaigns/{plan_id}")
    assert get_response.status_code == 200
    assert get_response.json()["plan_id"] == plan_id

    update_response = session_client.put(
        f"/api/settings/seasonal/campaigns/{plan_id}",
        json={"status": "active", "destination": "Barcelona"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["plan_id"] == plan_id
    assert updated["status"] == "active"
    assert updated["destination"] == "Barcelona"

    delete_response = session_client.delete(f"/api/settings/seasonal/campaigns/{plan_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"ok": True, "plan_id": plan_id}


def test_settings_router_seasonal_campaign_controls_return_canonical_shapes(session_client):
    create_response = session_client.post(
        "/api/settings/seasonal/campaigns",
        json={"name": "Campaign Controls Regression"},
    )
    assert create_response.status_code == 200
    created = create_response.json()
    plan_id = created["plan_id"]

    try:
        simulate_response = session_client.post(
            f"/api/settings/seasonal/campaigns/{plan_id}/simulate",
            json={"scenario": "baseline"},
        )
        assert simulate_response.status_code == 200
        simulate_payload = simulate_response.json()
        assert simulate_payload["plan_id"] == plan_id
        assert simulate_payload["scenario"] == "baseline"
        assert isinstance(simulate_payload["projected_leads"], int)
        assert isinstance(simulate_payload["projected_bookings"], int)
        assert isinstance(simulate_payload["projected_margin_pct"], (int, float))
        assert isinstance(simulate_payload["confidence"], (int, float))
        assert isinstance(simulate_payload["notes"], list)

        preflight_response = session_client.post(
            f"/api/settings/seasonal/campaigns/{plan_id}/preflight",
        )
        assert preflight_response.status_code == 200
        preflight_payload = preflight_response.json()
        assert preflight_payload["plan_id"] == plan_id
        assert isinstance(preflight_payload["ok"], bool)
        assert isinstance(preflight_payload["checks"], list)
        assert isinstance(preflight_payload["risk_score"], (int, float))
        assert preflight_payload["checks"]

        dispatch_response = session_client.post(
            f"/api/settings/seasonal/campaigns/{plan_id}/dispatch",
            json={"dry_run": False},
        )
        assert dispatch_response.status_code == 200
        dispatch_payload = dispatch_response.json()
        assert dispatch_payload["plan_id"] == plan_id
        assert dispatch_payload["ok"] is True
        assert dispatch_payload["dry_run"] is False
        assert isinstance(dispatch_payload["dispatched_channels"], list)
    finally:
        session_client.delete(f"/api/settings/seasonal/campaigns/{plan_id}")
