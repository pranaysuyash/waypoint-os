"""
src/agents/sandbox.py — Tool execution timeout sandboxing and tenant concurrency throttling.

Grounding doctrine:
- PER-0700 (Agentic Systems Architect): Bounded execution budgets prevent runaway tools and multi-tenant resource starvation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("src.agents.sandbox")


class ToolTimeoutError(Exception):
    """Raised when a tool exceeds its allocated execution budget."""
    pass


class TenantConcurrencyLimitExceeded(Exception):
    """Raised when an agency exceeds its concurrent agent run quota."""
    pass


@dataclass(slots=True)
class ToolExecutionResult:
    """Outcome of a sandboxed tool call."""
    success: bool
    tool_name: str
    duration_ms: float
    output: Any
    error_message: Optional[str] = None


class ToolSandbox:
    """Sandboxes tool executions with strict timeout enforcement."""

    DEFAULT_TIMEOUT_BUDGETS: Dict[str, float] = {
        "supplier_search": 15.0,
        "flight_pricing": 10.0,
        "hotel_availability": 10.0,
        "db_read": 3.0,
        "db_write": 5.0,
        "llm_inference": 30.0,
        "default": 10.0,
    }

    @classmethod
    async def execute_tool(
        cls,
        tool_name: str,
        func: Callable[..., Any],
        *args: Any,
        custom_timeout_seconds: Optional[float] = None,
        **kwargs: Any,
    ) -> ToolExecutionResult:
        """
        Execute an async or sync function within a strict timeout budget.
        """
        timeout = custom_timeout_seconds or cls.DEFAULT_TIMEOUT_BUDGETS.get(tool_name, cls.DEFAULT_TIMEOUT_BUDGETS["default"])
        start = time.perf_counter()

        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                loop = asyncio.get_running_loop()
                result = await asyncio.wait_for(loop.run_in_executor(None, lambda: func(*args, **kwargs)), timeout=timeout)

            duration_ms = (time.perf_counter() - start) * 1000.0
            return ToolExecutionResult(
                success=True,
                tool_name=tool_name,
                duration_ms=round(duration_ms, 2),
                output=result,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - start) * 1000.0
            err = f"Tool '{tool_name}' timed out after {timeout:.1f}s execution budget"
            logger.error(err)
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                duration_ms=round(duration_ms, 2),
                output=None,
                error_message=err,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000.0
            err = f"Tool '{tool_name}' failed with error: {str(exc)}"
            logger.exception(err)
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                duration_ms=round(duration_ms, 2),
                output=None,
                error_message=err,
            )


class TenantConcurrencyLimiter:
    """Manages active concurrent run counts per agency tenant."""

    _instance: Optional[TenantConcurrencyLimiter] = None

    def __init__(self, default_max_concurrent: int = 10):
        self.default_max_concurrent = default_max_concurrent
        self._active_runs: Dict[str, int] = {}  # agency_id -> active count

    @classmethod
    def get_instance(cls) -> TenantConcurrencyLimiter:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def try_acquire_slot(self, agency_id: str, max_concurrent: Optional[int] = None) -> bool:
        """Attempt to acquire a concurrency slot for an agency."""
        limit = max_concurrent or self.default_max_concurrent
        current = self._active_runs.get(agency_id, 0)
        if current >= limit:
            logger.warning("Agency %s exceeded concurrent run limit (%d/%d)", agency_id, current, limit)
            return False
        self._active_runs[agency_id] = current + 1
        return True

    def release_slot(self, agency_id: str) -> None:
        """Release an active concurrency slot for an agency."""
        if agency_id in self._active_runs:
            self._active_runs[agency_id] = max(0, self._active_runs[agency_id] - 1)
            if self._active_runs[agency_id] == 0:
                del self._active_runs[agency_id]

    def get_active_count(self, agency_id: str) -> int:
        return self._active_runs.get(agency_id, 0)
