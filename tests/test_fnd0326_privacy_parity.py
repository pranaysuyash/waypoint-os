"""FND-0326 — privacy-boundary parity: drafts + run-ledger doors run the guard.

The P0 defect: the privacy guard (check_trip_data) ran at the TripStore door
only, while two sibling persistence doors accepted the SAME customer PII in
plaintext in every posture:

1. DraftStore writes (create/save/patch/update_run_state) — drafts carry
   customer_message, agent_notes, customer_name_snapshot, and run_snapshots
   (packet snapshots).
2. Run-ledger mirrors (run_ledger_sql.mirror_meta/mirror_step) — checkpoint
   payloads are pipeline packet state.

Contract pinned here (dogfood posture, matching TripStore):
- DraftStore.save with populated freeform fields (agent_notes) in real-user
  shape → REFUSED (PrivacyGuardError), nothing persisted.
- Run-ledger mirror_step with a refused checkpoint → mirror SKIPPED (loudly),
  nothing persisted; the lifecycle record (mirror_meta) still persists with
  extra_meta redacted — state-machine honesty survives, PII does not.
- Beta posture over SQL → guard audits without blocking (parity with
  TripStore).

Residual (registered separately if pursued): at-rest ENCRYPTION parity for
draft files / ledger rows is posture work — the guard is the scan boundary.
"""

from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")


@pytest.fixture()
def drafts_dir(tmp_path, monkeypatch):
    import spine_api.draft_store as ds

    drafts = tmp_path / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ds, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ds, "DRAFTS_DIR", drafts)
    return drafts


class TestDraftDoor:
    def test_save_refuses_real_user_pii_in_dogfood(self, tmp_path, monkeypatch, drafts_dir):
        from spine_api.draft_store import Draft, DraftStore

        monkeypatch.setenv("DATA_PRIVACY_MODE", "dogfood")
        monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")

        now = "2026-10-23T00:00:00Z"
        draft = Draft(
            id="draft_fnd0326",
            created_at=now,
            updated_at=now,
            agency_id="agency_a",
            created_by="usr_a",
            name="PII probe",
            customer_message="Need help rebooking",
            agent_notes=(
                "Customer Priya Sharma, +91 98765 43210, diabetic — "
                "prefers veg meals"
            ),
        )
        with pytest.raises(Exception, match="plaintext"):
            DraftStore.save(draft)
        # Nothing persisted.
        assert DraftStore.get("draft_fnd0326") is None

    def test_clean_synthetic_draft_still_saves_in_dogfood(self, tmp_path, monkeypatch, drafts_dir):
        """The guard blocks real-user-shaped PII, not drafts in general —
        synthetic content keeps the dogfood workflow usable."""
        from spine_api.draft_store import Draft, DraftStore

        monkeypatch.setenv("DATA_PRIVACY_MODE", "dogfood")
        now = "2026-10-23T00:00:00Z"
        draft = Draft(
            id="draft_clean",
            created_at=now,
            updated_at=now,
            agency_id="agency_a",
            created_by="usr_a",
            name="Clean probe",
            customer_message="Planning question about sightseeing options",
        )
        saved = DraftStore.save(draft)
        assert saved.id == "draft_clean"


class TestRunLedgerDoor:
    def test_mirror_step_skips_refused_payload(self, monkeypatch):
        """Dogfood: a checkpoint payload the guard refuses must NOT be
        mirrored — the skip is loud (logged) and nothing persists."""
        from spine_api.run_ledger_sql import SQLRunCheckpointStore

        monkeypatch.setenv("DATA_PRIVACY_MODE", "dogfood")
        monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
        checkpoint = {
            "checkpointed_at": "2026-10-23T00:00:00Z",
            "data": {
                "raw_note": "Priya Sharma +91 98765 43210 diabetic",
                "status": "ok",
            },
        }
        SQLRunCheckpointStore.mirror_step(
            "run_fnd0326_step", "extraction", checkpoint
        )
        loaded = SQLRunCheckpointStore.load_step("run_fnd0326_step", "extraction")
        assert loaded is None

    def test_mirror_meta_persists_lifecycle_redacts_extra(self, monkeypatch):
        """The STRICT lifecycle record still persists (state machine honesty)
        but extra_meta — the wildcard carrier — is redacted on refusal."""
        from spine_api.run_ledger_sql import SQLRunCheckpointStore

        monkeypatch.setenv("DATA_PRIVACY_MODE", "dogfood")
        meta = {
            "run_id": "run_fnd0326_meta",
            "state": "completed",
            "customer_note": "Priya Sharma +91 98765 43210 diabetic",
        }
        SQLRunCheckpointStore.mirror_meta(meta)
        loaded = SQLRunCheckpointStore.load_meta("run_fnd0326_meta")
        assert loaded is not None
        assert loaded.get("state") == "completed"
        # load_meta may unfold extra_meta to the top level — accept either
        # shape, but the redaction marker must be present and the refused
        # payload text must not survive anywhere in the row.
        extra = loaded.get("extra_meta") or {}
        redaction = extra.get("privacy_redacted") or loaded.get("privacy_redacted")
        assert redaction is True
        assert "Priya" not in json.dumps(loaded, default=str)
