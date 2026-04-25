import json
import random
from datetime import datetime, timedelta
import os

def generate_academic_scenario():
    """Generates a specialized academic research scenario."""
    scenarios_dir = "/Users/pranay/Projects/travel_agency_agent/data/fixtures"
    os.makedirs(scenarios_dir, exist_ok=True)
    
    trips = [
        {
            "id": "ACAD-2026-001",
            "status": "new",
            "destination": "Manaus, Brazil (Amazon Basin)",
            "customerMessage": "Planning a biodiversity sampling trip for Grant #NSF-BIO-2026. 4 researchers traveling with specialized soil sensors and drone equipment. Need to confirm Nagoya Protocol compliance and ATA Carnet requirements for Brazil.",
            "agentNotes": "Principal Investigator: Dr. Aris Thorne. University of Seattle grant funding.",
            "extracted": {
                "destination": "Manaus",
                "trip_purpose": "academic research field site",
                "party_size": 4,
                "budget": 25000,
                "date_window": "Sept 2026",
                "origin": "Seattle"
            },
            "decision": {
                "confidence_score": 0.92,
                "decision_state": "PROCEED_SAFE",
                "action": "AUTO_PILOT"
            },
            "analytics": {
                "margin_pct": 12,
                "quality_score": 88,
                "requires_review": True
            }
        },
        {
            "id": "REPAT-2026-042",
            "status": "new",
            "destination": "Dublin, Ireland",
            "customerMessage": "Urgent: Need to arrange repatriation of remains for late Mr. John Doe to New York. Death certificate issued in Dublin. Need to coordinate with local mortuary and airline cargo for consular clearance.",
            "agentNotes": "Family requesting urgent transport. High emotional sensitivity.",
            "extracted": {
                "destination": "New York",
                "trip_purpose": "human remains repatriation",
                "party_size": 1,
                "budget": 15000,
                "date_window": "Immediate",
                "origin": "Dublin"
            },
            "decision": {
                "confidence_score": 0.75,
                "decision_state": "ESCALATE_RECOVERY",
                "action": "MANUAL_REVIEW"
            },
            "analytics": {
                "margin_pct": 25,
                "quality_score": 95,
                "requires_review": True
            }
        }
    ]
    
    file_path = os.path.join(scenarios_dir, "scenario_niche_longtail.json")
    with open(file_path, "w") as f:
        json.dump(trips, f, indent=2)
    
    print(f"Generated niche scenario at {file_path}")

if __name__ == "__main__":
    generate_academic_scenario()
