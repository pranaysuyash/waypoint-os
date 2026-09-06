"""
ICAO Doc 9303 MRZ & Travel Voucher Parser Tests (PER-DOC, DOC-01..12).
"""

from src.intake.mrz_parser_engine import MRZParserEngine


def test_icao_731_check_digit_calculation():
    # Passport Number "L898902C<" -> Check Digit 3
    # L(21)*7 + 8*3 + 9*1 + 8*7 + 9*3 + 0*1 + 2*7 + C(12)*3 + <(0)*1 = 147 + 24 + 9 + 56 + 27 + 0 + 14 + 36 + 0 = 313 -> 313 % 10 = 3
    calc = MRZParserEngine.calculate_check_digit("L898902C<")
    assert calc == 3
    assert MRZParserEngine.verify_check_digit("L898902C<", "3") is True


def test_parse_td3_passport_mrz():
    # Standard 2-line TD3 MRZ sample
    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C<3UTO6908061F2801027ZE184226B<<<<<10"

    parsed = MRZParserEngine.parse_td3_passport(line1, line2)
    assert parsed.surname == "ERIKSSON"
    assert parsed.given_names == "ANNA MARIA"
    assert parsed.passport_number == "L898902C"
    assert parsed.nationality == "UTO"
    assert parsed.gender == "F"
    assert parsed.is_passport_number_valid is True
    assert parsed.is_dob_valid is True
    assert parsed.is_expiry_valid is True


def test_eticket_and_voucher_extraction():
    sample_text = """
    ELECTRONIC TICKET RECEIPT
    AIRLINE: DELTA AIR LINES
    TICKET NUMBER: 006-2345678901
    BOOKING REF: W4KZ9L
    HOTEL CONFIRMATION: HTL-883921
    """
    res = MRZParserEngine.extract_eticket_and_voucher(sample_text)
    assert res["e_ticket_number"] == "006-2345678901"
    assert res["airline_prefix"] == "006"
    assert res["pnr_locator"] == "W4KZ9L"
    assert res["hotel_confirmation_code"] == "HTL-883921"
    assert res["is_valid_eticket"] is True
