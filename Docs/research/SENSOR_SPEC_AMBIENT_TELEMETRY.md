# Sensor Spec: Ambient Sensory Agency (SENSOR-001)

**Status**: Research/Draft
**Area**: Physical-Digital Integration & Real-Time Telemetry

---

## 1. The Problem: "The Blind Agent"
Most agents only see the world through APIs (e.g., "The flight is delayed"). They don't know that the traveler is currently running through the terminal, has a heart rate of 140 BPM, and is 2 miles from the gate with 5 minutes to boarding. The "Decision" to hold a flight or book a backup depends on this "Physical Grounding."

## 2. The Solution: 'Sensory-Input-Bridge' (SIB)

The SIB streams real-time mobile/wearable telemetry into the agent's reasoning engine.

### Sensory Input Streams:

1.  **Locational Telemetry (GPS/Indoor-Positioning)**:
    *   **Action**: Determining "Distance-to-Gate" and "Movement-Velocity."
2.  **Biometric Stress Indicators (Wearable Integration)**:
    *   **Action**: Correlating high heart rate/respiratory rate with trip-disruption events to trigger "Calming-Comm" protocols (COMM-001).
3.  **Environmental Awareness (Audio/Haptic)**:
    *   **Action**: Detecting "High-Noise" levels (airport announcements) or "Impact-Events" (accidents) to adjust communication modality (e.g., switch from Voice to Haptic/Alert).

## 3. Data Schema: `Sensory_Telemetry_Packet`

```json
{
  "timestamp": "2026-05-10T14:10:00Z",
  "traveler_id": "T-9901",
  "locational": {
    "lat_long": [51.4700, -0.4543],
    "altitude": 25,
    "context": "LHR_TERMINAL_5",
    "dist_to_destination_m": 850,
    "velocity_m_s": 1.2
  },
  "biometric": {
    "heart_rate_bpm": 132,
    "stress_score": 0.85
  },
  "environmental": {
    "ambient_noise_db": 85,
    "network_quality": "WEAK_LTE"
  },
  "inferred_state": "RUSHING_TO_GATE_STRESSED"
}
```

## 4. Key Logic Rules

- **Rule 1: 'The Sprint' Threshold**: If velocity > 2.5 m/s and distance > 500m, trigger the **'Pre-emptive-Gate-Hold'** request or book the **'Instant-Backup-Flight'** if success probability < 10%.
- **Rule 2: Privacy-by-Default**: Sensory data is processed locally where possible and only "Inferred States" (e.g., "Stressed," "Moving") are sent to the central `Spine` to preserve PII.
- **Rule 3: Haptic-First Override**: If `ambient_noise_db` > 75, the agent defaults to "Critical-Haptic-Alerts" on the watch rather than attempting Voice/Chat communication.

## 5. Success Metrics (Grounding)

- **Intervention Timing**: Reduction in the time between "Physical-Delay" and "Digital-Recovery" (Target: < 30 seconds).
- **Communication Relevance**: % of alerts that were ignored due to "Physical-Infeasibility" (e.g., "Don't ask the traveler to re-book while they are sprinting").
- **Safety Response**: Speed of emergency initiation during "Impact/Fall" detection.
