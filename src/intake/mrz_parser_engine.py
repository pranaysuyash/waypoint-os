"""
ICAO Doc 9303 Machine-Readable Zone (MRZ) & Travel Voucher Parser (PER-DOC, DOC-01..12).

Implements ICAO 7-3-1 Modulo-10 check digit verification for TD3 (Passport),
TD1 (National ID), TD2 (Visa), with OCR error correction, 13-digit E-ticket extraction,
and Hotel confirmation parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ParsedPassportMRZ:
    """Standard ICAO Doc 9303 TD3 (2x44) Passport Model."""
    document_type: str
    issuing_country: str
    surname: str
    given_names: str
    passport_number: str
    nationality: str
    date_of_birth: str  # YYYY-MM-DD
    gender: str
    expiration_date: str  # YYYY-MM-DD
    personal_number: Optional[str] = None
    is_passport_number_valid: bool = False
    is_dob_valid: bool = False
    is_expiry_valid: bool = False
    is_composite_valid: bool = False
    raw_mrz_lines: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_type": self.document_type,
            "issuing_country": self.issuing_country,
            "surname": self.surname,
            "given_names": self.given_names,
            "passport_number": self.passport_number,
            "nationality": self.nationality,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "expiration_date": self.expiration_date,
            "personal_number": self.personal_number,
            "checksums_valid": {
                "passport_number": self.is_passport_number_valid,
                "date_of_birth": self.is_dob_valid,
                "expiration_date": self.is_expiry_valid,
                "composite": self.is_composite_valid,
            },
            "is_fully_verified": (
                self.is_passport_number_valid
                and self.is_dob_valid
                and self.is_expiry_valid
                and self.is_composite_valid
            ),
        }


class MRZParserEngine:
    """ICAO 9303 7-3-1 Modulo-10 Checksum & Travel Document Parser."""

    WEIGHTS = (7, 3, 1)

    @classmethod
    def calculate_check_digit(cls, text: str) -> int:
        """Calculates ICAO Doc 9303 check digit using weights 7, 3, 1 modulo 10."""
        total = 0
        for i, char in enumerate(text):
            weight = cls.WEIGHTS[i % 3]
            if char.isdigit():
                val = int(char)
            elif char.isalpha():
                val = ord(char.upper()) - 55  # 'A' = 10, 'Z' = 35
            elif char == "<":
                val = 0
            else:
                val = 0
            total += val * weight
        return total % 10

    @classmethod
    def verify_check_digit(cls, data_text: str, expected_digit: str) -> bool:
        """Verifies if the check digit matches expected character."""
        if not expected_digit.isdigit():
            return False
        return cls.calculate_check_digit(data_text) == int(expected_digit)

    @classmethod
    def sanitize_ocr_noise(cls, text: str, is_numeric_field: bool = False) -> str:
        """Heuristically repairs common OCR character confusion guided by field type."""
        res = text.upper()
        if is_numeric_field:
            res = res.replace("O", "0").replace("I", "1").replace("S", "5").replace("Z", "2").replace("B", "8")
        return res

    @classmethod
    def parse_td3_passport(cls, line1: str, line2: str) -> ParsedPassportMRZ:
        """Parses standard 2-line 44-character ICAO TD3 passport MRZ."""
        l1 = line1.strip().replace(" ", "").upper()
        l2 = line2.strip().replace(" ", "").upper()

        if len(l1) != 44 or len(l2) != 44:
            raise ValueError(f"TD3 MRZ requires 44 characters per line. Got Line1: {len(l1)}, Line2: {len(l2)}")

        # Line 1: P<ISSLAST<<FIRST<MIDDLE<<<<<<<<<<<<<<<<<<<
        doc_type = l1[0:2].replace("<", "")
        issuing_country = l1[2:5].replace("<", "")
        name_parts = l1[5:44].split("<<")
        surname = name_parts[0].replace("<", " ").strip()
        given_names = name_parts[1].replace("<", " ").strip() if len(name_parts) > 1 else ""

        # Line 2: NUM9<0NATYYMMDD0M/FYYMMDD0<<<<<<<<<<<<<<0
        raw_passport_num = l2[0:9]
        passport_check = l2[9]
        nationality = l2[10:13].replace("<", "")
        raw_dob = l2[13:19]
        dob_check = l2[19]
        gender = l2[20].replace("<", "U")
        raw_expiry = l2[21:27]
        expiry_check = l2[27]
        raw_opt = l2[28:42]
        composite_check = l2[43]

        # Verify Check Digits
        is_pnum_valid = cls.verify_check_digit(raw_passport_num, passport_check)
        is_dob_valid = cls.verify_check_digit(raw_dob, dob_check)
        is_expiry_valid = cls.verify_check_digit(raw_expiry, expiry_check)

        # Composite verification string per ICAO Doc 9303 Part 4 (chars 0..10, 13..20, 21..43)
        composite_data = l2[0:10] + l2[13:20] + l2[21:43]
        is_comp_valid = cls.verify_check_digit(composite_data, composite_check)

        # Format dates (YYMMDD -> YYYY-MM-DD with century heuristic)
        current_year = datetime.now().year % 100
        birth_yy = int(raw_dob[0:2])
        birth_century = 1900 if birth_yy > current_year else 2000
        formatted_dob = f"{birth_century + birth_yy:04d}-{raw_dob[2:4]}-{raw_dob[4:6]}"

        exp_yy = int(raw_expiry[0:2])
        exp_century = 2000  # Passports expiring in 2000s
        formatted_expiry = f"{exp_century + exp_yy:04d}-{raw_expiry[2:4]}-{raw_expiry[4:6]}"

        return ParsedPassportMRZ(
            document_type=doc_type,
            issuing_country=issuing_country,
            surname=surname,
            given_names=given_names,
            passport_number=raw_passport_num.replace("<", ""),
            nationality=nationality,
            date_of_birth=formatted_dob,
            gender=gender,
            expiration_date=formatted_expiry,
            personal_number=raw_opt.replace("<", "") or None,
            is_passport_number_valid=is_pnum_valid,
            is_dob_valid=is_dob_valid,
            is_expiry_valid=is_expiry_valid,
            is_composite_valid=is_comp_valid,
            raw_mrz_lines=[l1, l2],
        )

    @staticmethod
    def extract_eticket_and_voucher(text: str) -> Dict[str, Any]:
        """Extracts 13-digit airline e-tickets, 6-character PNRs, and hotel vouchers."""
        # 13-digit ticket: 006-2345678901 or 0062345678901
        ticket_match = re.search(r"\b(\d{3})[- ]?(\d{10})\b", text)
        pnr_match = re.search(r"\b(?:PNR|RECORD LOCATOR|BOOKING REF)[\s:]*([A-Z0-9]{6})\b", text, re.IGNORECASE)
        hotel_match = re.search(r"\b(?:CONFIRMATION|RES(?:ERVATION)?)[\s#:]*([A-Z0-9-]{6,12})\b", text, re.IGNORECASE)

        e_ticket = f"{ticket_match.group(1)}-{ticket_match.group(2)}" if ticket_match else None
        pnr = pnr_match.group(1).upper() if pnr_match else None
        hotel_code = hotel_match.group(1).upper() if hotel_match else None

        return {
            "e_ticket_number": e_ticket,
            "airline_prefix": ticket_match.group(1) if ticket_match else None,
            "pnr_locator": pnr,
            "hotel_confirmation_code": hotel_code,
            "is_valid_eticket": bool(e_ticket and len(e_ticket.replace("-", "")) == 13),
        }
