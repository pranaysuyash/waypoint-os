"""Lossless component migration, including refusal of a lossy reversal."""

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.fixture
def migration_db():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(sa.text(
            "CREATE TABLE booking_confirmations (id TEXT PRIMARY KEY, agency_id TEXT NOT NULL, "
            "trip_id TEXT NOT NULL, confirmation_type TEXT NOT NULL, confirmation_status TEXT NOT NULL)"
        ))
        connection.execute(sa.text(
            "CREATE UNIQUE INDEX uq_bc_trip_type_active ON booking_confirmations "
            "(trip_id, confirmation_type) WHERE confirmation_status != 'voided'"
        ))
        connection.execute(sa.text(
            "INSERT INTO booking_confirmations VALUES ('old', 'agency', 'trip', 'hotel', 'recorded')"
        ))
        source = Path(__file__).parents[1] / "alembic/versions/bc_component_identity.py"
        spec = importlib.util.spec_from_file_location("component_migration", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with Operations.context(MigrationContext.configure(connection)):
            yield connection, module
    engine.dispose()


def test_upgrade_preserves_legacy_and_allows_separate_components(migration_db):
    connection, migration = migration_db
    migration.upgrade()
    assert connection.execute(sa.text("SELECT component_key FROM booking_confirmations WHERE id='old'")).scalar_one() == "primary"
    connection.execute(sa.text(
        "INSERT INTO booking_confirmations VALUES ('new', 'agency', 'trip', 'hotel', 'recorded', 'stay_2')"
    ))
    assert connection.execute(sa.text("SELECT COUNT(*) FROM booking_confirmations")).scalar_one() == 2
    indexes = {index["name"] for index in sa.inspect(connection).get_indexes("booking_confirmations")}
    assert "uq_bc_component_active" in indexes
    assert "uq_bc_trip_type_active" not in indexes


def test_legacy_only_downgrade_is_reversible(migration_db):
    connection, migration = migration_db
    migration.upgrade()
    migration.downgrade()
    assert "component_key" not in {column["name"] for column in sa.inspect(connection).get_columns("booking_confirmations")}
    assert connection.execute(sa.text("SELECT id FROM booking_confirmations")).scalar_one() == "old"


@pytest.mark.parametrize("status", ["recorded", "voided"])
def test_downgrade_refuses_to_discard_component_history(migration_db, status):
    connection, migration = migration_db
    migration.upgrade()
    connection.execute(sa.text(
        "INSERT INTO booking_confirmations VALUES ('new', 'agency', 'trip', 'hotel', :status, 'stay_2')"
    ), {"status": status})
    with pytest.raises(RuntimeError, match="preserve booking component identities"):
        migration.downgrade()
    assert connection.execute(sa.text("SELECT COUNT(*) FROM booking_confirmations")).scalar_one() == 2
    assert "component_key" in {column["name"] for column in sa.inspect(connection).get_columns("booking_confirmations")}
