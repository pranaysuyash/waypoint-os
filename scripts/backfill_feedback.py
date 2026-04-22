import sys
import os
import random
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "spine-api"))

from persistence import TripStore

MOCK_FEEDBACKS = [
    {"rating": 5, "notes": "Absolutely loved the trip! Everything was perfect."},
    {"rating": 5, "notes": "Highly recommend. Alice was very helpful."},
    {"rating": 4, "notes": "Great experience overall. Small delay at the airport but resolved quickly."},
    {"rating": 4, "notes": "Very good planning. The hotel was excellent."},
    {"rating": 3, "notes": "It was okay. Expected better hotel options for the price."},
]

def backfill():
    print("Starting feedback backfill...")
    trips = TripStore.list_trips(limit=500)
    count = 0
    
    for trip in trips:
        # Only backfill trips that don't have real feedback and are older/completed
        analytics = trip.get("analytics", {})
        
        # If already has feedback, skip
        if trip.get("extracted", {}).get("feedback") or analytics.get("review_metadata", {}).get("feedback"):
            continue
            
        # Select random mock feedback
        mock = random.choice(MOCK_FEEDBACKS).copy()
        mock["is_simulated"] = True
        mock["simulated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update extracted packet
        extracted = trip.get("extracted", {})
        extracted["feedback"] = mock
        
        # Update trip
        updates = {
            "extracted": extracted,
            "analytics": {
                **analytics,
                "latest_feedback": mock
            }
        }
        
        TripStore.update_trip(trip["id"], updates)
        count += 1
        
    print(f"Successfully backfilled {count} trips with simulated feedback.")

if __name__ == "__main__":
    backfill()
