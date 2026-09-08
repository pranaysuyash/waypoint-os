"""RDA-2026-09-08 FT-05 — public-checker runtime kill switch.

PUBLIC_CHECKER_ENABLED is read at call time (no import-time caching), so
operators can disable the unauthenticated surface without a code deploy and
tests can toggle it with monkeypatch. When disabled, every public-checker
endpoint must fail closed with 503.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from spine_api.routers.public_checker import (
    _require_public_checker_enabled,
    public_checker_enabled,
)


class TestPublicCheckerEnabled:
    def test_enabled_by_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
        assert public_checker_enabled() is True

    def test_zero_disables(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PUBLIC_CHECKER_ENABLED", "0")
        assert public_checker_enabled() is False

    @pytest.mark.parametrize("value", ["false", "False", "no", "off", " 0 "])
    def test_other_falsy_values_disable(self, monkeypatch: pytest.MonkeyPatch, value: str):
        monkeypatch.setenv("PUBLIC_CHECKER_ENABLED", value)
        assert public_checker_enabled() is False

    def test_one_enables(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PUBLIC_CHECKER_ENABLED", "1")
        assert public_checker_enabled() is True

    def test_require_raises_503_when_disabled(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PUBLIC_CHECKER_ENABLED", "0")
        with pytest.raises(HTTPException) as exc_info:
            _require_public_checker_enabled()
        assert exc_info.value.status_code == 503

    def test_require_passes_when_enabled(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PUBLIC_CHECKER_ENABLED", "1")
        _require_public_checker_enabled()
