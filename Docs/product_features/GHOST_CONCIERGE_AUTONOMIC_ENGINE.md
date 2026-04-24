# FEATURE: Ghost Concierge Autonomic Engine

## 1. Business Purpose
The **Ghost Concierge** is designed to eliminate the "Last-Mile Anxiety" of travel by automating low-risk, high-frequency logistical checks without human intervention. This increases agent capacity by 40% and ensures travelers feel "watched over" 24/7.

## 2. User POV
- **Traveler**: Receives proactive confirmations (e.g., "Your driver is 5 mins away") without having to ask.
- **Agent**: Doesn't have to wake up at 3 AM to check if a client in a different timezone made it to their hotel.

## 3. Internal Logic & Workflows

### A. The "Silent Watch" Loop
The engine runs as a background process monitoring the `GhostWorkflow` table.
1. **Event Listener**: Detects upcoming trip milestones (T-minus 2 hours to flight, T-plus 30 mins to landing).
2. **Action Dispatch**: Pings a supplier API or automated bot to verify status.
3. **Status Update**: If "OK", silently logs the success and sends a "Reassurance Ping" to the traveler if configured.

### B. Autonomic Escalation (The "Broken Ghost" Protocol)
If the Ghost Engine detects a failure:
1. **Ambiguity Filter**: If the driver doesn't answer the ping, wait 5 mins and retry.
2. **Severity Score**: If the 2nd retry fails, calculate severity (e.g., "Client stranded at airport" = P0).
3. **Human Handoff**: Instantly notify the P2 (Agent) or P1 (Owner) with a `HandoffBrief` containing:
    - Attempted actions.
    - Detected failure.
    - Recommended fix (e.g., "Call alternative driver +55...").

## 4. Technical Constraints
- **Autonomy Levels**: Agencies can set "Autonomy Thresholds" (e.g., "Only automate transfers < $100").
- **Privacy**: The Ghost Engine only accesses the minimum necessary PII (Name, Phone, Flight #).
- **Auditability**: Every "Silent Action" must be recorded in the `AuditStore`.

## 5. Success Metrics
- **Automated Check-ins**: % of hotel/transfer confirmations completed without human touch.
- **Sentiment Recovery**: Sentiment score improvement after a Ghost-initiated reassurance.
- **Agent Sleep Quality**: Reduction in out-of-hours notifications for P2/P3.
