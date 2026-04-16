# Discovery Gap Analysis: In-Trip Operations & Emergency Protocol

**Date**: 2026-04-16
**Gap Register**: #09 (P2 — in-trip is post-MVP but emergency routing exists)
**Scope**: Active trip monitoring, flight status, check-in confirmation, crisis/disaster response, rebooking cascades, pre-departure automation. NOT: cancellation/refund (#05), customer portal (#08).

---

## 1. Executive Summary

The system has a working `operating_mode=emergency` pathway (detection → decision → strategy → message → tests) that detects crisis keywords and routes to `STOP_NEEDS_REVIEW`. **But this is the intake/emergency triage only.** There is zero implementation of any post-booking operational capability: no active-trip states, no flight monitoring, no check-in confirmation, no daily check-in, no cascading rebooking, no 7 documented disaster-response workflows, and no incident logging. The TripStatus model stops at `BOOKED` — there are no active/in-progress/disrupted/emergency states.

---

## 2. Evidence Inventory

### What's Documented (20+ specific processes)

| Doc | What | Location |
|-----|------|----------|
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L133 | Travel advisory alerts (government warnings, weather) | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L139-143 | Flight monitoring, check-in confirmation, daily check-in, issue escalation, cascading rebooking | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L250-256 | 7 crisis types: natural disaster, political instability, pandemic, airline bankruptcy, hotel overbooking, medical evacuation, theft/loss | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L130-132 | Pre-departure: trip dossier, document delivery, D-1 reminder | Docs/ |
| `UX_MESSAGE_TEMPLATES` L546-566 | Full emergency flow: keyword detection → EMERGENCY mode → callback → incident log | Docs/ |
| `UX_AND_USER_EXPERIENCE` L136 | "24/7 automated triage + agent callback in 10 minutes" | Docs/ |
| `UX_MULTI_CHANNEL_STRATEGY` L761 | `send_emergency_alert()` function stub | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS` L153 | Traveler: "Flight cancelled, hotel won't check me in" → no emergency protocol | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS` L254 | Emergency protocol as P1 gap #12 | Docs/ |
| `MASTER_GAP_REGISTER` L135 | "During-trip monitoring: Flight status, check-in confirmation — Not modeled" | Docs/ |
| `SCENARIO_COVERAGE_GAPS` L93 | Scenario #24 "Medical Emergency During Trip" — entirely missing | Docs/ |
| `V02_GOVERNING_PRINCIPLES` L56,67 | `operating_mode=emergency` → `STOP_NEEDS_REVIEW` | Docs/ |

### What's Implemented

| Code | What | Status |
|------|------|--------|
| `extractors.py` L598 | Emergency keyword detection ("emergency", "urgent", "medical", "hospital", "evacuate") | **Working** — mode detection |
| `decision.py` L98 | `operating_mode: "emergency"` in DecisionResult | **Working** — data model supports it |
| `strategy.py` L266, L510-515, L671-673 | Emergency goals, actions, traveler message | **Working** — display only |
| `decision.py` L1070-1097 | `document_risk` flag checks passport/visa urgency | **Working** — intake-time only |
| `packet_models.py` L288 | `"emergency"` as valid operating mode | **Working** |
| Tests | Emergency mode E2E test | **Working** — tests detection, not resolution |
| `persistence.py` | `TripStatus` enum: NEW, BOOKED, CANCELLED | **INCOMPLETE** — no active/in-progress states |
| `UX_MULTI_CHANNEL_STRATEGY` L761 | `send_emergency_alert()` stub | **Stub** — function signature only |

### What's NOT Implemented

- No `IN_PROGRESS`, `ACTIVE`, `DISRUPTED`, `EMERGENCY` TripStatus states
- No `EMERGENCY_PROTOCOL` DecisionResult option (stops at `STOP_NEEDS_REVIEW`)
- No flight status monitoring or integration
- No check-in confirmation tracking
- No daily check-in flow
- No real-time issue escalation pipeline
- No cascading rebooking logic
- No travel advisory feed
- No pre-departure automation (D-7/D-3/D-1)
- No incident logging
- No "all travelers in country X" emergency query
- No emergency contact management (DMC phones, local emergency numbers)

---

## 3. Gap Taxonomy

### Structural Gaps

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **TR-01** | Active trip state model | TripStatus stops at BOOKED | All in-trip operations |
| **TR-02** | Emergency resolution options | Only STOP_NEEDS_REVIEW, no EMERGENCY_PROTOCOL | Crisis decision-making |
| **TR-03** | Flight status monitoring | None | Proactive disruption detection |
| **TR-04** | Pre-departure automation | None | Trip dossier delivery, D-7/D-3/D-1 reminders |
| **TR-05** | Incident logging | None (AuditStore doesn't log incidents) | Post-crisis review, learning loops |

### Computation Gaps

| Gap ID | What Needs Computing | Current State | Blocked By |
|--------|---------------------|---------------|------------|
| **TC-01** | Traveler location ("who is in country X?") | No trip state persistence | #02, TR-01 |
| **TC-02** | Flight disruption detection | No flight API integration | #07 (LLM for triage), external APIs |
| **TC-03** | Cascading rebooking impact | No component dependency graph | #01 (vendor data), TR-01 |
| **TC-04** | Crisis response recommendation | Only STOP_NEEDS_REVIEW | #07, TR-02 |

---

## 4. Phase-In Recommendations

### Phase 1: Active Trip States + Emergency Triage Enhancement (P1, ~2 days, blocked by #02)

1. Add `IN_PROGRESS`, `ACTIVE`, `DISRUPTED`, `COMPLETED` TripStatus states
2. Add `EMERGENCY_PROTOCOL` as DecisionResult option with structured options (rebook, evacuate, refund, insurance claim)
3. Wire existing `operating_mode=emergency` to produce structured recommendations instead of just `STOP_NEEDS_REVIEW`
4. Add incident logging to AuditStore for emergency events

**Acceptance**: Emergency inquiry produces structured options ("Rebook alternative flight", "File insurance claim") instead of just "connect with agent".

### Phase 2: Pre-Departure Automation (P2, ~3 days, blocked by #02, #03)

1. Add pre-departure milestone tracking (D-7 trip dossier, D-3 document delivery, D-1 reminder)
2. Wire to notification engine (#03) for automated sends
3. Add document checklist per destination (links to #10 visa management)

**Acceptance**: Agent gets automated reminders at D-7, D-3, D-1 with document checklist status.

### Phase 3: Flight Monitoring + Crisis Response (P3, ~5-7 days, blocked by external APIs)

1. Integrate flight status API (FlightAware/AviationStack) for active trips
2. Add "all travelers in country X" emergency query
3. Add 7 crisis response workflows (natural disaster, political, pandemic, airline bankruptcy, hotel overbooking, medical evacuation, theft)
4. Add emergency contact management per destination

**Acceptance**: System alerts agent when client's flight is delayed >2hrs. Agent can query "which travelers are in Thailand?" during crisis.

---

## 5-8. Key Decisions, Risks, Out of Scope

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Flight status source | (a) Manual entry, (b) AviationStack API, (c) None for MVP | **(a) Manual** for MVP — agent enters flight details, system tracks manually |
| Active trip state transitions | (a) Manual by agent, (b) Automated from flight data, (c) Hybrid | **(c) Hybrid** — agent confirms, system suggests |
| Emergency response hierarchy | (a) Agent handles alone, (b) Owner escalation for emergencies, (c) Configurable | **(b) Owner escalation** — emergencies always notify owner |
| Incident logging detail | (a) Minimal (event type + timestamp), (b) Full (event type, timestamp, actions, outcome), (c) Structured (full + follow-up) | **(b) Full** — type, timestamp, actions taken, outcome, resolution |

| Risk | Severity | Mitigation |
|------|----------|------------|
| Flight API costs | Medium | Manual entry for MVP. Add API in Phase 3 when ROI is proven. |
| False emergency detection | High | Existing safety.py patterns help. Add confirmation step before crisis mode. |
| Emergency response liability | High | System recommends, agent decides. Never auto-rebook without human confirmation. |

**Out of Scope**: Flight booking APIs, hotel API integrations, real-time weather/geopolitical monitoring, automated rebooking without human confirmation.