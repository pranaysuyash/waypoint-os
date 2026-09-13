"""L0/L2 attribution — speaker segmentation and per-traveler fact binding.

Ontology layer: A-segment (deterministic speaker segmentation) +
A-attribute (bind facts to the speaker who stated them).

Sim #2 (FND-0275): Meera's "i'm jain" and "terrified of heights" were
captured group-wide or dropped entirely because the pipeline had no
per-speaker structure. This module splits a delegation thread into
speaker-attributed segments and binds per-person facts to named travelers,
keeping group facts separate.

Design contract (INTAKE_ONTOLOGY_STATES_EVENTS_ACTIONS_2026-09-13.md):
- Personal facts NEVER widen to group facts during binding.
- Unattributed statements stay in the group lane as today (degraded but
  visible via the speakers fact).
- The group budget/window/party remain packet-level facts — travelers carry
  only constraints, preferences, and occasion anchors.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from src.intake.extractors import _extract_trip_intent

# Speaker markers, checked in priority order:
#   1. Forwarded header: "[forwarded voice note from Arjun]:" — most specific
#   2. Chat-dump line: "[priya]: text"
#   3. Self-identification: "meera here," / "it's arjun here"
_HEADER_RE = re.compile(
    r"^\s*\[[^\]]*?\bfrom\s+([A-Za-z][\w']{0,30})\s*\]",
    re.IGNORECASE,
)
_CHAT_LINE_RE = re.compile(r"^\s*\[([A-Za-z][\w']{0,30})\]:\s*", re.IGNORECASE)
_SELF_ID_RE = re.compile(
    r"^(?:hello[,.!]?\s*)?it'?s\s+([a-z][a-z']{0,20})\s+here\b"
    r"|^(?:hello[,.!]?\s*)?([a-z][a-z']{0,20})\s+here\b",
    re.IGNORECASE,
)

# Names that are clearly not people (month/season/greeting collisions).
_NON_NAME_WORDS = frozenset({
    "update", "updates", "budget", "dates", "plan", "ok", "so", "and",
    "the", "a", "an", "i", "we", "it", "also", "maybe", "fine", "sorry",
    "group", "chat", "dump", "forwarded", "voice", "note", "from",
})


def _clean_name(raw: str) -> Optional[str]:
    name = re.sub(r"\s+", " ", raw.strip().rstrip(":").strip()).title()
    if not name:
        return None
    # Reject when ANY word is a non-name token ("Group Chat Dump",
    # "Forwarded Voice Note From Meera").
    if any(w.lower() in _NON_NAME_WORDS for w in name.split()):
        return None
    return name


def extract_speaker_segments(text: str) -> List[Dict[str, Any]]:
    """Split a delegation thread into speaker-attributed segments.

    Returns a list of {speaker, text, kind} where kind is "chat" (dump
    lines), "self_id" (paragraph opened by a self-identification), or
    "group" (unattributed text — typically the organizer's opening or
    pure logistics).
    """
    segments: List[Dict[str, Any]] = []
    current_speaker: Optional[str] = None
    current_lines: List[str] = []

    def flush():
        body = "\n".join(current_lines).strip()
        if body:
            segments.append({
                "speaker": current_speaker,
                "text": body,
                "kind": "chat" if current_speaker and len(current_lines) > 0 and all(
                    line.startswith("[") for line in current_lines
                ) else "self_id" if current_speaker else "group",
            })

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # 1) Forwarded header (most specific — checked before chat lines so
        # "[forwarded voice note from X]:" isn't read as speaker "forwarded
        # voice note from X").
        header = _HEADER_RE.match(stripped)
        if header:
            speaker = _clean_name(header.group(1))
            if speaker:
                flush()
                current_speaker, current_lines = speaker, []
                # The header itself carries no facts; following lines do.
                continue

        # 2) Chat-dump line: "[priya]: text"
        chat = _CHAT_LINE_RE.match(stripped)
        if chat:
            speaker = _clean_name(chat.group(1))
            if speaker:
                if current_speaker != speaker:
                    flush()
                    current_speaker, current_lines = speaker, []
                current_lines.append(stripped)
                continue

        # 3) Self-ID opening: "hello, meera here (…)" / "it's arjun here —"
        self_id = _SELF_ID_RE.match(stripped)
        if self_id:
            speaker = _clean_name(next(g for g in self_id.groups() if g))
            if speaker:
                flush()
                current_speaker, current_lines = speaker, [stripped]
                continue

        current_lines.append(stripped)

    flush()
    return segments


def build_travelers(text: str) -> List[Dict[str, Any]]:
    """Extract per-traveler fact bundles from speaker-attributed segments.

    Runs the intent extractor per segment and binds the personal facts
    (constraints, meals, occasion, preferences) to the segment speaker.
    Group-level facts (budget, window, party size) are NOT copied into
    travelers — they stay packet-level.
    """
    travelers: List[Dict[str, Any]] = []
    seen: Dict[str, Dict[str, Any]] = {}

    for segment in extract_speaker_segments(text):
        speaker = segment.get("speaker")
        if not speaker:
            continue
        intent = _extract_trip_intent(segment["text"])
        entry = seen.get(speaker)
        if entry is None:
            entry = {"name": speaker, "constraints": [], "meal_preferences": None,
                     "preferences": [], "occasion": None}
            seen[speaker] = entry
            travelers.append(entry)

        for constraint in intent.get("hard_constraints") or []:
            if constraint not in entry["constraints"]:
                entry["constraints"].append(constraint)
        if intent.get("meal_preferences") and not entry["meal_preferences"]:
            entry["meal_preferences"] = intent["meal_preferences"]
        for pref in intent.get("soft_preferences") or []:
            if len(pref.split()) >= 2 and pref not in entry["preferences"]:
                entry["preferences"].append(pref)
        if intent.get("occasion") and not entry["occasion"]:
            entry["occasion"] = intent["occasion"]

    return travelers
