# Customer Communication Preferences — Master Index

> Research on notification channel management, frequency controls, quiet hours, opt-in/opt-out systems, and regulatory compliance for customer communications for the Waypoint OS platform.

---

## Series Overview

This series covers customer communication preferences — the system that lets customers control how, when, and what the agency communicates. From channel selection (WhatsApp, email, SMS, phone, app) and frequency controls (daily, weekly, important-only) to quiet hours and regulatory compliance (DPDP Act, TRAI DND), the preference center respects the customer's wishes while ensuring critical trip information is always delivered.

**Target Audience:** Product managers, marketing managers, compliance officers

**Key Insight:** 70% of customer unsubscribes happen after receiving irrelevant messages at inconvenient times. A preference center that lets customers choose "WhatsApp only, important updates, no marketing" reduces unsubscribe rates by 60% while maintaining engagement for messages that matter. Respect for customer preferences is the best retention strategy.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [COMM_PREFS_01_CENTER.md](COMM_PREFS_01_CENTER.md) | Preference center (channels, frequency, quiet hours, content), notification engine (transactional, reminder, marketing, engagement), smart scheduling, regulatory compliance (DPDP Act, TRAI DND, WhatsApp policy) |

---

## Key Themes

### 1. Customer Controls, System Respects
The customer decides how they want to be communicated with. The system respects those preferences rigorously — no "just this once" exceptions for marketing messages.

### 2. Critical Messages Always Deliver
Payment reminders, document deadlines, emergency alerts — these are always sent regardless of preference settings. The customer can choose the channel, but not whether they receive critical information.

### 3. One Channel Per Message
Never send the same message on WhatsApp, email, and SMS simultaneously. Pick the customer's preferred channel and use it. Multiple channels for the same message feels like spam.

### 4. Compliance Is Built In, Not Bolted On
DPDP Act consent, TRAI DND compliance, WhatsApp Business policies, and unsubscribe management are system-level requirements, not afterthoughts. Every message respects all applicable regulations automatically.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| WhatsApp Business (WHATSAPP_BIZ_*) | WhatsApp channel integration |
| Email Marketing (EMAIL_MKTG_*) | Email channel with preference integration |
| Pre-Trip Preparation (TRAVEL_PREP_*) | Checklist reminder delivery |
| Payment Processing (PAYMENT_PROCESSING_DEEP_DIVE_*) | Payment reminder triggers |
| PII Detection (PII_DETECT_*) | Communication preference data as PII |
| Customer Onboarding (CUSTOMER_ONBOARD_*) | Initial preference capture during onboarding |
| Marketing Automation (MARKETING_AUTOMATION_*) | Marketing message delivery with preference checks |
| Notification & Messaging (NOTIFICATION_MESSAGING_*) | Notification infrastructure |

---

**Created:** 2026-04-30
