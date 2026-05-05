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

import base64
import json
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from uuid import uuid4
from dataclasses import asdict, is_dataclass
import logging
import threading
from contextlib import contextmanager
import re

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from spine_api.core.database import DATABASE_URL
from spine_api.models.trips import Trip
from src.security.encryption import decrypt, encrypt

logger = logging.getLogger(__name__)

_tripstore_session_makers: dict[int, async_sessionmaker[AsyncSession]] = {}
_tripstore_session_makers_lock = threading.Lock()


def _create_tripstore_session_maker() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def tripstore_session_maker() -> AsyncSession:
    """Return an AsyncSession bound to the current event loop's engine.

    asyncpg/SQLAlchemy internals keep loop-bound synchronization primitives.
    Runtime agents call the async TripStore through a synchronous bridge loop,
    while FastAPI endpoints use the app loop. Keeping one engine/sessionmaker per
    loop prevents cross-loop pool and event mutex reuse.
    """
    loop_id = id(asyncio.get_running_loop())
    with _tripstore_session_makers_lock:
        maker = _tripstore_session_makers.get(loop_id)
        if maker is None:
            maker = _create_tripstore_session_maker()
            _tripstore_session_makers[loop_id] = maker
    return maker()

# Data directories
DATA_DIR = Path(__file__).parent.parent / "data"
TRIPS_DIR = DATA_DIR / "trips"
ASSIGNMENTS_DIR = DATA_DIR / "assignments"
AUDIT_DIR = DATA_DIR / "audit"
PUBLIC_CHECKER_DIR = DATA_DIR / "public_checker"
PUBLIC_CHECKER_UPLOADS_DIR = PUBLIC_CHECKER_DIR / "uploads"
PUBLIC_CHECKER_MANIFESTS_DIR = PUBLIC_CHECKER_DIR / "manifests"

# Ensure directories exist
TRIPS_DIR.mkdir(parents=True, exist_ok=True)
ASSIGNMENTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_CHECKER_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_CHECKER_MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)


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


def _safe_filename(name: str) -> str:
    """Return a filesystem-safe filename while preserving the base name."""
    base = Path(name).name or "upload.bin"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base)


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
                stale_age_seconds = _time.time() - lock_dir.stat().st_mtime if lock_dir.exists() else 0
                if stale_age_seconds > timeout_seconds:
                    try:
                        if pid_file.exists():
                            _os.remove(pid_file)
                        _os.rmdir(lock_dir)
                        last_owner = f"unknown (stale ownerless lock removed after {stale_age_seconds:.1f}s)"
                        continue
                    except OSError:
                        last_owner = "unknown (ownerless stale lock could not be removed)"
                else:
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


class FileTripStore:
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
        with FileTripStore._lock:
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
        """List trips, optionally filtered by status and/or agency.
        
        status accepts a single status (e.g. 'new') or a comma-separated list
        (e.g. 'new,incomplete,needs_followup') for inbox-style multi-status filters.
        """
        allowed_statuses = (
            set(status.split(",")) if status else None
        )
        trips = []
        
        for filepath in sorted(TRIPS_DIR.glob("trip_*.json"), reverse=True):
            try:
                with open(filepath) as f:
                    trip = json.load(f)
                    
                # Filter by agency_id if provided
                if agency_id and trip.get("agency_id") != agency_id:
                    continue
                
                if allowed_statuses is None or trip.get("status") in allowed_statuses:
                    trips.append(trip)
                if len(trips) >= limit:
                    break
            except Exception:
                continue
        
        return trips

    @staticmethod
    def count_trips(status: Optional[str] = None, agency_id: Optional[str] = None) -> int:
        return len(FileTripStore.list_trips(status=status, limit=10000, agency_id=agency_id))
    
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
        
        with FileTripStore._lock:
            with file_lock(filepath):
                trip = FileTripStore.get_trip(trip_id)
                if not trip:
                    return None
                
                trip.update(updates)
                trip["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                # Convert to JSON-serializable format
                serializable_trip = _make_json_serializable(trip)
                
                with open(filepath, "w") as f:
                    json.dump(serializable_trip, f, indent=2)
                
                return trip

    @staticmethod
    def delete_trip(trip_id: str) -> bool:
        filepath = TRIPS_DIR / f"{trip_id}.json"
        if not filepath.exists():
            return False

        with FileTripStore._lock:
            with file_lock(filepath):
                if filepath.exists():
                    filepath.unlink()
                    return True
        return False

    @staticmethod
    def get_booking_data(trip_id: str) -> Optional[dict]:
        """Get booking_data from file store. Returns None if trip missing."""
        trip = FileTripStore.get_trip(trip_id)
        return trip.get("booking_data") if trip else None

    @staticmethod
    def get_pending_booking_data(trip_id: str) -> Optional[dict]:
        """Get pending_booking_data from file store. Returns None if trip missing."""
        trip = FileTripStore.get_trip(trip_id)
        return trip.get("pending_booking_data") if trip else None


class SQLTripStore:
    """PostgreSQL-backed trip storage with dual encryption model.

    Private compartments (internal_bundle, safety, fees, frontier_result,
    traveler_bundle) are blob-encrypted — the entire JSON object is encrypted
    as a single Fernet token. PII-key fields (extracted, raw_input) use
    recursive key-level encryption for individual sensitive values.
    """

    # Fields whose entire JSON blob is encrypted as one Fernet token.
    _PRIVATE_BLOB_FIELDS = frozenset({
        "traveler_bundle",
        "internal_bundle",
        "safety",
        "fees",
        "frontier_result",
        "booking_data",
        "pending_booking_data",
    })

    # Fields where only specific PII sub-keys are encrypted recursively.
    _PII_KEY_FIELDS = frozenset({
        "extracted",
        "raw_input",
    })

    _PII_FIELDS = {
        "address",
        "contact_email",
        "contact_name",
        "contact_phone",
        "customer_email",
        "customer_name",
        "customer_phone",
        "dietary_restrictions",
        "email",
        "full_name",
        "medical_notes",
        "mobile",
        "name",
        "passport",
        "passport_number",
        "phone",
        "phone_number",
        "special_requests",
        "traveler_email",
        "traveler_name",
        "traveler_phone",
    }

    @staticmethod
    def _encrypt_pii(data: Any) -> Any:
        if isinstance(data, dict):
            return {
                key: encrypt(value) if key.lower() in SQLTripStore._PII_FIELDS and isinstance(value, str)
                else SQLTripStore._encrypt_pii(value)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [SQLTripStore._encrypt_pii(item) for item in data]
        return data

    @staticmethod
    def _decrypt_pii(data: Any) -> Any:
        if isinstance(data, dict):
            return {
                key: decrypt(value) if key.lower() in SQLTripStore._PII_FIELDS and isinstance(value, str)
                else SQLTripStore._decrypt_pii(value)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [SQLTripStore._decrypt_pii(item) for item in data]
        return data

    @staticmethod
    def _encrypt_blob(data: Any) -> Any:
        """Encrypt an entire JSON object as a single Fernet token."""
        if data is None:
            return None
        serialized = json.dumps(data, default=str)
        token = encrypt(serialized)
        return {"__encrypted_blob": True, "v": 1, "ciphertext": token}

    @staticmethod
    def _decrypt_blob(data: Any) -> Any:
        """Decrypt a blob-encrypted JSON object back to its original form."""
        if data is None:
            return None
        if isinstance(data, dict) and data.get("__encrypted_blob"):
            token = data.get("ciphertext", "")
            serialized = decrypt(token)
            return json.loads(serialized)
        # Not a blob wrapper — return as-is (handles pre-migration plaintext)
        return data

    @staticmethod
    def _encrypt_field_for_storage(field: str, value: Any) -> Any:
        """Unified encryption entry point for both save_trip and update_trip."""
        if field in SQLTripStore._PRIVATE_BLOB_FIELDS:
            if value is None:
                return None
            if field == "safety" and not value:
                return {}
            return SQLTripStore._encrypt_blob(value)
        if field in SQLTripStore._PII_KEY_FIELDS:
            return SQLTripStore._encrypt_pii(value or {})
        return value

    @staticmethod
    def _decrypt_field_from_storage(field: str, value: Any) -> Any:
        """Unified decryption entry point for _to_dict."""
        if field in SQLTripStore._PRIVATE_BLOB_FIELDS:
            return SQLTripStore._decrypt_blob(value)
        if field in SQLTripStore._PII_KEY_FIELDS:
            return SQLTripStore._decrypt_pii(value or {}) if value else value
        return value

    @staticmethod
    def _parse_datetime(value: Any) -> Any:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                logger.warning("Invalid datetime for Trip.follow_up_due_date: %s", value)
                return None
        return value

    @staticmethod
    def _to_dict(trip_obj: Trip) -> dict:
        return {
            "id": trip_obj.id,
            "run_id": trip_obj.run_id,
            "agency_id": trip_obj.agency_id,
            "user_id": trip_obj.user_id,
            "assigned_to_id": trip_obj.assigned_to_id,
            "source": trip_obj.source,
            "status": trip_obj.status,
            "stage": trip_obj.stage,
            "follow_up_due_date": trip_obj.follow_up_due_date.isoformat() if trip_obj.follow_up_due_date else None,
            "party_composition": trip_obj.party_composition,
            "pace_preference": trip_obj.pace_preference,
            "date_year_confidence": trip_obj.date_year_confidence,
            "lead_source": trip_obj.lead_source,
            "activity_provenance": trip_obj.activity_provenance,
            "extracted": SQLTripStore._decrypt_field_from_storage("extracted", trip_obj.extracted or {}),
            "validation": trip_obj.validation or {},
            "decision": trip_obj.decision or {},
            "strategy": trip_obj.strategy,
            "traveler_bundle": SQLTripStore._decrypt_field_from_storage("traveler_bundle", trip_obj.traveler_bundle),
            "internal_bundle": SQLTripStore._decrypt_field_from_storage("internal_bundle", trip_obj.internal_bundle),
            "safety": SQLTripStore._decrypt_field_from_storage("safety", trip_obj.safety) if trip_obj.safety else {},
            "frontier_result": SQLTripStore._decrypt_field_from_storage("frontier_result", trip_obj.frontier_result),
            "fees": SQLTripStore._decrypt_field_from_storage("fees", trip_obj.fees),
            "raw_input": SQLTripStore._decrypt_field_from_storage("raw_input", trip_obj.raw_input or {}),
            "analytics": trip_obj.analytics,
            "booking_data_source": trip_obj.booking_data_source,
            "created_at": trip_obj.created_at.isoformat() if trip_obj.created_at else None,
            "updated_at": trip_obj.updated_at.isoformat() if trip_obj.updated_at else None,
        }

    @staticmethod
    async def save_trip(trip_data: dict, agency_id: Optional[str] = None) -> str:
        trip_id = trip_data.get("id") or f"trip_{uuid4().hex[:12]}"

        # Privacy guard: block real-user PII in dogfood mode (same as FileTripStore)
        from src.security.privacy_guard import check_trip_data
        check_trip_data(trip_data)
        model_data = {
            "id": trip_id,
            "run_id": trip_data.get("run_id"),
            "agency_id": agency_id or trip_data.get("agency_id"),
            "user_id": trip_data.get("user_id"),
            "assigned_to_id": trip_data.get("assigned_to_id"),
            "source": trip_data.get("source", "unknown"),
            "status": trip_data.get("status", "new"),
            "stage": trip_data.get("stage", "discovery"),
            "follow_up_due_date": SQLTripStore._parse_datetime(trip_data.get("follow_up_due_date")),
            "party_composition": trip_data.get("party_composition"),
            "pace_preference": trip_data.get("pace_preference"),
            "date_year_confidence": trip_data.get("date_year_confidence"),
            "lead_source": trip_data.get("lead_source"),
            "activity_provenance": trip_data.get("activity_provenance"),
            "extracted": SQLTripStore._encrypt_field_for_storage("extracted", trip_data.get("extracted") or {}),
            "validation": trip_data.get("validation") or {},
            "decision": trip_data.get("decision") or {},
            "strategy": trip_data.get("strategy"),
            "traveler_bundle": SQLTripStore._encrypt_field_for_storage("traveler_bundle", trip_data.get("traveler_bundle")),
            "internal_bundle": SQLTripStore._encrypt_field_for_storage("internal_bundle", trip_data.get("internal_bundle")),
            "safety": SQLTripStore._encrypt_field_for_storage("safety", trip_data.get("safety")),
            "frontier_result": SQLTripStore._encrypt_field_for_storage("frontier_result", trip_data.get("frontier_result")),
            "fees": SQLTripStore._encrypt_field_for_storage("fees", trip_data.get("fees")),
            "booking_data": SQLTripStore._encrypt_field_for_storage("booking_data", trip_data.get("booking_data")),
            "pending_booking_data": SQLTripStore._encrypt_field_for_storage("pending_booking_data", trip_data.get("pending_booking_data")),
            "booking_data_source": trip_data.get("booking_data_source"),
            "raw_input": SQLTripStore._encrypt_field_for_storage("raw_input", trip_data.get("raw_input") or {}),
            "analytics": trip_data.get("analytics"),
            "created_at": SQLTripStore._parse_datetime(trip_data.get("created_at")) or datetime.now(timezone.utc),
            "updated_at": SQLTripStore._parse_datetime(trip_data.get("updated_at")),
        }
        if not model_data["agency_id"]:
            raise ValueError("SQLTripStore requires agency_id")

        async with tripstore_session_maker() as session:
            existing = await session.get(Trip, trip_id)
            if existing:
                for key, value in model_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                session.add(Trip(**model_data))
            await session.commit()
        return trip_id

    @staticmethod
    async def get_trip(trip_id: str) -> Optional[dict]:
        async with tripstore_session_maker() as session:
            trip_obj = await session.get(Trip, trip_id)
            return SQLTripStore._to_dict(trip_obj) if trip_obj else None

    @staticmethod
    async def list_trips(status: Optional[str] = None, limit: int = 100, agency_id: Optional[str] = None, offset: int = 0) -> list:
        """List trips, optionally filtered by status and/or agency.
        
        status accepts single status or comma-separated statuses (e.g., 'new,incomplete').
        """
        async with tripstore_session_maker() as session:
            query = select(Trip).order_by(Trip.created_at.desc())
            if status:
                statuses = [s.strip() for s in status.split(",") if s.strip()]
                if len(statuses) == 1:
                    query = query.where(Trip.status == statuses[0])
                else:
                    query = query.where(Trip.status.in_(statuses))
            if agency_id:
                query = query.where(Trip.agency_id == agency_id)
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            return [SQLTripStore._to_dict(trip) for trip in result.scalars().all()]

    @staticmethod
    async def count_trips(status: Optional[str] = None, agency_id: Optional[str] = None) -> int:
        """Count trips matching filter (without limit)."""
        async with tripstore_session_maker() as session:
            from sqlalchemy import func
            query = select(func.count()).select_from(Trip)
            if status:
                statuses = [s.strip() for s in status.split(",") if s.strip()]
                if len(statuses) == 1:
                    query = query.where(Trip.status == statuses[0])
                else:
                    query = query.where(Trip.status.in_(statuses))
            if agency_id:
                query = query.where(Trip.agency_id == agency_id)
            result = await session.execute(query)
            return result.scalar_one()

    @staticmethod
    async def update_trip(trip_id: str, updates: dict) -> Optional[dict]:
        # Privacy guard: only check for PII if updates touch user-input fields.
        # Checking updates directly (without full trip context) would false-positive
        # on legitimate agent notes or non-PII text in raw_input. Full-trip merge
        # is the correct check (as FileTripStore does) but requires extra DB read
        # + decryption; the guard on save_trip already prevents initial PII entry.
        # Check only email/phone-like values in updates (fast, no false positives).
        _pii_sensitive_keys = {"raw_input", "extracted", "extracted_facts"}
        if set(updates.keys()) & _pii_sensitive_keys:
            from src.security.privacy_guard import check_trip_data
            check_trip_data(updates)

        _encrypted_fields = SQLTripStore._PRIVATE_BLOB_FIELDS | SQLTripStore._PII_KEY_FIELDS
        async with tripstore_session_maker() as session:
            trip_obj = await session.get(Trip, trip_id)
            if not trip_obj:
                return None
            for key, value in updates.items():
                if key in _encrypted_fields:
                    value = SQLTripStore._encrypt_field_for_storage(key, value)
                elif key == "follow_up_due_date":
                    value = SQLTripStore._parse_datetime(value)
                if hasattr(trip_obj, key):
                    setattr(trip_obj, key, value)
            trip_obj.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return SQLTripStore._to_dict(trip_obj)

    @staticmethod
    async def delete_trip(trip_id: str) -> bool:
        async with tripstore_session_maker() as session:
            trip_obj = await session.get(Trip, trip_id)
            if not trip_obj:
                return False
            await session.delete(trip_obj)
            await session.commit()
            return True

    @staticmethod
    async def get_booking_data(trip_id: str) -> Optional[dict]:
        """Get decrypted booking_data only. Returns None if trip missing or no data."""
        async with tripstore_session_maker() as session:
            trip_obj = await session.get(Trip, trip_id)
            if not trip_obj:
                return None
            return SQLTripStore._decrypt_field_from_storage("booking_data", trip_obj.booking_data)

    @staticmethod
    async def get_pending_booking_data(trip_id: str) -> Optional[dict]:
        """Get decrypted pending_booking_data only. Returns None if trip missing."""
        async with tripstore_session_maker() as session:
            trip_obj = await session.get(Trip, trip_id)
            if not trip_obj:
                return None
            return SQLTripStore._decrypt_field_from_storage("pending_booking_data", trip_obj.pending_booking_data)


def _run_async_blocking(coro):
    """Run an async SQL operation from the existing synchronous TripStore API.

    Uses one process-wide background event loop. Async SQLAlchemy/asyncpg keep
    loop-bound connection-pool state, so creating a fresh loop per sync call can
    bind locks/connections to different loops under agent-runtime scans.
    """
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    bridge = _get_sync_async_bridge()
    if running_loop is bridge.loop:
        raise RuntimeError("Cannot synchronously wait on the TripStore SQL bridge from its own event loop")
    return bridge.run(coro)


class _SyncAsyncBridge:
    def __init__(self) -> None:
        import threading

        self.loop = asyncio.new_event_loop()
        self._run_lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, name="tripstore-sql-sync-bridge", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        with self._run_lock:
            try:
                future = asyncio.run_coroutine_threadsafe(coro, self.loop)
                return future.result()
            except RuntimeError as exc:
                if "cannot schedule new futures after shutdown" in str(exc):
                    raise RuntimeError(
                        "TripStore SQL bridge event loop was shut down "
                        "(possible cause: app lifespan closed the connection pool). "
                        "Ensure PostgreSQL is reachable or set TRIPSTORE_BACKEND=file."
                    ) from exc
                raise


_SYNC_ASYNC_BRIDGE: _SyncAsyncBridge | None = None


def _get_sync_async_bridge() -> _SyncAsyncBridge:
    global _SYNC_ASYNC_BRIDGE
    if _SYNC_ASYNC_BRIDGE is None:
        _SYNC_ASYNC_BRIDGE = _SyncAsyncBridge()
    elif _SYNC_ASYNC_BRIDGE.loop.is_closed():
        _SYNC_ASYNC_BRIDGE = _SyncAsyncBridge()
    return _SYNC_ASYNC_BRIDGE


class TripStore:
    """Stable synchronous TripStore facade over file or SQL persistence."""

    @staticmethod
    def _backend():
        backend = os.getenv("TRIPSTORE_BACKEND", "file").lower().strip()
        if backend == "sql":
            return SQLTripStore
        if backend not in {"", "file", "json"}:
            logger.warning("Unknown TRIPSTORE_BACKEND=%s; falling back to file store", backend)
        return FileTripStore

    @staticmethod
    def save_trip(trip_data: dict, agency_id: Optional[str] = None) -> str:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.save_trip(trip_data, agency_id=agency_id)
        return _run_async_blocking(SQLTripStore.save_trip(trip_data, agency_id=agency_id))

    @staticmethod
    async def asave_trip(trip_data: dict, agency_id: Optional[str] = None) -> str:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.save_trip(trip_data, agency_id=agency_id)
        return await SQLTripStore.save_trip(trip_data, agency_id=agency_id)

    @staticmethod
    def get_trip(trip_id: str) -> Optional[dict]:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.get_trip(trip_id)
        return _run_async_blocking(SQLTripStore.get_trip(trip_id))

    @staticmethod
    async def aget_trip(trip_id: str) -> Optional[dict]:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.get_trip(trip_id)
        return await SQLTripStore.get_trip(trip_id)

    @staticmethod
    def list_trips(status: Optional[str] = None, limit: int = 100, agency_id: Optional[str] = None, offset: int = 0) -> list:
        backend = TripStore._backend()
        if backend is FileTripStore:
            # File store doesn't support offset natively;
            # callers that need DB-level pagination should use SQL backend.
            return FileTripStore.list_trips(status=status, limit=limit, agency_id=agency_id)
        return _run_async_blocking(SQLTripStore.list_trips(status=status, limit=limit, agency_id=agency_id, offset=offset))

    @staticmethod
    async def alist_trips(status: Optional[str] = None, limit: int = 100, agency_id: Optional[str] = None, offset: int = 0) -> list:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.list_trips(status=status, limit=limit, agency_id=agency_id)
        return await SQLTripStore.list_trips(status=status, limit=limit, agency_id=agency_id, offset=offset)

    @staticmethod
    def count_trips(status: Optional[str] = None, agency_id: Optional[str] = None) -> int:
        """Count trips matching filter (without limit)."""
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.count_trips(status=status, agency_id=agency_id)
        return _run_async_blocking(
            SQLTripStore.count_trips(status=status, agency_id=agency_id)
        )

    @staticmethod
    def update_trip(trip_id: str, updates: dict) -> Optional[dict]:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.update_trip(trip_id, updates)
        return _run_async_blocking(SQLTripStore.update_trip(trip_id, updates))

    @staticmethod
    async def aupdate_trip(trip_id: str, updates: dict) -> Optional[dict]:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.update_trip(trip_id, updates)
        return await SQLTripStore.update_trip(trip_id, updates)

    @staticmethod
    def delete_trip(trip_id: str) -> bool:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.delete_trip(trip_id)
        return _run_async_blocking(SQLTripStore.delete_trip(trip_id))

    @staticmethod
    async def adelete_trip(trip_id: str) -> bool:
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.delete_trip(trip_id)
        return await SQLTripStore.delete_trip(trip_id)

    @staticmethod
    def get_booking_data(trip_id: str) -> Optional[dict]:
        """Get decrypted booking_data only. Not included in generic trip reads."""
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.get_booking_data(trip_id)
        return _run_async_blocking(SQLTripStore.get_booking_data(trip_id))

    @staticmethod
    def get_pending_booking_data(trip_id: str) -> Optional[dict]:
        """Get decrypted pending_booking_data only. Not in generic trip reads."""
        backend = TripStore._backend()
        if backend is FileTripStore:
            return FileTripStore.get_pending_booking_data(trip_id)
        return _run_async_blocking(SQLTripStore.get_pending_booking_data(trip_id))


def _build_processed_trip(
    spine_output: dict,
    source: str,
    user_id: Optional[str],
    follow_up_due_date: Optional[str],
    party_composition: Optional[str],
    pace_preference: Optional[str],
    date_year_confidence: Optional[str],
    lead_source: Optional[str],
    activity_provenance: Optional[str],
    trip_status: str,
) -> dict:
    packet = spine_output.get("packet", {}) or {}
    validation = spine_output.get("validation", {}) or {}
    decision = spine_output.get("decision", {}) or {}
    safety = spine_output.get("safety", {}) or {}
    frontier_result = spine_output.get("frontier_result")
    fees = spine_output.get("fees")

    trip = {
        "id": f"trip_{uuid4().hex[:12]}",
        "run_id": spine_output.get("run_id"),
        "user_id": user_id,
        "source": source,
        "status": trip_status,
        "stage": (
            (spine_output.get("meta") or {}).get("stage")
            or (packet or {}).get("stage")
            or "discovery"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "follow_up_due_date": follow_up_due_date,
        "party_composition": party_composition,
        "pace_preference": pace_preference,
        "date_year_confidence": date_year_confidence,
        "lead_source": lead_source,
        "activity_provenance": activity_provenance,
        "extracted": packet,
        "validation": validation,
        "decision": decision,
        "strategy": spine_output.get("strategy"),
        "traveler_bundle": spine_output.get("traveler_bundle"),
        "internal_bundle": spine_output.get("internal_bundle"),
        "safety": safety,
        "frontier_result": frontier_result,
        "fees": fees,
        "raw_input": spine_output.get("meta", {}),
    }

    try:
        analytics = process_trip_analytics(trip)
        trip["analytics"] = analytics.model_dump()
    except Exception as e:
        logger.warning(f"Analytics calculation failed: {e}")
        trip["analytics"] = None

    return _make_json_serializable(trip)


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
    """Atomic append-only audit logging to JSONL.
    
    Design (v2):
    - Each event is written as one JSON line (append mode).
    - No read-modify-write cycle on log_event — crash-safe at the event level.
    - File rotation (MAX_EVENTS cap) is a periodic compaction that rewrites
      only the tail; failed compaction is non-destructive (original file kept
      until new file is atomically renamed).
    - Migrates legacy events.json to events.jsonl on first access.
    """
    
    AUDIT_FILE = AUDIT_DIR / "events.jsonl"
    MAX_EVENTS = 10000
    _lock = threading.RLock()
    _write_count = 0
    _WRITE_COUNT_BEFORE_TRIM = 100

    # ------------------------------------------------------------------
    # Migration
    # ------------------------------------------------------------------

    @staticmethod
    def _migrate_if_needed():
        """One-shot: migrate legacy events.json to events.jsonl."""
        legacy = AUDIT_DIR / "events.json"
        if not legacy.exists():
            return
        try:
            with open(legacy) as f:
                old_events = json.load(f)
        except (json.JSONDecodeError, OSError):
            try:
                legacy.rename(legacy.with_suffix(".corrupt.json"))
            except OSError:
                pass
            return
        if not isinstance(old_events, list):
            try:
                legacy.rename(legacy.with_suffix(".corrupt.json"))
            except OSError:
                pass
            return
        # Convert JSON array to JSONL
        AuditStore.AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = AuditStore.AUDIT_FILE.with_suffix(".migrating")
        try:
            with open(tmp, "w") as out:
                for event in old_events[-AuditStore.MAX_EVENTS:]:
                    out.write(json.dumps(event) + "\n")
            os.replace(tmp, AuditStore.AUDIT_FILE)
            destination = legacy.with_suffix(".migrated-from")
            if destination.exists():
                destination.unlink()
            legacy.rename(destination)
            logger.info("Migrated %d legacy audit events to %s", min(len(old_events), AuditStore.MAX_EVENTS), AuditStore.AUDIT_FILE)
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Core I/O
    # ------------------------------------------------------------------

    @staticmethod
    def _read_events() -> list:
        """Read all events from JSONL, skipping corrupted lines."""
        AuditStore._migrate_if_needed()
        if not AuditStore.AUDIT_FILE.exists():
            return []
        events = []
        with open(AuditStore.AUDIT_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # Skip corrupted line
        return events

    @staticmethod
    def _append_event(event: dict):
        """Append one event as a JSON line. Atomic at the event level."""
        AuditStore.AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event) + "\n"
        with file_lock(AuditStore.AUDIT_FILE):
            with open(AuditStore.AUDIT_FILE, "a") as f:
                f.write(line)

    @staticmethod
    def _trim_if_needed():
        """Periodically compact the file to MAX_EVENTS lines.
        
        Uses atomic rename (write to temp, then replace) so a crash during
        trim leaves the original file intact.
        """
        if AuditStore._write_count % AuditStore._WRITE_COUNT_BEFORE_TRIM != 0:
            return
        if not AuditStore.AUDIT_FILE.exists():
            return
        with AuditStore._lock:
            events = AuditStore._read_events()
            if len(events) <= AuditStore.MAX_EVENTS:
                return
            events = events[-AuditStore.MAX_EVENTS:]
            tmp = AuditStore.AUDIT_FILE.with_suffix(".trim")
            try:
                with open(tmp, "w") as out:
                    for e in events:
                        out.write(json.dumps(e) + "\n")
                os.replace(tmp, AuditStore.AUDIT_FILE)
            except OSError:
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # Public API (unchanged signatures)
    # ------------------------------------------------------------------

    @staticmethod
    def log_event(event_type: str, user_id: str, details: dict):
        """Log an audit event — append-only, crash-safe per event."""
        event = {
            "id": f"evt_{uuid4().hex[:12]}",
            "type": event_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
        }
        with AuditStore._lock:
            AuditStore._append_event(event)
            AuditStore._write_count += 1
        AuditStore._trim_if_needed()

    @staticmethod
    def get_events(limit: int = 100) -> list:
        """Get recent events (up to `limit`)."""
        events = AuditStore._read_events()
        return events[-limit:]

    @staticmethod
    def get_events_for_trip(trip_id: str) -> list:
        """Get events for a specific trip. Chronological order."""
        events = AuditStore._read_events()
        return [
            e for e in events
            if e.get("details", {}).get("trip_id") == trip_id
        ]

    @staticmethod
    def get_agent_events_for_trip(trip_id: str, limit: int = 100) -> list:
        """Get canonical product-agent events for a specific trip."""
        events = AuditStore._read_events()
        filtered = [
            e for e in events
            if e.get("type") == "agent_event"
            and e.get("details", {}).get("trip_id") == trip_id
        ]
        return filtered[-limit:]

    @staticmethod
    def get_agent_events(
        limit: int = 100,
        agent_name: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> list:
        """Get canonical product-agent events across trips."""
        events = AuditStore._read_events()
        filtered = [e for e in events if e.get("type") == "agent_event"]
        if agent_name:
            filtered = [
                e for e in filtered
                if e.get("details", {}).get("agent_name") == agent_name
            ]
        if correlation_id:
            filtered = [
                e for e in filtered
                if e.get("details", {}).get("correlation_id") == correlation_id
            ]
        return filtered[-limit:]


class PublicCheckerArtifactStore:
    """Persist consented public checker uploads and manifests."""

    @staticmethod
    def _trip_dir(trip_id: str) -> Path:
        return PUBLIC_CHECKER_UPLOADS_DIR / trip_id

    @staticmethod
    def _manifest_path(trip_id: str) -> Path:
        return PUBLIC_CHECKER_MANIFESTS_DIR / f"{trip_id}.json"

    @staticmethod
    def save_trip_artifacts(trip_id: str, submission: Optional[dict], trip_record: Optional[dict] = None) -> Optional[dict]:
        if not submission or not submission.get("retention_consent"):
            return None

        source_payload = submission.get("source_payload") or {}
        uploaded_file = source_payload.get("uploaded_file") or {}
        content_base64 = uploaded_file.get("content_base64")
        if not content_base64:
            return None

        file_name = _safe_filename(str(uploaded_file.get("file_name") or "upload.bin"))
        mime_type = str(uploaded_file.get("mime_type") or "application/octet-stream")
        extracted_text = str(uploaded_file.get("extracted_text") or "")
        extraction_method = str(uploaded_file.get("extraction_method") or "unknown")

        try:
            raw_bytes = base64.b64decode(content_base64)
        except Exception as exc:
            logger.warning("Failed to decode consented upload for trip %s: %s", trip_id, exc)
            return None

        trip_dir = PublicCheckerArtifactStore._trip_dir(trip_id)
        trip_dir.mkdir(parents=True, exist_ok=True)

        archive_path = trip_dir / file_name
        with open(archive_path, "wb") as handle:
            handle.write(raw_bytes)

        manifest = {
            "trip_id": trip_id,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "retention_consent": True,
            "artifact_type": "public_checker_upload",
            "uploaded_file": {
                "file_name": file_name,
                "mime_type": mime_type,
                "file_size": len(raw_bytes),
                "extraction_method": extraction_method,
                "archive_path": str(archive_path),
                "extracted_text_chars": len(extracted_text),
            },
        }

        if trip_record is not None:
            manifest["trip_snapshot"] = {
                "status": trip_record.get("status"),
                "source": trip_record.get("source"),
                "agency_id": trip_record.get("agency_id"),
            }

        manifest_path = PublicCheckerArtifactStore._manifest_path(trip_id)
        with file_lock(manifest_path):
            with open(manifest_path, "w") as handle:
                json.dump(manifest, handle, indent=2)

        return manifest

    @staticmethod
    def get_trip_artifacts(trip_id: str) -> Optional[dict]:
        manifest_path = PublicCheckerArtifactStore._manifest_path(trip_id)
        if not manifest_path.exists():
            return None
        with open(manifest_path) as handle:
            return json.load(handle)

    @staticmethod
    def delete_trip_artifacts(trip_id: str) -> bool:
        manifest_path = PublicCheckerArtifactStore._manifest_path(trip_id)
        trip_dir = PublicCheckerArtifactStore._trip_dir(trip_id)
        removed = False

        if manifest_path.exists():
            manifest_path.unlink()
            removed = True

        if trip_dir.exists():
            for child in trip_dir.iterdir():
                if child.is_file():
                    child.unlink()
            trip_dir.rmdir()
            removed = True

        return removed

    @staticmethod
    def export_trip_package(trip_id: str) -> Optional[dict]:
        trip = TripStore.get_trip(trip_id)
        if not trip:
            return None
        return {
            "trip_id": trip_id,
            "trip": trip,
            "artifact_manifest": PublicCheckerArtifactStore.get_trip_artifacts(trip_id),
        }


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
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.error(
                "Override index file %s is corrupt — re-initializing. "
                "All existing override index entries will be rebuilt on next save.",
                OVERRIDES_INDEX_FILE,
            )
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
    """
    File-based team member storage using JSON.

    DEPRECATED — Use spine_api.services.membership_service instead.
                Team members are now real User + Membership DB records.
                Kept for reference; will be removed after migration.
    """

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
    serializable_trip = _build_processed_trip(
        spine_output=spine_output,
        source=source,
        user_id=user_id,
        follow_up_due_date=follow_up_due_date,
        party_composition=party_composition,
        pace_preference=pace_preference,
        date_year_confidence=date_year_confidence,
        lead_source=lead_source,
        activity_provenance=activity_provenance,
        trip_status=trip_status,
    )
    logger.debug(f"Serializable trip keys: {list(serializable_trip.keys())}")
    
    trip_id = TripStore.save_trip(serializable_trip, agency_id=agency_id)

    submission = (spine_output.get("meta", {}) or {}).get("submission")
    artifact_manifest = PublicCheckerArtifactStore.save_trip_artifacts(
        trip_id=trip_id,
        submission=submission,
        trip_record=serializable_trip,
    )
    if artifact_manifest:
        try:
            TripStore.update_trip(trip_id, {"public_checker_artifacts": artifact_manifest})
        except Exception as exc:
            logger.warning("Failed to attach public checker artifact manifest to %s: %s", trip_id, exc)
    
    # Log creation
    AuditStore.log_event("trip_created", "system", {
        "trip_id": trip_id,
        "source": source,
        "agency_id": agency_id,
    })
    
    return trip_id


async def save_processed_trip_async(
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
    """Async variant for FastAPI/background tasks and SQL-backed persistence."""
    serializable_trip = _build_processed_trip(
        spine_output=spine_output,
        source=source,
        user_id=user_id,
        follow_up_due_date=follow_up_due_date,
        party_composition=party_composition,
        pace_preference=pace_preference,
        date_year_confidence=date_year_confidence,
        lead_source=lead_source,
        activity_provenance=activity_provenance,
        trip_status=trip_status,
    )
    logger.debug(f"Serializable trip keys: {list(serializable_trip.keys())}")

    trip_id = await TripStore.asave_trip(serializable_trip, agency_id=agency_id)

    AuditStore.log_event("trip_created", "system", {
        "trip_id": trip_id,
        "source": source,
        "agency_id": agency_id,
    })

    return trip_id
