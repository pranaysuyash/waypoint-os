"""Hybrid local-vector + lexical + graph-traversal retriever for Waypoint OS.

Uses Reciprocal Rank Fusion (RRF) to merge vector similarity (provider-backed
or deterministic hash fallback) and substring lexical matching, with
entity-matching and 1-hop knowledge graph edge traversal under strict tenant
isolation.
"""

from typing import List, Dict, Optional
from src.rag.models import (
    RAGChunk,
    RAGSearchResult,
    HybridSearchQuery,
)
from src.rag.store import SQLiteRAGStore
from src.rag.embeddings import EmbeddingProvider, HashEmbeddingProvider


class HybridGraphVectorRetriever:
    def __init__(
        self,
        store: SQLiteRAGStore,
        rrf_k: float = 60.0,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.store = store
        self.rrf_k = rrf_k
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()

    def retrieve(self, search_query: HybridSearchQuery) -> List[RAGSearchResult]:
        """Perform local-vector/lexical retrieval fused via RRF.

        ``include_graph`` enables entity-reference matching and 1-hop edge
        traversal across knowledge nodes and edges stored for the agency.
        """
        agency_id = search_query.agency_id
        query_text = search_query.query
        top_k = search_query.top_k

        source_type_filter = (
            [st.value if hasattr(st, "value") else str(st) for st in search_query.source_types]
            if search_query.source_types
            else None
        )

        # 1. Vector similarity search (provider-backed or deterministic hash fallback).
        query_vector = self.embedding_provider.embed_text(query_text)
        dense_results = self.store.search_dense(
            query_vector=query_vector,
            agency_id=agency_id,
            top_k=top_k * 2,
            source_types=source_type_filter,
        )

        # 2. Sparse substring lexical heuristic (not standards-compliant BM25).
        sparse_results = self.store.search_sparse_bm25(
            query_text=query_text,
            agency_id=agency_id,
            top_k=top_k * 2,
            source_types=source_type_filter,
        )

        # 3. Reciprocal Rank Fusion (RRF)
        chunk_map: Dict[str, RAGChunk] = {}
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}
        dense_scores: Dict[str, float] = {}
        sparse_scores: Dict[str, float] = {}

        for rank, (chunk, score) in enumerate(dense_results, start=1):
            chunk_map[chunk.id] = chunk
            dense_ranks[chunk.id] = rank
            dense_scores[chunk.id] = score

        for rank, (chunk, score) in enumerate(sparse_results, start=1):
            chunk_map[chunk.id] = chunk
            sparse_ranks[chunk.id] = rank
            sparse_scores[chunk.id] = score

        rrf_scores: Dict[str, float] = {}
        all_chunk_ids = set(dense_ranks.keys()).union(set(sparse_ranks.keys()))

        for chunk_id in all_chunk_ids:
            score = 0.0
            if chunk_id in dense_ranks:
                score += search_query.alpha * (1.0 / (self.rrf_k + dense_ranks[chunk_id]))
            if chunk_id in sparse_ranks:
                score += (1.0 - search_query.alpha) * (1.0 / (self.rrf_k + sparse_ranks[chunk_id]))
            rrf_scores[chunk_id] = score

        # 4. Optional graph traversal: direct matching nodes (1.5x) + 1-hop connected nodes (1.25x).
        if search_query.include_graph:
            graph_nodes = self.store.get_nodes(agency_id)
            query_lower = query_text.lower()
            matching_node_ids = {n.id for n in graph_nodes if n.label.lower() in query_lower}

            one_hop_node_ids: set[str] = set()
            for nid in matching_node_ids:
                edges = self.store.get_edges_for_node(nid, agency_id)
                for edge in edges:
                    connected_id = edge.target_node_id if edge.source_node_id == nid else edge.source_node_id
                    if connected_id not in matching_node_ids:
                        one_hop_node_ids.add(connected_id)

            if matching_node_ids or one_hop_node_ids:
                for chunk_id, chunk in chunk_map.items():
                    for ref in chunk.metadata.entity_references:
                        if ref in matching_node_ids:
                            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) * 1.5
                        elif ref in one_hop_node_ids:
                            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) * 1.25

        # Format final search results
        sorted_ids = sorted(all_chunk_ids, key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]
        
        final_results: List[RAGSearchResult] = []
        for cid in sorted_ids:
            chunk = chunk_map[cid]
            res = RAGSearchResult(
                chunk=chunk,
                score=round(rrf_scores[cid], 6),
                dense_score=round(dense_scores.get(cid, 0.0), 4),
                sparse_score=round(sparse_scores.get(cid, 0.0), 4),
                retrieval_method="hybrid" if (cid in dense_ranks and cid in sparse_ranks) else ("dense" if cid in dense_ranks else "sparse"),
            )
            final_results.append(res)

        return final_results
