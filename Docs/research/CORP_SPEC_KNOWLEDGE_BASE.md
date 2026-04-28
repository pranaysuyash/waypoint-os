# Corp Spec: Agentic 'Agency-Knowledge-Base' Self-Builder (CORP-REAL-032)

**Status**: Research/Draft
**Area**: Institutional Memory Accumulation, Knowledge Extraction & Proprietary Intelligence Building

---

## 1. The Problem: "The Knowledge-Evaporation-Cycle"
Every trip an agency handles generates enormous operational intelligence: which hotel room category actually has the best view, which airport lounge is genuinely worth the fee, which local guide delivered above expectations, which visa requirement changed since the last booking. This knowledge evaporates — it lives in one agent's memory, in an email thread, or is simply lost when a staff member leaves. The agency starts fresh with every similar booking, never compounding its expertise.

## 2. The Solution: 'Institutional-Memory-Protocol' (IMP)

The IMP acts as the "Knowledge-Compounding-Engine."

### Knowledge Actions:

1.  **Post-Trip-Intelligence-Extraction**:
    *   **Action**: After every completed trip, the agent systematically extracts structured "Knowledge-Atoms" — discrete, reusable operational facts — from traveler feedback, agent notes, vendor communications, and incident reports:
        - **Property-Intelligence**: Specific room categories worth requesting, seasonal quality variations, staff names to mention at check-in.
        - **Logistics-Intelligence**: Transfer timing buffers that proved realistic vs. optimistic, local transport nuances, border-crossing protocols that changed.
        - **Vendor-Intelligence**: Updated vendor reliability assessments, new offerings, pricing intelligence, relationship notes.
        - **Regulatory-Intelligence**: Visa or entry requirement changes discovered during the trip, health documentation that was actually requested vs. theoretically required.
2.  **Knowledge-Atom-Indexing**:
    *   **Action**: Structuring extracted Knowledge-Atoms by destination, property, vendor, and trip type — making them retrievable at the point of next booking, not discoverable only by memory.
3.  **Conflict-Resolution**:
    *   **Action**: When a new Knowledge-Atom conflicts with an existing one (e.g., a room category that was excellent in 2023 but poor in 2026), applying a recency-weighted confidence scoring to determine which version to surface — and flagging the conflict for human review.
4.  **Knowledge-Base-Gap-Detection**:
    *   **Action**: Before designing an itinerary for a destination or vendor category with sparse Knowledge-Atom coverage, the agent flags the gap — recommending proactive research or a direct vendor briefing call before proceeding.

## 3. Data Schema: `Knowledge_Atom`

```json
{
  "atom_id": "IMP-88221",
  "destination": "MALDIVES",
  "property": "RESORT_ALPHA",
  "category": "PROPERTY_INTELLIGENCE",
  "content": "Ocean-facing water villas on the east side receive direct sunrise light. West-facing villas get better sunset views but more boat traffic noise after 17:00.",
  "source_trip_id": "MALDIVES-2026-03",
  "extracted_date": "2026-04-01",
  "confidence_score": 0.92,
  "conflicts_with": null,
  "human_verified": true
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Atom-Granularity' Standard**: Knowledge-Atoms MUST be specific and actionable, not generic. "Good hotel" is not a Knowledge-Atom. "Ocean-villa east side — sunrise light, minimal boat noise" is.
- **Rule 2: The 'Recency-Decay' Model**: Knowledge-Atoms older than 18 months in fast-changing categories (visa rules, pricing, staff) MUST have their confidence score reduced and be flagged for re-verification before surfacing.
- **Rule 3: The 'Proprietary-Boundary'**: The Knowledge-Base is a core agency proprietary asset. It MUST NOT be shared with competing agencies, white-label sub-instances without the parent agency's explicit per-domain permission, or any external party.

## 5. Success Metrics (Knowledge)

- **Knowledge-Atom-Accumulation-Rate**: New Knowledge-Atoms added per trip handled.
- **Knowledge-Retrieval-Rate**: % of new itinerary designs where at least one relevant Knowledge-Atom was retrieved and applied.
- **Knowledge-Impact-Score**: Traveler satisfaction delta for trips where Knowledge-Atoms were applied vs. trips where the destination/vendor had no prior coverage.
