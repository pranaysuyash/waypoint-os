import json
import os
from datetime import datetime, timezone, timedelta
import random

# Ensure data directories exist
DATA_DIR = "/Users/pranay/Projects/travel_agency_agent/data/fixtures"
os.makedirs(DATA_DIR, exist_ok=True)

def generate_frontier_scenario(id_num, title, category, sentiment=0.9, commercial_status="paid"):
    """
    Generates a high-fidelity Frontier scenario with sentiment and commercial data.
    """
    now = datetime.now(timezone.utc)
    
    return {
        "id": f"sc_frontier_{id_num:03d}",
        "title": title,
        "category": category,
        "created_at": (now - timedelta(days=2)).isoformat(),
        "updated_at": now.isoformat(),
        "trip_data": {
            "destination": "Amangiri, Utah",
            "party_size": 4,
            "budget": 25000,
            "currency": "USD"
        },
        "frontier_state": {
            "sentiment_score": sentiment,
            "emotional_trend": "STABLE" if sentiment > 0.8 else "VOLATILE",
            "ghost_workflow_status": "MONITORING",
            "risk_level": "LOW" if sentiment > 0.7 else "CRITICAL"
        },
        "commercial_ledger": {
            "total_cost": 25000,
            "paid_amount": 25000 if commercial_status == "paid" else 18750,
            "status": commercial_status,
            "fx_rate_at_quote": 1.0,
            "fx_rate_current": 1.02 if category == "commercial" else 1.0,
            "commission_expected": 2500,
            "commission_received": 0
        },
        "regulatory_compliance": {
            "gdpr_status": "COMPLIANT",
            "data_retention_until": (now + timedelta(days=365*7)).isoformat(),
            "special_handling": ["MEDICAL_PII"] if "medical" in title.lower() else []
        },
        "audit_logs": [
            {"event": "TRIP_CREATED", "timestamp": (now - timedelta(days=2)).isoformat(), "actor": "system"},
            {"event": "SENTIMENT_CHECK", "timestamp": now.isoformat(), "actor": "ghost_concierge", "value": sentiment}
        ]
    }

# Scenario 318: Fractional Payment Failure (Commercial)
s318 = generate_frontier_scenario(318, "Fractional Payment Failure: Group Villa", "commercial", sentiment=0.6, commercial_status="partial")

# Scenario 319: Medical Data Privacy Request (Regulatory)
s319 = generate_frontier_scenario(319, "Right to be Forgotten: Medical PII Purge", "regulatory", sentiment=0.95)

# Scenario 320: Hostile Sentiment UI Pivot (Visual)
s320 = generate_frontier_scenario(320, "Hostile Sentiment Pivot: Airport Strike", "visual", sentiment=0.2)

scenarios = [s318, s319, s320]

for s in scenarios:
    filename = os.path.join(DATA_DIR, f"{s['id']}.json")
    with open(filename, "w") as f:
        json.dump(s, f, indent=2)
    print(f"Generated {filename}")

print(f"Total Frontier scenarios generated: {len(scenarios)}")
