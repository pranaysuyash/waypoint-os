# Supply Spec: Dynamic Vendor Reliability Tracking (SU-001)

**Status**: Research/Draft
**Area**: Supplier Scoring & Real-Time Filtering

---

## 1. The Problem: "The Static Preference Trap"
Most agencies use static "Preferred Vendor" lists that don't account for real-time failures. If a "Preferred" airline is currently experiencing a mass-strike or technical outage, it should NOT be the #1 recommendation.

## 2. The Solution: 'Supplier-Reliability-Index' (SRI)

The SRI is a dynamic score (0-100) updated in real-time based on live operational telemetry.

### SRI Calculation Factors:

1.  **On-Time Performance (OTP)**: (e.g., % of flights arriving within 15 mins of ETA).
2.  **Disruption Recovery Rate**: How effectively the vendor handles its own failures (e.g., % of travelers re-booked by the airline within 4 hours).
3.  **Sentiment Delta**: Real-time analysis of social/news sentiment for the brand.
4.  **Contractual Adherence**: % of bookings that are honored without modification or overbooking.

### Logic Rules for Filtering:

- **Threshold 1 (SRI > 80)**: **Green**. No restrictions.
- **Threshold 2 (SRI 50-80)**: **Yellow**. Show a "Reliability Warning" to the traveler/agent.
- **Threshold 3 (SRI < 50)**: **Red**. Auto-deprioritize. Move vendor to the bottom of the search or hide entirely if a comparable alternative exists.

## 3. Data Schema: `Vendor_SRI_Record`

```json
{
  "vendor_id": "AIR-LH",
  "vendor_name": "Lufthansa",
  "current_sri": 42,
  "status": "RED",
  "reason": "Mass Technical Outage at FRA Hub",
  "telemetry": {
    "otp_24h": 0.15,
    "cancellation_rate_24h": 0.65,
    "sentiment_score": -0.85
  },
  "last_updated": "2026-05-10T09:00:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: Region-Specific SRI**: A vendor may have high reliability globally but fail in a specific region (e.g., "Exclude Airline X only for arrivals at HKG due to local handling strike").
- **Rule 2: The 'Phoenix' Recovery**: SRI scores must have a "Cooldown Period." If a vendor stabilizes for 12 hours, the score begins to "Recover" automatically.
- **Rule 3: VIP Exclusion**: SRI filtering is STRICTER for VIP travelers (e.g., "Never suggest a Red-tier vendor for a Board Member").

## 5. Success Metrics (Reliability)

- **Disruption Avoidance**: % of travelers who avoided a disruption by choosing a high-SRI alternative.
- **Booking Integrity**: Reduction in "Supplier-Initiated Cancellations" for agency bookings.
- **Trust Rebound**: Increase in traveler confidence in the "AI-Curated" search results.
