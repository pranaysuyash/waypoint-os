import os
from unittest.mock import patch
from src.rag.embeddings import (
    EmbeddingProvider,
    HashEmbeddingProvider,
    SemanticEmbeddingProvider,
)
from src.rag.service import RAGService
from src.rag.models import DocumentSourceType, HybridSearchQuery


def test_hash_embedding_provider_contract():
    provider = HashEmbeddingProvider(dimension=32)
    assert isinstance(provider, EmbeddingProvider)
    assert provider.provider_name == "local_hash"
    assert provider.model_name == "md5_word_bucket"
    assert provider.dimension == 32
    assert not provider.is_semantic

    v = provider.embed_text("luxury hotels in Kyoto with garden view")
    assert len(v) == 32
    # Verify unit length normalization
    norm = sum(x * x for x in v) ** 0.5
    assert abs(norm - 1.0) < 1e-4

    batch = provider.embed_batch(["tokyo train", "kyoto temple"])
    assert len(batch) == 2
    assert len(batch[0]) == 32
    assert len(batch[1]) == 32


def test_semantic_embedding_provider_fallback_when_credentials_absent():
    with patch.dict(os.environ, {}, clear=True):
        provider = SemanticEmbeddingProvider(provider_name="openai")
        assert isinstance(provider, EmbeddingProvider)
        assert not provider.is_semantic
        assert "fallback" in provider.provider_name

        v = provider.embed_text("test fallback query")
        assert len(v) == 64
        norm = sum(x * x for x in v) ** 0.5
        assert abs(norm - 1.0) < 1e-4


def test_rag_service_with_custom_embedding_provider(tmp_path):
    db_path = str(tmp_path / "custom_rag.db")
    custom_provider = HashEmbeddingProvider(dimension=48)
    service = RAGService(db_path=db_path, embedding_provider=custom_provider)

    assert service.embedding_provider.dimension == 48

    chunks = service.index_document(
        document_id="doc_test_1",
        agency_id="agency_01",
        source_type=DocumentSourceType.SUPPLIER_CONTRACT,
        title="Baggage Policy",
        text="All business class travelers get 2 checked bags free of charge.",
    )
    assert len(chunks) >= 1
    assert len(chunks[0].embedding) == 48

    results = service.search(
        HybridSearchQuery(
            query="business class baggage allowance",
            agency_id="agency_01",
            top_k=3,
        )
    )
    assert len(results) >= 1
    assert results[0].chunk.id == chunks[0].id
