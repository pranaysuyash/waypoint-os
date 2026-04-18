import os
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

def test_load_non_existent_returns_defaults(tmp_path, monkeypatch):
    # Point the _DATA_ROOT to a temporary path
    mod = mod_agency_settings
    monkeypatch.setattr(mod, "_DATA_ROOT", str(tmp_path))
    
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
    
    # Verify file exists
    expected_path = tmp_path / "agency_custom-agency.json"
    assert expected_path.exists()
    
    # Load back and verify changes are persisted
    loaded = AgencySettingsStore.load("custom-agency")
    assert loaded.agency_id == "custom-agency"
    assert loaded.target_margin_pct == 25.0
    assert loaded.brand_tone == "direct"
    assert loaded.operating_hours_end == "18:00"

def test_load_ignores_unknown_keys(tmp_path, monkeypatch):
    mod = mod_agency_settings
    monkeypatch.setattr(mod, "_DATA_ROOT", str(tmp_path))
    
    path = tmp_path / "agency_dirty-agency.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "agency_id": "dirty-agency",
            "target_margin_pct": 18.0,
            "some_unknown_field": "ignore me"
        }, f)
        
    loaded = AgencySettingsStore.load("dirty-agency")
    assert loaded.agency_id == "dirty-agency"
    assert loaded.target_margin_pct == 18.0
    assert not hasattr(loaded, "some_unknown_field")
