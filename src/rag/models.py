"""Data models for the Waypoint OS RAG Engine.

Models cover the current local hash-vector representation, sparse lexical
indexing, knowledge-graph records, citation metadata, and heuristic
groundedness evaluation.  The model names are intentionally stable while the
implementation remains provider-neutral; a future semantic embedding provider
must carry its model/version provenance before these local vectors are treated
as semantic evidence.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
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
    # Embedding contract (FND-0362): every stored vector must say what
    # produced it. Chunks without an embedding leave these None; chunks WITH
    # an embedding may not be inserted without both fields (store enforces,
    # fail-closed). Cross-model retrieval is filtered, never silently compared.
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    # Verbatim source span for citation provenance (CoverWise source/retrieval
    # split). None means content IS the verbatim source (the default indexer
    # slices original text); a future retrieval-optimized transform would fill
    # both and keep this field as the citable truth.
    source_text: Optional[str] = None
    # Retrieval-optimized rendering (FND-0329-style contextual retrieval):
    # document title (+ part/section context) prepended so contextless child
    # chunks embed and FTS-match with their document grounding. None means
    # "same as content" (store/indexer fall back). Citations NEVER quote this.
    retrieval_text: Optional[str] = None
    # Corpus license governance (CoverWise manifest pattern): the redistribution
    # posture of the document this chunk came from. Validated at the API edge;
    # "agency_owned" is the default for everything the agency writes itself.
    #   agency_owned | redistribution_safe | local_eval_only
    license_class: str = "agency_owned"
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
    # Lexical support and literal provenance are not factual entailment. These
    # fields let consumers preserve that distinction without guessing from a
    # score or treating a retrieval hit as claim verification.
    grounding_method: str = "lexical_overlap_numeric_guard_v1"
    lexical_overlap_score: float = 0.0
    claim_support_status: Literal[
        "no_sources", "source_excerpt", "not_verified", "unsupported_numeric", "empty_answer"
    ] = "not_verified"


class HybridSearchQuery(BaseModel):
    query: str
    agency_id: str
    top_k: int = 5
    source_types: Optional[List[DocumentSourceType]] = None
    destination_filter: Optional[str] = None
    tags_filter: Optional[List[str]] = None
    alpha: float = 0.5  # Dense vs sparse weight (0.0 = sparse only, 1.0 = dense only)
    include_graph: bool = True
