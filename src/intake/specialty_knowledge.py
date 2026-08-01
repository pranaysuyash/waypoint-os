from typing import List, Optional
from pydantic import BaseModel
from src.rag.models import DocumentSourceType, HybridSearchQuery
from src.rag.service import RAGService

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
    def identify_niche(
        text: str,
        agency_id: str = "default_agency",
        rag_service: Optional[RAGService] = None,
    ) -> List[SpecialtyKnowledgeEntry]:
        """Identify matching specialty niches using RAG hybrid search with keyword fallback."""
        hits: List[SpecialtyKnowledgeEntry] = []

        if rag_service:
            try:
                search_res = rag_service.search(
                    HybridSearchQuery(
                        query=text,
                        agency_id=agency_id,
                        top_k=3,
                        source_types=[DocumentSourceType.SPECIALTY_KNOWLEDGE],
                    )
                )
                for res in search_res:
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
            except Exception:
                pass

        # Fallback to keyword matching if RAG produced no hits
        if not hits:
            text_lower = text.lower()
            for entry in KNOWLEDGE_BASE.values():
                if any(kw in text_lower for kw in entry.keywords):
                    hits.append(entry)

        return hits

    @staticmethod
    def seed_rag_knowledge(agency_id: str, rag_service: RAGService) -> int:
        """Seed default specialty knowledge entries into RAG store for an agency."""
        count = 0
        for key, entry in KNOWLEDGE_BASE.items():
            doc_id = f"specialty_{key}"
            text_content = (
                f"Niche: {entry.niche}\n"
                f"Keywords: {', '.join(entry.keywords)}\n"
                f"Checklist Items: {', '.join(entry.checklists)}\n"
                f"Compliance Rules: {', '.join(entry.compliance)}\n"
                f"Safety Notes: {entry.safety_notes or ''}\n"
                f"Urgency Level: {entry.urgency}"
            )
            rag_service.index_document(
                document_id=doc_id,
                agency_id=agency_id,
                source_type=DocumentSourceType.SPECIALTY_KNOWLEDGE,
                title=entry.niche,
                text=text_content,
                tags=entry.keywords,
            )
            count += 1
        return count
