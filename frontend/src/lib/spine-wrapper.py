#!/usr/bin/env python3
"""
spine-wrapper.py — Thin Python wrapper that exposes run_spine_once as a JSON subprocess.

This is the ONLY entrypoint the Next.js BFF should use to call the spine.
It:
1. Reads JSON input from stdin
2. Builds SourceEnvelope objects from the input
3. Calls run_spine_once from src.intake.orchestration
4. Outputs JSON result to stdout
5. Handles errors gracefully

Usage:
    echo '{"raw_note": "...", "stage": "discovery", ...}' | python spine-wrapper.py
"""

from __future__ import annotations

import sys
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on path
# frontend/src/lib/spine-wrapper.py → PROJECT_ROOT = travel_agency_agent/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope


def build_envelopes(data: Dict[str, Any]) -> List[SourceEnvelope]:
    """Build SourceEnvelope objects from input data."""
    envelopes: List[SourceEnvelope] = []

    if data.get("raw_note"):
        envelopes.append(SourceEnvelope.from_freeform(
            data["raw_note"], "agency_notes", "agent"
        ))

    if data.get("owner_note"):
        envelopes.append(SourceEnvelope.from_freeform(
            data["owner_note"], "agency_notes", "owner"
        ))

    if data.get("structured_json"):
        envelopes.append(SourceEnvelope.from_structured(
            data["structured_json"], "structured_import", "system"
        ))

    if data.get("itinerary_text"):
        envelopes.append(SourceEnvelope.from_freeform(
            data["itinerary_text"], "traveler_form", "traveler"
        ))

    return envelopes


def serialize_result(result: Any) -> Dict[str, Any]:
    """Serialize SpineResult to a JSON-serializable dict."""

    def _to_dict(obj: Any) -> Any:
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        if hasattr(obj, '__dict__'):
            return {k: _to_dict(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
        if isinstance(obj, (list, tuple)):
            return [_to_dict(item) for item in obj]
        if isinstance(obj, dict):
            return {k: _to_dict(v) for k, v in obj.items()}
        return obj

    output = {
        "packet": _to_dict(result.packet) if hasattr(result, 'packet') else result.packet,
        "validation": _to_dict(result.validation) if hasattr(result, 'validation') else result.validation,
        "decision": _to_dict(result.decision) if hasattr(result, 'decision') else result.decision,
        "strategy": _to_dict(result.strategy) if hasattr(result, 'strategy') else result.strategy,
        "internal_bundle": _to_dict(result.internal_bundle) if hasattr(result, 'internal_bundle') else result.internal_bundle,
        "traveler_bundle": _to_dict(result.traveler_bundle) if hasattr(result, 'traveler_bundle') else result.traveler_bundle,
        "leakage": result.leakage_result if hasattr(result, 'leakage_result') else {},
        "assertions": result.assertion_result if hasattr(result, 'assertion_result') else None,
        "run_ts": result.run_timestamp if hasattr(result, 'run_timestamp') else "",
    }

    return output


def main() -> None:
    """Main entrypoint — read stdin, call spine, output JSON."""
    try:
        # Read input from stdin
        data = json.load(sys.stdin)

        # Build envelopes
        envelopes = build_envelopes(data)

        # Extract parameters
        stage = data.get("stage", "discovery")
        operating_mode = data.get("operating_mode", "normal_intake")
        strict_leakage = data.get("strict_leakage", False)

        # Set strict leakage mode in the safety module before running spine
        if strict_leakage:
            from src.intake.safety import set_strict_mode
            set_strict_mode(True)

        # Run spine
        result = run_spine_once(
            envelopes=envelopes,
            stage=stage,
            operating_mode=operating_mode,
        )

        # Serialize and output
        output = serialize_result(result)
        print(json.dumps(output))

    except Exception as e:
        error_output = {
            "error": str(e),
            "error_type": type(e).__name__,
        }
        print(json.dumps(error_output))
        sys.exit(1)


if __name__ == "__main__":
    main()