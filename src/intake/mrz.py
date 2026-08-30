"""
src/intake/mrz.py — ICAO Doc 9303 Machine Readable Zone (MRZ) Checksum & Validation Engine.

Grounding doctrine:
- Document Intelligence Specialist & Epistemic Truth: Verify physical document mathematical integrity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# ICAO Doc 9303 7-3-1 weighting table
ICAO_WEIGHTS = [7, 3, 1]


def compute_mrz_check_digit(data_str: str) -> int:
    """
    Calculate the ICAO 9303 check digit for a string using 7-3-1 weighting modulo 10.
    Characters A-Z map to 10-35, '<' maps to 0, digits 0-9 map to 0-9.
    """
    total = 0
    for idx, char in enumerate(data_str):
        weight = ICAO_WEIGHTS[idx % 3]
        if char.isdigit():
            val = int(char)
        elif char.isalpha():
            val = ord(char.upper()) - 55  # 'A' -> 10, 'B' -> 11, etc.
        elif char == "<":
            val = 0
        else:
            val = 0
        total += val * weight
    return total % 10


def verify_mrz_field(data_str: str, expected_check_digit: str | int) -> bool:
    """Verify that the check digit of data_str matches expected_check_digit."""
    expected = int(expected_check_digit) if str(expected_check_digit).isdigit() else -1
    if expected < 0:
        return False
    return compute_mrz_check_digit(data_str) == expected


@dataclass(slots=True)
class MRZValidationResult:
    """Validation report for a 2-line (TD3) or 3-line (TD1) MRZ passport zone."""
    is_valid: bool
    passport_number: Optional[str]
    passport_number_valid: bool
    date_of_birth: Optional[str]  # YYYY-MM-DD
    date_of_birth_valid: bool
    expiry_date: Optional[str]    # YYYY-MM-DD
    expiry_date_valid: bool
    nationality: Optional[str]
    issuing_country: Optional[str]
    composite_valid: bool
    error_messages: list[str]


def parse_and_validate_td3_mrz(line1: str, line2: str) -> MRZValidationResult:
    """
    Parse and validate a standard 2-line x 44-character passport MRZ (TD3 format per ICAO 9303).
    """
    errors: list[str] = []
    l1 = line1.strip().replace(" ", "").upper()
    l2 = line2.strip().replace(" ", "").upper()

    if len(l1) != 44 or len(l2) != 44:
        return MRZValidationResult(
            is_valid=False,
            passport_number=None,
            passport_number_valid=False,
            date_of_birth=None,
            date_of_birth_valid=False,
            expiry_date=None,
            expiry_date_valid=False,
            nationality=None,
            issuing_country=None,
            composite_valid=False,
            error_messages=[f"Invalid MRZ line length: line1={len(l1)}, line2={len(l2)} (expected 44)"],
        )

    issuing_country = l1[2:5].replace("<", "")

    # Line 2 fields
    passport_num_raw = l2[0:9]
    passport_check = l2[9]
    nationality = l2[10:13].replace("<", "")
    dob_raw = l2[13:19]  # YYMMDD
    dob_check = l2[19]
    expiry_raw = l2[21:27]  # YYMMDD
    expiry_check = l2[27]

    passport_num_clean = passport_num_raw.replace("<", "")

    # Validate Passport Number Check Digit
    p_valid = verify_mrz_field(passport_num_raw, passport_check)
    if not p_valid:
        errors.append(f"Passport number check digit failed: expected {passport_check}")

    # Validate Date of Birth
    dob_valid = verify_mrz_field(dob_raw, dob_check)
    dob_iso = None
    if dob_valid:
        try:
            yy, mm, dd = int(dob_raw[0:2]), int(dob_raw[2:4]), int(dob_raw[4:6])
            curr_yy = datetime.now(timezone.utc).year % 100
            full_year = (1900 + yy) if yy > curr_yy else (2000 + yy)
            dob_iso = f"{full_year:04d}-{mm:02d}-{dd:02d}"
        except Exception:
            dob_valid = False
            errors.append("Invalid date format in MRZ DOB")
    else:
        errors.append(f"DOB check digit failed: expected {dob_check}")

    # Validate Expiry Date
    exp_valid = verify_mrz_field(expiry_raw, expiry_check)
    exp_iso = None
    if exp_valid:
        try:
            yy, mm, dd = int(expiry_raw[0:2]), int(expiry_raw[2:4]), int(expiry_raw[4:6])
            curr_yy = datetime.now(timezone.utc).year % 100
            # Passports are valid for <= 10 years
            full_year = (2000 + yy) if yy <= curr_yy + 15 else (1900 + yy)
            exp_iso = f"{full_year:04d}-{mm:02d}-{dd:02d}"
        except Exception:
            exp_valid = False
            errors.append("Invalid date format in MRZ expiry")
    else:
        errors.append(f"Expiry check digit failed: expected {expiry_check}")

    overall_valid = p_valid and dob_valid and exp_valid and len(errors) == 0

    return MRZValidationResult(
        is_valid=overall_valid,
        passport_number=passport_num_clean,
        passport_number_valid=p_valid,
        date_of_birth=dob_iso,
        date_of_birth_valid=dob_valid,
        expiry_date=exp_iso,
        expiry_date_valid=exp_valid,
        nationality=nationality,
        issuing_country=issuing_country,
        composite_valid=overall_valid,
        error_messages=errors,
    )
