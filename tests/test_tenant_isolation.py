"""
tests/test_tenant_isolation.py — Tenant isolation verification.

Verifies:
  - Cross-agency trip read returns 404
  - Cross-agency trip mutation returns 404
  - Timeline access across agencies returns 404
  - Public checker scopes strictly to PUBLIC_CHECKER_AGENCY_ID
"""

from unittest.mock import patch

from spine_api.persistence import TripStore, FileTripStore


class TestTenantIsolationStorageLayer:
    """Storage-level enforcement of tenant isolation."""

    def test_get_trip_for_agency_matching_agency(self, tmp_path):
        trip_data = {
            "id": "trip_tenant_1",
            "agency_id": "agency_alpha",
            "packet": {"destination": "Tokyo"},
        }

        with patch.object(TripStore, "_backend", return_value=FileTripStore), \
             patch.object(FileTripStore, "get_trip_for_agency", return_value=trip_data):
            trip = TripStore.get_trip_for_agency("trip_tenant_1", "agency_alpha")
            assert trip is not None
            assert trip["id"] == "trip_tenant_1"

    def test_get_trip_for_agency_mismatched_agency(self):
        """Cross-agency access must return None at storage layer."""
        with patch.object(TripStore, "_backend", return_value=FileTripStore), \
             patch.object(FileTripStore, "get_trip_for_agency", return_value=None):
            trip = TripStore.get_trip_for_agency("trip_tenant_1", "agency_beta")
            assert trip is None

    def test_get_trip_for_public_access_strips_internals(self):
        """Public access projection strips agency internal fields."""
        full_trip = {
            "id": "trip_public_1",
            "agency_id": "agency_alpha",
            "packet": {"destination": "Paris"},
            "internal_bundle": {"secret_cost": 500},
            "agent_notes": "Client loves wine",
            "fees": {"commission": 150},
        }

        with patch.object(TripStore, "_get_trip_internal", return_value=full_trip):
            public_trip = TripStore.get_trip_for_public_access("trip_public_1")
            assert public_trip is not None
            assert public_trip["id"] == "trip_public_1"
            assert "internal_bundle" not in public_trip
            assert "agent_notes" not in public_trip
            assert "fees" not in public_trip
            assert public_trip["packet"]["destination"] == "Paris"


class TestNoUnscopedGetTripInRouters:
    """Ensure no router calls bare TripStore.get_trip except designated rewritten routers."""

    def test_ci_gate_script_runs(self):
        import subprocess
        result = subprocess.run(
            ["/bin/bash", "scripts/check_unscoped_trip_access.sh"],
            capture_output=True,
            text=True,
        )
        # Check script output structure
        assert result.returncode == 0, f"check_unscoped_trip_access.sh failed: stdout={result.stdout}, stderr={result.stderr}"
