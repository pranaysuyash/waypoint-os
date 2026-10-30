#!/usr/bin/env python3
"""TinyFish research-sweep runner — reusable CLI for login-walled source sweeps.

Wraps the TinyFish agentic-browser automation endpoint (run-sse) with the same
discipline as the verified prototype (/Users/pranay/Projects/TinyFish-Experiments/run_first_test.py):
stdlib-only, API key read from /Users/pranay/Projects/.env.local and never
logged, evidence written as JSONL before any retry could occur.

Safety boundaries — this tool does two network things and both are guarded:
  1. It hands a start URL to the TinyFish automation service, whose browser
     fetches it. That URL must be https, on the research-host allowlist, and
     never a literal/internal address (validate_target_url).
  2. It POSTs to the fixed ENDPOINT itself. That fetch pins DNS resolution
     (refuses non-global addresses, blocking rebinding toward private space)
     and disables redirect following.

Usage:
  python3 tools/tinyfish_sweep.py \
    --url "https://www.youtube.com/results?search_query=TBEX+AI+travel+agent" \
    --goal "Extract the top 10 video titles, channels, view counts, and upload dates. Return as JSON." \
    --out Docs/sims/assets/tinyfish_youtube_2026-10-27.jsonl \
    --max-seconds 420

Output: writes every SSE event (one JSON object per line) to --out as it
arrives, then prints a compact digest (event count, terminal statuses, and
the extracted payload when the automation returns one).
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ENV_FILE = Path("/Users/pranay/Projects/.env.local")

ENDPOINT_HOST = "agent.tinyfish.ai"
ENDPOINT = f"https://{ENDPOINT_HOST}/v1/automation/run-sse"

# Research sources this sweep tool is for. Extend deliberately, never widely.
ALLOWED_HOST_SUFFIXES = (
    "youtube.com",
    "facebook.com",
    "reddit.com",
    "x.com",
    "twitter.com",
    "apps.apple.com",
    "play.google.com",
    "bing.com",
    "google.com",
    "duckduckgo.com",
)


def read_api_key() -> str:
    """Read only the TINYFISH_API_KEY assignment; never echo or log its value."""
    found: list[str] = []
    try:
        with ENV_FILE.open("r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if line.startswith("export "):
                    line = line[7:].lstrip()
                name, separator, value = line.partition("=")
                if separator and name.strip() == "TINYFISH_API_KEY":
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                        value = value[1:-1]
                    found.append(value)
    except OSError:
        raise SystemExit("Could not read .env.local; no request was sent.")
    if len(found) != 1 or not found[0]:
        raise SystemExit("Set exactly one non-empty TINYFISH_API_KEY line in .env.local; no request was sent.")
    return found[0]


def _reject_internal_host(host: str) -> None:
    """Refuse hostnames and literal addresses that could name internal space."""
    normalized = (host or "").lower().rstrip(".")
    if not normalized:
        raise SystemExit("URL has no hostname.")
    try:
        addr = ipaddress.ip_address(normalized)
    except ValueError:
        addr = None
    if addr is not None and not addr.is_global:
        raise SystemExit(f"Literal non-global address {addr} is not allowed.")
    if normalized in {"localhost", "localhost.localdomain"} or normalized.endswith(".local") or normalized.endswith(".internal"):
        raise SystemExit(f"Internal hostname {normalized} is not allowed.")


def validate_target_url(url: str) -> None:
    """Reject anything that is not a public https research URL.

    The URL is sent to a third-party automation service whose browser will
    fetch it, so internal destinations must be refused here, at the only
    boundary this tool controls.
    """
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise SystemExit("Only https:// start URLs are allowed.")
    if parts.username or parts.password or (parts.port not in (None, 443)):
        raise SystemExit("URL must not carry credentials or a non-default port.")
    host = (parts.hostname or "").lower()
    _reject_internal_host(host)
    if not any(host == s or host.endswith("." + s) for s in ALLOWED_HOST_SUFFIXES):
        raise SystemExit(
            f"Host {host} is not on the research allowlist ({', '.join(ALLOWED_HOST_SUFFIXES)}). "
            "Extend ALLOWED_HOST_SUFFIXES deliberately if this is a new research source."
        )


def validate_endpoint() -> None:
    """Pin our own outbound request target before any bytes are sent."""
    parts = urlsplit(ENDPOINT)
    if parts.scheme != "https" or parts.hostname != ENDPOINT_HOST:
        raise SystemExit("Endpoint definition mismatch; refusing to send.")
    _reject_internal_host(parts.hostname or "")
    try:
        infos = socket.getaddrinfo(parts.hostname, 443, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise SystemExit(f"DNS resolution failed for {parts.hostname}; refusing to send ({exc}).")
    resolved = {info[4][0] for info in infos}
    for address in resolved:
        if not ipaddress.ip_address(address).is_global:
            raise SystemExit(f"{parts.hostname} resolves to non-global address {address}; refusing to send.")


class _NoRedirects(HTTPRedirectHandler):
    """Treat any redirect of the SSE POST as an error instead of following it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102 - urllib contract
        return None


def _extract_payloads(events: list[dict]) -> list[str]:
    """Pull result-ish text out of SSE events for the terminal digest.

    TinyFish event shapes have varied across runs (result / data / message
    fields); scan shallowly for string payloads rather than pinning one key.
    """
    payloads: list[str] = []
    for event in events:
        for key in ("result", "data", "output", "content", "message", "text"):
            value = event.get(key)
            if isinstance(value, str) and len(value) > 40 and key != "raw_data":
                payloads.append(value)
                break
            if isinstance(value, dict):
                payloads.append(json.dumps(value, ensure_ascii=False))
                break
    return payloads


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--url", required=True, help="Start URL for the browser automation")
    parser.add_argument("--goal", required=True, help="Natural-language goal for the agent")
    parser.add_argument("--out", required=True, help="Evidence JSONL path (must not exist)")
    parser.add_argument("--max-seconds", type=int, default=420, help="Agent budget in seconds")
    args = parser.parse_args()

    validate_target_url(args.url)
    validate_endpoint()

    out_path = Path(args.out)
    if out_path.exists():
        raise SystemExit(f"Evidence file already exists at {out_path}; inspect run history before any retry.")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    api_key = read_api_key()
    payload = {
        "url": args.url,
        "goal": args.goal,
        "agent_config": {"max_duration_seconds": args.max_seconds},
    }
    request = Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )
    del api_key

    events: list[dict] = []
    try:
        opener = build_opener(_NoRedirects())
        with out_path.open("x", encoding="utf-8") as output, opener.open(request, timeout=args.max_seconds + 120) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                if not line.startswith("data:"):
                    continue
                data = line[5:].lstrip()
                if not data:
                    continue
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    event = {"raw_data": data}
                events.append(event)
                output.write(json.dumps(event, ensure_ascii=False) + "\n")
                output.flush()
    except HTTPError as exc:
        print(f"TinyFish returned HTTP {exc.code}; body not logged. No retry attempted.", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, OSError) as exc:
        print(f"Request outcome may be uncertain ({type(exc).__name__}). No retry attempted; check run history.", file=sys.stderr)
        return 1

    statuses = [str(e.get("status") or e.get("type") or "?") for e in events]
    print(f"events={len(events)} statuses_tail={statuses[-5:]}")
    digests = _extract_payloads(events)
    if digests:
        print("--- extracted payload (last) ---")
        print(digests[-1][:4000])
    else:
        print("no embedded payload found; inspect the JSONL evidence file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
