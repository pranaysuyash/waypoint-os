# Neural Spec: BCI-Speed & Sub-Perceptual Agency (NEURAL-001)

**Status**: Research/Draft
**Area**: Brain-Computer Interface & Neural Logistics

---

## 1. The Problem: "The Decision Latency"
Even with "Predictive-Agency," the "Human-in-the-Loop" approval process (notification -> reading -> clicking) takes 15-60 seconds. In a "Hyper-Fluctuating" crisis (e.g., seats disappearing in milliseconds), this latency is a failure. Furthermore, constant notifications cause "Decision-Fatigue" for the traveler.

## 2. The Solution: 'Implicit-Acceptance-Loop' (IAL)

The IAL allows the agent to use "Sub-Perceptual" neural signals to secure "Approval" without requiring conscious action from the traveler.

### Neural Actions:

1.  **Visual-Cortex-Projection**:
    *   **Action**: The agent projects a "Flash-Visual" of the proposed re-booking (e.g., a simple route map) directly into the traveler's augmented/neural vision.
2.  **Affirmative-Signal-Capture**:
    *   **Action**: Monitoring for "N200/P300" ERP signals (Event-Related Potentials) which indicate "Recognition and Acceptance" of the stimulus.
3.  **Neural-Calm-Tuning**:
    *   **Action**: If the BCI detects "Amygdala-Spike" (Fear/Stress), the agent autonomously suppresses the "Notification-Detail" and only presents the "Resolution-Outcome" to maintain traveler psychological stability.

## 3. Data Schema: `Neural_Approval_Packet`

```json
{
  "request_id": "NEURAL-SYNC-8811",
  "decision_node": "REBOOK_LH_404",
  "neural_stimulus": "ROUTE_MAP_OVERLAY_05",
  "observed_signal": {
    "type": "P300_ACCEPTED",
    "confidence": 0.98,
    "latency_ms": 250
  },
  "verdict": "EXECUTE_ACTION",
  "traveler_awareness_level": "SUB_PERCEPTUAL"
}
```

## 4. Key Logic Rules

- **Rule 1: Hard-Veto-Override**: A "Conscious-Veto" (e.g., the traveler says "No" or manually cancels) ALWAYS overrides a "Neural-Implicit" approval.
- **Rule 2: Baseline-Integrity**: Implicit approval is only authorized for "Low-Stakes" or "Time-Critical" decisions (e.g., seat selection, 1:1 route swaps). High-stakes changes (e.g., +$10k cost) require "Full-Conscious-Consent."
- **Rule 3: Privacy-Neural-Wall**: The agent only reads "Specific-ERP-Signals" related to the stimulus; it is strictly prohibited from "General-Thought-Capture" or "Emotional-Data-Logging" beyond the decision loop.

## 5. Success Metrics (Neural)

- **Approval-Latency**: Reduction in average decision time from seconds to milliseconds.
- **Decision-Fatigue-Reduction**: % reduction in "Manual-Notification-Count" for the traveler.
- **Signal-Accuracy**: % of "Implicit-Approvals" that were NOT later regretted by the traveler.
