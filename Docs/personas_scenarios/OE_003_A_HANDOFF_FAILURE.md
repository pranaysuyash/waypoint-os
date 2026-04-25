# OE-003-A: The '3-AM-Silent-Switch'

**Persona**: Traveler (S1) + Junior Agent (P3)
**Scenario**: A traveler's flight is cancelled in the middle of the night. The AI escalates to the human agent, but the agent is asleep and misses the 15-minute SLA. The AI must activate its "Dead Man's Switch" and take autonomous recovery action.

---

## 1. Situation

- **Traveler**: Sarah Jenkins (Solo business traveler).
- **Time**: 3:15 AM (Agent's local time).
- **Problem**: Sarah's flight from New York (JFK) to London (LHR) is cancelled due to a mechanical issue. She is at the gate.
- **Urgency**: `CRITICAL`. If she doesn't get on the 4:30 AM flight, she misses a $1M board meeting.

### What is happening now
- The AI detects the cancellation.
- The AI escalates to the "Junior Agent" (P3) and the "Owner" (P2).
- Neither human responds. The 15-minute "Crisis SLA" is ticking.

---

## 2. What the System Should Do

### Step 1: SLA Monitoring & Breach
- **Watchdog Action**: Monitor the `ReviewQueue`.
- **Logic**: If `Time_Since_Escalation > 15m` AND `Urgency == CRITICAL`:
  - Trigger **"Autonomous Authority Mode"**.

### Step 2: Risk Budget Allocation
- **System Action**: AI checks the `Risk_Budget` for Sarah Jenkins (Gold Member).
- **Budget**: $1,500.
- **Action**: The AI finds one last seat on a Delta flight departing at 4:30 AM for $1,200.
- **Execution**: The AI auto-books the ticket, voids the original, and issues the new boarding pass.

### Step 3: Crisis Resolution & Handoff Brief
- **Communication**: AI sends Sarah a message: "I noticed your flight was cancelled and your agent is currently offline. I've autonomously re-booked you on Delta DL123 at 4:30 AM to ensure you make your meeting. Details attached."
- **Internal Note**: "Autonomous action taken at 3:31 AM due to SLA breach. Risk budget used: $1,200."

---

## 3. Operational Logic & Rules

- **Rule 1**: The Dead Man's Switch ONLY activates for `CRITICAL` urgency where a delay would cause irreversible loss.
- **Rule 2**: The AI must prioritize "Same Carrier" then "Same Alliance" then "Competitor" based on cost/speed.
- **Rule 3**: The AI must verify "Financial Sufficiency" (Risk Budget) before committing funds.

---

## 4. Success Criteria

- **Safety**: Traveler arrives in time for her meeting.
- **Accountability**: A detailed "Autonomous Rationale" is available for the agent to review at 9 AM.
- **Financial**: Spend is within the approved member-level risk budget.

---

## 5. Case Study Execution Plan (Future)

- **Input**: `CRITICAL` disruption event + `Delayed_Human_Response` simulator.
- **System Trace**: Verify the transition from `Escalated` -> `SLA_Breach` -> `Autonomic_Action`.
- **Verification**: Ensure the `AuditStore` records the "Logical Rationale" for the specific flight choice.
