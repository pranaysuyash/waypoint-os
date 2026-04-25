# Operational Logic Spec: Supplier Bankruptcy (LCC/Hotel Collapse)

## 1. Scenario Context (OE-001)
A major supplier (e.g., a Low-Cost Carrier or a regional Hotel Chain) declares insolvency mid-trip or pre-departure. The system must move from "Alerting" to "Autonomous Recovery" to protect travelers and agency margin.

## 2. Playbook Logic: The "Re-Protection" Engine

### Phase 1: Impact Analysis (Detection)
- **Signal**: External API alert or GDS status `UN` (Unconfirmed) / `HX` (Cancelled by carrier).
- **Logic**:
  - Scan all `active` and `confirmed` trips in `AuditStore`.
  - Filter by `supplier_id` matching the insolvent entity.
  - Categorize by **Urgency Band**:
    - **Band A (Mid-Trip)**: Traveler is at the airport or checked in.
    - **Band B (Pre-Departure < 48h)**: Imminent travel.
    - **Band C (Future)**: Travel > 48h away.

### Phase 2: Autonomous Re-Shopping
- **Constraint**: Maintain the original "Traveler Persona" preferences (e.g., "Must have flat bed", "Direct only").
- **Logic**:
  - Auto-generate 3 alternative itineraries via `ItineraryEngine`.
  - **Financial Arbitration**:
    - If `agency_margin` covers the delta: Auto-book and notify (Seamless recovery).
    - If `delta > margin`: Route to Owner for "Client Goodwill vs. Agency Loss" decision.

### Phase 3: Financial Recovery (The Chargeback SOP)
- **Logic**:
  - Auto-generate "Letter of Non-Performance" for the traveler.
  - Trigger "Chargeback Defense" status in the payment ledger to prevent merchant account freeze.
  - Log "Supplier Default" in `AdversarialEngine` to blacklist the entity from future quotes.

---

## 3. 11-Dimension Quality Audit (Playbook Evaluation)

| Dimension | Evaluation | Status |
| :--- | :--- | :--- |
| **Code** | Requires `SupplierStatusWatcher` thread in `spine_api`. | 🟡 |
| **Operational** | Operators need a "Mass-Action" UI to approve re-protection for 100+ travelers. | ❌ |
| **User Experience** | Traveler gets "Don't worry, we've already re-booked you" notification before they see the news. | ✅ |
| **Logical Consistency** | Re-protection must handle "Split Tickets" (e.g., Outbound LCC, Return Legacy). | ✅ |
| **Commercial** | Logic must decide between "Refund & New Booking" vs "Ticket Exchange" based on GDS rules. | 🟡 |
| **Data Integrity** | No "Ghost PNRs" left in the system; old segments must be marked `VOID`. | ✅ |
| **Quality & Reliability** | Fallback to "Human Agent" if re-shopping fails to find a flight within 15% of original price. | ✅ |
| **Compliance** | EU261 or local consumer protection laws must be cited in the recovery brief. | 🟡 |
| **Operational Readiness** | Crisis runbook needed for "Merchant Account Reserve" negotiations. | ❌ |
| **Critical Path** | Dependent on `GDS_DIRECT_CANCEL` capability. | 🟡 |
| **Final Verdict** | **Strategic Match**: High. Move to technical spec once UI for mass-action is defined. | **🟡 Partial** |

---

## 4. Open Questions for Research
- **Q1**: How do we handle "Non-Refundable" Net Rates where the agency has already paid the consolidator?
- **Q2**: Can the AI negotiate "Bulk Re-protection" with a competitor airline for 50+ displaced travelers?
