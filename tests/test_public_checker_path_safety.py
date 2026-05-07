from __future__ import annotations

import base64
from pathlib import Path

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

    trip_id = persistence.FileTripStore.save_trip(trip_payload, agency_id="d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b")

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
