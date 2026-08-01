"""Canonical RAG Service facade for Waypoint OS.

Provides unified document indexing, hybrid vector/sparse/graph search,
and grounded generation interfaces with multi-tenant isolation.
"""

from typing import Callable, List, Optional
from src.rag.models import (
    RAGChunk,
    DocumentSourceType,
    HybridSearchQuery,
    RAGSearchResult,
    GroundedAnswer,
    KnowledgeNode,
    KnowledgeEdge,
)
from src.rag.store import SQLiteRAGStore
from src.rag.indexer import DocumentIndexer
from src.rag.retriever import HybridGraphVectorRetriever
from src.rag.grounding import GroundednessEvaluator


class RAGService:
    def __init__(self, db_path: str = "data/rag_store.db"):
        self.store = SQLiteRAGStore(db_path=db_path)
        self.indexer = DocumentIndexer()
        self.retriever = HybridGraphVectorRetriever(self.store)
        self.evaluator = GroundednessEvaluator()

    def index_document(
        self,
        document_id: str,
        agency_id: str,
        source_type: DocumentSourceType,
        title: str,
        text: str,
        canonical_url: Optional[str] = None,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[RAGChunk]:
        """Chunk, embed, and store a full text document."""
        chunks = self.indexer.chunk_text(
            text=text,
            document_id=document_id,
            agency_id=agency_id,
            source_type=source_type,
            title=title,
            canonical_url=canonical_url,
            file_path=file_path,
            tags=tags,
        )
        for chunk in chunks:
            self.store.insert_chunk(chunk)
        return chunks

    def search(self, search_query: HybridSearchQuery) -> List[RAGSearchResult]:
        """Perform hybrid retrieval."""
        return self.retriever.retrieve(search_query)

    def query_and_ground(
        self,
        query: str,
        agency_id: str,
        generator_fn: Optional[Callable[[str, List[RAGSearchResult]], str]] = None,
        source_types: Optional[List[DocumentSourceType]] = None,
        top_k: int = 5,
    ) -> GroundedAnswer:
        """Retrieve relevant knowledge, generate answer, and evaluate groundedness."""
        search_query = HybridSearchQuery(
            query=query,
            agency_id=agency_id,
            top_k=top_k,
            source_types=source_types,
        )
        citations = self.search(search_query)

        if generator_fn:
            answer_text = generator_fn(query, citations)
        else:
            # Fallback simple synthesis from top citations
            if citations:
                top_contents = "\n\n".join(c.chunk.content for c in citations[:2])
                answer_text = f"Based on retrieved documents:\n\n{top_contents}"
            else:
                answer_text = "No relevant knowledge found in the agency document repository."

        grounded = self.evaluator.evaluate_answer(
            query=query,
            answer=answer_text,
            citations=citations,
        )
        return grounded

    def add_node(self, node: KnowledgeNode) -> None:
        self.store.insert_node(node)

    def add_edge(self, edge: KnowledgeEdge) -> None:
        self.store.insert_edge(edge)

    def get_nodes(self, agency_id: str, node_type: Optional[str] = None) -> List[KnowledgeNode]:
        return self.store.get_nodes(agency_id, node_type)
