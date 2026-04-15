"""
intake.telemetry — Lightweight telemetry for spine quality metrics.

This module provides non-blocking telemetry emission for:
- NB02 ambiguity synthesis (when NB01 missed an ambiguity)
- Extraction quality signals
- Decision confidence tracking

All telemetry is async and non-blocking. Failures are silently logged, never raised.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("intake.telemetry")

# Default telemetry directory
DEFAULT_TELEMETRY_DIR = Path.home() / ".gstack" / "telemetry"


def _get_telemetry_path() -> Path:
    """Get telemetry directory from env or default."""
    env_path = os.environ.get("SPINE_TELEMETRY_DIR")
    if env_path:
        return Path(env_path)
    return DEFAULT_TELEMETRY_DIR


def emit_telemetry(
    event_type: str,
    data: Dict[str, Any],
    timestamp: Optional[str] = None,
) -> None:
    """
    Emit a telemetry event asynchronously.
    
    This is non-blocking and failures are silently logged.
    Used for quality metrics and debugging, not for critical logic.
    
    Args:
        event_type: Category of event (e.g., "nb02.ambiguity_synthesis")
        data: Event payload (must be JSON-serializable)
        timestamp: Optional ISO-8601 timestamp (defaults to now)
    """
    try:
        telemetry_dir = _get_telemetry_path()
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        # Daily rotation files
        date_str = datetime.now().strftime("%Y-%m-%d")
        telemetry_file = telemetry_dir / f"spine_telemetry_{date_str}.jsonl"
        
        event = {
            "ts": timestamp or datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
        }
        
        # Append to JSONL file
        with open(telemetry_file, "a") as f:
            f.write(json.dumps(event) + "\n")
            
    except Exception as e:
        # Telemetry should never block or fail visibly
        logger.debug(f"Telemetry emission failed: {e}")


def emit_ambiguity_synthesis(
    field_name: str,
    reason: str,
    stage: str,
    candidates: Optional[list] = None,
    packet_id: Optional[str] = None,
) -> None:
    """
    Emit telemetry when NB02 synthesizes an ambiguity that NB01 missed.
    
    This is a measurable upstream extraction-quality signal.
    High synthesis counts indicate systematic NB01 gaps.
    """
    emit_telemetry(
        event_type="nb02.ambiguity_synthesis",
        data={
            "field": field_name,
            "reason": reason,
            "stage": stage,
            "candidates": candidates,
            "packet_id": packet_id,
        },
    )