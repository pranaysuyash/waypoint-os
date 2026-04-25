from typing import List, Dict, Any, Optional
from pydantic import BaseModel

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
    def identify_niche(text: str) -> List[SpecialtyKnowledgeEntry]:
        hits = []
        text_lower = text.lower()
        for entry in KNOWLEDGE_BASE.values():
            if any(kw in text_lower for kw in entry.keywords):
                hits.append(entry)
        return hits
