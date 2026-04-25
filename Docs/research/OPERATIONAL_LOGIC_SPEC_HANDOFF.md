# Operational Logic Spec: Handoff Integrity (The Dead Man's Switch)

## 1. Scenario Context (OE-003)
An AI agent detects a critical failure (e.g., flight cancellation) and escalates to a human agent. However, the human agent is unavailable (after-hours, mass-outage, or negligence). The system must have a "Dead Man's Switch" to take autonomous action if the SLA is breached during a crisis.

## 2. Playbook Logic: The "Risk Budget" Protocol

### Phase 1: Escalation & SLA Monitoring
- **Trigger**: `CRITICAL` suitability flag or `SUPPLIER_FAILURE` event.
- **Logic**:
  - Escalation to `Owner` and `PrimaryAgent`.
  - Set **Crisis SLA**: 15 minutes (configurable).
  - Continuous heartbeat check of the "Review Queue".

### Phase 2: The "Dead Man's Switch" (Autonomous Trigger)
- **Logic**:
  - If SLA expires AND `Risk_Score > Threshold`:
    - The AI assumes **"Temporary Operational Authority"**.
    - **Risk Budgeting**: The AI is authorized to spend up to **X%** of the original trip cost (or $Y) to secure a recovery option.
    - **Action**: Execute the "Next Best Option" (e.g., book the only remaining seat on the next flight).

### Phase 3: Post-Autonomous Audit
- **Logic**:
  - The AI logs a `CRITICAL_AUTONOMOUS_ACTION` event.
  - The `IntegrityWatchdog` flags the trip for "Post-Mortem Review".
  - Notification sent to Owner: "Autonomous action taken due to SLA breach during crisis."

---

## 3. 11-Dimension Quality Audit (Playbook Evaluation)

| Dimension | Evaluation | Status |
| :--- | :--- | :--- |
| **Code** | Requires a "Heartbeat" background task in `watchdog.py`. | 🟡 |
| **Operational** | Clear visibility of "AI in Control" state on the dashboard. | ❌ |
| **User Experience** | Traveler is not left stranded because an agent was sleeping. | ✅ |
| **Logical Consistency** | "Risk Budget" must be per-customer or per-trip (High-value clients get higher budgets). | ✅ |
| **Commercial** | Autonomous spend protects against $10,000 "Disruption Claims" by spending $500 on a flight now. | ✅ |
| **Data Integrity** | Every autonomous action must have a "Logical Rationale" recorded in the audit log. | ✅ |
| **Quality & Reliability** | Fallback: AI *never* cancels a non-refundable booking autonomously without 100% confirmation of failure. | ✅ |
| **Compliance** | Liability check: Who is responsible for an autonomous error? (Policy: Agency accepts liability). | 🟡 |
| **Operational Readiness** | Owner must configure the "Risk Budget" before turning this on. | ❌ |
| **Critical Path** | Dependent on `Autonomous_Booking_Enabled` flag in `SettingsPanel`. | 🟡 |
| **Final Verdict** | **High Leverage**: Essential for "True" 24/7 autonomous operations. | **🟡 Partial** |

---

## 4. Open Questions for Research
- **Q1**: What happens if the AI takes an autonomous action that is *worse* than what the human would have done?
- **Q2**: Should the AI "Call" the traveler autonomously via Voice AI if the human agent doesn't respond?
