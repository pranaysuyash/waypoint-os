"""RDA-2026-09-08 FT-08 — proxy-aware rate-limit key.

Behind the deployment proxy (fly.io) the direct peer is the proxy itself, so
the limiter must key on the leftmost X-Forwarded-For entry. Trusting proxy
headers is the default and can be disabled with TRUST_PROXY_HEADERS=0 (then a
spoofed header cannot evade limiting).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from spine_api.core.rate_limiter import _key_func


def _request(headers: dict[str, str] | None = None, client_host: str = "10.0.0.1"):
    return SimpleNamespace(
        headers={k.lower(): v for k, v in (headers or {}).items()},
        client=SimpleNamespace(host=client_host),
    )


class TestKeyFunc:
    def test_leftmost_xff_wins_when_trusted(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
        req = _request({"X-Forwarded-For": "203.0.113.7, 10.0.0.2"})
        assert _key_func(req) == "203.0.113.7"

    def test_single_xff_entry(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
        req = _request({"X-Forwarded-For": "198.51.100.9"})
        assert _key_func(req) == "198.51.100.9"

    def test_trust_disabled_uses_peer(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("TRUST_PROXY_HEADERS", "0")
        req = _request({"X-Forwarded-For": "203.0.113.7"}, client_host="10.0.0.1")
        assert _key_func(req) == "10.0.0.1"

    def test_missing_xff_falls_back_to_peer(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
        req = _request({}, client_host="10.0.0.1")
        assert _key_func(req) == "10.0.0.1"

    def test_blank_xff_entry_falls_back_to_peer(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
        req = _request({"X-Forwarded-For": " , 10.0.0.2"}, client_host="10.0.0.1")
        assert _key_func(req) == "10.0.0.1"
