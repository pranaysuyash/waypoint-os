"""RAG mount tests — router surface, wiring, provider egress discipline.

Covers the 2026-10-22 mount tranche (Docs/exploration/
RAG_EMBEDDINGS_MOUNT_EXPLORATION_2026-10-22.md §5 Option B):

- Router: auth required, caps/clamps, honest errors, status surface,
  tenant isolation on the mounted API.
- Wiring: the frontier specialty hook actually receives the canonical
  process-wide RAG service and the caller's agency id.
- Provider: the semantic embedding lane strips PII before egress and
  emits forensics; failures degrade to the honest hash fallback.

Tier 2 (targeted); no external provider calls — the OpenAI SDK client is
mocked at the seam.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from spine_api.routers import rag as rag_router
from src.rag.service import RAGService


@pytest.fixture
def rag_service(tmp_path):
    return RAGService(db_path=str(tmp_path / "mount_rag.db"))


@pytest.fixture
def client(rag_service):
    app = FastAPI()
    app.include_router(rag_router.router)
    app.dependency_overrides[get_current_agency] = lambda: Agency(
        id="agency_mount", name="Mount Test", slug="mount-test"
    )
    app.dependency_overrides[rag_router.get_rag_service] = lambda: rag_service
    return TestClient(app)


AUTH = {"Authorization": "Bearer test-token"}


def test_router_requires_auth():
    """No agency dependency override → the real get_current_agency rejects."""
    app = FastAPI()
    app.include_router(rag_router.router)
    with TestClient(app, raise_server_exceptions=False) as bare:
        resp = bare.post("/api/v1/rag/query", json={"query": "x"}, headers=AUTH)
        assert resp.status_code in (401, 403)


def test_status_surface_is_truthful(client, rag_service):
    resp = client.get("/api/v1/rag/status", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_semantic"] is False  # hash provider by default — honest
    assert body["embedding_model"] == "md5_word_bucket"
    assert body["agency_chunk_count"] == 0


def test_index_and_query_roundtrip(client, rag_service):
    resp = client.post(
        "/api/v1/rag/documents/index",
        headers=AUTH,
        json={
            "document_id": "advisory_1",
            "source_type": "government_advisory",
            "title": "Japan Visa Advisory",
            "text": "Japan Visa Advisory.\n\nUS passport holders enter Japan visa free for 90 days with a valid passport.",
            "tags": ["japan", "visa"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["chunks_created"] >= 1
    assert body["embedding_model"] == "md5_word_bucket"

    grounded = client.post(
        "/api/v1/rag/query",
        headers=AUTH,
        json={"query": "Can US passport holders enter Japan visa free?", "top_k": 3},
    )
    assert grounded.status_code == 200
    body = grounded.json()
    assert body["is_grounded"] is True
    assert len(body["citations"]) >= 1

    # Lineage row exists, hashed only.
    with rag_service.store._get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM rag_runs WHERE agency_id = ?", ("agency_mount",)
        ).fetchone()
    assert row is not None
    assert len(row["query_sha256"]) == 64


def test_tenant_isolation_on_mounted_api(client, rag_service):
    client.post(
        "/api/v1/rag/documents/index",
        headers=AUTH,
        json={
            "document_id": "secret_1",
            "source_type": "supplier_contract",
            "title": "Agency Mount Rates",
            "text": "Confidential agency mount rates for Phuket villas.",
        },
    )
    # Another agency queries through a client bound to THEIR agency id.
    app = client.app
    app.dependency_overrides[get_current_agency] = lambda: Agency(
        id="agency_other", name="Other", slug="other"
    )
    grounded = client.post(
        "/api/v1/rag/query", headers=AUTH, json={"query": "Phuket villa rates"}
    )
    body = grounded.json()
    assert body["citations"] == []
    assert body["is_grounded"] is False


def test_document_size_cap_rejected(client):
    resp = client.post(
        "/api/v1/rag/documents/index",
        headers=AUTH,
        json={
            "document_id": "big",
            "source_type": "agency_policy",
            "title": "Big",
            "text": "x" * 200_001,
        },
    )
    assert resp.status_code == 413


def test_query_and_top_k_clamped(client):
    resp = client.post(
        "/api/v1/rag/query",
        headers=AUTH,
        json={"query": "x", "top_k": 999},
    )
    assert resp.status_code == 422  # pydantic ge/le bound
    resp = client.post(
        "/api/v1/rag/query",
        headers=AUTH,
        json={"query": "y" * 4_001},
    )
    assert resp.status_code == 422


def test_tag_cap_rejected(client):
    resp = client.post(
        "/api/v1/rag/documents/index",
        headers=AUTH,
        json={
            "document_id": "tags",
            "source_type": "agency_policy",
            "title": "Tags",
            "text": "content",
            "tags": [f"t{i}" for i in range(21)],
        },
    )
    assert resp.status_code == 422


# --- Frontier wiring ---------------------------------------------------------


def test_frontier_specialty_hook_receives_canonical_service_and_agency():
    from src.intake.config.agency_settings import AgencySettings
    from src.intake.frontier_orchestrator import run_frontier_orchestration
    from src.intake.decision import DecisionResult
    from src.intake.packet_models import CanonicalPacket, Slot

    packet = CanonicalPacket(packet_id="ragwiring")
    packet.raw_note = "family trip to singapore"
    packet.facts["resolved_destination"] = Slot(
        value="Singapore", authority_level="imported_structured", confidence=0.9
    )
    decision = DecisionResult(
        packet_id="ragwiring",
        current_stage="discovery",
        operating_mode="normal",
        decision_state="PROCEED_TRAVELER_SAFE",
    )
    settings = AgencySettings(agency_id="agency_frontier")

    captured = {}

    def _fake_identify(text, agency_id="default_agency", rag_service=None):
        captured["agency_id"] = agency_id
        captured["rag_service"] = rag_service
        return []

    sentinel_service = object()
    with patch(
        "src.rag.service.get_default_rag_service", return_value=sentinel_service
    ), patch.object(
        __import__("src.intake.frontier_orchestrator", fromlist=["SpecialtyKnowledgeService"]).SpecialtyKnowledgeService,
        "identify_niche",
        side_effect=_fake_identify,
    ):
        run_frontier_orchestration(packet, decision, agency_settings=settings)

    assert captured["agency_id"] == "agency_frontier"
    assert captured["rag_service"] is sentinel_service


# --- Provider egress discipline ----------------------------------------------


def _semantic_provider():
    from src.rag.embeddings import SemanticEmbeddingProvider

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        return SemanticEmbeddingProvider(provider_name="openai")


def test_semantic_provider_strips_pii_and_records_forensics():
    provider = _semantic_provider()
    assert provider.is_semantic is True

    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(index=0, embedding=[0.1, 0.2, 0.3])]
    )
    with patch.object(provider, "_get_sdk_client", return_value=fake_client), patch(
        "src.rag.embeddings._strip_pii_for_egress",
        side_effect=lambda t: t.replace("P1234567", "[REDACTED]"),
    ) as strip_mock:
        vector = provider.embed_text("passport P1234567 for Asha")

    assert vector == [0.1, 0.2, 0.3]
    strip_mock.assert_called_once()
    # The provider saw the STRIPPED text, never the raw passport number.
    sent_input = fake_client.embeddings.create.call_args.kwargs["input"]
    assert "P1234567" not in sent_input and "[REDACTED]" in sent_input
    # Forensics emitted, hashes only.
    rec = provider.last_call_record
    assert rec["model"] == "text-embedding-3-small"
    assert "P1234567" not in str(rec["prompt_sha256"])


def test_semantic_provider_raises_on_provider_failure():
    """Contract-verification fix (2026-10-22): when active, a remote failure
    RAISES — the old silent hash fallback stamped 'text-embedding-3-small'
    onto hash vectors, exactly the mislabeled-vector class FND-0362 forbids."""
    provider = _semantic_provider()
    failing = MagicMock()
    failing.embeddings.create.side_effect = RuntimeError("provider down")
    with patch.object(provider, "_get_sdk_client", return_value=failing), pytest.raises(
        RuntimeError, match="semantic embedding provider"
    ):
        provider.embed_text("some text")


def test_indexing_refuses_to_write_mislabeled_vectors_when_provider_fails(tmp_path):
    """End-to-end: with the semantic lane active and the provider down,
    index_document fails WITHOUT writing any vector under the semantic
    model name — the corpus stays provable."""

    service = RAGService(db_path=str(tmp_path / "refusal.db"))
    service.embedding_provider = _semantic_provider()
    service.indexer.embedding_provider = service.embedding_provider
    service.retriever.embedding_provider = service.embedding_provider

    failing = MagicMock()
    failing.embeddings.create.side_effect = RuntimeError("provider down")
    from src.rag.models import DocumentSourceType

    with patch.object(service.embedding_provider, "_get_sdk_client", return_value=failing), pytest.raises(
        RuntimeError, match="semantic embedding provider"
    ):
        service.index_document(
            document_id="adv",
            agency_id="agency_refusal",
            source_type=DocumentSourceType.AGENCY_POLICY,
            title="Advisory",
            text="Some policy text.",
        )
    # Nothing mislabeled entered the corpus.
    assert service.store.count_chunks("agency_refusal") == 0


def test_retriever_degrades_to_sparse_only_on_query_embedding_failure(tmp_path):
    """Query side: provider failure → sparse-only results with the RRF
    fallback, never a hash-query-vs-semantic-store comparison."""
    from src.rag.models import (
        DocumentSourceType,
        HybridSearchQuery,
        RAGChunk,
        RAGChunkMetadata,
    )
    from src.rag.retriever import HybridGraphVectorRetriever
    from src.rag.store import SQLiteRAGStore

    store = SQLiteRAGStore(db_path=str(tmp_path / "sparse_only.db"))
    provider = _semantic_provider()
    retriever = HybridGraphVectorRetriever(store, embedding_provider=provider)

    store.insert_chunk(RAGChunk(
        id="c1", content="kerala backwaters cruise",
        embedding=[0.1] * provider.dimension,
        metadata=RAGChunkMetadata(
            document_id="d", agency_id="a",
            source_type=DocumentSourceType.AGENCY_POLICY, title="t",
            embedding_model=provider.model_name,
            embedding_dimension=provider.dimension,
        ),
    ))

    failing = MagicMock()
    failing.embeddings.create.side_effect = RuntimeError("provider down")
    with patch.object(provider, "_get_sdk_client", return_value=failing):
        results = retriever.retrieve(
            HybridSearchQuery(query="kerala cruise", agency_id="a", top_k=3)
        )
    # Sparse-only still returns the chunk (FTS/substring), never raises,
    # and the dense leg contributed nothing (methods show no hybrid/dense).
    assert [r.chunk.id for r in results] == ["c1"]
    assert results[0].retrieval_method == "sparse"
