"""RAG (Retrieval Augmented Generation) API Router for Spine API.

Exposes endpoints for hybrid search, grounded answer generation, document indexing,
Knowledge Graph management, and service status, scoped to the authenticated
agency.

Tenant isolation: every store query filters on the authenticated agency's id
(application-level scoping in ``SQLiteRAGStore``). This is NOT database-level
RLS — DB-enforced isolation is the Postgres endgame
(``Docs/architecture/DURABLE_STORE_ENDGAME_2026-09-08.md``).

Hardening (mount, 2026-10-22): input caps on indexing and querying, bounded
top_k/alpha, canonical rate limiting, contract violations surfaced as 400
(vs unexpected failures as opaque 500s), and a truthful /rag/status surface.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency
from spine_api.core.rate_limiter import limiter
from spine_api.models.tenant import Agency

from src.rag.models import (
    DocumentSourceType,
    KnowledgeNode,
    KnowledgeEdge,
)
from src.rag.service import RAGService, get_default_rag_service

logger = logging.getLogger("spine_api.rag")

router = APIRouter(prefix="/api/v1/rag")

# Input caps — an indexed document costs chunking + one embedding batch, so
# its size is the cost lever. Query length bounds lexical work.
MAX_INDEX_TEXT_CHARS = 200_000
MAX_QUERY_CHARS = 4_000
MAX_TITLE_CHARS = 300
MAX_DOC_ID_CHARS = 200
MAX_TAGS = 20
MAX_TAG_CHARS = 100

# Corpus license governance (CoverWise manifest pattern): every indexed
# document declares its redistribution posture.
ALLOWED_LICENSE_CLASSES = {"agency_owned", "redistribution_safe", "local_eval_only"}


def get_rag_service() -> RAGService:
    """Depends wrapper over the canonical process-wide factory — never a
    parallel instance (src.rag.service owns the singleton)."""
    return get_default_rag_service()


def _validate_index_request(req: "IndexDocumentRequest") -> None:
    if len(req.text) > MAX_INDEX_TEXT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Document text exceeds the {MAX_INDEX_TEXT_CHARS} character cap.",
        )
    if len(req.tags) > MAX_TAGS or any(len(t) > MAX_TAG_CHARS for t in req.tags):
        raise HTTPException(
            status_code=422,
            detail=f"tags must hold at most {MAX_TAGS} entries of {MAX_TAG_CHARS} characters.",
        )
    if req.license_class not in ALLOWED_LICENSE_CLASSES:
        raise HTTPException(
            status_code=422,
            detail=f"license_class must be one of {sorted(ALLOWED_LICENSE_CLASSES)}.",
        )


class IndexDocumentRequest(BaseModel):
    document_id: str = Field(max_length=MAX_DOC_ID_CHARS)
    source_type: DocumentSourceType
    title: str = Field(max_length=MAX_TITLE_CHARS)
    text: str
    canonical_url: Optional[str] = Field(default=None, max_length=2_000)
    file_path: Optional[str] = Field(default=None, max_length=1_000)
    tags: List[str] = Field(default_factory=list)
    license_class: str = Field(default="agency_owned", max_length=40)


class RAGQueryRequest(BaseModel):
    query: str = Field(max_length=MAX_QUERY_CHARS)
    top_k: int = Field(default=5, ge=1, le=50)
    source_types: Optional[List[DocumentSourceType]] = None
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    include_graph: bool = True


@router.get("/status")
def rag_status(
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Truthful service status: live provider, corpus provenance, lexical leg."""
    return rag.status(agency_id=agency.id)


@router.get("/documents")
def list_documents(
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Indexed documents for the current agency, with license governance."""
    return {"items": rag.store.list_documents(agency.id), "total": None}


@limiter.limit("60/minute")
@router.post("/query")
def query_rag(
    request: Request,
    req: RAGQueryRequest,
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Execute hybrid search & grounded answer generation for the current agency."""
    try:
        grounded = rag.query_and_ground(
            query=req.query,
            agency_id=agency.id,
            source_types=req.source_types,
            top_k=req.top_k,
        )
        payload = grounded.model_dump()
        # Payload hygiene: vectors are provider internals (up to 1536 floats
        # per citation) — the UI needs the citation, not the embedding.
        for citation in payload.get("citations", []):
            citation["chunk"]["embedding"] = None
        return payload
    except HTTPException:
        raise
    except ValueError as e:
        # Contract violations (ours) are safe to echo; unexpected failures are not.
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.error("RAG query failed for agency %s", agency.id, exc_info=True)
        raise HTTPException(status_code=500, detail="RAG query failed.")


@limiter.limit("30/minute")
@router.post("/documents/index")
def index_document(
    request: Request,
    req: IndexDocumentRequest,
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Index a new document text into the agency RAG repository."""
    _validate_index_request(req)
    try:
        chunks = rag.index_document(
            document_id=req.document_id,
            agency_id=agency.id,
            source_type=req.source_type,
            title=req.title,
            text=req.text,
            canonical_url=req.canonical_url,
            file_path=req.file_path,
            tags=req.tags,
            license_class=req.license_class,
        )
        # Cost visibility (FND-0361 sweep): when the semantic lane served, the
        # last batch forensics record carries the char-derived INR estimate.
        cost_estimate = getattr(rag.embedding_provider, "last_call_record", {}).get(
            "cost_estimate_inr"
        )
        return {
            "status": "indexed",
            "document_id": req.document_id,
            "chunks_created": len(chunks),
            "embedding_model": rag.embedding_provider.model_name,
            "embedding_cost_estimate_inr": cost_estimate,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.error("Document indexing failed for agency %s", agency.id, exc_info=True)
        raise HTTPException(status_code=500, detail="RAG indexing failed.")


@router.get("/nodes")
def get_knowledge_nodes(
    node_type: Optional[str] = Query(None),
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Get Knowledge Graph nodes for current agency."""
    nodes = rag.get_nodes(agency_id=agency.id, node_type=node_type)
    return {"items": nodes, "total": len(nodes)}


@router.post("/nodes")
def add_knowledge_node(
    node: KnowledgeNode,
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Add or update a Knowledge Graph node for current agency."""
    if node.agency_id != agency.id:
        node.agency_id = agency.id
    rag.add_node(node)
    return {"status": "ok", "node_id": node.id}


@router.post("/edges")
def add_knowledge_edge(
    edge: KnowledgeEdge,
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Add or update a Knowledge Graph edge for current agency."""
    if edge.agency_id != agency.id:
        edge.agency_id = agency.id
    rag.add_edge(edge)
    return {"status": "ok", "edge_id": edge.id}
