# Domain Knowledge: Communication Compliance & Consent

**Category**: Communication & Data Intake Architecture  
**Focus**: The legal and ethical guardrails for capturing and storing traveler data.

---

## 1. GDPR & CCPA "Right to be Forgotten"
- **Logic**: A traveler has the legal right to ask the agency to delete all their data.
- **The Complexity**: The agency must delete CRM data but **MUST KEEP** financial/tax data (e.g., invoices) for 7 years.
- **SOP**: A **"Tiered Deletion"** protocol. PII (Names/Passports) are deleted; Financial records are "Anonymized."

---

## 2. "Privacy by Design" in Chat
- **Logic**: Chat logs (WhatsApp/Signal) often contain PII.
- **SOP**: Automated "PII Scrubbing" of chat logs before they are stored in the long-term archive.

---

## 3. Explicit vs. Implicit Consent
- **Logic**: Recording a phone call or capturing a location (via a travel app).
- **SOP**: **"Double Opt-in."** The client must click a "Consent Link" sent via email/chat before the agent can activate high-stakes tracking or biometric capture.

---

## 4. Sub-processor Transparency
- **Logic**: The agency uses 10 different APIs (GDS, Hotel beds, Weather, Security).
- **SOP**: Maintaining a **"Data Map"** of where the traveler's data goes. "Your name was shared with [Hotel X] and [Airline Y] for the purpose of booking."

---

## 5. Proposed Scenarios
- **The "Deletion" Request**: A high-profile client has a falling out with the agency and demands "Immediate Deletion" of all records. The agent must explain what can be deleted (Preferences/Chat) and what must stay (BSP Invoices/Tax records).
- **The "Leaked" Chat Log**: A junior agent exports a chat log to a PDF and sends it to the wrong client. This is a **"Major Breach."** The agent must report it to the DPO (Data Protection Officer) within 72 hours.
- **Consent Withdrawal**: A client withdraws consent for "Location Tracking" mid-trip. The agent must immediately "Kill the Feed" even if it makes the client harder to protect.
- **The "Minor" traveler**: Capturing data for a child. The agent must secure **"Parental Consent"** via a separate, verified channel.
