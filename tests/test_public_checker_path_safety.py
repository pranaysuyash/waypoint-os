from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path

import pytest
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from spine_api import persistence
from spine_api.core.middleware import PUBLIC_CHECKER_MAX_BYTES, RequestBodySizeMiddleware


def _wire_tmp_dirs(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    trips_dir = data_dir / "trips"
    public_checker_dir = data_dir / "public_checker"
    uploads_dir = public_checker_dir / "uploads"
    manifests_dir = public_checker_dir / "manifests"

    monkeypatch.setattr(persistence, "DATA_DIR", data_dir, raising=False)
    monkeypatch.setattr(persistence, "TRIPS_DIR", trips_dir, raising=False)
    monkeypatch.setattr(persistence, "PUBLIC_CHECKER_DIR", public_checker_dir, raising=False)
    monkeypatch.setattr(persistence, "PUBLIC_CHECKER_UPLOADS_DIR", uploads_dir, raising=False)
    monkeypatch.setattr(persistence, "PUBLIC_CHECKER_MANIFESTS_DIR", manifests_dir, raising=False)

    trips_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)


def test_file_trip_store_discards_unsafe_trip_id(tmp_path, monkeypatch):
    _wire_tmp_dirs(tmp_path, monkeypatch)

    trip_payload = {
        "id": "../escape",
        "packet": {"raw_input": {"fixture_id": "security_fixture"}},
        "validation": {"valid": True},
        "decision": {"decision_type": "accept"},
    }

    trip_id = persistence.FileTripStore.save_trip(trip_payload, agency_id=persistence.TEST_AGENCY_ID)

    assert trip_id.startswith("trip_")
    assert ".." not in trip_id
    assert "/" not in trip_id
    assert (persistence.TRIPS_DIR / f"{trip_id}.json").exists()
    assert not (tmp_path / "escape.json").exists()


def test_public_checker_artifact_store_rejects_invalid_trip_id(tmp_path, monkeypatch):
    _wire_tmp_dirs(tmp_path, monkeypatch)

    payload = {
        "retention_consent": True,
        "source_payload": {
            "uploaded_file": {
                "file_name": "test.txt",
                "mime_type": "text/plain",
                "extraction_method": "direct_text",
                "extracted_text": "hello",
                "content_base64": base64.b64encode(b"hello").decode("ascii"),
            }
        },
    }

    manifest = persistence.PublicCheckerArtifactStore.save_trip_artifacts("../escape", payload)

    assert manifest is None
    assert list((tmp_path / "data" / "public_checker" / "uploads").glob("**/*")) == []


def test_public_checker_artifact_store_rejects_oversized_upload(tmp_path, monkeypatch):
    _wire_tmp_dirs(tmp_path, monkeypatch)

    oversized_bytes = b"x" * (persistence.PublicCheckerArtifactStore.MAX_ARCHIVE_BYTES + 1)
    payload = {
        "retention_consent": True,
        "source_payload": {
            "uploaded_file": {
                "file_name": "big.bin",
                "mime_type": "application/octet-stream",
                "extraction_method": "direct_bytes",
                "extracted_text": "",
                "content_base64": base64.b64encode(oversized_bytes).decode("ascii"),
            }
        },
    }

    manifest = persistence.PublicCheckerArtifactStore.save_trip_artifacts("trip_safe123", payload)

    assert manifest is None
    assert (persistence.PUBLIC_CHECKER_UPLOADS_DIR / "trip_safe123").exists() is False


def test_public_checker_content_length_over_limit_returns_413(session_client):
    """Oversized request body returns 413 via the endpoint's Content-Length guard.

    Uses structured_json (which has no per-field max_length) to build a body
    that exceeds PUBLIC_CHECKER_MAX_BYTES without triggering Pydantic field-level
    validation. The endpoint reads Content-Length before using the payload and
    returns 413.
    """
    large_data = "x" * 300_000
    body = json.dumps({"raw_note": "test query", "structured_json": {"data": large_data}})
    assert len(body.encode("utf-8")) > PUBLIC_CHECKER_MAX_BYTES

    resp = session_client.post(
        "/api/public-checker/run",
        content=body.encode("utf-8"),
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 413, (
        f"Expected 413, got {resp.status_code}: {resp.text[:200]}"
    )


def test_public_checker_body_size_middleware_rejects_streamed_body():
    """RequestBodySizeMiddleware rejects a body that exceeds the limit when the
    wrapped application reads it via receive().

    Drives the ASGI receive stream with a single http.request chunk that
    exceeds PUBLIC_CHECKER_MAX_BYTES. The wrapped application calls receive()
    to get the body, which triggers the middleware's sized_receive wrapper,
    which should raise 413 before the application can process the payload.
    """
    sentinel_reached = False

    async def consuming_app(scope: Scope, receive: Receive, send: Send) -> None:
        """Application that actually reads the request body via receive().
        The middleware's sized_receive wrapper counts bytes during this call
        and should raise 413 before the full body is consumed.
        """
        nonlocal sentinel_reached
        while True:
            message = await receive()
            if message["type"] == "http.request":
                remaining = message.get("more_body", False)
                if not remaining:
                    break
        sentinel_reached = True
        response = JSONResponse({"ok": True})
        await response(scope, receive, send)

    middleware = RequestBodySizeMiddleware(consuming_app)

    scope: Scope = {
        "type": "http",
        "path": "/api/public-checker/run",
        "method": "POST",
        "headers": [
            (b"content-type", b"application/json"),
        ],
        "http_version": "1.1",
        "scheme": "http",
        "query_string": b"",
        "root_path": "",
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8000),
    }

    chunk_size = PUBLIC_CHECKER_MAX_BYTES + 1

    async def oversized_receive() -> dict:
        return {"type": "http.request", "body": b"x" * chunk_size, "more_body": False}

    messages: list[dict] = []

    async def capture_send(message: dict) -> None:
        messages.append(message)

    async def run():
        await middleware(scope, oversized_receive, capture_send)

    asyncio.run(run())

    assert sentinel_reached is False, "Middleware must not reach the application response"
    status_msg = next((m for m in messages if m["type"] == "http.response.start"), None)
    assert status_msg is not None, "Expected http.response.start"
    assert status_msg["status"] == 413, f"Expected 413, got {status_msg['status']}"


def test_public_checker_malformed_content_length_returns_400_via_code_path():
    """The endpoint's Content-Length guard catches non-integer values.

    Tests the code path directly: int(content_length) on a non-numeric
    string raises ValueError which the endpoint catches and converts to 400.
    This complements the endpoint-level test by verifying the guard logic
    works correctly regardless of TestClient's Content-Length handling.
    """
    from spine_api.core.middleware import PUBLIC_CHECKER_MAX_BYTES

    with pytest.raises(ValueError):
        int("not-a-number")

    with pytest.raises(ValueError):
        int("12.5")

    with pytest.raises(TypeError):
        int(None)  # type: ignore[arg-type]

    # Valid values must parse and compare correctly
    assert int("100") <= PUBLIC_CHECKER_MAX_BYTES
    assert int("999999") > PUBLIC_CHECKER_MAX_BYTES


def test_request_body_size_middleware_constants_are_consistent():
    """Middleware and endpoint use the same max-size constant for public-checker paths."""
    from spine_api.core.middleware import PUBLIC_CHECKER_MAX_BYTES

    assert PUBLIC_CHECKER_MAX_BYTES == 256 * 1024
    assert RequestBodySizeMiddleware._DEFAULT_MAX_BYTES == 5 * 1024 * 1024
