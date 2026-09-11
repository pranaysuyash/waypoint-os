"""
tests/test_fnd0267_attachment_hardening.py — ISS-010 / FND-0267 (2026-09-11).

Hardening of the TS-03 S1 inbound-attachment surface:
- Real caps: 3 MiB per attachment, 3.5 MiB decoded total — the documented
  5×5 MiB envelope was unreachable under the 5 MB ASGI body cap.
- Magic-byte verification: declared mime must match actual content.
- Tombstone delete + retention purge in document storage (bytes must be able
  to leave the disk; "soft-delete that keeps everything forever" was a lie).
"""

import base64
import os
import time

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"


# --- envelope caps and content verification ---------------------------------


def _png_bytes(size: int = 64) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * (size - 8)


def _jpeg_bytes(size: int = 64) -> bytes:
    return b"\xff\xd8\xff" + b"\x00" * (size - 3)


def _pdf_bytes(size: int = 64) -> bytes:
    return b"%PDF-1.7\n" + b"\x00" * (size - 9)


def _make_attachment(kind="image", mime="image/png", data=None, filename="quote.png"):
    from spine_api.contract import InboundAttachment

    return InboundAttachment(
        kind=kind,
        mime=mime,
        filename=filename,
        data_b64=base64.b64encode(data if data is not None else _png_bytes()).decode(),
    )


def test_per_attachment_cap_is_three_mib():
    """A single attachment over 3 MiB decoded is rejected (fits the 5 MB body cap)."""
    from spine_api.contract import InboundAttachment, _INBOUND_ATTACHMENT_MAX_BYTES

    assert _INBOUND_ATTACHMENT_MAX_BYTES == 3 * 1024 * 1024
    with pytest.raises(Exception, match="exceeds"):
        InboundAttachment(
            kind="image",
            mime="image/png",
            data_b64=base64.b64encode(_png_bytes(3 * 1024 * 1024 + 1)).decode(),
        )


def test_total_attachment_cap_is_three_point_five_mib():
    """The per-inquiry decoded total is capped at 3.5 MiB."""
    from spine_api.contract import (
        InboundInquiryRequest,
        _INBOUND_ATTACHMENTS_TOTAL_MAX_BYTES,
    )

    assert _INBOUND_ATTACHMENTS_TOTAL_MAX_BYTES == 3584 * 1024
    two_mib = _png_bytes(2 * 1024 * 1024)
    atts = [
        _make_attachment(data=two_mib, filename="a.png"),
        _make_attachment(data=two_mib, filename="b.png"),
    ]
    with pytest.raises(Exception, match="total attachment payload"):
        InboundInquiryRequest(channel="manual_paste", raw_text="trip to japan please", attachments=atts)


def test_total_under_cap_is_accepted():
    from spine_api.contract import InboundInquiryRequest

    atts = [
        _make_attachment(data=_png_bytes(1024), filename="a.png"),
        _make_attachment(kind="pdf", mime="application/pdf", data=_pdf_bytes(2048), filename="b.pdf"),
    ]
    req = InboundInquiryRequest(channel="manual_paste", raw_text="trip to japan please", attachments=atts)
    assert len(req.attachments) == 2


def test_magic_byte_mismatch_is_rejected():
    """Declared png carrying jpeg bytes must fail validation."""
    with pytest.raises(Exception, match="magic-byte"):
        _make_attachment(mime="image/png", data=_jpeg_bytes())


def test_declared_pdf_carrying_png_bytes_is_rejected():
    with pytest.raises(Exception, match="magic-byte"):
        _make_attachment(kind="pdf", mime="application/pdf", data=_png_bytes())


def test_valid_magics_pass_for_each_kind():
    _make_attachment(mime="image/png", data=_png_bytes())
    _make_attachment(mime="image/jpeg", data=_jpeg_bytes(), filename="q.jpg")
    _make_attachment(kind="pdf", mime="application/pdf", data=_pdf_bytes(), filename="q.pdf")


def test_envelope_base64_fits_asgi_body_cap():
    """The documented worst case must survive the 5 MB middleware body cap."""
    from spine_api.contract import _INBOUND_ATTACHMENTS_TOTAL_MAX_BYTES

    worst_case_body = len(base64.b64encode(b"\x00" * _INBOUND_ATTACHMENTS_TOTAL_MAX_BYTES))
    assert worst_case_body < 5 * 1024 * 1024


# --- tombstone delete + retention purge -------------------------------------


@pytest.fixture()
def storage(tmp_path):
    from spine_api.services.document_storage import LocalDocumentStorage

    return LocalDocumentStorage(root=tmp_path / "documents")


def _run(coro):
    import asyncio

    return asyncio.get_event_loop().run_until_complete(coro)


def test_delete_tombstones_instead_of_retaining_live_bytes(storage):
    import asyncio

    key = "agency_a/trip_1/att_x.png"
    asyncio.run(storage.put(key, _png_bytes()))
    assert asyncio.run(storage.delete(key)) is True

    # Live bytes are gone from the live namespace...
    with pytest.raises(FileNotFoundError):
        asyncio.run(storage.get(key))

    # ...and the tombstone artifact exists for the retention purge.
    tombstones = list(storage.root.rglob("*.tombstone"))
    assert len(tombstones) == 1


def test_delete_missing_key_returns_false(storage):
    import asyncio

    assert asyncio.run(storage.delete("agency_a/trip_1/never_existed.png")) is False


def test_purge_removes_only_aged_tombstones(storage):
    import asyncio

    from spine_api.services.document_storage import purge_tombstoned_documents

    old_key = "agency_a/trip_1/att_old.png"
    new_key = "agency_a/trip_2/att_new.png"
    asyncio.run(storage.put(old_key, _png_bytes()))
    asyncio.run(storage.put(new_key, _png_bytes()))
    asyncio.run(storage.delete(old_key))
    asyncio.run(storage.delete(new_key))

    # Age only the first tombstone beyond the retention window.
    old_tombstone = next(storage.root.rglob("att_old.png.tombstone"))
    aged = time.time() - (8 * 24 * 3600)
    os.utime(old_tombstone, (aged, aged))

    purged = purge_tombstoned_documents(root=storage.root, older_than_hours=7 * 24)
    assert purged == 1
    assert not old_tombstone.exists()
    assert next(storage.root.rglob("att_new.png.tombstone"), None) is not None


def test_purge_noop_without_tombstones(storage):
    from spine_api.services.document_storage import purge_tombstoned_documents

    assert purge_tombstoned_documents(root=storage.root) == 0
