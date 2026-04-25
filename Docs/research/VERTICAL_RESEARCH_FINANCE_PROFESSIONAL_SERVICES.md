# Vertical Research: Finance & Professional Services

**Status**: Research/Draft
**Area**: Audit-Trail Integrity, Compliance & High-Value Deal Logistics

---

## 1. Context: The 'Billable-Precision' Segment
Travel in Finance and Professional Services (Consulting, Law) is driven by "Billable Accuracy" and "Deal Deadlines." The system must ensure every dollar is attributable to a client project and every trip is compliant with both the firm's and the client's travel policies.

## 2. Specialized Operational Requirements

### [A] Immutable Client-Project Attribution
- **Constraint**: Every expense must be tagged with a `Client_Project_ID` at the moment of booking.
- **Action**: Mandatory field validation in the `CanonicalPacket`. If the project code is invalid, the booking is blocked.

### [B] Dual-Policy Enforcement (Firm vs. Client)
- **Constraint**: A consultant must follow the most restrictive rule between their Firm's policy and the Client's policy (e.g., Firm allows Business Class, but Client only pays for Economy).
- **Action**: `Intersect_Policy_Engine`. The search filter must auto-calculate the "Lowest Common Denominator" of allowed options.

### [C] SEC/Regulatory Audit Readiness
- **Constraint**: For regulated firms, travel records must be immutable and stored in a way that satisfies SEC/FINRA audit requests.
- **Action**: `Audit_Vault_Mirror`. A write-only mirror of the `AuditStore` that hashes events for tamper-evidence.

## 3. Frontier Scenarios (Finance)

1.  **FI-001: The 'Deal-Closing' Deadline Disruption**:
    *   **Scenario**: A lawyer is traveling to sign a merger agreement. Their flight is cancelled.
    *   **Recovery**: AI calculates the "Transaction Value" vs. "Recovery Cost." Authorized for `Private_Jet_Empty_Leg` if it's the only way to meet the signature window.

2.  **FI-002: The 'Policy-Clash' Resolution**:
    *   **Scenario**: A partner books a flight that is Firm-compliant but Client-non-compliant.
    *   **Recovery**: AI flags the `Policy_Drift` and prompts the partner: "This flight exceeds the Client's Economy-only policy. The Firm will need to absorb the $800 difference. Do you want to proceed or downgrade?"

3.  **FI-003: The 'Anonymized-Billing' Request**:
    *   **Scenario**: An investment bank is doing due-diligence on a target company and needs to travel to the site without the target company seeing the bank's name on the hotel guest list.
    *   **Recovery**: `Discrete_Entity_Booking`. Use a shell entity or "Company Secret" greeter protocols.

## 4. Key Logic Extensions

- **Extension 1: Billable-Rate Mapper**: Automatically calculates the "Agency Service Fee" as a percentage of the billable project value (if permitted).
- **Extension 2: Policy Intersector**: A logic layer that ingests multiple JSON policies and returns a single unified "Permitted Search Schema."
- **Extension 3: SEC-Compliance Hash**: A background worker that generates a daily SHA-256 hash of all financial audit events.

## 5. Success Metrics (Finance)

- **Billing Accuracy**: Zero "Unassigned Project Codes" in the monthly reconciliation.
- **Compliance Rate**: 100% adherence to dual-policy constraints.
- **Audit Speed**: 100% of travel data retrieval completed in < 1 hour for regulatory requests.
