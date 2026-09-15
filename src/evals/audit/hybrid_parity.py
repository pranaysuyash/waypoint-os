"""hybrid_parity — the degraded-mode authority invariant for the D6 lane.

ADR-008 §7 item 2 (ratified 2026-09-14): the serving posture is declared
off-by-default with envelope-level opt-in, and the eval lane must make the
declared configuration falsifiable end-to-end. This module grades the
first of three truths: **authority invariance under degradation**.

Invariant: with ``USE_HYBRID_DECISION_ENGINE=1`` and *no provider
credentials*, the decision engine must degrade to the deterministic rules
path without changing any authority axis (decision state, hard blockers,
contradictions) versus the flag-off posture. An outage is exactly when
the safety envelope matters most; divergence between "flag OFF" and
"flag ON + provider absent" means the ON posture is unsafe to hold, and
the snapshot's ``gap_decision`` promotion gate must stay closed.

Credential-safe by construction: provider keys are stripped in-process
for the ON arm so the engine's safe fallback is exercised — the collector
never authorizes a network call.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

# Provider credential variables whose presence could turn the "degraded"
# arm into a live-provider run. All are stripped in-process for that arm
# and restored afterward.
_PROVIDER_KEY_VARS = (
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "HF_TOKEN",
)


def collect_hybrid_parity(fixtures_path: Path) -> Dict[str, Any]:
    """Run the scenario collector under both postures and diff the axes.

    Returns a machine-readable record embedded in the D6 snapshot under
    ``hybrid_config.degraded_parity``. Never raises for engine-mode
    divergence — divergence is a *finding* (``parity: "fail"`` with the
    divergent packet ids), not an exception.
    """
    from src.evals.audit.snapshot import _collect_live_scenario_results
    from src.intake import decision as _decision

    saved: Dict[str, str | None] = {v: os.environ.get(v) for v in _PROVIDER_KEY_VARS}
    results: Dict[str, Dict[str, Dict[str, Any]]] = {}
    try:
        for mode, flag in (("off", "0"), ("on_degraded", "1")):
            for var, val in saved.items():
                if val is not None:
                    os.environ.pop(var, None)
            os.environ["USE_HYBRID_DECISION_ENGINE"] = flag
            _decision._reset_hybrid_engine()
            try:
                results[mode] = _collect_live_scenario_results(fixtures_path)
            finally:
                _decision._reset_hybrid_engine()
    finally:
        for var, val in saved.items():
            if val is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = val

    off = results.get("off", {})
    on_degraded = results.get("on_degraded", {})
    common = sorted(set(off) & set(on_degraded))
    divergent: List[str] = []
    for packet_id in common:
        a, b = off[packet_id], on_degraded[packet_id]
        if (
            a["decision_state"] != b["decision_state"]
            or a["hard_blockers"] != b["hard_blockers"]
            or a["contradictions"] != b["contradictions"]
        ):
            divergent.append(packet_id)
    parity = "pass" if (common and not divergent) else "fail"
    return {
        "invariant": "flag ON + provider absent == flag OFF on authority axes",
        "parity": parity,
        "scenarios_compared": len(common),
        "scenarios_collected": {"off": len(off), "on_degraded": len(on_degraded)},
        "divergent_scenarios": divergent,
        "credential_safe": True,
    }
