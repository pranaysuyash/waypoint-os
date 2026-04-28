# Corp Spec: Agentic 'Agency-Alumni' Network Protocol (CORP-REAL-031)

**Status**: Research/Draft
**Area**: Dormant Traveler Re-Engagement, Alumni Advocacy & Lapsed Client Recovery

---

## 1. The Problem: "The Forgotten-Alumni"
Most agencies invest enormous effort in acquiring new travelers while passively losing past clients to inactivity. A traveler who took one extraordinary trip 3 years ago and hasn't returned is an "Alumni" — someone who trusted the agency, had a good experience, but simply drifted away through lack of contact. This "Forgotten-Alumni" problem is the single biggest untapped revenue source for established agencies. Re-engagement costs a fraction of acquisition.

## 2. The Solution: 'Alumni-Engagement-Protocol' (AEP)

The AEP acts as the "Relationship-Revival-Engine."

### Alumni Actions:

1.  **Alumni-Segmentation**:
    *   **Action**: Classifying all past travelers into "Alumni-Cohorts" based on recency, booking value, and trip type:
        - **"Warm-Alumni"**: Last booked 12–24 months ago (highest re-engagement probability).
        - **"Cool-Alumni"**: Last booked 24–48 months ago (moderate probability, requires trigger event).
        - **"Cold-Alumni"**: Last booked 48+ months ago (requires high-value re-engagement hook).
2.  **Re-Engagement-Trigger-Identification**:
    *   **Action**: Monitoring for "Natural-Re-Engagement-Moments" for each alumni: the anniversary of their last trip, a new opening at their favorite destination category, a seasonal window that matches their historical travel pattern, or a life-event signal.
3.  **Personalized-Alumni-Outreach**:
    *   **Action**: Generating deeply personalized re-engagement messages rooted in specific Memory-Crystals from past trips (e.g., "It's been 2 years since your Amalfi trip. We still think about that private boat day you mentioned — and there's a new coastal experience we think you'd love even more").
4.  **Alumni-Ambassador-Activation**:
    *   **Action**: For "Warm-Alumni" with high Advocacy-Value Trust-Score dimensions, proactively offering "Alumni-Ambassador" status — exclusive early access to new itineraries, private events, and referral benefits — in exchange for active community advocacy.

## 3. Data Schema: `Alumni_Engagement_Profile`

```json
{
  "profile_id": "AEP-77221",
  "traveler_id": "TRAVELER_ALPHA",
  "alumni_cohort": "WARM_ALUMNI",
  "last_trip_date": "2024-09-15",
  "last_trip_id": "AMALFI-2024-09",
  "re_engagement_trigger": "TRIP_ANNIVERSARY_APPROACHING",
  "memory_crystal_hook": "PRIVATE_BOAT_DAY_AMALFI",
  "outreach_message_generated": true,
  "ambassador_status_offered": false,
  "re_engagement_status": "OUTREACH_SENT"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Specificity-Over-Volume' Standard**: Alumni outreach MUST be highly specific and Memory-Crystal-anchored. Generic "We miss you" campaigns are prohibited — they signal the agency doesn't actually remember the traveler.
- **Rule 2: The 'Frequency-Discipline' Rule**: Cold and Cool Alumni MUST receive maximum 2 outreach attempts per year. Over-messaging a lapsed traveler accelerates unsubscribe behavior.
- **Rule 3: The 'Unsubscribe-Dignity' Commitment**: If an Alumni unsubscribes or indicates they don't wish to be contacted, the agent MUST immediately and permanently cease outreach — with a graceful acknowledgment of the relationship.

## 5. Success Metrics (Alumni)

- **Alumni-Re-Engagement-Rate**: % of outreach campaigns that result in a new booking within 6 months.
- **Alumni-vs-Acquisition-Cost-Ratio**: Revenue per re-engaged alumni vs. revenue per newly acquired traveler (ROI comparison).
- **Ambassador-Referral-Volume**: Number of new traveler introductions generated through Alumni-Ambassador activations per year.
