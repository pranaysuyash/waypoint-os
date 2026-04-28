"""
llm.usage_guard — LLM usage guard for rate limiting and budget control.

Provides a guard layer that checks whether an LLM call should proceed
based on configured limits for rate, budget, and thresholds.

Key design decisions:
- Storage is abstracted behind LLMUsageStore (src/llm/usage_store.py).
- Initial store is SQLite, but Redis/Postgres can be added later.
- check_before_call() uses atomic check-and-reserve via store.check_and_reserve().
- record_call() finalizes the reservation with actual cost.
- If storage fails, the guard fails closed: no LLM call.
- In-memory cache keeps guard responsive within process.

Usage:
    guard = LLMUsageGuard()

    decision = guard.check_before_call(
        model="gemini-2.0-flash",
        estimated_cost=0.15,
        feature="hybrid_engine",
    )

    if not decision.allowed:
        return fallback_result

    try:
        result = call_llm(...)
        guard.record_call(decision, success=True, actual_cost=0.17)
    except Exception:
        guard.record_call(decision, success=False)
        raise

Storage guarantees (SQLite, single-container):
- WAL mode, 5-second busy timeout
- Atomic check + reserve in single transaction
- Cross-worker within same DB file (same container only)
- Not safe across different hosts/containers
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

from .usage_store import LLMUsageStore, GuardStorageError, InMemoryUsageStore, RedisUsageStore

logger = logging.getLogger(__name__)


@dataclass
class LLMUsageDecision:
    """
    Structured result from usage guard check.
    """
    allowed: bool
    reason: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    request_id: str = ""                         # unique reservation id / request id
    reservation: Optional[dict] = None            # store reservation dict
    current_daily_cost: float = 0.0
    projected_daily_cost: float = 0.0
    daily_budget: Optional[float] = None
    current_hourly_calls: int = 0
    hourly_limit: Optional[int] = None
    block_reason: Optional[str] = None


class LLMUsageGuard:
    """
    Guard layer for LLM usage control with durable, atomic storage.

    Storage backend defaults to SQLite.
    Fail-closed on storage failure: does not call the LLM if usage store fails.
    """

    _instance: Optional[LLMUsageGuard] = None

    def __init__(
        self,
        enabled: bool = True,
        agency_id: str = "default",
        max_calls_per_hour: Optional[int] = None,
        daily_budget: Optional[float] = None,
        budget_mode: str = "warn",
        budget_warning_thresholds: Optional[list[float]] = None,
        store: Optional[LLMUsageStore] = None,
        now_func: Optional[Callable[[], datetime]] = None,
    ):
        """
        Initialize the usage guard.

        Args:
            enabled: Whether the guard is active.
            agency_id: Which agency's limits to enforce.
            max_calls_per_hour: Hourly call limit, None = no limit.
            daily_budget: Daily budget in INR, None = no limit.
            budget_mode: "warn" or "block".
            budget_warning_thresholds: [0.5, 0.8, 1.0].
            store: Storage backend (defaults to SQLite).
            now_func: Injectable clock for testing.
        """
        self.enabled = enabled
        self.agency_id = agency_id
        self.max_calls_per_hour = max_calls_per_hour
        self.daily_budget = daily_budget
        self.budget_mode = budget_mode
        self.budget_warning_thresholds = budget_warning_thresholds or [0.5, 0.8, 1.0]
        self.store = store or InMemoryUsageStore()
        self._now_func = now_func or (lambda: datetime.now())

    # ── factory ──────────────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "LLMUsageGuard":
        """Build guard from environment.

        Storage backend selection:
          - REDIS_URL set → RedisUsageStore (multi-instance, atomic via Lua)
          - otherwise    → InMemoryUsageStore (single-process dev/test)
        """
        enabled = os.environ.get("LLM_GUARD_ENABLED", "1") == "1"
        max_calls = os.environ.get("LLM_MAX_CALLS_PER_HOUR")
        daily_budget = os.environ.get("LLM_DAILY_BUDGET")
        budget_mode = os.environ.get("LLM_BUDGET_MODE", "warn")
        thresholds_str = os.environ.get("LLM_BUDGET_WARNING_THRESHOLDS", "0.5,0.8,1.0")

        if os.environ.get("REDIS_URL"):
            store: LLMUsageStore = RedisUsageStore.from_env()
            logger.info("LLMUsageGuard: using RedisUsageStore (REDIS_URL set)")
        else:
            store = InMemoryUsageStore()
            logger.debug("LLMUsageGuard: using InMemoryUsageStore (no REDIS_URL)")

        return cls(
            enabled=enabled,
            max_calls_per_hour=int(max_calls) if max_calls is not None else None,
            daily_budget=float(daily_budget) if daily_budget is not None else None,
            budget_mode=budget_mode,
            budget_warning_thresholds=[float(t.strip()) for t in thresholds_str.split(",") if t.strip()],
            store=store,
        )

    # ── public API ───────────────────────────────────────────────────────────────────

    def check_before_call(
        self,
        model: str,
        estimated_cost: float,
        feature: str,
    ) -> LLMUsageDecision:
        """
        Check whether an LLM call is allowed.

        If allowed, a 'reserved' event is atomically persisted.
        Call finalize_reservation after the LLM call.
        """
        if not self.enabled:
            return LLMUsageDecision(allowed=True)

        request_id = f"req_{uuid.uuid4().hex[:16]}"
        try:
            reservation = self.store.check_and_reserve(
                request_id=request_id,
                agency_id=self.agency_id,
                model=model,
                feature=feature,
                estimated_cost=estimated_cost,
                hourly_limit=self.max_calls_per_hour,
                daily_budget=self.daily_budget,
                budget_mode=self.budget_mode,
                warning_thresholds=self.budget_warning_thresholds,
                now_func=self._now_func,
            )
        except GuardStorageError as exc:
            logger.error("llm_usage_guard.storage_failed", extra={"error": str(exc)})
            return LLMUsageDecision(
                allowed=False,
                reason=f"Guard storage failure: {exc}",
                block_reason="guard_unavailable",
            )

        if reservation.get("block_reason"):
            decision = LLMUsageDecision(
                allowed=False,
                reason=self._blocked_reason(reservation),
                warnings=reservation.get("warnings", []),
                request_id=request_id,
                current_daily_cost=reservation.get("daily_cost", 0.0),
                projected_daily_cost=reservation.get("projected_cost", 0.0),
                daily_budget=self.daily_budget,
                current_hourly_calls=reservation.get("hourly_calls", 0),
                hourly_limit=self.max_calls_per_hour,
                block_reason=reservation.get("block_reason"),
            )
            logger.warning(
                "llm_usage_guard.blocked",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "feature": feature,
                    "block_reason": decision.block_reason,
                    "reason": decision.reason,
                    "current_hourly_calls": decision.current_hourly_calls,
                    "daily_budget": self.daily_budget,
                    "projected_cost": decision.projected_daily_cost,
                },
            )
            return decision

        warnings = reservation.get("warnings", [])
        for w in warnings:
            logger.warning(
                "llm_usage_guard.threshold_warning",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "feature": feature,
                    "warning": w,
                },
            )

        return LLMUsageDecision(
            allowed=True,
            warnings=warnings,
            request_id=request_id,
            reservation=reservation,
            current_daily_cost=reservation.get("daily_cost", 0.0),
            projected_daily_cost=reservation.get("projected_cost", 0.0),
            daily_budget=self.daily_budget,
            current_hourly_calls=reservation.get("hourly_calls", 0),
            hourly_limit=self.max_calls_per_hour,
        )

    def record_call(
        self,
        decision: LLMUsageDecision,
        actual_cost: float,
        success: bool,
    ) -> None:
        """
        Finalize a previously reserved call.

        Must be called after the LLM call completes (success or failure).
        """
        if not self.enabled or not decision.allowed:
            return
        if not decision.reservation:
            return

        event_id = decision.reservation.get("event_id")
        status = ("completed" if success else "failed")
        try:
            self.store.finalize_reservation(
                event_id=event_id,
                actual_cost=actual_cost,
                status=status,
            )
        except GuardStorageError as exc:
            logger.error(
                "llm_usage_guard.finalize_failed",
                extra={"request_id": decision.request_id, "error": str(exc)},
            )

    # ── helpers ──────────────────────────────────────────────────────────────────────

    def _blocked_reason(self, reservation: dict) -> str:
        br = reservation.get("block_reason")
        if br == "rate_limit_exceeded":
            call_count = reservation.get("hourly_calls", 0)
            limit = self.max_calls_per_hour
            return (
                f"Rate limit exceeded: {call_count}/{limit} calls in last hour"
                if limit is not None
                else "Rate limit exceeded"
            )
        if br == "budget_exceeded":
            pct = reservation.get("projected_cost", 0.0)
            return f"Daily budget exceeded: projected ₹{pct:.2f} > ₹{self.daily_budget:.2f}"
        return "Guard blocked call"

    def get_state(self) -> dict:
        now = self._now_func()
        usage_date = now.strftime("%Y-%m-%d")
        summary = self.store.get_summary(
            agency_id=self.agency_id,
            model="*",
            feature="*",
            usage_date=usage_date,
            now=now,
        )
        return {
            "enabled": self.enabled,
            "agency_id": self.agency_id,
            "max_calls_per_hour": self.max_calls_per_hour,
            "daily_budget": self.daily_budget,
            "budget_mode": self.budget_mode,
            "current_hourly_calls": summary["hourly_calls"],
            "current_daily_cost": summary["daily_cost"],
        }

    def reset_state(self) -> None:
        """Reset store (useful for tests)."""
        self.store.reset()


# ── factory helpers ────────────────────────────────────────────────────────────────


def get_usage_guard() -> LLMUsageGuard:
    """Singleton accessor."""
    if LLMUsageGuard._instance is None:
        LLMUsageGuard._instance = LLMUsageGuard.from_env()
    return LLMUsageGuard._instance


def reset_usage_guard() -> None:
    """Reset singleton (useful for tests)."""
    LLMUsageGuard._instance = None
