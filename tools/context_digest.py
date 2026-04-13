#!/usr/bin/env python3
"""Create a structured digest from large exported chat context files.

Usage:
  python tools/context_digest.py --input path/to/context.txt \
      --output-md Docs/context/CONTEXT_DIGEST_YYYY-MM-DD.md \
      --output-json Docs/context/context_digest_YYYY-MM-DD.json
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

THEME_KEYWORDS = {
    "intake_and_discovery": ["intake", "clarification", "discovery", "question", "traveler profile"],
    "constraints_and_feasibility": ["constraint", "feasibility", "realistic", "season", "duration", "budget"],
    "itinerary_design": ["itinerary", "day plan", "route", "schedule", "multi-city"],
    "sourcing_and_research": ["research", "compare", "option", "supplier", "hotel", "flight"],
    "booking_and_operations": ["booking", "confirm", "voucher", "payment", "payout", "ops"],
    "in_trip_support": ["support", "change", "reschedule", "cancel", "emergency", "during trip"],
    "post_trip_and_learning": ["feedback", "review", "learning", "memory", "post trip"],
    "agent_architecture": ["agent", "workflow", "orchestration", "layer", "pipeline", "designated agents"],
}

ACTION_PREFIX = re.compile(r"^\s*(?:[-*]\s+|\d+[.)]\s+)?(?:must|should|need to|create|build|implement|define|add|track|check|run|document)\b", re.IGNORECASE)
PART_HEADER = re.compile(r"^\s*part\s+\d+\s*:\s*$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Digest exported context text files.")
    parser.add_argument("--input", required=True, help="Path to input context .txt")
    parser.add_argument("--output-md", required=True, help="Path to write markdown digest")
    parser.add_argument("--output-json", required=True, help="Path to write JSON digest")
    parser.add_argument("--max-actions", type=int, default=80, help="Maximum action lines to keep")
    return parser.parse_args()


def detect_theme_hits(lines: list[str]) -> dict[str, int]:
    joined = "\n".join(lines).lower()
    scores: dict[str, int] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(joined.count(keyword.lower()) for keyword in keywords)
        scores[theme] = score
    return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))


def extract_actions(lines: list[str], max_actions: int) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()
    for raw in lines:
        line = raw.strip().replace("\ufeff", "")
        if len(line) < 20:
            continue
        if not ACTION_PREFIX.search(line):
            continue
        normalized = re.sub(r"\s+", " ", line)
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        actions.append(normalized)
        if len(actions) >= max_actions:
            break
    return actions


def extract_parts(lines: list[str]) -> list[dict[str, object]]:
    parts: list[dict[str, object]] = []
    current = {"title": "Part 0", "start_line": 1, "preview": []}
    for idx, raw in enumerate(lines, start=1):
        line = raw.strip()
        if PART_HEADER.match(line):
            if current["preview"]:
                parts.append(current)
            current = {"title": line, "start_line": idx, "preview": []}
            continue
        if len(current["preview"]) < 5 and line:
            current["preview"].append(line)
    if current["preview"]:
        parts.append(current)
    return parts


def top_terms(lines: list[str], limit: int = 40) -> list[tuple[str, int]]:
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "are", "you", "your", "trip", "agent", "agents",
        "have", "will", "not", "but", "can", "into", "when", "what", "where", "who", "how", "they", "them",
    }
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", "\n".join(lines).lower())
    freq = collections.Counter(token for token in tokens if token not in stop)
    return freq.most_common(limit)


def render_markdown(
    input_path: Path,
    line_count: int,
    char_count: int,
    parts: list[dict[str, object]],
    themes: dict[str, int],
    actions: list[str],
    terms: list[tuple[str, int]],
) -> str:
    top_themes = [f"- `{name}`: {score}" for name, score in list(themes.items())[:8]]
    part_lines = []
    for part in parts[:20]:
        preview = " ".join(part["preview"])[:260]
        part_lines.append(f"- {part['title']} (line {part['start_line']}): {preview}")

    action_lines = [f"- {a}" for a in actions]
    terms_line = ", ".join(f"`{term}` ({count})" for term, count in terms[:25])

    return "\n".join(
        [
            "# Context Digest",
            "",
            f"Source: `{input_path}`",
            f"Size: {line_count} lines, {char_count} characters",
            "",
            "## Detected Sections",
            *part_lines,
            "",
            "## Theme Strength",
            *top_themes,
            "",
            "## Candidate Action Statements",
            *action_lines,
            "",
            "## Dominant Terms",
            terms_line,
            "",
            "## Notes",
            "- This digest is heuristic and should be used as a navigation aid, not as ground truth.",
            "- Keep the full archived source file for authoritative reference.",
        ]
    )


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    output_md = Path(args.output_md)
    output_json = Path(args.output_json)

    raw = input_path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()

    digest = {
        "source": str(input_path),
        "line_count": len(lines),
        "char_count": len(raw),
        "parts": extract_parts(lines),
        "theme_scores": detect_theme_hits(lines),
        "actions": extract_actions(lines, max_actions=args.max_actions),
        "top_terms": top_terms(lines),
    }

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(digest, indent=2), encoding="utf-8")
    output_md.write_text(
        render_markdown(
            input_path=input_path,
            line_count=digest["line_count"],
            char_count=digest["char_count"],
            parts=digest["parts"],
            themes=digest["theme_scores"],
            actions=digest["actions"],
            terms=digest["top_terms"],
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
