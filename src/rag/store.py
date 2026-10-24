"""SQLite-backed multi-tenant storage for the local RAG engine.

Provides cosine similarity over stored local vectors, BM25-style sparse
keyword search (FTS5 when available, substring heuristic otherwise), and
knowledge-graph (nodes/edges) persistence with strict tenant isolation.

Contract notes:
- Embedding provenance (FND-0362): every stored vector carries
  ``embedding_model`` + ``embedding_dimension``; inserts with an embedding but
  without provenance are rejected, and dense search is scoped to ONE model so
  cross-model comparisons are impossible by construction. A provider switch
  therefore degrades to sparse-only (visible, logged) — never silent zeros.
- The vector and lexical scores are implementation scores, not calibrated
  semantic confidence or standards-compliant BM25 scores.
- ``rag_runs`` records retrieval lineage with HASHED queries only — raw query
  text is never persisted (same privacy contract as ``record_llm_call``).
- Every SQL statement in this module is fully static and parameterized;
  optional metadata filters (``source_types``) are applied in Python over the
  tenant-scoped row set, never by string-building SQL.
"""

import json
import math
import re
import sqlite3
from datetime import datetime, timezone
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


def _source_type_passes(chunk: RAGChunk, source_types: Optional[List[str]]) -> bool:
    """Python-side optional filter over tenant-scoped rows (no dynamic SQL)."""
    if not source_types:
        return True
    value = (
        chunk.metadata.source_type.value
        if hasattr(chunk.metadata.source_type, "value")
        else str(chunk.metadata.source_type)
    )
    return value in source_types


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
            self._init_fts(conn)
            self._init_runs_table(conn)

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

    def _init_fts(self, conn: sqlite3.Connection) -> None:
        """FTS5 lexical leg (real tf-idf-family ranking) with an honest
        fallback flag when the runtime SQLite lacks the module."""
        try:
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks_fts USING fts5(chunk_id UNINDEXED, agency_id UNINDEXED, content, title)")
            self.fts_available = True
        except sqlite3.OperationalError:
            self.fts_available = False

    def _init_runs_table(self, conn: sqlite3.Connection) -> None:
        """Retrieval-lineage table. Hashed queries only — raw query text is
        never persisted (same privacy contract as ``record_llm_call``)."""
        conn.execute("CREATE TABLE IF NOT EXISTS rag_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, agency_id TEXT NOT NULL, query_sha256 TEXT NOT NULL, query_length INTEGER NOT NULL, top_k INTEGER NOT NULL, embedding_model TEXT NOT NULL, latency_ms REAL, result_count INTEGER NOT NULL, top_chunk_ids_json TEXT NOT NULL, created_at TEXT NOT NULL)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_agency ON rag_runs(agency_id, created_at);")

    # --- Chunk Storage & Retrieval ---

    def insert_chunk(self, chunk: RAGChunk) -> None:
        # Embedding contract (FND-0362), fail-closed: a vector without
        # provenance can never be compared safely, so it is never stored.
        # Provenance lives in metadata_json (model + dimension); a SQL-level
        # column is deferred to the Postgres endgame.
        if chunk.embedding is not None:
            model = chunk.metadata.embedding_model
            dim = chunk.metadata.embedding_dimension
            if not model or not dim:
                raise ValueError(
                    f"Chunk {chunk.id!r} has an embedding but no embedding_model/"
                    "embedding_dimension provenance — refusing to store an "
                    "unlabeled vector (FND-0362)."
                )
            if dim != len(chunk.embedding):
                raise ValueError(
                    f"Chunk {chunk.id!r} declares embedding_dimension={dim} but "
                    f"carries {len(chunk.embedding)} values."
                )
        # Citation provenance: content is the verbatim source unless a
        # retrieval-optimized transform explicitly separated the two.
        if not chunk.metadata.source_text:
            chunk.metadata.source_text = chunk.content
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
            if self.fts_available:
                conn.execute("DELETE FROM rag_chunks_fts WHERE chunk_id = ?", (chunk.id,))
                # The FTS leg indexes the RETRIEVAL rendering when present
                # (contextual prefix grounds contextless child chunks); the
                # verbatim source stays in metadata for citations.
                fts_content = chunk.metadata.retrieval_text or chunk.content
                conn.execute("INSERT INTO rag_chunks_fts (chunk_id, agency_id, content, title) VALUES (?, ?, ?, ?)", (chunk.id, chunk.metadata.agency_id, fts_content, chunk.metadata.title))
            conn.commit()

    def count_chunks(self, agency_id: str, source_type: Optional[str] = None) -> int:
        """Count stored chunks for a tenant (seeding/idempotence checks)."""
        if source_type:
            sql = "SELECT COUNT(*) AS n FROM rag_chunks WHERE agency_id = ? AND source_type = ?"
            params: List[Any] = [agency_id, source_type]
        else:
            sql = "SELECT COUNT(*) AS n FROM rag_chunks WHERE agency_id = ?"
            params = [agency_id]
        with self._get_connection() as conn:
            row = conn.execute(sql, params).fetchone()
        return int(row["n"])

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
            rows = conn.execute("SELECT id FROM rag_chunks WHERE agency_id = ? AND json_extract(metadata_json, '$.document_id') = ?", (agency_id, document_id)).fetchall()
            ids = [row["id"] for row in rows]
            if not ids:
                return 0
            if self.fts_available:
                for chunk_id in ids:
                    conn.execute("DELETE FROM rag_chunks_fts WHERE chunk_id = ?", (chunk_id,))
            cursor = conn.execute("DELETE FROM rag_chunks WHERE agency_id = ? AND json_extract(metadata_json, '$.document_id') = ?", (agency_id, document_id))
            conn.commit()
            return cursor.rowcount

    def get_embedding_models(self, agency_id: str) -> List[dict]:
        """Distinct embedding models present for the agency, with counts.

        Powers the provider-switch warning and the /rag/status honesty
        surface: more than one model (or none) means the dense leg is not
        comparable across the corpus.
        """
        sql = "SELECT metadata_json FROM rag_chunks WHERE agency_id = ? AND embedding_json IS NOT NULL"
        counts: dict = {}
        with self._get_connection() as conn:
            for row in conn.execute(sql, (agency_id,)):
                meta = json.loads(row["metadata_json"])
                key = (meta.get("embedding_model") or "unknown", meta.get("embedding_dimension") or 0)
                counts[key] = counts.get(key, 0) + 1
        return [
            {"embedding_model": model, "embedding_dimension": dim, "chunk_count": n}
            for (model, dim), n in sorted(counts.items(), key=lambda kv: -kv[1])
        ]

    def list_documents(self, agency_id: str) -> List[dict]:
        """Distinct indexed documents for the agency with license governance.

        The corpus-governance surface (CoverWise manifest pattern): every
        document's title, source type, chunk count, embedding model, and
        license_class in one listing.
        """
        sql = "SELECT metadata_json FROM rag_chunks WHERE agency_id = ?"
        docs: dict = {}
        with self._get_connection() as conn:
            for row in conn.execute(sql, (agency_id,)):
                meta = json.loads(row["metadata_json"])
                doc_id = meta.get("document_id") or "unknown"
                entry = docs.setdefault(
                    doc_id,
                    {
                        "document_id": doc_id,
                        "title": meta.get("title", ""),
                        "source_type": meta.get("source_type", ""),
                        "license_class": meta.get("license_class", "agency_owned"),
                        "embedding_model": meta.get("embedding_model"),
                        "chunk_count": 0,
                    },
                )
                entry["chunk_count"] += 1
        return sorted(docs.values(), key=lambda d: d["document_id"])

    def search_dense(
        self,
        query_vector: List[float],
        agency_id: str,
        top_k: int = 5,
        source_types: Optional[List[str]] = None,
        embedding_model: Optional[str] = None,
    ) -> List[Tuple[RAGChunk, float]]:
        """Search tenant-local vectors by cosine similarity, ONE model at a time.

        ``embedding_model`` is required (fail-closed): comparing a query
        vector against chunks embedded by a different model is meaningless,
        and the pre-contract behaviour silently scored such pairs 0.0
        (FND-0362). Chunks under other models — or legacy rows without
        provenance — are excluded by the filter, so a provider switch shows
        up as an empty dense leg, never as fabricated similarity.
        """
        if not embedding_model:
            raise ValueError(
                "search_dense requires embedding_model — refusing a "
                "cross-model vector comparison (FND-0362)."
            )
        sql = "SELECT * FROM rag_chunks WHERE agency_id = ? AND embedding_json IS NOT NULL"
        with self._get_connection() as conn:
            rows = conn.execute(sql, (agency_id,)).fetchall()

        results: List[Tuple[RAGChunk, float]] = []
        for row in rows:
            chunk = self._row_to_chunk(row)
            if not _source_type_passes(chunk, source_types):
                continue
            if chunk.metadata.embedding_model != embedding_model:
                continue
            if chunk.embedding and len(chunk.embedding) == len(query_vector):
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
        """Lexical leg: FTS5 bm25 ranking when available, substring heuristic
        otherwise. Both are implementation scores, not calibrated BM25."""
        if self.fts_available:
            fts_results = self._search_sparse_fts(query_text, agency_id, top_k, source_types)
            if fts_results is not None:
                return fts_results
        return self._search_sparse_substring(query_text, agency_id, top_k, source_types)

    @staticmethod
    def _fts_query_for(query_text: str) -> str:
        """Build a safe FTS5 MATCH expression from plain query text.

        Tokens are quoted and OR-joined so user punctuation can neither
        break the MATCH grammar nor inject operators. The MATCH argument is
        still bound as a parameter — nothing user-supplied is concatenated
        into SQL text.
        """
        tokens = [w for w in re.findall(r"\w+", query_text) if len(w) > 1]
        if not tokens:
            return ""
        return " OR ".join('"%s"' % t.replace('"', '""') for t in tokens[:32])

    def _search_sparse_fts(
        self,
        query_text: str,
        agency_id: str,
        top_k: int,
        source_types: Optional[List[str]] = None,
    ) -> Optional[List[Tuple[RAGChunk, float]]]:
        match_expr = self._fts_query_for(query_text)
        if not match_expr:
            return None
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    "SELECT c.*, bm25(rag_chunks_fts) AS fts_rank FROM rag_chunks_fts f JOIN rag_chunks c ON c.id = f.chunk_id WHERE rag_chunks_fts MATCH ? AND f.agency_id = ? AND c.agency_id = ? ORDER BY bm25(rag_chunks_fts)",
                    (match_expr, agency_id, agency_id),
                ).fetchall()
        except sqlite3.OperationalError:
            # Malformed MATCH or FTS hiccup → honest fallback to the
            # substring heuristic rather than an empty-looking failure.
            return None

        results: List[Tuple[RAGChunk, float]] = []
        for row in rows:
            chunk = self._row_to_chunk(row)
            if not _source_type_passes(chunk, source_types):
                continue
            # bm25() ranks negative-better; bound it into a positive display
            # score. The retriever fuses on RANKS, so only ordering is
            # load-bearing.
            rank = float(row["fts_rank"]) if row["fts_rank"] is not None else 0.0
            score = round(1.0 / (1.0 + min(100.0, abs(rank))), 4)
            results.append((chunk, score))
            if len(results) >= top_k:
                break
        return results

    def _search_sparse_substring(
        self,
        query_text: str,
        agency_id: str,
        top_k: int = 5,
        source_types: Optional[List[str]] = None,
    ) -> List[Tuple[RAGChunk, float]]:
        """Score substring keyword matches over content and title.

        The formula is intentionally a small offline heuristic inspired by
        BM25; it does not calculate BM25 document frequency or IDF.
        """
        query_tokens = [w.lower() for w in re.findall(r"\w+", query_text) if len(w) > 1]
        if not query_tokens:
            return []

        sql = "SELECT * FROM rag_chunks WHERE agency_id = ?"
        with self._get_connection() as conn:
            rows = conn.execute(sql, (agency_id,)).fetchall()

        results: List[Tuple[RAGChunk, float]] = []
        for row in rows:
            chunk = self._row_to_chunk(row)
            if not _source_type_passes(chunk, source_types):
                continue
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

    # --- Retrieval audit (hashes only — raw query text is never stored) ---

    def record_retrieval_run(
        self,
        agency_id: str,
        query_sha256: str,
        query_length: int,
        top_k: int,
        embedding_model: str,
        latency_ms: Optional[float],
        result_count: int,
        top_chunk_ids: List[str],
    ) -> None:
        """Persist one retrieval lineage row. Callers supply hashes and
        identifiers only; raw query/answer text is never accepted."""
        sql = "INSERT INTO rag_runs (agency_id, query_sha256, query_length, top_k, embedding_model, latency_ms, result_count, top_chunk_ids_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        with self._get_connection() as conn:
            conn.execute(
                sql,
                (
                    agency_id,
                    query_sha256,
                    query_length,
                    top_k,
                    embedding_model,
                    latency_ms,
                    result_count,
                    json.dumps([str(cid) for cid in top_chunk_ids[:20]]),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()

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
            if self.fts_available:
                conn.execute("DELETE FROM rag_chunks_fts WHERE agency_id = ?", (agency_id,))
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
