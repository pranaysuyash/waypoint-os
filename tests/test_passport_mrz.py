"""
tests/test_passport_mrz.py — Unit tests for ICAO Doc 9303 MRZ checksum calculations.
"""

from src.intake.mrz import (
    compute_mrz_check_digit,
    parse_and_validate_td3_mrz,
)


def test_compute_mrz_check_digit():
    """Verify ICAO 9303 7-3-1 modulo 10 checksum algorithm."""
    # Standard test vector: "L898902C3" -> 6
    check = compute_mrz_check_digit("L898902C3")
    assert check == 6

    # Date of birth vector: "740812" -> 2
    check_dob = compute_mrz_check_digit("740812")
    assert check_dob == 2

    # Expiry date vector: "120415" -> 9
    check_exp = compute_mrz_check_digit("120415")
    assert check_exp == 9


def test_parse_and_validate_td3_mrz_valid():
    """Verify parsing a valid 2-line TD3 passport MRZ."""
    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"

    res = parse_and_validate_td3_mrz(line1, line2)
    assert res.is_valid is True
    assert res.passport_number == "L898902C3"
    assert res.passport_number_valid is True
    assert res.date_of_birth == "1974-08-12"
    assert res.date_of_birth_valid is True
    assert res.expiry_date == "2012-04-15"
    assert res.expiry_date_valid is True
    assert res.nationality == "UTO"
    assert res.issuing_country == "UTO"


def test_parse_and_validate_td3_mrz_invalid_checksum():
    """Verify rejection when passport number check digit is tampered."""
    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    # Changed passport check digit from 6 to 0
    line2 = "L898902C30UTO7408122F1204159ZE184226B<<<<<10"

    res = parse_and_validate_td3_mrz(line1, line2)
    assert res.is_valid is False
    assert res.passport_number_valid is False
    assert any("Passport number check digit failed" in err for err in res.error_messages)
