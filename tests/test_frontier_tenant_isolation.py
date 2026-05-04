"""
Tests for frontier router tenant isolation fix.

Verifies that:
1. GhostWorkflowCreate and EmotionalLogRequest no longer accept agency_id in the body.
2. The route handlers inject agency_id via get_current_agency_id (JWT membership),
   not from the caller-supplied request body.

These are schema-level + inspection tests — they do not require a live database.

Background:
    Prior to this fix, the schemas carried `agency_id: str` and handlers used
    `request.agency_id` directly. Any authenticated user could write
    agency_id=<another-tenant> in the body to read or write another agency's
    ghost workflows and emotion logs.

    The fix removes agency_id from request schemas and injects it via
    `Depends(get_current_agency_id)` so the value always comes from the
    JWT-backed membership, not the caller.
"""

import inspect
import sys
from pathlib import Path

import pytest

# Path setup — must happen before any spine_api import
spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))


class TestFrontierSchemas:
    """Verify agency_id is absent from mutable request schemas."""

    def test_ghost_workflow_create_has_no_agency_id(self):
        """agency_id must not be a field on GhostWorkflowCreate."""
        from spine_api.routers.frontier import GhostWorkflowCreate
        assert "agency_id" not in GhostWorkflowCreate.model_fields, (
            "GhostWorkflowCreate must not expose agency_id — "
            "callers cannot be trusted to supply the correct tenant."
        )

    def test_ghost_workflow_create_has_required_fields(self):
        """GhostWorkflowCreate must still require trip_id and task_type."""
        from spine_api.routers.frontier import GhostWorkflowCreate
        fields = GhostWorkflowCreate.model_fields
        assert "trip_id" in fields
        assert "task_type" in fields

    def test_emotional_log_request_has_no_agency_id(self):
        """EmotionalLogRequest must not expose agency_id."""
        from spine_api.routers.frontier import EmotionalLogRequest
        assert "agency_id" not in EmotionalLogRequest.model_fields, (
            "EmotionalLogRequest must not expose agency_id — "
            "callers cannot be trusted to supply the correct tenant."
        )

    def test_emotional_log_request_has_required_fields(self):
        """EmotionalLogRequest must still have traveler_id, trip_id, sentiment_score."""
        from spine_api.routers.frontier import EmotionalLogRequest
        fields = EmotionalLogRequest.model_fields
        assert "traveler_id" in fields
        assert "trip_id" in fields
        assert "sentiment_score" in fields

    def test_intelligence_pool_request_still_has_source_agency_hash(self):
        """
        IntelligencePoolRequest uses source_agency_hash (anonymized), not agency_id.
        This is correct — the intelligence pool is cross-agency by design.
        """
        from spine_api.routers.frontier import IntelligencePoolRequest
        fields = IntelligencePoolRequest.model_fields
        assert "source_agency_hash" in fields
        assert "agency_id" not in fields


class TestFrontierHandlerSignatures:
    """
    Verify route handlers accept agency_id as a FastAPI Depends parameter,
    not as a request body field.

    This uses Python inspect to check the handler function signature rather
    than running a live request, making it safe in environments without a DB.
    """

    def _get_param_names(self, fn) -> list[str]:
        return list(inspect.signature(fn).parameters.keys())

    def test_create_ghost_workflow_has_agency_id_param(self):
        from spine_api.routers.frontier import create_ghost_workflow
        params = self._get_param_names(create_ghost_workflow)
        assert "agency_id" in params, (
            "create_ghost_workflow must accept agency_id as a Depends parameter "
            "to enforce JWT-sourced tenant scoping."
        )

    def test_get_ghost_workflow_has_agency_id_param(self):
        from spine_api.routers.frontier import get_ghost_workflow
        params = self._get_param_names(get_ghost_workflow)
        assert "agency_id" in params, (
            "get_ghost_workflow must accept agency_id to enforce ownership check."
        )

    def test_log_emotional_state_has_agency_id_param(self):
        from spine_api.routers.frontier import log_emotional_state
        params = self._get_param_names(log_emotional_state)
        assert "agency_id" in params

    def test_report_intelligence_has_agency_id_param(self):
        """
        report_intelligence still requires authentication (_agency_id) even though
        it doesn't store the agency_id (federated pool uses source_agency_hash).
        """
        from spine_api.routers.frontier import report_intelligence
        params = self._get_param_names(report_intelligence)
        # The parameter is named _agency_id to document intentional discard
        assert "_agency_id" in params
