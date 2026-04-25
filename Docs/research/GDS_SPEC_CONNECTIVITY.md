# GDS Spec: Connectivity & Protocol Translation (GDS-001)

**Status**: Research/Draft
**Area**: API Engineering & Inventory Management

---

## 1. The Problem: "The Legacy Mismatch"
The travel industry is a patchwork of legacy EDIFACT-based GDS systems (Sabre, Amadeus) and modern JSON-based NDC APIs. A single booking might require translating between three different schemas. Errors in translation lead to "Ghost-Bookings," incorrect pricing, or failed ticketing.

## 2. The Solution: 'Schema-Bridge-Protocol' (SBP)

The SBP acts as a "Universal Translator" that ensures data-integrity across the travel stack.

### Engineering Actions:

1.  **Atomic-Intent-Normalization**:
    *   **Action**: Converting traveler requests into a "Canonical-Travel-Object" (CTO) before sending to any provider API.
2.  **Idempotency-Locking**:
    *   **Action**: Ensuring that a "Double-Click" or a "Network-Retry" doesn't result in two tickets being issued in the legacy GDS.
3.  **Latency-Aware-Inventory-Sync**:
    *   **Action**: Tracking the time-gap between "Price-Quote" and "Ticketing-Approval." If gap > 180s, the agent MUST re-validate price before charging.

## 3. Data Schema: `Canonical_Travel_Object` (CTO)

```json
{
  "cto_id": "CTO-8822",
  "segments": [
    {
      "origin": "LHR",
      "destination": "JFK",
      "departure": "2026-11-10T10:00:00Z",
      "carrier_code": "BA",
      "cabin": "BUSINESS"
    }
  ],
  "provider_mappings": {
    "sabre": "REQ_X_122",
    "amadeus": "REQ_Y_99",
    "ndc_lh": "REQ_Z_44"
  }
}
```

## 4. Key Logic Rules

- **Rule 1: Re-Validation-on-Drift**: If the GDS returns a price that differs by >0.5% from the initial quote, the agent must halt and re-verify intent.
- **Rule 2: Fallback-Sync**: If the primary NDC API fails, the agent autonomously falls back to the legacy GDS path to ensure seat-guarantee, even if at a slightly higher cost.
- **Rule 3: Session-Heartbeat**: For stateful GDS connections, the agent must maintain a "Heartbeat" every 30s to prevent session-expiry during complex manual review phases.

## 5. Success Metrics (GDS)

- **Translation-Error-Rate**: % of bookings that failed due to schema-mismatch.
- **Quote-to-Ticket-Success**: % of successful tickets issued at the quoted price.
- **API-Latency-P99**: Response time for multi-provider inventory searches.
