# Operational Logic Spec: Multi-Party Reconciliation (The GST Ghost)

## 1. Scenario Context (OE-002)
A complex multi-family group booking (e.g., 3 families traveling together) requires fractional invoicing across different tax jurisdictions (e.g., Family A needs an Indian GST invoice, Family B needs a UK VAT invoice, and Family C is US-based with no tax ID).

## 2. Playbook Logic: The "Fractional Ledger"

### Phase 1: Group Segmentation (`sub_groups`)
- **Data Structure**: The `CanonicalPacket` must support an array of `sub_groups`.
- **Logic**:
  - Each `traveler` is mapped to exactly one `sub_group_id`.
  - Each `segment` (Flight, Hotel) is mapped to one or more `sub_group_ids` with a **Weight** (e.g., 50/50 split for a shared villa).

### Phase 2: Fractional Invoicing
- **Logic**:
  - **Direct Segments**: Invoiced 100% to the assigned `sub_group`.
  - **Shared Segments**: Calculation of "Cost per Head" vs "Cost per Room" based on family preference.
  - **Tax Layer**:
    - Apply **GST (18%)** to Service Fees for Indian `sub_groups`.
    - Apply **VAT (20%)** for UK `sub_groups` if the agency has a UK entity.
    - Handle **TCS (Tax Collected at Source)** for Indian residents booking international travel.

### Phase 3: Payment Tracking & Reconciliation
- **Logic**:
  - Track "Paid vs. Due" at the `sub_group` level, not the `trip` level.
  - **Conflict Resolution**: If Family A pays but Family B doesn't, the system must block the *entire* booking only if it's a non-split PNR. If split-able, it should auto-split the PNR to protect the paying family.

---

## 3. 11-Dimension Quality Audit (Playbook Evaluation)

| Dimension | Evaluation | Status |
| :--- | :--- | :--- |
| **Code** | `CanonicalPacket` requires `sub_groups` and `weight` fields. | 🟡 |
| **Operational** | Agents need a "Split Cost" UI that supports drag-and-drop travelers into buckets. | ❌ |
| **User Experience** | Families get individual invoices that look professional and clear, reducing "Who owes what" tension. | ✅ |
| **Logical Consistency** | Must handle "Shared Amenities" (e.g., a $500 tour for the whole group). | ✅ |
| **Commercial** | Split-payment logic prevents one family's credit card failure from tanking the whole trip. | ✅ |
| **Data Integrity** | Invoice totals across all sub-groups must sum exactly to the `trip_total`. | ✅ |
| **Quality & Reliability** | Audit check: Ensure GST IDs are validated against government APIs before invoice generation. | 🟡 |
| **Compliance** | Compliance with Indian LRS (Liberalized Remittance Scheme) limits for each family. | 🟡 |
| **Operational Readiness** | Handoff to Accounting (Tally/Zoho) requires a "Sub-Group Aware" export. | ❌ |
| **Critical Path** | Requires `PaymentGateway` to support multiple transactions per `trip_id`. | 🟡 |
| **Final Verdict** | **Critical Feature**: Solves a major pain point for high-net-worth group travel. | **🟡 Partial** |

---

## 4. Open Questions for Research
- **Q1**: How do we handle "Non-Proportional Splits" (e.g., Dad pays 70%, Son pays 30%)?
- **Q2**: If the PNR cannot be split (e.g., group fare), what is the legal liability for the agency if one party defaults?
