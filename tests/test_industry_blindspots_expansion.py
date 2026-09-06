"""
Unit and API tests for Industry Expansion & Gap Closures:
1. Corporate Travel Policy & Approval Hierarchy (Area #17.15)
2. Visa Application Workflow & Document Checklist (Gap #10 & Area #17.7)
3. Pre-Departure Automated Briefing Cadence (Area #17.8)
4. Accounting System Export Bridge (Area #17.19)
"""


from src.corporate.policy_engine import (
    ApprovalState,
    CabinClass,
    CorporatePolicyEngine,
    EmployeeTier,
)
from src.documents.visa_workflow import (
    DocumentStatus,
    VisaStage,
    VisaWorkflowEngine,
)
from src.briefing.pre_departure_cadence import (
    CadenceStage,
    PreDepartureCadenceEngine,
)
from src.accounting.export_bridge import AccountingExportBridge
from src.fees.tax_compliance import (
    GSTTaxScheme,
    SourcingChannel,
    SourcingLineItem,
    TaxComplianceEngine,
)


# ---------------------------------------------------------------------------
# 1. Corporate Travel Policy Engine Tests
# ---------------------------------------------------------------------------

def test_corporate_policy_compliant_standard():
    """Verify that within-policy standard itinerary is auto-approved."""
    result = CorporatePolicyEngine.audit_itinerary(
        trip_id="corp_trip_1",
        employee_tier=EmployeeTier.STANDARD,
        flight_duration_hours=5.0,
        requested_cabin_class=CabinClass.PREMIUM_ECONOMY,
        nightly_hotel_rate_usd=200.0,
        destination_city="Berlin",
        days_in_advance=21,
        total_trip_budget_usd=2500.0,
    )
    assert result.is_compliant is True
    assert result.approval_state == ApprovalState.AUTO_APPROVED
    assert len(result.violations) == 0


def test_corporate_policy_cabin_exceeded():
    """Verify that requesting Business for short flight requires Director approval."""
    result = CorporatePolicyEngine.audit_itinerary(
        trip_id="corp_trip_2",
        employee_tier=EmployeeTier.STANDARD,
        flight_duration_hours=3.0,
        requested_cabin_class=CabinClass.BUSINESS,
        nightly_hotel_rate_usd=180.0,
        destination_city="Rome",
        days_in_advance=15,
        total_trip_budget_usd=2000.0,
    )
    assert result.is_compliant is False
    assert result.approval_state == ApprovalState.PENDING_DIRECTOR
    assert any(v.rule_code == "CABIN_CLASS_EXCEEDED" for v in result.violations)
    assert "DIRECTOR" in result.escalation_chain


def test_corporate_policy_high_value_finance_escalation():
    """Verify budget > $5,000 escalates to Finance VP."""
    result = CorporatePolicyEngine.audit_itinerary(
        trip_id="corp_trip_3",
        employee_tier=EmployeeTier.SENIOR_MGMT,
        flight_duration_hours=10.0,
        requested_cabin_class=CabinClass.BUSINESS,
        nightly_hotel_rate_usd=300.0,
        destination_city="London",
        days_in_advance=30,
        total_trip_budget_usd=7500.0,
    )
    assert result.is_compliant is False
    assert result.approval_state == ApprovalState.PENDING_FINANCE
    assert any(v.rule_code == "HIGH_VALUE_BUDGET_CAP" for v in result.violations)
    assert "FINANCE_VP" in result.escalation_chain


# ---------------------------------------------------------------------------
# 2. Visa Workflow & Document Verification Tests
# ---------------------------------------------------------------------------

def test_visa_workflow_initialization_and_milestones():
    """Verify initialization builds document checklist and milestone dates."""
    state = VisaWorkflowEngine.initialize_application(
        trip_id="visa_trip_1",
        traveler_name="Alexander Wright",
        destination_country="SCHENGEN",
        departure_date_str="2026-10-15",
        passport_expiry_str="2027-08-20",
    )
    assert state.current_stage == VisaStage.CHECKLIST_PENDING
    assert len(state.checklist) == 6
    assert len(state.milestones) == 4
    assert state.delay_risk_level == "LOW"
    assert any(m.days_before_departure == 30 for m in state.milestones)


def test_visa_workflow_passport_expiry_critical_risk():
    """Verify critical risk when passport expires in <6 months from departure."""
    state = VisaWorkflowEngine.initialize_application(
        trip_id="visa_trip_2",
        traveler_name="Elena Rostova",
        destination_country="UK",
        departure_date_str="2026-10-15",
        passport_expiry_str="2026-12-01",  # Only 1.5 months validity
    )
    assert state.delay_risk_level == "CRITICAL"
    assert "rejection guaranteed" in state.delay_risk_rationale.lower()


def test_visa_document_verification_transition():
    """Verify stage transitions to DOCS_VERIFIED when all mandatory documents pass."""
    state = VisaWorkflowEngine.initialize_application(
        trip_id="visa_trip_3",
        traveler_name="Marcus Vance",
        destination_country="JAPAN",
        departure_date_str="2026-11-01",
    )
    for doc_item in state.checklist:
        VisaWorkflowEngine.verify_document(state, doc_item.doc_type, DocumentStatus.VERIFIED)

    assert state.current_stage == VisaStage.DOCS_VERIFIED


# ---------------------------------------------------------------------------
# 3. Pre-Departure Cadence & Briefing Packet Tests
# ---------------------------------------------------------------------------

def test_pre_departure_cadence_d_minus_7():
    """Verify D-7 briefing incorporates local currency, power voltage, and packing guide."""
    briefing = PreDepartureCadenceEngine.generate_briefing(
        trip_id="briefing_trip_1",
        traveler_name="Sophia Loren",
        departure_date="2026-09-08",
        destination_country_code="IT",
        stage=CadenceStage.D_MINUS_7,
        hotel_name="Hotel de Russie Rome",
    )
    assert briefing.stage == CadenceStage.D_MINUS_7
    assert "Italy" in briefing.destination
    assert "EUR" in briefing.formatted_message_body
    assert "Type C" in briefing.formatted_message_body
    assert len(briefing.action_items) >= 3


def test_pre_departure_cadence_d_minus_1_emergency_packet():
    """Verify D-1 briefing attaches emergency SOS contacts and flight verification."""
    briefing = PreDepartureCadenceEngine.generate_briefing(
        trip_id="briefing_trip_2",
        traveler_name="Kenji Sato",
        departure_date="2026-09-02",
        destination_country_code="JP",
        stage=CadenceStage.D_MINUS_1,
        flight_number="JL-001",
    )
    assert briefing.stage == CadenceStage.D_MINUS_1
    assert "110" in briefing.emergency_contacts["Local Emergency Police"]
    assert "Waypoint 24/7 SOS Concierge" in briefing.emergency_contacts
    assert "JL-001" in briefing.formatted_message_body


# ---------------------------------------------------------------------------
# 4. Accounting System Export Bridge Tests
# ---------------------------------------------------------------------------

def test_accounting_tally_xml_export():
    """Verify Tally XML sales voucher contains proper ledger tags and amounts."""
    items = [
        SourcingLineItem(
            item_id="item_fl_1",
            service_type="flight",
            title="Lufthansa Business BOM-FRA",
            supplier_name="Amadeus GDS",
            sourcing_channel=SourcingChannel.GDS_AMADEUS,
            currency="USD",
            supplier_net_amount=1500.0,
            fx_rate_to_inr=85.0,
            supplier_net_inr=0.0,
            agency_markup_pct=10.0,
            agency_markup_inr=0.0,
            gross_client_price_inr=0.0,
            gst_scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT,
        )
    ]
    invoice = TaxComplianceEngine.compile_commercial_invoice(
        trip_id="trip_tally_01",
        line_items=items,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
    )

    xml = AccountingExportBridge.export_tally_xml(
        invoice=invoice,
        customer_name="Stark Industries",
    )
    assert "<TALLYREQUEST>Import Data</TALLYREQUEST>" in xml
    assert "<VOUCHER VCHTYPE=\"Sales\" ACTION=\"Create\">" in xml
    assert "<LEDGERNAME>Stark Industries</LEDGERNAME>" in xml
    assert "<LEDGERNAME>Package Tour Sales</LEDGERNAME>" in xml
    assert "<LEDGERNAME>GST Output Payable</LEDGERNAME>" in xml
    assert "<LEDGERNAME>TCS Payable Sec 206C(1G)</LEDGERNAME>" in xml


def test_accounting_quickbooks_json_export():
    """Verify QuickBooks Online JSON invoice contains Line items and metadata."""
    items = [
        SourcingLineItem(
            item_id="item_ht_1",
            service_type="hotel",
            title="Aman Tokyo Deluxe Suite",
            supplier_name="Hotelbeds",
            sourcing_channel=SourcingChannel.BEDBANK_HOTELBEDS,
            currency="USD",
            supplier_net_amount=3000.0,
            fx_rate_to_inr=85.0,
            supplier_net_inr=0.0,
            agency_markup_pct=15.0,
            agency_markup_inr=0.0,
            gross_client_price_inr=0.0,
            gst_scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT,
        )
    ]
    invoice = TaxComplianceEngine.compile_commercial_invoice(
        trip_id="trip_qb_01",
        line_items=items,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
    )

    qb_json = AccountingExportBridge.export_quickbooks_json(
        invoice=invoice,
        customer_id="cust_999",
        customer_name="Wayne Enterprises",
    )
    assert qb_json["CustomerRef"]["value"] == "cust_999"
    assert qb_json["CustomerRef"]["name"] == "Wayne Enterprises"
    assert len(qb_json["Line"]) >= 1
    assert qb_json["TotalAmt"] == invoice.grand_total_payable_inr
    assert any(cf["Name"] == "TotalTCS" for cf in qb_json["CustomField"])
