"""
Travel Financial Settlement & Virtual Card Engine (PER-FIN, FIN-01..12).

Manages FX volatility slippage buffers, payment gateway interchange deduction,
supplier-native virtual credit card (VCC) generation, staged deposit/balance schedules,
and sub-agent commission split calculations.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List


@dataclass(slots=True)
class VirtualCreditCard:
    """Single-use merchant-bound virtual card in supplier native currency."""
    card_id: str
    trip_id: str
    supplier_name: str
    currency: str
    authorized_amount: float
    card_number_masked: str
    expiration_month: int
    expiration_year: int
    cvv: str
    valid_from: str
    valid_until: str
    status: str = "ACTIVE"  # ACTIVE | SETTLED | EXPIRED | CANCELLED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "trip_id": self.trip_id,
            "supplier_name": self.supplier_name,
            "currency": self.currency,
            "authorized_amount": self.authorized_amount,
            "card_number_masked": self.card_number_masked,
            "expiration_month": self.expiration_month,
            "expiration_year": self.expiration_year,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "status": self.status,
        }


@dataclass(slots=True)
class PaymentMilestone:
    """Staged payment milestone (e.g. deposit vs final balance)."""
    milestone_name: str
    percentage: float
    amount: float
    currency: str
    due_date: str
    is_paid: bool = False


class FinancialSettlementEngine:
    """Travel Financial Settlement, FX Buffer & Virtual Card Manager."""

    @staticmethod
    def calculate_fx_quote(
        base_amount: float,
        from_currency: str,
        to_currency: str,
        raw_exchange_rate: float,
        volatility_buffer_pct: float = 2.0,  # 2.0% buffer
        interchange_pct: float = 2.9,        # Stripe standard 2.9%
        interchange_fixed: float = 0.30,
    ) -> Dict[str, Any]:
        """
        Calculates quote with FX volatility buffer and gateway processing deductions.
        Protects agency margins against currency swings during confirmation windows.
        """
        # Convert base amount to target currency
        converted_raw = base_amount * raw_exchange_rate
        # Add FX volatility cushion
        buffered_rate = raw_exchange_rate * (1.0 + (volatility_buffer_pct / 100.0))
        customer_quoted_total = round(base_amount * buffered_rate, 2)

        # Calculate interchange fee
        gateway_fee = round((customer_quoted_total * (interchange_pct / 100.0)) + interchange_fixed, 2)
        net_settled_amount = round(customer_quoted_total - gateway_fee, 2)

        return {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "raw_exchange_rate": raw_exchange_rate,
            "buffered_exchange_rate": round(buffered_rate, 4),
            "volatility_buffer_pct": volatility_buffer_pct,
            "base_amount": base_amount,
            "customer_quoted_total": customer_quoted_total,
            "estimated_gateway_fee": gateway_fee,
            "net_settled_amount": net_settled_amount,
            "fx_cushion_amount": round(customer_quoted_total - converted_raw, 2),
        }

    @staticmethod
    def issue_supplier_vcc(
        trip_id: str,
        supplier_name: str,
        authorized_amount: float,
        currency: str = "EUR",
        validity_days: int = 7,
    ) -> VirtualCreditCard:
        """Issues a single-use virtual Mastercard in supplier native currency."""
        seed = f"{trip_id}:{supplier_name}:{authorized_amount}:{datetime.now(timezone.utc).isoformat()}"
        h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        card_id = f"VCC-{h[:8].upper()}"
        last_four = h[8:12]
        masked_number = f"5424-XXXX-XXXX-{last_four}"

        now = datetime.now(timezone.utc)
        valid_from = now.strftime("%Y-%m-%d")
        valid_until = (now + timedelta(days=validity_days)).strftime("%Y-%m-%d")

        return VirtualCreditCard(
            card_id=card_id,
            trip_id=trip_id,
            supplier_name=supplier_name,
            currency=currency.upper(),
            authorized_amount=authorized_amount,
            card_number_masked=masked_number,
            expiration_month=((now.month + 6) % 12) + 1,
            expiration_year=now.year + 1,
            cvv=h[12:15],
            valid_from=valid_from,
            valid_until=valid_until,
            status="ACTIVE",
        )

    @staticmethod
    def build_payment_schedule(
        total_amount: float,
        currency: str,
        departure_date: date,
        deposit_pct: float = 20.0,
        balance_due_days_prior: int = 45,
    ) -> List[PaymentMilestone]:
        """Generates staged deposit and balance payment milestones."""
        deposit_amount = round(total_amount * (deposit_pct / 100.0), 2)
        balance_amount = round(total_amount - deposit_amount, 2)

        deposit_due = date.today().isoformat()
        balance_due = max(date.today(), departure_date - timedelta(days=balance_due_days_prior)).isoformat()

        return [
            PaymentMilestone(
                milestone_name="Initial Booking Deposit",
                percentage=deposit_pct,
                amount=deposit_amount,
                currency=currency.upper(),
                due_date=deposit_due,
            ),
            PaymentMilestone(
                milestone_name="Final Balance Payment",
                percentage=round(100.0 - deposit_pct, 1),
                amount=balance_amount,
                currency=currency.upper(),
                due_date=balance_due,
            ),
        ]

    @staticmethod
    def calculate_commission_split(
        gross_commission: float,
        contractor_split_pct: float = 70.0,
        host_agency_split_pct: float = 30.0,
    ) -> Dict[str, Any]:
        """Calculates split between independent contractor travel advisor and host agency."""
        contractor_payout = round(gross_commission * (contractor_split_pct / 100.0), 2)
        host_payout = round(gross_commission - contractor_payout, 2)

        return {
            "gross_commission": gross_commission,
            "contractor_split_pct": contractor_split_pct,
            "host_agency_split_pct": host_agency_split_pct,
            "contractor_payout": contractor_payout,
            "host_agency_payout": host_payout,
        }
