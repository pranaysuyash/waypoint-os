"""SQLite-backed multi-tenant storage for the RAG engine.

Provides vector similarity search, BM25 sparse keyword scoring,
and knowledge graph (nodes/edges) persistence with strict tenant isolation.
"""

import json
import math
import re
import sqlite3
from typing import List, Any, Optional, Tuple
import os

from src.rag.models import (
    RAGChunk,
    RAGChunkMetadata,
    KnowledgeNode,
    KnowledgeEdge,
)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vector lists."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class SQLiteRAGStore:
    def __init__(self, db_path: str = "data/rag_store.db"):
        self.db_path = db_path
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    id TEXT PRIMARY KEY,
                    parent_id TEXT,
                    agency_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding_json TEXT,
                    metadata_json TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_agency ON rag_chunks(agency_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source_type ON rag_chunks(source_type);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id TEXT NOT NULL,
                    agency_id TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    properties_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (id, agency_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_agency ON knowledge_nodes(agency_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON knowledge_nodes(node_type);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id TEXT NOT NULL,
                    agency_id TEXT NOT NULL,
                    source_node_id TEXT NOT NULL,
                    target_node_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    properties_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (id, agency_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_agency ON knowledge_edges(agency_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON knowledge_edges(source_node_id, agency_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON knowledge_edges(target_node_id, agency_id);")
            conn.commit()

    # --- Chunk Storage & Retrieval ---

    def insert_chunk(self, chunk: RAGChunk) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO rag_chunks
                (id, parent_id, agency_id, source_type, title, content, embedding_json, metadata_json, token_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.id,
                    chunk.parent_id,
                    chunk.metadata.agency_id,
                    chunk.metadata.source_type.value if hasattr(chunk.metadata.source_type, "value") else str(chunk.metadata.source_type),
                    chunk.metadata.title,
                    chunk.content,
                    json.dumps(chunk.embedding) if chunk.embedding is not None else None,
                    chunk.metadata.model_dump_json(),
                    chunk.token_count,
                    chunk.metadata.created_at,
                ),
            )
            conn.commit()

    def get_chunk(self, chunk_id: str, agency_id: str) -> Optional[RAGChunk]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM rag_chunks WHERE id = ? AND agency_id = ?",
                (chunk_id, agency_id),
            ).fetchone()
            if not row:
                return None
            return self._row_to_chunk(row)

    def delete_chunks_by_document(self, document_id: str, agency_id: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM rag_chunks WHERE agency_id = ? AND json_extract(metadata_json, '$.document_id') = ?",
                (agency_id, document_id),
            )
            conn.commit()
            return cursor.rowcount

    def search_dense(
        self,
        query_vector: List[float],
        agency_id: str,
        top_k: int = 5,
        source_types: Optional[List[str]] = None,
    ) -> List[Tuple[RAGChunk, float]]:
        """Vector similarity search (cosine distance)."""
        with self._get_connection() as conn:
            query = "SELECT * FROM rag_chunks WHERE agency_id = ? AND embedding_json IS NOT NULL"
            params: List[Any] = [agency_id]

            if source_types:
                placeholders = ",".join("?" for _ in source_types)
                query += f" AND source_type IN ({placeholders})"
                params.extend(source_types)

            rows = conn.execute(query, params).fetchall()

        results: List[Tuple[RAGChunk, float]] = []
        for row in rows:
            chunk = self._row_to_chunk(row)
            if chunk.embedding:
                score = cosine_similarity(query_vector, chunk.embedding)
                results.append((chunk, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def search_sparse_bm25(
        self,
        query_text: str,
        agency_id: str,
        top_k: int = 5,
        source_types: Optional[List[str]] = None,
    ) -> List[Tuple[RAGChunk, float]]:
        """BM25-style keyword matching score over content and title."""
        query_tokens = [w.lower() for w in re.findall(r"\w+", query_text) if len(w) > 1]
        if not query_tokens:
            return []

        with self._get_connection() as conn:
            query = "SELECT * FROM rag_chunks WHERE agency_id = ?"
            params: List[Any] = [agency_id]

            if source_types:
                placeholders = ",".join("?" for _ in source_types)
                query += f" AND source_type IN ({placeholders})"
                params.extend(source_types)

            rows = conn.execute(query, params).fetchall()

        results: List[Tuple[RAGChunk, float]] = []
        for row in rows:
            chunk = self._row_to_chunk(row)
            content_lower = chunk.content.lower()
            title_lower = chunk.metadata.title.lower()
            
            score = 0.0
            for token in query_tokens:
                c_count = content_lower.count(token)
                t_count = title_lower.count(token)
                if c_count > 0 or t_count > 0:
                    score += (c_count * 1.0) + (t_count * 2.5)

            if score > 0.0:
                # Length normalization
                norm_score = score / (1.0 + math.log(max(1, chunk.token_count or len(content_lower.split()))))
                results.append((chunk, norm_score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    # --- Knowledge Graph Storage & Retrieval ---

    def insert_node(self, node: KnowledgeNode) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO knowledge_nodes
                (id, agency_id, node_type, label, properties_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    node.id,
                    node.agency_id,
                    node.node_type,
                    node.label,
                    json.dumps(node.properties),
                    node.created_at,
                ),
            )
            conn.commit()

    def insert_edge(self, edge: KnowledgeEdge) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO knowledge_edges
                (id, agency_id, source_node_id, target_node_id, relation, weight, properties_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge.id,
                    edge.agency_id,
                    edge.source_node_id,
                    edge.target_node_id,
                    edge.relation,
                    edge.weight,
                    json.dumps(edge.properties),
                    edge.created_at,
                ),
            )
            conn.commit()

    def get_nodes(self, agency_id: str, node_type: Optional[str] = None) -> List[KnowledgeNode]:
        with self._get_connection() as conn:
            if node_type:
                rows = conn.execute(
                    "SELECT * FROM knowledge_nodes WHERE agency_id = ? AND node_type = ?",
                    (agency_id, node_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM knowledge_nodes WHERE agency_id = ?",
                    (agency_id,),
                ).fetchall()
            return [self._row_to_node(row) for row in rows]

    def get_edges_for_node(self, node_id: str, agency_id: str) -> List[KnowledgeEdge]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM knowledge_edges
                WHERE agency_id = ? AND (source_node_id = ? OR target_node_id = ?)
                """,
                (agency_id, node_id, node_id),
            ).fetchall()
            return [self._row_to_edge(row) for row in rows]

    def clear_agency_data(self, agency_id: str) -> None:
        """Clear all RAG chunks, nodes, and edges for a tenant (for testing/cleanup)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM rag_chunks WHERE agency_id = ?", (agency_id,))
            conn.execute("DELETE FROM knowledge_nodes WHERE agency_id = ?", (agency_id,))
            conn.execute("DELETE FROM knowledge_edges WHERE agency_id = ?", (agency_id,))
            conn.commit()

    # --- Helpers ---

    def _row_to_chunk(self, row: sqlite3.Row) -> RAGChunk:
        metadata_dict = json.loads(row["metadata_json"])
        embedding = json.loads(row["embedding_json"]) if row["embedding_json"] else None
        return RAGChunk(
            id=row["id"],
            parent_id=row["parent_id"],
            content=row["content"],
            embedding=embedding,
            metadata=RAGChunkMetadata(**metadata_dict),
            token_count=row["token_count"],
        )

    def _row_to_node(self, row: sqlite3.Row) -> KnowledgeNode:
        return KnowledgeNode(
            id=row["id"],
            agency_id=row["agency_id"],
            node_type=row["node_type"],
            label=row["label"],
            properties=json.loads(row["properties_json"]),
            created_at=row["created_at"],
        )

    def _row_to_edge(self, row: sqlite3.Row) -> KnowledgeEdge:
        return KnowledgeEdge(
            id=row["id"],
            agency_id=row["agency_id"],
            source_node_id=row["source_node_id"],
            target_node_id=row["target_node_id"],
            relation=row["relation"],
            weight=row["weight"],
            properties=json.loads(row["properties_json"]),
            created_at=row["created_at"],
        )
