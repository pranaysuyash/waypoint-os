import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.intake.frontier_orchestrator import run_frontier_orchestration
from src.intake.packet_models import CanonicalPacket
from src.intake.decision import DecisionResult, ConfidenceScorecard

def test_specialty_detection():
    print("--- Testing Specialty Knowledge Detection ---")
    
    # 1. Academic Case
    acad_packet = CanonicalPacket(
        packet_id="ACAD-001",
        stage="discovery",
        operating_mode="normal_intake",
        raw_note="Planning a research trip for grant #123. Need sampling permits and ATA Carnet.",
        facts={}
    )
    acad_decision = DecisionResult(
        packet_id="ACAD-001",
        current_stage="discovery",
        operating_mode="normal_intake",
        decision_state="PROCEED_SAFE",
        commercial_decision="PROCEED_SAFE",
        confidence=ConfidenceScorecard(overall=0.95)
    )
    
    acad_res = run_frontier_orchestration(acad_packet, acad_decision)
    print(f"\n[ACADEMIC] Found {len(acad_res.specialty_knowledge)} niche hits:")
    for hit in acad_res.specialty_knowledge:
        print(f" - {hit.niche} (Urgency: {hit.urgency})")
        print(f"   Checklists: {hit.checklists}")

    # 2. Repatriation Case
    repat_packet = CanonicalPacket(
        packet_id="REPAT-001",
        stage="discovery",
        operating_mode="normal_intake",
        raw_note="Urgent repatriation of remains. Need death certificate and consular clearance.",
        facts={}
    )
    repat_decision = DecisionResult(
        packet_id="REPAT-001",
        current_stage="discovery",
        operating_mode="normal_intake",
        decision_state="ESCALATE_RECOVERY",
        commercial_decision="ESCALATE_RECOVERY",
        confidence=ConfidenceScorecard(overall=0.85)
    )
    
    repat_res = run_frontier_orchestration(repat_packet, repat_decision)
    print(f"\n[REPATRIATION] Found {len(repat_res.specialty_knowledge)} niche hits:")
    for hit in repat_res.specialty_knowledge:
        print(f" - {hit.niche} (Urgency: {hit.urgency})")
        print(f"   Compliance: {hit.compliance}")

    # 3. Diving Case
    dive_packet = CanonicalPacket(
        packet_id="DIVE-001",
        stage="discovery",
        operating_mode="normal_intake",
        raw_note="Booking a rebreather diving expedition in Palau.",
        facts={}
    )
    dive_decision = DecisionResult(
        packet_id="DIVE-001",
        current_stage="discovery",
        operating_mode="normal_intake",
        decision_state="PROCEED_SAFE",
        commercial_decision="PROCEED_SAFE",
        confidence=ConfidenceScorecard(overall=0.98)
    )
    
    dive_res = run_frontier_orchestration(dive_packet, dive_decision)
    print(f"\n[DIVING] Found {len(dive_res.specialty_knowledge)} niche hits:")
    for hit in dive_res.specialty_knowledge:
        print(f" - {hit.niche}")
        print(f"   Safety Note: {hit.safety_notes}")

    # 4. Medical Case
    med_packet = CanonicalPacket(
        packet_id="MED-001",
        stage="discovery",
        operating_mode="normal_intake",
        raw_note="Client traveling to Istanbul for dental surgery and post-op recovery.",
        facts={}
    )
    med_decision = DecisionResult(
        packet_id="MED-001",
        current_stage="discovery",
        operating_mode="normal_intake",
        decision_state="PROCEED_SAFE",
        commercial_decision="PROCEED_SAFE",
        confidence=ConfidenceScorecard(overall=0.92)
    )
    med_res = run_frontier_orchestration(med_packet, med_decision)
    print(f"\n[MEDICAL] Found {len(med_res.specialty_knowledge)} niche hits:")
    for hit in med_res.specialty_knowledge:
        print(f" - {hit.niche} (Urgency: {hit.urgency})")
        print(f"   Checklists: {hit.checklists}")

    # 5. MICE Case
    mice_packet = CanonicalPacket(
        packet_id="MICE-001",
        stage="discovery",
        operating_mode="normal_intake",
        raw_note="Organizing an annual summit for 50 delegates in Singapore.",
        facts={}
    )
    mice_decision = DecisionResult(
        packet_id="MICE-001",
        current_stage="discovery",
        operating_mode="normal_intake",
        decision_state="PROCEED_SAFE",
        commercial_decision="PROCEED_SAFE",
        confidence=ConfidenceScorecard(overall=0.96)
    )
    mice_res = run_frontier_orchestration(mice_packet, mice_decision)
    print(f"\n[MICE] Found {len(mice_res.specialty_knowledge)} niche hits:")
    for hit in mice_res.specialty_knowledge:
        print(f" - {hit.niche}")
        print(f"   Checklists: {hit.checklists}")

if __name__ == "__main__":
    test_specialty_detection()
