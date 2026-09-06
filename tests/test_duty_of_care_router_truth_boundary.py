"""The duty-of-care cockpit must remain a local, non-operative preview."""

from spine_api.routers.duty_of_care_radar import (
    CockpitSummaryRequest,
    get_duty_of_care_summary,
)


def test_cockpit_summary_is_preview_only_and_non_operational() -> None:
    response = get_duty_of_care_summary(CockpitSummaryRequest(agency_id="AGENCY-TEST-01"))

    assert response["status"] == "PREVIEW_ONLY"
    assert response["reality"]["reality_tier"] == "deterministic_preview"
    assert response["reality"]["provider_connected"] is False
    assert response["reality"]["external_reference"] is None
    assert response["reality"]["effects"] == []

    cockpit = response["cockpit"]
    assert cockpit["evidence_status"] == "UNVERIFIED_LOCAL_FIXTURES"
    assert cockpit["step_consular_manifests_status"] == "DRAFT_NOT_SUBMITTED"
    assert cockpit["ground_dispatch_status"] == "FIXTURE_NOT_DISPATCHED"
    assert cockpit["sos_broadcast_status"] == "PAYLOAD_PREVIEW_NOT_SENT"
    assert "nothing was verified" in cockpit["operator_next_step"]
