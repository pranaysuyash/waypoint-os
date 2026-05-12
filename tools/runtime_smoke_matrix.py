#!/usr/bin/env python3
"""Authenticated runtime smoke matrix for Waypoint local stack.

Verifies key BFF/page routes with a real login session and returns non-zero on
any contract failure.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import http.client
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    name: str
    path: str
    expected_status: int = 200


@dataclass(frozen=True)
class HealthCheck:
    name: str
    url: str
    expected_status: int = 200


LOCAL_STACK_HEALTH_CHECKS = (
    HealthCheck("backend health", "http://127.0.0.1:8000/health"),
    HealthCheck("frontend health", "http://127.0.0.1:3000/overview"),
)


def build_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def request_json(opener: urllib.request.OpenerDirector, url: str, payload: dict) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req, timeout=20) as res:
            return int(res.getcode()), res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return int(e.code), e.read().decode("utf-8", errors="replace")


def request_status(opener: urllib.request.OpenerDirector, url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with opener.open(req, timeout=20) as res:
            return int(res.getcode()), res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return int(e.code), e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return 0, str(e)
    except http.client.RemoteDisconnected as e:
        return 0, str(e)


def run_local_stack_preflight() -> bool:
    ok = True
    opener = build_opener()
    for check in LOCAL_STACK_HEALTH_CHECKS:
        status, body = request_status(opener, check.url)
        passed = status == check.expected_status
        print(f"{check.name}: {status} {'OK' if passed else 'FAIL'}")
        if not passed:
            ok = False
            if body:
                print(f"  body: {body[:500]}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Run authenticated runtime smoke checks")
    parser.add_argument("--base", default="http://localhost:3000", help="frontend base URL")
    parser.add_argument("--email", default="newuser@test.com")
    parser.add_argument("--password", default="testpass123")
    parser.add_argument(
        "--preflight-local-stack",
        action="store_true",
        help="verify local backend/frontend health before the authenticated smoke matrix",
    )
    args = parser.parse_args()

    if args.preflight_local_stack and not run_local_stack_preflight():
        return 1

    opener = build_opener()
    login_url = urllib.parse.urljoin(args.base, "/api/auth/login")
    code, body = request_json(opener, login_url, {"email": args.email, "password": args.password})
    if code != 200:
        print(f"login: {code} FAIL")
        print(body[:500])
        return 1
    print("login: 200 OK")

    checks = [
        Check("auth/me", "/api/auth/me"),
        Check("overview page", "/overview"),
        Check("workbench safety page", "/workbench?draft=new&tab=safety"),
        Check("api/inbox", "/api/inbox?page=1&limit=1"),
        Check("api/trips workspace", "/api/trips?view=workspace&limit=5"),
        Check("api/reviews", "/api/reviews?status=pending"),
        Check("api/inbox/stats", "/api/inbox/stats"),
        Check("api/pipeline", "/api/pipeline"),
    ]

    failed = []
    for check in checks:
        url = urllib.parse.urljoin(args.base, check.path)
        status, response_body = request_status(opener, url)
        ok = status == check.expected_status
        print(f"{check.name}: {status} {'OK' if ok else 'FAIL'}")
        if not ok:
            failed.append((check.name, status, response_body[:500]))

    if failed:
        print("\nFailures:")
        for name, status, snippet in failed:
            print(f"- {name}: status={status}")
            if snippet:
                print(f"  body: {snippet}")
        return 1

    print("\nSmoke matrix passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
