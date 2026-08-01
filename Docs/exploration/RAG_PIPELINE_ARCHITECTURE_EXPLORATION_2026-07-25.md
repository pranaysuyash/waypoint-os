# Domain-Specific RAG Pipeline & Knowledge Architecture — Exploration Map & Blueprint

**Project**: Waypoint OS (`travel_agency_agent`)  
**Date**: 2026-07-25  
**Status**: Exploration Completed — Ready for Discussion & Scoping  
**Parent Index**: [Docs/EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) §6e  

---

## 1. Executive Summary

Generic RAG solutions (simple vector search over PDF text chunks) fail in specialized multi-tenant domain platforms like **Waypoint OS**. Travel agencies do not merely need semantic text search; they require **grounded, referenceable, traceable, zero-hallucination knowledge retrieval** that operates across strict multi-tenant agency boundaries.

This exploration establishes the **5-Pillar Knowledge Architecture** for Waypoint OS, mapping out how RAG transitions from static hardcoded mocks (e.g. `specialty_knowledge.py`) into an enterprise-grade **Hybrid Graph-Vector RAG Engine**.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                WAYPOINT OS DOMAIN-SPECIFIC RAG                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  1. Institutional Memory     2. Regulatory & Visa       3. Supplier & Destination  4. Trip Evidence│
│  (Rates, Tribal Hacks,       (Passports, Visas,         (Suitability, Weather,    (Passports,      │
│   Margin Rules, Templates)    6-Mo Rules, Transit)       Accessibility, Hikes)     WhatsApp, Docs) │
│                                                                                                  │
│  5. Operator Overrides & Disruption Playbooks (Historical edits, crisis resolution graphs)       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   HYBRID GRAPH-VECTOR ENGINE                                     │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  • Dense Semantic Retrieval (Vector Embeddings)                                                  │
│  • Sparse Lexical Retrieval (BM25 for exact hotel/flight/passport terms)                         │
│  • Knowledge Graph Traversal (Agency ➔ Supplier ➔ Destination ➔ Policy ➔ Customer)               │
│  • Grounded Citation & Provable Traceability Engine (Document ID, Page, Line, Confidence)        │
│  • Multi-Tenant RLS Security (Strict agency_id isolation)                                        │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Capabilities: The 6 RAG Pillars

To satisfy high-stakes travel agency operations, our RAG pipeline enforces 6 mandatory capabilities:

### 2.1 Searchable (Multi-Modal Hybrid Search)
* **Problem**: Pure vector search misses exact terms (e.g., flight code "6E-204", hotel name "Amanpuri", passport number, PNR). Pure lexical search misses semantic intent (e.g., "quiet romantic beach resort with vegetarian food").
* **Solution**: **Hybrid Retrieval** combining:
  1. Dense Vector Similarity (e.g. `text-embedding-3-small` / bge-large-en).
  2. Sparse Lexical BM25 Search.
  3. Structured Metadata Filtering (`agency_id`, `destination`, `supplier_id`, `niche`, `date_range`).
  4. Reciprocal Rank Fusion (RRF) to merge dense and sparse results cleanly.

### 2.2 Referenceable (Granular Document & Chunk Provenance)
* **Problem**: Operators cannot trust AI recommendations without knowing *where* the rule or rate came from.
* **Solution**: Every chunk indexed carries explicit provenance metadata:
  * `document_id` & `document_version`
  * `source_type` (`agency_policy`, `supplier_contract`, `government_advisory`, `trip_document`, `tribal_note`, `override_log`)
  * `page_number`, `line_range`, `section_heading`
  * `canonical_url` or `file_path`
  * `agency_id` (tenant boundary)

### 2.3 Traceable (End-to-End Decision Lineage)
* **Problem**: Debugging why an AI agent made a specific proposal or flagged a visa risk requires inspecting the exact context injected into the prompt.
* **Solution**: RAG execution emits structured telemetry events into `run_ledger` and `telemetry.py`:
  * `rag_query_executed`: records query text, filter parameters, top-k vector distances, BM25 scores, and final selected chunks.
  * `rag_prompt_injected`: records exact formatted context string fed into LLM.
  * `rag_citation_resolved`: records downstream links generated in traveler proposals or operator checklists.

### 2.4 Grounded (Anti-Hallucination & Verification)
* **Problem**: Hallucinating a visa rule (e.g. claiming a 30-day visa-on-arrival exists when it requires an e-Visa) leads to traveler deportation or stranded clients.
* **Solution**:
  1. **Groundedness Scoring**: Post-retrieval LLM verification checking if the generated answer is strictly supported by the retrieved context chunks.
  2. **Confidence Thresholding**: If similarity/groundedness score < 0.75, automatically flag `must_confirm` for human operator review instead of stating unverified claims.
  3. **Fact-Level Attestation**: Critical facts (passport expiry, visa duration, deposit deadlines) must link directly to an attestation chunk.

### 2.5 Embedded (Multi-Vector & Hierarchical Representation)
* **Problem**: Small text chunks lose high-level document context; large chunks dilute granular facts.
* **Solution**: **Hierarchical & Parent-Child Chunking**:
  * **Parent Chunks** (1000 tokens): Retain overall document context (e.g. full visa policy for Japan).
  * **Child Chunks** (200 tokens): Vector embedded for precise match retrieval. When a child matches, the parent context is passed to the generation model.
  * **Summary Vectors**: Document-level summaries indexed for high-level routing.

### 2.6 Linkages, Nodes & Graphs (Graph RAG)
* **Problem**: Travel knowledge is inherently relational. Searching for "hotels in Bali near diving centers suitable for elderly travelers" requires traversing entity linkages (`Destination` ➔ `Activity` ➔ `Supplier` ➔ `Suitability Constraints`).
* **Solution**: **Knowledge Graph RAG**:
  * **Nodes**: `Agency`, `Supplier`, `Destination`, `Activity`, `Policy`, `Trip`, `Customer`, `Override`.
  * **Edges**: `LOCATED_IN`, `OFFERS_ACTIVITY`, `SUITABLE_FOR`, `GOVERNED_BY`, `OVERRODE_OPTION`, `PREFERRED_BY`.
  * **Graph Traversal**: Combines vector similarity with multi-hop graph retrieval to answer complex contextual inquiries.

---

## 3. Data Model & Architecture Design

### 3.1 Proposed Schema (`src/rag/models.py`)

```python
from datetime import datetime
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
    entity_references: List[str] = Field(default_factory=list)  # e.g., ["destination:bali", "supplier:amanpuri"]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RAGChunk(BaseModel):
    id: str
    parent_id: Optional[str] = None
    content: str
    embedding: Optional[List[float]] = None
    metadata: RAGChunkMetadata
    token_count: int


class KnowledgeNode(BaseModel):
    id: str  # e.g. "destination:singapore"
    agency_id: str
    node_type: str  # "destination", "supplier", "policy", "niche", "activity"
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeEdge(BaseModel):
    id: str
    agency_id: str
    source_node_id: str
    target_node_id: str
    relation: str  # "SUITABLE_FOR", "GOVERNED_BY", "REQUIRES_VISA", "PREFERRED_SUPPLIER"
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class RAGSearchResult(BaseModel):
    chunk: RAGChunk
    score: float
    dense_score: float
    sparse_score: float
    graph_distance: Optional[int] = None
    retrieval_method: str  # "hybrid", "dense", "sparse", "graph"


class GroundedAnswer(BaseModel):
    answer: str
    groundedness_score: float  # 0.0 to 1.0
    is_grounded: bool
    citations: List[RAGSearchResult]
    must_confirm: List[str] = Field(default_factory=list)
    execution_telemetry_id: str
```

---

## 4. Integration into Existing `travel_agency_agent` Codebase

The RAG pipeline directly upgrades existing core modules in `src/` and `spine_api/`:

| Module | Current State | RAG Upgraded State |
|--------|---------------|-------------------|
| `src/intake/specialty_knowledge.py` | Static 5-item dictionary with naive string search | Dynamic RAG over indexed niche guides, regulatory docs, and supplier protocols |
| `src/agents/runtime.py` (`DocumentReadinessAgent`) | Hardcoded link to static markdown scenario file | RAG query over government visa advisories & passport 6-month validity rules by country pair |
| `src/decision/hybrid_engine.py` | Rule matching + pattern cache | RAG-assisted contextual rule resolution for complex traveler preferences |
| `spine_api/models/tenant.py` (`BookingDocument`) | Binary files stored, raw extract Fernet encrypted | Document chunking, vector indexing, and grounded citation mapping per trip document |
| `src/decision/override_learning.py` | Override event logging | RAG indexing of senior operator overrides so agents learn from historical human edits |

---

## 5. Phased Implementation Roadmap

```
  Phase 1: RAG Foundation Core (Contracts & Hybrid Store)
  ├── Models (`src/rag/models.py`)
  ├── Hybrid Vector + BM25 Store (`src/rag/store.py`)
  └── Chunker & Embedder (`src/rag/indexer.py`)

  Phase 2: Grounding & Citation Engine
  ├── Groundedness Evaluator (`src/rag/grounding.py`)
  ├── Citation Formatter & Metadata Lineage (`src/rag/citations.py`)
  └── Upgrade `specialty_knowledge.py` to RAG service

  Phase 3: Knowledge Graph Integration (Graph RAG)
  ├── Graph Nodes & Edges Store (`src/rag/graph_store.py`)
  ├── Multi-Hop Graph + Vector Retriever (`src/rag/retriever.py`)
  └── Entity Extractor (`src/rag/graph_extractor.py`)

  Phase 4: Agent & Spine API Integration
  ├── DocumentReadinessAgent RAG Integration
  ├── API Router `spine_api/routers/rag.py` (`POST /api/rag/query`, `POST /api/rag/documents/index`)
  └── Operator UI Traceability & Citation Drawer
```

---

## 6. Open Discussion Points for User Review

Before proceeding with Phase 1 implementation, we invite discussion on the following architectural choices:

1. **Storage Vector Engine**:
   * *Option A (Recommended for current scale)*: SQLite-backed vector store (using cosine similarity on stored embeddings) for zero external infrastructure overhead during development/testing.
   * *Option B*: External Vector DB (pgvector / ChromaDB / Qdrant).

2. **Embedding Model Selection**:
   * OpenAI `text-embedding-3-small` vs Local fallback (`sentence-transformers/all-MiniLM-L6-v2`) via `src/llm/` provider abstraction.

3. **Knowledge Graph Storage**:
   * *Option A (Recommended)*: Lightweight SQLite node/edge relational tables indexed by `agency_id`.
   * *Option B*: NetworkX in-memory graph with persistent serialization.

4. **Integration Scope**:
   * Should we begin by upgrading `SpecialtyKnowledgeService` and `DocumentReadinessAgent` first as the baseline RAG demonstration?
