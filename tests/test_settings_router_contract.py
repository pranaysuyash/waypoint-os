from __future__ import annotations


def test_settings_router_returns_frontend_consumed_settings_shape(session_client):
    response = session_client.get("/api/settings")

    assert response.status_code == 200
    payload = response.json()

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
