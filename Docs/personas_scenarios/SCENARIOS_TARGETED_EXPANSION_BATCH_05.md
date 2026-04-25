# Scenarios: Targeted Expansion Batch 05 (Operational Integrity)

This batch populates the 'Missing Buckets' identified in the `MATRIX_VALIDATION_AUDIT_2026-04-24.md`. These scenarios are designed to stress-test the operational logic specifications defined in the research phase.

## [OE-001] Supplier Bankruptcy / Failure

### [OE-001-A] The 'LCC-332' Mid-Trip Collapse (P1)
- **Persona**: P1 (Solo Agent) + S1 (Traveler)
- **Scenario**: A low-cost carrier (LCC) goes bankrupt while a family of 4 is at the airport in Singapore. The system detects the failure via GDS signal.
- **Goal**: Validate "Autonomous Re-protection" vs "Manual Oversight" trigger based on `Risk_Budget`.
- **Logic Reference**: `OPERATIONAL_LOGIC_SPEC_BANKRUPTCY.md`

### [OE-001-B] The 'Hotel-Chain-Default' Pre-Departure (P2)
- **Persona**: P2 (Agency Owner)
- **Scenario**: A boutique hotel chain in Italy closes overnight due to insolvency. 15 upcoming bookings are affected.
- **Goal**: Validate "Mass-Action" re-booking logic and commercial cost-benefit analysis.

## [OE-002] Multi-Party Reconciliation

### [OE-002-A] The 'GST-Fractional' Group (S2)
- **Persona**: S2 (Family Coordinator)
- **Scenario**: Three families (India-based, UK-based, US-based) book a shared villa in the Maldives. Family A needs a corporate GST invoice.
- **Goal**: Validate the `sub_groups` data structure and fractional tax calculation.
- **Logic Reference**: `OPERATIONAL_LOGIC_SPEC_MULTI_PARTY.md`

### [OE-002-B] The 'Shared-Segment' Default (P3)
- **Persona**: P3 (Junior Agent)
- **Scenario**: One family in a group booking fails to pay their share of the deposit.
- **Goal**: Validate "Split-PNR" logic to protect the paying families without tanking the whole trip.

## [OE-003] Handoff Integrity

### [OE-003-A] The '3-AM-Silent-Switch' (S1)
- **Persona**: S1 (Traveler)
- **Scenario**: A traveler's flight is cancelled at 3 AM. The escalation reaches the Junior Agent, who doesn't respond within 15 minutes.
- **Goal**: Validate the "Dead Man's Switch" autonomous recovery and post-action audit.
- **Logic Reference**: `OPERATIONAL_LOGIC_SPEC_HANDOFF.md`

## [RE-001] Regulatory & Compliance

### [RE-001-A] The 'Mid-Trip-Purge' Request (P2)
- **Persona**: P2 (Agency Owner)
- **Scenario**: A traveler exercises their "Right to be Forgotten" (GDPR) while they are still mid-trip.
- **Goal**: Validate the conflict resolution between "Data Deletion" and "Operational Retention" for tax/GDS purposes.

### [RE-002-A] The 'Visa-Ghost' Rule Change (S1)
- **Persona**: S1 (Traveler)
- **Scenario**: A country changes its visa-on-arrival rules for a specific nationality while a traveler is in the air.
- **Goal**: Validate the "Federated Intelligence" threat detection and redirection logic.

## [VL-001] Vertical-Specific Logistics

### [VL-001-A] The 'Maritime-Rotation' Miss (P3)
- **Persona**: P3 (Junior Agent)
- **Scenario**: A crew rotation for an oil rig is delayed by 4 hours, risking a "Heli-Lift" window that costs $50k.
- **Goal**: Validate the "High-Stakes Logistics" priority scoring.

### [VL-002-A] The 'Oxygen-SLA' Failure (S1)
- **Persona**: S1 (Traveler)
- **Scenario**: A traveler with medical oxygen requirements has their flight swapped to an aircraft that doesn't support their specific concentrator.
- **Goal**: Validate "Critical Medical Suitability" blocking and recovery.
