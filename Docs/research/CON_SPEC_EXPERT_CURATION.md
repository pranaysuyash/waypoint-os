# Con Spec: Hyper-Local Expert-Curation-Engine (CON-REAL-013)

**Status**: Research/Draft
**Area**: Curation & Authenticity

---

## 1. The Problem: "The Yelp Bubble"
Major travel platforms (TripAdvisor, Yelp, Google Maps) tend to optimize for "Volume-of-Reviews," which often surfaces commercialized, tourist-heavy locations. Travelers seeking "Authenticity" often find themselves at the same "Hidden-Gems" as thousands of others, leading to a "Sanitized-Travel-Experience." There is no automated bridge between highly localized, non-commercial expert networks and the traveler's itinerary.

## 2. The Solution: 'Anti-Generic-Travel-Protocol' (AGTP)

The AGTP allows the agent to act as a "Local-Insider."

### Curation Actions:

1.  **Non-Commercial Network-Ingestion**:
    *   **Action**: Identifying and "Quiet-Monitoring" hyper-local sources (e.g., neighborhood Subreddits, local artisan WhatsApp groups, regional food critics' newsletters, hobbyist Discord servers).
2.  **Sentiment-Signal-Isolation**:
    *   **Action**: Filtering out "Influencer-Marketing" and "Tourist-Hype." The agent prioritizes recommendations that mention "Local-Favorites," "Daily-Rituals," or "Historical-Continuity."
3.  **The 'Zero-Saturation' Filter**:
    *   **Action**: Cross-referencing suggestions with major review platforms. If a location has <50 reviews on TripAdvisor but high-sentiment in local networks, it is tagged as a "True-Hidden-Gem."
4.  **Bespoke 'Vibe-Matching'**:
    *   **Action**: Matching the "Vibe" of local spots to the traveler's specific persona (TWO). (e.g., "This specific bookstore in Brooklyn is known for rare first-editions, which matches your interest in 20th-century literature").

## 3. Data Schema: `Hyper_Local_Curation_Asset`

```json
{
  "asset_id": "AGTP-99221",
  "traveler_id": "GUID_9911",
  "asset_name": "CAFÉ DE LA LUZ",
  "source_network": "MADRID_ARTISAN_NEWSLETTER",
  "saturation_score": 0.12,
  "vibe_tags": ["LOW_LIGHT", "HIDDEN_ENTRANCE", "LOCAL_ONLY"],
  "persona_match_confidence": 0.94,
  "status": "ASSET_SUGGESTED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'No-Influencer' Gate**: Any source identified as having >10k social media followers or an "Affiliate-Revenue-Model" MUST be de-prioritized in the AGTP to maintain authenticity.
- **Rule 2: Freshness-Requirement**: Recommendations MUST be verified against local events (e.g., "This cafe is closed for a private neighborhood festival today") before being presented to the traveler.
- **Rule 3: Respectful-Incursion-Limit**: The agent MUST NOT suggest "Private-Residential" or "Sacred-Spaces" unless they are explicitly open to respectful tourism.

## 5. Success Metrics (Curation)

- **Authenticity-Yield**: % of visited locations with <100 reviews on major global platforms.
- **Curation-Surprise-Score**: Traveler self-reported satisfaction with "Unexpected/Unique" finds.
- **Local-Sentiment-Alignment**: Correlation between agent suggestions and "Local-Favorite" designations.
