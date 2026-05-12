import json

from src.evals.audit.public_authority import resolve_public_authority


def test_resolve_public_authority_uses_manifest_fallback_without_snapshot(monkeypatch):
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", "/tmp/does-not-exist-d6-snapshot.json")
    authority = resolve_public_authority("budget")
    assert authority.authority == "authoritative"
    assert authority.category_status == "gating"
    assert authority.source == "manifest_fallback"


def test_resolve_public_authority_prefers_snapshot_when_available(tmp_path, monkeypatch):
    snapshot_path = tmp_path / "d6_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "categories": {
                    "weather": {
                        "status": "shadow",
                        "authoritative_for_public_surface": True,
                        "reasons": ["manually_promoted_for_experiment"],
                    }
                }
            }
        )
    )
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", str(snapshot_path))

    authority = resolve_public_authority("weather")
    assert authority.authority == "authoritative"
    assert authority.category_status == "shadow"
    assert authority.source == "eval_snapshot"
    assert authority.reasons == ["manually_promoted_for_experiment"]
