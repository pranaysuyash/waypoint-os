"""
spine_api.services.pre_departure_scheduler — T12: D-7/D-3/D-1 briefing triggers.

The pre-departure bundle endpoint is served on demand; this scheduler makes
the cadence *happen*: a daemon loop (retention-sweep pattern) scans active
trips daily, and when a trip enters a D-7/D-3/D-1 window it generates the
stage bundle and records a ``pre_departure_briefings`` artifact on the trip
(added once per stage — idempotent via ``stages_fired``).

Honesty boundaries:
- Generation is deterministic (cadence templates + stored trip data — same
  engine as the router). No provider calls, no sends.
- The artifact records what was generated and when; delivery to the traveler
  is explicitly out of scope here (the advisor uses the T1 dispatch lane /
  bundle PDF manually until an owner decision wires briefing delivery).
- Feature-gated: ``PRE_DEPARTURE_SCHEDULER=1`` (off by default, zero
  implicit defaults), scan interval env-tunable.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("spine_api.pre_departure_scheduler")

_stages = ("D_MINUS_7", "D_MINUS_3", "D_MINUS_1")
_STAGE_DAYS = {"D_MINUS_7": 7, "D_MINUS_3": 3, "D_MINUS_1": 1}

_thread: Optional[threading.Thread] = None
_stop = threading.Event()

_scheduler_lock = threading.Lock()
_fired_state: Dict[str, Dict[str, Any]] = {}  # memory-backend idempotency


def scheduler_enabled() -> bool:
    return os.getenv("PRE_DEPARTURE_SCHEDULER", "0").strip().lower() in ("1", "true", "yes", "on")


def scan_interval_seconds() -> int:
    raw = os.getenv("PRE_DEPARTURE_SCAN_INTERVAL_SECONDS", "21600").strip()  # 6h
    try:
        return max(300, int(raw))
    except ValueError:
        return 21600


def _parse_departure(trip: dict) -> Optional[date]:
    raw = str(trip.get("departure_date") or trip.get("start_date") or "").strip()
    if not raw or raw == "TBD":
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def stages_due(trip: dict, today: Optional[date] = None) -> List[str]:
    """Which D-stages this trip has entered (never ones already fired)."""
    departure = _parse_departure(trip)
    if departure is None:
        return []
    today = today or date.today()
    days_out = (departure - today).days
    already = set((trip.get("pre_departure_briefings") or {}).get("stages_fired") or [])
    memory_fired = set((_fired_state.get(trip.get("id") or "") or {}).get("stages_fired") or [])
    already |= memory_fired
    due: List[str] = []
    for stage in _stages:
        if stage in already:
            continue
        if days_out <= _STAGE_DAYS[stage] and days_out >= 0:
            due.append(stage)
    # Departure passed → the D-1 artifact is the last that could fire.
    return due


def fire_due_briefings(trip: dict, agency_id: str) -> Optional[Dict[str, Any]]:
    """Generate + record briefing artifacts for all due stages. Returns the
    artifact written, or None when nothing was due."""
    due = stages_due(trip)
    if not due:
        return None

    from spine_api.persistence import TripStore
    from src.briefing.pre_departure_cadence import CadenceStage, PreDepartureCadenceEngine

    generated: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    packet = trip.get("packet") or {}
    departure = _parse_departure(trip)
    traveler = str(
        trip.get("traveler_name") or packet.get("customer_name") or trip.get("customer_name") or "Traveler"
    )
    country = str(
        packet.get("destination_country_code") or packet.get("destination_country") or "DEFAULT"
    )
    for stage in due:
        try:
            cadence_stage = CadenceStage[stage]
            briefing = PreDepartureCadenceEngine.generate_briefing(
                trip_id=str(trip.get("id") or ""),
                traveler_name=traveler,
                departure_date=departure.isoformat() if departure else "TBD",
                destination_country_code=country,
                stage=cadence_stage,
            )
            generated.append(
                {
                    "stage": stage,
                    "generated_at": now_iso,
                    "sections": sorted(briefing.to_dict().keys()) if hasattr(briefing, "to_dict") else ["packet"],
                }
            )
        except Exception as exc:  # generation failure never blocks the loop
            logger.warning("pre-departure generation failed (%s/%s): %s", trip.get("id"), stage, exc)
            return None

    artifact = {
        "stages_fired": sorted(
            set((trip.get("pre_departure_briefings") or {}).get("stages_fired") or [])
            | set((_fired_state.get(trip.get("id") or "") or {}).get("stages_fired") or [])
            | set(due)
        ),
        "last_generated_at": now_iso,
        "generated": generated,
        "delivery": "advisor_manual",  # honest: nothing was sent
    }

    updated = TripStore.update_trip_for_agency(trip["id"], agency_id, {"pre_departure_briefings": artifact})
    if updated is not None:
        with _scheduler_lock:
            _fired_state[trip["id"]] = artifact
        return artifact
    return None


def scan_all_agencies() -> Dict[str, int]:
    """Scan every agency's active trips with a departure date; fire due
    briefings. Returns counters for the log line."""
    from spine_api.persistence import TripStore

    fired = 0
    scanned = 0
    agencies = _known_agency_ids()
    for agency_id in agencies:
        try:
            trips = TripStore.list_trips(limit=500, agency_id=agency_id)
        except Exception as exc:
            logger.warning("pre-departure scan skipped agency %s: %s", agency_id, exc)
            continue
        for trip in trips:
            if trip.get("status") in ("cancelled", "completed"):
                continue
            scanned += 1
            try:
                if fire_due_briefings(trip, agency_id) is not None:
                    fired += 1
            except Exception as exc:
                logger.warning("pre-departure fire failed for %s: %s", trip.get("id"), exc)
    return {"agencies": len(agencies), "trips_scanned": scanned, "briefings_fired": fired}


def _known_agency_ids() -> List[str]:
    """Distinct agency ids across the trip store (dual-backend aware)."""
    from spine_api.persistence import TripStore

    ids = set()
    try:
        for trip in TripStore.list_trips(limit=1000):
            agency = trip.get("agency_id")
            if agency:
                ids.add(agency)
    except Exception as exc:
        logger.warning("pre-departure agency discovery failed: %s", exc)
    return sorted(ids)


def _loop() -> None:
    interval = scan_interval_seconds()
    while not _stop.is_set():
        try:
            counters = scan_all_agencies()
            if counters["briefings_fired"]:
                logger.info("pre-departure scheduler: %s", counters)
        except Exception as exc:
            logger.warning("pre-departure scheduler scan failed: %s", exc)
        _stop.wait(interval)


def start_scheduler() -> None:
    global _thread
    if _thread is not None or not scheduler_enabled():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, daemon=True, name="pre-departure-scheduler")
    _thread.start()
    logger.info("pre-departure scheduler started (interval=%ss)", scan_interval_seconds())


def stop_scheduler() -> None:
    global _thread
    _stop.set()
    if _thread is not None:
        _thread.join(timeout=2)
        _thread = None
