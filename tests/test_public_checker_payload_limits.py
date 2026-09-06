"""S-07 (audit RT-04/RT-05) regressions — public-checker input resource caps.

/api/public-checker/run is unauthenticated and runs the full pipeline
synchronously. These tests pin:

  - text fields (raw_note / owner_note / itinerary_text) each and combined are
    capped (413) independent of the HTTP body cap;
  - structured_json nesting depth and total node count are bounded (422) by an
    iterative pure helper, so hostile shapes can never reach the serializer
    (RecursionError) or drive superlinear extraction.

Rejection happens before any pipeline work, so no trip rows are written.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

import spine_api.services.public_checker_service as pcs
from spine_api.services.public_checker_service import (
    PUBLIC_CHECKER_MAX_JSON_DEPTH,
    PUBLIC_CHECKER_MAX_JSON_NODES,
    PUBLIC_CHECKER_MAX_TEXT_CHARS,
    enforce_public_checker_payload_limits,
    run_public_checker_submission,
    scan_structured_json_limits,
)


def _nested(depth: int, leaf: object = "x") -> object:
    node: object = leaf
    for _ in range(depth - 1):
        node = {"child": node}
    return node


def _broad(node_count: int) -> dict:
    return {f"k{i}": i for i in range(node_count)}


# ---------------------------------------------------------------------------
# Pure helper: scan_structured_json_limits
# ---------------------------------------------------------------------------


class TestScanStructuredJsonLimits:
    def test_depth_within_limit_passes(self):
        max_depth, nodes = scan_structured_json_limits(_nested(PUBLIC_CHECKER_MAX_JSON_DEPTH))
        assert max_depth == PUBLIC_CHECKER_MAX_JSON_DEPTH
        assert nodes == PUBLIC_CHECKER_MAX_JSON_DEPTH

    def test_depth_over_limit_raises(self):
        with pytest.raises(ValueError, match="nesting depth"):
            scan_structured_json_limits(_nested(PUBLIC_CHECKER_MAX_JSON_DEPTH + 1))

    def test_node_count_within_limit_passes(self):
        # A dict of N entries counts as N + 1 nodes (the dict itself + values).
        _, nodes = scan_structured_json_limits(_broad(PUBLIC_CHECKER_MAX_JSON_NODES - 1))
        assert nodes == PUBLIC_CHECKER_MAX_JSON_NODES

    def test_node_count_over_limit_raises(self):
        with pytest.raises(ValueError, match="node count"):
            scan_structured_json_limits(_broad(PUBLIC_CHECKER_MAX_JSON_NODES + 1))

    def test_deep_nesting_never_hits_recursion_limit(self):
        """100k-deep structure must be rejected by iteration, not RecursionError."""
        deep = "x"
        for _ in range(100_000):
            deep = {"child": deep}
        with pytest.raises(ValueError, match="nesting depth"):
            scan_structured_json_limits(deep)

    def test_scalar_passes(self):
        for scalar in (None, 5, "text", 1.5, True):
            max_depth, nodes = scan_structured_json_limits(scalar)
            assert (max_depth, nodes) == (1, 1)


# ---------------------------------------------------------------------------
# Enforcement: text caps (413) and structured_json shape (422)
# ---------------------------------------------------------------------------


class TestEnforcePayloadLimits:
    def test_oversized_raw_note_rejected_413(self):
        with pytest.raises(HTTPException) as excinfo:
            enforce_public_checker_payload_limits({"raw_note": "x" * (PUBLIC_CHECKER_MAX_TEXT_CHARS + 1)})
        assert excinfo.value.status_code == 413
        assert "raw_note" in excinfo.value.detail

    def test_oversized_itinerary_text_rejected_413(self):
        with pytest.raises(HTTPException) as excinfo:
            enforce_public_checker_payload_limits(
                {"itinerary_text": "y" * (PUBLIC_CHECKER_MAX_TEXT_CHARS + 1)}
            )
        assert excinfo.value.status_code == 413

    def test_combined_text_over_cap_rejected_413(self):
        half = PUBLIC_CHECKER_MAX_TEXT_CHARS // 2
        payload = {"raw_note": "a" * half, "itinerary_text": "b" * (half + 1)}
        with pytest.raises(HTTPException) as excinfo:
            enforce_public_checker_payload_limits(payload)
        assert excinfo.value.status_code == 413
        assert "Combined" in excinfo.value.detail

    def test_text_at_cap_passes(self):
        enforce_public_checker_payload_limits(
            {"raw_note": "a" * PUBLIC_CHECKER_MAX_TEXT_CHARS, "owner_note": None}
        )

    def test_deep_structured_json_rejected_422(self):
        with pytest.raises(HTTPException) as excinfo:
            enforce_public_checker_payload_limits(
                {"structured_json": _nested(PUBLIC_CHECKER_MAX_JSON_DEPTH + 1)}
            )
        assert excinfo.value.status_code == 422

    def test_wide_structured_json_rejected_422(self):
        with pytest.raises(HTTPException) as excinfo:
            enforce_public_checker_payload_limits(
                {"structured_json": _broad(PUBLIC_CHECKER_MAX_JSON_NODES + 1)}
            )
        assert excinfo.value.status_code == 422

    def test_valid_payload_passes(self):
        enforce_public_checker_payload_limits(
            {
                "raw_note": "Trip to Bali in December",
                "structured_json": {"source_payload": {"session_id": "s1", "kind": "freeform"}},
            }
        )


# ---------------------------------------------------------------------------
# Service seam: rejection happens before any pipeline work
# ---------------------------------------------------------------------------


class _Boom:
    """Any callable touched after the enforcement point fails the test."""

    def __call__(self, *args, **kwargs):  # pragma: no cover - guard
        raise AssertionError("pipeline callable reached despite payload rejection")


def test_service_rejects_before_pipeline(monkeypatch):
    monkeypatch.setattr(pcs, "run_spine_once", _Boom())
    monkeypatch.setattr(pcs, "build_consented_submission", _Boom())

    with pytest.raises(HTTPException) as excinfo:
        run_public_checker_submission(
            {"raw_note": "z" * (PUBLIC_CHECKER_MAX_TEXT_CHARS + 1)},
            build_envelopes=_Boom(),
            load_fixture_expectations=_Boom(),
            to_dict=_Boom(),
            save_processed_trip=_Boom(),
            get_public_checker_agency_id=_Boom(),
            logger=pcs.logging.getLogger("test"),
        )
    assert excinfo.value.status_code == 413


# ---------------------------------------------------------------------------
# Router contract (uses the shared session_client; rejections are pre-pipeline)
# ---------------------------------------------------------------------------


def test_router_rejects_oversized_raw_note_with_413(session_client):
    response = session_client.post(
        "/api/public-checker/run",
        json={"raw_note": "x" * (PUBLIC_CHECKER_MAX_TEXT_CHARS + 1), "retention_consent": True},
    )
    assert response.status_code == 413
    assert "raw_note" in response.json()["detail"]


def test_router_rejects_deep_structured_json_with_422(session_client):
    response = session_client.post(
        "/api/public-checker/run",
        json={"structured_json": _nested(50), "retention_consent": True},
    )
    assert response.status_code == 422
    assert "nesting depth" in response.json()["detail"]
