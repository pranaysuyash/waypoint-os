"""Data models for the Waypoint OS RAG Engine.

Supports dense vector embeddings, sparse lexical indexing, knowledge graph nodes/edges,
granular citation metadata, and groundedness evaluation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentSourceType(str, Enum):
    AGENCY_POLICY = "agency_policy"
    SUPPLIER_CONTRACT = "supplier_contract"
    GOVERNMENT_ADVISORY = "government_advisory"
    TRIP_DOCUMENT = "trip_document"
    TRIBAL_KNOWLEDGE = "tribal_knowledge"
    OVERRIDE_LOG = "override_log"
    ITINERARY_TEMPLATE = "itinerary_template"
    SPECIALTY_KNOWLEDGE = "specialty_knowledge"


class RAGChunkMetadata(BaseModel):
    document_id: str
    agency_id: str
    source_type: DocumentSourceType
    title: str
    section_heading: Optional[str] = None
    page_number: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    canonical_url: Optional[str] = None
    file_path: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    entity_references: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RAGChunk(BaseModel):
    id: str
    parent_id: Optional[str] = None
    content: str
    embedding: Optional[List[float]] = None
    metadata: RAGChunkMetadata
    token_count: int = 0


class KnowledgeNode(BaseModel):
    id: str  # e.g., "destination:singapore"
    agency_id: str
    node_type: str  # "destination", "supplier", "policy", "niche", "activity"
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KnowledgeEdge(BaseModel):
    id: str
    agency_id: str
    source_node_id: str
    target_node_id: str
    relation: str  # "SUITABLE_FOR", "GOVERNED_BY", "REQUIRES_VISA", "PREFERRED_SUPPLIER"
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RAGSearchResult(BaseModel):
    chunk: RAGChunk
    score: float
    dense_score: float = 0.0
    sparse_score: float = 0.0
    graph_distance: Optional[int] = None
    retrieval_method: str = "hybrid"  # "hybrid", "dense", "sparse", "graph"


class GroundedAnswer(BaseModel):
    query: str
    answer: str
    groundedness_score: float  # 0.0 to 1.0
    is_grounded: bool
    citations: List[RAGSearchResult] = Field(default_factory=list)
    must_confirm: List[str] = Field(default_factory=list)
    execution_telemetry_id: str = ""


class HybridSearchQuery(BaseModel):
    query: str
    agency_id: str
    top_k: int = 5
    source_types: Optional[List[DocumentSourceType]] = None
    destination_filter: Optional[str] = None
    tags_filter: Optional[List[str]] = None
    alpha: float = 0.5  # Dense vs Sparse weighting (0.0 = sparse only, 1.0 = dense only)
    include_graph: bool = True
