"""WOBS 2026-09-09 P3 — re-verification endpoint + report fingerprint.

Re-verify is read-only (never mutates the stored trip), fail-open on provider
outage, kill-switched, and bounded to consented-derivable data (packet only).
The report fingerprint is a deterministic findings-only sha256 seed for
Verify-as-API — same findings ⇒ same fingerprint.
"""

from __future__ import annotations

import pytest

from spine_api.services.public_checker_service import compute_report_fingerprint


class TestReportFingerprint:
    def test_deterministic(self):
        a = compute_report_fingerprint({"overall_score": 61}, {"hard_blockers": ["x"]})
        b = compute_report_fingerprint({"overall_score": 61}, {"hard_blockers": ["x"]})
        assert a == b
        assert a.startswith("fp_")

    def test_changes_when_findings_change(self):
        a = compute_report_fingerprint({"overall_score": 61}, {"hard_blockers": ["x"]})
        b = compute_report_fingerprint({"overall_score": 61}, {"hard_blockers": ["y"]})
        assert a != b

    def test_key_order_irrelevant(self):
        a = compute_report_fingerprint(
            {"overall_score": 61, "other": 1}, {"hard_blockers": ["x"], "soft_blockers": ["y"]}
        )
        b = compute_report_fingerprint(
            {"other": 1, "overall_score": 61}, {"soft_blockers": ["y"], "hard_blockers": ["x"]}
        )
        assert a == b

    def test_free_text_not_in_payload(self):
        """Consent-dependent raw inputs are excluded — fingerprint is shareable."""
        fp = compute_report_fingerprint({"overall_score": 61, "raw": "secret"}, {})
        assert "secret" not in fp


@pytest.fixture()
def stored_trip(monkeypatch: pytest.MonkeyPatch):
    trip = {
        "id": "trip_revtest01",
        "source": "public_checker",
        "packet": {"resolved_destination": "Kerala", "quality_score": 70},
        "validation": {"overall_score": 61},
        "decision": {"hard_blockers": ["visa"], "soft_blockers": []},
    }
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-x")
    from spine_api import persistence as persistence_module

    monkeypatch.setattr(
        persistence_module.TripStore,
        "get_trip_for_agency",
        classmethod(lambda cls, trip_id_arg, agency_id: dict(trip) if trip_id_arg == trip["id"] else None),
    )
    return trip


def test_reverify_returns_fresh_signals(session_client, monkeypatch, stored_trip):
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    import spine_api.routers.public_checker as router_module

    fresh_live = {
        "destination": "Kerala",
        "score_penalty": 10,
        "hard_blockers": [],
        "soft_blockers": ["monsoon window"],
    }
    monkeypatch.setattr(
        router_module, "build_live_checker_signals", lambda packet, text: dict(fresh_live)
    )
    monkeypatch.setattr(
        router_module,
        "run_entity_checks",
        lambda text, city=None, max_entities=3: [
            type("R", (), {"as_dict": lambda self: {"name": "X", "status": "not_found"}})()
        ],
    )

    resp = session_client.post("/api/public-checker/re-verify", json={"trip_id": "trip_revtest01"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["refreshed"] is True
    assert payload["overall_score_preview"] == 51  # 61 - 10 penalty
    assert payload["entity_checks"][0]["status"] == "not_found"
    assert "checked_at" in payload


def test_reverify_fail_open_on_provider_outage(session_client, monkeypatch, stored_trip):
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    import spine_api.routers.public_checker as router_module

    def boom(packet, text):
        raise OSError("provider down")

    monkeypatch.setattr(router_module, "build_live_checker_signals", boom)
    monkeypatch.setattr(
        router_module,
        "run_entity_checks",
        lambda text, city=None, max_entities=3: [],
    )

    resp = session_client.post("/api/public-checker/re-verify", json={"trip_id": "trip_revtest01"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["refreshed"] is True
    assert payload["live_checks"] is None
    assert payload["overall_score_preview"] == 61  # stored score, unchanged


def test_reverify_unknown_trip_404(session_client, monkeypatch):
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-x")
    resp = session_client.post("/api/public-checker/re-verify", json={"trip_id": "trip_missing"})
    assert resp.status_code == 404


def test_reverify_kill_switch(session_client, monkeypatch):
    monkeypatch.setenv("PUBLIC_CHECKER_ENABLED", "0")
    resp = session_client.post("/api/public-checker/re-verify", json={"trip_id": "trip_x"})
    assert resp.status_code == 503
