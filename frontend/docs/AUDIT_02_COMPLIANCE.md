# Audit & Compliance — Compliance Monitoring & Reporting

> Research document for automated compliance checking, regulatory reporting, and policy enforcement.

---

## Key Questions

1. **What regulations apply, and how do we map them to system controls?**
2. **How do we automate compliance checks without creating false positives?**
3. **What compliance reports are required, and at what frequency?**
4. **How do we handle multi-jurisdiction compliance (India, EU, US)?**
5. **What's the compliance dashboard for management visibility?**

---

## Research Areas

### Compliance Framework

```typescript
interface ComplianceFramework {
  regulation: string;
  jurisdiction: string;
  requirements: ComplianceRequirement[];
  controls: ComplianceControl[];
  reportingSchedule: ReportingSchedule[];
}

// Key regulations for travel platform:
// 1. IT Act 2000 + DPDP Act (India data protection)
// 2. GDPR (EU customers)
// 3. PCI DSS (payment card handling)
// 4. RBI guidelines (payment processing)
// 5. GST (tax compliance)
// 6. IRDAI (insurance distribution)
// 7. IATA/BSP (airline ticketing)

interface ComplianceControl {
  controlId: string;
  requirement: string;
  type: 'preventive' | 'detective' | 'corrective';
  implementation: string;
  testProcedure: string;
  testFrequency: 'continuous' | 'daily' | 'weekly' | 'monthly' | 'quarterly';
  lastTested?: Date;
  status: 'compliant' | 'partially_compliant' | 'non_compliant' | 'not_tested';
}
```

### Automated Compliance Checks

```typescript
interface ComplianceCheck {
  checkId: string;
  control: string;
  schedule: string;
  check: ComplianceCheckFunction;
  alertOn: 'failure' | 'warning' | 'change';
}

type ComplianceCheckFunction =
  | 'verify_consent_before_data_collection'
  | 'check_data_retention_limits'
  | 'validate_gst_on_invoices'
  | 'verify_pci_tokenization'
  | 'check_access_review_current'
  | 'validate_encryption_at_rest'
  | 'check_password_policy_compliance'
  | 'verify_backup_integrity'
  | 'check_supplier_license_currency'
  | 'validate_tcs_collection';

// Example: Data retention check
// - Customer booking data retained >7 years? Flag for review.
// - Webhook logs retained >90 days? Auto-delete.
// - Session tokens expired but not cleaned? Flag.
```

### Compliance Reporting

```typescript
interface ComplianceReport {
  reportType: ComplianceReportType;
  period: DateRange;
  generatedAt: Date;
  findings: ComplianceFinding[];
  summary: ComplianceSummary;
  signOff: SignOff[];
}

type ComplianceReportType =
  | 'dpdp_monthly'               // Data protection compliance
  | 'gst_quarterly'              // GST filing
  | 'pci_dss_annual'             // PCI compliance
  | 'audit_committee_quarterly'  // Board reporting
  | 'regulatory_filing'          // Government filing
  | 'incident_report';           // Breach/incident report

interface ComplianceSummary {
  totalControls: number;
  compliant: number;
  partiallyCompliant: number;
  nonCompliant: number;
  notTested: number;
  overallScore: number;           // 0-100
}
```

---

## Open Problems

1. **Multi-regulation overlap** — GDPR and DPDP both govern data protection but with different requirements. Complying with both simultaneously needs careful mapping.

2. **Compliance automation limits** — Some controls require human judgment (e.g., "is this data processing fair?"). Full automation isn't possible.

3. **Regulatory change tracking** — Regulations change. How to detect relevant changes and update controls accordingly?

4. **Evidence collection** — Auditors want proof that controls are working. Collecting and presenting evidence for each control is labor-intensive.

5. **Vendor compliance** — Our compliance depends on our vendors' compliance (cloud provider, payment gateway, CRM). Need vendor compliance tracking.

---

## Next Steps

- [ ] Map applicable regulations to system controls
- [ ] Design automated compliance check framework
- [ ] Create compliance dashboard for management
- [ ] Study compliance automation tools (Vanta, Drata, Secureframe)
- [ ] Design regulatory change monitoring process
