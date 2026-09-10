"""
tests/test_ts03_inbound_attachments.py — TS-03 S1 (2026-09-10): inbound
attachment envelope on /api/v1/inbound/parse.

Contract under test (Docs/exploration/TS03_MULTIMODAL_INTAKE_COMPLETION_2026-09-09.md S1):
- Envelope validation: mime allowlist per kind, base64 validity, 5 MiB size
  cap, max 5 attachments per inquiry.
- Happy path: attachments persisted via the canonical document-storage lane
  (data/documents/{agency}/{trip}/...), manifest recorded on the trip,
  response reports attachments_accepted.
- Attachment bytes participate in idempotency identity (same text + same
  bytes replays; different bytes mints a new trip).
- Storage degradation never fails the parse (trip already saved) — the
  response reports fewer accepted than sent.
"""

import base64
import os

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"


from spine_api import persistence  # noqa: E402

TripStore = persistence.TripStore

AGENCY = "test_agency_ts03"


@pytest.fixture(autouse=True)
def ts03_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    # Route document storage at a temp root so tests never touch real
    # runtime documents.
    from spine_api.services import document_storage

    monkeypatch.setattr(document_storage, "DOCUMENTS_DIR", tmp_path / "documents")
    yield


def _png_bytes(size: int = 64) -> bytes:
    # Minimal valid-ish PNG header + padding; content only needs to be bytes.
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * (size - 8)


def _attachment(kind="image", mime="image/png", data=None, filename="quote.png"):
    from spine_api.contract import InboundAttachment

    return InboundAttachment(
        kind=kind,
        mime=mime,
        filename=filename,
        data_b64=base64.b64encode(data if data is not None else _png_bytes()).decode(),
    )


# --- envelope validation -----------------------------------------------------------


def test_attachment_mime_must_match_kind():
    from spine_api.contract import InboundAttachment

    with pytest.raises(Exception):
        InboundAttachment(
            kind="image", mime="application/pdf",
            data_b64=base64.b64encode(b"x").decode(),
        )
    with pytest.raises(Exception):
        InboundAttachment(
            kind="pdf", mime="image/png",
            data_b64=base64.b64encode(b"x").decode(),
        )
    with pytest.raises(Exception):
        InboundAttachment(
            kind="image", mime="application/zip",
            data_b64=base64.b64encode(b"x").decode(),
        )


def test_attachment_rejects_invalid_base64_and_empty():
    from spine_api.contract import InboundAttachment

    with pytest.raises(Exception):
        InboundAttachment(kind="image", mime="image/png", data_b64="not-base64!!!")
    with pytest.raises(Exception):
        InboundAttachment(kind="image", mime="image/png", data_b64="")


def test_attachment_size_cap():
    from spine_api.contract import InboundAttachment

    big = b"x" * (5 * 1024 * 1024 + 1)
    with pytest.raises(Exception):
        InboundAttachment(
            kind="image", mime="image/png",
            data_b64=base64.b64encode(big).decode(),
        )


def test_request_rejects_more_than_five_attachments():
    from spine_api.contract import InboundInquiryRequest

    atts = [_attachment(filename=f"q{i}.png") for i in range(6)]
    with pytest.raises(Exception):
        InboundInquiryRequest(channel="manual_paste", raw_text="trip to japan please", attachments=atts)


# --- happy path: storage + manifest + response ---------------------------------------


def _parse(client, attachments=(), raw_text="Trip to Japan in October for 4 people, budget 4L"):
    return client.post(
        "/api/v1/inbound/parse",
        headers={"X-Agency-ID": AGENCY},
        json={
            "channel": "manual_paste",
            "raw_text": raw_text,
            "attachments": [
                {
                    "kind": a.kind,
                    "mime": a.mime,
                    "filename": a.filename,
                    "data_b64": a.data_b64,
                }
                for a in attachments
            ],
        },
    )


def test_parse_persists_attachment_and_manifest(session_client, tmp_path):
    data = _png_bytes(128)
    resp = _parse(session_client, attachments=[_attachment(data=data)])
    assert resp.status_code == 200
    body = resp.json()
    assert body["attachments_accepted"] == 1
    trip_id = body["trip_id"]

    trip = TripStore.get_trip_for_agency(trip_id, AGENCY)
    manifest = trip.get("inbound_attachments")
    assert manifest and len(manifest) == 1
    entry = manifest[0]
    assert entry["source"] == "inbound_attachment"
    assert entry["size_bytes"] == len(data)
    # Bytes actually landed in the storage lane under agency/trip scoping
    stored = tmp_path / "documents" / AGENCY / trip_id
    files = list(stored.glob("att_*.png"))
    assert files and files[0].read_bytes() == data


def test_parse_without_attachments_reports_zero(session_client):
    resp = _parse(session_client)
    assert resp.status_code == 200
    assert resp.json()["attachments_accepted"] == 0


def test_attachment_bytes_participate_in_idempotency(session_client):
    a1 = _attachment(data=_png_bytes(100), filename="one.png")
    a2 = _attachment(data=_png_bytes(200), filename="two.png")

    r1 = _parse(session_client, attachments=[a1])
    assert r1.status_code == 200
    # Same text + same bytes -> replay of the same trip
    r2 = _parse(session_client, attachments=[a1])
    assert r2.status_code == 200
    assert r2.json()["trip_id"] == r1.json()["trip_id"]
    # Same text + different bytes -> a new trip (different request identity)
    r3 = _parse(session_client, attachments=[a2])
    assert r3.status_code == 200
    assert r3.json()["trip_id"] != r1.json()["trip_id"]


def test_storage_failure_never_fails_parse(session_client, monkeypatch):
    """Attachment persistence is best-effort post-save: a broken storage
    backend degrades the count, never the parse."""
    from spine_api.services import document_storage

    class _Broken:
        async def put(self, key, data):
            raise OSError("disk full")

    monkeypatch.setattr(document_storage, "get_document_storage", lambda: _Broken())
    resp = _parse(session_client, attachments=[_attachment()])
    assert resp.status_code == 200
    body = resp.json()
    assert body["attachments_accepted"] == 0
    # The trip itself exists
    assert TripStore.get_trip_for_agency(body["trip_id"], AGENCY)
