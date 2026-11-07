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
import json
import os
import re
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
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
    # Money-truth tracking: set when this row has been recorded through the
    # durable AdvisorPayoutStore (R2-B flow closure). One recording per row.
    recorded: bool = False
    recorded_payout_id: Optional[str] = None

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
                # Sim-pass money-safety fix (2026-11-07): a fuzzy match is a
                # SUGGESTION, never an auto-confirmation — difflib similarity
                # alone must not enable one-click recording of a durable
                # payout against a possibly-wrong trip. Downgrade to
                # manual_candidate with the suggestion attached; the operator
                # links (confirming) before Record unlocks.
                row.match_status = "manual_candidate"
                row.match_trip_id = None
                row.match_method = "fuzzy_suggestion"
                row.match_confidence = round(score, 3)
                row.raw_text = (
                    f"{row.raw_text} | suggested: {cand['trip_id']} "
                    f"({cand['supplier_name']}, {score:.0%})"
                )[:300]
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
    _save_batch(batch)
    return batch


# In-process working store: ingest candidates are preview-grade until an
# operator confirms a payout through the durable AdvisorPayoutStore. Money
# truth never lives here.
# FND-0404 (2026-11-07): batches persist to disk (JSON, one file per batch)
# so a backend restart or reload no longer orphans the operator's manual
# links mid-review. Money truth still only moves through the payout store.
_INGEST_BATCHES: Dict[str, IngestBatch] = {}


def batches_dir() -> Path:
    override = os.getenv("WAYPOINT_COMMISSION_BATCHES_DIR", "").strip()
    base = Path(override) if override else Path("data/commission_batches")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _save_batch(batch: IngestBatch) -> None:
    path = batches_dir() / f"{batch.batch_id}.json"
    path.write_text(json.dumps(batch.to_dict(), indent=2), encoding="utf-8")


def _load_batch(batch_id: str) -> Optional[IngestBatch]:
    path = batches_dir() / f"{batch_id}.json"
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = [StatementRow(**r) for r in raw.get("rows", [])]
        batch = IngestBatch(
            batch_id=raw["batch_id"],
            source_format=raw["source_format"],
            source_label=raw.get("source_label", ""),
            created_at=raw.get("created_at", ""),
            agency_id=raw.get("agency_id", ""),
            durable=False,
            rows=rows,
            linked={int(k): v for k, v in (raw.get("linked") or {}).items()},
        )
        return batch
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        # Corrupt/hand-edited batch file: skip it, never crash the read path.
        del exc
        return None


def list_batches(agency_id: str) -> List[Dict[str, Any]]:
    """Batch summaries for the agency, newest first (FND-0404 reopen UI)."""
    out: List[Dict[str, Any]] = []
    if not batches_dir().exists():
        return out
    for path in sorted(batches_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        batch = _load_batch(path.stem)
        if batch is None or batch.agency_id != agency_id:
            continue
        out.append({
            "batch_id": batch.batch_id,
            "source_format": batch.source_format,
            "source_label": batch.source_label,
            "created_at": batch.created_at,
            "row_count": len(batch.rows),
            "matched_count": sum(1 for r in batch.rows if r.match_status == "matched"),
            "manual_candidate_count": sum(1 for r in batch.rows if r.match_status == "manual_candidate"),
        })
    return out


def get_batch(batch_id: str, agency_id: str) -> Optional[IngestBatch]:
    batch = _INGEST_BATCHES.get(batch_id)
    if batch is None:
        batch = _load_batch(batch_id)
        if batch is not None:
            _INGEST_BATCHES[batch_id] = batch  # re-cache for fast mutation
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
    _save_batch(batch)
    return batch


def record_row_payout(
    batch_id: str,
    agency_id: str,
    row_index: int,
    *,
    advisor_id: str,
    recorded_by: str,
) -> Tuple[Optional["IngestBatch"], Optional[Dict[str, Any]], Optional[str]]:
    """Record a matched statement row as a DURABLE payout (R2-B flow closure).

    This is the only path from ingest candidates to money truth: the row must
    be matched, not previously recorded, and denominated in USD — the payout
    ledger stores ``amount_usd`` and this service never performs an FX
    conversion (a non-USD statement row is rejected with explicit guidance,
    never silently converted). On success the row is marked with the durable
    payout id; re-recording is rejected (idempotent against double-count).

    Returns (updated_batch, payout_record_dict, None) or
    (None, None, error_message).
    """
    from spine_api.services.advisor_payout_store import AdvisorPayoutStore

    batch = get_batch(batch_id, agency_id)
    if batch is None:
        return None, None, "Ingest batch not found"
    if not (0 <= row_index < len(batch.rows)):
        return None, None, f"row_index {row_index} out of range (batch has {len(batch.rows)} rows)"
    row = batch.rows[row_index]
    if row.recorded:
        return None, None, (
            f"Row {row_index} was already recorded (payout {row.recorded_payout_id}); "
            "recording it again would double-count the commission."
        )
    if row.match_status != "matched" or not row.match_trip_id:
        return None, None, (
            f"Row {row_index} is not matched to a trip — link it (manual-link "
            "fallback) before recording a payout."
        )
    if row.amount is None or row.amount <= 0:
        return None, None, f"Row {row_index} has no positive amount to record."
    currency = (row.currency or "USD").upper()
    if currency != "USD":
        return None, None, (
            f"Row {row_index} is denominated {currency}; the payout ledger stores "
            "USD and this service does not convert currencies. Convert at the "
            "prevailing rate and record through the payout endpoint with the "
            "USD amount and this statement reference in the note."
        )
    if not advisor_id.strip():
        return None, None, "advisor_id is required for payout attribution."

    # Contract-review R2 (2026-11-07): the row.recorded flag is process-local —
    # multi-worker or restart bypasses it, double-recording a durable payout.
    # Durable idempotency: a deterministic payout_id keyed to (batch, row).
    # record_payout stores it verbatim (memory PK / SQL PK), so any duplicate
    # — pre-check or insert conflict — resolves to the existing payout.
    payout_id = f"stmt-{batch.batch_id}-{row_index}"
    existing = AdvisorPayoutStore.get_payout(agency_id=agency_id, payout_id=payout_id)
    if existing is not None:
        row.recorded = True
        row.recorded_payout_id = existing.get("payout_id") or payout_id
        return None, None, (
            f"Row {row_index} was already recorded (payout {row.recorded_payout_id}); "
            "recording it again would double-count the commission."
        )

    try:
        payout = AdvisorPayoutStore.record_payout(
            agency_id=agency_id,
            advisor_id=advisor_id.strip(),
            amount_usd=round(float(row.amount), 2),
            recorded_by=recorded_by,
            trip_id=row.match_trip_id,
            payout_id=payout_id,
            note=(
                f"Commission statement row {row_index} of batch {batch.batch_id} "
                f"({row.supplier_name or 'unknown supplier'}, ref {row.booking_ref or 'n/a'}; "
                f"match: {row.match_method})"
            ),
        )
    except Exception as exc:  # duplicate PK / race — resolve to existing record
        existing = AdvisorPayoutStore.get_payout(agency_id=agency_id, payout_id=payout_id)
        if existing is not None:
            row.recorded = True
            row.recorded_payout_id = existing.get("payout_id") or payout_id
            return None, None, (
                f"Row {row_index} was already recorded (payout {row.recorded_payout_id}); "
                "recording it again would double-count the commission."
            )
        return None, None, f"Payout recording failed: {exc}"
    row.recorded = True
    row.recorded_payout_id = payout.payout_id
    batch.linked[f"recorded_{row_index}"] = payout.payout_id
    _save_batch(batch)
    return batch, {
        "payout_id": payout.payout_id,
        "amount_usd": round(float(row.amount), 2),
        "trip_id": row.match_trip_id,
        "advisor_id": advisor_id.strip(),
        "storage_backend": getattr(payout, "storage_backend", "unknown"),
    }, None
