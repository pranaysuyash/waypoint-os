# UNIFIED_COMMUNICATION_AND_CHANNEL_STRATEGY

## 1. How Customers Communicate (The "Front Door")
Frontier Agency OS supports an omnichannel intake model, moving beyond single-platform reliance.

### A. Core Channels
- **WhatsApp (Primary)**: Messaging-first interaction. Customers send voice notes, photos of passports, and text queries.
- **Email**: Formal documentation (Confirmations, Invoices, Itineraries).
- **Client Portal (Browser-based)**: For complex comparisons, document uploads, and secure payments.
- **SMS**: Critical time-sensitive alerts (e.g., "Driver is here", "Flight delayed").

### B. Input Types
- **Unstructured**: Messy chat logs, "Thinking out loud" voice notes.
- **Structured**: Form-fills for preferences, passport data, and payment details.
- **Visual**: Screenshots of competitor quotes, photos of physical documents.

---

## 2. Data Capture & Extraction Logic
How the system turns "Noise" into "Actionable Data".

### A. The "Intake Funnel"
1. **Ingestion**: Messages from all channels flow into a unified `CommunicationThread`.
2. **Entity Extraction (NB01)**: AI identifies names, dates, budgets, and "Vibes" (Preferences).
3. **Ghost Processing**: The system autonomously clarifies missing info (e.g., "Which city in Italy?").
4. **Validation**: PII is verified (e.g., Passport expiry check).

### B. The "Dual-Sided" Output
The system captures data into two separate streams:
- **Traveler-Safe View**: A polished, "Branded" proposal.
- **Operator View (Spine)**: Full margin breakdown, net costs, and risk scores.

---

## 3. Communication Playbooks

| Phase | Channel | System Action | Goal |
|-------|---------|---------------|------|
| **Inquiry** | WhatsApp | AI Clarification Loop | Get to "Feasible Package" fast. |
| **Proposal** | Secure Link | Interactive Comparison | Get traveler to click "Confirm Option A". |
| **Booking** | Email + Portal | Doc Capture | Collect Passports/Payments securely. |
| **In-Trip** | WhatsApp + SMS | Ghost Concierge | Proactive disruption management. |
| **Post-Trip**| WhatsApp | Feedback Loop | Capture sentiment for loyalty scoring. |

---

## 4. Technical Channel Matrix

| Channel | Integration | Sync Type | Data Weight |
|---------|-------------|-----------|-------------|
| **WhatsApp** | WATI / Official API | Async | High (Chat Context) |
| **Email** | Postmark / Resend | Sync | Medium (Formal Docs) |
| **Portal** | Next.js / Clerk | Real-time | Low (Interaction Logs) |
| **SMS** | Twilio | Sync | Minimal (Alerts) |

---

## 5. Next Implementation Threads
- **[ ]** Wire the `CommunicationThread` model to the backend.
- **[ ]** Build the "Copy-for-WhatsApp" formatter in the Output Panel.
- **[ ]** Implement the `shareToken` secure link generator.
