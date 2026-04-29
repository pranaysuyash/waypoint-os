# Audit & Compliance — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, handling PII (passports, visas)  
**Approach:** Independent analysis — minimum viable compliance, not enterprise overkill  

---

## 1. The Core Problem: You're Handling HIGHLY Sensitive PII**

### What You Store (HIGH Risk)**

| Data Type | Risk Level | Why |
|-----------|------------|-----|
| **Passport numbers** | 🔴 CRITICAL | Identity theft, government ID |
| **Passport scan copies** | 🔴 CRITICAL | Full identity + address |
| **Visa documents** | 🔴 CRITICAL | Travel history, personal data |
| **Medical conditions** | 🔴 HIGH | Health PII, insurance risk |
| **Bank details** | 🔴 HIGH | Financial fraud risk |
| **Phone numbers** | 🟡 MEDIUM | WhatsApp, tracking |
| **Email addresses** | 🟡 MEDIUM | Marketing, tracking |
| **Travel history** | 🟡 LOW | Behavioral profile |

### Legal Frameworks That Apply**

| Law | Applies If | What It Means |
|-----|------------|--------------|
| **GDPR** | EU customers | Right to delete, export, consent |
| **DPDP Act 2023** | Indian customers | Consent, reasonable security, 3-year retention |
| **Sector 57 (India)** | Tour operators | Keep records 5 years for tax |
| **PCI DSS** | Store cards | ❌ You DON'T — tokenize only |

**My insight:**  
DPDP Act 2023 (India) is NEW — came into force 2024. Consent ARCHITECTURE is mandatory.  
GDPR applies if ANY EU customer books with you (even one German tourist).

---

## 2. My Lean Consent Model (DPDP / GDPR Compliance)**

### Consent Record (What You MUST Track)**

```json
{
  "consent_id": "string (UUID)",
  "customer_id": "string",
  "consent_version": "DPDP_2023_V1 | GDPR_2018_V1",
  
  // What they consented to
  "purposes": [
    {
      "purpose": "BOOKING_PROCESSING",  // Name, passport, visa for booking
      "consented": "boolean",  // true
      "consented_at": "string (ISO8601)",
      "withdrawn_at": "string | null"
    },
    {
      "purpose": "MARKETING_COMMUNICATIONS",  // WhatsApp promos
      "consented": "boolean",  // false (they said no)
      "consented_at": "string | null",
      "withdrawn_at": "string | null"
    },
    {
      "purpose": "WHATSAPP_COMMUNICATIONS",  // Enquiry replies
      "consented": "boolean",  // true
      "consented_at": "string (ISO8601)",
      "withdrawn_at": "string | null"  // They can withdraw
    }
  ],
    
  // Proof (required by law)
  "consent_mechanism": "CHECKBOX | WHATSAPP_REPLY | EMAIL_CLICK | SIGNED_FORM",
  "proof_url": "string | null",  // Screenshot of signed form
  "ip_address": "string | null",  // For web forms
  "user_agent": "string | null",
    
  // Withdrawal (right to withdraw)
  "withdrawal_requested_at": "string | null",
  "withdrawn_by": "CUSTOMER | AGENT",
  "withdrawal_method": "WHATSAPP_MESSAGE | EMAIL | IN_APP",
  "processed_at": "string | null"  // You deleted their data
}
```

**My insight:**  
`withdrawn_at` for marketing = STOP sending WhatsApp promos.  
GDPR "Right to be forgotten" = DELETE everything except tax-required data.

---

## 3. Data Retention Policy (What to Keep vs Delete)**

### DPDP Act + Sector 57 + GDPR Rules**

```json
{
  "retention_policy": {
    "booking_records": {
      "retain_years": 7,  // Sector 57 (tax audit)
      "legal_basis": "TAX_COMPLIANCE",
      "can_delete_early": "NO"  // Law says 7 years
    },
    "customer_pii": {
      "retain_years": 3,  // DPDP Act default
      "legal_basis": "CONSENT",
      "can_delete_early": "YES"  // If they withdraw consent
    },
    "communication_logs": {
      "retain_years": 3,  // Dispute resolution
      "legal_basis": "LEGITIMATE_INTEREST",
      "can_delete_early": "NO"  // Evidence for complaints
    },
    "payment_records": {
      "retain_years": 7,  // Tax + EMI tracking
      "legal_basis": "TAX_COMPLIANCE",
      "can_delete_early": "NO"
    },
    "vendor_communications": {
      "retain_years": 5,  // Contract disputes
      "legal_basis": "CONTRACT",
      "can_delete_early": "NO"
    }
  }
}
```

**My insight:**  
Sector 57 overrides DPDP — you MUST keep booking records 7 years for tax.  
`communication_logs` = evidence if customer says "I never agreed to ₹50k refund."

---

## 4. Audit Log (Who Changed What?)**

### Why This Matters (Disputes)**

Customer says: "I NEVER agreed to change my dates to June 20!"  
You check audit log: "Ah, YOU sent WhatsApp: 'Change to June 20 please' on April 15."

### My Audit Log Model**

```json
{
  "audit_id": "string (UUID)",
  "entity_type": "ENQUIRY | BOOKING | CUSTOMER | PAYMENT | COMMUNICATION",
  "entity_id": "string",  // enquiry_id, booking_id, etc.
    
  // What changed?
  "action_type": "CREATE | UPDATE | DELETE | VIEW | EXPORT | DELETE_REQUEST",
  "field_changed": "start_date | total_value | passport_number | ...",
  "old_value": "string | null",  // Masked if PII
  "new_value": "string | null",  // Masked if PII
    
  // Who did it?
  "acted_by_type": "AGENT | CUSTOMER | SYSTEM | VENDOR",
  "acted_by_id": "string",  // agent_id, customer_id
  "acted_at": "string (ISO8601)",
  "ip_address": "string | null",
    
  // Context
  "channel": "WHATSAPP | EMAIL | IN_APP",
  "session_id": "string | null",
  "user_agent": "string | null",
  "request_id": "string | null",  // For tracing API calls
    
  // Evidence (proof)
  "evidence_url": "string | null",  // Screenshot, email PDF
  "evidence_type": "WHATSAPP_SCREENSHOT | EMAIL_PDF | SYSTEM_LOG",
    
  // Data classification
  "contains_pii": "boolean",
  "pii_fields": ["passport_number", "phone_number"],
  "data_classification": "PUBLIC | INTERNAL | CONFIDENTIAL | RESTRICTED"
}
```

**My insight:**  
Mask PII in old_value/new_value: "passport: A12****89" not full number.  
`evidence_url` = WhatsApp screenshot of customer saying "Yes, change dates."

---

## 5. Encryption (Protecting PII at Rest)**

### What Needs Encryption (Solo Dev Reality)**

| Data | Encrypt? | How (Simple) |
|------|---------|--------------|
| **Passport numbers** | ✅ YES | AES-256 (PostgreSQL pgcrypto) |
| **Passport scan files** | ✅ YES | AES-256 (file-level) |
| **Visa documents** | ✅ YES | AES-256 (file-level) |
| **Medical conditions** | ✅ YES | AES-256 (DB column) |
| **Phone numbers** | 🟡 OPTIONAL | Hash if you want |
| **Email addresses** | ❌ NO | Not sensitive enough |
| **Booking amounts** | ❌ NO | Business data, not PII |

### My Lean Encryption Model**

```sql
-- Enable pgcrypto (PostgreSQL extension)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt passport number before storing
CREATE OR REPLACE FUNCTION encrypt_pii(data TEXT, secret_key TEXT) 
RETURNS TEXT AS $$
BEGIN
  RETURN encode(pgp_sym_encrypt(data, secret_key, 'cipher-algo=aes256'), 'base64');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Decrypt when needed (agent views passport)
CREATE OR REPLACE FUNCTION decrypt_pii(encrypted_data TEXT, secret_key TEXT) 
RETURNS TEXT AS $$
BEGIN
  RETURN pgp_sym_decrypt(decode(encrypted_data, 'base64'), secret_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Usage in app:
INSERT INTO travellers (passport_encrypted) 
VALUES (encrypt_pii('A1234567', current_setting('app.secret_key')));
```

**My insight:**  
`app.secret_key` should be **environment variable**, not in code.  
NEVER log decrypted PII — audit log stores masked values only.

---

## 6. GDPR Rights (EU Customers)**

### Right to Export (Data Portability)**

```json
{
  "export_request": {
    "request_id": "string (UUID)",
    "customer_id": "string",
    "requested_at": "string (ISO8601)",
    "requested_by": "CUSTOMER | AGENT",
    
    // Status
    "status": "PENDING | PROCESSING | READY | DOWNLOADED",
    "processed_by_agent_id": "string | null",
    "processed_at": "string | null",
    
    // Output
    "export_format": "JSON | PDF | EXCEL",
    "file_url": "string | null",  // Secure, expires in 7 days
    "expires_at": "string (ISO8601)",
    
    // What's included?
    "included_data": [
      "customer_profile",
      "enquiries_list",
      "bookings_list",
      "communication_logs",  // Last 3 years
      "payment_history"
    ],
    "excluded_data": [
      "vendor_communications",  // Internal
      "agent_notes"  // Internal
    ]
  }
}
```

### Right to Delete (Right to be Forgotten)**

```json
{
  "deletion_request": {
    "request_id": "string (UUID)",
    "customer_id": "string",
    "requested_at": "string (ISO8601)",
    
    // What CAN'T be deleted? (law)
    "legal_hold": {
      "booking_records": "7 years (Sector 57)",
      "payment_records": "7 years (tax)",
      "active_bookings": "Until travel completes"
    },
    
    // What WILL be deleted?
    "will_delete": [
      "passport_scan_file",  // PII, no legal hold
      "phone_number",  // Consent withdrawn
      "email_address",
      "communication_logs"  // After 3 years
    ],
    
    // Process
    "status": "PENDING | ANONYMIZING | COMPLETED | REJECTED",
    "rejection_reason": "string | null",  // "Active booking exists"
    "completed_at": "string | null",
    
    // Proof
    "deletion_certificate_url": "string | null",  // PDF for customer
    "audit_log_entry_id": "string"  // Link to audit trail
  }
}
```

**My insight:**  
"Right to delete" ≠ "delete everything." Tax records have LEGAL HOLD.  
Return `deletion_certificate_url` — PDF saying "We deleted your PII on DATE."

---

## 7. Data Breach Notification (What to Do If Hacked)**

### DPDP Act Requirement**

| Timeline | Action |
|----------|--------|
| **Within 72 hours** | Notify Data Protection Board of India |
| **Without undue delay** | Notify affected customers |
| **Immediately** | Contain the breach, forensic analysis |

### My Breach Log Model**

```json
{
  "breach_id": "string (UUID)",
  "detected_at": "string (ISO8601)",
  "detected_by": "SYSTEM | AGENT",
    
  // Scope
  "affected_customers_count": "integer",
  "affected_records_count": "integer",
  "pii_types_exposed": ["passport_number", "phone_number", "email"],
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
    
  // Cause
  "breach_type": "HACK | INSDER | LOSS | MISDELIVERY",
  "root_cause": "Unpatched server | Stolen laptop | WhatsApp screenshot leaked",
    
  // Actions taken
  "contained_at": "string | null",
  "notified_board_at": "string | null",  // DPDP requirement
  "notified_customers_at": "string | null",
    
  // Notifications sent
  "customer_notification_method": "WHATSAPP | EMAIL | SMS",
  "notification_count": "integer",
    
  // Reporting
  "incident_report_url": "string | null",  // For board
  "police_complaint_fir": "string | null"  // If criminal
}
```

**My insight:**  
In India, you MUST notify the **Data Protection Board** within 72 hours.  
WhatsApp message to customer: "Your passport data may be exposed. We're sorry."

---

## 8. Current State vs Compliance Model**

| Concept | Current Schema | My Lean Model |
|---------|---------------|-------------------|
| Consent tracking | None | `ConsentRecord` with purpose + withdrawal |
| Data retention | None | `retention_policy` (7yrs tax, 3yrs PII) |
| Audit log | None | `AuditLog` (who changed what, evidence URL) |
| Encryption | None | PGP symmetric (pgcrypto) for PII columns |
| GDPR export | None | `export_request` → JSON/PDF |
| GDPR delete | None | `deletion_request` → anonymize (not delete tax data) |
| Breach log | None | `breach_id` → notify board within 72h |

---

## 9. Decisions Needed (Solo Dev Reality)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Encrypt PII? | Yes / No | **YES** — passport data = HIGH risk |
| Audit logs? | Full / Critical only | **Critical only** — passport view, booking value change |
| Consent UI? | Full / Checkbox only | **Checkbox** — simple, DPDP compliant |
| GDPR export? | Full / Summary | **Summary** — PDF with key details |
| Auto-delete? | Yes / Manual | **Manual** — verify legal hold first |
| Breach notification? | Auto / Manual | **Template** — fill in blanks, send within 72h |

---

## 10. Next Discussion: Testing Strategy**

Now that we know **HOW to stay legal**, we need to discuss: **How to test this solo?**

Key questions for next discussion:
1. **Unit tests** — what's critical? (payment logic, visa rules?)
2. **Integration tests** — API + DB, WhatsApp mock?
3. **E2E tests** — Playwright? Too heavy for solo dev?
4. **AI testing** — how to test LLM outputs? (variance!)
5. **Solo dev reality** — NO QA team, YOU test everything
6. **Test data** — synthetic enquiries, fake passports?
7. **Regression** — did that bug fix break something else?

---

**Next file:** `Docs/discussions/testing_strategy_2026-04-29.md`
