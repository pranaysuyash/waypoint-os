"""
src/orchestration/irops_watch_service.py — 24/7 IROPS Continuous Disruption Watch Loop.

Implements the autonomous disruption watch loop that closes the gap between
one-shot ``IROPSAutoHealerEngine.execute_healing_protocol()`` and a real
24/7 self-healing travel operations system.

Design (first principles):
- One asyncio background task per ASGI lifespan — no external scheduler dep.
- Polls ``TripStore`` for active trips every ``IROPS_POLL_INTERVAL_SECONDS``
  (default 300 = 5 min).
- For each active trip's JDG, evaluates every flight/transfer node for a
  disruption signal (real path: swap ``_disruption_signal`` for a live
  flight-status API call against FlightAware/OAG).
- When disruption is detected, runs ``IROPSAutoHealerEngine.execute_healing_protocol``
  and persists the healing plan onto the trip record so the companion app
  and advisor workbench can surface it immediately.
- Honest labeling: all auto-generated healing plans carry
  ``reality_tier="deterministic_preview"`` and ``auto_healed=True``.

Reality boundary: the disruption signal is currently a deterministic
simulation (nodes flagged via ``metadata.disrupted=true`` on the stored JDG).
The missing-for-upgrade path is a live flight-status API integration.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("src.orchestration.irops_watch_service")

# Default poll interval. Override with IROPS_POLL_INTERVAL_SECONDS env var.
_DEFAULT_POLL_INTERVAL = 300  # 5 minutes

# Global handle so the lifespan can cancel the task on shutdown.
_watch_task: "Optional[asyncio.Task[None]]" = None

# In-memory incident registry so we don't fire duplicate alerts per trip per
# disrupted node within the same process lifetime.
_SEEN_INCIDENTS: Dict[str, str] = {}  # "trip_id:node_id" -> incident_id


def _poll_interval() -> int:
    try:
        return int(os.environ.get("IROPS_POLL_INTERVAL_SECONDS", _DEFAULT_POLL_INTERVAL))
    except (TypeError, ValueError):
        return _DEFAULT_POLL_INTERVAL


def _disruption_signal(node: Dict[str, Any]) -> bool:
    """Evaluate whether a JDG node signals a disruption.

    Current implementation: checks ``metadata.disrupted`` flag on the stored
    node dict. In production this is replaced by a live flight-status API
    call (FlightAware / OAG / airline status API).
    """
    meta = node.get("metadata") or {}
    if isinstance(meta, dict) and meta.get("disrupted"):
        return True
    # Treat nodes with commitment_status == "disrupted" as signals too.
    return str(node.get("commitment_status", "")).lower() == "disrupted"


async def _scan_trip(trip_id: str, trip: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Scan a single trip's JDG for disrupted nodes and execute healing."""
    from src.orchestration.irops_healer import IROPSAutoHealerEngine
    from src.schemas.journey_graph import JourneyDependencyGraph

    if not trip:
        return None

    stored_nodes = trip.get("journey_graph_nodes") or []
    stored_edges = trip.get("journey_graph_edges") or []
    if not stored_nodes:
        return None

    graph = JourneyDependencyGraph.from_stored(trip_id, stored_nodes, stored_edges)

    healing_results: List[Dict[str, Any]] = []
    for node_id, node_obj in graph.nodes.items():
        # Only assess flight/transfer nodes for air disruption.
        node_type = str(getattr(node_obj, "node_type", "") or "").upper()
        if node_type not in ("FLIGHT", "TRANSFER"):
            continue

        # Find the raw stored dict to check metadata flags.
        raw_node = next(
            (n for n in stored_nodes if n.get("node_id") == node_id), {}
        )
        if not _disruption_signal(raw_node):
            continue

        incident_key = f"{trip_id}:{node_id}"
        if incident_key in _SEEN_INCIDENTS:
            logger.debug(
                "IROPS watch: incident already processed for trip %s node %s; skipping",
                trip_id,
                node_id,
            )
            continue

        logger.warning(
            "IROPS watch: disruption detected — trip=%s node=%s (%s)",
            trip_id,
            node_id,
            getattr(node_obj, "title", node_id),
        )

        try:
            plan = IROPSAutoHealerEngine.execute_healing_protocol(
                trip_id=trip_id,
                delayed_node_id=node_id,
                delay_minutes=180,
                stored_graph=graph,
            )
            _SEEN_INCIDENTS[incident_key] = plan.incident_id

            # Persist the healing plan onto the trip so companion/workbench sees it.
            from spine_api.persistence import AuditStore, TripStore

            plan_dict = plan.to_dict()
            plan_dict["auto_healed"] = True
            plan_dict["reality_tier"] = "deterministic_preview"
            plan_dict["watch_triggered_at"] = datetime.now(timezone.utc).isoformat()

            # Append to the trip's irops_incidents list (non-destructive merge).
            current = TripStore.get_trip(trip_id) or {}
            incidents: List[Dict[str, Any]] = list(current.get("irops_incidents") or [])
            incidents.append(plan_dict)
            TripStore.update_trip(trip_id, {"irops_incidents": incidents})

            AuditStore.log_event(
                "irops_auto_healed",
                "irops_watch_service",
                {
                    "trip_id": trip_id,
                    "incident_id": plan.incident_id,
                    "delayed_node_id": node_id,
                    "delay_minutes": plan.delay_minutes,
                    "auto_healed": True,
                    "reality_tier": "deterministic_preview",
                },
            )
            logger.info(
                "IROPS watch: healing plan %s persisted for trip %s",
                plan.incident_id,
                trip_id,
            )
            healing_results.append(plan_dict)

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "IROPS watch: healing protocol failed for trip %s node %s: %s",
                trip_id,
                node_id,
                exc,
            )

    return {"trip_id": trip_id, "healing_results": healing_results} if healing_results else None


async def _watch_loop() -> None:
    """Main async loop — runs until cancelled."""
    from spine_api.persistence import TripStore

    interval = _poll_interval()
    logger.info("IROPS watch loop started (poll interval: %ds)", interval)

    while True:
        try:
            await asyncio.sleep(interval)
            logger.debug("IROPS watch: scanning active trips…")
            # TripStore.list_active_trips() returns trip dicts for trips whose
            # status is not 'completed' or 'cancelled'. Fallback to empty list
            # when the method is unavailable (dev/test without DB).
            list_fn = getattr(TripStore, "list_active_trips", None)
            trips: List[Dict[str, Any]] = list_fn() if callable(list_fn) else []

            for trip in trips:
                trip_id = str(trip.get("trip_id") or trip.get("id") or "")
                if not trip_id:
                    continue
                try:
                    await _scan_trip(trip_id, trip)
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "IROPS watch: scan failed for trip %s: %s", trip_id, exc
                    )

        except asyncio.CancelledError:
            logger.info("IROPS watch loop cancelled — shutting down.")
            break
        except Exception as exc:  # noqa: BLE001
            logger.error("IROPS watch loop error (will retry): %s", exc)


# ---------------------------------------------------------------------------
# Public API consumed by spine_api/server.py lifespan
# ---------------------------------------------------------------------------

def start_watch_service(loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    """Start the IROPS background watch task.

    Called from the FastAPI lifespan (startup) or API endpoints so the task lives
    for the process lifetime. Safe to call multiple times — a running task is
    not restarted.
    """
    global _watch_task  # noqa: PLW0603
    if _watch_task is not None and not _watch_task.done():
        logger.info("IROPS watch service already running.")
        return
    try:
        active_loop = loop or asyncio.get_running_loop()
        _watch_task = active_loop.create_task(_watch_loop(), name="irops_watch_loop")
        logger.info("IROPS watch service task created.")
    except RuntimeError:
        logger.warning("IROPS watch service cannot start: no running event loop.")


def stop_watch_service() -> None:
    """Cancel the IROPS background watch task.

    Called from the FastAPI lifespan (shutdown).
    """
    global _watch_task  # noqa: PLW0603
    if _watch_task is not None and not _watch_task.done():
        _watch_task.cancel()
        logger.info("IROPS watch service task cancelled.")
    _watch_task = None


def watch_service_status() -> Dict[str, Any]:
    """Return a status snapshot for the /irops-healer/watch/status endpoint."""
    running = _watch_task is not None and not _watch_task.done()
    return {
        "running": running,
        "poll_interval_seconds": _poll_interval(),
        "active_incidents": len(_SEEN_INCIDENTS),
        "incidents": list(_SEEN_INCIDENTS.keys()),
        "reality_tier": "deterministic_preview",
        "provider_connected": False,
        "missing_for_upgrade": [
            "Live flight-status API (FlightAware / OAG) replacing the metadata.disrupted flag",
            "Outbound advisor push notifications (WebSocket / FCM) on new incidents",
        ],
    }
