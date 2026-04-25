# Integration Spec: Tool-Output-Synthesizer (INT-002)

**Status**: Research/Draft
**Area**: Data Integrity & Interoperability

---

## 1. The Problem: "The Naming Tower of Babel"
Different travel APIs return the same data using wildly different schemas. Amadeus might call a seat class `ECONOMY_STANDARD`, while a direct NDC connection from Lufthansa calls it `LIGHT_FARE`, and Sabre uses a proprietary code like `Y-CLASS`. If the agent's reasoning model receives these raw, it will fail to compare them accurately or hallucinate that they are different products.

## 2. The Solution: 'Cross-GDS-Normalization-Protocol' (CGNP)

The CGNP acts as a "Universal-Translator" for the agent's perception layer.

### Normalization Actions:

1.  **Schema-Mapping-Layer**:
    *   **Action**: Mapping vendor-specific keys to a "Canonical-Travel-Schema" (e.g., all variations of coach/standard/light are mapped to `SERVICE_CLASS: ECONOMY`).
2.  **Amenity-De-Duplication**:
    *   **Action**: Identifying that "Free Wi-Fi" (Amadeus) and "Connected Cabin" (NDC) refer to the same feature and normalizing them to a single boolean flag: `amenities.wifi = true`.
3.  **Currency-Harmonization**:
    *   **Action**: Automatically converting all prices to the traveler's "Base-Currency" (e.g., USD) using a real-time mid-market rate, ensuring "Apples-to-Apples" price comparisons.
4.  **Confidence-Weighting**:
    *   **Action**: Assigning a "Reliability-Score" to the data source (e.g., Direct-NDC = 1.0, 3rd Party Scraper = 0.6). The agent's reasoning logic prioritizes data from higher-scored sources.

## 3. Data Schema: `Normalized_Travel_State`

```json
{
  "canonical_id": "CTS-99221",
  "segments": [
    {
      "type": "FLIGHT",
      "operator": "LH",
      "service_class": "ECONOMY",
      "amenities": {
        "wifi": true,
        "power": true,
        "checked_bag": 0
      },
      "raw_sources": ["NDC_LH_API", "AMADEUS_GDS"],
      "price_total_usd": 450.00
    }
  ],
  "normalization_latency_ms": 12
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Strict-Type' Rule**: The reasoning model MUST NOT receive raw tool output. It only interacts with the `Normalized_Travel_State` to prevent schema-drift hallucinations.
- **Rule 2: Conflict-Resolution**: If two sources disagree (e.g., Amadeus says 1 bag, NDC says 0), the agent MUST prioritize the "Most-Direct" source (NDC) and log the discrepancy for the `Amenity-Audit-Protocol` (OPS-REAL-017).
- **Rule 3: Unknown-Value-Handling**: If a vendor uses a code the CGNP doesn't recognize, it MUST be flagged as `UNKNOWN_VENDOR_SPECIFIC` and triggered for an autonomous "Research-Lookup" to map it for future trips.

## 5. Success Metrics (Normalization)

- **Mapping-Coverage**: % of incoming JSON keys successfully mapped to the canonical schema.
- **Reasoning-Coherence**: Reduction in agent errors caused by misinterpreted vendor naming.
- **Price-Parity-Error**: % difference between normalized price and final checkout price (target: <0.1%).
