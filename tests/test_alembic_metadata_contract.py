"""Focused A-20 tests for metadata ownership and existing schema contracts."""

from pathlib import Path

from sqlalchemy.dialects import postgresql, sqlite

from spine_api.models import AuditLog, Base, TripRoutingState
from spine_api.models.tenant import Membership


def test_runtime_models_are_registered_for_alembic_metadata() -> None:
    assert "audit_logs" in Base.metadata.tables
    assert "trip_routing_states" in Base.metadata.tables
    assert Base.metadata.tables["audit_logs"] is AuditLog.__table__
    assert Base.metadata.tables["trip_routing_states"] is TripRoutingState.__table__


def test_routing_foreign_keys_match_existing_delete_actions() -> None:
    table = TripRoutingState.__table__
    assert next(iter(table.c.agency_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.primary_assignee_id.foreign_keys)).ondelete == "SET NULL"
    assert next(iter(table.c.reviewer_id.foreign_keys)).ondelete == "SET NULL"
    assert next(iter(table.c.escalation_owner_id.foreign_keys)).ondelete == "SET NULL"


def test_specializations_uses_jsonb_on_postgres_and_json_on_sqlite() -> None:
    column_type = Membership.__table__.c.specializations.type
    assert isinstance(column_type.dialect_impl(postgresql.dialect()), postgresql.JSONB)
    assert isinstance(column_type.dialect_impl(sqlite.dialect()), sqlite.JSON)


def test_raw_requeue_table_has_a_narrow_explicit_alembic_exemption() -> None:
    source = Path("alembic/env.py").read_text()
    assert 'name == "agent_requeue_jobs"' in source
    assert 'type_ == "table"' in source
    assert "and reflected" in source
    assert "broad unknown-table suppression" in source
    assert "return False" in source
