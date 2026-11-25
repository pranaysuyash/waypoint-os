"""Compare the current destination extractor with a bounded OpenAI probe on fictional inputs."""

import argparse
import json
import os
import time

import requests

from spine_api.core.env import load_project_env
from src.intake.extractors import _extract_destination_candidates

MODEL = "gpt-4.1-mini-2025-04-14"
CASES = (
    ("transit_and_hotel", "Flying to Dubai via Istanbul. Staying at Atlantis The Royal.", ["Dubai"], ["Istanbul"]),
    ("overnight", "Doha 23:55 to Istanbul 01:10 next day. Separate tickets; staying in Istanbul.", ["Istanbul"], []),
    ("two_stays", "Three nights in Kyoto and two nights in Osaka, connecting via Seoul.", ["Kyoto", "Osaka"], ["Seoul"]),
    ("unknown", "Two adults in November, hotel and flights still undecided.", [], []),
)
FIELDS = ("destinations", "explicit_connections")
ENTRY = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "evidence": {"type": "string"}},
    "required": ["name", "evidence"],
    "additionalProperties": False,
}
SCHEMA = {
    "type": "object",
    "properties": {field: {"type": "array", "items": ENTRY} for field in FIELDS},
    "required": list(FIELDS),
    "additionalProperties": False,
}


def run_openai(key: str, note: str, destinations: list[str], connections: list[str]) -> dict:
    started = time.monotonic()
    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": MODEL,
                "store": False,
                "instructions": (
                    "Extract explicitly visited cities and cities explicitly identified as connections. "
                    "Do not infer connections from routes or treat hotels as cities. "
                    "Quote exact supporting text spans. Abstain with empty arrays if unknown."
                ),
                "input": note,
                "max_output_tokens": 400,
                "text": {"format": {"type": "json_schema", "name": "trip_facts", "strict": True, "schema": SCHEMA}},
            },
            timeout=30,
        )
        result = response.json()
        if not response.ok:
            return {"http_status": response.status_code, "error_code": result.get("error", {}).get("code")}
        content = next(
            entry["text"] for item in result["output"] for entry in item.get("content", [])
            if entry.get("type") == "output_text"
        )
        parsed = json.loads(content)
        names = {field: sorted(item["name"] for item in parsed[field]) for field in FIELDS}
        return {
            "response_model": result["model"],
            "roles_correct": names["destinations"] == sorted(destinations)
            and names["explicit_connections"] == sorted(connections),
            "exact_spans": all(
                entry["evidence"] and entry["evidence"] in note
                for field in FIELDS for entry in parsed[field]
            ),
            **names,
            "usage": result.get("usage"),
            "latency_seconds": round(time.monotonic() - started, 2),
        }
    except (requests.RequestException, ValueError, KeyError, StopIteration) as error:
        return {"error_type": type(error).__name__}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openai", action="store_true", help="Send only the four built-in fictional cases to OpenAI.")
    arguments = parser.parse_args()
    if arguments.openai:
        load_project_env()
    key = os.getenv("OPENAI_API_KEY") if arguments.openai else None
    if arguments.openai and not key:
        parser.error("OPENAI_API_KEY is required for the provider lane.")

    failed = False
    for case_id, note, destinations, connections in CASES:
        baseline, _, _ = _extract_destination_candidates(note)
        result = {
            "case": case_id,
            "baseline": baseline,
            "expected_destinations": destinations,
            "baseline_destinations_correct": sorted(baseline) == sorted(destinations),
        }
        if key:
            provider = run_openai(key, note, destinations, connections)
            result["openai"] = provider
            if provider.get("http_status") in {401, 403}:
                key = None
            failed |= not (provider.get("roles_correct") and provider.get("exact_spans"))
        print(json.dumps(result))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
