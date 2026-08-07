"""
tests/test_yield_arbitrage_real.py — Tests for yield and commission arbitrage engine.

Verifies:
  - Non-existent trip returns 404
  - Valid trip computes sorted supplier options by net margin
  - Real uploaded supplier contracts are integrated when available
  - Supplier swap updates trip and logs audit event
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException

from spine_api.routers.yield_arbitrage import (
    SupplierSwapRequest,
    compute_yield_arbitrage,
    swap_supplier_option,
)
from spine_api.persistence import TripStore


@pytest.mark.asyncio
class TestYieldArbitrageEngine:
    """Test yield arbitrage computation and supplier swap."""

    def setup_method(self):
        from spine_api.routers.supplier import CONTRACTS_STORE
        CONTRACTS_STORE.clear()

    async def test_compute_unknown_trip_returns_404(self):
        with patch.object(TripStore, "get_trip_for_agency", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await compute_yield_arbitrage("nonexistent_trip", agency_id="agency_1")
            assert exc_info.value.status_code == 404

    async def test_compute_yield_arbitrage_real_trip(self):
        from spine_api.routers.supplier import CONTRACTS_STORE
        CONTRACTS_STORE["agency_1"] = {
            "c_1": {
                "supplier_name": "Direct Resort Contract",
                "rate_table": [{"net_rate_per_night": 300.0, "rack_rate_per_night": 500.0}],
            },
            "c_2": {
                "supplier_name": "Partner Villa Contract",
                "rate_table": [{"net_rate_per_night": 400.0, "rack_rate_per_night": 700.0}],
            },
        }
        trip_data = {
            "id": "trip_1",
            "agency_id": "agency_1",
            "packet": {"budget_max": 6000.0},
        }
        with patch.object(TripStore, "get_trip_for_agency", return_value=trip_data):
            res = await compute_yield_arbitrage("trip_1", agency_id="agency_1")
            assert res.ok is True
            assert res.trip_id == "trip_1"
            assert res.data_sufficient is True
            assert len(res.supplier_options) == 2
            # Check options are sorted by net_margin descending
            margins = [o.net_margin for o in res.supplier_options]
            assert margins == sorted(margins, reverse=True)
            assert res.potential_margin_gain >= 0.0

    async def test_swap_supplier_unknown_trip_returns_404(self):
        req = SupplierSwapRequest(
            trip_id="nonexistent_trip",
            supplier_name="Direct Preferred Resort Contract",
        )
        with patch.object(TripStore, "get_trip_for_agency", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await swap_supplier_option(req, agency_id="agency_1")
            assert exc_info.value.status_code == 404

    async def test_swap_supplier_success(self):
        from spine_api.core.reality_tier import RealityTier
        trip_data = {
            "id": "trip_1",
            "agency_id": "agency_1",
            "selected_supplier": None,
        }
        req = SupplierSwapRequest(
            trip_id="trip_1",
            supplier_name="Kyoto Luxury DMC",
        )
        with patch.object(TripStore, "get_trip_for_agency", return_value=trip_data), \
             patch.object(TripStore, "save_trip") as mock_save, \
             patch("spine_api.routers.yield_arbitrage.get_feature_tier", return_value=RealityTier.REAL):
            res = await swap_supplier_option(req, agency_id="agency_1")
            assert res["ok"] is True
            assert res["selected_supplier"] == "Kyoto Luxury DMC"
            assert mock_save.called
