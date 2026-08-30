"""
src/agents/idempotency.py — Idempotency key reservation and execution deduplication engine.

Grounding doctrine:
- PER-0700 (Agentic Systems Architect): Prevent duplicate side-effects during agent lease transitions or network retries.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger("src.agents.idempotency")


class IdempotencyStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(slots=True)
class IdempotencyRecord:
    """Stored execution record for an idempotent operation."""
    key: str
    trip_id: str
    action_name: str
    request_hash: str
    status: IdempotencyStatus
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    response_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    ttl_seconds: int = 86400  # 24-hour default retention


class IdempotencyRegistry:
    """In-memory thread-safe registry with pluggable backend for idempotency keys."""

    _instance: Optional[IdempotencyRegistry] = None

    def __init__(self):
        self._records: Dict[str, IdempotencyRecord] = {}

    @classmethod
    def get_instance(cls) -> IdempotencyRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def generate_key(trip_id: str, action_name: str, payload: Dict[str, Any]) -> str:
        """Generate a deterministic idempotency key from trip_id, action, and payload hash."""
        serialized = json.dumps(payload, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        return f"idem:{trip_id}:{action_name}:{payload_hash}"

    def try_acquire(
        self,
        key: str,
        trip_id: str,
        action_name: str,
        payload: Dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> tuple[bool, Optional[IdempotencyRecord]]:
        """
        Attempt to acquire an idempotency key.
        Returns:
            (True, record) if acquired (new execution allowed).
            (False, record) if already exists (should return cached response or reject concurrent run).
        """
        now = time.time()
        record = self._records.get(key)

        # Check if existing record expired
        if record and (now - record.created_at) > record.ttl_seconds:
            del self._records[key]
            record = None

        if record is not None:
            if record.status == IdempotencyStatus.COMPLETED:
                logger.info("Idempotent hit: returning cached result for key=%s", key)
                return False, record
            elif record.status == IdempotencyStatus.PENDING:
                # Concurrent in-flight execution
                logger.warning("Idempotent conflict: action currently in-flight for key=%s", key)
                return False, record
            elif record.status == IdempotencyStatus.FAILED:
                logger.info("Idempotent retry: previous attempt failed for key=%s", key)
                # Allow retry on failure

        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        new_record = IdempotencyRecord(
            key=key,
            trip_id=trip_id,
            action_name=action_name,
            request_hash=payload_hash,
            status=IdempotencyStatus.PENDING,
            created_at=now,
            ttl_seconds=ttl_seconds,
        )
        self._records[key] = new_record
        return True, new_record

    def mark_completed(self, key: str, response_payload: Dict[str, Any]) -> None:
        """Mark an idempotent operation as completed and store its cached result."""
        if key in self._records:
            self._records[key].status = IdempotencyStatus.COMPLETED
            self._records[key].completed_at = time.time()
            self._records[key].response_payload = response_payload

    def mark_failed(self, key: str, error_message: str) -> None:
        """Mark an idempotent operation as failed."""
        if key in self._records:
            self._records[key].status = IdempotencyStatus.FAILED
            self._records[key].completed_at = time.time()
            self._records[key].error_message = error_message
