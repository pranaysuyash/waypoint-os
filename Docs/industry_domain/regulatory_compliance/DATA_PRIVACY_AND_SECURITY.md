# Data Privacy and Security in Travel

Agencies handle highly sensitive PII (Personally Identifiable Information) and financial data.

---

## 1. Sensitive Data Categories

1. **Identity Data**: Full names, Passport numbers, Birth dates, National IDs.
2. **Financial Data**: Credit card details (PCI-DSS), Bank account info, Remittance records.
3. **Health Data**: Medical conditions, dietary allergies, accessibility needs.
4. **Behavioral Data**: Past destinations, spending patterns, traveler preferences.

---

## 2. Regulatory Frameworks

- **GDPR (Europe)**: "Right to be forgotten" after a trip is completed. Strict rules on sharing data with non-EU suppliers.
- **DPDP Act (India)**: New regulations on data processing, consent, and storage within national borders.
- **PCI-DSS**: Global standard for handling card payments. Agencies should **never** store CVV numbers or full credit card digits in plain text.

---

## 3. Agency Operational Security

- **WhatsApp Risks**: Sharing passport copies via WhatsApp is common but insecure. Data is trapped on individual agent phones.
- **The "Leaky" Agency**: When an agent leaves, they often take the "Traveler Database" (WhatsApp contacts/Excel) with them.
- **AI Safety**: Ensuring PII is redacted when sending data to LLMs for "Decision" or "Strategy" phases, unless necessary for the specific task.

---

## 4. Best Practices for the AI Agent

1. **Redaction**: Automatically blur/redact passport numbers in preview screens for unauthorized users (e.g., Junior Agents vs. Ops Leads).
2. **Consent Management**: Capture explicit traveler consent for storing health or identity data for future trips.
3. **Data Retention**: Automatically archive/delete sensitive documents 30 days after the trip return date.
4. **Audit Trail**: Every time a passport is viewed or downloaded, log the event in the `AuditStore`.
