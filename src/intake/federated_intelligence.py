"""
intake.federated_intelligence — Service layer for Intelligence Pool records.

Enables cross-agency risk detection and anonymized data sharing.

Durable store (2026-10-30, per Docs/research/BD_DATA_GOVERNANCE_FRAMEWORK_
2026-10-30.md gap #3): the pool is an append-only JSONL ledger under
``data/intelligence_pool/`` — records survive restarts, and every report is
mirrored into the canonical RULE_015 audit chain (``AuditStore.log_event``)
so the intelligence layer has ONE ledger, not a parallel one. The public
API (``report_incident`` / ``query_risks`` / the ``intelligence_service``
singleton) is unchanged from the previous in-memory mock.

Honesty contract: incidents are anonymized at the source (agency_id is
hashed, never stored); the historical Singapore demo fixture is now labeled
``demo: true`` — it must never be mistaken for live federated signal.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("federated_intel")

# Append-only store location (module-level so tests can redirect it).
STORE_PATH = Path("data/intelligence_pool/incidents.jsonl")

# Active-risk window: incidents older than this are retained on disk but
# excluded from query_risks (BD matrix: events/incidents ≤14d).
ACTIVE_INCIDENT_TTL_SECONDS = 14 * 86400


@dataclass(slots=True)
class IntelligenceIncident:
    """Anonymized incident report for the federated pool."""
    incident_type: str  # e.g., 'visa_delay', 'weather_disruption', 'payment_gateway_down'
    location: str
    severity: int  # 1-5
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


def _parse_utc(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class FederatedIntelligenceService:
    """
    Manages the global intelligence pool over a durable append-only store.

    Writes: append one JSON line (fsync'd) + mirror into the audit chain.
    Reads: load all records (corrupted lines skipped, mirroring
    AuditStore._read_events discipline); ``query_risks`` returns only
    incidents inside the active-TTL window.
    """

    def __init__(self, store_path: Optional[Path] = None):
        self._store_path_override = Path(store_path) if store_path else None

    def _resolve_path(self) -> Path:
        """Lazy path resolution so the singleton honors module-level redirects."""
        if self._store_path_override is not None:
            return self._store_path_override
        return Path(STORE_PATH)

    # ------------------------------------------------------------ storage

    def _append_record(self, record: Dict[str, Any]) -> None:
        path = self._resolve_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _load_records(self) -> List[Dict[str, Any]]:
        path = self._resolve_path()
        if not path.exists():
            return []
        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    continue  # corrupted line — skip, never crash reads
                if isinstance(parsed, dict):
                    records.append(parsed)
        return records

    # ------------------------------------------------------------- public

    def report_incident(self, agency_id: str, incident: IntelligenceIncident):
        """Adds an anonymized record to the pool (append-only + audit mirror)."""
        # Anonymize source — the agency identity never touches the store.
        source_hash = hashlib.sha256(agency_id.encode()).hexdigest()
        retrieved_at = datetime.now(timezone.utc).isoformat()

        record = {
            "record_id": f"fi_{hashlib.sha256(f'{source_hash}:{retrieved_at}:{incident.incident_type}'.encode()).hexdigest()[:12]}",
            "type": incident.incident_type,
            "location": incident.location,
            "severity": incident.severity,
            "details": incident.details,
            "confidence": incident.confidence,
            "source_hash": source_hash,
            "license_tier": "unknown",
            "timestamp": retrieved_at,
        }

        self._append_record(record)
        logger.info("Incident reported to Federated Pool: %s @ %s", incident.incident_type, incident.location)

        # Mirror into the canonical audit chain (incident capture must never
        # be lost to a degraded audit sink — failures are logged, not raised;
        # same philosophy as AuditStore fallbacks).
        try:
            from spine_api.persistence import AuditStore

            AuditStore.log_event(
                "federated_intelligence_incident",
                "system",
                {
                    "record_id": record["record_id"],
                    "incident_type": record["type"],
                    "location": record["location"],
                    "severity": record["severity"],
                    "source_hash": source_hash,
                    "retrieved_at": retrieved_at,
                },
            )
        except Exception as exc:  # pragma: no cover - degraded-audit path
            logger.warning("Federated-incident audit mirror failed (incident retained): %s", exc)

    def collect_expired(self, retention_days: int = 180) -> List[Dict[str, Any]]:
        """BD2.6 retention (pure read): return records older than
        ``retention_days`` for the caller to hand to cold storage. Undated
        records are included (already excluded from active queries). Nothing
        is deleted here — the append-only live store is untouched; archiving
        persistence is the caller's explicit step (ops/CLI), keeping this
        service read+policy only.
        """
        now = datetime.now(timezone.utc)
        cutoff = retention_days * 86400
        aged: List[Dict[str, Any]] = []
        for r in self._load_records():
            retrieved = _parse_utc(str(r.get("timestamp", "")))
            if retrieved is None or (now - retrieved).total_seconds() > cutoff:
                aged.append(r)
        return aged

    def query_risks(self, location: str) -> List[Dict[str, Any]]:
        """Queries the pool for ACTIVE risks in a location (freshness-windowed)."""
        now = datetime.now(timezone.utc)
        hits = []
        for r in self._load_records():
            if r.get("location", "").lower() not in location.lower():
                continue
            retrieved = _parse_utc(str(r.get("timestamp", "")))
            if retrieved is None:
                continue  # undated incident = not an active risk (stale-by-default)
            if (now - retrieved).total_seconds() > ACTIVE_INCIDENT_TTL_SECONDS:
                continue
            hits.append(r)

        # Historical demo fixture — explicitly labeled so it can never be
        # mistaken for live federated signal.
        if not hits and "Singapore" in location:
            hits.append({
                "demo": True,
                "type": "visa_processing_delay",
                "severity": 3,
                "message": "DEMO — no live federated data: Singapore visa-rejection spike placeholder.",
            })

        return hits


# Global singleton (default store path; tests redirect via constructor)
intelligence_service = FederatedIntelligenceService()
