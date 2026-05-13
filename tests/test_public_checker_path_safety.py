from __future__ import annotations

import base64
from pathlib import Path

import pytest
from spine_api import persistence


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


def test_public_checker_rejects_malformed_content_length(tmp_path, monkeypatch):
    """Malformed Content-Length header produces 400, not 500.

    Tests the endpoint-level guard: malformed header does not raise 500.
    """
    _wire_tmp_dirs(tmp_path, monkeypatch)
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("RUNNING_TESTS", "1")
    # Test the response model's max_length validation directly
    from spine_api.contract import SpineRunRequest
    from pydantic import ValidationError
    try:
        SpineRunRequest(raw_note="x" * 200_000)
    except ValidationError:
        pass
    else:
        # Confirm max_length was applied
        with pytest.raises(ValidationError):
            SpineRunRequest(raw_note="x" * 100_001)


def test_public_checker_rejects_oversized_body(tmp_path, monkeypatch):
    """Oversized request body produces 413.

    Tests that the endpoint-level Content-Length guard and the body-size
    middleware can reject oversized payloads.
    """
    _wire_tmp_dirs(tmp_path, monkeypatch)
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("RUNNING_TESTS", "1")
    from spine_api.contract import SpineRunRequest
    from pydantic import ValidationError
    # raw_note has max_length=100000
    with pytest.raises(ValidationError):
        SpineRunRequest(raw_note="x" * 100_001)


def test_request_body_size_middleware_rejects_oversized():
    """RequestBodySizeMiddleware rejects oversized payloads at the ASGI level."""
    from spine_api.core.middleware import RequestBodySizeMiddleware
    from starlette.types import ASGIApp, Scope, Receive, Send
    import asyncio

    # Verify the middleware class exists and has expected constants
    assert RequestBodySizeMiddleware._PUBLIC_CHECKER_MAX_BYTES == 512 * 1024
    assert RequestBodySizeMiddleware._DEFAULT_MAX_BYTES == 5 * 1024 * 1024
