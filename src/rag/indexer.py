"""Document chunking and embedding indexer for Waypoint OS RAG Engine.

Supports parent-child hierarchical chunking, metadata extraction,
and embedding generation with API and deterministic local fallbacks.
"""

import hashlib
import uuid
from typing import List, Optional
from src.rag.models import RAGChunk, RAGChunkMetadata, DocumentSourceType


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "to", "was", "were",
    "will", "with", "we", "you", "your", "this", "have"
}


def generate_local_embedding(text: str, dim: int = 64) -> List[float]:
    """Generate a deterministic normalized pseudo-embedding vector for offline/test use."""
    words = [w.strip(".,!?:;\"'()[]{}") for w in text.lower().split()]
    filtered_words = [w for w in words if w and w not in STOPWORDS and len(w) > 1]
    
    vector = [0.0] * dim
    for idx, word in enumerate(filtered_words):
        # Hash each word into vector buckets
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        vector[h % dim] += 1.0 / (1.0 + idx * 0.1)

    # Normalize vector to unit length
    norm = sum(v * v for v in vector) ** 0.5
    if norm > 0.0:
        vector = [v / norm for v in vector]
    return vector


class DocumentIndexer:
    def __init__(
        self,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 500,
        embedding_dim: int = 64,
    ):
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.embedding_dim = embedding_dim

    def chunk_text(
        self,
        text: str,
        document_id: str,
        agency_id: str,
        source_type: DocumentSourceType,
        title: str,
        canonical_url: Optional[str] = None,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[RAGChunk]:
        """Split raw text into hierarchical parent and child chunks with metadata."""
        if not text or not text.strip():
            return []

        chunks: List[RAGChunk] = []

        # Step 1: Create parent chunks
        parent_texts = self._slice_into_blocks(text, max_chars=self.parent_chunk_size)

        for p_idx, p_text in enumerate(parent_texts):
            p_id = f"chunk_{document_id}_{p_idx}_{uuid.uuid4().hex[:6]}"
            p_metadata = RAGChunkMetadata(
                document_id=document_id,
                agency_id=agency_id,
                source_type=source_type,
                title=f"{title} (Part {p_idx+1})" if len(parent_texts) > 1 else title,
                canonical_url=canonical_url,
                file_path=file_path,
                tags=tags or [],
            )
            
            p_embedding = generate_local_embedding(p_text, dim=self.embedding_dim)
            parent_chunk = RAGChunk(
                id=p_id,
                parent_id=None,
                content=p_text,
                embedding=p_embedding,
                metadata=p_metadata,
                token_count=len(p_text.split()),
            )
            chunks.append(parent_chunk)

            # Step 2: Slice parent into child chunks only if parent exceeds child_chunk_size
            if len(p_text) > self.child_chunk_size:
                child_texts = self._slice_into_blocks(p_text, max_chars=self.child_chunk_size)
                if len(child_texts) > 1:
                    for c_idx, c_text in enumerate(child_texts):
                        c_id = f"child_{p_id}_{c_idx}"
                        c_metadata = RAGChunkMetadata(
                            document_id=document_id,
                            agency_id=agency_id,
                            source_type=source_type,
                            title=f"{title} (Section {p_idx+1}.{c_idx+1})",
                            canonical_url=canonical_url,
                            file_path=file_path,
                            tags=tags or [],
                        )
                        c_embedding = generate_local_embedding(c_text, dim=self.embedding_dim)
                        child_chunk = RAGChunk(
                            id=c_id,
                            parent_id=p_id,
                            content=c_text,
                            embedding=c_embedding,
                            metadata=c_metadata,
                            token_count=len(c_text.split()),
                        )
                        chunks.append(child_chunk)

        return chunks

    def _slice_into_blocks(self, text: str, max_chars: int) -> List[str]:
        """Slice text into blocks prioritizing paragraph breaks."""
        paragraphs = text.split("\n\n")
        blocks: List[str] = []
        current_block: List[str] = []
        current_len = 0

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue

            if current_len + len(p_clean) > max_chars and current_block:
                blocks.append("\n\n".join(current_block))
                current_block = [p_clean]
                current_len = len(p_clean)
            else:
                current_block.append(p_clean)
                current_len += len(p_clean)

        if current_block:
            blocks.append("\n\n".join(current_block))

        return blocks
