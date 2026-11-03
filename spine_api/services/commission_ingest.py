"""Commission-statement ingest breadth (R2-B / Travefy bar, 2026-11-03).

Operators receive supplier commission statements as CSV exports, email
bodies, and screenshots. This service turns those into candidate commission
rows, fuzzy-matches them to agency trips (booking-ref exact → amount-tolerance
+ fuzzy supplier), and returns manual-link candidates for the rest.

Honesty posture (ADR-008 / money-boundary doctrine):
- Ingest candidates are PREVIEW-grade working state (in-process batch store,
  ``durable=False``) until an operator records the payout through the durable
  ``AdvisorPayoutStore`` — a statement row is never silently treated as
  collected money.
- Image statements are accepted only as OCR text (the multimodal lane's
  ``/image-ocr`` contract); there is no in-process OCR engine, and one is
  never fabricated.
"""

from __future__ import annotations

import csv
import difflib
import io
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Sub-cent differences are not mismatches (same tolerance as reconciliation).
AMOUNT_TOLERANCE_RATIO = 0.02  # statements round; 2% of the row amount
FUZZY_SUPPLIER_THRESHOLD = 0.6

# Column-header aliases for CSV statements (first matching alias wins).
COLUMN_ALIASES = {
    "supplier": ("supplier", "supplier_name", "vendor", "partner", "hotel", "operator"),
    "booking_ref": ("booking_ref", "booking_reference", "reference", "ref", "confirmation", "locator", "booking_id"),
    "amount": ("amount", "commission", "payout", "net_amount", "total", "value"),
    "currency": ("currency", "ccy"),
    "date": ("date", "statement_date", "booking_date", "paid_at"),
}

_MONEY_RE = re.compile(r"(-?\d[\d,]*(?:\.\d{1,2})?)")
_REF_RE = re.compile(r"[A-Z0-9][A-Z0-9-]{4,}")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")


@dataclass(slots=True)
class StatementRow:
    """One ingested commission-statement line, with its match disposition."""

    row_index: int
    supplier_name: str
    booking_ref: str
    amount: Optional[float]
    currency: str
    date: str
    raw_text: str
    match_status: str = "unmatched"  # matched | manual_candidate | unmatched
    match_trip_id: Optional[str] = None
    match_method: Optional[str] = None  # booking_ref | amount_fuzzy_supplier
    match_confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IngestBatch:
    batch_id: str
    source_format: str  # csv | email | image_ocr
    source_label: str
    created_at: str
    agency_id: str
    durable: bool = False  # preview-grade until a payout is recorded durably
    rows: List[StatementRow] = field(default_factory=list)
    linked: Dict[int, str] = field(default_factory=dict)  # row_index -> trip_id (manual)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source_format": self.source_format,
            "source_label": self.source_label,
            "created_at": self.created_at,
            "agency_id": self.agency_id,
            "durable": self.durable,
            "row_count": len(self.rows),
            "matched_count": sum(1 for r in self.rows if r.match_status == "matched"),
            "manual_candidate_count": sum(1 for r in self.rows if r.match_status == "manual_candidate"),
            "unmatched_count": sum(1 for r in self.rows if r.match_status == "unmatched"),
            "rows": [r.to_dict() for r in self.rows],
            "linked": dict(self.linked),
        }


def _parse_amount(raw: str) -> Optional[float]:
    match = _MONEY_RE.search(raw)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _looks_like_header(line: str) -> bool:
    lowered = line.lower()
    return any(alias in lowered for pair in COLUMN_ALIASES.values() for alias in pair) and (
        "ref" in lowered or "amount" in lowered or "commission" in lowered or "supplier" in lowered
    )


def _row_from_parts(parts: List[str], row_index: int, raw_text: str) -> Optional[StatementRow]:
    supplier = booking_ref = currency = date = ""
    amount: Optional[float] = None
    for part in parts:
        token = str(part).strip()
        if not token:
            continue
        if amount is None and _MONEY_RE.search(token) and not _REF_RE.fullmatch(token):
            candidate = _parse_amount(token)
            if candidate is not None:
                amount = candidate
                if "," in token and len(token) <= 22:
                    # A currency code often rides along ("USD 1,240.50").
                    upper = token.upper()
                    for code in ("USD", "INR", "EUR", "GBP", "AED", "SGD"):
                        if code in upper:
                            currency = code
                            break
                continue
        if not booking_ref and _REF_RE.fullmatch(token):
            booking_ref = token
            continue
        if not date and _DATE_RE.fullmatch(token):
            date = token
            continue
        if not currency and token.upper() in {"USD", "INR", "EUR", "GBP", "AED", "SGD"}:
            currency = token.upper()
            continue
        if not supplier:
            supplier = token
    if amount is None and not booking_ref and not supplier:
        return None
    return StatementRow(
        row_index=row_index,
        supplier_name=supplier,
        booking_ref=booking_ref,
        amount=amount,
        currency=currency,
        date=date,
        raw_text=raw_text[:300],
    )


def parse_csv_statement(text: str) -> List[StatementRow]:
    """Parse a CSV commission statement (header row optional)."""
    reader = csv.reader(io.StringIO(text))
    rows: List[StatementRow] = []
    index = 0
    for parts in reader:
        if not parts or not [p for p in parts if str(p).strip()]:
            continue
        joined = ",".join(parts)
        if _looks_like_header(joined):
            continue
        row = _row_from_parts(parts, index, joined)
        if row is not None:
            rows.append(row)
            index += 1
    return rows


def parse_line_statement(text: str, source_format: str) -> List[StatementRow]:
    """Parse email bodies / OCR text: one statement line per row.

    Deliberately deterministic (no LLM): supplier, booking reference, amount,
    and date are picked from whitespace-separated tokens. Lines without any
    recognizable token are skipped — a line that parses to nothing is never
    fabricated into a candidate.
    """
    rows: List[StatementRow] = []
    index = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or _looks_like_header(stripped):
            continue
        row = _row_from_parts(stripped.split(), index, stripped)
        if row is not None and (row.amount is not None or row.booking_ref):
            rows.append(row)
            index += 1
    return rows


def fuzzy_supplier_score(name_a: str, name_b: str) -> float:
    return difflib.SequenceMatcher(None, name_a.lower().strip(), name_b.lower().strip()).ratio()


def _trip_booking_facts(trip: Dict[str, Any]) -> List[Dict[str, Any]]:
    booking = trip.get("booking_confirmation") or {}
    if not isinstance(booking, dict):
        return []
    total = booking.get("total_charged_usd")
    if total is None:
        return []
    return [
        {
            "trip_id": trip.get("id"),
            "supplier_name": str(
                booking.get("supplier_name") or booking.get("supplier") or trip.get("destination") or ""
            ),
            "booking_ref": str(
                booking.get("booking_ref") or booking.get("record_locator") or booking.get("confirmation_code") or ""
            ),
            "amount": float(total),
        }
    ]


def match_rows(
    rows: List[StatementRow],
    trips: List[Dict[str, Any]],
    tolerance_ratio: float = AMOUNT_TOLERANCE_RATIO,
) -> None:
    """Assign match dispositions in place (booking-ref exact → amount+supplier fuzzy)."""
    candidates: List[Dict[str, Any]] = []
    for trip in trips:
        candidates.extend(_trip_booking_facts(trip))

    for row in rows:
        if row.amount is None and not row.booking_ref:
            row.match_status = "unmatched"
            continue

        # 1. Exact booking reference.
        if row.booking_ref:
            for cand in candidates:
                if cand["booking_ref"] and cand["booking_ref"].upper() == row.booking_ref.upper():
                    row.match_status = "matched"
                    row.match_trip_id = cand["trip_id"]
                    row.match_method = "booking_ref"
                    row.match_confidence = 0.95
                    break
        if row.match_status == "matched":
            continue

        # 2. Amount within tolerance + fuzzy supplier ≥ threshold.
        if row.amount is not None and row.supplier_name:
            best: Tuple[float, Optional[Dict[str, Any]]] = (0.0, None)
            for cand in candidates:
                if cand["amount"] <= 0:
                    continue
                delta = abs(cand["amount"] - row.amount)
                if delta > max(cand["amount"], row.amount) * tolerance_ratio:
                    continue
                score = fuzzy_supplier_score(row.supplier_name, cand["supplier_name"])
                if score > best[0]:
                    best = (score, cand)
            score, cand = best
            if cand is not None and score >= FUZZY_SUPPLIER_THRESHOLD:
                row.match_status = "matched"
                row.match_trip_id = cand["trip_id"]
                row.match_method = "amount_fuzzy_supplier"
                row.match_confidence = round(score, 3)
                continue

        # 3. Recognizable statement line without a trip match → manual link.
        row.match_status = "manual_candidate"


def create_ingest_batch(
    *,
    source_format: str,
    content: str,
    agency_id: str,
    trips: List[Dict[str, Any]],
    source_label: str = "",
) -> IngestBatch:
    """Parse, match, and register an ingest batch (in-process, preview-grade)."""
    if source_format == "csv":
        rows = parse_csv_statement(content)
    elif source_format in ("email", "image_ocr"):
        rows = parse_line_statement(content, source_format)
    else:
        raise ValueError(
            f"Unsupported statement format '{source_format}' (expected csv | email | image_ocr)"
        )
    match_rows(rows, trips)
    batch = IngestBatch(
        batch_id=f"ci_{uuid.uuid4().hex[:12]}",
        source_format=source_format,
        source_label=source_label or source_format,
        created_at=datetime.now(timezone.utc).isoformat(),
        agency_id=agency_id,
        rows=rows,
    )
    _INGEST_BATCHES[batch.batch_id] = batch
    return batch


# In-process working store: ingest candidates are preview-grade until an
# operator confirms a payout through the durable AdvisorPayoutStore. Money
# truth never lives here.
_INGEST_BATCHES: Dict[str, IngestBatch] = {}


def get_batch(batch_id: str, agency_id: str) -> Optional[IngestBatch]:
    batch = _INGEST_BATCHES.get(batch_id)
    if batch is None or batch.agency_id != agency_id:
        return None
    return batch


def link_row(batch_id: str, agency_id: str, row_index: int, trip_id: str) -> Optional[IngestBatch]:
    """Manual-link fallback (Travefy bar): operator asserts row↔trip."""
    batch = get_batch(batch_id, agency_id)
    if batch is None:
        return None
    if not (0 <= row_index < len(batch.rows)):
        raise ValueError(f"row_index {row_index} out of range (batch has {len(batch.rows)} rows)")
    batch.rows[row_index].match_status = "matched"
    batch.rows[row_index].match_trip_id = trip_id
    batch.rows[row_index].match_method = "manual_link"
    batch.rows[row_index].match_confidence = 1.0
    batch.linked[row_index] = trip_id
    return batch
