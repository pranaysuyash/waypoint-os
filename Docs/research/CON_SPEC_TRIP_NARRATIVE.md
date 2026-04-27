# Con Spec: Agentic 'Trip-Narrative' Generator (CON-REAL-030)

**Status**: Research/Draft
**Area**: Post-Trip Storytelling, Retention & Brand Differentiation

---

## 1. The Problem: "The Forgettable Trip"
Travel experiences are ephemeral. Travelers return home, upload photos to a cloud drive, and within weeks the specificity of the experience — the vendor's name, the exact dish, the reason they loved that particular moment — fades. Agencies lose the opportunity to transform a completed trip into a lasting "Brand-Imprint" and a powerful retention anchor. No agency currently gives travelers a beautifully written record of their journey.

## 2. The Solution: 'Experiential-Story-Protocol' (ESP)

The ESP acts as the "Agency's Ghostwriter."

### Narrative Actions:

1.  **Trip-Data-Synthesis**:
    *   **Action**: Pulling structured data from the completed itinerary: vendors visited, activities, meals, accommodation notes, and any feedback signals or conversation highlights from the trip.
2.  **Voice-Calibrated-Narrative-Generation**:
    *   **Action**: Generating a beautifully written "Trip-Narrative" in a voice calibrated to the traveler's psychographic profile (e.g., evocative and literary for an "Authentic-Seeker"; clean and precise for a "Status-Signal" traveler).
3.  **Keepsake-Package-Assembly**:
    *   **Action**: Assembling a "Digital-Keepsake-Package" — the narrative, a curated vendor list with personal notes, a recommended "Return-Reasons" section ("Why you'd go back"), and a suggested itinerary for sharing with friends who ask "What did you do?").
4.  **Referral-Seeded-Story**:
    *   **Action**: Embedding a subtle, non-intrusive "Agency-Attribution-Line" in the narrative (e.g., "Trip curated by [Agency Name]") so when the traveler shares the narrative, it acts as an organic brand referral.

## 3. Data Schema: `Trip_Narrative_Package`

```json
{
  "package_id": "ESP-88221",
  "traveler_id": "TRAVELER_ALPHA",
  "trip_id": "KYOTO-2026-01",
  "narrative_word_count": 1200,
  "voice_profile": "LITERARY_EVOCATIVE",
  "keepsake_sections": ["NARRATIVE", "VENDOR_LIST", "RETURN_REASONS", "SHARE_ITINERARY"],
  "referral_attribution": "SUBTLE_BRAND_FOOTER",
  "delivery_status": "DELIVERED_VIA_EMAIL"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'No-Marketing-Copy' Standard**: The narrative MUST read as a genuine, personal travel account — not as marketing material. Any agency attribution MUST be tasteful and minimal.
- **Rule 2: Traveler-Edit-Right**: The traveler MUST be able to edit or request a re-generation of the narrative before it is finalized in their memory vault.
- **Rule 3: Opt-In-Sharing-Only**: The "Share-Itinerary" section MUST be clearly marked as optional and only activated if the traveler explicitly consents to sharing their trip details.

## 5. Success Metrics (Narrative)

- **Narrative-Open-Rate**: % of travelers who open and read their generated trip narrative.
- **Organic-Referral-Rate**: % of new traveler inquiries that cite the narrative as the source of their agency discovery.
- **Retention-Impact**: Difference in rebooking rates between travelers who received a narrative vs. those who did not.
