# Data Privacy & Consent Management — Breach Response

> Research document for data breach detection, notification, investigation, remediation, and post-incident review under DPDP Act and global regulations.

---

## Key Questions

1. **How do we detect and classify data breaches?**
2. **What's the DPDP Act notification timeline and process?**
3. **How do we investigate and contain a breach?**
4. **What's the breach remediation and recovery process?**
5. **How do we prevent future breaches with post-incident learnings?**

---

## Research Areas

### Breach Detection & Classification

```typescript
interface BreachManagement {
  detection: BreachDetection;
  classification: BreachClassification;
  notification: BreachNotification;
  containment: BreachContainment;
  investigation: BreachInvestigation;
  remediation: BreachRemediation;
  postIncident: PostIncidentReview;
}

interface BreachDetection {
  sources: DetectionSource[];
  indicators: BreachIndicator[];
  alerting: BreachAlerting;
}

type DetectionSource =
  | 'siem'                             // Security Information and Event Management
  | 'dlp'                              // Data Loss Prevention
  | 'access_anomaly'                   // Unusual data access patterns
  | 'external_report'                  // External researcher or media report
  | 'employee_report'                  // Internal whistleblower
  | 'third_party_report'              // Supplier/partner notification
  | 'customer_report';                 // Customer reports suspicious activity

// Breach indicators:
// UNUSUAL ACCESS:
// - Bulk download of customer records
// - Data access outside business hours
// - Access from unusual geographic locations
// - Repeated failed access attempts followed by success
// - Privilege escalation before data access
//
// DATA EXFILTRATION:
// - Large outbound data transfer
// - Encrypted outbound traffic to unknown endpoints
// - Database queries selecting PII columns without business context
// - Copy operations on sensitive tables
// - Unusual API call patterns (mass data export)
//
// SYSTEM ANOMALIES:
// - Unauthorized database schema changes
// - New admin accounts created without approval
// - Disabled audit logging
// - Modified access control rules
// - Unexpected backup downloads
//
// THIRD-PARTY INDICATORS:
// - Customer data appearing on dark web
// - Credential stuffing attacks on customer accounts
// - Supplier notifies of their own breach affecting shared data

interface BreachClassification {
  severity: BreachSeverity;
  scope: BreachScope;
  dataTypes: DataCategory[];
  affectedParties: AffectedParty[];
}

type BreachSeverity =
  | 'critical'                         // >100,000 records, sensitive data (IDs, financial)
  | 'high'                             // 10,000-100,000 records, PII
  | 'medium'                           // 1,000-10,000 records, limited PII
  | 'low';                             // <1,000 records, non-sensitive data

// Breach severity matrix:
//                    <1K records    1K-10K       10K-100K     >100K
// Government IDs:    High          Critical     Critical     Critical
// Financial data:    High          Critical     Critical     Critical
// Contact + PII:     Medium        High         Critical     Critical
// Travel history:    Medium        Medium       High         Critical
// Aggregated data:   Low           Low          Medium       High
// Public data:       Low           Low          Low          Medium

// DPDP Act breach notification requirements:
// Section 8(6): Data Fiduciary must notify:
//   1. Data Protection Board of India — Within 72 hours of becoming aware
//   2. Each affected Data Principal — Without unreasonable delay
//
// Notification to Data Protection Board must include:
// - Nature of breach
// - Number of affected data principals
// - Categories of personal data affected
// - Likely consequences of the breach
// - Measures taken or proposed to mitigate the breach
// - Contact details of Data Protection Officer
//
// Notification to affected individuals must include:
// - Clear description of what happened (plain language)
// - What data was affected
// - What they can do to protect themselves
// - What the organization is doing to address the breach
// - Contact information for questions
//
// Penalties for notification failure:
// Up to ₹50 crore per incident
// Up to ₹200 crore for broader data processing violations
```

### Breach Response Playbook

```typescript
interface BreachResponsePlaybook {
  phases: ResponsePhase[];
  communication: BreachCommunication;
  legal: LegalResponse;
  technical: TechnicalResponse;
}

// Breach response phases:
//
// PHASE 1: DETECTION & TRIAGE (0-4 hours)
// - Alert received → Incident commander assigned
// - Initial assessment: Is this a confirmed breach?
// - Classify severity and scope
// - Assemble response team: DPO, CTO, Legal, Communications
// - Begin incident log (every action timestamped)
//
// PHASE 2: CONTAINMENT (0-24 hours)
// - Isolate affected systems
// - Revoke compromised credentials
// - Block exfiltration paths
// - Preserve forensic evidence (don't destroy logs)
// - Enable enhanced monitoring
// - Assess if customer-facing systems need to go offline
//
// PHASE 3: NOTIFICATION (24-72 hours)
// - Notify Data Protection Board (within 72 hours)
// - Prepare customer notification
// - Notify third-party processors if their data affected
// - Engage legal counsel for regulatory communications
// - Prepare media statement (if high-profile)
//
// PHASE 4: INVESTIGATION (1-4 weeks)
// - Forensic analysis: How did breach occur?
// - Scope analysis: Exactly what data was accessed/exfiltrated?
// - Timeline reconstruction: When did breach start? How long?
// - Root cause analysis: What vulnerability was exploited?
// - Impact assessment: How many customers affected? What data?
//
// PHASE 5: REMEDIATION (2-8 weeks)
// - Patch vulnerability that enabled breach
// - Reset all potentially compromised credentials
// - Enhance security controls to prevent recurrence
// - Update monitoring and detection rules
// - Re-verify access controls and permissions
//
// PHASE 6: RECOVERY & LESSONS (1-3 months)
// - Restore services to normal operation
// - Customer support for affected individuals
// - Credit monitoring / identity protection (if financial data)
// - Post-incident review with full team
// - Update security policies and procedures
// - Board/management briefing with lessons learned

// Customer notification template:
// Subject: Important Security Notice from [Agency Name]
//
// Dear [Customer Name],
//
// We are writing to inform you of a security incident that may have
// affected your personal information.
//
// WHAT HAPPENED:
// On [date], we detected unauthorized access to [system/database]
// containing customer information. We immediately secured the system
// and began an investigation with cybersecurity experts.
//
// WHAT DATA WAS INVOLVED:
// The following types of your information may have been accessed:
// [List specific data types — be precise]
//
// We have NO evidence that the following was accessed:
// [List what was NOT affected — credit card numbers, passwords, etc.]
//
// WHAT WE ARE DOING:
// - Engaged cybersecurity firm [Name] for forensic investigation
// - Notified the Data Protection Board of India
// - Enhanced security measures to prevent similar incidents
// - Offering [credit monitoring / identity protection] for 12 months
//
// WHAT YOU CAN DO:
// - Change your password on our platform and any site where you use the same password
// - Monitor your financial statements for unusual activity
// - Be cautious of phishing emails claiming to be from us
//
// FOR QUESTIONS:
// Dedicated helpline: [Phone number]
// Email: privacy@[agency].com
// Available: 9 AM - 9 PM IST, 7 days a week
//
// We sincerely apologize for this incident and are committed to
// protecting your information.
//
// Sincerely,
// [DPO Name], Data Protection Officer
// [Agency Name]

// Legal response:
// - Engage external legal counsel (cyber law specialist)
// - Document all actions taken (for regulatory defense)
// - Assess regulatory reporting obligations (DPDP, RBI, IRDAI)
// - Prepare for potential class-action litigation
// - Insurance claim: Cyber liability insurance policy
// - Regulatory cooperation: Full transparency with authorities
//
// Technical response by breach type:
//
// DATABASE BREACH:
// - Take affected database offline
// - Restore from clean backup to new infrastructure
// - Rotate all database credentials
// - Enable enhanced query logging
// - Audit all admin access
//
// CREDENTIAL THEFT:
// - Force password reset for all affected accounts
// - Revoke all active sessions and tokens
// - Enable mandatory MFA for affected accounts
// - Block suspicious IP ranges
//
// THIRD-PARTY BREACH (supplier/partner):
// - Assess what data was shared with the breached party
// - Revoke API keys and access tokens
// - Request details of breach from partner
// - Notify affected customers based on shared data
// - Evaluate if relationship should continue
//
// INSIDER THREAT:
// - Suspend employee access immediately
// - Forensic analysis of their access patterns
// - Legal review (NDA, employment contract)
// - Law enforcement if criminal activity suspected
// - Review access control policies
```

---

## Open Problems

1. **Detection latency** — The average time to detect a data breach is 200+ days (IBM). Reducing detection time requires sophisticated SIEM rules, anomaly detection, and 24/7 monitoring — expensive for small agencies.

2. **Notification without panic** — Over-notifying (every minor incident) causes notification fatigue. Under-notifying risks regulatory penalties. Calibrating notification thresholds is difficult.

3. **Multi-tenant breach scope** — In a multi-tenant platform, a breach affecting one agency's data may or may not affect others. Determining tenant-specific scope quickly is critical for targeted notification.

4. **Backup data erasure** — Even after erasing production data, backups may contain breached data. Re-restoring all backups without the breached data is operationally complex. Crypto-shredding helps but must be planned in advance.

5. **Reputation recovery** — A data breach damages trust, especially for a platform handling passport and payment data. Rebuilding customer confidence takes months or years and requires transparent communication.

---

## Next Steps

- [ ] Build breach detection system with anomaly-based alerting
- [ ] Create breach response playbook with automated containment actions
- [ ] Design customer notification system with regulatory-compliant templates
- [ ] Implement post-incident review process with lessons-learned tracking
- [ ] Study breach response frameworks (NIST SP 800-61, ISO 27035, SANS Incident Handling)
