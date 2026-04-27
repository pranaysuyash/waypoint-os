# Con Spec: Agentic 'Trip-Simulation' Pre-Visualizer (CON-REAL-032)

**Status**: Research/Draft
**Area**: Pre-Booking Confidence, Cancellation Reduction & Decision Alignment

---

## 1. The Problem: "The Purchase-Regret-Gap"
A significant number of travel cancellations and post-trip disappointments happen because the traveler had a misaligned expectation of what the trip would feel like. They booked based on photos and bullet points, not on a genuine "Emotional-Preview" of the experience. This "Expectation-Gap" generates costly cancellations, chargebacks, and poor reviews — all of which damage the agency's reputation.

## 2. The Solution: 'Experiential-Preview-Protocol' (EPP)

The EPP acts as the "Imagination-Engine."

### Simulation Actions:

1.  **Narrative-Day-Simulation**:
    *   **Action**: Generating a vivid, first-person narrative "simulation" of each day of the proposed itinerary. The traveler reads what a day would actually feel and sound and smell like — not just what they'll do.
    *   **Example**: "Day 3 — You wake at 6am to the sound of the Kyoto temple bell drifting through your ryokan's paper screens. Breakfast is a lacquered tray of pickled vegetables, miso, and steamed rice served in complete silence. By 7:30am you're the only person in Fushimi Inari's thousand gates as the early light turns the vermillion red."
2.  **Friction-Point-Previewing**:
    *   **Action**: Proactively surfacing the "difficult" moments of the trip alongside the beautiful ones (e.g., "This trek is a 6-hour round trip on loose rock — here's what our past travelers said about the physical challenge").
3.  **Preference-Alignment-Check**:
    *   **Action**: After the traveler reads the simulation, the agent asks targeted alignment questions: "How did Day 3 feel for you? Too slow? Too active?" — and uses responses to refine the itinerary before booking.
4.  **Confidence-Score-Gate**:
    *   **Action**: Calculating a "Booking-Confidence-Score" based on the traveler's alignment responses. If it falls below 0.70, the agent suggests itinerary modifications before proceeding to payment.

## 3. Data Schema: `Trip_Simulation_Session`

```json
{
  "session_id": "EPP-55221",
  "traveler_id": "TRAVELER_ALPHA",
  "itinerary_id": "KYOTO-2026-01",
  "simulation_days_generated": 7,
  "alignment_responses_collected": 7,
  "booking_confidence_score": 0.88,
  "refinement_requests": 1,
  "status": "SIMULATION_APPROVED_PROCEED_TO_PAYMENT"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Honest-Preview' Standard**: Simulations MUST include the realistic friction and challenge points, not just the highlights. An exclusively euphoric simulation is misleading and increases post-trip disappointment.
- **Rule 2: Voice-Calibration-Requirement**: The narrative tone of the simulation MUST match the traveler's psychographic resonance language (from the DPP profile). A literary evocative traveler gets poetic prose; a pragmatic traveler gets clear, structured day briefs.
- **Rule 3: Simulation-Is-Not-Commitment**: The simulation phase MUST be clearly framed as exploratory. No financial commitments can be triggered during the simulation review.

## 5. Success Metrics (Simulation)

- **Cancellation-Rate-Reduction**: % decrease in cancellations for travelers who completed a trip simulation vs. those who did not.
- **Post-Trip-Satisfaction-Lift**: Difference in satisfaction scores between simulation-reviewed and non-reviewed trips.
- **Refinement-Acceptance-Rate**: % of itinerary refinements suggested post-simulation that travelers accepted, indicating simulation quality.
