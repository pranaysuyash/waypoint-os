# Vendor Compliance — Regulatory & Quality Compliance

> Research document for supplier regulatory compliance, quality assurance, and audit management.

---

## Key Questions

1. **What regulatory frameworks apply to travel suppliers in key markets (India, Southeast Asia, Europe, Middle East)?**
2. **How do we verify ongoing compliance without manual audits for every supplier?**
3. **What's the compliance minimum for each supplier tier and category?**
4. **How do we handle a supplier who falls out of compliance mid-contract?**
5. **What data privacy obligations flow down from our platform to suppliers?**
6. **How do we balance compliance rigor with onboarding speed for small/local suppliers?**

---

## Research Areas

### Compliance Domains

```typescript
interface ComplianceRequirement {
  requirementId: string;
  domain: ComplianceDomain;
  name: string;
  description: string;
  applicableCategories: SupplierCategory[];
  jurisdictions: string[];
  verificationMethod: VerificationMethod;
  frequency: ComplianceFrequency;
  consequences: NonComplianceAction[];
}

type ComplianceDomain =
  | 'licensing'       // Business licenses and registrations
  | 'safety'          // Safety certifications and inspections
  | 'insurance'       // Required insurance coverage
  | 'labor'           // Employment law compliance
  | 'data_privacy'    // GDPR, IT Act, PDPA compliance
  | 'accessibility'   // Disability access requirements
  | 'environmental'   // Environmental certifications
  | 'financial'       // Tax registration, financial solvency
  | 'quality'         // Quality certifications (ISO, etc.)
  | 'consumer_protection';  // Consumer rights compliance

type VerificationMethod =
  | 'document_upload'     // Supplier provides certificate
  | 'registry_check'      // Automated government registry lookup
  | 'third_party_verify'  // Verification service (D&B, etc.)
  | 'site_audit'          // Physical inspection
  | 'self_attestation'    // Supplier self-certifies
  | 'platform_observed';  // Derived from platform behavior

type ComplianceFrequency =
  | 'on_onboarding'
  | 'annual'
  | 'semi_annual'
  | 'quarterly'
  | 'continuous';  // Ongoing monitoring
```

### India-Specific Compliance (Primary Market)

**Accommodation suppliers:**
- GST registration (mandatory for > ₹20L turnover)
- Fire safety NOC from local fire department
- Health trade license from municipal corporation
- Tourism department registration (state-specific)
- FSSAI license (if providing food)
- Building safety certificate

**Transport suppliers:**
- Commercial vehicle fitness certificate
- All India tourist permit (for inter-state)
- Driver badges and background verification
- Vehicle insurance (comprehensive + third-party)
- State transport authority registration

**Tour/activity operators:**
- Adventure sports license (for specific activities)
- Guide certification (regional tourism boards)
- First aid certification for staff
- Public liability insurance
- Environmental clearance (for eco-sensitive zones)

**Open questions:**
- How many of these can be verified via government API/database lookups?
- What's the compliance rate among small suppliers in India?
- Are there aggregated compliance databases that cover multiple requirements?

### Data Privacy Flow-Down

**When our platform shares customer data with suppliers:**

```typescript
interface DataFlowDown {
  dataType: CustomerDataType;
  sharedWith: SupplierCategory;
  purpose: string;
  legalBasis: string;
  retentionBySupplier: string;
  protectionRequired: string;
  auditMechanism: string;
}

type CustomerDataType =
  | 'pii'             // Name, contact, ID numbers
  | 'payment_info'    // Payment card or bank details
  | 'travel_docs'     // Passport, visa copies
  | 'preferences'     // Dietary, accessibility, room preferences
  | 'special_requests' // Health conditions, special needs
  | 'location_data'   // Real-time location for transfers/meetups;
```

**Key requirements:**
- GDPR Article 28 (Data Processor Agreement) for EU customers
- India DPDP Act 2023 obligations for data principals
- Singapore PDPA for Southeast Asian operations
- Right-to-deletion coordination with suppliers

### Audit Framework

```typescript
interface ComplianceAudit {
  auditId: string;
  supplierId: string;
  auditType: 'scheduled' | 'triggered' | 'random';
  scope: ComplianceDomain[];
  auditor: 'internal' | 'third_party' | 'self_assessment';
  status: 'planned' | 'in_progress' | 'findings' | 'closed';
  findings: AuditFinding[];
  overallRating: 'compliant' | 'minor_gaps' | 'major_gaps' | 'non_compliant';
  remediationPlan?: RemediationPlan;
}

interface AuditFinding {
  findingId: string;
  domain: ComplianceDomain;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  evidence: string;
  remediationDeadline: Date;
  status: 'open' | 'in_progress' | 'resolved';
}
```

---

## Open Problems

1. **Compliance verification automation** — Government databases for licenses vary wildly in accessibility across Indian states. Some are digitized, others require RTI requests. Need a scalable approach.

2. **Liability for supplier non-compliance** — If a hotel lacks a fire safety certificate and there's an incident, what's the agency's liability? Need legal research.

3. **Small supplier accommodation** — A homestay in rural Kerala may never obtain all "required" certifications. Do we exclude them, accept them with caveats, or create a simplified compliance tier?

4. **Cross-jurisdictional compliance** — A supplier in Thailand serving Indian, EU, and US customers needs to satisfy multiple regulatory frameworks simultaneously.

5. **Continuous monitoring vs. point-in-time** — Annual compliance checks miss mid-year lapses. Real-time monitoring is ideal but may not be feasible for many compliance domains.

6. **Data processor agreements at scale** — Getting hundreds of small suppliers to sign GDPR Article 28 agreements is operationally challenging. Need a pragmatic approach.

---

## Next Steps

- [ ] Map regulatory requirements per supplier category for India
- [ ] Research government database APIs for license verification
- [ ] Investigate third-party compliance verification services
- [ ] Design tiered compliance framework (essential vs. preferred vs. optional)
- [ ] Study liability frameworks for supplier non-compliance in Indian context
- [ ] Draft data processor agreement template for suppliers
