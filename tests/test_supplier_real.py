"""
tests/test_supplier_real.py — Tests for supplier contract ingestion and inventory holds.

Verifies:
  - Contract upload creates agency-scoped contract
  - Hold against non-existent contract returns 404
  - Hold against unknown room type returns 400
  - Soft hold computes real net/rack total and margin
"""

import pytest
from fastapi import HTTPException

from spine_api.routers.supplier import (
    ContractUploadRequest,
    RateTableItem,
    SoftHoldRequest,
    upload_supplier_contract,
    create_inventory_soft_hold,
    CONTRACTS_STORE,
    HOLDS_STORE,
)


@pytest.mark.asyncio
class TestSupplierManagement:
    """Test supplier contract ingestion and holds."""

    def setup_method(self):
        CONTRACTS_STORE.clear()
        HOLDS_STORE.clear()

    async def test_upload_supplier_contract(self):
        req = ContractUploadRequest(
            supplier_name="Kyoto Luxury DMC",
            destination="Kyoto, Japan",
            rate_table=[
                RateTableItem(
                    room_type="Garden Villa",
                    net_rate_per_night=400.0,
                    rack_rate_per_night=650.0,
                )
            ],
        )
        res = await upload_supplier_contract(req, agency_id="agency_1")
        assert res.contract_id.startswith("contract_")
        assert res.supplier_name == "Kyoto Luxury DMC"
        assert res.total_rates_ingested == 1

    async def test_soft_hold_unknown_contract_returns_404(self):
        req = SoftHoldRequest(
            contract_id="contract_nonexistent",
            room_type="Garden Villa",
            check_in="2026-10-01",
            check_out="2026-10-05",
            guest_name="Taro Yamada",
        )
        with pytest.raises(HTTPException) as exc_info:
            await create_inventory_soft_hold(req, agency_id="agency_1")
        assert exc_info.value.status_code == 404

    async def test_soft_hold_unknown_room_type_returns_400(self):
        # Upload contract first
        upload_req = ContractUploadRequest(
            supplier_name="Kyoto Luxury DMC",
            destination="Kyoto, Japan",
            rate_table=[
                RateTableItem(
                    room_type="Garden Villa",
                    net_rate_per_night=400.0,
                    rack_rate_per_night=650.0,
                )
            ],
        )
        upload_res = await upload_supplier_contract(upload_req, agency_id="agency_1")

        hold_req = SoftHoldRequest(
            contract_id=upload_res.contract_id,
            room_type="Presidential Suite",  # Not in rate table
            check_in="2026-10-01",
            check_out="2026-10-05",
            guest_name="Taro Yamada",
        )
        with pytest.raises(HTTPException) as exc_info:
            await create_inventory_soft_hold(hold_req, agency_id="agency_1")
        assert exc_info.value.status_code == 400

    async def test_soft_hold_computes_real_margin(self):
        upload_req = ContractUploadRequest(
            supplier_name="Kyoto Luxury DMC",
            destination="Kyoto, Japan",
            rate_table=[
                RateTableItem(
                    room_type="Garden Villa",
                    net_rate_per_night=400.0,
                    rack_rate_per_night=650.0,
                )
            ],
        )
        upload_res = await upload_supplier_contract(upload_req, agency_id="agency_1")

        hold_req = SoftHoldRequest(
            contract_id=upload_res.contract_id,
            room_type="Garden Villa",
            check_in="2026-10-01",
            check_out="2026-10-05",  # 4 nights
            guest_name="Taro Yamada",
        )
        hold_res = await create_inventory_soft_hold(hold_req, agency_id="agency_1")

        assert hold_res.net_rate_total == 1600.0  # 400 * 4
        assert hold_res.rack_rate_total == 2600.0  # 650 * 4
        assert hold_res.estimated_agency_margin == 1000.0  # 2600 - 1600
        assert hold_res.status == "SOFT_HOLD_ACTIVE"
