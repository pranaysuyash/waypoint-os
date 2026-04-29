# PII Detection & Data Classification — Storage, Encryption & Lifecycle

> Research document for PII field-level encryption, key management, data retention policies, automated purging, and compliance automation for the Waypoint OS platform.

---

## Key Questions

1. **How do we implement field-level encryption for PII at rest?**
2. **What key management strategy protects encrypted PII?**
3. **How does automated data retention and purging work?**
4. **What compliance reporting is needed for PII handling?**

---

## Research Areas

### Field-Level Encryption Architecture

```typescript
interface FieldLevelEncryption {
  // Per-field encryption strategy for PII data
  encryption_strategy: {
    ENVELOPE_ENCRYPTION: {
      description: "AWS/GCP envelope encryption pattern adapted for application-level use";
      mechanism: {
        step_1: "Generate data encryption key (DEK) per tenant/agency";
        step_2: "Encrypt PII field values with DEK using AES-256-GCM";
        step_3: "Encrypt DEK with master key (KEK) stored in key vault";
        step_4: "Store encrypted DEK alongside encrypted data";
        step_5: "Decrypt DEK with KEK → decrypt data with DEK for authorized access";
      };
      rotation: "DEK rotated every 90 days; KEK rotated annually";
      performance: "1-3ms overhead per encrypt/decrypt operation";
    };

    FIELD_LEVEL_MAPPING: {
      phone_number: {
        tier: "TIER_3";
        algorithm: "AES-256-GCM with deterministic encryption for search";
        searchable: true;
        search_method: "HMAC-based searchable encryption (blind index)";
        display: "98***3210 (masked)";
      };

      email: {
        tier: "TIER_3";
        algorithm: "AES-256-GCM with deterministic encryption";
        searchable: true;
        search_method: "Lowercase + HMAC blind index";
        display: "r****@gmail.com";
      };

      full_name: {
        tier: "TIER_3";
        algorithm: "AES-256-GCM";
        searchable: true;
        search_method: "Phonetic hash (Soundex/Metaphone) for fuzzy match";
        display: "R**** S****";
      };

      passport_number: {
        tier: "TIER_4";
        algorithm: "AES-256-GCM (non-deterministic — different ciphertext each time)";
        searchable: false;
        access: "Decrypted only during active booking process";
        retention: "Trip duration + 30 days → auto-purge";
        display: "Never displayed in UI — [PROTECTED] badge";
      };

      aadhaar_number: {
        tier: "TIER_4";
        algorithm: "AES-256-GCM (non-deterministic)";
        searchable: false;
        access: "Decrypted only for government compliance (with audit trail)";
        retention: "Immediate purge after compliance use";
        display: "Never displayed — [PROTECTED] badge";
        legal_note: "Aadhaar can only be stored with explicit consent under Aadhaar Act";
      };

      credit_card_number: {
        tier: "TIER_4";
        algorithm: "NEVER STORED — tokenization only";
        storage: "Payment gateway token (Stripe/Razorpay reference)";
        display: "**** **** **** 1111 (last 4 digits only)";
        compliance: "PCI-DSS Level 1 compliance required";
      };
    };
  };

  // Key management
  key_management: {
    KEY_HIERARCHY: {
      master_key: "Stored in HSM or cloud KMS (AWS KMS / GCP KMS)";
      tenant_key: "One KEK per agency (derived from master key)";
      data_key: "One DEK per data classification batch (rotated every 90 days)";
      field_key: "Optional: per-field key for Tier 4 data (highest isolation)";
    };

    KEY_ROTATION: {
      scheduled: "DEK rotated every 90 days automatically";
      on_incident: "Immediate re-encryption of all data with new DEK on suspected breach";
      on_offboard: "Agency offboarding → destroy tenant key → all data becomes unreadable";
    };

    ACCESS_CONTROL: {
      encrypt: "Application service account (no human access)";
      decrypt_tier_3: "Authenticated agent with active session + MFA";
      decrypt_tier_4: "Specific business purpose (booking, compliance) + audit trail";
      key_admin: "Security team only, with MFA + approval workflow";
    };
  };
}

// ── Encryption status dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  PII Encryption — System Health                           │
// │                                                       │
// │  Encryption Coverage:                                 │
// │  Tier 3 fields encrypted: 9,812 / 9,812 (100%) ✅        │
// │  Tier 4 fields encrypted: 2,104 / 2,104 (100%) ✅        │
// │  Credit card tokenized:  487 / 487 (100%) ✅              │
// │  Unencrypted PII found: 0 ✅                              │
// │                                                       │
// │  Key Status:                                          │
// │  Master key: Active · Last rotated: 2026-01-15           │
// │  Tenant key (Raj Travels): Active · Rotated: 2026-03-01  │
// │  DEK batch #14: Active · Expires: 2026-06-28             │
// │  DEK batch #15: Pre-generated · Activates: 2026-06-28    │
// │                                                       │
// │  Retention Alerts:                                    │
// │  ⚠️ 47 Tier 4 records expire in next 7 days              │
// │  ⚠️ 3 credit card tokens expire this month                │
// │  [View Expiring Records] [Schedule Purge]                 │
// │                                                       │
// │  Access Log (last 24h):                               │
// │  Tier 3 decryptions: 342 (agent queries)                  │
// │  Tier 4 decryptions: 12 (booking process)                 │
// │  Failed decrypt attempts: 0 ✅                            │
// │                                                       │
// │  [Rotate Keys] [Audit Report] [Purge Now]                 │
// └─────────────────────────────────────────────────────┘
```

### Data Retention & Automated Purging

```typescript
interface DataRetentionPurging {
  // Retention policies and automated purging
  retention_policies: {
    ACTIVE_RELATIONSHIP: {
      tier_2: "Retain while customer is active + 3 years";
      tier_3: "Retain while customer is active + 1 year after last interaction";
      tier_4: "Retain only for active trip + 30 days post-trip";
      trigger: "Last booking or interaction date";
    };

    INACTIVE_CUSTOMER: {
      definition: "No interaction or booking for 12+ months";
      action_tier_2: "Anonymize (replace with statistical data)";
      action_tier_3: "Delete PII, keep booking history (destination, value, dates)";
      action_tier_4: "Purge immediately";
      notification: "30-day notice before deletion via WhatsApp/email";
    };

    RIGHT_TO_DELETE: {
      trigger: "Customer exercises DPDP Act right to erasure";
      action: "Purge all tiers of data for that customer within 15 days";
      exceptions: "Financial records retained per tax law (6 years) — but anonymized";
      confirmation: "Written confirmation to customer post-deletion";
    };

    AGENCY_OFFBOARDING: {
      trigger: "Agency cancels Waypoint OS subscription";
      grace_period: "30 days to export data";
      action: "Destroy tenant encryption key → all data becomes unreadable";
      verification: "Cryptographic proof of key destruction";
    };
  };

  // Purging implementation
  purging_mechanism: {
    SOFT_DELETE: {
      description: "Mark as deleted, remove from all queries, schedule hard delete";
      timeline: "Hard delete within 30 days of soft delete";
    };

    CRYPTO_SHREDDING: {
      description: "Destroy the encryption key → data becomes permanently unreadable";
      use_case: "Tier 4 data purging, agency offboarding";
      advantage: "No need to find and overwrite every copy — key destruction is sufficient";
    };

    VERIFIABLE_DELETION: {
      description: "Cryptographic proof that data was deleted";
      mechanism: "Hash of data before deletion + signed deletion certificate";
      use_case: "DPDP Act compliance — prove to regulator that deletion occurred";
    };
  };
}

// ── Retention scheduler ──
// ┌─────────────────────────────────────────────────────┐
// │  Data Retention — Upcoming Actions                        │
// │                                                       │
// │  This Week:                                           │
// │  🔴 PURGE: 12 passport records (trip completed 30+ days) │
// │     Customers: Sharma, Gupta, Patel + 9 others           │
// │     Action: Crypto-shred Tier 4 data                     │
// │     [Execute] [Review List]                                │
// │                                                       │
// │  🟡 ANONYMIZE: 45 customer profiles (inactive 12+ months) │
// │     Notifications sent: 35 of 45 (10 pending)             │
// │     Action: Strip PII, keep booking statistics            │
// │     [Execute] [Send Remaining Notices]                     │
// │                                                       │
// │  🟢 DELETE REQUESTS: 2 right-to-erasure requests         │
// │     Customer: A. Kumar — Deadline: May 12                 │
// │     Customer: R. Singh — Deadline: May 18                 │
// │     [Process Now] [View Details]                           │
// │                                                       │
// │  Scheduled (next 30 days):                            │
// │  - 78 Tier 4 records expiring                           │
// │  - 23 customer profiles reaching inactive threshold     │
// │  - DEK batch #14 rotation on Jun 28                     │
// │                                                       │
// │  [Retention Report] [Policy Settings] [Audit Log]         │
// └─────────────────────────────────────────────────────┘
```

### PII Compliance Automation

```typescript
interface PIIComplianceAutomation {
  // Automated compliance checks and reporting
  compliance_framework: {
    DPDP_ACT_INDIA: {
      requirements: {
        consent_management: "Granular, purpose-specific consent collection and tracking";
        data_minimization: "Collect only PII necessary for stated purpose";
        purpose_limitation: "PII used only for the purpose consent was given";
        storage_limitation: "Retain only as long as necessary (enforced by retention policies)";
        data_subject_rights: "Automated response to access, correction, erasure requests";
        breach_notification: "72-hour notification to Data Protection Board + affected individuals";
        cross_border: "PII transfer outside India only with adequate protection";
        sensitive_data: "Explicit consent for Aadhaar, financial, health, biometric data";
      };

      automation: {
        CONSENT_GATE: "Every PII collection point requires consent before storage";
        PURPOSE_CHECK: "System validates PII access against stated purpose";
        RETENTION_ENFORCER: "Automated purging per retention schedule";
        RIGHTS_HANDLER: "Automated response pipeline for data subject requests";
        BREACH_DETECTOR: "Anomaly detection on PII access patterns";
      };
    };

    PCI_DSS: {
      scope: "Credit card handling (even if tokenized through payment gateway)";
      requirements: {
        no_storage: "Never store full credit card number, CVV, or magnetic stripe data";
        tokenization: "Use payment gateway tokens for recurring reference";
        last_four: "Display only last 4 digits";
        network: "PII traffic encrypted in transit (TLS 1.2+)";
        testing: "Quarterly vulnerability scans, annual penetration test";
      };
    };
  };

  // Compliance reporting
  reporting: {
    MONTHLY_PRIVACY_REPORT: {
      contents: [
        "PII inventory: count of records per classification tier",
        "Access log summary: who accessed what, how often",
        "Retention compliance: records purged on schedule vs. overdue",
        "Consent status: active vs. expired vs. withdrawn",
        "Incident report: any unauthorized access or breaches",
        "DSAR (Data Subject Access Request) response times",
      ];
      recipients: "Agency owner + Data Protection Officer";
    };

    QUARTERLY_REGULATORY: {
      contents: [
        "DPDP Act compliance scorecard",
        "Data breach incidents and response actions",
        "Cross-border data transfer summary",
        "Consent withdrawal trends",
        "Retention policy adherence metrics",
      ];
      recipients: "Internal compliance team, retained for regulator review";
    };
  };
}
```

---

## Open Problems

1. **Searchable encryption overhead** — Encrypted fields can't be searched by default. HMAC-based blind indexes enable search but add complexity and minor security tradeoffs. Need to balance usability with security.

2. **Crypto-shredding verification** — Proving data was destroyed is technically challenging. Key destruction is verifiable, but proving no backup copies exist requires organizational controls, not just technical ones.

3. **Cross-tenant isolation** — In multi-tenant architecture, one agency's DEK must never be used to decrypt another agency's data. Key hierarchy must enforce strict tenant boundaries.

4. **Performance under encryption** — Field-level decryption on every read adds 1-3ms per field. A trip view with 20+ PII fields could add 30-60ms latency. Need caching strategy for decrypted data with short TTL.

---

## Next Steps

- [ ] Implement field-level encryption with AES-256-GCM for Tier 3 and Tier 4 data
- [ ] Build searchable encryption using HMAC blind indexes
- [ ] Create automated retention engine with purge scheduling
- [ ] Design DPDP Act compliance automation pipeline
- [ ] Implement key management integration with cloud KMS
