from __future__ import annotations

from tools import runtime_smoke_matrix


def test_local_stack_preflight_checks_backend_and_frontend(monkeypatch, capsys):
    calls: list[str] = []

    def fake_request_status(_opener, url: str) -> tuple[int, str]:
        calls.append(url)
        return 200, "ok"

    monkeypatch.setattr(runtime_smoke_matrix, "request_status", fake_request_status)

    assert runtime_smoke_matrix.run_local_stack_preflight() is True
    assert calls == [
        "http://127.0.0.1:8000/health",
        "http://127.0.0.1:3000/overview",
    ]
    assert "backend health: 200 OK" in capsys.readouterr().out


def test_local_stack_preflight_fails_closed(monkeypatch, capsys):
    def fake_request_status(_opener, url: str) -> tuple[int, str]:
        if url.endswith(":8000/health"):
            return 503, "backend warming up"
        return 200, "ok"

    monkeypatch.setattr(runtime_smoke_matrix, "request_status", fake_request_status)

    assert runtime_smoke_matrix.run_local_stack_preflight() is False
    output = capsys.readouterr().out
    assert "backend health: 503 FAIL" in output
    assert "frontend health: 200 OK" in output
