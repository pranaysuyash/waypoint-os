"""
tests/test_relationship_stages.py — Contract tests for the relationship-axis
lifecycle (Extraction-Realignment Blueprint Addendum 8 ratified design,
PER-0369 seat ruling: 6 coarse stages, invariants not adjacency table,
DORMANT never auto-churns, LOST soft at relationship level).

Covers the ratified lifecycle:
  PROSPECT -> BOOKED_ACTIVE -> POST_TRIP -> (decay) -> DORMANT
  repeat commit -> REPEAT_CLIENT; deal_lost (prospect only) -> LOST;
  win_back (LOST/DORMANT only) -> PROSPECT; retention-window derived signal.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.memory.relationship_stages import (
    DEFAULT_DORMANT_DAYS,
    DEFAULT_RETENTION_WINDOW_DAYS,
    RelationshipRecord,
    RelationshipStage,
    TripEvent,
    apply_decay,
    apply_trip_event,
    derived_signal,
    validate_relationship_record,
)

T0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(days=10)
T2 = T1 + timedelta(days=30)


def _prospect() -> RelationshipRecord:
    return RelationshipRecord(customer_id="cust_test_001", stage_entered_at=T0)


# ---------------------------------------------------------------------------
# Happy path: PROSPECT -> BOOKED_ACTIVE -> POST_TRIP -> (decay) -> DORMANT
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_full_lifecycle_prospect_to_dormant(self):
        record = _prospect()
        assert record.stage is RelationshipStage.PROSPECT

        booked, audit_commit = apply_trip_event(
            record, "trip_committed", at=T0
        )
        assert booked.stage is RelationshipStage.BOOKED_ACTIVE
        assert booked.stage_entered_at == T0
        assert booked.repeat_trip_count == 0
        validate_relationship_record(booked)

        post_trip, audit_complete = apply_trip_event(
            booked, TripEvent.TRIP_COMPLETED, at=T1
        )
        assert post_trip.stage is RelationshipStage.POST_TRIP
        assert post_trip.last_trip_completed_at == T1
        assert post_trip.stage_entered_at == T1
        validate_relationship_record(post_trip)

        dormant, audit_decay = apply_decay(
            post_trip, T1 + timedelta(days=DEFAULT_DORMANT_DAYS + 1)
        )
        assert dormant.stage is RelationshipStage.DORMANT
        assert dormant.stage_entered_at == T1 + timedelta(
            days=DEFAULT_DORMANT_DAYS + 1
        )
        # History preserved through decay
        assert dormant.last_trip_completed_at == T1
        validate_relationship_record(dormant)

    def test_inputs_are_never_mutated(self):
        record = _prospect()
        booked, _ = apply_trip_event(record, "trip_committed", at=T0)
        apply_trip_event(booked, TripEvent.TRIP_COMPLETED, at=T1)
        assert record.stage is RelationshipStage.PROSPECT
        assert record.last_trip_completed_at is None
        assert record.stage_entered_at == T0

    def test_audit_dicts_are_correct(self):
        record = _prospect()
        decayed_at = T1 + timedelta(days=DEFAULT_DORMANT_DAYS + 1)

        _, audit_commit = apply_trip_event(record, "trip_committed", at=T0)
        assert audit_commit == {
            "from": "prospect",
            "to": "booked_active",
            "at": T0.isoformat(),
            "trigger": "trip_committed",
        }

        booked, _ = apply_trip_event(record, "trip_committed", at=T0)
        _, audit_complete = apply_trip_event(
            booked, TripEvent.TRIP_COMPLETED, at=T1
        )
        assert audit_complete == {
            "from": "booked_active",
            "to": "post_trip",
            "at": T1.isoformat(),
            "trigger": "trip_completed",
        }

        post_trip, _ = apply_trip_event(
            booked, TripEvent.TRIP_COMPLETED, at=T1
        )
        _, audit_decay = apply_decay(post_trip, decayed_at)
        assert audit_decay == {
            "from": "post_trip",
            "to": "dormant",
            "at": decayed_at.isoformat(),
            "trigger": "time_decay",
        }
        # Audit values are JSON-serializable primitives
        for audit in (audit_commit, audit_complete, audit_decay):
            assert set(audit.keys()) == {"from", "to", "at", "trigger"}
            datetime.fromisoformat(audit["at"])


# ---------------------------------------------------------------------------
# Repeat flow: second commit -> REPEAT_CLIENT
# ---------------------------------------------------------------------------


class TestRepeatFlow:
    def _post_trip_record(self):
        record = _prospect()
        booked, _ = apply_trip_event(record, "trip_committed", at=T0)
        post_trip, _ = apply_trip_event(booked, TripEvent.TRIP_COMPLETED, at=T1)
        return post_trip

    def test_second_commit_reaches_repeat_client(self):
        post_trip = self._post_trip_record()
        repeat, audit = apply_trip_event(
            post_trip, "trip_committed", at=T2
        )
        assert repeat.stage is RelationshipStage.REPEAT_CLIENT
        assert repeat.repeat_trip_count == 1
        assert repeat.stage_entered_at == T2
        assert repeat.last_trip_completed_at == T1  # history preserved
        validate_relationship_record(repeat)
        assert audit == {
            "from": "post_trip",
            "to": "repeat_client",
            "at": T2.isoformat(),
            "trigger": "trip_committed",
        }

    def test_third_commit_keeps_repeat_client_and_increments_count(self):
        post_trip = self._post_trip_record()
        repeat, _ = apply_trip_event(post_trip, "trip_committed", at=T2)
        repeat_again, audit = apply_trip_event(repeat, "trip_committed", at=T2 + timedelta(days=5))
        assert repeat_again.stage is RelationshipStage.REPEAT_CLIENT
        assert repeat_again.repeat_trip_count == 2
        validate_relationship_record(repeat_again)
        assert audit["from"] == "repeat_client"
        assert audit["to"] == "repeat_client"

    def test_commit_without_prior_completed_trip_stays_booked_active(self):
        record = _prospect()
        booked, _ = apply_trip_event(record, "trip_committed", at=T0)
        rebooked, audit = apply_trip_event(booked, "trip_committed", at=T1)
        assert rebooked.stage is RelationshipStage.BOOKED_ACTIVE
        assert rebooked.repeat_trip_count == 0
        assert audit is None  # idempotent re-commit, no mutation

    def test_repeat_client_invariant_requires_count(self):
        bogus = RelationshipRecord(
            customer_id="cust_bad",
            stage=RelationshipStage.REPEAT_CLIENT,
            repeat_trip_count=0,
        )
        with pytest.raises(ValueError, match="repeat_trip_count"):
            validate_relationship_record(bogus)


# ---------------------------------------------------------------------------
# Invariant validation
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_booked_active_with_zero_active_trips_raises(self):
        record = RelationshipRecord(
            customer_id="cust_bad",
            stage=RelationshipStage.BOOKED_ACTIVE,
        )
        with pytest.raises(ValueError, match="BOOKED_ACTIVE"):
            validate_relationship_record(record, active_trips=0)

    def test_booked_active_without_trip_context_is_allowed(self):
        """No trip context provided -> BOOKED_ACTIVE invariant is not asserted."""
        record = RelationshipRecord(
            customer_id="cust_ok",
            stage=RelationshipStage.BOOKED_ACTIVE,
        )
        validate_relationship_record(record, active_trips=None)
        validate_relationship_record(record)

    def test_booked_active_with_active_trips_passes(self):
        record = RelationshipRecord(
            customer_id="cust_ok",
            stage=RelationshipStage.BOOKED_ACTIVE,
        )
        validate_relationship_record(record, active_trips=1)
        validate_relationship_record(record, active_trips=3)

    def test_other_stages_unaffected_by_active_trip_context(self):
        """Providing trip context never rejects non-BOOKED_ACTIVE stages."""
        for stage in RelationshipStage:
            if stage is RelationshipStage.BOOKED_ACTIVE:
                continue  # dedicated tests above cover its invariant
            record = RelationshipRecord(
                customer_id="cust_ok",
                stage=stage,
                repeat_trip_count=1 if stage is RelationshipStage.REPEAT_CLIENT else 0,
            )
            validate_relationship_record(record, active_trips=0)

    def test_negative_repeat_trip_count_raises(self):
        record = RelationshipRecord(
            customer_id="cust_bad", repeat_trip_count=-1
        )
        with pytest.raises(ValueError, match="repeat_trip_count"):
            validate_relationship_record(record)

    def test_transition_validates_resulting_record(self):
        """A commit landing on BOOKED_ACTIVE with explicit context is checked."""
        record = _prospect()
        with pytest.raises(ValueError, match="BOOKED_ACTIVE"):
            apply_trip_event(
                record, "trip_committed", at=T0, active_trips=0
            )


# ---------------------------------------------------------------------------
# deal_lost: only from PROSPECT
# ---------------------------------------------------------------------------


class TestDealLost:
    def test_deal_lost_from_prospect_sets_lost_with_reason(self):
        record = _prospect()
        lost, audit = apply_trip_event(
            record, "deal_lost", at=T0, loss_reason="chose_competitor"
        )
        assert lost.stage is RelationshipStage.LOST
        assert lost.loss_reason == "chose_competitor"
        assert lost.stage_entered_at == T0
        validate_relationship_record(lost)
        assert audit == {
            "from": "prospect",
            "to": "lost",
            "at": T0.isoformat(),
            "trigger": "deal_lost",
        }

    def test_deal_lost_only_legal_from_prospect(self):
        booked, _ = apply_trip_event(_prospect(), "trip_committed", at=T0)
        unchanged, audit = apply_trip_event(
            booked, "deal_lost", at=T1, loss_reason="whatever"
        )
        assert unchanged is booked
        assert unchanged.stage is RelationshipStage.BOOKED_ACTIVE
        assert audit is None

    def test_deal_lost_from_dormant_is_noop(self):
        post_trip, _ = apply_trip_event(
            apply_trip_event(_prospect(), "trip_committed", at=T0)[0],
            TripEvent.TRIP_COMPLETED,
            at=T1,
        )
        dormant, _ = apply_decay(
            post_trip, T1 + timedelta(days=DEFAULT_DORMANT_DAYS + 1)
        )
        assert dormant.stage is RelationshipStage.DORMANT
        unchanged, audit = apply_trip_event(
            dormant, "deal_lost", at=T2, loss_reason="x"
        )
        assert unchanged is dormant
        assert audit is None


# ---------------------------------------------------------------------------
# win_back: -> PROSPECT from LOST/DORMANT only
# ---------------------------------------------------------------------------


class TestWinBack:
    def test_win_back_from_lost_is_legal(self):
        lost, _ = apply_trip_event(
            _prospect(), "deal_lost", at=T0, loss_reason="price"
        )
        revived, audit = apply_trip_event(lost, "win_back", at=T1)
        assert revived.stage is RelationshipStage.PROSPECT
        assert revived.loss_reason is None
        assert revived.stage_entered_at == T1
        validate_relationship_record(revived)
        assert audit == {
            "from": "lost",
            "to": "prospect",
            "at": T1.isoformat(),
            "trigger": "win_back",
        }

    def test_win_back_from_dormant_is_legal(self):
        booked, _ = apply_trip_event(_prospect(), "trip_committed", at=T0)
        post_trip, _ = apply_trip_event(booked, TripEvent.TRIP_COMPLETED, at=T1)
        dormant, _ = apply_decay(
            post_trip, T1 + timedelta(days=DEFAULT_DORMANT_DAYS + 1)
        )
        revived, audit = apply_trip_event(dormant, "win_back", at=T2)
        assert revived.stage is RelationshipStage.PROSPECT
        assert audit["to"] == "prospect"

    def test_win_back_from_active_stages_is_noop(self):
        booked, _ = apply_trip_event(_prospect(), "trip_committed", at=T0)
        unchanged, audit = apply_trip_event(booked, "win_back", at=T1)
        assert unchanged is booked
        assert audit is None

    def test_win_back_preserves_repeat_history(self):
        """Revived repeat customer who rebooks returns to REPEAT_CLIENT."""
        lost, _ = apply_trip_event(
            _prospect(), "deal_lost", at=T0, loss_reason="price"
        )
        revived, _ = apply_trip_event(lost, "win_back", at=T1)
        # Customer completes a trip then commits again -> repeat
        booked, _ = apply_trip_event(revived, "trip_committed", at=T1)
        completed, _ = apply_trip_event(
            booked, TripEvent.TRIP_COMPLETED, at=T2
        )
        repeat, _ = apply_trip_event(completed, "trip_committed", at=T2 + timedelta(days=1))
        assert repeat.stage is RelationshipStage.REPEAT_CLIENT
        assert repeat.repeat_trip_count == 1

    def test_win_back_then_commit_clears_loss_reason(self):
        lost, _ = apply_trip_event(
            _prospect(), "deal_lost", at=T0, loss_reason="price"
        )
        revived, _ = apply_trip_event(lost, "win_back", at=T1)
        booked, _ = apply_trip_event(revived, "trip_committed", at=T2)
        assert booked.loss_reason is None
        assert booked.stage is RelationshipStage.BOOKED_ACTIVE


# ---------------------------------------------------------------------------
# Time decay
# ---------------------------------------------------------------------------


class TestDecay:
    def _post_trip_record(self):
        booked, _ = apply_trip_event(_prospect(), "trip_committed", at=T0)
        post_trip, _ = apply_trip_event(booked, TripEvent.TRIP_COMPLETED, at=T1)
        return post_trip

    def test_decay_noop_inside_window(self):
        post_trip = self._post_trip_record()
        unchanged, audit = apply_decay(post_trip, T1 + timedelta(days=89))
        assert unchanged is post_trip
        assert unchanged.stage is RelationshipStage.POST_TRIP
        assert audit is None

    def test_decay_fires_at_window_boundary(self):
        post_trip = self._post_trip_record()
        decayed, audit = apply_decay(
            post_trip, T1 + timedelta(days=DEFAULT_DORMANT_DAYS)
        )
        assert decayed.stage is RelationshipStage.DORMANT
        assert audit["trigger"] == "time_decay"

    def test_decay_window_is_configurable(self):
        post_trip = self._post_trip_record()
        decayed, _ = apply_decay(post_trip, T1 + timedelta(days=14), dormant_days=14)
        assert decayed.stage is RelationshipStage.DORMANT
        unchanged, _ = apply_decay(
            post_trip, T1 + timedelta(days=13), dormant_days=14
        )
        assert unchanged is post_trip

    def test_dormant_never_auto_churns(self):
        post_trip = self._post_trip_record()
        dormant, _ = apply_decay(post_trip, T1 + timedelta(days=91))
        assert dormant.stage is RelationshipStage.DORMANT
        # Churn is signal-based, not clock-based: decay is a no-op forever
        still_dormant, audit = apply_decay(
            dormant, T1 + timedelta(days=3650)
        )
        assert still_dormant is dormant
        assert still_dormant.stage is RelationshipStage.DORMANT
        assert audit is None

    def test_decay_ignores_non_post_trip_stages(self):
        prospect = _prospect()
        unchanged, audit = apply_decay(
            prospect, T0 + timedelta(days=3650)
        )
        assert unchanged is prospect
        assert audit is None

        booked, _ = apply_trip_event(prospect, "trip_committed", at=T0)
        unchanged, audit = apply_decay(
            booked, T0 + timedelta(days=3650)
        )
        assert unchanged is booked
        assert audit is None

    def test_decay_skips_post_trip_without_completion_anchor(self):
        # Defensive: malformed POST_TRIP without anchor must not crash
        orphan = RelationshipRecord(
            customer_id="cust_orphan",
            stage=RelationshipStage.POST_TRIP,
            stage_entered_at=T0,
            last_trip_completed_at=None,
        )
        unchanged, audit = apply_decay(orphan, T0 + timedelta(days=3650))
        assert unchanged is orphan
        assert audit is None


# ---------------------------------------------------------------------------
# Derived signals (NOT stages)
# ---------------------------------------------------------------------------


class TestDerivedSignals:
    def _post_trip_record(self):
        booked, _ = apply_trip_event(_prospect(), "trip_committed", at=T0)
        post_trip, _ = apply_trip_event(booked, TripEvent.TRIP_COMPLETED, at=T1)
        return post_trip

    def test_retention_window_active_inside_window(self):
        post_trip = self._post_trip_record()
        signals = derived_signal(post_trip, now=T1 + timedelta(days=89))
        assert signals == {"retention_window_active": True}

    def test_retention_window_inactive_after_window(self):
        post_trip = self._post_trip_record()
        signals = derived_signal(
            post_trip, now=T1 + timedelta(days=DEFAULT_RETENTION_WINDOW_DAYS + 1)
        )
        assert signals == {"retention_window_active": False}

    def test_retention_window_inactive_without_completed_trip(self):
        prospect = _prospect()
        signals = derived_signal(prospect, now=T1)
        assert signals == {"retention_window_active": False}

    def test_retention_window_configurable(self):
        post_trip = self._post_trip_record()
        assert derived_signal(
            post_trip, now=T1 + timedelta(days=10), retention_window_days=10
        ) == {"retention_window_active": True}
        assert derived_signal(
            post_trip, now=T1 + timedelta(days=11), retention_window_days=10
        ) == {"retention_window_active": False}

    def test_decay_does_not_change_signals_shape(self):
        post_trip = self._post_trip_record()
        dormant, _ = apply_decay(
            post_trip, T1 + timedelta(days=DEFAULT_DORMANT_DAYS + 1)
        )
        signals = derived_signal(dormant, now=T1 + timedelta(days=91))
        assert set(signals.keys()) == {"retention_window_active"}
        # Stage and signal are independent axes: DORMANT stage, expired window
        assert dormant.stage is RelationshipStage.DORMANT
        assert signals["retention_window_active"] is False


# ---------------------------------------------------------------------------
# Input handling / robustness
# ---------------------------------------------------------------------------


class TestInputHandling:
    def test_events_accept_enum_and_string(self):
        record = _prospect()
        via_enum, _ = apply_trip_event(record, TripEvent.TRIP_COMMITTED, at=T0)
        via_str, _ = apply_trip_event(record, "trip_committed", at=T0)
        assert via_enum.stage == via_str.stage

    def test_unknown_event_string_raises(self):
        with pytest.raises(ValueError):
            apply_trip_event(_prospect(), "explode_trip", at=T0)

    def test_naive_datetimes_treated_as_utc(self):
        record = _prospect()
        naive = datetime(2026, 1, 1, 12, 0, 0)  # no tzinfo
        booked, _ = apply_trip_event(record, "trip_committed", at=naive)
        assert booked.stage_entered_at.tzinfo is timezone.utc
        post_trip, _ = apply_trip_event(
            booked, TripEvent.TRIP_COMPLETED, at=naive + timedelta(days=1)
        )
        decayed, _ = apply_decay(
            post_trip,
            (naive + timedelta(days=1)) + timedelta(days=DEFAULT_DORMANT_DAYS + 1),
        )
        assert decayed.stage is RelationshipStage.DORMANT
