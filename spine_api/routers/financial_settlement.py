"""
Financial settlement calculation-preview API (PER-FIN, FIN-01..12).

The local implementation can calculate illustrative FX, fee, schedule, and
commission values. It has no payment, treasury, card-issuing, or supplier
provider connected, so every response is explicitly non-operative.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel

from spine_api.core.reality_tier import RealityTier, TierMetadata
from src.fees.settlement_engine import FinancialSettlementEngine

router = APIRouter(prefix="/api/v1/settlement", tags=["settlement"])

_SETTLEMENT_PREVIEW_MISSING = [
    "authenticated market-data or treasury provider",
    "payment/card-issuing provider and authorization scope",
    "external reference and reconciliation contract",
    "quote, schedule, refund, and failure/expiry policy",
]


def _preview_metadata(feature_name: str, *, data_sufficient: bool = True) -> Dict[str, Any]:
    """Return canonical provenance and non-operative flags for a preview."""
    metadata = TierMetadata.for_response(
        RealityTier.DETERMINISTIC_PREVIEW,
        feature_name,
        data_sufficient=data_sufficient,
        computation_method="local deterministic settlement arithmetic; no provider call or financial write",
        missing_for_upgrade=_SETTLEMENT_PREVIEW_MISSING,
    )
    metadata.update(
        {
            "source": "local_deterministic_preview",
            "simulation": True,
            "provider_connected": False,
            "external_reference": None,
            "external_action": False,
            "operational_write": False,
            "effects": [],
        }
    )
    return metadata


def _preview_envelope(
    *,
    feature_name: str,
    status: str,
    payload: Dict[str, Any],
    data_sufficient: bool = True,
) -> Dict[str, Any]:
    """Attach the common result contract without changing useful calculations."""
    return {
        **payload,
        "status": status,
        "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
        "provider_connected": False,
        "external_reference": None,
        "effects": [],
        "metadata": _preview_metadata(feature_name, data_sufficient=data_sufficient),
    }


class FXQuoteRequest(BaseModel):
    base_amount: float
    from_currency: str = "USD"
    to_currency: str = "EUR"
    raw_exchange_rate: float = 0.92
    volatility_buffer_pct: float = 2.0
    interchange_pct: float = 2.9
    interchange_fixed: float = 0.30


class IssueVCCRequest(BaseModel):
    trip_id: str
    supplier_name: str
    authorized_amount: float
    currency: str = "EUR"
    validity_days: int = 7


class PaymentScheduleRequest(BaseModel):
    total_amount: float
    currency: str = "USD"
    departure_date: date
    deposit_pct: float = 20.0
    balance_due_days_prior: int = 45


class CommissionSplitRequest(BaseModel):
    gross_commission: float
    contractor_split_pct: float = 70.0


@router.post("/fx/calculate-quote")
def calculate_fx_quote(payload: FXQuoteRequest) -> Dict[str, Any]:
    """Calculate a customer-quote preview without issuing a quote or charge."""
    result = FinancialSettlementEngine.calculate_fx_quote(
            base_amount=payload.base_amount,
            from_currency=payload.from_currency,
            to_currency=payload.to_currency,
            raw_exchange_rate=payload.raw_exchange_rate,
            volatility_buffer_pct=payload.volatility_buffer_pct,
            interchange_pct=payload.interchange_pct,
            interchange_fixed=payload.interchange_fixed,
    )
    return _preview_envelope(
        feature_name="settlement_fx_quote",
        status="COMPUTED_PREVIEW",
        payload=result,
    )


@router.post("/vcc/issue")
def issue_virtual_credit_card(payload: IssueVCCRequest) -> Dict[str, Any]:
    """Return an issuance preview; never create or expose card credentials."""
    return _preview_envelope(
        feature_name="settlement_vcc_issuance",
        status="PREVIEW_ONLY",
        payload={
            "issuance_status": "NOT_ISSUED",
            "virtual_card": None,
            "requested_trip_id": payload.trip_id,
            "requested_supplier": payload.supplier_name,
            "requested_amount": payload.authorized_amount,
            "requested_currency": payload.currency.upper(),
            "requested_validity_days": payload.validity_days,
            "notice": "No card credential, authorization, provider call, or supplier payment was created.",
        },
    )


@router.post("/schedules/build")
def build_payment_schedule(payload: PaymentScheduleRequest) -> Dict[str, Any]:
    """Calculate illustrative payment timing without scheduling an invoice or charge."""
    schedule = FinancialSettlementEngine.build_payment_schedule(
        total_amount=payload.total_amount,
        currency=payload.currency,
        departure_date=payload.departure_date,
        deposit_pct=payload.deposit_pct,
        balance_due_days_prior=payload.balance_due_days_prior,
    )
    return _preview_envelope(
        feature_name="settlement_payment_schedule",
        status="COMPUTED_PREVIEW",
        payload={"milestones": [
            {
                "name": m.milestone_name,
                "percentage": m.percentage,
                "amount": m.amount,
                "currency": m.currency,
                "due_date": m.due_date,
            }
            for m in schedule
        ]},
    )


@router.post("/commission/split")
def calculate_commission_split(payload: CommissionSplitRequest) -> Dict[str, Any]:
    """Calculate an illustrative commission split; no funds are transferred."""
    result = FinancialSettlementEngine.calculate_commission_split(
            gross_commission=payload.gross_commission,
            contractor_split_pct=payload.contractor_split_pct,
    )
    return _preview_envelope(
        feature_name="settlement_commission_split",
        status="COMPUTED_PREVIEW",
        payload=result,
    )
