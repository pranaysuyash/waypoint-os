from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]

_ENV_LOADED = False


def load_project_env() -> None:
    """Load local development env files without overriding real shell env."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    original_env_keys = set(os.environ.keys())
    merged_values: dict[str, str] = {}

    for env_path in (
        PROJECT_ROOT / '.env',
        PROJECT_ROOT / '.env.local',
        PROJECT_ROOT / 'frontend' / '.env.local',
    ):
        if not env_path.exists():
            continue

        for key, value in dotenv_values(env_path).items():
            if value is None:
                continue
            merged_values[key] = value

    for key, value in merged_values.items():
        if key not in original_env_keys:
            os.environ[key] = value

    _ENV_LOADED = True
