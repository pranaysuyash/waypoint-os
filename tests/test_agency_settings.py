import os
import sqlite3
import json
import pytest
from src.intake.config.agency_settings import AgencySettings, AgencySettingsStore
import src.intake.config.agency_settings as mod_agency_settings

def test_defaults():
    settings = AgencySettingsStore.defaults("agency-123")
    assert settings.agency_id == "agency-123"
    assert settings.target_margin_pct == 15.0
    assert settings.default_currency == "INR"
    assert settings.brand_tone == "professional"
    # Profile fields should be empty by default
    assert settings.agency_name == ""
    assert settings.contact_email == ""

def test_load_non_existent_returns_defaults(tmp_path, monkeypatch):
    mod = mod_agency_settings
    monkeypatch.setattr(mod, "_DATA_ROOT", str(tmp_path))
    # Force re-init of DB on next call by clearing any cached state
    settings = AgencySettingsStore.load("missing-agency")
    assert settings.agency_id == "missing-agency"
    assert settings.target_margin_pct == 15.0

def test_save_and_load(tmp_path, monkeypatch):
    mod = mod_agency_settings
    monkeypatch.setattr(mod, "_DATA_ROOT", str(tmp_path))
    
    # Save custom settings
    settings = AgencySettingsStore.defaults("custom-agency")
    settings.target_margin_pct = 25.0
    settings.brand_tone = "direct"
    settings.operating_hours_end = "18:00"
    
    AgencySettingsStore.save(settings)
    
    # Verify SQLite DB exists
    db_path = tmp_path / "agency_settings.db"
    assert db_path.exists()
    
    # Verify row exists in DB
    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        "SELECT config_json FROM agency_settings WHERE agency_id = ?",
        ("custom-agency",)
    ).fetchone()
    conn.close()
    assert row is not None
    stored = json.loads(row[0])
    assert stored["target_margin_pct"] == 25.0
    
    # Load back and verify changes are persisted
    loaded = AgencySettingsStore.load("custom-agency")
    assert loaded.agency_id == "custom-agency"
    assert loaded.target_margin_pct == 25.0
    assert loaded.brand_tone == "direct"
    assert loaded.operating_hours_end == "18:00"

def test_load_ignores_unknown_keys(tmp_path, monkeypatch):
    mod = mod_agency_settings
    monkeypatch.setattr(mod, "_DATA_ROOT", str(tmp_path))
    
    # Seed via direct DB insert with unknown key
    db_path = tmp_path / "agency_settings.db"
    os.makedirs(tmp_path, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agency_settings (
            agency_id TEXT PRIMARY KEY,
            config_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    config = {
        "agency_id": "dirty-agency",
        "target_margin_pct": 18.0,
        "some_unknown_field": "ignore me"
    }
    conn.execute(
        "INSERT INTO agency_settings (agency_id, config_json) VALUES (?, ?)",
        ("dirty-agency", json.dumps(config))
    )
    conn.commit()
    conn.close()
        
    loaded = AgencySettingsStore.load("dirty-agency")
    assert loaded.agency_id == "dirty-agency"
    assert loaded.target_margin_pct == 18.0
    assert not hasattr(loaded, "some_unknown_field")

def test_legacy_json_migration(tmp_path, monkeypatch):
    mod = mod_agency_settings
    monkeypatch.setattr(mod, "_DATA_ROOT", str(tmp_path))
    
    # Create legacy JSON file
    legacy_path = tmp_path / "agency_legacy-agency.json"
    legacy_data = {
        "agency_id": "legacy-agency",
        "target_margin_pct": 20.0,
        "brand_tone": "cautious",
        "autonomy": {
            "approval_gates": {
                "PROCEED_TRAVELER_SAFE": "block",
                "PROCEED_INTERNAL_DRAFT": "review"
            }
        }
    }
    with open(legacy_path, "w", encoding="utf-8") as f:
        json.dump(legacy_data, f)
    
    # Load should migrate from JSON to SQLite
    loaded = AgencySettingsStore.load("legacy-agency")
    assert loaded.agency_id == "legacy-agency"
    assert loaded.target_margin_pct == 20.0
    assert loaded.brand_tone == "cautious"
    assert loaded.autonomy.approval_gates["PROCEED_TRAVELER_SAFE"] == "block"
    
    # Legacy JSON should be deleted after migration
    assert not legacy_path.exists()
    
    # DB should now contain the migrated data
    db_path = tmp_path / "agency_settings.db"
    assert db_path.exists()
    
    # Reload from SQLite should return same values
    loaded2 = AgencySettingsStore.load("legacy-agency")
    assert loaded2.target_margin_pct == 20.0

def test_profile_fields_persist(tmp_path, monkeypatch):
    mod = mod_agency_settings
    monkeypatch.setattr(mod, "_DATA_ROOT", str(tmp_path))
    
    settings = AgencySettingsStore.defaults("profile-test")
    settings.agency_name = "Test Agency"
    settings.contact_email = "test@example.com"
    settings.contact_phone = "+91 99999 99999"
    settings.logo_url = "https://example.com/logo.png"
    settings.website = "https://example.com"
    
    AgencySettingsStore.save(settings)
    loaded = AgencySettingsStore.load("profile-test")
    
    assert loaded.agency_name == "Test Agency"
    assert loaded.contact_email == "test@example.com"
    assert loaded.contact_phone == "+91 99999 99999"
    assert loaded.logo_url == "https://example.com/logo.png"
    assert loaded.website == "https://example.com"
