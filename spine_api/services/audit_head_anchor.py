"""Audit-chain head-hash anchoring — EXPLORE #5 / topic 51a hardening item (gap 1).

Gap: neither audit chain's head hash is snapshotted outside its own store, so
a write-capable attacker could rewrite history AND the chain. The anchor is a
deliberately minimal external witness: an append-only anchor file
(`audit_head_anchors.jsonl`) that records {anchored_at, head_hash,
event_count} from `AuditStore.verify_chain()`. Rewriting history then
requires tampering with two stores whose divergence
`detect_anchor_divergence` catches (chain shrank after anchoring = rewritten;
head changed without growth = rewritten).

This is the minimal local-disk witness design — KMS/remote anchoring is a
later hardening step if the threat model demands it.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from spine_api.persistence import AuditStore

ANCHOR_FILE = Path("data/audit/audit_head_anchors.jsonl")


def record_head_anchor() -> dict:
    """Verify both chains and append the current head to the anchor witness."""
    report = AuditStore.verify_chain()
    entry = {
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "head_hash": report.get("head_hash"),
        "event_count": report.get("event_count"),
        "chain_valid": report.get("valid"),
    }
    ANCHOR_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ANCHOR_FILE.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def detect_anchor_divergence(current_report: dict | None = None) -> dict:
    """Compare the latest anchor against the current chain state.

    Diverged when the chain shrank after anchoring (rewritten) or the head
    changed while the count stayed flat (in-place rewrite). Growth is normal.
    """
    if current_report is None:
        current_report = AuditStore.verify_chain()
    anchors = []
    if ANCHOR_FILE.exists():
        for line in ANCHOR_FILE.read_text().splitlines():
            if line.strip():
                try:
                    anchors.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    if not anchors:
        return {"diverged": False, "reason": "no anchors recorded", "anchor": None}

    last = anchors[-1]
    head_now = current_report.get("head_hash")
    count_now = current_report.get("event_count")
    head_then = last.get("head_hash")
    count_then = last.get("event_count")

    if head_then and head_now and head_now != head_then:
        if count_now is not None and count_then is not None and count_now < count_then:
            return {"diverged": True, "reason": "chain shrank after anchoring (rewritten)", "anchor": last}
        if count_now == count_then:
            return {"diverged": True, "reason": "head hash changed at unchanged count (in-place rewrite)", "anchor": last}
    return {"diverged": False, "reason": "head matches last anchor or chain grew", "anchor": last}
