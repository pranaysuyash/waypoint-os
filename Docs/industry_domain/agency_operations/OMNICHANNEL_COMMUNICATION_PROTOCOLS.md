# Domain Knowledge: Omnichannel Communication Protocols

**Category**: Communication & Data Intake Architecture  
**Focus**: Managing the flow of high-stakes information across fragmented chat, voice, and email channels.

---

## 1. The Channel Hierarchy
- **Level 1 (Crisis/Immediate)**: Phone Voice Call / Signal (Encrypted).
- **Level 2 (Active Booking)**: WhatsApp / WeChat / Telegram.
- **Level 3 (Documentation/Financials)**: Email.
- **SOP**: If a client sends a "Passport Photo" on WhatsApp, it must be immediately moved to the "Secure Vault" and deleted from the chat thread to maintain compliance.

---

## 2. Asynchronous "Stitching"
- **Logic**: A client starts a request on WhatsApp at 10 AM, follows up via Email at 2 PM, and calls at 6 PM.
- **SOP**: The agent must maintain a **"Single Thread of Truth"** in the CRM, linking the WhatsApp ID, Email address, and Phone number to one "Session ID."

---

## 3. The "Signal" Protocol (High-Security)
- **Logic**: For VVIPs or "Ghost" travelers, standard WhatsApp is too risky.
- **SOP**: Use of **Signal** with "Disappearing Messages" (e.g., 1-hour expiry) for sharing flight numbers or hotel suite details.

---

## 4. Voice to Text (Automated Minutes)
- **Logic**: Phone calls are often where the "Context" (the client's mood, the unspoken preference) is shared.
- **SOP**: All phone calls are transcribed (if legal) and an **"Executive Summary"** of the call is appended to the PNR notes.

---

## 5. Proposed Scenarios
- **The "Fragmented" Request**: A client sends half their flight details on WhatsApp and the other half on Email. The agent must "Stitch" them and verify the **"Conflict"** (e.g., Different dates on different channels).
- **The "Leaked" WhatsApp**: A client's phone is stolen. Their entire trip itinerary is in the WhatsApp chat. The agent must have enforced the **"Disappearing Message"** protocol or a "Code-word" system for sensitive data.
- **The "Signal" Dropout**: A client is in a country where Signal is blocked. The agent must provide an "Alternative Secure Bridge" (VPN) or move to a "Coded Email" protocol.
- **Urgent Voice "Panic"**: A client calls screaming because of a delay. The agent must use the **"De-escalation Script"** while simultaneously rebooking the flight in the GDS.
