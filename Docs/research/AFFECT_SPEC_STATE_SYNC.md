# Affective Spec: Emotional State-Sync (AFFECT-001)

**Status**: Research/Draft
**Area**: Affective Computing & Human-Agent Symbiosis

---

## 1. The Problem: "The Tone-Deaf Agent"
An agent that provides "Perfect Logic" (e.g., "You have missed your flight; please walk 2km to the next terminal") to a traveler who is experiencing an anxiety attack or extreme fatigue is a failure. The agent must "Sync" its internal operational state with the traveler's biological state.

## 2. The Solution: 'Emotional-Resonance-Loop' (ERL)

The ERL protocol adjusts the agent's "Logic-Gates" and "Comm-Modality" based on real-time affective telemetry.

### Resonance States:

1.  **State: STABILIZE (High Stress/Panic)**:
    *   **Action**: Simplify information to "Binary-Choices" (Yes/No). Use low-urgency, calm linguistic patterns. Delay "Cost/Complex" decisions.
2.  **State: SUSTAIN (High Fatigue)**:
    *   **Action**: Prioritize "Sleep/Recovery" nodes. Auto-book premium airport lounges or near-gate hotels even if they exceed standard budget.
3.  **State: EMPOWER (Standard/Executive)**:
    *   **Action**: Provide "High-Density" information. Present 3+ recovery options. Use "Efficiency-Focused" language.

## 3. Data Schema: `Affective_Sync_Status`

```json
{
  "sync_id": "ERL-5566",
  "traveler_state": {
    "stress_index": 0.88,
    "fatigue_index": 0.72,
    "cognitive_load": "MAX_CAPACITY"
  },
  "agent_response_mode": "STABILIZE",
  "logic_gate_overrides": [
    {
      "gate": "MAX_WALK_DISTANCE",
      "original": 2000,
      "override": 500
    },
    {
      "gate": "MIN_HOTEL_STAR_RATING",
      "original": 3,
      "override": 5
    }
  ],
  "comm_modality_shift": "HAPTIC_ONLY"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Panic-Stop'**: If `stress_index` > 0.90, the agent MUST stop providing itinerary updates and switch to "Safety-Stabilization" mode (e.g., "I've handled everything. Sit down. I'll alert you when it's time to move").
- **Rule 2: Fatigue-Weighted Routing**: If `fatigue_index` > 0.70, the agent is authorized to spend up to 200% of the "Wait-Time-Budget" to secure a "Bed" instead of a "Chair."
- **Rule 3: Biological Verification**: State-Sync requires 2+ independent sensory signals (e.g., Heart Rate + GPS Jitter + Typing Speed) to prevent "False-Positive" state shifts.

## 5. Success Metrics (Symbiosis)

- **Stress Reduction Rate**: Average drop in traveler `stress_index` after agent "Stabilization" intervention.
- **Decision Compliance**: % of agent-recommended "Recovery-Nodes" accepted by the traveler during high-stress events.
- **User Satisfaction (Subjective)**: "The agent felt like it knew exactly how I was feeling."
