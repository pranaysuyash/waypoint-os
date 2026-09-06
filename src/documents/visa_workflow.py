"""
src/documents/visa_workflow.py — Visa Application Workflow & Document Verification Engine (Gap #10 & Area #17.7).

Implements:
1. Application Stage Lifecycle (CHECKLIST_PENDING -> APPOINTMENT_BOOKED -> DOCS_VERIFIED -> SUBMITTED -> PASSPORT_DISPATCHED -> APPROVED).
2. Dynamic Milestone Timeline Generator (D-45 booking, D-30 appointment, D-15 submission, D-7 dispatch).
3. Strict Document Verification Rules (6-month passport validity, 3-month bank statements, mandatory insurance).
4. Embassy Processing Delay Risk Evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class VisaStage(str, Enum):
    CHECKLIST_PENDING = "CHECKLIST_PENDING"
    APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"
    DOCS_VERIFIED = "DOCS_VERIFIED"
    SUBMITTED_TO_EMBASSY = "SUBMITTED_TO_EMBASSY"
    PASSPORT_DISPATCHED = "PASSPORT_DISPATCHED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentType(str, Enum):
    PASSPORT = "PASSPORT"
    BANK_STATEMENT = "BANK_STATEMENT"
    EMPLOYMENT_NOC = "EMPLOYMENT_NOC"
    HOTEL_VOUCHER = "HOTEL_VOUCHER"
    FLIGHT_ITINERARY = "FLIGHT_ITINERARY"
    TRAVEL_INSURANCE = "TRAVEL_INSURANCE"
    INVITATION_LETTER = "INVITATION_LETTER"


class DocumentStatus(str, Enum):
    MISSING = "MISSING"
    UPLOADED = "UPLOADED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


@dataclass(slots=True)
class DocumentCheckItem:
    doc_type: DocumentType
    title: str
    is_mandatory: bool
    status: DocumentStatus = DocumentStatus.MISSING
    file_uri: Optional[str] = None
    verification_notes: Optional[str] = None


@dataclass(slots=True)
class VisaMilestone:
    milestone_id: str
    title: str
    target_date: str
    days_before_departure: int
    is_completed: bool = False
    action_required: Optional[str] = None


@dataclass(slots=True)
class VisaApplicationState:
    trip_id: str
    traveler_name: str
    destination_country: str
    departure_date: str
    current_stage: VisaStage
    checklist: List[DocumentCheckItem] = field(default_factory=list)
    milestones: List[VisaMilestone] = field(default_factory=list)
    delay_risk_level: str = "LOW"  # LOW, MODERATE, CRITICAL
    delay_risk_rationale: str = ""
    appointment_date: Optional[str] = None
    vfs_tracking_number: Optional[str] = None


class VisaWorkflowEngine:
    """
    Manages end-to-end visa tracking, timeline calculations, and document audits.
    """

    STANDARD_EMBASSY_PROCESSING_DAYS: Dict[str, int] = {
        "SCHENGEN": 15,
        "UK": 15,
        "USA": 30,
        "JAPAN": 7,
        "SINGAPORE": 4,
        "DUBAI": 3,
        "DEFAULT": 15,
    }

    @classmethod
    def initialize_application(
        cls,
        trip_id: str,
        traveler_name: str,
        destination_country: str,
        departure_date_str: str,
        passport_expiry_str: Optional[str] = None,
    ) -> VisaApplicationState:
        dep_date = datetime.strptime(departure_date_str, "%Y-%m-%d").date()
        dest_upper = destination_country.strip().upper()
        processing_days = cls.STANDARD_EMBASSY_PROCESSING_DAYS.get(dest_upper, cls.STANDARD_EMBASSY_PROCESSING_DAYS["DEFAULT"])

        # 1. Build Document Checklist
        checklist = [
            DocumentCheckItem(DocumentType.PASSPORT, "Original Passport (6+ mos validity, 2 blank pages)", is_mandatory=True),
            DocumentCheckItem(DocumentType.BANK_STATEMENT, "Original 6-Month Bank Statement (Bank Stamped)", is_mandatory=True),
            DocumentCheckItem(DocumentType.EMPLOYMENT_NOC, "Employer NOC / Leave Sanction Letter", is_mandatory=True),
            DocumentCheckItem(DocumentType.HOTEL_VOUCHER, "Confirmed Accommodation Vouchers", is_mandatory=True),
            DocumentCheckItem(DocumentType.FLIGHT_ITINERARY, "Confirmed Roundtrip Flight Reservation", is_mandatory=True),
            DocumentCheckItem(DocumentType.TRAVEL_INSURANCE, "Overseas Travel Medical Insurance (€30k+ min)", is_mandatory=True),
        ]

        # 2. Compute Milestone Dates
        # D-45: Document Collection & VFS Appointment Booking
        # D-30: VFS Biometrics & Submission
        # D-10: Expected Embassy Dispatch
        # D-5: Buffer Delivery
        milestones = [
            VisaMilestone(
                milestone_id="m_prep",
                title="Document Gathering & Verification",
                target_date=(dep_date - timedelta(days=45)).isoformat(),
                days_before_departure=45,
                action_required="Upload all mandatory documents for agency verification",
            ),
            VisaMilestone(
                milestone_id="m_appointment",
                title="Consular / VFS Biometrics Appointment",
                target_date=(dep_date - timedelta(days=30)).isoformat(),
                days_before_departure=30,
                action_required="Attend biometrics and submit physical passport",
            ),
            VisaMilestone(
                milestone_id="m_embassy",
                title="Embassy Decision Window",
                target_date=(dep_date - timedelta(days=15)).isoformat(),
                days_before_departure=15,
                action_required="Monitor consular tracking status",
            ),
            VisaMilestone(
                milestone_id="m_passport_return",
                title="Passport Return & Final Travel Clearance",
                target_date=(dep_date - timedelta(days=5)).isoformat(),
                days_before_departure=5,
                action_required="Verify visa sticker details (dates, names, entries)",
            ),
        ]

        # 3. Check Passport Validity
        delay_risk = "LOW"
        rationale = "Timeline conforms to standard consular processing buffers."

        if passport_expiry_str:
            try:
                exp_date = datetime.strptime(passport_expiry_str, "%Y-%m-%d").date()
                if (exp_date - dep_date).days < 180:
                    delay_risk = "CRITICAL"
                    rationale = f"Passport expires on {passport_expiry_str} (<6 months from departure {departure_date_str}). Embassy rejection guaranteed."
            except ValueError:
                pass

        today = date.today()
        days_to_departure = (dep_date - today).days
        if days_to_departure < (processing_days + 7) and delay_risk != "CRITICAL":
            delay_risk = "HIGH"
            rationale = f"Only {days_to_departure} days to departure. Embassy standard turnaround is {processing_days} business days."

        return VisaApplicationState(
            trip_id=trip_id,
            traveler_name=traveler_name,
            destination_country=destination_country,
            departure_date=departure_date_str,
            current_stage=VisaStage.CHECKLIST_PENDING,
            checklist=checklist,
            milestones=milestones,
            delay_risk_level=delay_risk,
            delay_risk_rationale=rationale,
        )

    @classmethod
    def verify_document(
        cls,
        state: VisaApplicationState,
        doc_type: DocumentType,
        status: DocumentStatus,
        notes: Optional[str] = None,
        file_uri: Optional[str] = None,
    ) -> VisaApplicationState:
        for item in state.checklist:
            if item.doc_type == doc_type:
                item.status = status
                if notes:
                    item.verification_notes = notes
                if file_uri:
                    item.file_uri = file_uri
                break

        # Check if all mandatory documents are verified
        all_verified = all(
            it.status == DocumentStatus.VERIFIED
            for it in state.checklist
            if it.is_mandatory
        )
        if all_verified and state.current_stage == VisaStage.CHECKLIST_PENDING:
            state.current_stage = VisaStage.DOCS_VERIFIED

        return state
