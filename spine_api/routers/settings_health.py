"""
Settings health check router.

On-demand health check for alert destinations and per-agency configuration.
Mounted separately so it can be included without auth if needed.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException

from spine_api.core.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_webhook_health(url: str, timeout_seconds: float = 5.0) -> Dict[str, Any]:
    """Probe a webhook URL with a lightweight HEAD request."""
    if not url:
        return {"status": "unconfigured", "detail": "No URL configured"}
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "WaypointOS-HealthCheck/1.0")
        start = time.monotonic()
        resp = urllib.request.urlopen(req, timeout=timeout_seconds)
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        return {
            "status": "healthy",
            "http_status": resp.status,
            "latency_ms": elapsed_ms,
        }
    except urllib.error.HTTPError as e:
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        # HTTP errors still mean the server is reachable
        return {
            "status": "reachable",
            "http_status": e.code,
            "latency_ms": elapsed_ms,
            "detail": f"HTTP {e.code}",
        }
    except Exception as e:
        return {
            "status": "unreachable",
            "error": str(e)[:200],
        }


def _check_email_health(smtp_host: str, smtp_port: int = 25, timeout_seconds: float = 5.0) -> Dict[str, Any]:
    """Probe SMTP connectivity with a socket connect."""
    if not smtp_host:
        return {"status": "unconfigured", "detail": "No SMTP host configured"}
    try:
        import socket

        start = time.monotonic()
        sock = socket.create_connection((smtp_host, smtp_port), timeout=timeout_seconds)
        sock.close()
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        return {
            "status": "healthy",
            "host": smtp_host,
            "port": smtp_port,
            "latency_ms": elapsed_ms,
        }
    except Exception as e:
        return {
            "status": "unreachable",
            "host": smtp_host,
            "port": smtp_port,
            "error": str(e)[:200],
        }


@router.get("/api/settings/health")
def get_settings_health(
    agency_id: str = "waypoint-hq",
    _perm=require_permission("settings:read"),
) -> Dict[str, Any]:
    """On-demand health check for alert destinations and agency configuration.

    Returns:
        - alert_destinations: per-destination health probe results
        - llm_guard: guard state summary
        - overall: healthy/degraded/critical
    """
    from src.intake.config.agency_settings import AgencySettingsStore
    from src.llm.usage_guard import get_guard_for_agency

    settings = AgencySettingsStore.load(agency_id)
    ad = settings.alert_destinations

    # Probe each enabled destination
    destination_results: List[Dict[str, Any]] = []
    healthy_count = 0
    total_enabled = 0

    for dest in ad.destinations:
        if not dest.enabled:
            destination_results.append({
                "id": dest.id,
                "label": dest.label,
                "type": dest.type,
                "enabled": False,
                "status": "disabled",
            })
            continue

        total_enabled += 1

        if dest.type == "webhook":
            probe = _check_webhook_health(dest.url)
        elif dest.type == "email":
            probe = _check_email_health(dest.smtp_host, dest.smtp_port)
        else:
            probe = {"status": "unknown_type", "detail": f"Unsupported type: {dest.type}"}

        if probe.get("status") in ("healthy", "reachable"):
            healthy_count += 1

        destination_results.append({
            "id": dest.id,
            "label": dest.label,
            "type": dest.type,
            "enabled": True,
            **probe,
        })

    # LLM guard summary
    try:
        guard = get_guard_for_agency(agency_id)
        guard_state = guard.get_state()
    except Exception as e:
        guard_state = {"error": str(e)[:200]}

    # Overall status
    if not ad.enabled:
        overall = "degraded"
        overall_detail = "Alert destinations are disabled"
    elif total_enabled == 0:
        overall = "degraded"
        overall_detail = "Alerts enabled but no destinations configured"
    elif healthy_count == total_enabled:
        overall = "healthy"
        overall_detail = f"All {total_enabled} destination(s) reachable"
    elif healthy_count > 0:
        overall = "degraded"
        overall_detail = f"{healthy_count}/{total_enabled} destination(s) reachable"
    else:
        overall = "critical"
        overall_detail = f"0/{total_enabled} destination(s) reachable"

    return {
        "agency_id": agency_id,
        "overall": overall,
        "overall_detail": overall_detail,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "alert_destinations": {
            "enabled": ad.enabled,
            "total_destinations": len(ad.destinations),
            "total_enabled": total_enabled,
            "healthy": healthy_count,
            "destinations": destination_results,
        },
        "llm_guard": guard_state,
    }
