"""X-14 contract tests for the retention-enforcer prototype.

These tests intentionally assert the runtime boundary, not a compliance claim:
the module owns only an in-process registry and must not be mistaken for the
canonical cross-store erasure workflow.
"""

from datetime import datetime, timedelta, timezone

from src.security.retention_enforcer import RetentionCategory, RetentionEnforcer


def setup_function() -> None:
    """Keep the class-level prototype registry isolated between tests."""
    RetentionEnforcer._ASSET_REGISTRY.clear()
    RetentionEnforcer._CERTIFICATE_STORE.clear()


def test_runtime_boundary_is_explicitly_shadow() -> None:
    assert RetentionEnforcer.RUNTIME_STATUS == "shadow"
    assert RetentionEnforcer.EXTERNAL_ERASURE_ENABLED is False


def test_sweep_only_marks_registry_asset_and_certificate() -> None:
    now = datetime(2026, 9, 4, tzinfo=timezone.utc)
    asset = RetentionEnforcer.register_asset(
        asset_id="asset_x14_passport",
        trip_id="trip_x14",
        customer_id="customer_x14",
        category=RetentionCategory.PASSPORT_MRZ,
        created_at_iso=(now - timedelta(days=31)).isoformat(),
    )

    certificates = RetentionEnforcer.sweep_and_enforce_erasure(now_dt=now)

    assert len(certificates) == 1
    assert asset.is_erased is True
    assert asset.erasure_certificate_id == certificates[0].certificate_id
    assert RetentionEnforcer.get_certificate(certificates[0].certificate_id) is certificates[0]
    # The prototype registry retains the asset as an in-memory tombstone. A
    # real erasure workflow must separately prove deletion in every backing
    # store before issuing a compliance certificate.
    assert RetentionEnforcer._ASSET_REGISTRY[asset.asset_id] is asset


def test_repeated_sweep_does_not_emit_duplicate_for_marked_asset() -> None:
    now = datetime(2026, 9, 4, tzinfo=timezone.utc)
    RetentionEnforcer.register_asset(
        asset_id="asset_x14_logs",
        trip_id="trip_x14",
        customer_id="customer_x14",
        category=RetentionCategory.COMMUNICATION_LOGS,
        created_at_iso=(now - timedelta(days=181)).isoformat(),
    )

    first = RetentionEnforcer.sweep_and_enforce_erasure(now_dt=now)
    second = RetentionEnforcer.sweep_and_enforce_erasure(now_dt=now)

    assert len(first) == 1
    assert second == []
