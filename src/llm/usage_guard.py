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

Per-Agency Guard Registry:
  Each agency gets its own guard instance with agency-specific limits
  and alert destinations. Guards are created lazily on first access and
  can be hot-reloaded when settings change via reload_guard_for_agency().

  - get_guard_for_agency(agency_id) — returns/creates guard for a specific agency
  - reload_guard_for_agency(agency_id) — rebuilds guard from current settings
  - get_usage_guard() — backward-compatible default guard (agency_id="default")

Usage:
    # Per-agency (preferred for API request paths)
    guard = get_guard_for_agency("waypoint-hq")
    decision = guard.check_before_call(model="gemini-2.0-flash", estimated_cost=0.15, feature="hybrid_engine")

    # Default fallback (for callers without agency context)
    guard = get_usage_guard()
    decision = guard.check_before_call(model="gemini-2.0-flash", estimated_cost=0.15, feature="hybrid_engine")

Storage guarantees (SQLite, single-container):
- WAL mode, 5-second busy timeout
- Atomic check + reserve in single transaction
- Cross-worker within same DB file (same container only)
- Not safe across different hosts/containers
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

from .usage_store import LLMUsageStore, GuardStorageError, InMemoryUsageStore, RedisUsageStore
from .alert_service import AlertDeliveryService, AlertEventType, alert_service_from_env

logger = logging.getLogger(__name__)


@dataclass(slots=True)
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

    _default_instance: Optional[LLMUsageGuard] = None

    def __init__(
        self,
        enabled: bool = True,
        agency_id: str = "default",
        max_calls_per_hour: Optional[int] = None,
        max_calls_per_model: Optional[dict[str, int]] = None,
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
            max_calls_per_hour: Hourly call limit (all models), None = no limit.
            max_calls_per_model: Per-model hourly limits, e.g. {"gemini-2.0-flash": 100}.
            daily_budget: Daily budget in INR, None = no limit.
            budget_mode: "warn" or "block".
            budget_warning_thresholds: [0.5, 0.8, 1.0].
            store: Storage backend (defaults to SQLite).
            now_func: Injectable clock for testing.
        """
        self.enabled = enabled
        self.agency_id = agency_id
        self.max_calls_per_hour = max_calls_per_hour
        self.max_calls_per_model = max_calls_per_model or {}
        self.daily_budget = daily_budget
        self.budget_mode = budget_mode
        self.budget_warning_thresholds = budget_warning_thresholds or [0.5, 0.8, 1.0]
        self.store = store or InMemoryUsageStore()
        self._now_func = now_func or (lambda: datetime.now())
        self.alerts: Optional[AlertDeliveryService] = None

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

        # Per-model limits: LLM_MAX_CALLS_PER_MODEL='gemini-2.0-flash:100,gemini-2.5-pro:20'
        max_per_model_str = os.environ.get("LLM_MAX_CALLS_PER_MODEL", "")
        max_per_model: dict[str, int] = {}
        for pair in max_per_model_str.split(","):
            pair = pair.strip()
            if ":" in pair:
                mname, mlimit = pair.split(":", 1)
                mname, mlimit = mname.strip(), mlimit.strip()
                if mname and mlimit.isdigit():
                    max_per_model[mname] = int(mlimit)

        return cls(
            enabled=enabled,
            max_calls_per_hour=int(max_calls) if max_calls is not None else None,
            max_calls_per_model=max_per_model or None,
            daily_budget=float(daily_budget) if daily_budget is not None else None,
            budget_mode=budget_mode,
            budget_warning_thresholds=[float(t.strip()) for t in thresholds_str.split(",") if t.strip()],
            store=store,
        )

    @classmethod
    def from_settings(cls, settings, alert_destinations=None) -> "LLMUsageGuard":
        """Build guard from persisted AgencySettings.

        Args:
            settings: AgencySettings instance (or any object with .llm_guard attribute).
            alert_destinations: Optional AlertDestinationsSettings to attach.
        """
        llm_guard_settings = settings.llm_guard
        enabled = llm_guard_settings.enabled
        agency_id = settings.agency_id

        # Use the same Redis/InMemory backend selection as from_env
        if os.environ.get("REDIS_URL"):
            store: LLMUsageStore = RedisUsageStore.from_env()
        else:
            store = InMemoryUsageStore()

        guard = cls(
            enabled=enabled,
            agency_id=agency_id,
            max_calls_per_hour=llm_guard_settings.max_calls_per_hour,
            max_calls_per_model=llm_guard_settings.max_calls_per_model,
            daily_budget=llm_guard_settings.daily_budget,
            budget_mode=llm_guard_settings.budget_mode,
            budget_warning_thresholds=llm_guard_settings.budget_warning_thresholds,
            store=store,
        )

        # Attach alert service from persisted destinations
        if alert_destinations is not None:
            from .alert_service import alert_service_from_settings
            guard.set_alert_service(alert_service_from_settings(alert_destinations))

        return guard

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
        model_limit = self.max_calls_per_model.get(model)
        try:
            reservation = self.store.check_and_reserve(
                request_id=request_id,
                agency_id=self.agency_id,
                model=model,
                feature=feature,
                estimated_cost=estimated_cost,
                hourly_limit=self.max_calls_per_hour,
                model_hourly_limit=model_limit,
                daily_budget=self.daily_budget,
                budget_mode=self.budget_mode,
                warning_thresholds=self.budget_warning_thresholds,
                now_func=self._now_func,
            )
        except GuardStorageError as exc:
            logger.error("llm_usage_guard.storage_failed", extra={"error": str(exc)})
            if self.alerts:
                self.alerts.send_guard_unavailable(self.agency_id, str(exc))
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
            if self.alerts:
                self._emit_block_alert(model, feature, decision)
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
        if warnings and self.alerts:
            for w in warnings:
                self.alerts.send_threshold_warning(
                    agency_id=self.agency_id,
                    model=model,
                    feature=feature,
                    warning=w,
                    current_cost=reservation.get("projected_cost", 0.0),
                    budget=self.daily_budget or 0.0,
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

    def _emit_block_alert(self, model: str, feature: str, decision: LLMUsageDecision) -> None:
        """Send an alert for a blocked call."""
        br = decision.block_reason
        if br in ("rate_limit_exceeded", "model_rate_limit_exceeded"):
            self.alerts.send_rate_limit_blocked(
                agency_id=self.agency_id,
                model=model,
                feature=feature,
                reason=decision.reason or "Rate limit exceeded",
                current_calls=decision.current_hourly_calls,
                limit=decision.hourly_limit or 0,
            )
        elif br == "budget_exceeded":
            self.alerts.send_budget_exceeded(
                agency_id=self.agency_id,
                model=model,
                feature=feature,
                reason=decision.reason or "Budget exceeded",
                projected_cost=decision.projected_daily_cost,
                budget=decision.daily_budget or 0.0,
            )

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
        if br == "model_rate_limit_exceeded":
            call_count = reservation.get("hourly_calls", 0)
            return f"Per-model rate limit exceeded: {call_count} calls for this model in last hour"
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
            "max_calls_per_model": dict(self.max_calls_per_model),
            "daily_budget": self.daily_budget,
            "budget_mode": self.budget_mode,
            "current_hourly_calls": summary["hourly_calls"],
            "current_daily_cost": summary["daily_cost"],
        }

    def set_alert_service(self, alerts: Optional[AlertDeliveryService]) -> None:
        """Attach an alert delivery service for threshold/block notifications."""
        self.alerts = alerts

    def reset_state(self) -> None:
        """Reset store (useful for tests)."""
        self.store.reset()


# ── Per-Agency Guard Registry ──────────────────────────────────────────────────────

_registry_lock = threading.Lock()
_guard_registry: dict[str, LLMUsageGuard] = {}
_REGISTRY_MAX_SIZE = 128  # prevent unbounded growth in multi-agency deployments


def get_guard_for_agency(agency_id: str) -> LLMUsageGuard:
    """Return the usage guard for a specific agency.

    Lazily creates a guard from persisted settings on first access.
    Subsequent calls return the cached instance.  Thread-safe.
    Registry is capped at _REGISTRY_MAX_SIZE entries; oldest (first-inserted)
    entries are evicted FIFO when the cap is reached.

    Args:
        agency_id: The agency whose guard limits to enforce.
    """
    guard = _guard_registry.get(agency_id)
    if guard is not None:
        return guard

    with _registry_lock:
        guard = _guard_registry.get(agency_id)
        if guard is not None:
            return guard

        # Evict oldest entry if registry is full (dict preserves insertion order in 3.7+)
        if len(_guard_registry) >= _REGISTRY_MAX_SIZE:
            evict_key = next(iter(_guard_registry))
            logger.info("Guard registry full, evicting oldest entry: agency=%s", evict_key)
            del _guard_registry[evict_key]

        try:
            from src.intake.config.agency_settings import AgencySettingsStore
            settings = AgencySettingsStore.load(agency_id)
            guard = LLMUsageGuard.from_settings(settings, settings.alert_destinations)
        except Exception as exc:
            logger.warning(
                "get_guard_for_agency: failed to load settings for agency=%s, "
                "falling back to env defaults: %s",
                agency_id, exc,
            )
            guard = LLMUsageGuard.from_env()
            guard.agency_id = agency_id

        _guard_registry[agency_id] = guard
        logger.info("Guard created for agency=%s (enabled=%s)", agency_id, guard.enabled)
        return guard


def reload_guard_for_agency(agency_id: str) -> LLMUsageGuard:
    """Rebuild the guard for an agency from current persisted settings.

    Called by the settings router when alert destinations or LLM guard
    config is saved, so changes take effect immediately without restart.

    Preserves the existing store (and its in-memory counters) when rebuilding,
    so a settings save does not reset usage counters.
    """
    with _registry_lock:
        existing_guard = _guard_registry.get(agency_id)
        existing_store = existing_guard.store if existing_guard else None

    try:
        from src.intake.config.agency_settings import AgencySettingsStore
        settings = AgencySettingsStore.load(agency_id)
        guard = LLMUsageGuard.from_settings(settings, settings.alert_destinations)
        # Carry forward the existing store so usage counters survive a reload.
        if existing_store is not None:
            guard.store = existing_store
    except Exception as exc:
        logger.warning(
            "reload_guard_for_agency: failed to rebuild guard for agency=%s, "
            "falling back to env defaults: %s",
            agency_id, exc,
        )
        guard = LLMUsageGuard.from_env()
        guard.agency_id = agency_id
        if existing_store is not None:
            guard.store = existing_store

    with _registry_lock:
        _guard_registry[agency_id] = guard
    logger.info("Guard reloaded for agency=%s (enabled=%s)", agency_id, guard.enabled)
    return guard


def reset_guard_registry() -> None:
    """Reset the guard registry (useful for tests)."""
    with _registry_lock:
        _guard_registry.clear()
    LLMUsageGuard._default_instance = None


# ── Backward-compatible singleton accessor ─────────────────────────────────────────

def get_usage_guard() -> LLMUsageGuard:
    """Return the default usage guard (backward-compatible).

    This guard uses agency_id="default" and is built from environment
    variables.  Callers with agency context should use get_guard_for_agency()
    instead.
    """
    if LLMUsageGuard._default_instance is None:
        LLMUsageGuard._default_instance = LLMUsageGuard.from_env()
    return LLMUsageGuard._default_instance


def reset_usage_guard() -> None:
    """Reset singleton (useful for tests)."""
    LLMUsageGuard._default_instance = None
    reset_guard_registry()
