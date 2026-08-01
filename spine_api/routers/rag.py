"""RAG (Retrieval Augmented Generation) API Router for Spine API.

Exposes endpoints for hybrid search, grounded answer generation, document indexing,
and Knowledge Graph management with multi-tenant RLS protection.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency

from src.rag.models import (
    DocumentSourceType,
    KnowledgeNode,
    KnowledgeEdge,
)
from src.rag.service import RAGService

logger = logging.getLogger("spine_api.rag")

router = APIRouter()

# Single shared RAG service instance for the Spine API process
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(db_path="data/rag_store.db")
    return _rag_service


class IndexDocumentRequest(BaseModel):
    document_id: str
    source_type: DocumentSourceType
    title: str
    text: str
    canonical_url: Optional[str] = None
    file_path: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    source_types: Optional[List[DocumentSourceType]] = None
    alpha: float = 0.5
    include_graph: bool = True


@router.post("/rag/query")
def query_rag(
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
        return grounded
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/documents/index")
def index_document(
    req: IndexDocumentRequest,
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Index a new document text into the agency RAG repository."""
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
        )
        return {
            "status": "indexed",
            "document_id": req.document_id,
            "chunks_created": len(chunks),
        }
    except Exception as e:
        logger.error(f"Document indexing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/nodes")
def get_knowledge_nodes(
    node_type: Optional[str] = Query(None),
    agency: Agency = Depends(get_current_agency),
    rag: RAGService = Depends(get_rag_service),
):
    """Get Knowledge Graph nodes for current agency."""
    nodes = rag.get_nodes(agency_id=agency.id, node_type=node_type)
    return {"items": nodes, "total": len(nodes)}


@router.post("/rag/nodes")
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


@router.post("/rag/edges")
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
