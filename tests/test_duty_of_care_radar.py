"""
Enterprise Duty-of-Care Radar Tests (PER-DUTY-SYNC).
"""

from src.orchestration.duty_of_care_radar import DutyOfCareRadarEngine


def test_duty_of_care_cockpit_compilation():
    cockpit = DutyOfCareRadarEngine.compile_live_cockpit(agency_id="AGENCY-GLOBAL-99")

    assert cockpit.cockpit_id == "DOCKPIT-L-99"
    assert len(cockpit.active_threat_incidents) == 1
    assert cockpit.total_travelers_in_geofences == 2
    assert cockpit.accounted_travelers_count == 1
    assert cockpit.unaccounted_travelers_count == 1
    assert cockpit.step_consular_manifests_compiled >= 1
    assert cockpit.ground_dispatches_active == 1
    assert "URGENT WAYPOINT OS ADVISORY" in cockpit.sos_broadcast_payload
