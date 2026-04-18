import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List

# Define the data root dynamically
_DATA_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "settings"
)

@dataclass
class AgencySettings:
    """Configuration set for an agency."""
    agency_id: str
    target_margin_pct: float = 15.0
    default_currency: str = "INR"
    operating_hours_start: str = "09:00"
    operating_hours_end: str = "21:00"
    operating_days: List[str] = field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri", "sat"])
    preferred_channels: List[str] = field(default_factory=lambda: ["whatsapp", "email"])
    brand_tone: str = "professional"  # cautious | measured | confident | direct | professional

    @classmethod
    def from_dict(cls, data: dict) -> "AgencySettings":
        """Load from dictionary, ignoring unknown keys."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

class AgencySettingsStore:
    """File-backed persistence store for AgencySettings."""
    
    @staticmethod
    def _path(agency_id: str) -> str:
        return os.path.join(_DATA_ROOT, f"agency_{agency_id}.json")

    @classmethod
    def defaults(cls, agency_id: str = "default") -> AgencySettings:
        return AgencySettings(agency_id=agency_id)

    @classmethod
    def load(cls, agency_id: str) -> AgencySettings:
        """Load settings for the agency. If not found, return defaults."""
        path = cls._path(agency_id)
        if not os.path.exists(path):
            return cls.defaults(agency_id)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Ensure the loaded object retains the requested ID 
            data["agency_id"] = agency_id
            return AgencySettings.from_dict(data)
        except Exception:
            return cls.defaults(agency_id)

    @classmethod
    def save(cls, settings: AgencySettings) -> None:
        """Persist settings to the file system."""
        os.makedirs(_DATA_ROOT, exist_ok=True)
        path = cls._path(settings.agency_id)
        data = asdict(settings)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
