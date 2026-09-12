"""Regression tests for FND-0277 — draft-reprocess duplicate leads (Sim #2).

Live evidence (Family Summit, 2026-09-12): six reprocesses of one draft
created SIX incomplete leads. Root cause: `_resolve_draft_reprocess_target`
resolved the previous trip via ContextVar-based RLS `get_trip()`, which sees
an empty set in the pipeline executor (request ContextVar not set) — so the
"never resurrect a dead id" branch fired and every run created a new lead.

Contract: the resolver must consult the store through the explicit-agency
RLS session (`get_trip_for_agency(trip_id, draft.agency_id)`), never through
the ContextVar-based lookup.
"""


from spine_api.services.pipeline_execution_service import (
    _resolve_draft_reprocess_target,
)


class _Draft:
    def __init__(self, agency_id, linked_trip_ids):
        self.id = "draft_b4117a661e95"
        self.agency_id = agency_id
        self.promoted_trip_id = None
        self.linked_trip_ids = linked_trip_ids


class _RlsFilteredStore:
    """Store whose ContextVar-based get_trip sees nothing (RLS hides rows in
    a background executor), but whose explicit-agency lookup works."""

    def __init__(self, trips):
        self.trips = trips
        self.contextvar_calls = []
        self.agency_calls = []

    def get_trip(self, trip_id):
        self.contextvar_calls.append(trip_id)
        return None  # RLS-filtered: background context sees nothing

    def get_trip_for_agency(self, trip_id, agency_id):
        self.agency_calls.append((trip_id, agency_id))
        return self.trips.get(trip_id)


class _LegacyStore:
    """Test double without get_trip_for_agency must keep working."""

    def __init__(self, trips):
        self.trips = trips

    def get_trip(self, trip_id):
        return self.trips.get(trip_id)


class _Ledger:
    def __init__(self, draft_id):
        self._meta = {"draft_id": draft_id}

    def get_meta(self, run_id):
        return dict(self._meta)


class _DraftStore:
    def __init__(self, draft):
        self._draft = draft

    def get(self, draft_id):
        return self._draft if draft_id == self._draft.id else None


AGENCY = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"


class _Logger:
    def warning(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass


def test_resolver_uses_explicit_agency_lookup_when_contextvar_rls_is_empty():
    trip = {"trip_id": "trip_1", "status": "incomplete", "agency_id": AGENCY}
    store = _RlsFilteredStore({"trip_1": trip})
    draft = _Draft(AGENCY, ["trip_1"])

    trip_id, status = _resolve_draft_reprocess_target(
        _DraftStore(draft), _Ledger("draft_b4117a661e95"), store, "run-1", logger=_Logger()
    )

    assert trip_id == "trip_1"
    assert status == "incomplete"
    assert store.agency_calls == [("trip_1", AGENCY)]
    assert store.contextvar_calls == [], (
        "ContextVar-based lookup must not be consulted when the explicit-"
        "agency lookup is available — it sees an RLS-filtered empty set in "
        "the executor and caused 6 duplicate leads in Sim #2"
    )


def test_resolver_falls_back_to_get_trip_without_agency_method():
    trip = {"trip_id": "trip_1", "status": "incomplete"}
    store = _LegacyStore({"trip_1": trip})
    draft = _Draft(None, ["trip_1"])  # no agency on draft → legacy path

    trip_id, status = _resolve_draft_reprocess_target(
        _DraftStore(draft), _Ledger("draft_b4117a661e95"), store, "run-1", logger=_Logger()
    )

    assert trip_id == "trip_1"
    assert status == "incomplete"


def test_resolver_still_refuses_dead_trip_ids():
    store = _RlsFilteredStore({})  # linked trip gone from the store
    draft = _Draft(AGENCY, ["trip_dead"])

    trip_id, status = _resolve_draft_reprocess_target(
        _DraftStore(draft), _Ledger("draft_b4117a661e95"), store, "run-1", logger=_Logger()
    )

    assert trip_id is None and status is None
