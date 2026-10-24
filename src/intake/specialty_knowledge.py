from typing import List, Optional
import logging
import re

from pydantic import BaseModel
from src.rag.models import DocumentSourceType, HybridSearchQuery, KnowledgeNode
from src.rag.service import RAGService

logger = logging.getLogger(__name__)

class SpecialtyKnowledgeEntry(BaseModel):
    niche: str
    keywords: List[str]
    checklists: List[str]
    compliance: List[str] = []
    safety_notes: Optional[str] = None
    urgency: str = "NORMAL"

KNOWLEDGE_BASE = {
    "academic_research": SpecialtyKnowledgeEntry(
        niche="Academic Research Logistics",
        keywords=["grant", "field site", "sampling", "research", "pi", "professor", "university"],
        checklists=["ATA Carnet for Sensors", "Research Visa Verification", "Hazmat Manifest (Batteries)", "Cold Chain Protocol"],
        compliance=["Fly America Act", "Nagoya Protocol Disclosure"],
        safety_notes="Coordinate with institutional field safety office for remote site tracking.",
        urgency="HIGH"
    ),
    "human_remains": SpecialtyKnowledgeEntry(
        niche="Human Remains Repatriation",
        keywords=["repatriation", "mortuary", "remains", "death certificate", "funeral", "casket"],
        checklists=["Consular Clearance", "Laissez-Passer for Corpse", "Zinc-lined Casket Compliance", "Mortuary Lead-in Time"],
        compliance=["IATA TACT Rules", "Health Department Burial Permit"],
        safety_notes="High emotional sensitivity required. Direct dial to airline cargo desk mandatory.",
        urgency="CRITICAL"
    ),
    "sub_aquatic": SpecialtyKnowledgeEntry(
        niche="Sub-Aquatic & Diving Operations",
        keywords=["diving", "saturation", "rebreather", "compressor", "nitrox", "scuba"],
        checklists=["DAN Insurance Verification", "Hyperbaric Chamber Proximity", "Cylinder Hydro-test Check", "Oxygen Supply Log"],
        compliance=["PADI/NAUI Professional Standards", "Local Maritime Authority Registration"],
        safety_notes="Strict no-fly time calculation required after last dive (minimum 24h recommended).",
        urgency="NORMAL"
    ),
    "medical_tourism": SpecialtyKnowledgeEntry(
        niche="Medical Tourism & Post-Op Recovery",
        keywords=["surgery", "recovery", "post-op", "dental", "elective", "clinic", "treatment", "patient"],
        checklists=["Medical Records Transfer Protocol", "Physician Fit-to-Fly Clearance", "Ground Transport (Reclining)", "Post-Op Diet Coordination"],
        compliance=["HIPAA/GDPR Data Handling", "Local Health Authority Facility Licensing"],
        safety_notes="Verify proximity to emergency care and 24/7 nursing availability at recovery site.",
        urgency="HIGH"
    ),
    "mice_logistics": SpecialtyKnowledgeEntry(
        niche="MICE (Meetings & Incentives)",
        keywords=["conference", "exhibition", "incentive", "convention", "delegate", "summit", "keynote"],
        checklists=["Rooming List Automation", "VAT Reclamation Eligibility", "Breakout Session AV Mapping", "VIP Manifest Coordination"],
        compliance=["Force Majeure Contract Clause", "Group Insurance Liability"],
        safety_notes="Ensure ADA compliance for all venue transitions and dietary manifest for all plenary sessions.",
        urgency="NORMAL"
    )
}

class SpecialtyKnowledgeService:
    @staticmethod
    def ensure_seeded(agency_id: str, rag_service: RAGService) -> bool:
        """Seed the specialty knowledge base + graph nodes once per agency.

        Idempotent: a no-op when the agency already holds specialty chunks.
        Each entry is indexed WITH an entity reference to its graph node so
        the retriever's graph boost can fire; nodes carry the entry keywords
        so a query mentioning any keyword matches the niche.
        """
        try:
            if rag_service.store.count_chunks(
                agency_id, source_type=DocumentSourceType.SPECIALTY_KNOWLEDGE.value
            ) > 0:
                return False
            seeded = 0
            for key, entry in KNOWLEDGE_BASE.items():
                node_id = f"niche:{key}"
                rag_service.index_document(
                    document_id=f"specialty_{key}",
                    agency_id=agency_id,
                    source_type=DocumentSourceType.SPECIALTY_KNOWLEDGE,
                    title=entry.niche,
                    text=(
                        f"Niche: {entry.niche}\n"
                        f"Keywords: {', '.join(entry.keywords)}\n"
                        f"Checklist Items: {', '.join(entry.checklists)}\n"
                        f"Compliance Rules: {', '.join(entry.compliance)}\n"
                        f"Safety Notes: {entry.safety_notes or ''}\n"
                        f"Urgency Level: {entry.urgency}"
                    ),
                    tags=entry.keywords,
                    entity_references=[node_id],
                )
                rag_service.add_node(KnowledgeNode(
                    id=node_id,
                    agency_id=agency_id,
                    node_type="niche",
                    label=entry.niche,
                    properties={
                        "keywords": entry.keywords,
                        "urgency": entry.urgency,
                    },
                ))
                seeded += 1
            logger.info("Seeded %d specialty knowledge entries for agency %s", seeded, agency_id)
            return True
        except Exception as exc:
            # Seeding failure must never break intake — but it must be VISIBLE.
            logger.warning("Specialty knowledge seeding failed for agency %s: %s", agency_id, exc)
            return False

    @staticmethod
    def identify_niche(
        text: str,
        agency_id: str = "default_agency",
        rag_service: Optional[RAGService] = None,
    ) -> List[SpecialtyKnowledgeEntry]:
        """Identify matching specialty niches using RAG hybrid search with keyword fallback."""
        hits: List[SpecialtyKnowledgeEntry] = []

        if rag_service:
            try:
                SpecialtyKnowledgeService.ensure_seeded(agency_id, rag_service)
                search_res = rag_service.search(
                    HybridSearchQuery(
                        query=text,
                        agency_id=agency_id,
                        top_k=3,
                        source_types=[DocumentSourceType.SPECIALTY_KNOWLEDGE],
                    )
                )
                # Relevance floor (eval-gate finding, 2026-10-22): RRF always
                # ranks SOMETHING top-k — raw fused scores are rank-derived
                # and never zero — so an unfiltered consumer "matched" every
                # query. Accept a hit only when it carries real lexical
                # evidence: a substantive query token present in the chunk.
                query_tokens = {
                    w.lower() for w in re.findall(r"\w+", text or "") if len(w) > 3
                }
                relevant_res = [
                    res
                    for res in search_res
                    if query_tokens
                    and (
                        query_tokens & set(re.findall(r"\w+", res.chunk.content.lower()))
                        or query_tokens
                        & set(re.findall(r"\w+", res.chunk.metadata.title.lower()))
                    )
                ]
                for res in relevant_res:
                    doc_id = res.chunk.metadata.document_id
                    key = doc_id.replace("specialty_", "")
                    if key in KNOWLEDGE_BASE and KNOWLEDGE_BASE[key] not in hits:
                        hits.append(KNOWLEDGE_BASE[key])
                    else:
                        niche_title = res.chunk.metadata.title.lower()
                        chunk_text = res.chunk.content.lower()
                        for entry in KNOWLEDGE_BASE.values():
                            if entry.niche.lower() in niche_title or entry.niche.lower() in chunk_text:
                                if entry not in hits:
                                    hits.append(entry)
            except Exception as exc:
                # Abstain-with-reason, never silently: the keyword fallback
                # below still serves, but the degradation is logged.
                logger.warning(
                    "RAG specialty lookup failed for agency %s (%s); keyword fallback served",
                    agency_id, exc,
                )

        # Fallback to keyword matching if RAG produced no hits
        if not hits:
            text_lower = text.lower()
            for entry in KNOWLEDGE_BASE.values():
                if any(kw in text_lower for kw in entry.keywords):
                    hits.append(entry)

        return hits

    # seed_rag_knowledge removed 2026-10-22 — superseded by ensure_seeded,
    # which is idempotent (count-guarded), threads entity_references so the
    # retriever's graph boost can fire, and registers graph nodes.
    # Removal analysis (doctrine §6): behavior fully covered; sole prior
    # caller (tests/test_rag_integration.py) migrated to ensure_seeded.
