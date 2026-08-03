#!/usr/bin/env python3
"""
Download geography datasets required by src/intake/geography.py.

This script is safe to run in both local development and CI:
- It skips files that already exist.
- It downloads from the documented upstream sources:
    * GeoNames cities5000.txt (CC-BY 4.0)
    * countries-states-cities-database countries+cities.json (ODbL-1.0)
- It validates checksums by checking that the downloaded files are non-empty
  and parseable where applicable.

Usage:
    python scripts/download_geography_data.py
    python scripts/download_geography_data.py --force  # re-download even if present
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

GEONAMES_URL = "https://download.geonames.org/export/dump/cities5000.zip"
GEONAMES_ZIP = DATA_DIR / "cities5000.zip"
GEONAMES_TXT = DATA_DIR / "cities5000.txt"

CITIES_JSON_URL = (
    "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/"
    "master/json/countries+cities.json"
)
CITIES_JSON = DATA_DIR / "cities.json"


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def download_geonames(force: bool = False) -> None:
    """Download and extract GeoNames cities5000.txt."""
    if GEONAMES_TXT.exists() and not force:
        _log(f"[skip] {GEONAMES_TXT.name} already exists")
        return

    _log(f"[download] {GEONAMES_URL} -> {GEONAMES_ZIP.name}")
    urllib.request.urlretrieve(GEONAMES_URL, GEONAMES_ZIP)

    _log(f"[extract] {GEONAMES_ZIP.name} -> {GEONAMES_TXT.name}")
    with zipfile.ZipFile(GEONAMES_ZIP, "r") as zf:
        zf.extract(GEONAMES_TXT.name, DATA_DIR)

    GEONAMES_ZIP.unlink()

    if not GEONAMES_TXT.exists() or GEONAMES_TXT.stat().st_size == 0:
        raise RuntimeError(f"{GEONAMES_TXT.name} download/extract failed")

    _log(f"[ok] {GEONAMES_TXT.name} ({GEONAMES_TXT.stat().st_size:,} bytes)")


def download_cities_json(force: bool = False) -> None:
    """Download countries-states-cities-database JSON."""
    if CITIES_JSON.exists() and not force:
        _log(f"[skip] {CITIES_JSON.name} already exists")
        return

    _log(f"[download] {CITIES_JSON_URL} -> {CITIES_JSON.name}")
    urllib.request.urlretrieve(CITIES_JSON_URL, CITIES_JSON)

    if not CITIES_JSON.exists() or CITIES_JSON.stat().st_size == 0:
        raise RuntimeError(f"{CITIES_JSON.name} download failed")

    # Validate JSON parses
    with CITIES_JSON.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
        if not isinstance(data, list) or len(data) == 0:
            raise RuntimeError(f"{CITIES_JSON.name} is not a non-empty JSON array")

    _log(f"[ok] {CITIES_JSON.name} ({CITIES_JSON.stat().st_size:,} bytes, {len(data)} countries)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download geography datasets")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        download_geonames(force=args.force)
        download_cities_json(force=args.force)
    except Exception as exc:
        _log(f"[error] {exc}")
        return 1

    _log("[done] Geography datasets are ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
