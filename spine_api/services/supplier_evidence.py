"""Read-only observations from an explicitly configured supplier snapshot."""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, ValidationError, model_validator

MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_id: str = Field(min_length=1, max_length=96)
    service_id: str = Field(min_length=1, max_length=96)
    source_record_id: str = Field(min_length=1, max_length=160)
    source_url: HttpUrl
    observed_at: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_url.scheme != "https" or self.source_url.username or self.source_url.password:
            raise ValueError("Supplier source links must be HTTPS and contain no credentials")
        if self.expires_at <= self.observed_at:
            raise ValueError("Source expiry must follow observation time")
        return self

    def fresh(self, now: datetime) -> bool:
        return self.observed_at <= now < self.expires_at

    def provenance(self) -> dict:
        return self.model_dump(mode="json", include={"source_record_id", "source_url", "observed_at", "expires_at"})


class RateObservation(Observation):
    effective_from: date
    effective_through: date
    minimum_guests: int = Field(ge=1)
    maximum_guests: int = Field(ge=1)
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    basis: Literal["per_service", "per_guest", "per_night"]

    @model_validator(mode="after")
    def validate_rate_range(self):
        if self.effective_from > self.effective_through or self.minimum_guests > self.maximum_guests:
            raise ValueError("Supplier rate coverage is inverted")
        return self


class CalendarObservation(Observation):
    service_date: date
    available_guests: int = Field(ge=0)


class SupplierSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    agency_id: str = Field(min_length=1)
    provenance: Literal["fictional_fixture", "buyer_supplied_snapshot"]
    rates: list[RateObservation]
    calendar: list[CalendarObservation]


def _evidence(rows: list, now: datetime, values) -> dict:
    if not rows:
        return {"state": "missing", "sources": []}
    current = [row for row in rows if row.fresh(now)]
    if not current:
        return {"state": "stale", "sources": [row.provenance() for row in rows]}
    observed = list({tuple(values(row).items()): values(row) for row in current}.values())
    sources = [row.provenance() for row in current]
    if len(observed) != 1:
        return {"state": "conflicting", "sources": sources}
    return {"state": "observed", "sources": sources, **observed[0]}


def lookup(
    path: str, agency_id: str, supplier_id: str, service_id: str, service_date: date, guests: int,
) -> dict:
    result = {
        "supplier_id": supplier_id, "service_id": service_id, "service_date": service_date.isoformat(),
        "guests": guests, "state": "staff_review", "provenance": None,
        "rate": {"state": "missing", "sources": []}, "calendar": {"state": "missing", "sources": []},
    }
    if not path:
        return {**result, "review_reasons": ["snapshot_not_configured"]}
    try:
        with Path(path).open("rb") as source:
            raw = source.read(MAX_SNAPSHOT_BYTES + 1)
        if len(raw) > MAX_SNAPSHOT_BYTES:
            return {**result, "review_reasons": ["snapshot_invalid"]}
        snapshot = SupplierSnapshot.model_validate_json(raw)
    except OSError:
        return {**result, "review_reasons": ["snapshot_unavailable"]}
    except ValidationError:
        return {**result, "review_reasons": ["snapshot_invalid"]}
    if snapshot.agency_id != agency_id:
        return {**result, "review_reasons": ["snapshot_not_configured"]}

    now = datetime.now(timezone.utc)
    rate = _evidence([
        row for row in snapshot.rates
        if (row.supplier_id, row.service_id) == (supplier_id, service_id)
        and row.effective_from <= service_date <= row.effective_through
        and row.minimum_guests <= guests <= row.maximum_guests
    ], now, lambda row: {
        "amount": format(row.amount.normalize(), "f"), "currency": row.currency, "basis": row.basis,
    })
    calendar = _evidence([
        row for row in snapshot.calendar
        if (row.supplier_id, row.service_id, row.service_date) == (supplier_id, service_id, service_date)
    ], now, lambda row: {"available_guests": row.available_guests})
    if calendar["state"] == "observed":
        calendar["state"] = "available_observed" if calendar["available_guests"] >= guests else "unavailable_observed"
    reasons = []
    if rate["state"] != "observed":
        reasons.append(f"rate_{rate['state']}")
    if calendar["state"] != "available_observed":
        reasons.append(f"calendar_{calendar['state']}")
    return {
        **result, "state": "staff_review" if reasons else "evidence_found", "provenance": snapshot.provenance,
        "rate": rate, "calendar": calendar, "review_reasons": reasons,
    }
