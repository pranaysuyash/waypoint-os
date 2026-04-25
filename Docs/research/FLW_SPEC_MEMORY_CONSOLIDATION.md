# Flow Spec: Agentic Memory-Consolidation (FLW-005)

**Status**: Research/Draft
**Area**: Personalization & Long-Term Learning

---

## 1. The Problem: "The Amnesiac Agent"
Most travel agents treat every trip as a "Clean-Slate." Even if a traveler hated their stay at a generic business hotel in London, the agent might suggest the same chain in Tokyo. Valuable behavioral data (rejections, complaints, local discoveries) is lost after the trip concludes, leading to repetitive sub-optimal planning.

## 2. The Solution: 'Post-Trip-Distillation-Protocol' (PTDP)

The PTDP allows the agent to act as an "Institutional-Historian."

### Distillation Actions:

1.  **Sentiment-Nuance-Extraction**:
    *   **Action**: Analyzing the traveler's feedback (chat logs, direct ratings, photos) to identify "Latent-Preferences" (e.g., "The user complained about the street noise in Paris, implying a preference for 'Courtyard-Facing' or 'High-Floor' units").
2.  **Itinerary-Deviation-Audit**:
    *   **Action**: Comparing the "Planned-Itinerary" with the "Actual-Location-History" (via metadata). If the traveler skipped a museum for a local jazz club, the agent updates the persona to bias toward "Live-Performance-Discovery."
3.  **Wisdom-Object-Serialization**:
    *   **Action**: Packaging these insights into a `Travel-Wisdom-Object` (TWO) that is injected into the prompt context for all future trip generations.
4.  **Implicit-Rejection-Learning**:
    *   **Action**: If the agent suggested 5 breakfast spots and the user went to a 6th un-suggested spot, the agent analyzes the 6th spot to find the "Missing-Attribute" in the previous 5 suggestions.

## 3. Data Schema: `Travel_Wisdom_Object`

```json
{
  "wisdom_id": "TWO-55221",
  "traveler_id": "GUID_9911",
  "source_trip": "LONDON_PARIS_2026",
  "distilled_insights": [
    { "type": "ACCOMMODATION", "value": "Prefers boutique hotels over 500+ room properties", "confidence": 0.92 },
    { "type": "TRANSIT", "value": "Avoids 6AM flights even if €200 cheaper", "confidence": 0.98 },
    { "type": "FOOD", "value": "High interest in natural wine bars", "confidence": 0.85 }
  ],
  "persona_delta_applied": true,
  "last_updated_utc": "2026-12-01T10:00:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Multi-Signal-Verification' Rule**: An insight MUST be supported by at least two signals (e.g., a chat comment AND an itinerary deviation) before it is committed to the long-term `Travel-Wisdom-Object`.
- **Rule 2: Negative-Preference-Weighting**: Negative preferences (rejections) are weighted 3x more heavily than positive preferences to avoid repeating past frustrations.
- **Rule 3: User-Review-Gate**: Before a major persona shift (e.g., "Moving from Budget to Luxury bias"), the agent MUST present a "Wisdom-Summary" to the user for validation.

## 5. Success Metrics (Memory)

- **Preference-Alignment-Delta**: % decrease in user-itinerary-edits over sequential trips.
- **Repeat-Frustration-Rate**: Number of times the agent suggests a previously rejected category/property (target: 0).
- **Discovery-Success-Rate**: % of agent-suggested "New-Discoveries" that the user actually visits.
