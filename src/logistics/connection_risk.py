"""
src/logistics/connection_risk.py — Flight Connection & Hub Transit Risk Scorer (Area #17.18).

Implements:
1. IATA Minimum Connection Time (MCT) validation by hub airport.
2. Terminal Change & Inter-Airport Transit Penalties (e.g. CDG 2E->2G, LHR T2->T5, NRT->HND).
3. Separate PNR / Self-Transfer Risk Modeling (customs clearance + baggage re-check requirement).
4. Automated Layover Stress & Misconnect Probability Classification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ConnectionRiskLevel(str, Enum):
    SAFE = "SAFE"
    TIGHT_BUFFER = "TIGHT_BUFFER"
    HIGH_MISCONNECT_RISK = "HIGH_MISCONNECT_RISK"
    ILLEGAL_MCT_VIOLATION = "ILLEGAL_MCT_VIOLATION"


@dataclass(slots=True)
class HubTransitSpec:
    airport_code: str
    hub_name: str
    mct_same_terminal_mins: int
    mct_terminal_change_mins: int
    immigration_reclear_penalty_mins: int = 45
    self_transfer_penalty_mins: int = 90
    description: str = ""
    terminal_pair_mct_mins: Dict[Tuple[str, str], int] = field(default_factory=dict)

    def get_terminal_pair_mct(self, from_terminal: str, to_terminal: str) -> Optional[int]:
        """Look up fine-grained minimum connection time between specific terminal pairs."""
        t1 = from_terminal.strip().upper()
        t2 = to_terminal.strip().upper()
        # Direct lookup (t1, t2)
        if (t1, t2) in self.terminal_pair_mct_mins:
            return self.terminal_pair_mct_mins[(t1, t2)]
        # Symmetric check (t2, t1)
        if (t2, t1) in self.terminal_pair_mct_mins:
            return self.terminal_pair_mct_mins[(t2, t1)]
        # Normalize strip 'T' prefix e.g. "T2" -> "2" or vice versa
        t1_raw = t1.removeprefix("T")
        t2_raw = t2.removeprefix("T")
        if (t1_raw, t2_raw) in self.terminal_pair_mct_mins:
            return self.terminal_pair_mct_mins[(t1_raw, t2_raw)]
        if (t2_raw, t1_raw) in self.terminal_pair_mct_mins:
            return self.terminal_pair_mct_mins[(t2_raw, t1_raw)]
        return None


# Canonical Hub MCT Directory with Fine-Grained Terminal-Pair Transit Times
HUB_MCT_CATALOG: Dict[str, HubTransitSpec] = {
    "DXB": HubTransitSpec(
        airport_code="DXB",
        hub_name="Dubai International",
        mct_same_terminal_mins=60,
        mct_terminal_change_mins=90,
        immigration_reclear_penalty_mins=30,
        self_transfer_penalty_mins=90,
        description="Large hub; Terminal 3 to Terminal 2 shuttle requires 30m+ airside bus transit.",
        terminal_pair_mct_mins={
            ("T3", "T2"): 120,
            ("T2", "T3"): 120,
            ("T1", "T2"): 105,
            ("T2", "T1"): 105,
            ("T1", "T3"): 75,
            ("T3", "T1"): 75,
        },
    ),
    "CDG": HubTransitSpec(
        airport_code="CDG",
        hub_name="Paris Charles de Gaulle",
        mct_same_terminal_mins=60,
        mct_terminal_change_mins=90,
        immigration_reclear_penalty_mins=45,
        self_transfer_penalty_mins=90,
        description="Terminal 2E to 2G/2F transfers require shuttle bus and mandatory security re-screening.",
        terminal_pair_mct_mins={
            ("2E", "2G"): 105,
            ("2G", "2E"): 105,
            ("2F", "2G"): 90,
            ("2G", "2F"): 90,
            ("2E", "2F"): 75,
            ("2F", "2E"): 75,
            ("1", "2E"): 95,
            ("2E", "1"): 95,
            ("1", "2G"): 110,
            ("2G", "1"): 110,
            ("2A", "2E"): 85,
            ("2E", "2A"): 85,
        },
    ),
    "LHR": HubTransitSpec(
        airport_code="LHR",
        hub_name="London Heathrow",
        mct_same_terminal_mins=60,
        mct_terminal_change_mins=90,
        immigration_reclear_penalty_mins=45,
        self_transfer_penalty_mins=90,
        description="Inter-terminal transfers (T2/T3 to T5/T4) require flight connection bus or Heathrow Express.",
        terminal_pair_mct_mins={
            ("T2", "T5"): 105,
            ("T5", "T2"): 105,
            ("T3", "T5"): 95,
            ("T5", "T3"): 95,
            ("T4", "T5"): 105,
            ("T5", "T4"): 105,
            ("T2", "T3"): 75,
            ("T3", "T2"): 75,
            ("T2", "T4"): 90,
            ("T4", "T2"): 90,
            ("T3", "T4"): 90,
            ("T4", "T3"): 90,
        },
    ),
    "JFK": HubTransitSpec(
        airport_code="JFK",
        hub_name="New York JFK",
        mct_same_terminal_mins=60,
        mct_terminal_change_mins=105,
        immigration_reclear_penalty_mins=60,
        self_transfer_penalty_mins=90,
        description="AirTrain between non-connected terminals requires clearing TSA security at destination terminal.",
        terminal_pair_mct_mins={
            ("T4", "T8"): 120,
            ("T8", "T4"): 120,
            ("T1", "T4"): 105,
            ("T4", "T1"): 105,
            ("T1", "T8"): 120,
            ("T8", "T1"): 120,
            ("T5", "T8"): 105,
            ("T8", "T5"): 105,
            ("T4", "T7"): 105,
            ("T7", "T4"): 105,
            ("T7", "T8"): 105,
            ("T8", "T7"): 105,
            ("4", "8"): 120,
            ("8", "4"): 120,
            ("1", "4"): 105,
            ("4", "1"): 105,
            ("1", "8"): 120,
            ("8", "1"): 120,
        },
    ),
    "FRA": HubTransitSpec(
        airport_code="FRA",
        hub_name="Frankfurt Airport",
        mct_same_terminal_mins=45,
        mct_terminal_change_mins=75,
        immigration_reclear_penalty_mins=35,
        self_transfer_penalty_mins=90,
        description="Long concourses; SkyLine elevated train connects Terminal 1 and Terminal 2.",
        terminal_pair_mct_mins={
            ("T1", "T2"): 75,
            ("T2", "T1"): 75,
            ("1", "2"): 75,
            ("2", "1"): 75,
        },
    ),
    "SIN": HubTransitSpec(
        airport_code="SIN",
        hub_name="Singapore Changi",
        mct_same_terminal_mins=45,
        mct_terminal_change_mins=60,
        immigration_reclear_penalty_mins=20,
        self_transfer_penalty_mins=75,
        description="Highly efficient Skytrain connecting T1/T2/T3; shuttle bus to T4.",
        terminal_pair_mct_mins={
            ("T1", "T4"): 75,
            ("T4", "T1"): 75,
            ("T2", "T4"): 75,
            ("T4", "T2"): 75,
            ("T3", "T4"): 75,
            ("T4", "T3"): 75,
        },
    ),
    "HND": HubTransitSpec(
        airport_code="HND",
        hub_name="Tokyo Haneda",
        mct_same_terminal_mins=45,
        mct_terminal_change_mins=70,
        immigration_reclear_penalty_mins=30,
        self_transfer_penalty_mins=80,
        description="Domestic (T1/T2) to International (T3) terminal shuttle bus.",
        terminal_pair_mct_mins={
            ("T1", "T3"): 80,
            ("T3", "T1"): 80,
            ("T2", "T3"): 80,
            ("T3", "T2"): 80,
            ("T1", "T2"): 60,
            ("T2", "T1"): 60,
        },
    ),
    "BOM": HubTransitSpec(
        airport_code="BOM",
        hub_name="Mumbai Chhatrapati Shivaji",
        mct_same_terminal_mins=45,
        mct_terminal_change_mins=90,
        immigration_reclear_penalty_mins=45,
        self_transfer_penalty_mins=90,
        description="T1 (Domestic) to T2 (International) requires city road taxi/coach transfer.",
        terminal_pair_mct_mins={
            ("T1", "T2"): 105,
            ("T2", "T1"): 105,
            ("1", "2"): 105,
            ("2", "1"): 105,
        },
    ),
    "DEL": HubTransitSpec(
        airport_code="DEL",
        hub_name="Delhi Indira Gandhi",
        mct_same_terminal_mins=45,
        mct_terminal_change_mins=90,
        immigration_reclear_penalty_mins=40,
        self_transfer_penalty_mins=90,
        description="T1/T2 to T3 transfer requires landside airport shuttle bus.",
        terminal_pair_mct_mins={
            ("T1", "T3"): 100,
            ("T3", "T1"): 100,
            ("T2", "T3"): 75,
            ("T3", "T2"): 75,
            ("T1", "T2"): 75,
            ("T2", "T1"): 75,
        },
    ),
    "DEFAULT": HubTransitSpec(
        airport_code="DEFAULT",
        hub_name="Standard International Hub",
        mct_same_terminal_mins=50,
        mct_terminal_change_mins=80,
        immigration_reclear_penalty_mins=30,
        self_transfer_penalty_mins=90,
        description="Default IATA MCT baseline.",
    ),
}


@dataclass(slots=True)
class ConnectionEvaluationResult:
    connection_airport: str
    inbound_flight: str
    outbound_flight: str
    layover_minutes: int
    required_mct_minutes: int
    risk_level: ConnectionRiskLevel
    is_same_terminal: bool
    is_self_transfer: bool
    warnings: List[str] = field(default_factory=list)
    recommendation: str = ""


class ConnectionRiskScorer:
    """
    Evaluates flight transit itineraries to detect illegal or high-risk connection layovers.
    Supports fine-grained terminal-pair Minimum Connection Time (MCT) lookups,
    separate PNR self-transfer penalties (+60m to +90m), and immigration clearance audits.
    """

    @classmethod
    def evaluate_connection(
        cls,
        connection_airport: str,
        inbound_flight: str,
        outbound_flight: str,
        layover_minutes: int,
        inbound_terminal: str = "T1",
        outbound_terminal: str = "T1",
        is_self_transfer: bool = False,
        requires_immigration_reclear: bool = False,
        custom_self_transfer_penalty_mins: Optional[int] = None,
    ) -> ConnectionEvaluationResult:
        hub_code = connection_airport.strip().upper()
        hub = HUB_MCT_CATALOG.get(hub_code, HUB_MCT_CATALOG["DEFAULT"])

        inbound_term_clean = inbound_terminal.strip().upper()
        outbound_term_clean = outbound_terminal.strip().upper()
        is_same_terminal = (inbound_term_clean == outbound_term_clean)

        # 1. Fine-grained terminal-pair MCT lookup
        specific_pair_mct = hub.get_terminal_pair_mct(inbound_term_clean, outbound_term_clean)

        if is_same_terminal:
            base_mct = hub.mct_same_terminal_mins
        elif specific_pair_mct is not None:
            base_mct = specific_pair_mct
        else:
            base_mct = hub.mct_terminal_change_mins

        required_mct = base_mct
        warnings: List[str] = []

        if not is_same_terminal:
            if specific_pair_mct is not None:
                warnings.append(
                    f"Terminal change ({inbound_terminal} ➔ {outbound_terminal}) at {hub.hub_name}: "
                    f"fine-grained route minimum is {specific_pair_mct}m."
                )
            else:
                warnings.append(f"Terminal change ({inbound_terminal} ➔ {outbound_terminal}) at {hub.hub_name}.")

        # 2. Immigration & customs re-screening penalty
        if requires_immigration_reclear:
            immig_penalty = hub.immigration_reclear_penalty_mins
            required_mct += immig_penalty
            warnings.append(
                f"🛂 Passport Control & Security Re-Screening (+{immig_penalty}m): "
                f"International arrival requires entering border control and re-clearing departure security."
            )

        # 3. Self-transfer / Separate PNR penalty (+60m to +90m)
        if is_self_transfer:
            penalty = (
                custom_self_transfer_penalty_mins
                if custom_self_transfer_penalty_mins is not None
                else hub.self_transfer_penalty_mins
            )
            required_mct += penalty
            warnings.append(
                f"🚨 Self-Transfer / Separate PNR (+{penalty}m): Baggage is NOT interlined. "
                f"Traveler must exit airside, claim baggage at carousel, transfer between terminals landside, "
                f"queue at check-in desk before cutoff (T-60m), and clear TSA/departure security."
            )

        # 4. Classify risk level
        # Legal MCT boundary is the airline's scheduled minimum (base_mct for single ticket, or base_mct + 30 for self transfer)
        legal_threshold = base_mct if not is_self_transfer else (base_mct + 30)

        if layover_minutes < legal_threshold:
            risk_level = ConnectionRiskLevel.ILLEGAL_MCT_VIOLATION
            rec = (
                f"Connection is below IATA Minimum Connection Time ({layover_minutes}m < {required_mct}m). "
                f"Inbound flight delay will cause guaranteed misconnect. Airlines will not protect misconnect on separate tickets."
            )
        elif layover_minutes < required_mct:
            risk_level = ConnectionRiskLevel.HIGH_MISCONNECT_RISK
            rec = (
                f"High risk of baggage and passenger misconnect ({layover_minutes}m layover vs {required_mct}m required). "
                f"Minimal tolerance for taxi delays or customs queues."
            )
        elif layover_minutes < (required_mct + 20):
            risk_level = ConnectionRiskLevel.TIGHT_BUFFER
            rec = "Tight connection. Recommend fast-track transit and notifying cabin crew upon boarding."
        else:
            risk_level = ConnectionRiskLevel.SAFE
            rec = f"Comfortable layover ({layover_minutes}m) safely exceeding {required_mct}m minimum transit threshold."

        return ConnectionEvaluationResult(
            connection_airport=hub_code,
            inbound_flight=inbound_flight,
            outbound_flight=outbound_flight,
            layover_minutes=layover_minutes,
            required_mct_minutes=required_mct,
            risk_level=risk_level,
            is_same_terminal=is_same_terminal,
            is_self_transfer=is_self_transfer,
            warnings=warnings,
            recommendation=rec,
        )
