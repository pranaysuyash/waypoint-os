"""
Test Scenarios for Notebook 02 Gap & Decision Pipeline

This module provides 30+ CanonicalPacket fixtures for comprehensive testing.
Each scenario is a factory function returning a configured packet.

Usage:
    from data.fixtures.test_scenarios import TestScenarios
    
    # Get a specific scenario
    packet = TestScenarios.basic_empty()
    
    # Get all scenarios
    all_scenarios = TestScenarios.get_all()
    
    # Run tests
    for name, packet in all_scenarios.items():
        result = run_gap_and_decision(packet)
        print(f"{name}: {result.decision_state}")
"""

import sys
sys.path.insert(0, '/Users/pranay/Projects/travel_agency_agent')

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# Minimal CanonicalPacket implementation for fixtures
@dataclass
class EvidenceRef:
    ref_id: str
    envelope_id: str
    evidence_type: str
    excerpt: str
    field_path: Optional[str] = None
    confidence: float = 1.0

@dataclass
class Slot:
    value: Any = None
    confidence: float = 0.0
    authority_level: str = "unknown"
    extraction_mode: str = "unknown"
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class UnknownField:
    field_name: str
    reason: str = "not_present_in_source"

@dataclass
class CanonicalPacket:
    packet_id: str
    created_at: str
    last_updated: str
    facts: Dict[str, Slot] = field(default_factory=dict)
    derived_signals: Dict[str, Slot] = field(default_factory=dict)
    hypotheses: Dict[str, Slot] = field(default_factory=dict)
    unknowns: List[UnknownField] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    source_envelope_ids: List[str] = field(default_factory=list)
    stage: str = "discovery"


class TestScenarios:
    """Factory class for all test scenarios."""
    
    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat()
    
    @staticmethod
    def _evidence(excerpt: str, envelope: str = "env_test") -> EvidenceRef:
        return EvidenceRef(
            ref_id=f"ref_{uuid.uuid4().hex[:6]}",
            envelope_id=envelope,
            evidence_type="text_span",
            excerpt=excerpt
        )

    # =========================================================================
    # CATEGORY A: Basic Flows (6 scenarios)
    # =========================================================================
    
    @classmethod
    def basic_empty(cls) -> CanonicalPacket:
        """A1: Empty packet - baseline test."""
        return CanonicalPacket(
            packet_id="pkt_basic_empty",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery"
        )
    
    @classmethod
    def basic_complete_discovery(cls) -> CanonicalPacket:
        """A2: Complete discovery packet - all fields filled."""
        return CanonicalPacket(
            packet_id="pkt_basic_complete",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(
                    value="Singapore", confidence=0.95, authority_level="explicit_user",
                    evidence_refs=[cls._evidence("Singapore")]
                ),
                "origin_city": Slot(
                    value="Bangalore", confidence=0.95, authority_level="explicit_user",
                    evidence_refs=[cls._evidence("Bangalore")]
                ),
                "travel_dates": Slot(
                    value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user",
                    evidence_refs=[cls._evidence("March 15-22")]
                ),
                "traveler_count": Slot(
                    value=5, confidence=0.95, authority_level="explicit_user",
                    evidence_refs=[cls._evidence("5 people")]
                ),
                "budget_range": Slot(
                    value="mid_range", confidence=0.80, authority_level="explicit_owner",
                    evidence_refs=[cls._evidence("mid-range")]
                ),
                "trip_purpose": Slot(
                    value="family leisure", confidence=0.85, authority_level="explicit_user",
                    evidence_refs=[cls._evidence("family leisure")]
                ),
                "traveler_preferences": Slot(
                    value="relaxed pace, kid-friendly", confidence=0.80, authority_level="explicit_user",
                    evidence_refs=[cls._evidence("relaxed, kid-friendly")]
                ),
            }
        )
    
    @classmethod
    def basic_hypothesis_only(cls) -> CanonicalPacket:
        """A3: Hypothesis-only packet - hypotheses do NOT fill blockers."""
        return CanonicalPacket(
            packet_id="pkt_hypothesis_only",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "origin_city": Slot(
                    value="Bangalore", confidence=0.90, authority_level="explicit_owner",
                    evidence_refs=[cls._evidence("Bangalore")]
                ),
            },
            hypotheses={
                "destination_city": Slot(
                    value="Singapore", confidence=0.50, authority_level="soft_hypothesis",
                    evidence_refs=[cls._evidence("maybe Singapore")]
                ),
                "travel_dates": Slot(
                    value="March 2026", confidence=0.40, authority_level="soft_hypothesis",
                    evidence_refs=[cls._evidence("sometime March")]
                ),
                "traveler_count": Slot(
                    value=4, confidence=0.45, authority_level="soft_hypothesis",
                    evidence_refs=[cls._evidence("family of 4")]
                ),
            }
        )
    
    @classmethod
    def basic_derived_fills(cls) -> CanonicalPacket:
        """A4: Derived signal fills hard blocker."""
        return CanonicalPacket(
            packet_id="pkt_derived_fills",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "origin_city": Slot(
                    value="Bangalore", confidence=0.90, authority_level="explicit_owner",
                    evidence_refs=[cls._evidence("Bangalore")]
                ),
                "traveler_count": Slot(
                    value=5, confidence=0.95, authority_level="explicit_user",
                    evidence_refs=[cls._evidence("5 travelers")]
                ),
                "travel_dates": Slot(
                    value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user",
                    evidence_refs=[cls._evidence("March 15-22")]
                ),
            },
            derived_signals={
                "destination_city": Slot(
                    value="Singapore",
                    confidence=0.75,
                    authority_level="derived_signal",
                    extraction_mode="derived",
                    evidence_refs=[
                        EvidenceRef(
                            ref_id="ref_derived",
                            envelope_id="env_notes",
                            evidence_type="derived",
                            excerpt="Inferred from flight route + hotel mentions"
                        )
                    ]
                ),
            }
        )
    
    @classmethod
    def basic_soft_only(cls) -> CanonicalPacket:
        """A5: Soft blockers only - no hard blockers."""
        return CanonicalPacket(
            packet_id="pkt_soft_only",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            }
        )
    
    @classmethod
    def basic_minimal_safe(cls) -> CanonicalPacket:
        """A6: Minimum viable traveler-safe - low confidence edge."""
        return CanonicalPacket(
            packet_id="pkt_minimal_safe",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.60, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.60, authority_level="explicit_user"),
                "travel_dates": Slot(value="March 2026", confidence=0.60, authority_level="explicit_user"),
                "traveler_count": Slot(value=2, confidence=0.60, authority_level="explicit_user"),
                "budget_range": Slot(value="mid_range", confidence=0.60, authority_level="explicit_user"),
                "trip_purpose": Slot(value="leisure", confidence=0.60, authority_level="explicit_user"),
                "traveler_preferences": Slot(value="none", confidence=0.60, authority_level="explicit_user"),
            }
        )

    # =========================================================================
    # CATEGORY B: Contradictions (5 scenarios)
    # =========================================================================
    
    @classmethod
    def contradiction_date_critical(cls) -> CanonicalPacket:
        """B1: Date contradiction - critical, should STOP_NEEDS_REVIEW."""
        return CanonicalPacket(
            packet_id="pkt_date_conflict",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(
                    value=["2026-03-15", "2026-04-01"],
                    confidence=0.70,
                    authority_level="explicit_owner",
                    evidence_refs=[
                        cls._evidence("March 15", "env1"),
                        cls._evidence("April 1", "env2"),
                    ]
                ),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            },
            contradictions=[{
                "field_name": "travel_dates",
                "values": ["2026-03-15", "2026-04-01"],
                "sources": ["env1", "env2"]
            }]
        )
    
    @classmethod
    def contradiction_budget_branch(cls) -> CanonicalPacket:
        """B2: Budget contradiction - should trigger BRANCH_OPTIONS."""
        return CanonicalPacket(
            packet_id="pkt_budget_conflict",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
                "budget_range": Slot(
                    value=["budget", "premium"],
                    confidence=0.60,
                    authority_level="explicit_owner",
                    evidence_refs=[
                        cls._evidence("budget trip", "env3"),
                        cls._evidence("wants premium hotels", "env4"),
                    ]
                ),
            },
            contradictions=[{
                "field_name": "budget_range",
                "values": ["budget", "premium"],
                "sources": ["env3", "env4"]
            }]
        )
    
    @classmethod
    def contradiction_destination_ask(cls) -> CanonicalPacket:
        """B3: Destination contradiction - should ASK_FOLLOWUP."""
        return CanonicalPacket(
            packet_id="pkt_dest_conflict",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(
                    value=["Singapore", "Thailand"],
                    confidence=0.70,
                    authority_level="explicit_user",
                    evidence_refs=[
                        cls._evidence("Singapore", "env1"),
                        cls._evidence("Thailand", "env2"),
                    ]
                ),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            },
            contradictions=[{
                "field_name": "destination_city",
                "values": ["Singapore", "Thailand"],
                "sources": ["env1", "env2"]
            }]
        )
    
    @classmethod
    def contradiction_count_ask(cls) -> CanonicalPacket:
        """B4: Traveler count contradiction."""
        return CanonicalPacket(
            packet_id="pkt_count_conflict",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(
                    value=[3, 5],
                    confidence=0.70,
                    authority_level="explicit_owner",
                    evidence_refs=[
                        cls._evidence("family of 3", "env1"),
                        cls._evidence("5 people", "env2"),
                    ]
                ),
            },
            contradictions=[{
                "field_name": "traveler_count",
                "values": [3, 5],
                "sources": ["env1", "env2"]
            }]
        )
    
    @classmethod
    def contradiction_origin_ask(cls) -> CanonicalPacket:
        """B5: Origin city contradiction."""
        return CanonicalPacket(
            packet_id="pkt_origin_conflict",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(
                    value=["Bangalore", "Mumbai"],
                    confidence=0.70,
                    authority_level="explicit_owner",
                    evidence_refs=[
                        cls._evidence("Bangalore", "env1"),
                        cls._evidence("Mumbai", "env2"),
                    ]
                ),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            },
            contradictions=[{
                "field_name": "origin_city",
                "values": ["Bangalore", "Mumbai"],
                "sources": ["env1", "env2"]
            }]
        )

    # =========================================================================
    # CATEGORY C: Authority Tests (5 scenarios)
    # =========================================================================
    
    @classmethod
    def authority_manual_override(cls) -> CanonicalPacket:
        """C1: Manual override has highest authority."""
        return CanonicalPacket(
            packet_id="pkt_manual_override",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Maldives", confidence=1.0, authority_level="manual_override"),
                "origin_city": Slot(value="Delhi", confidence=1.0, authority_level="manual_override"),
                "travel_dates": Slot(value="2026-05-01 to 2026-05-07", confidence=1.0, authority_level="manual_override"),
                "traveler_count": Slot(value=2, confidence=1.0, authority_level="manual_override"),
                "budget_range": Slot(value="luxury", confidence=1.0, authority_level="manual_override"),
            }
        )
    
    @classmethod
    def authority_owner_vs_imported(cls) -> CanonicalPacket:
        """C2: imported_structured > explicit_owner conflict."""
        return CanonicalPacket(
            packet_id="pkt_authority_conflict",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(
                    value="Mumbai",  # Owner said Mumbai
                    confidence=0.80,
                    authority_level="imported_structured",  # But CRM imported says Bangalore
                    evidence_refs=[cls._evidence("Mumbai", "crm_import")]
                ),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            },
            contradictions=[{
                "field_name": "origin_city",
                "values": ["Bangalore", "Mumbai"],
                "sources": ["owner_notes", "crm_import"]
            }]
        )
    
    @classmethod
    def authority_derived_vs_hypothesis(cls) -> CanonicalPacket:
        """C3: Derived fills blocker, hypothesis doesn't."""
        return CanonicalPacket(
            packet_id="pkt_derived_vs_hypo",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_owner"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
            },
            derived_signals={
                "destination_city": Slot(value="Singapore", confidence=0.70, authority_level="derived_signal"),
            },
            hypotheses={
                "traveler_count": Slot(value=4, confidence=0.50, authority_level="soft_hypothesis"),
            }
        )
    
    @classmethod
    def authority_explicit_user_high(cls) -> CanonicalPacket:
        """C4: All explicit_user - high authority."""
        return CanonicalPacket(
            packet_id="pkt_explicit_user",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Bali", confidence=0.95, authority_level="explicit_user"),
                "origin_city": Slot(value="Chennai", confidence=0.95, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-06-10 to 2026-06-17", confidence=0.95, authority_level="explicit_user"),
                "traveler_count": Slot(value=4, confidence=0.95, authority_level="explicit_user"),
                "budget_range": Slot(value="premium", confidence=0.90, authority_level="explicit_user"),
                "trip_purpose": Slot(value="anniversary", confidence=0.95, authority_level="explicit_user"),
                "traveler_preferences": Slot(value="beach, relaxation", confidence=0.90, authority_level="explicit_user"),
            }
        )
    
    @classmethod
    def authority_unknown_rejected(cls) -> CanonicalPacket:
        """C5: Unknown authority does not fill blockers."""
        return CanonicalPacket(
            packet_id="pkt_unknown_auth",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="???", confidence=0.0, authority_level="unknown"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026", confidence=0.3, authority_level="unknown"),
                "traveler_count": Slot(value="few", confidence=0.2, authority_level="unknown"),
            }
        )


    # =========================================================================
    # CATEGORY D: Stage Progression (4 scenarios)
    # =========================================================================
    
    @classmethod
    def stage_discovery_to_shortlist(cls) -> CanonicalPacket:
        """D1: Missing selected_destinations in shortlist stage."""
        return CanonicalPacket(
            packet_id="pkt_stage_shortlist",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="shortlist",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
                # Missing: selected_destinations
            }
        )
    
    @classmethod
    def stage_shortlist_to_proposal(cls) -> CanonicalPacket:
        """D2: Missing selected_itinerary in proposal stage."""
        return CanonicalPacket(
            packet_id="pkt_stage_proposal",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="proposal",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
                "selected_destinations": Slot(value=["Singapore", "Bali"], confidence=0.85, authority_level="explicit_user"),
                # Missing: selected_itinerary
            }
        )
    
    @classmethod
    def stage_proposal_to_booking(cls) -> CanonicalPacket:
        """D3: Missing traveler_details and payment_method in booking stage."""
        return CanonicalPacket(
            packet_id="pkt_stage_booking",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="booking",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
                "selected_destinations": Slot(value=["Singapore"], confidence=0.90, authority_level="explicit_user"),
                "selected_itinerary": Slot(value="singapore_family_package_v1", confidence=0.90, authority_level="explicit_user"),
                # Missing: traveler_details, payment_method
            }
        )
    
    @classmethod
    def stage_booking_complete(cls) -> CanonicalPacket:
        """D4: All booking fields filled."""
        return CanonicalPacket(
            packet_id="pkt_booking_complete",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="booking",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.95, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.95, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.95, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.95, authority_level="explicit_user"),
                "selected_destinations": Slot(value=["Singapore"], confidence=0.95, authority_level="explicit_user"),
                "selected_itinerary": Slot(value="singapore_family_package_v1", confidence=0.95, authority_level="explicit_user"),
                "traveler_details": Slot(
                    value=[
                        {"name": "Rajesh Kumar", "dob": "1985-06-15", "passport": "A1234567"},
                        {"name": "Priya Kumar", "dob": "1988-09-22", "passport": "A7654321"},
                        {"name": "Aryan Kumar", "dob": "2015-03-10", "passport": "A1112223"},
                    ],
                    confidence=0.95,
                    authority_level="explicit_user"
                ),
                "payment_method": Slot(value="credit_card", confidence=0.95, authority_level="explicit_user"),
            }
        )

    # =========================================================================
    # CATEGORY E: Edge Cases (5 scenarios)
    # =========================================================================
    
    @classmethod
    def edge_null_values(cls) -> CanonicalPacket:
        """E1: Null values in slots."""
        return CanonicalPacket(
            packet_id="pkt_null_values",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value=None, confidence=0.0, authority_level="unknown"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value=None, confidence=0.0, authority_level="unknown"),
                "traveler_count": Slot(value=None, confidence=0.0, authority_level="unknown"),
            }
        )
    
    @classmethod
    def edge_empty_strings(cls) -> CanonicalPacket:
        """E2: Empty string values."""
        return CanonicalPacket(
            packet_id="pkt_empty_strings",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="", confidence=0.1, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="", confidence=0.1, authority_level="explicit_user"),
                "traveler_count": Slot(value="", confidence=0.1, authority_level="explicit_user"),
            }
        )
    
    @classmethod
    def edge_zero_confidence(cls) -> CanonicalPacket:
        """E3: Zero confidence facts."""
        return CanonicalPacket(
            packet_id="pkt_zero_confidence",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.0, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.0, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15", confidence=0.0, authority_level="explicit_user"),
                "traveler_count": Slot(value=2, confidence=0.0, authority_level="explicit_user"),
            }
        )
    
    @classmethod
    def edge_duplicate_layers(cls) -> CanonicalPacket:
        """E4: Same field in facts, derived, and hypotheses."""
        return CanonicalPacket(
            packet_id="pkt_duplicate_layers",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.95, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            },
            derived_signals={
                "destination_city": Slot(value="Thailand", confidence=0.70, authority_level="derived_signal"),
            },
            hypotheses={
                "destination_city": Slot(value="Bali", confidence=0.50, authority_level="soft_hypothesis"),
            }
        )
    
    @classmethod
    def edge_unknown_stage(cls) -> CanonicalPacket:
        """E5: Unknown stage defaults to discovery."""
        return CanonicalPacket(
            packet_id="pkt_unknown_stage",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="unknown_stage",  # Invalid stage
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
            }
        )

    # =========================================================================
    # CATEGORY F: Complex Hybrid (5 scenarios)
    # =========================================================================
    
    @classmethod
    def hybrid_multi_source(cls) -> CanonicalPacket:
        """F1: Multi-source same field with different excerpts."""
        return CanonicalPacket(
            packet_id="pkt_multi_source",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(
                    value="Singapore",
                    confidence=0.85,
                    authority_level="explicit_user",
                    evidence_refs=[
                        EvidenceRef(ref_id="r1", envelope_id="env_email", evidence_type="text_span", excerpt="SG"),
                        EvidenceRef(ref_id="r2", envelope_id="env_chat", evidence_type="text_span", excerpt="Singapore"),
                    ]
                ),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            },
            contradictions=[{
                "field_name": "destination_city",
                "values": ["SG", "Singapore"],
                "sources": ["env_email", "env_chat"],
                "type": "multi_source_conflict"
            }]
        )
    
    @classmethod
    def hybrid_normalized(cls) -> CanonicalPacket:
        """F2: Normalized city codes (blr → Bangalore)."""
        return CanonicalPacket(
            packet_id="pkt_normalized",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.90, authority_level="explicit_user"),
                "origin_city": Slot(
                    value="Bangalore",  # Normalized from "blr"
                    confidence=0.90,
                    authority_level="imported_structured",
                    extraction_mode="normalized",
                    evidence_refs=[
                        EvidenceRef(ref_id="r1", envelope_id="env_form", evidence_type="structured_field", excerpt="blr")
                    ]
                ),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            }
        )
    
    @classmethod
    def hybrid_cross_layer(cls) -> CanonicalPacket:
        """F3: Fact contradicts derived signal."""
        return CanonicalPacket(
            packet_id="pkt_cross_layer",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.95, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.90, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.90, authority_level="explicit_user"),
            },
            derived_signals={
                "destination_city": Slot(value="Thailand", confidence=0.70, authority_level="derived_signal"),
            }
        )
    
    @classmethod
    def hybrid_confidence_boundary(cls) -> CanonicalPacket:
        """F4: Confidence exactly at threshold boundary."""
        return CanonicalPacket(
            packet_id="pkt_confidence_boundary",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.60, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.60, authority_level="explicit_user"),
                "travel_dates": Slot(value="March 2026", confidence=0.60, authority_level="explicit_user"),
                "traveler_count": Slot(value=2, confidence=0.60, authority_level="explicit_user"),
            }
        )
    
    @classmethod
    def hybrid_all_layers(cls) -> CanonicalPacket:
        """F5: Facts, derived, hypotheses, and unknowns all present."""
        return CanonicalPacket(
            packet_id="pkt_all_layers",
            created_at=cls._now(),
            last_updated=cls._now(),
            stage="discovery",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.95, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.90, authority_level="explicit_user"),
            },
            derived_signals={
                "travel_dates": Slot(value="2026-03-15 to 2026-03-22", confidence=0.75, authority_level="derived_signal"),
            },
            hypotheses={
                "traveler_count": Slot(value=4, confidence=0.50, authority_level="soft_hypothesis"),
            },
            unknowns=[
                UnknownField(field_name="budget_range", reason="not_present_in_source"),
            ]
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    @classmethod
    def get_all(cls) -> Dict[str, CanonicalPacket]:
        """Return all 30 test scenarios as a dictionary."""
        return {
            # Category A: Basic Flows
            "basic_empty": cls.basic_empty(),
            "basic_complete_discovery": cls.basic_complete_discovery(),
            "basic_hypothesis_only": cls.basic_hypothesis_only(),
            "basic_derived_fills": cls.basic_derived_fills(),
            "basic_soft_only": cls.basic_soft_only(),
            "basic_minimal_safe": cls.basic_minimal_safe(),
            
            # Category B: Contradictions
            "contradiction_date_critical": cls.contradiction_date_critical(),
            "contradiction_budget_branch": cls.contradiction_budget_branch(),
            "contradiction_destination_ask": cls.contradiction_destination_ask(),
            "contradiction_count_ask": cls.contradiction_count_ask(),
            "contradiction_origin_ask": cls.contradiction_origin_ask(),
            
            # Category C: Authority Tests
            "authority_manual_override": cls.authority_manual_override(),
            "authority_owner_vs_imported": cls.authority_owner_vs_imported(),
            "authority_derived_vs_hypothesis": cls.authority_derived_vs_hypothesis(),
            "authority_explicit_user_high": cls.authority_explicit_user_high(),
            "authority_unknown_rejected": cls.authority_unknown_rejected(),
            
            # Category D: Stage Progression
            "stage_discovery_to_shortlist": cls.stage_discovery_to_shortlist(),
            "stage_shortlist_to_proposal": cls.stage_shortlist_to_proposal(),
            "stage_proposal_to_booking": cls.stage_proposal_to_booking(),
            "stage_booking_complete": cls.stage_booking_complete(),
            
            # Category E: Edge Cases
            "edge_null_values": cls.edge_null_values(),
            "edge_empty_strings": cls.edge_empty_strings(),
            "edge_zero_confidence": cls.edge_zero_confidence(),
            "edge_duplicate_layers": cls.edge_duplicate_layers(),
            "edge_unknown_stage": cls.edge_unknown_stage(),
            
            # Category F: Complex Hybrid
            "hybrid_multi_source": cls.hybrid_multi_source(),
            "hybrid_normalized": cls.hybrid_normalized(),
            "hybrid_cross_layer": cls.hybrid_cross_layer(),
            "hybrid_confidence_boundary": cls.hybrid_confidence_boundary(),
            "hybrid_all_layers": cls.hybrid_all_layers(),
        }
    
    @classmethod
    def get_by_category(cls, category: str) -> Dict[str, CanonicalPacket]:
        """Get scenarios by category.
        
        Categories: basic, contradiction, authority, stage, edge, hybrid
        """
        all_scenarios = cls.get_all()
        prefix_map = {
            "basic": "basic_",
            "contradiction": "contradiction_",
            "authority": "authority_",
            "stage": "stage_",
            "edge": "edge_",
            "hybrid": "hybrid_",
        }
        prefix = prefix_map.get(category, "")
        return {k: v for k, v in all_scenarios.items() if k.startswith(prefix)}
    
    @classmethod
    def get_expected_results(cls) -> Dict[str, Dict[str, Any]]:
        """Return expected decision states for each scenario."""
        return {
            # Basic Flows
            "basic_empty": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 4},
            "basic_complete_discovery": {"decision_state": "PROCEED_TRAVELER_SAFE", "hard_blockers": 0},
            "basic_hypothesis_only": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 3},
            "basic_derived_fills": {"decision_state": "PROCEED_INTERNAL_DRAFT", "hard_blockers": 0},
            "basic_soft_only": {"decision_state": "PROCEED_INTERNAL_DRAFT", "hard_blockers": 0},
            "basic_minimal_safe": {"decision_state": "PROCEED_TRAVELER_SAFE", "hard_blockers": 0},
            
            # Contradictions
            "contradiction_date_critical": {"decision_state": "STOP_NEEDS_REVIEW", "has_contradictions": True},
            "contradiction_budget_branch": {"decision_state": "BRANCH_OPTIONS", "has_contradictions": True},
            "contradiction_destination_ask": {"decision_state": "ASK_FOLLOWUP", "has_contradictions": True},
            "contradiction_count_ask": {"decision_state": "ASK_FOLLOWUP", "has_contradictions": True},
            "contradiction_origin_ask": {"decision_state": "ASK_FOLLOWUP", "has_contradictions": True},
            
            # Authority Tests
            "authority_manual_override": {"decision_state": "PROCEED_TRAVELER_SAFE", "hard_blockers": 0},
            "authority_owner_vs_imported": {"decision_state": "ASK_FOLLOWUP", "has_contradictions": True},
            "authority_derived_vs_hypothesis": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 1},
            "authority_explicit_user_high": {"decision_state": "PROCEED_TRAVELER_SAFE", "hard_blockers": 0},
            "authority_unknown_rejected": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 3},
            
            # Stage Progression
            "stage_discovery_to_shortlist": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 1},
            "stage_shortlist_to_proposal": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 1},
            "stage_proposal_to_booking": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 2},
            "stage_booking_complete": {"decision_state": "PROCEED_TRAVELER_SAFE", "hard_blockers": 0},
            
            # Edge Cases
            "edge_null_values": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 3},
            "edge_empty_strings": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 3},
            "edge_zero_confidence": {"decision_state": "PROCEED_INTERNAL_DRAFT", "hard_blockers": 0},
            "edge_duplicate_layers": {"decision_state": "PROCEED_INTERNAL_DRAFT", "hard_blockers": 0},
            "edge_unknown_stage": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 2},
            
            # Complex Hybrid
            "hybrid_multi_source": {"decision_state": "PROCEED_INTERNAL_DRAFT", "has_contradictions": True},
            "hybrid_normalized": {"decision_state": "PROCEED_TRAVELER_SAFE", "hard_blockers": 0},
            "hybrid_cross_layer": {"decision_state": "PROCEED_TRAVELER_SAFE", "hard_blockers": 0},
            "hybrid_confidence_boundary": {"decision_state": "PROCEED_INTERNAL_DRAFT", "hard_blockers": 0},
            "hybrid_all_layers": {"decision_state": "ASK_FOLLOWUP", "hard_blockers": 1},
        }


# Simple test runner
def run_tests():
    """Run all test scenarios and print results."""
    print("=" * 80)
    print("TEST SCENARIOS VALIDATION")
    print("=" * 80)
    
    scenarios = TestScenarios.get_all()
    expected = TestScenarios.get_expected_results()
    
    print(f"\nTotal scenarios: {len(scenarios)}\n")
    
    for name, packet in scenarios.items():
        exp = expected.get(name, {})
        print(f"✓ {name}")
        print(f"  Stage: {packet.stage}")
        print(f"  Facts: {len(packet.facts)}, Derived: {len(packet.derived_signals)}, Hypotheses: {len(packet.hypotheses)}")
        print(f"  Expected: {exp.get('decision_state', 'UNKNOWN')}")
        if 'hard_blockers' in exp:
            print(f"  Expected hard blockers: {exp['hard_blockers']}")
        if exp.get('has_contradictions'):
            print(f"  Has contradictions: {len(packet.contradictions)}")
        print()
    
    print("=" * 80)
    print("All scenarios defined successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
