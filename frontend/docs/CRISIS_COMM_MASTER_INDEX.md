# Crisis Communication Protocol — Master Index

> Research on agency emergency communication, mass traveler notification, safety tracking, and post-crisis recovery for the Waypoint OS platform.

---

## Series Overview

This series covers the crisis communication protocol — the system and processes for communicating with active travelers during emergencies. From natural disasters and political unrest to health emergencies and mass transport disruptions, the protocol ensures every traveler is contacted, tracked, and assisted. The system combines automated mass notification with agent-driven personal coordination, escalating from WhatsApp to SMS to phone calls until every traveler is accounted for.

**Target Audience:** Operations managers, crisis coordinators, agency owners

**Key Insight:** During the 2023 Turkey-Syria earthquake, agencies with traveler tracking systems located and assisted all their customers within 4 hours. Agencies without systems spent 24-48 hours frantically calling hotels and embassies. The difference wasn't technology — it was preparedness. A crisis protocol that's practiced and ready activates in minutes, not hours.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [CRISIS_COMM_01_PROTOCOL.md](CRISIS_COMM_01_PROTOCOL.md) | Crisis types and severity classification, emergency broadcast system (WhatsApp/SMS/call), message templates, traveler safety tracking workflow, post-crisis recovery operations |

---

## Key Themes

### 1. Speed Is the First Metric
In a crisis, the first 30 minutes determine outcomes. Automated crisis detection and instant mass notification via WhatsApp (95%+ open rate in 5 minutes) means the agency reaches travelers before they panic. The agent's first message should arrive before the customer's frantic call.

### 2. Track Until 100% Accounted For
Every traveler must be marked CONFIRMED_SAFE. The tracking dashboard treats "no response" as actively dangerous — not "probably fine." Escalation to hotel concierge, embassy, and local authorities continues until every single traveler is accounted for.

### 3. Empathy Over Efficiency
Crisis communication is not the time for automated chatbots or templated responses. Each traveler's situation is unique — stranded at the airport vs. safe in hotel vs. needing medical help. Agent-led personal communication, supported by system tracking, is the right balance.

### 4. Rehearse or Fail
A crisis protocol that exists only on paper fails under pressure. Regular drills (quarterly tabletop exercises) where agents practice the notification workflow, tracking dashboard, and escalation procedures ensure the system works when it matters.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Trip Control Room (TRIP_CTRL_*) | Real-time trip monitoring feeds crisis detection |
| Traveler Companion App (TRAVELER_APP_*) | Emergency card and in-app crisis notifications |
| WhatsApp Business (WHATSAPP_BIZ_*) | Primary broadcast channel |
| Agency Insurance (AGENCY_INSURE_*) | Claims during crisis events |
| Support AI (SUPPORT_AI_*) | Chatbot pauses during crisis — human-only mode |
| Ops Playbook (OPS_PLAYBOOK_*) | Agent SOPs for crisis situations |
| Help Desk (HELP_DESK_*) | Ticket management during crisis volume spikes |

---

**Created:** 2026-04-30
