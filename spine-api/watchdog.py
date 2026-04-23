"""
Integrity Watchdog — Background drift detection for Waypoint OS.

Runs periodically to ensure the DashboardAggregator SSOT remains consistent.
Emits system alerts if drift is detected.
"""

import sys
from pathlib import Path

# Ensure project root is in path - MUST be first before any other imports
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Now we can import from src and root-level modules
import time
import logging
import threading
from datetime import datetime, timezone

# Import after path is set
from src.services.dashboard_aggregator import DashboardAggregator

# This imports 'persistence' at root level - works now with path set
from src.analytics.review import _emit_notification

logger = logging.getLogger("watchdog")

class IntegrityWatchdog:
    """Monitors system integrity and alerts on drift."""
    
    def __init__(self, interval_seconds: int = 600):
        self.interval = interval_seconds
        self._stop_event = threading.Event()
        self._thread = None
        self.last_check = None
        self.consecutive_failures = 0

    def start(self):
        """Start the watchdog in a background thread."""
        if self._thread is not None:
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="IntegrityWatchdog")
        self._thread.start()
        logger.info(f"Integrity Watchdog started (interval: {self.interval}s)")

    def stop(self):
        """Stop the watchdog."""
        if self._thread is None:
            return
        
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None
        logger.info("Integrity Watchdog stopped")

    def _run_loop(self):
        """Main execution loop."""
        while not self._stop_event.is_set():
            try:
                self.check_integrity()
            except Exception as e:
                logger.error(f"Watchdog check failed: {e}")
            
            # Wait for interval or stop event
            self._stop_event.wait(self.interval)

    def check_integrity(self):
        """Perform a single integrity check."""
        self.last_check = datetime.now(timezone.utc).isoformat()
        logger.debug(f"Watchdog performing integrity check at {self.last_check}")
        
        state = DashboardAggregator.get_unified_state()
        meta = state.get("integrity_meta", {})
        
        is_consistent = meta.get("consistent", True)
        
        if not is_consistent:
            self.consecutive_failures += 1
            logger.warning(f"INTEGRITY DRIFT DETECTED: {meta}")
            
            # Emit notification to alert operators
            _emit_notification(
                trip_id="system",
                recipient="operator_dashboard",
                type="INTEGRITY_DRIFT",
                message=f"System drift detected. Sum of stages ({meta.get('sum_stages')}) != Canonical Total ({meta.get('canonical_total')}). Possible orphans: {len(state.get('orphans', []))}"
            )
        else:
            if self.consecutive_failures > 0:
                logger.info("System integrity restored.")
                _emit_notification(
                    trip_id="system",
                    recipient="operator_dashboard",
                    type="INTEGRITY_RESTORED",
                    message="System integrity has been restored and is now consistent."
                )
            self.consecutive_failures = 0

# Global instance
watchdog = IntegrityWatchdog(interval_seconds=600)  # 10 minutes
