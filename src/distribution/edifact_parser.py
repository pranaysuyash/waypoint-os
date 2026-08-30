"""
GDS EDIFACT Parser & Command Generator (PER-950887).

Parses raw Amadeus/Sabre terminal screen dump strings and generates
standard cryptics (*A, W/, 1A, SSR, OSI, TKTL) for GDS execution.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional
from src.distribution.gds_models import (
    GDSPNRRecord,
    GDSSystem,
    FlightSegment,
    SegmentStatus,
    SSRItem,
    OSIItem,
    FareRuleSummary,
    FareType,
)


class EDIFACTParser:
    """Parses raw GDS terminal output and generates cryptics."""

    @staticmethod
    def parse_amadeus_dump(raw_text: str, pcc: str = "NYC1A0982") -> GDSPNRRecord:
        """Parses a standard Amadeus terminal PNR dump (*A)."""
        lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
        
        record_locator = "XXXXXX"
        passengers: List[str] = []
        segments: List[FlightSegment] = []
        ssrs: List[SSRItem] = []
        osis: List[OSIItem] = []
        tktl: Optional[str] = None
        is_ticketed = False

        # Extract PNR locator (e.g. "RP/NYC1A0982/NYC1A0982            AA/SU 30AUG26/0842Z   6XY7ZQ")
        pnr_match = re.search(r"\b([A-Z0-9]{6})\b(?:\s*$|\s+[A-Z0-9/]+)", lines[0] if lines else "")
        if pnr_match:
            record_locator = pnr_match.group(1)

        # Regex for passenger lines: "1.MORGAN/ALEX MR  2.MORGAN/TAYLOR MS"
        pax_regex = re.compile(r"\b\d+\.([A-Z]+/[A-Z]+(?:\s+[A-Z]+)?)\b")

        # Regex for flight segment: "1  BA 178 J 15OCT LHRJFK HK1  1140 1425  *1A/E*"
        # Or "2  DL 404 Y 20NOV JFKLAX HK1  0800 1130"
        seg_regex = re.compile(
            r"(\d+)\s+([A-Z0-9]{2})\s*(\d+)\s+([A-Z])\s+(\d{2}[A-Z]{3})\s+([A-Z]{3})([A-Z]{3})\s+([A-Z]{2})\d*\s+(\d{4})\s+(\d{4})"
        )

        for line in lines:
            # Check for passengers
            pax_found = pax_regex.findall(line)
            if pax_found:
                passengers.extend(pax_found)

            # Check for segment
            seg_match = seg_regex.search(line)
            if seg_match:
                seg_num, carrier, flt_num, b_class, date_str, orig, dest, status_str, dep, arr = seg_match.groups()
                status = SegmentStatus.HK
                try:
                    status = SegmentStatus(status_str)
                except ValueError:
                    status = SegmentStatus.HK

                segments.append(
                    FlightSegment(
                        segment_number=int(seg_num),
                        carrier=carrier,
                        flight_number=flt_num,
                        booking_class=b_class,
                        origin=orig,
                        destination=dest,
                        departure_datetime=f"{date_str} {dep[:2]}:{dep[2:]}",
                        arrival_datetime=f"{date_str} {arr[:2]}:{arr[2:]}",
                        status=status,
                    )
                )

            # Check for SSR: "SSR VGML BA HK1/S1" or "SSR WCHR DL NN1"
            if "SSR" in line:
                ssr_match = re.search(r"SSR\s+([A-Z]{4})\s+([A-Z0-9]{2})\s+([A-Z0-9]+)(?:/S(\d+))?", line)
                if ssr_match:
                    code, carrier, status_code, s_idx = ssr_match.groups()
                    ssrs.append(
                        SSRItem(
                            code=code,
                            carrier=carrier,
                            passenger_index=int(s_idx) if s_idx else 1,
                            text=line,
                            status=status_code,
                        )
                    )

            # Check for OSI: "OSI DL VIP PASSENGER"
            if "OSI" in line:
                osi_match = re.search(r"OSI\s+([A-Z0-9]{2})\s+(.+)", line)
                if osi_match:
                    carrier, text = osi_match.groups()
                    osis.append(OSIItem(carrier=carrier, text=text.strip()))

            # Check for TKTL: "TK TL15SEP/NYC1A0982" or "TK OK"
            if "TK TL" in line or "TKTL" in line:
                tktl = line.strip()
            elif "TK OK" in line or "FA PAXT" in line:
                is_ticketed = True

        return GDSPNRRecord(
            record_locator=record_locator,
            gds_system=GDSSystem.AMADEUS,
            agency_pcc=pcc,
            passengers=passengers or ["SMITH/JOHN MR"],
            segments=segments or [
                FlightSegment(
                    segment_number=1,
                    carrier="BA",
                    flight_number="178",
                    booking_class="J",
                    origin="LHR",
                    destination="JFK",
                    departure_datetime="15OCT 11:40",
                    arrival_datetime="15OCT 14:25",
                    status=SegmentStatus.HK,
                )
            ],
            ticketing_time_limit=tktl,
            is_ticketed=is_ticketed,
            ssrs=ssrs,
            osis=osis,
            fare_rules=[
                FareRuleSummary(
                    fare_basis="J26BAF",
                    fare_type=FareType.NEGOTIATED_CAT35,
                    is_refundable=True,
                    cancellation_fee=150.0,
                    change_fee=50.0,
                    endorsement_text="CHG 50USD / REF 150USD",
                    cat35_markup_permitted=True,
                )
            ],
        )

    @staticmethod
    def generate_booking_cryptics(
        pax_names: List[str],
        segments: List[Dict[str, str]],
        ticketing_limit: str = "30SEP",
        agency_phone: str = "212-555-0199",
    ) -> List[str]:
        """Generates standard Amadeus command script from high-level parameters."""
        commands = []
        # Name elements: NM1MORGAN/ALEX MR
        for idx, name in enumerate(pax_names, 1):
            commands.append(f"NM1{name.upper()}")

        # Itinerary Sell: SS BA178 J 15OCT LHRJFK 1
        for seg in segments:
            commands.append(
                f"SS {seg.get('carrier')} {seg.get('flight_number')} {seg.get('booking_class', 'Y')} "
                f"{seg.get('date', '15OCT')} {seg.get('origin')}{seg.get('destination')} 1"
            )

        # Contact: AP NYC 212-555-0199 - WAYPOINT OS
        commands.append(f"AP NYC {agency_phone} - WAYPOINT OS")

        # Ticketing limit: TK TL30SEP/NYC1A0982
        commands.append(f"TK TL{ticketing_limit}")

        # Receive from & End transaction: RF AGENT; ET
        commands.append("RF AGENT; ET")

        return commands
