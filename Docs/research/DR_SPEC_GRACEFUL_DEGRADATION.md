# DR Spec: Graceful Degradation (DR-002)

**Status**: Research/Draft
**Area**: Resource Management & Operational Resilience

---

## 1. The Problem: "The Cascade Failure"
During a mass-disruption (e.g., global IT outage), the agency is hit with 100x the normal load. If the system tries to perform "Full Intelligence" for everyone, it will crash, leaving no one served.

## 2. The Solution: 'Capability-Priority-Matrix' (CPM)

The CPM autonomously shuts down "Non-Critical" services to preserve "Survival" functions.

### Degradation Tiers:

1.  **Tier 1 (Critical/Survival)**:
    *   **Features**: Flight/Hotel Re-booking, Safety Notifications, Emergency PII Access.
    *   **Priority**: **ALWAY_ON**.
2.  **Tier 2 (Operational/Enhanced)**:
    *   **Features**: CSAT Surveys, Marketing Emails, Social Sentiment Analysis.
    *   **Action**: Auto-Disable if system CPU > 80% or LLM latency > 10s.
3.  **Tier 3 (Intelligence/Premium)**:
    *   **Features**: 'Emotional Triage', 'Sustainability Ledger', 'Synthetic Scenario Generation'.
    *   **Action**: Auto-Disable if system load is in "Emergency-State."

## 3. Data Schema: `Degradation_Status`

```json
{
  "system_state": "DEGRADED_MODE",
  "trigger": "LLM_API_LATENCY_EXCEEDED",
  "active_tier": 1,
  "disabled_modules": [
    "analytics_aggregator",
    "emotional_triage_engine",
    "social_sentiment_watchdog"
  ],
  "resource_usage": {
    "cpu": 0.92,
    "mem": 0.78,
    "api_latency_ms": 12500
  },
  "estimated_recovery": "2026-05-10T16:00:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: Role-Aware Degradation**: High-priority travelers (VIPs, Medical cases) continue to receive "Full-Intelligence" services longer than standard travelers.
- **Rule 2: 'Lightweight' Inference Fallback**: Switch from complex reasoning models (e.g., Ultra) to fast, local models (e.g., Flash/Distilled) for re-booking logic during high load.
- **Rule 3: Queue-Throttling**: Automatically "Park" non-urgent traveler requests (e.g., "Change seat for flight in 3 months") in favor of urgent disruption handling.

## 5. Success Metrics (Resilience)

- **Service Continuity**: Zero downtime for "Tier 1" Survival functions.
- **Failure Isolation**: % of disruption events where non-critical service failure did NOT affect core re-booking.
- **Resource Efficiency**: Reduction in LLM token costs during high-load peaks by using "Lightweight" mode.
