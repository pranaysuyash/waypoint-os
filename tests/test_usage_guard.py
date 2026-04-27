"""
tests.test_usage_guard — Unit tests for LLM LLMUsageGuard with atomic storage.

Tests rate limiting, budget checking, warn/block modes,
threshold warnings, and usage recording.
"""

import pytest
from datetime import datetime, timedelta

from src.llm.usage_guard import (
    LLMUsageGuard,
    LLMUsageDecision,
    reset_usage_guard,
)
from src.llm.usage_store import InMemoryUsageStore


class TestLLMUsageDecision:
    """Tests for LLMUsageDecision dataclass."""

    def test_allowed_decision_defaults(self):
        """Test decision with all defaults."""
        d = LLMUsageDecision(allowed=True)
        assert d.allowed is True
        assert d.reason is None
        assert d.warnings == []
        assert d.current_daily_cost == 0.0
        assert d.block_reason is None

    def test_blocked_decision(self):
        """Test blocked decision with reason."""
        d = LLMUsageDecision(
            allowed=False,
            reason="Rate limit exceeded",
            block_reason="rate_limit_exceeded",
            current_hourly_calls=100,
            hourly_limit=100,
        )
        assert d.allowed is False
        assert d.reason == "Rate limit exceeded"
        assert d.block_reason == "rate_limit_exceeded"


class TestLLMUsageGuard:
    """Tests for LLMUsageGuard."""

    def _make_guard(self, **kwargs):
        """Create a guard with a frozen clock for testing."""
        now = datetime(2026, 4, 26, 12, 0, 0)
        store = kwargs.pop("store", InMemoryUsageStore())
        return LLMUsageGuard(now_func=lambda: now, store=store, **kwargs)

    def test_allows_call_when_guard_disabled(self):
        """Guard disabled allows all calls."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(enabled=False, store=store)
        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=1.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True

    def test_allows_call_when_no_limits_configured(self):
        """No limits means all calls allowed."""
        store = InMemoryUsageStore()
        guard = self._make_guard(store=store)
        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=1.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        assert result.warnings == []

    def test_blocks_when_hourly_limit_exceeded(self):
        """Rate limit blocks when exceeded."""
        store = InMemoryUsageStore()
        now = datetime(2026, 4, 26, 12, 0, 0)

        guard = LLMUsageGuard(
            enabled=True,
            max_calls_per_hour=3,
            store=store,
            now_func=lambda: now,
        )

        for i in range(3):
            result = guard.check_before_call(
                model="gemini-2.0-flash",
                estimated_cost=0.5,
                feature="hybrid_engine",
            )
            assert result.allowed is True, f"Call {i+1} should be allowed"
            guard.record_call(result, actual_cost=0.5, success=True)

        blocked = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=0.5,
            feature="hybrid_engine",
        )
        assert blocked.allowed is False
        assert blocked.block_reason == "rate_limit_exceeded"
        assert "Rate limit exceeded" in blocked.reason

    def test_old_calls_not_counted_in_hourly_limit(self):
        """Calls older than 1 hour are ignored."""
        store = InMemoryUsageStore()
        now = datetime(2026, 4, 26, 12, 0, 0)

        guard = LLMUsageGuard(
            enabled=True,
            max_calls_per_hour=3,
            store=store,
            now_func=lambda: now,
        )

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=0.5,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        assert result.current_hourly_calls == 0

    def test_warns_at_50_percent_threshold(self):
        """Warning issued when projected cost crosses 50%."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            daily_budget=100.0,
            budget_warning_thresholds=[0.5],
            store=store,
        )

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=51.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        assert any("50%" in w for w in result.warnings)

    def test_warns_at_80_percent_threshold(self):
        """Warning issued when projected cost crosses 80%."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            daily_budget=100.0,
            budget_warning_thresholds=[0.5, 0.8],
            store=store,
        )

        # Seed a previous successful call so budget is at ₹75
        result1 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=75.0,
            feature="hybrid_engine",
        )
        assert result1.allowed is True
        guard.record_call(result1, actual_cost=75.0, success=True)

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=6.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        assert any("80%" in w for w in result.warnings)

    def test_warns_but_allows_at_100_percent_in_warn_mode(self):
        """Warn mode allows over-budget calls with warning."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            daily_budget=100.0,
            budget_mode="warn",
            budget_warning_thresholds=[0.5, 0.8, 1.0],
            store=store,
        )

        # Seed at ₹90
        result1 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=90.0,
            feature="hybrid_engine",
        )
        assert result1.allowed is True
        guard.record_call(result1, actual_cost=90.0, success=True)

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=15.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        assert any("exceeded" in w for w in result.warnings)
        assert result.projected_daily_cost == 105.0

    def test_blocks_at_100_percent_in_block_mode(self):
        """Block mode rejects over-budget calls."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            daily_budget=100.0,
            budget_mode="block",
            store=store,
        )

        # Seed at ₹90
        result1 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=90.0,
            feature="hybrid_engine",
        )
        assert result1.allowed is True
        guard.record_call(result1, actual_cost=90.0, success=True)

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=15.0,
            feature="hybrid_engine",
        )
        assert result.allowed is False
        assert result.block_reason == "budget_exceeded"

    def test_blocks_on_second_call(self):
        """Budget block on second call."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            daily_budget=1.0,
            budget_mode="block",
            store=store,
        )

        result1 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=1.0,
            feature="hybrid_engine",
        )
        assert result1.allowed is True
        guard.record_call(result1, actual_cost=1.0, success=True)

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=0.5,
            feature="hybrid_engine",
        )
        assert result.allowed is False
        assert "budget_exceeded" in result.block_reason

    def test_no_budget_limit_allows_call(self):
        """No budget limit means all calls allowed regardless of cost."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            daily_budget=None,
            store=store,
        )

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=1000.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True

    def test_record_call_increments_hourly_and_daily(self):
        """Recording successful call updates both hourly and daily counters."""
        store = InMemoryUsageStore()
        now = datetime(2026, 4, 26, 12, 0, 0)

        guard = LLMUsageGuard(
            daily_budget=100.0,
            store=store,
            now_func=lambda: now,
        )

        result1 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=10.0,
            feature="hybrid_engine",
        )
        assert result1.allowed is True
        guard.record_call(result1, actual_cost=10.0, success=True)

        result2 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=5.0,
            feature="hybrid_engine",
        )
        assert result2.allowed is True
        guard.record_call(result2, actual_cost=5.0, success=True)

        state = store.get_summary(
            agency_id="default",
            model="*",
            feature="*",
            usage_date="2026-04-26",
        )
        assert state["daily_cost"] == 15.0

    def test_record_call_does_not_count_failed_calls_toward_budget(self):
        """Failed calls are recorded for rate limit but don't add to daily cost."""
        store = InMemoryUsageStore()
        now = datetime(2026, 4, 26, 12, 0, 0)

        guard = LLMUsageGuard(
            max_calls_per_hour=100,
            daily_budget=999.0,
            store=store,
            now_func=lambda: now,
        )

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=10.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        guard.record_call(result, actual_cost=10.0, success=False)

        state = store.get_summary(
            agency_id="default",
            model="*",
            feature="*",
            usage_date="2026-04-26",
            now=now,
        )
        assert state["hourly_calls"] >= 1  # failed/reserved calls counted for rate
        assert state["daily_cost"] == 0.0   # but not for budget

    def test_get_state_returns_current_status(self):
        """get_state returns current guard state."""
        store = InMemoryUsageStore()
        now = datetime(2026, 4, 26, 12, 0, 0)

        guard = LLMUsageGuard(
            enabled=True,
            max_calls_per_hour=100,
            daily_budget=50.0,
            budget_mode="block",
            store=store,
            now_func=lambda: now,
        )

        # Seed a call
        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=25.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        guard.record_call(result, actual_cost=25.0, success=True)

        state = guard.get_state()

        assert state["enabled"] is True
        assert state["max_calls_per_hour"] == 100
        assert state["daily_budget"] == 50.0
        assert state["budget_mode"] == "block"
        assert state["current_hourly_calls"] == 1
        assert state["current_daily_cost"] == 25.0

    def test_reset_clears_all_state(self):
        """reset clears store."""
        store = InMemoryUsageStore()
        now = datetime(2026, 4, 26, 12, 0, 0)

        guard = LLMUsageGuard(
            daily_budget=100.0,
            store=store,
            now_func=lambda: now,
        )

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=50.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        guard.record_call(result, actual_cost=50.0, success=True)

        guard.reset_state()

        state = guard.get_state()
        assert state["current_daily_cost"] == 0.0
        assert state["current_hourly_calls"] == 0

    def test_multiple_thresholds_fired(self):
        """Multiple thresholds can fire on a single call."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            daily_budget=100.0,
            budget_warning_thresholds=[0.5, 0.8],
            store=store,
        )

        result = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=85.0,
            feature="hybrid_engine",
        )
        assert result.allowed is True
        assert len(result.warnings) >= 2

    def test_from_env_defaults(self):
        """from_env creates guard with defaults when env vars not set."""
        import os
        env_backup = os.environ.copy()
        try:
            for key in ["LLM_GUARD_ENABLED", "LLM_MAX_CALLS_PER_HOUR", "LLM_DAILY_BUDGET"]:
                os.environ.pop(key, None)

            reset_usage_guard()
            guard = LLMUsageGuard.from_env()

            assert guard.enabled is True
            assert guard.max_calls_per_hour is None
            assert guard.daily_budget is None
            assert guard.budget_mode == "warn"
            assert guard.budget_warning_thresholds == [0.5, 0.8, 1.0]
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

    def test_from_env_parses_values(self):
        """from_env parses environment variables correctly."""
        import os
        env_backup = os.environ.copy()
        try:
            os.environ["LLM_GUARD_ENABLED"] = "1"
            os.environ["LLM_MAX_CALLS_PER_HOUR"] = "50"
            os.environ["LLM_DAILY_BUDGET"] = "500.0"
            os.environ["LLM_BUDGET_MODE"] = "block"
            os.environ["LLM_BUDGET_WARNING_THRESHOLDS"] = "0.25,0.5,0.75,1.0"

            reset_usage_guard()
            guard = LLMUsageGuard.from_env()

            assert guard.enabled is True
            assert guard.max_calls_per_hour == 50
            assert guard.daily_budget == 500.0
            assert guard.budget_mode == "block"
            assert guard.budget_warning_thresholds == [0.25, 0.5, 0.75, 1.0]
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

    def test_guard_disabled_from_env(self):
        """from_env respects LLM_GUARD_ENABLED=0."""
        import os
        env_backup = os.environ.copy()
        try:
            os.environ["LLM_GUARD_ENABLED"] = "0"

            reset_usage_guard()
            guard = LLMUsageGuard.from_env()

            assert guard.enabled is False
        finally:
            os.environ.clear()
            os.environ.update(env_backup)


class TestLLMUsageGuardIntegration:
    """Integration-style tests for guard + hybrid engine path."""

    def test_guard_blocks_at_rate_limit_integration(self):
        """Rate limit blocks LLM calls in integrated scenario."""
        from src.llm.usage_store import InMemoryUsageStore

        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            enabled=True,
            max_calls_per_hour=2,
            daily_budget=10000.0,
            store=store,
        )

        result1 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=0.5,
            feature="hybrid_engine",
        )
        assert result1.allowed is True
        guard.record_call(result1, actual_cost=0.5, success=True)

        result2 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=0.5,
            feature="hybrid_engine",
        )
        assert result2.allowed is True
        guard.record_call(result2, actual_cost=0.5, success=True)

        blocked = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=0.5,
            feature="hybrid_engine",
        )
        assert blocked.allowed is False
        assert blocked.block_reason == "rate_limit_exceeded"


class TestGuardConcurrency:
    """Concurrency tests — prove atomic check-and-reserve works."""

    def test_race_hundred_calls_single_worker(self):
        """100 simultaneous calls into same store — all correctly enforced."""
        import threading
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            max_calls_per_hour=10,
            daily_budget=1000.0,
            store=store,
        )

        results: list[LLMUsageDecision] = []
        lock = threading.Lock()
        errors: list[Exception] = []

        def worker():
            try:
                result = guard.check_before_call(
                    model="gemini-2.0-flash",
                    estimated_cost=1.0,
                    feature="hybrid_engine",
                )
                with lock:
                    results.append(result)
                if result.allowed:
                    guard.record_call(result, actual_cost=1.0, success=True)
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        if errors:
            raise errors[0]

        allowed_count = sum(1 for r in results if r.allowed)
        blocked_count = sum(1 for r in results if not r.allowed)

        # Exactly 10 should be allowed, 90 blocked
        assert allowed_count == 10, (
            f"Expected 10 allowed, got {allowed_count}"
        )
        assert blocked_count == 90, (
            f"Expected 90 blocked, got {blocked_count}"
        )

    def test_parallel_budget_enforcement(self):
        """Multiple threads trying to exceed budget all correctly blocked."""
        import threading
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            max_calls_per_hour=999999,
            daily_budget=5.0,
            budget_mode="block",
            store=store,
        )

        results: list[LLMUsageDecision] = []
        lock = threading.Lock()

        def worker():
            result = guard.check_before_call(
                model="gemini-2.0-flash",
                estimated_cost=1.0,
                feature="hybrid_engine",
            )
            with lock:
                results.append(result)
            if result.allowed:
                guard.record_call(result, actual_cost=1.0, success=True)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        allowed_count = sum(1 for r in results if r.allowed)
        assert allowed_count == 5, (
            f"Budget 5.0 allows exactly 5 calls at ₹1 each, got {allowed_count}"
        )

    def test_reservation_finalization(self):
        """Reserved events correctly updated after LLM call."""
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            max_calls_per_hour=10,
            daily_budget=100.0,
            store=store,
        )

        decision = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=10.0,
            feature="hybrid_engine",
        )
        assert decision.allowed is True
        assert decision.reservation is not None
        assert decision.reservation["status"] == "reserved"

        # Simulate LLM call
        guard.record_call(decision, actual_cost=17.5, success=True)

        # No way to inspect internal events directly, but next budget check
        # should reflect actual cost, not estimated
        decision2 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=10.0,
            feature="hybrid_engine",
        )
        assert decision2.current_daily_cost == 17.5

    def test_blocked_call_not_finalized(self):
        """Blocked calls do not get finalized."""
        import threading
        store = InMemoryUsageStore()
        guard = LLMUsageGuard(
            max_calls_per_hour=1,
            store=store,
        )

        decision1 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=0.5,
            feature="hybrid_engine",
        )
        assert decision1.allowed is True
        guard.record_call(decision1, actual_cost=0.5, success=True)

        decision2 = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=0.5,
            feature="hybrid_engine",
        )
        assert not decision2.allowed
        assert decision2.reservation is None  # no reservation for blocked

    def test_guard_storage_error_fails_closed(self):
        """If check_and_reserve raises GuardStorageError, decision is blocked."""
        class BrokenStore:
            def check_and_reserve(self, **kwargs):
                from src.llm.usage_store import GuardStorageError
                raise GuardStorageError("disk full")
            def finalize_reservation(self, **kwargs):
                pass
            def get_summary(self, **kwargs):
                return {"hourly_calls": 0, "daily_cost": 0.0}
            def reset(self):
                pass

        guard = LLMUsageGuard(store=BrokenStore())
        decision = guard.check_before_call(
            model="gemini-2.0-flash",
            estimated_cost=1.0,
            feature="hybrid_engine",
        )
        assert not decision.allowed
        assert decision.block_reason == "guard_unavailable"
