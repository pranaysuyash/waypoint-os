"""WOBS 2026-09-09 P1 — Ghost Hotel Test (entity-existence advisory checks).

Pure-logic + injected-transport tests; no network. The design contract under
test: advisory-only findings (fail OPEN), conservative extraction, Nominatim
usage policy (1 req/s, User-Agent), call-time env kill switch, per-run cap.
"""

from __future__ import annotations

import json
import urllib.parse

import pytest

from src.public_checker import entity_checks as ec
from src.public_checker.entity_checks import (
    EntityCheckResult,
    entity_checks_enabled,
    extract_lodging_names,
    run_entity_checks,
    verify_entity,
)


@pytest.fixture(autouse=True)
def _isolated_module_state(monkeypatch: pytest.MonkeyPatch):
    """Reset module-level cache + rate-limiter clock between tests."""
    monkeypatch.setattr(ec, "_cache", {})
    monkeypatch.setattr(ec, "_last_request_at", 0.0)


def _nominatim_payload(results: list) -> str:
    return json.dumps(results)


def _fake_transport(pages: dict[str, list], seen: list[str] | None = None):
    def transport(url: str):
        if seen is not None:
            seen.append(url)
        path = url.split("?")[0]
        key = [k for k in pages if path.endswith(k)]
        if not key:
            raise AssertionError(f"unexpected url: {url}")
        return json.loads(_nominatim_payload(pages[key[0]]))

    return transport


def _hotel_hit(name: str) -> dict:
    return {
        "class": "tourism",
        "type": "hotel",
        "display_name": f"{name}, Marina District, Singapore",
    }


class TestExtraction:
    def test_extracts_checkin_and_prefix_and_suffix_forms(self):
        text = (
            "Day 1: check-in at Taj Palace Hotel. Day 2: staying at The Orchid Resort. "
            "Day 3: Hotel Blue Bay, then the museum."
        )
        names = [n.lower() for n in extract_lodging_names(text)]
        assert any("taj palace" in n for n in names)
        assert any("orchid" in n for n in names)
        assert any("blue bay" in n for n in names)

    def test_ignores_non_lodging_sentences(self):
        assert extract_lodging_names("Visit the museum and Try the street food at night.") == []

    def test_ignores_bare_keywords_and_lowercase_noise(self):
        assert extract_lodging_names("hotel is nice. resort something something.") == []

    def test_empty_text_safe(self):
        assert extract_lodging_names("") == []


class TestVerifyEntity:
    def test_verified_when_lodging_record_exists(self):
        transport = _fake_transport({"/search": [_hotel_hit("Taj Palace")]})
        result = verify_entity("Taj Palace", "Singapore", transport=transport)
        assert result.status == "verified"
        assert result.confidence >= 0.5
        assert "Taj Palace" in result.message

    def test_not_found_is_advisory_not_accusatory(self):
        transport = _fake_transport({"/search": []})
        result = verify_entity("Hotel Falkoria", "Tokyo", transport=transport)
        assert result.status == "not_found"
        assert "double-check" in result.message.lower()
        assert "does not exist" not in result.message.lower()
        assert "fake" not in result.message.lower()

    def test_place_but_not_lodging_is_unverified_weak(self):
        transport = _fake_transport({"/search": [{"class": "amenity", "type": "restaurant", "display_name": "X"}]})
        result = verify_entity("The Orchid", "Paris", transport=transport)
        assert result.status == "unverified"
        assert "verify your booking" in result.message

    def test_network_error_fails_open(self):
        def boom(url):
            raise OSError("network down")

        result = verify_entity("Hotel X", "Rome", transport=boom)
        assert result.status == "unverified"
        assert result.confidence == 0.0

    def test_user_agent_and_query_shape(self):
        seen: list[str] = []
        transport = _fake_transport({"/search": [_hotel_hit("Taj Palace")]}, seen)
        verify_entity("Taj Palace", "Singapore", transport=transport)
        url = seen[0]
        assert "nominatim" in url or "NOMINATIM" in url.upper()
        params = urllib.parse.parse_qs(url.split("?")[1])
        assert params["format"] == ["jsonv2"]
        assert "Taj" in params["q"][0]

    def test_base_url_env_respected(self, monkeypatch: pytest.MonkeyPatch):
        seen: list[str] = []
        transport = _fake_transport({"/search": [_hotel_hit("Taj Palace")]}, seen)
        monkeypatch.setenv("NOMINATIM_BASE_URL", "https://nominatim.example.org/")
        verify_entity("Taj Palace", "Singapore", transport=transport)
        assert seen[0].startswith("https://nominatim.example.org/search?")


class TestRunEntityChecks:
    def test_runs_extraction_to_verification(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("ENTITY_CHECK_ENABLED", raising=False)
        transport = _fake_transport({"/search": [_hotel_hit("Taj Palace")]})
        results = run_entity_checks(
            "Day 1: check-in at Taj Palace Hotel.", city="Singapore", transport=transport
        )
        assert len(results) == 1
        assert results[0].status == "verified"

    def test_kill_switch_disables(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("ENTITY_CHECK_ENABLED", "0")

        def bomb(url):
            raise AssertionError("must not be called when disabled")

        assert run_entity_checks("check-in at Taj Palace Hotel", transport=bomb) == []
        assert entity_checks_enabled() is False

    def test_per_run_entity_cap(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("ENTITY_CHECK_ENABLED", raising=False)
        transport = _fake_transport({"/search": [_hotel_hit("Grand Palace")]})
        text = (
            "check-in at Alpha Hotel, stay at Beta Resort, check-in at Gamma Hotel, "
            "stay at Delta Inn, check-in at Epsilon Hotel, stay at Zeta Lodge, check-in at Eta Hotel"
        )
        results = run_entity_checks(text, transport=transport, max_entities=3)
        assert len(results) <= 3

    def test_cache_hits_do_not_refetch(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("ENTITY_CHECK_ENABLED", raising=False)
        seen: list[str] = []
        transport = _fake_transport({"/search": [_hotel_hit("Taj Palace")]}, seen)
        text = "check-in at Taj Palace Hotel"
        first = run_entity_checks(text, city="Singapore", transport=transport)
        second = run_entity_checks(text, city="Singapore", transport=transport)
        assert len(seen) == 1
        assert first == second

    def test_disabled_by_default_when_env_zero(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("ENTITY_CHECK_ENABLED", "false")
        assert entity_checks_enabled() is False

    def test_result_serializable(self):
        result = EntityCheckResult(
            name="X", place_query="X Y", status="verified", confidence=0.7, message="ok"
        )
        assert result.as_dict()["status"] == "verified"
