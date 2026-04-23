import json
import random
from datetime import datetime, timedelta

def generate_trip(id_num, status):
    created_at = (datetime.now() - timedelta(days=random.randint(0, 10))).isoformat()
    updated_at = (datetime.now() - timedelta(hours=random.randint(0, 24))).isoformat()
    
    destinations = ["Paris", "Tokyo", "London", "New York", "Dubai", "Singapore", "Sydney", "Rome", "Bali", "Iceland"]
    purposes = ["leisure", "business", "honeymoon", "family", "adventure"]
    
    dest = random.choice(destinations)
    purpose = random.choice(purposes)
    party_size = random.randint(1, 6)
    budget = random.randint(1000, 20000)
    
    return {
        "id": f"trip_alpha_{id_num:03d}",
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "extracted": {
            "destination": dest,
            "trip_purpose": purpose,
            "party_size": party_size,
            "budget": budget,
            "date_window": "Summer 2026",
            "origin": "London"
        },
        "decision": {
            "confidence_score": round(random.uniform(0.1, 0.95), 2),
            "decision_state": "PROCEED_SAFE" if status == "completed" else "ASK_FOLLOWUP",
            "action": "AUTO_PILOT" if status == "completed" else "MANUAL_REVIEW"
        },
        "analytics": {
            "margin_pct": random.randint(5, 40),
            "quality_score": random.randint(40, 95),
            "requires_review": status in ["new", "assigned", "in_progress"]
        },
        "validation": {
            "is_valid": random.random() > 0.1
        },
        "assignedTo": "agent_001" if status in ["assigned", "in_progress"] else None,
        "assignedToName": "Agent Smith" if status in ["assigned", "in_progress"] else None
    }

trips = []
# 10 new
for i in range(1, 11):
    trips.append(generate_trip(i, "new"))
# 10 assigned
for i in range(11, 21):
    trips.append(generate_trip(i, "assigned"))
# 5 in_progress
for i in range(21, 26):
    trips.append(generate_trip(i, "in_progress"))
# 3 completed
for i in range(26, 29):
    trips.append(generate_trip(i, "completed"))
# 2 cancelled
for i in range(29, 31):
    trips.append(generate_trip(i, "cancelled"))

with open("/Users/pranay/Projects/travel_agency_agent/data/fixtures/scenario_alpha.json", "w") as f:
    json.dump(trips, f, indent=2)

print(f"Generated 30 trips in scenario_alpha.json")
