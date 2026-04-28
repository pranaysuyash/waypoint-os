"""
Trip persistence layer for Waypoint OS.

Follows the existing JSON file patterns from /data/fixtures/
Stores trips, assignments, and audit events in JSON files.

WARNING: TripStore saves plaintext JSON. Real user PII is blocked in
dogfood mode by the privacy guard. Before beta/launch, configure:
  - DATA_PRIVACY_MODE=beta or production,
  - Encryption for TripStore fields, and/or
  - PostgreSQL migration for trip data.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from uuid import uuid4
from dataclasses import asdict, is_dataclass
import logging
import threading
from contextlib import contextmanager

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


def _is_process_dead(pid: int) -> bool:
    """True if the process does not exist or is a zombie (defunct)."""
    import os as _os, subprocess as _subprocess
    try:
        _os.kill(pid, 0)
    except OSError:
        return True  # process doesn't exist at all
    # Process exists — check if it's a zombie
    try:
        out = _subprocess.check_output(
            ["ps", "-o", "state=", "-p", str(pid)],
            stderr=_subprocess.DEVNULL,
            text=True,
        ).strip()
        return out.startswith("Z")  # Z = zombie/defunct
    except _subprocess.CalledProcessError:
        return True
    except Exception:
        return False  # conservative: assume alive if we can't check


@contextmanager
def file_lock(filepath: Path, timeout_seconds: float = 30.0):
    """Cross-process file lock using atomic directory creation.

    Uses os.mkdir which is atomic on all platforms. Includes stale-lock
    detection: if the lock directory was created by a process that is no
    longer alive, it is removed and retried.

    Each lock directory contains a PID file so we can detect stale locks
    from crashed processes.
    """
    lock_dir = filepath.with_suffix(filepath.suffix + ".lockdir")
    pid_file = lock_dir / "pid"
    import time as _time, os as _os

    deadline = _time.monotonic() + timeout_seconds
    delay = 0.01
    acquired = False
    last_owner = "none"

    while _time.monotonic() < deadline:
        try:
            _os.mkdir(lock_dir)
            # Write our PID
            with open(pid_file, "w") as f:
                f.write(str(_os.getpid()))
            acquired = True
            break
        except FileExistsError:
            # Check if the lock is stale (owner process dead or zombie)
            try:
                with open(pid_file) as f:
                    pid_str = f.read().strip()
                lock_pid = int(pid_str)
                if _is_process_dead(lock_pid):
                    try:
                        _os.remove(pid_file)
                        _os.rmdir(lock_dir)
                        last_owner = f"pid={lock_pid} (DEAD, removed)"
                        continue  # retry immediately
                    except OSError:
                        last_owner = f"pid={lock_pid} (dead, could not remove stale lock)"
                else:
                    last_owner = f"pid={lock_pid} (alive)"
            except (FileNotFoundError, ValueError):
                last_owner = "unknown (no pid file)"
            _time.sleep(delay)
            delay = min(delay * 1.5, 0.3)

    if not acquired:
        raise TimeoutError(
            f"Could not acquire lock on {lock_dir} within {timeout_seconds}s "
            f"(last owner: {last_owner})"
        )
    try:
        yield
    finally:
        try:
            _os.remove(pid_file)
        except OSError:
            pass
        try:
            _os.rmdir(lock_dir)
        except OSError:
            pass


class TripStore:
    """File-based trip storage using JSON."""
    _lock = threading.Lock()

    @staticmethod
    def save_trip(trip_data: dict, agency_id: Optional[str] = None) -> str:
        """Save a trip to disk. Returns trip ID.

        WARNING: TripStore persists plaintext JSON. Real user PII is blocked
        in dogfood mode by the privacy guard. Before storing real user data,
        enable encryption or migrate to PostgreSQL.
        """
        # Privacy guard: block real-user PII in dogfood mode
        from src.security.privacy_guard import check_trip_data

        check_trip_data(trip_data)

        trip_id = trip_data.get("id") or f"trip_{uuid4().hex[:12]}"
        trip_data["id"] = trip_id
        trip_data["saved_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store agency_id with trip for scoping
        if agency_id:
            trip_data["agency_id"] = agency_id
        
        # Convert to JSON-serializable format
        serializable_data = _make_json_serializable(trip_data)
        
        filepath = TRIPS_DIR / f"{trip_id}.json"
        with TripStore._lock:
            with file_lock(filepath):
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
    def list_trips(status: Optional[str] = None, limit: int = 100, agency_id: Optional[str] = None) -> list:
        """List trips, optionally filtered by status and/or agency."""
        trips = []
        
        for filepath in sorted(TRIPS_DIR.glob("trip_*.json"), reverse=True):
            try:
                with open(filepath) as f:
                    trip = json.load(f)
                    
                    # Filter by agency_id if provided
                    if agency_id and trip.get("agency_id") != agency_id:
                        continue
                    
                    if status is None or trip.get("status") == status:
                        trips.append(trip)
                    if len(trips) >= limit:
                        break
            except Exception:
                continue
        
        return trips
    
    @staticmethod
    def update_trip(trip_id: str, updates: dict) -> Optional[dict]:
        """
        Update trip fields.

        WARNING: TripStore persists plaintext JSON. Real user PII is blocked
        in dogfood mode. Before storing real user data, enable encryption
        or migrate to PostgreSQL.
        """
        # Privacy guard: block updates that inject real-user PII
        from src.security.privacy_guard import check_trip_data

        check_trip_data(updates)
        filepath = TRIPS_DIR / f"{trip_id}.json"
        
        with TripStore._lock:
            with file_lock(filepath):
                trip = TripStore.get_trip(trip_id)
                if not trip:
                    return None
                
                trip.update(updates)
                trip["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                # Convert to JSON-serializable format
                serializable_trip = _make_json_serializable(trip)
                
                with open(filepath, "w") as f:
                    json.dump(serializable_trip, f, indent=2)
                
                return trip


class AssignmentStore:
    """Track who is assigned to which trip."""
    
    ASSIGNMENTS_FILE = ASSIGNMENTS_DIR / "assignments.json"
    _lock = threading.RLock()
    
    @staticmethod
    def _load_assignments() -> dict:
        """Load all assignments."""
        with AssignmentStore._lock:
            if not AssignmentStore.ASSIGNMENTS_FILE.exists():
                return {}
        
            with open(AssignmentStore.ASSIGNMENTS_FILE) as f:
                return json.load(f)
    
    @staticmethod
    def _save_assignments(data: dict):
        """Save all assignments."""
        with AssignmentStore._lock:
            with file_lock(AssignmentStore.ASSIGNMENTS_FILE):
                with open(AssignmentStore.ASSIGNMENTS_FILE, "w") as f:
                    json.dump(data, f, indent=2)
    
    @staticmethod
    def assign_trip(trip_id: str, agent_id: str, agent_name: str, assigned_by: str):
        """Assign a trip to an agent."""
        with AssignmentStore._lock:
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
        with AssignmentStore._lock:
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
    _lock = threading.RLock()
    
    @staticmethod
    def _load_events() -> list:
        """Load all events."""
        with AuditStore._lock:
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
        with AuditStore._lock:
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


# =============================================================================
# Team Member Store
# =============================================================================

TEAM_DIR = DATA_DIR / "team"
TEAM_DIR.mkdir(parents=True, exist_ok=True)


class TeamStore:
    """File-based team member storage using JSON."""

    TEAM_FILE = TEAM_DIR / "members.json"
    _lock = threading.Lock()

    @staticmethod
    def _load_members() -> dict:
        if not TeamStore.TEAM_FILE.exists():
            return {}
        with open(TeamStore.TEAM_FILE) as f:
            return json.load(f)

    @staticmethod
    def _save_members(data: dict):
        with open(TeamStore.TEAM_FILE, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def create_member(member_data: dict) -> str:
        member_id = f"agent_{uuid4().hex[:12]}"
        member_data["id"] = member_id
        member_data["created_at"] = datetime.now(timezone.utc).isoformat()
        member_data["active"] = True

        with TeamStore._lock:
            members = TeamStore._load_members()
            members[member_id] = member_data
            TeamStore._save_members(members)

        AuditStore.log_event("team_member_created", "owner", {
            "member_id": member_id,
            "email": member_data.get("email"),
            "role": member_data.get("role"),
        })
        return member_id

    @staticmethod
    def get_member(member_id: str) -> Optional[dict]:
        members = TeamStore._load_members()
        return members.get(member_id)

    @staticmethod
    def list_members(active_only: bool = False) -> list:
        members = TeamStore._load_members()
        result = list(members.values())
        if active_only:
            result = [m for m in result if m.get("active", True)]
        return result

    @staticmethod
    def update_member(member_id: str, updates: dict) -> Optional[dict]:
        with TeamStore._lock:
            members = TeamStore._load_members()
            if member_id not in members:
                return None
            members[member_id].update(updates)
            members[member_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            TeamStore._save_members(members)
            return members[member_id]

    @staticmethod
    def deactivate_member(member_id: str) -> bool:
        with TeamStore._lock:
            members = TeamStore._load_members()
            if member_id not in members:
                return False
            members[member_id]["active"] = False
            members[member_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            TeamStore._save_members(members)

            AuditStore.log_event("team_member_deactivated", "owner", {
                "member_id": member_id,
            })
            return True


# =============================================================================
# Config Store (pipeline stages + approval thresholds)
# =============================================================================

CONFIG_DIR = DATA_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class ConfigStore:
    """File-based configuration storage for pipeline stages and approval thresholds."""

    PIPELINE_FILE = CONFIG_DIR / "pipeline.json"
    APPROVALS_FILE = CONFIG_DIR / "approvals.json"
    _lock = threading.Lock()

    @staticmethod
    def _load_file(filepath: Path) -> list:
        if not filepath.exists():
            return []
        with open(filepath) as f:
            return json.load(f)

    @staticmethod
    def _save_file(filepath: Path, data: list):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def get_pipeline_stages() -> list:
        return ConfigStore._load_file(ConfigStore.PIPELINE_FILE)

    @staticmethod
    def set_pipeline_stages(stages: list):
        with ConfigStore._lock:
            ConfigStore._save_file(ConfigStore.PIPELINE_FILE, stages)

    @staticmethod
    def get_approval_thresholds() -> list:
        return ConfigStore._load_file(ConfigStore.APPROVALS_FILE)

    @staticmethod
    def set_approval_thresholds(thresholds: list):
        with ConfigStore._lock:
            ConfigStore._save_file(ConfigStore.APPROVALS_FILE, thresholds)


# Convenience functions
def save_processed_trip(
    spine_output: dict,
    source: str = "unknown",
    agency_id: Optional[str] = None,
    user_id: Optional[str] = None,
    follow_up_due_date: Optional[str] = None,
    party_composition: Optional[str] = None,
    pace_preference: Optional[str] = None,
    date_year_confidence: Optional[str] = None,
    lead_source: Optional[str] = None,
    activity_provenance: Optional[str] = None,
    trip_status: str = "new"
) -> str:
    """
    Convert spine output to a savable trip and persist it.
    
    Args:
        spine_output: The processed trip data
        source: Source identifier (e.g., "spine_api", "seed_scenario")
        agency_id: Optional agency ID to scope the trip
        follow_up_due_date: Optional ISO-8601 datetime string for when a follow-up is due
        party_composition: Optional party composition (e.g., "2 adults, 1 toddler")
        pace_preference: Optional travel pace (rushed/normal/relaxed)
        date_year_confidence: Optional date confidence (certain/likely/unsure)
        lead_source: Optional lead source (referral/web/social/other)
        activity_provenance: Optional activity interests
        trip_status: Trip status (default "new", set "incomplete" for partial intakes)
        
    Returns:
        The saved trip ID
    """
    # Extract data from spine output
    packet = spine_output.get("packet", {}) or {}
    validation = spine_output.get("validation", {}) or {}
    decision = spine_output.get("decision", {}) or {}
    safety = spine_output.get("safety", {}) or {}
    
    trip = {
        "id": f"trip_{uuid4().hex[:12]}",
        "run_id": spine_output.get("run_id"),
        "user_id": user_id,
        "source": source,
        "status": trip_status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "follow_up_due_date": follow_up_due_date,  # Track promised follow-up times
        "party_composition": party_composition,  # Who is traveling
        "pace_preference": pace_preference,  # Travel pace preference
        "date_year_confidence": date_year_confidence,  # Date certainty
        "lead_source": lead_source,  # How customer found us
        "activity_provenance": activity_provenance,  # Activity interests
        "extracted": packet,
        "validation": validation,
        "decision": decision,
        "strategy": spine_output.get("strategy"),
        "traveler_bundle": spine_output.get("traveler_bundle"),
        "internal_bundle": spine_output.get("internal_bundle"),
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
    
    trip_id = TripStore.save_trip(serializable_trip, agency_id=agency_id)
    
    # Log creation
    AuditStore.log_event("trip_created", "system", {
        "trip_id": trip_id,
        "source": source,
        "agency_id": agency_id,
    })
    
    return trip_id
