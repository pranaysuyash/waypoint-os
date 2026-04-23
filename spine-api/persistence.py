"""
Trip persistence layer for Waypoint OS.

Follows the existing JSON file patterns from /data/fixtures/
Stores trips, assignments, and audit events in JSON files.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from uuid import uuid4
from dataclasses import asdict, is_dataclass
import logging

logger = logging.getLogger(__name__)

# Data directories
DATA_DIR = Path(__file__).parent.parent / "data"
TRIPS_DIR = DATA_DIR / "trips"
ASSIGNMENTS_DIR = DATA_DIR / "assignments"
AUDIT_DIR = DATA_DIR / "audit"

# Ensure directories exist
TRIPS_DIR.mkdir(parents=True, exist_ok=True)
ASSIGNMENTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _make_json_serializable(obj: Any) -> Any:
    """
    Convert an object to a JSON-serializable format.
    Handles dataclasses, nested objects, and primitive types.
    """
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    elif is_dataclass(obj):
        return _make_json_serializable(asdict(obj))
    elif hasattr(obj, '__dict__'):
        # For regular objects with __dict__
        return _make_json_serializable(obj.__dict__)
    else:
        # Fallback: convert to string
        return str(obj)


class TripStore:
    """File-based trip storage using JSON."""
    
    @staticmethod
    def save_trip(trip_data: dict) -> str:
        """Save a trip to disk. Returns trip ID."""
        trip_id = trip_data.get("id") or f"trip_{uuid4().hex[:12]}"
        trip_data["id"] = trip_id
        trip_data["saved_at"] = datetime.now(timezone.utc).isoformat()
        
        # Convert to JSON-serializable format
        serializable_data = _make_json_serializable(trip_data)
        
        filepath = TRIPS_DIR / f"{trip_id}.json"
        with open(filepath, "w") as f:
            json.dump(serializable_data, f, indent=2)
        
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
        
        # Convert to JSON-serializable format
        serializable_trip = _make_json_serializable(trip)
        
        filepath = TRIPS_DIR / f"{trip_id}.json"
        with open(filepath, "w") as f:
            json.dump(serializable_trip, f, indent=2)
        
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


from src.analytics.engine import process_trip_analytics

# Override storage directories
OVERRIDES_DIR = DATA_DIR / "overrides"
OVERRIDES_PER_TRIP_DIR = OVERRIDES_DIR / "per_trip"
OVERRIDES_PATTERNS_DIR = OVERRIDES_DIR / "patterns"
OVERRIDES_INDEX_FILE = OVERRIDES_DIR / "index.json"

# Ensure override directories exist
OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)
OVERRIDES_PER_TRIP_DIR.mkdir(parents=True, exist_ok=True)
OVERRIDES_PATTERNS_DIR.mkdir(parents=True, exist_ok=True)


class OverrideStore:
    """File-based override storage using JSONL per trip and pattern files."""
    
    @staticmethod
    def save_override(trip_id: str, override_data: dict) -> str:
        """
        Save an override for a trip. Returns override_id.
        Appends to trip's overrides JSONL file.
        """
        override_id = f"ovr_{uuid4().hex[:12]}"
        override_data["override_id"] = override_id
        override_data["trip_id"] = trip_id
        override_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        # Ensure trip overrides file exists
        trip_overrides_file = OVERRIDES_PER_TRIP_DIR / f"{trip_id}.jsonl"
        
        # Append to JSONL (immutable log)
        with open(trip_overrides_file, "a") as f:
            json.dump(override_data, f)
            f.write("\n")
        
        # Update index
        OverrideStore._update_index(override_id, trip_id, str(trip_overrides_file))
        
        # If scope is "pattern", also add to pattern file
        if override_data.get("scope") == "pattern" and override_data.get("decision_type"):
            OverrideStore._add_pattern_override(override_data)
        
        return override_id
    
    @staticmethod
    def get_overrides_for_trip(trip_id: str) -> list:
        """List all overrides for a trip."""
        trip_overrides_file = OVERRIDES_PER_TRIP_DIR / f"{trip_id}.jsonl"
        
        if not trip_overrides_file.exists():
            return []
        
        overrides = []
        try:
            with open(trip_overrides_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            override = json.loads(line)
                            overrides.append(override)
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        
        return overrides
    
    @staticmethod
    def get_override(override_id: str) -> Optional[dict]:
        """Get a specific override by ID using the index."""
        try:
            index = OverrideStore._load_index()
            if override_id not in index:
                return None
            
            file_path = index[override_id]["file_path"]
            
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            override = json.loads(line)
                            if override.get("override_id") == override_id:
                                return override
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        
        return None
    
    @staticmethod
    def get_active_overrides_for_flag(trip_id: str, flag: str) -> list:
        """Get non-rescinded overrides for a specific flag on a trip."""
        all_overrides = OverrideStore.get_overrides_for_trip(trip_id)
        return [
            o for o in all_overrides
            if o.get("flag") == flag and not o.get("rescinded", False)
        ]
    
    @staticmethod
    def get_pattern_overrides(decision_type: str) -> list:
        """Get all pattern-scope overrides for a decision type."""
        pattern_file = OVERRIDES_PATTERNS_DIR / f"{decision_type}.jsonl"
        
        if not pattern_file.exists():
            return []
        
        overrides = []
        try:
            with open(pattern_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            override = json.loads(line)
                            overrides.append(override)
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        
        return overrides
    
    @staticmethod
    def _add_pattern_override(override_data: dict) -> None:
        """Add an override to the pattern file for its decision type."""
        decision_type = override_data.get("decision_type")
        if not decision_type:
            return
        
        pattern_file = OVERRIDES_PATTERNS_DIR / f"{decision_type}.jsonl"
        
        with open(pattern_file, "a") as f:
            json.dump(override_data, f)
            f.write("\n")
    
    @staticmethod
    def _load_index() -> dict:
        """Load the override index."""
        if not OVERRIDES_INDEX_FILE.exists():
            return {}
        
        try:
            with open(OVERRIDES_INDEX_FILE) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    @staticmethod
    def _update_index(override_id: str, trip_id: str, file_path: str) -> None:
        """Update the override index."""
        index = OverrideStore._load_index()
        index[override_id] = {
            "trip_id": trip_id,
            "file_path": file_path,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with open(OVERRIDES_INDEX_FILE, "w") as f:
            json.dump(index, f, indent=2)


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
    safety = spine_output.get("safety", {}) or {}
    
    trip = {
        "id": f"trip_{uuid4().hex[:12]}",
        "run_id": spine_output.get("run_id"),
        "source": source,
        "status": "new",  # Will be updated as it moves through pipeline
        "created_at": datetime.now(timezone.utc).isoformat(),
        "extracted": packet,
        "validation": validation,
        "decision": decision,
        "safety": safety,
        "raw_input": spine_output.get("meta", {}),
    }
    
    # Calculate analytics payload securely inside python ecosystem
    try:
        analytics = process_trip_analytics(trip)
        trip["analytics"] = analytics.model_dump()
    except Exception as e:
        logger.warning(f"Analytics calculation failed: {e}")
        trip["analytics"] = None
    
    logger.debug(f"Saving trip with data keys: {list(trip.keys())}")
    
    # Make the entire trip JSON serializable before saving
    serializable_trip = _make_json_serializable(trip)
    logger.debug(f"Serializable trip keys: {list(serializable_trip.keys())}")
    
    trip_id = TripStore.save_trip(serializable_trip)
    
    # Log creation
    AuditStore.log_event("trip_created", "system", {
        "trip_id": trip_id,
        "source": source,
    })
    
    return trip_id
