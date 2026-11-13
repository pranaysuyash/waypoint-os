"""Regression tests for Intelligence section backend improvements."""

from __future__ import annotations

from types import SimpleNamespace

from spine_api.routers import analytics, rag


def test_analytics_snapshot_cache_coalesces_unpatched_readers_and_clears(monkeypatch):
    analytics.clear_analytics_snapshot_cache()
    calls = {"count": 0}

    def fake_reader(*, agency_id: str, limit: int = 500, offset: int = 0):
        calls["count"] += 1
        if offset > 0:
            return []
        return [{"id": f"trip-{agency_id}-1", "status": "new"}]

    monkeypatch.setattr(analytics, "_UNPATCHED_LIST_TRIPS", fake_reader)
    first = analytics._all_agency_records(fake_reader, "agency-1")
    second = analytics._all_agency_records(fake_reader, "agency-1")
    assert len(first) == 1
    assert len(second) == 1
    assert calls["count"] == 1

    analytics.clear_analytics_snapshot_cache()
    third = analytics._all_agency_records(fake_reader, "agency-1")
    assert len(third) == 1
    assert calls["count"] == 2


def test_analytics_snapshot_cache_bypasses_patched_readers():
    analytics.clear_analytics_snapshot_cache()
    calls = {"count": 0}

    def patched_reader(*, agency_id: str, limit: int = 500, offset: int = 0):
        calls["count"] += 1
        return [{"id": "trip-patched"}]

    analytics._all_agency_records(patched_reader, "agency-1")
    analytics._all_agency_records(patched_reader, "agency-1")
    assert calls["count"] == 2


def test_rag_delete_document_scopes_to_agency(tmp_path):
    from src.rag.models import DocumentSourceType
    from src.rag.service import RAGService

    service = RAGService(db_path=str(tmp_path / "rag_test.db"))
    service.index_document(
        document_id="doc-1",
        agency_id="agency-a",
        source_type=DocumentSourceType.AGENCY_POLICY,
        title="Margin Policy",
        text="Quotes above $25,000 require senior review.",
    )
    agency_a = SimpleNamespace(id="agency-a")
    deleted = rag.delete_document("doc-1", agency=agency_a, rag=service)
    assert deleted["status"] == "deleted"
    assert deleted["chunks_deleted"] >= 1
    assert service.store.list_documents("agency-a") == []
