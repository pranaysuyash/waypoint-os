"""
src/logistics/timed_entry.py — Timed Entry & Excursion Slot Booking Manager (Area #17.13).

Implements:
1. Strict Timed Entry Window Tracking (Louvre, Colosseum, Universal Express, Sagrada Familia).
2. Buffer & Pacing Verification against preceding activities and traffic transit legs.
3. Automated Pre-Entry Reminder & Grace Period Management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional


class SlotStatus(str, Enum):
    ON_SCHEDULE = "ON_SCHEDULE"
    TIGHT_BUFFER_WARNING = "TIGHT_BUFFER_WARNING"
    MISSED_SLOT_RISK = "MISSED_SLOT_RISK"
    EXPIRED = "EXPIRED"


@dataclass(slots=True)
class TimedEntrySlot:
    slot_id: str
    venue_name: str
    entry_window_start: str  # ISO format "2026-10-15T10:00:00"
    entry_window_end: str    # ISO format "2026-10-15T10:30:00"
    grace_period_minutes: int = 15
    recommended_arrival_buffer_minutes: int = 20
    is_strict_cutoff: bool = True  # True = gate closes strictly at window_end


@dataclass(slots=True)
class TimedSlotAuditResult:
    slot_id: str
    venue_name: str
    scheduled_arrival_time: str
    status: SlotStatus
    buffer_minutes: float
    is_compliant: bool
    warnings: List[str] = field(default_factory=list)
    recommended_departure_time: Optional[str] = None


class TimedEntryScheduler:
    """
    Validates that planned tour sequencing respects strict timed admission slots.
    """

    @classmethod
    def audit_slot_transit(
        cls,
        slot: TimedEntrySlot,
        prior_activity_end_time_str: str,
        transit_duration_minutes: float,
    ) -> TimedSlotAuditResult:
        prior_end = datetime.fromisoformat(prior_activity_end_time_str)
        window_start = datetime.fromisoformat(slot.entry_window_start)
        window_end = datetime.fromisoformat(slot.entry_window_end)

        # Expected arrival = prior activity end + transit duration
        expected_arrival = prior_end + timedelta(minutes=transit_duration_minutes)

        # Buffer = minutes between expected arrival and window_start
        buffer_seconds = (window_start - expected_arrival).total_seconds()
        buffer_minutes = round(buffer_seconds / 60.0, 1)

        # Ideal departure to reach with recommended arrival buffer
        ideal_departure = window_start - timedelta(minutes=transit_duration_minutes + slot.recommended_arrival_buffer_minutes)

        warnings: List[str] = []
        is_compliant = True

        if expected_arrival > window_end:
            status = SlotStatus.MISSED_SLOT_RISK
            is_compliant = False
            warnings.append(
                f"🚨 Critical: Arrival at {expected_arrival.strftime('%H:%M')} is past strict gate cutoff {window_end.strftime('%H:%M')}."
            )
        elif expected_arrival > window_start:
            status = SlotStatus.TIGHT_BUFFER_WARNING
            warnings.append(
                f"⚠️ Warning: Arrival at {expected_arrival.strftime('%H:%M')} is inside the 30-min window (no security line buffer)."
            )
        elif buffer_minutes < slot.recommended_arrival_buffer_minutes:
            status = SlotStatus.TIGHT_BUFFER_WARNING
            warnings.append(
                f"⚠️ Pacing Note: Only {buffer_minutes:.0f}m buffer before entry at {venue_label(slot.venue_name)}. Recommend departing at {ideal_departure.strftime('%H:%M')}."
            )
        else:
            status = SlotStatus.ON_SCHEDULE

        return TimedSlotAuditResult(
            slot_id=slot.slot_id,
            venue_name=slot.venue_name,
            scheduled_arrival_time=expected_arrival.isoformat(),
            status=status,
            buffer_minutes=buffer_minutes,
            is_compliant=is_compliant,
            warnings=warnings,
            recommended_departure_time=ideal_departure.isoformat(),
        )


def venue_label(name: str) -> str:
    return name.strip().title()
