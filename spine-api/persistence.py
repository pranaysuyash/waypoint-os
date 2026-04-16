"""
Trip persistence layer for Waypoint OS.

Follows the existing JSON file patterns from /data/fixtures/
Stores trips, assignments, and audit events in JSON files.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

# Data directories
DATA_DIR = Path(__file__).parent.parent / "data"
TRIPS_DIR = DATA_DIR / "trips"
ASSIGNMENTS_DIR = DATA_DIR / "assignments"
AUDIT_DIR = DATA_DIR / "audit"

# Ensure directories exist
TRIPS_DIR.mkdir(parents=True, exist_ok=True)
ASSIGNMENTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


class TripStore:
    """File-based trip storage using JSON."""
    
    @staticmethod
    def save_trip(trip_data: dict) -> str:
        """Save a trip to disk. Returns trip ID."""
        trip_id = trip_data.get("id") or f"trip_{uuid4().hex[:12]}"
        trip_data["id"] = trip_id
        trip_data["saved_at"] = datetime.now(timezone.utc).isoformat()
        
        filepath = TRIPS_DIR / f"{trip_id}.json"
        with open(filepath, "w") as f:
            json.dump(trip_data, f, indent=2)
        
        return trip_id
    
    @staticmethod
    def get_trip(trip_id: str) -> Optional[dict]:
        """Get a trip by ID."""
        filepath = TRIPS_DIR / f"{trip_id}.json"
        if not filepath.exists():
            return None
        
        with open(filepath) as f:
            return json.load(f)
    
    @staticmethod
    def list_trips(status: Optional[str] = None, limit: int = 100) -> list:
        """List all trips, optionally filtered by status."""
        trips = []
        
        for filepath in sorted(TRIPS_DIR.glob("trip_*.json"), reverse=True):
            try:
                with open(filepath) as f:
                    trip = json.load(f)
                    if status is None or trip.get("status") == status:
                        trips.append(trip)
                    if len(trips) >= limit:
                        break
            except Exception:
                continue
        
        return trips
    
    @staticmethod
    def update_trip(trip_id: str, updates: dict) -> Optional[dict]:
        """Update trip fields."""
        trip = TripStore.get_trip(trip_id)
        if not trip:
            return None
        
        trip.update(updates)
        trip["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        filepath = TRIPS_DIR / f"{trip_id}.json"
        with open(filepath, "w") as f:
            json.dump(trip, f, indent=2)
        
        return trip


class AssignmentStore:
    """Track who is assigned to which trip."""
    
    ASSIGNMENTS_FILE = ASSIGNMENTS_DIR / "assignments.json"
    
    @staticmethod
    def _load_assignments() -> dict:
        """Load all assignments."""
        if not AssignmentStore.ASSIGNMENTS_FILE.exists():
            return {}
        
        with open(AssignmentStore.ASSIGNMENTS_FILE) as f:
            return json.load(f)
    
    @staticmethod
    def _save_assignments(data: dict):
        """Save all assignments."""
        with open(AssignmentStore.ASSIGNMENTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def assign_trip(trip_id: str, agent_id: str, agent_name: str, assigned_by: str):
        """Assign a trip to an agent."""
        assignments = AssignmentStore._load_assignments()
        
        assignments[trip_id] = {
            "trip_id": trip_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "assigned_by": assigned_by,
        }
        
        AssignmentStore._save_assignments(assignments)
        
        # Audit log
        AuditStore.log_event("trip_assigned", assigned_by, {
            "trip_id": trip_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
        })
    
    @staticmethod
    def get_assignment(trip_id: str) -> Optional[dict]:
        """Get assignment for a trip."""
        assignments = AssignmentStore._load_assignments()
        return assignments.get(trip_id)
    
    @staticmethod
    def get_trips_for_agent(agent_id: str) -> list:
        """Get all trips assigned to an agent."""
        assignments = AssignmentStore._load_assignments()
        return [a for a in assignments.values() if a["agent_id"] == agent_id]
    
    @staticmethod
    def unassign_trip(trip_id: str, unassigned_by: str):
        """Remove assignment from a trip."""
        assignments = AssignmentStore._load_assignments()
        
        if trip_id in assignments:
            agent_name = assignments[trip_id]["agent_name"]
            del assignments[trip_id]
            AssignmentStore._save_assignments(assignments)
            
            AuditStore.log_event("trip_unassigned", unassigned_by, {
                "trip_id": trip_id,
                "previous_agent": agent_name,
            })


class AuditStore:
    """Simple audit logging to JSON files."""
    
    AUDIT_FILE = AUDIT_DIR / "events.json"
    MAX_EVENTS = 10000  # Rotate after this many
    
    @staticmethod
    def _load_events() -> list:
        """Load all events."""
        if not AuditStore.AUDIT_FILE.exists():
            return []
        
        with open(AuditStore.AUDIT_FILE) as f:
            return json.load(f)
    
    @staticmethod
    def _save_events(events: list):
        """Save events, rotating if too many."""
        # Keep only last MAX_EVENTS
        if len(events) > AuditStore.MAX_EVENTS:
            events = events[-AuditStore.MAX_EVENTS:]
        
        with open(AuditStore.AUDIT_FILE, "w") as f:
            json.dump(events, f, indent=2)
    
    @staticmethod
    def log_event(event_type: str, user_id: str, details: dict):
        """Log an audit event."""
        events = AuditStore._load_events()
        
        events.append({
            "id": f"evt_{uuid4().hex[:12]}",
            "type": event_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
        })
        
        AuditStore._save_events(events)
    
    @staticmethod
    def get_events(limit: int = 100) -> list:
        """Get recent events."""
        events = AuditStore._load_events()
        return events[-limit:]
    
    @staticmethod
    def get_events_for_trip(trip_id: str) -> list:
        """Get events for a specific trip."""
        events = AuditStore._load_events()
        return [
            e for e in events
            if e.get("details", {}).get("trip_id") == trip_id
        ]


# Convenience functions
def save_processed_trip(spine_output: dict, source: str = "unknown") -> str:
    """
    Convert spine output to a savable trip and persist it.
    
    This is called by the spine-api after processing.
    """
    # Extract data from spine output
    packet = spine_output.get("packet", {}) or {}
    validation = spine_output.get("validation", {}) or {}
    decision = spine_output.get("decision", {}) or {}
    
    trip = {
        "id": f"trip_{uuid4().hex[:12]}",
        "run_id": spine_output.get("run_id"),
        "source": source,
        "status": "new",  # Will be updated as it moves through pipeline
        "created_at": datetime.now(timezone.utc).isoformat(),
        "extracted": packet,
        "validation": validation,
        "decision": decision,
        "raw_input": spine_output.get("meta", {}),
    }
    
    trip_id = TripStore.save_trip(trip)
    
    # Log creation
    AuditStore.log_event("trip_created", "system", {
        "trip_id": trip_id,
        "source": source,
    })
    
    return trip_id
