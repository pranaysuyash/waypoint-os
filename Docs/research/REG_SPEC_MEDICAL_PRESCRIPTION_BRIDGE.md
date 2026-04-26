# Reg Spec: Cross-Border Medical-Prescription-Bridge (REG-REAL-011)

**Status**: Research/Draft
**Area**: Medical Interoperability & Traveler Safety

---

## 1. The Problem: "The Prescription Silo"
Travelers with chronic conditions often face a crisis if they lose or damage their primary medication abroad. Medical prescriptions are rarely interoperable across borders; a US prescription is invalid in Japan, and a German prescription may not be accepted in the UK. Finding the "Local-Equivalent" (which may have a different brand name but the same active ingredient) and a physician who can issue an emergency local prescription is a high-friction, high-risk process.

## 2. The Solution: 'Pharma-Interoperability-Protocol' (PIP)

The PIP allows the agent to act as a "Medical-Liaison."

### Medical Support Actions:

1.  **Generic-Active-Ingredient Mapping**:
    *   **Action**: Analyzing the traveler's "Home-Country" medication and identifying the **International-Nonproprietary-Name** (INN) and dosage of the active ingredient (e.g., "Sertraline 50mg").
2.  **Local-Brand Identification**:
    *   **Action**: Identifying the equivalent brand name available in the traveler's current "Host-Country" (e.g., "In the UK, Zoloft is often branded as Lustral").
3.  **Agent-Approved Emergency-Clinic Sourcing**:
    *   **Action**: Identifying the nearest 24h clinic or hospital that accepts international travelers and has the authority to issue emergency "Local-Prescriptions" based on the traveler's medical history.
4.  **Local-Pharmacy Inventory-Check**:
    *   **Action**: Autonomously contacting the nearest pharmacies to confirm they have the specific medication in stock before the traveler departs their hotel.

## 3. Data Schema: `Medical_Prescription_Bridge_Event`

```json
{
  "event_id": "PIP-99221",
  "traveler_id": "GUID_9911",
  "home_country_medication": "ZOLOFT",
  "active_ingredient": "SERTRALINE",
  "dosage_mg": 50,
  "host_country": "UNITED_KINGDOM",
  "local_equivalent_brand": "LUSTRAL",
  "nearest_emergency_clinic_id": "NHS-LHR-01",
  "pharmacy_confirmed_stock": true,
  "status": "CLINIC_REFERRAL_ISSUED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Non-Diagnostic' Boundary**: The agent MUST NOT provide medical advice or "Diagnose" a condition. It must only act as a "Logistics-Liaison" for existing prescriptions.
- **Rule 2: The 'Controlled-Substance' Safety-Gate**: If the medication is a "Controlled-Substance" (e.g., specific narcotics or stimulants), the agent MUST immediately alert the traveler that a local physician consultation is mandatory and that cross-border transfer of the medication may have legal implications.
- **Rule 3: Digital-Prescription-Vault Integration**: The agent MUST prioritize clinics that can ingest the traveler's "Home-Country" digital health records (ID-001) to verify the existing prescription.

## 5. Success Metrics (Medical)

- **Medication-Recovery-Velocity**: Time from reporting lost medication to the traveler holding a local equivalent.
- **Clinic-Referral-Accuracy**: % of referred clinics that successfully issued the local prescription.
- **Traveler-Medical-Anxiety-Reduction**: Self-reported stress levels during the medical recovery process.
