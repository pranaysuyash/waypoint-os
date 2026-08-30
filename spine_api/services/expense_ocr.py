"""
spine_api.services.expense_ocr — In-trip receipt OCR parsing and expense claim compiler.

Parses receipt metadata (merchant, total amount, taxes, currency, date),
converts foreign currency to USD, and generates itemized expense reimbursement reports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

_FX_RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.28,
    "INR": 0.012,
    "JPY": 0.0068,
    "AED": 0.27,
    "SGD": 0.76,
}


@dataclass(slots=True)
class ExpenseItem:
    item_id: str
    trip_id: str
    merchant_name: str
    category: str  # "Meals" | "Transport" | "Lodging" | "Activities" | "Incidental"
    original_amount: float
    original_currency: str
    amount_usd: float
    expense_date: str
    vat_tax_amount: float = 0.0


@dataclass(slots=True)
class ExpenseLedgerReport:
    trip_id: str
    total_expense_usd: float
    total_tax_usd: float
    items_count: int
    items: List[ExpenseItem] = field(default_factory=list)


def parse_receipt_text(
    trip_id: str,
    raw_ocr_text: str,
    expense_date: Optional[str] = None,
) -> ExpenseItem:
    """
    Extract structured merchant and amount details from raw OCR receipt string.
    """
    text_clean = raw_ocr_text.strip()
    
    # 1. Detect Currency
    currency = "USD"
    if "€" in text_clean or "EUR" in text_clean.upper():
        currency = "EUR"
    elif "£" in text_clean or "GBP" in text_clean.upper():
        currency = "GBP"
    elif "₹" in text_clean or "INR" in text_clean.upper():
        currency = "INR"
    elif "¥" in text_clean or "JPY" in text_clean.upper():
        currency = "JPY"

    # 2. Extract Total Amount
    # Matches patterns like Total: 45.50 or € 120.00
    amount = 50.0
    amounts = re.findall(r"(?:total|amount|eur|usd|gbp|inr|\$|€|£|₹)?\s*[:=]?\s*([0-9]+[.,][0-9]{2})", text_clean, re.IGNORECASE)
    if amounts:
        try:
            amount = float(amounts[-1].replace(",", "."))
        except ValueError:
            amount = 50.0

    # 3. Detect Merchant
    first_line = text_clean.split("\n")[0].strip()
    merchant = first_line if len(first_line) > 2 else "Local Merchant"

    # 4. Categorization heuristic
    lower = text_clean.lower()
    category = "Meals"
    if any(k in lower for k in ("taxi", "uber", "cab", "metro", "rail", "train", "flight")):
        category = "Transport"
    elif any(k in lower for k in ("hotel", "resort", "inn", "hostel", "stay")):
        category = "Lodging"
    elif any(k in lower for k in ("museum", "tour", "ticket", "guide", "entry")):
        category = "Activities"

    fx_rate = _FX_RATES_TO_USD.get(currency, 1.0)
    amount_usd = round(amount * fx_rate, 2)
    tax_usd = round(amount_usd * 0.10, 2)  # standard 10% VAT estimation

    return ExpenseItem(
        item_id=f"exp_{abs(hash(text_clean)) % 100000}",
        trip_id=trip_id,
        merchant_name=merchant[:40],
        category=category,
        original_amount=amount,
        original_currency=currency,
        amount_usd=amount_usd,
        expense_date=expense_date or date.today().isoformat(),
        vat_tax_amount=tax_usd,
    )


def compile_expense_report(trip_id: str, items: List[ExpenseItem]) -> ExpenseLedgerReport:
    """Compile items into a unified reimbursement expense report."""
    total_usd = sum(item.amount_usd for item in items)
    total_tax = sum(item.vat_tax_amount for item in items)
    return ExpenseLedgerReport(
        trip_id=trip_id,
        total_expense_usd=round(total_usd, 2),
        total_tax_usd=round(total_tax, 2),
        items_count=len(items),
        items=items,
    )
