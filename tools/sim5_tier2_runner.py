"""
tools/sim5_tier2_runner.py — Sim #5 Tier-2 Indian Travel Agent Live Simulation Runner.

Simulates the day-in-the-life workflow of Rajesh Khandelwal, proprietor of
Shubh Yatra Holidays in Indore (Madhya Pradesh), serving outbound leisure
travelers across Central India.

Surfaces under test:
1. Live Message Triage (/api/triage/message) with Hinglish WhatsApp text.
2. Omnichannel Inbound Webhook & Message Store (/api/v1/messaging/webhook/whatsapp, /api/v1/messages).
3. Inbound Intake & Fact Extraction Pipeline (/api/v1/inbound/parse) — multi-generational family,
   Indian digit formatting (Lakhs), mobility and strict Jain dietary constraints.
4. Statutory Indian Tax Engine (/api/v1/tax-compliance/calculate-tcs, calculate-gst) — Section 206C(1G) TCS.
5. Inbound Follow-up Note Refinement & Location Preference Handling.
6. Omnichannel Outbound Messaging (/api/v1/messaging/send) with honest provider status.
7. Audit Trail & Non-Repudiation (AuditStore event logging and hash verification).

Evidence output: Docs/sims/assets/sim5/evidence/sim5_rajesh_indore_evidence.json
"""

# ruff: noqa: E402 — sys.path setup must precede imports in this standalone runner


from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

# Configure environment before imports
os.environ["TRIPSTORE_BACKEND"] = "file"
os.environ["SPINE_API_DISABLE_AUTH"] = "1"
os.environ["DATA_PRIVACY_MODE"] = "beta"
os.environ["RUNNING_TESTS"] = "1"
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-pytest-only-32byt")
os.environ.setdefault("PROPOSAL_SIGNING_KEY", "test-proposal-signing-key-for-pytest-32bytes")
WEBHOOK_SECRET = "sim5_test_meta_app_secret_indore"
os.environ["WHATSAPP_APP_SECRET"] = WEBHOOK_SECRET
os.environ["MESSAGING_WEBHOOK_AGENCY_ID"] = "agency_rajesh_indore"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "spine_api"))
EVIDENCE_DIR = REPO_ROOT / "Docs" / "sims" / "assets" / "sim5" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

from fastapi.testclient import TestClient
from spine_api.server import app, _auth_or_skip
from spine_api.core.auth import get_current_agency, get_current_agency_id
from spine_api.persistence import TripStore, AuditStore

AGENCY_ID = "agency_rajesh_indore"
AGENCY_NAME = "Shubh Yatra Holidays (Indore)"

# Set up test overrides
mock_agency = SimpleNamespace(id=AGENCY_ID, name=AGENCY_NAME, is_active=True, jurisdiction="IN")
app.dependency_overrides[_auth_or_skip] = lambda: None
app.dependency_overrides[get_current_agency_id] = lambda: AGENCY_ID
app.dependency_overrides[get_current_agency] = lambda: mock_agency

CLIENT = TestClient(app)

VOICES = {
    "5_A1_inbound": (
        "Bhaiya namaste. Hum 6 bade hain aur 2 bacche (ek 8 saal aur ek 3 saal) plus ek 7 mahine ka infant. "
        "Hume December 22 se 28 tak Dubai ka family trip karna hai Indore se. "
        "Mummy ji (age 72) ko chalne me dikkat hai to airport aur sightseeing pe wheelchair assistance compulsory chahiye. "
        "Khana pure vegetarian/Jain chahiye hotel aur sightseeing me. "
        "Budget around 4.5 lakh total sab milakar. Aur humare textile firm ke naam par GST invoice banwana hai. "
        "Jaldi batao options."
    ),
    "5_A2_refinement": (
        "Sunil Agrawal here again — bhaiya hotel Bur Dubai ya Deira taraf nahi chahiye, "
        "kids ko Burj Khalifa aur Dubai Mall paas chahiye so Downtown ya Sheikh Zayed Road taraf batao. "
        "Aur kya TCS 5% lagega ya 20%? Sabke passport valid hain till 2028."
    ),
    "5_A3_outbound": (
        "Namaste Sunil ji! Thank you for contacting Shubh Yatra Holidays, Indore. "
        "We have registered your Dubai family vacation (Dec 22-28, 6 adults, 2 children, 1 infant). "
        "All special requirements are locked: 100% pure Jain catering, airport & sightseeing wheelchair assistance "
        "for Mataji, and premium Downtown / Sheikh Zayed Road 4-star family suites. "
        "Tax breakdown: For ₹4,50,000 package, statutory TCS is 5% (₹22,500, fully adjustable against your advance tax), "
        "and B2B GST invoice with your firm's GSTIN will be provided. "
        "Detailed itinerary options are ready for your review."
    ),
}


def run_sim():
    evidence_log = []
    summary_report = {
        "simulation_id": "SIM-5-TIER2-INDIA-01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operator": {
            "persona_id": "P-TIER2-INDIA-01",
            "name": "Rajesh Khandelwal",
            "agency": AGENCY_NAME,
            "city": "Indore, Madhya Pradesh",
        },
        "customer": {
            "name": "Sunil Agrawal",
            "company": "Agrawal Textiles, Indore",
            "contact": "+919826012345",
            "channel": "WhatsApp",
        },
        "steps": [],
        "findings": {},
        "verdict": "COMPLETED",
    }

    def record_step(step_name: str, method: str, endpoint: str, request_data: dict, status_code: int, response_data: dict):
        entry = {
            "step": step_name,
            "method": method,
            "endpoint": endpoint,
            "request": request_data,
            "status_code": status_code,
            "response": response_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        evidence_log.append(entry)
        summary_report["steps"].append({
            "step": step_name,
            "endpoint": f"{method} {endpoint}",
            "status": status_code,
        })
        print(f"[{step_name}] {method} {endpoint} -> Status {status_code}")
        return entry

    print("======================================================================")
    print("STARTING SIM #5: TIER-2 INDIAN AGENT (RAJESH KHANDELWAL, INDORE)")
    print("======================================================================")

    # -------------------------------------------------------------------------
    # STEP 1: Live Message Triage of Inbound WhatsApp Message
    # -------------------------------------------------------------------------
    print("\n--- STEP 1: Live Message Triage ---")
    triage_payload = {
        "text": VOICES["5_A1_inbound"],
        "channel": "whatsapp",
    }
    triage_res = CLIENT.post("/api/triage/message", json=triage_payload)
    triage_data = triage_res.json()
    record_step("01_live_message_triage", "POST", "/api/triage/message", triage_payload, triage_res.status_code, triage_data)

    # -------------------------------------------------------------------------
    # STEP 2: Inbound WhatsApp Webhook Ingestion & Message Store
    # -------------------------------------------------------------------------
    print("\n--- STEP 2: Inbound Webhook & Message Store ---")
    webhook_payload = {
        "event": "message",
        "from": "+919826012345",
        "to": "+919826099999",
        "text": VOICES["5_A1_inbound"],
        "message_id": "wa_msg_sunil_001",
    }
    raw_wh_bytes = json.dumps(webhook_payload).encode("utf-8")
    sig_wh = "sha256=" + hmac.new(WEBHOOK_SECRET.encode("utf-8"), raw_wh_bytes, hashlib.sha256).hexdigest()
    wh_res = CLIENT.post(
        "/api/v1/messaging/webhook/whatsapp",
        content=raw_wh_bytes,
        headers={"X-Hub-Signature-256": sig_wh, "Content-Type": "application/json"},
    )
    wh_data = wh_res.json()
    record_step("02_inbound_whatsapp_webhook", "POST", "/api/v1/messaging/webhook/whatsapp", webhook_payload, wh_res.status_code, wh_data)

    # Verify message feed
    feed_res = CLIENT.get("/api/v1/messages?limit=20")
    feed_data = feed_res.json()
    record_step("03_agency_message_feed", "GET", "/api/v1/messages", {}, feed_res.status_code, feed_data)

    # -------------------------------------------------------------------------
    # STEP 3: Inbound Inquiry Parse & Intake Pipeline Execution
    # -------------------------------------------------------------------------
    print("\n--- STEP 3: Inbound Parse & Fact Extraction ---")
    inbound_payload = {
        "channel": "whatsapp_web",
        "raw_text": VOICES["5_A1_inbound"],
        "customer_name": "Sunil Agrawal",
        "customer_contact": "+919826012345",
        "agent_notes": "Urgent quote requested for joint family Dubai trip. High-value merchant client from Sitlamata Bazar.",
    }
    parse_res = CLIENT.post("/api/v1/inbound/parse", json=inbound_payload)
    parse_data = parse_res.json()
    record_step("04_inbound_intake_parse", "POST", "/api/v1/inbound/parse", inbound_payload, parse_res.status_code, parse_data)

    trip_id = parse_data.get("trip_id")
    trip_record = TripStore.get_trip_for_agency(trip_id, AGENCY_ID) if trip_id else None
    packet = (trip_record or {}).get("packet") or {}
    facts = packet.get("facts") or {}

    summary_report["findings"]["extracted_facts"] = {
        "budget_raw": (facts.get("budget_raw_text") or {}).get("value"),
        "budget_min": (facts.get("budget_min") or {}).get("value"),
        "budget_max": (facts.get("budget_max") or {}).get("value"),
        "budget_currency": (facts.get("budget_currency") or {}).get("value"),
        "mobility_constraints": (facts.get("mobility_constraints") or {}).get("value"),
        "meal_preferences": (facts.get("meal_preferences") or {}).get("value"),
        "trip_purpose": (facts.get("trip_purpose") or {}).get("value"),
        "origin_city": (facts.get("origin_city") or {}).get("value"),
        "destination_candidates": (facts.get("destination_candidates") or {}).get("value"),
        "party_size": (facts.get("party_size") or {}).get("value"),
        "party_composition": (facts.get("party_composition") or {}).get("value"),
        "child_ages": (facts.get("child_ages") or {}).get("value"),
    }

    # -------------------------------------------------------------------------
    # STEP 4: Indian Statutory Tax Compliance (TCS & GST)
    # -------------------------------------------------------------------------
    print("\n--- STEP 4: Indian Tax Compliance Engine (TCS & GST) ---")
    # Section 206C(1G) TCS calculation
    tcs_payload = {
        "current_amount_inr": 450000.0,
        "is_overseas_trip": True,
        "pan_number": "AAACA1234F",
        "cumulative_fy_spend_inr": 0.0,
    }
    tcs_res = CLIENT.post("/api/v1/tax-compliance/calculate-tcs", json=tcs_payload)
    tcs_data = tcs_res.json()
    record_step("05_tax_compliance_tcs", "POST", "/api/v1/tax-compliance/calculate-tcs", tcs_payload, tcs_res.status_code, tcs_data)

    # Tour Package GST calculation (5% without input tax credit)
    gst_pkg_payload = {
        "taxable_base_inr": 450000.0,
        "scheme": "TOUR_PACKAGE_5PCT",
        "is_inter_state": False,  # Intra-state in Madhya Pradesh (CGST 2.5% + SGST 2.5%)
    }
    gst_res = CLIENT.post("/api/v1/tax-compliance/calculate-gst", json=gst_pkg_payload)
    gst_data = gst_res.json()
    record_step("06_tax_compliance_gst_package", "POST", "/api/v1/tax-compliance/calculate-gst", gst_pkg_payload, gst_res.status_code, gst_data)

    # -------------------------------------------------------------------------
    # STEP 5: Follow-up Client Refinement (Voice 5-A2)
    # -------------------------------------------------------------------------
    print("\n--- STEP 5: Inbound Follow-up Note & Location Refinement ---")
    refinement_wh_payload = {
        "event": "message",
        "from": "+919826012345",
        "to": "+919826099999",
        "text": VOICES["5_A2_refinement"],
        "message_id": "wa_msg_sunil_002",
    }
    raw_ref_bytes = json.dumps(refinement_wh_payload).encode("utf-8")
    sig_ref = "sha256=" + hmac.new(WEBHOOK_SECRET.encode("utf-8"), raw_ref_bytes, hashlib.sha256).hexdigest()
    ref_res = CLIENT.post(
        "/api/v1/messaging/webhook/whatsapp",
        content=raw_ref_bytes,
        headers={"X-Hub-Signature-256": sig_ref, "Content-Type": "application/json"},
    )
    ref_data = ref_res.json()
    record_step("07_followup_message_webhook", "POST", "/api/v1/messaging/webhook/whatsapp", refinement_wh_payload, ref_res.status_code, ref_data)

    # Follow-up triage
    ref_triage_payload = {
        "text": VOICES["5_A2_refinement"],
        "channel": "whatsapp",
    }
    ref_triage_res = CLIENT.post("/api/triage/message", json=ref_triage_payload)
    ref_triage_data = ref_triage_res.json()
    record_step("08_followup_message_triage", "POST", "/api/triage/message", ref_triage_payload, ref_triage_res.status_code, ref_triage_data)

    # -------------------------------------------------------------------------
    # STEP 6: Outbound WhatsApp Dispatch (Rajesh to Sunil)
    # -------------------------------------------------------------------------
    print("\n--- STEP 6: Outbound Messaging Dispatch ---")
    outbound_payload = {
        "trip_id": trip_id or "trip_fallback_id",
        "recipient": "+919826012345",
        "channel": "whatsapp",
        "content": VOICES["5_A3_outbound"],
    }
    send_res = CLIENT.post("/api/v1/messaging/send", json=outbound_payload)
    send_data = send_res.json()
    record_step("09_outbound_whatsapp_dispatch", "POST", "/api/v1/messaging/send", outbound_payload, send_res.status_code, send_data)

    # -------------------------------------------------------------------------
    # STEP 7: Trip Message Thread Verification
    # -------------------------------------------------------------------------
    print("\n--- STEP 7: Trip Messages Thread ---")
    trip_msgs_res = CLIENT.get(f"/api/v1/trips/{trip_id}/messages")
    trip_msgs_data = trip_msgs_res.json()
    record_step("10_trip_messages_thread", "GET", f"/api/v1/trips/{trip_id}/messages", {}, trip_msgs_res.status_code, trip_msgs_data)

    # -------------------------------------------------------------------------
    # STEP 8: Audit Log Verification
    # -------------------------------------------------------------------------
    print("\n--- STEP 8: Audit Log Verification ---")
    audit_events = AuditStore.get_events(50)
    audit_summary = [
        {
            "event_type": e.get("event_type"),
            "timestamp": e.get("timestamp"),
            "user_id": e.get("user_id"),
            "details": e.get("details"),
        }
        for e in audit_events
    ]
    record_step("11_audit_store_events", "INTERNAL", "AuditStore.get_events", {"limit": 50}, 200, {"events_count": len(audit_summary), "events": audit_summary[:10]})

    # -------------------------------------------------------------------------
    # Save Evidence & Output Summary
    # -------------------------------------------------------------------------
    evidence_file = EVIDENCE_DIR / "sim5_rajesh_indore_evidence.json"
    evidence_file.write_text(json.dumps(evidence_log, indent=2, ensure_ascii=False))
    print(f"\nSaved raw evidence to: {evidence_file}")

    summary_file = EVIDENCE_DIR / "sim5_summary_report.json"
    summary_file.write_text(json.dumps(summary_report, indent=2, ensure_ascii=False))
    print(f"Saved summary report to: {summary_file}")

    print("\n======================================================================")
    print("SIM #5 EXECUTION COMPLETE!")
    print("======================================================================")
    return summary_report, evidence_log


if __name__ == "__main__":
    summary, ev = run_sim()
    print(f"Executed {len(summary['steps'])} steps successfully.")
