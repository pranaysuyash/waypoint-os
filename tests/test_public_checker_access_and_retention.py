"""WOBS P2/P3 — access tokens, dispute escrow, retention sweep.

Tokens: hashed-at-rest capability tokens bound to one trip, TTL-bounded by
retention, revocable; fail-closed on any mismatch. Disputes: recorded with
verified=false (client claims are quarantined, never corpus truth). Retention
sweep: file-store public-checker trips + artifacts expire together.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from spine_api.services.public_checker_access import (
    issue_access_token,
    list_disputes,
    prune_old_event_segments,
    record_dispute,
    revoke_tokens_for_trip,
    sweep_expired_public_checker_trips,
    verify_access_token,
)


@pytest.fixture(autouse=True)
def isolated_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    token_file = tmp_path / "public_checker" / "access_tokens.json"
    disputes_file = tmp_path / "public_checker" / "disputes.jsonl"
    monkeypatch.setenv("PUBLIC_CHECKER_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("PUBLIC_CHECKER_DISPUTES_FILE", str(disputes_file))
    monkeypatch.delenv("PUBLIC_CHECKER_RETENTION_DAYS", raising=False)
    return token_file


class TestAccessTokens:
    def test_issue_verify_roundtrip(self):
        token = issue_access_token("trip_abc")
        assert verify_access_token(token, "trip_abc") is True

    def test_wrong_trip_fails(self):
        token = issue_access_token("trip_abc")
        assert verify_access_token(token, "trip_other") is False

    def test_garbage_token_fails(self):
        assert verify_access_token("garbage", "trip_abc") is False

    def test_token_stored_hashed(self):
        token = issue_access_token("trip_abc")
        import os
        store_file = Path(os.environ["PUBLIC_CHECKER_TOKEN_FILE"])
        store_text = store_file.read_text(encoding="utf-8")
        assert token not in store_text, "raw token must never persist"

    def test_revoke(self):
        token = issue_access_token("trip_abc")
        assert revoke_tokens_for_trip("trip_abc") == 1
        assert verify_access_token(token, "trip_abc") is False

    def test_retention_expiry(self, monkeypatch: pytest.MonkeyPatch):
        token = issue_access_token("trip_abc")
        # Rewrite the created_at to be older than the 90-day default window.
        store_file = Path(__import__("os").environ["PUBLIC_CHECKER_TOKEN_FILE"])
        store = json.loads(store_file.read_text(encoding="utf-8"))
        for entry in store.values():
            entry["created_at"] = "2020-01-01T00:00:00+00:00"
        store_file.write_text(json.dumps(store), encoding="utf-8")
        assert verify_access_token(token, "trip_abc") is False

    def test_retention_zero_disables_expiry(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PUBLIC_CHECKER_RETENTION_DAYS", "0")
        token = issue_access_token("trip_abc")
        store_file = Path(__import__("os").environ["PUBLIC_CHECKER_TOKEN_FILE"])
        store = json.loads(store_file.read_text(encoding="utf-8"))
        for entry in store.values():
            entry["created_at"] = "2020-01-01T00:00:00+00:00"
        store_file.write_text(json.dumps(store), encoding="utf-8")
        assert verify_access_token(token, "trip_abc") is True


class TestDisputeEscrow:
    def test_recorded_as_unverified_client_claim(self):
        record = record_dispute(trip_id="trip_x", finding_text="monsoon risk", verdict="disagree")
        assert record["verified"] is False
        assert record["origin"] == "client"
        disputes = list_disputes()
        assert len(disputes) == 1
        assert disputes[0]["trip_id"] == "trip_x"


class TestRetentionSweep:
    def test_sweep_deletes_only_expired_public_checker_trips(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        import os

        trips_dir = tmp_path / "trips"
        trips_dir.mkdir()
        checker_dir = tmp_path / "public_checker"
        checker_dir.mkdir()

        old_trip = {"id": "trip_old", "source": "public_checker"}
        new_trip = {"id": "trip_new", "source": "public_checker"}
        agency_trip = {"id": "trip_agency", "source": "intake"}
        for name, payload in (
            ("trip_old.json", old_trip),
            ("trip_new.json", new_trip),
            ("trip_agency.json", agency_trip),
        ):
            (trips_dir / name).write_text(json.dumps(payload), encoding="utf-8")
        aged = (trips_dir / "trip_old.json").stat()
        os.utime(trips_dir / "trip_old.json", (aged.st_atime - 91 * 86400, aged.st_mtime - 91 * 86400))

        token = issue_access_token("trip_old")
        monkeypatch.setenv("PUBLIC_CHECKER_TOKEN_FILE", str(tmp_path / "tokens.json"))
        issue_access_token("trip_old")

        result = sweep_expired_public_checker_trips(
            trips_dir=trips_dir, public_checker_dir=checker_dir, max_age_days=90
        )
        assert result["deleted_trips"] == 1
        assert not (trips_dir / "trip_old.json").exists()
        assert (trips_dir / "trip_new.json").exists()
        assert (trips_dir / "trip_agency.json").exists()
        assert verify_access_token(token, "trip_old") is False

    def test_zero_days_disables(self, tmp_path: Path):
        trips_dir = tmp_path / "trips"
        trips_dir.mkdir()
        (trips_dir / "trip_old.json").write_text(
            json.dumps({"id": "trip_old", "source": "public_checker"}), encoding="utf-8"
        )
        result = sweep_expired_public_checker_trips(
            trips_dir=trips_dir, public_checker_dir=tmp_path / "pc", max_age_days=0
        )
        assert result["deleted_trips"] == 0
        assert (trips_dir / "trip_old.json").exists()


class TestEventSegmentPruning:
    def test_prunes_old_rotated_segments(self, tmp_path: Path):
        import os

        events_dir = tmp_path / "events"
        events_dir.mkdir()
        old_seg = events_dir / "events_raw.jsonl.1"
        current = events_dir / "events_raw.jsonl"
        old_seg.write_text("{}", encoding="utf-8")
        current.write_text("{}", encoding="utf-8")
        stat = old_seg.stat()
        os.utime(old_seg, (stat.st_atime - 200 * 86400, stat.st_mtime - 200 * 86400))

        pruned = prune_old_event_segments(events_dir=events_dir, max_age_days=180)
        assert pruned == 1
        assert not old_seg.exists()
        assert current.exists()
