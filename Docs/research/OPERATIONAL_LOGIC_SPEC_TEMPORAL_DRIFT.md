# Operational Logic Spec: Temporal Drift (OE-006)

**Status**: Research/Draft
**Area**: Information Freshness & Anticipatory Service

---

## 1. The Problem: "The Confirmation Paradox"
A trip is "Confirmed" at T-minus 6 months. At that moment, all information is true. By T-minus 2 days, the hotel's pool is closed for renovation, the airport lounge is under construction, and the "Fast Track" security gate has moved. The system still shows "Confirmed," leading to a degraded traveler experience upon arrival.

## 2. The Solution: Recursive Re-Validation (RRV)

The system must implement an **Automated Freshness Heartbeat** that re-validates every critical component of a trip at specific intervals.

### Heartbeat Intervals:

1. **T-Minus 30 Days**: Policy & Documentation Check (Visa, Passport validity).
2. **T-Minus 7 Days**: Major Infrastructure Check (Flight schedule, Hotel operational status).
3. **T-Minus 48 Hours**: Precision Check (Lounge status, Car service confirmation, weather-impacted rerouting).
4. **T-Minus 2 Hours**: Real-time Check (Gate changes, baggage belt assignments).

## 3. Data Schema: `Freshness_Audit`

```json
{
  "component_id": "HOTEL-PARIS-01",
  "last_validated": "2026-04-24T10:00:00Z",
  "status": "DRIFT_DETECTED",
  "drift_details": {
    "field": "amenities.pool",
    "old_value": "OPEN",
    "new_value": "CLOSED_FOR_RENOVATION",
    "source": "Web_Scraper_Hotel_Site"
  },
  "remediation_action": "NOTIFY_TRAVELER_WITH_ALTERNATIVE_GYM_PASS",
  "urgency": "LOW"
}
```

## 4. Key Logic Rules

- **Rule 1: Multi-Source Consensus**: Re-validation must use at least two sources (e.g., GDS + Hotel Website, or FlightRadar24 + Airline API).
- **Rule 2: Silent vs. Loud Correction**: 
  - If a flight time changes by < 15m, update silently.
  - If a critical amenity (Pool, Gym, Lounge) is lost, trigger a "Loud" notification with a "Value-Add" recovery (e.g., "The pool is closed, so I've added a complimentary spa credit to your booking").
- **Rule 3: Dependency Chaining**: If a flight re-validation shows a 3-hour delay, automatically trigger a re-validation of the "Airport Transfer" and "Hotel Late Check-in" components.

## 5. Success Metrics

- **Drift Detection Rate**: Percentage of "Arrival Surprises" caught by the system before the traveler discovers them.
- **Remediation Latency**: Time between drift detection and traveler notification/remediation.
- **No-Show Prevention**: Reduction in missed transfers or hotel cancellations due to uncommunicated flight changes.
