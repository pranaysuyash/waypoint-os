import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Add the project root to sys.path so we can import from src and spine-api
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from spine_api.persistence import TripStore, save_processed_trip
from src.analytics.engine import process_trip_analytics


def seed_trips(num_trips: int = 15):
    import random

    destinations = ["Maldives", "Paris", "New York", "Dubai", "Swiss Alps", "Tokyo", "Bali", "Safari (Kenya)"]
    trip_types = ["Honeymoon", "Family", "Corporate", "Solo", "Adventure", "Luxury"]
    statuses = ["new", "assigned", "in_progress", "completed", "cancelled"]

    print(f"Seeding {num_trips} simulated trips into the database...")

    for i in range(num_trips):
        trip_id = f"trip_seed_{uuid4().hex[:8]}"
        destination = random.choice(destinations)
        trip_type = random.choice(trip_types)
        party_size = random.randint(1, 8)
        created_days_ago = random.randint(0, 30)
        created_at = (datetime.now(timezone.utc) - timedelta(days=created_days_ago)).isoformat()
        
        status = random.choice(statuses)

        # Mock structured data representing a processed spine_output
        packet = {
            "trip_metadata": {
                "destination": destination,
                "primary_intent": trip_type,
                "date_window": "Sometime next month",
            },
            "party_profile": {
                "size": party_size,
                "composition_tags": ["budget_conscious"] if random.random() > 0.7 else ["luxury"]
            },
            "budget": {
                "value": random.randint(50000, 800000)
            },
            "ambiguities": ["Missing flight preferences"] if random.random() > 0.8 else []
        }

        # Mock decision based on status and chance
        decision_action = "PROCEED" if status in ["completed", "in_progress"] else random.choice(["PROCEED", "CLARIFY", "BLOCK"])
        decision = {
            "action": decision_action,
            "blockers": ["Awaiting passports"] if decision_action == "BLOCK" else []
        }

        safety = {
            "leakage_passed": random.random() > 0.1,  # 90% passed
            "leakage_errors": [] if random.random() > 0.1 else ["detected internal URL"]
        }

        # The base trip object format that save_processed_trip normally handles internally
        spine_output_mock = {
            "run_id": f"run_{uuid4().hex[:8]}",
            "packet": packet,
            "validation": {},
            "decision": decision,
            "safety": safety,
            "meta": {
                "stage": "discovery",
                "operating_mode": "normal_intake",
                "execution_ms": random.uniform(150.0, 800.0)
            }
        }

        # The save_processed_trip method internally calls process_trip_analytics on this trip 
        # so analytics payload will be natively generated.
        saved_id = save_processed_trip(spine_output_mock, source="seed_script")
        
        # Now artificially update dates and status overriding what save_processed_trip defaulted to
        TripStore.update_trip(saved_id, {
            "id": trip_id,
            "status": status,
            "created_at": created_at
        })
        
        # If it's old enough to be "late" or has a clarifying decision, maybe flag requires_review
        trip_data = TripStore.get_trip(trip_id)
        if trip_data and trip_data.get("analytics") and trip_data["analytics"].get("margin_pct", 100) < 15:
            print(f" -> Generated low-margin trip: {trip_id} ({destination})")
            
    print("Seeding complete. Run the FastAPI dev server to see analytics in action.")

if __name__ == "__main__":
    seed_trips()
