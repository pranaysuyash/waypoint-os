# Fin Spec: Agentic 'Autonomous-Rate-Intelligence' Feed (FIN-REAL-035)

**Status**: Research/Draft
**Area**: Real-Time Rate Monitoring, Price Anomaly Detection & Autonomous Repricing

---

## 1. The Problem: "The Rate-Opacity-Loss"
Travel pricing is one of the most dynamic markets on earth — airfares change hundreds of times per day, hotel rates shift with occupancy algorithms, tour operators run flash promotions with 24-hour windows. Agencies booking without continuous rate intelligence are systematically leaving money on the table: confirming a flight at $1,200 that dropped to $890 two days later, or missing a hotel flash sale that would have saved the traveler $600. Without "Rate-Intelligence," the agency's pricing decisions are always backward-looking.

## 2. The Solution: 'Market-Rate-Protocol' (MRP)

The MRP acts as the "Rate-Arbitrage-Engine."

### Rate Intelligence Actions:

1.  **Continuous-Rate-Ingestion**:
    *   **Action**: Continuously ingesting rate feeds across all active and pending bookings — monitoring flight prices on confirmed routes, hotel rates on confirmed properties, and tour operator pricing on confirmed activities — for both forward-looking opportunities and post-booking savings.
2.  **Price-Drop-Detection**:
    *   **Action**: When a confirmed booking's rate drops by more than a configurable threshold (e.g., >$150 flight price drop, >$80/night hotel rate drop), the agent alerts the agency with a "Reprice-Opportunity" — including the rebook cost, any change fees, and the net saving calculation.
3.  **Flash-Sale-Window-Capture**:
    *   **Action**: Detecting "Flash-Sale-Windows" — rate anomalies that are statistically below baseline for a given route/property/date combination — and alerting the agency in real-time to capture the window before it closes.
4.  **Historical-Rate-Baseline-Modeling**:
    *   **Action**: Building historical rate baselines for all frequently booked routes and properties — enabling the agent to distinguish genuine anomalies from seasonal pricing patterns and prevent false-positive alerts.

## 3. Data Schema: `Rate_Intelligence_Alert`

```json
{
  "alert_id": "MRP-88221",
  "booking_id": "JAPAN-CIRCUIT-2026",
  "component_type": "FLIGHT",
  "route": "LHR-NRT",
  "original_rate_usd": 1240,
  "current_rate_usd": 890,
  "rate_drop_usd": 350,
  "change_fee_usd": 85,
  "net_saving_usd": 265,
  "rebook_window_hours": 18,
  "historical_baseline_deviation": -0.28,
  "alert_type": "REPRICE_OPPORTUNITY",
  "status": "AWAITING_AGENCY_DECISION"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Net-Saving-Threshold'**: Reprice-Opportunity alerts MUST only fire when the net saving (after change fees and rebook costs) exceeds a configurable minimum (e.g., $100). Below-threshold opportunities create alert fatigue without meaningful value.
- **Rule 2: The 'No-Autonomous-Rebook' Rule**: The agent MUST NOT autonomously rebook a confirmed component without explicit agency owner approval. Rate-Intelligence is advisory; rebooking is a human decision.
- **Rule 3: The 'Flash-Sale-Time-Stamp'**: All Flash-Sale-Window alerts MUST include a "Window-Expiry-Estimate" so the agency knows how long they have to act. Time-expired alerts that weren't acted on MUST be archived, not silently dropped.

## 5. Success Metrics (Rate)

- **Reprice-Savings-Per-Year**: Total dollar value of post-booking repricing savings captured across all agency clients.
- **Flash-Sale-Capture-Rate**: % of Flash-Sale-Window alerts that result in a successful booking within the window period.
- **Alert-Precision-Rate**: % of Reprice-Opportunity alerts where the agency chose to act (high precision = low alert fatigue).
