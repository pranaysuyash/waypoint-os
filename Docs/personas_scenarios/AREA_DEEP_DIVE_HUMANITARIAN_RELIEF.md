# Area Deep Dive: Humanitarian & NGO Field Logistics

## High-Level Objective
To facilitate the movement of aid workers, emergency responders, and relief assets into high-risk, non-standard, or crisis-affected regions while maintaining strict donor compliance.

## Stakeholder Mapping
*   **P1 (Solo Agent)**: Manages high-stakes emergency deployments.
*   **P3 (Junior Agent)**: Handles the documentation-heavy grant reconciliation and reporting.
*   **S1 (Humanitarian Worker)**: Traveler focused on mission delivery, often working in austere environments.
*   **S2 (Supplier)**: UNHAS (UN Humanitarian Air Service), specialized charter operators, and humanitarian-fare airlines.
*   **Donor (Grant Owner)**: USAID, ECHO, or private foundations requiring 100% audit transparency.

## Critical Logistics & Logic
### 1. Grant-Based Reconciliation (The "Donor Ledger")
*   **Logic**: Every trip must be tagged with a `Grant_ID`. 
*   **Trigger**: Intake stage for any NGO-classified agency.
*   **Rule**: System blocks booking if the `Grant_ID` is expired or over-budget.

### 2. Humanitarian Fares (The "Flexibility Rule")
*   **Logic**: Automated application of "Humanitarian Fares" which offer 100% refundability and high baggage (40kg+) for relief gear.
*   **Validation**: System checks `NGO_Credential_Registry` before applying the fare.

### 3. UNHAS Integration
*   **Logic**: Coordination with UNHAS for "Last-Mile" aerial transport into zones without commercial airports.
*   **Workflow**: Seamless handoff from commercial air to UNHAS manifest.

## Specialized Scenarios

### Scenario 340: The "Grant Sunset" Rush
*   **Context**: A project grant expires in 72 hours; all remaining travel funds must be booked or lost.
*   **Frontier Logic**: `GhostConcierge` identifies all pending travel needs for that project and bulk-quotes them to lock in donor compliance before the midnight deadline.

### Scenario 341: Emergency Medevac Handoff
*   **Context**: A field worker is injured in a remote area.
*   **Immune Response**: System automatically switches the trip status to `CRITICAL_RECOVERY`, coordinates with the specialized Medevac insurer, and prepares the "Fit to Fly" documentation for the return flight.

## Commercial Mechanics
*   **Margins**: Low-margin, volume-based, or service-fee based.
*   **Transparency**: Monthly "Donor-Ready" PDF reports showing every cent spent per grant.
*   **Compliance**: Mandatory "Fly America Act" logic for US-funded grants.

## Design Identity (NGO / Field Ready)
*   **Aesthetic**: "Functional/Rugged" (high clarity, low distraction).
*   **Imagery**: Field sites, relief maps, cargo manifests.
*   **Trust Anchor**: "Compliance Score"—showing the audit-readiness of the current trip manifest.
