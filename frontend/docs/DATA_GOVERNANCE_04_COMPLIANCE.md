# DATA_GOVERNANCE_04: Compliance & Privacy Deep Dive

> GDPR compliance, data retention, privacy controls, and audit

---

## Table of Contents

1. [Overview](#overview)
2. [GDPR Compliance Framework](#gdpr-compliance-framework)
3. [Data Subject Rights](#data-subject-rights)
4. [Consent Management](#consent-management)
5. [Data Retention Policies](#data-retention-policies)
6. [Data Minimization](#data-minimization)
7. [Privacy by Design](#privacy-by-design)
8. [Data Protection Impact Assessment](#data-protection-impact-assessment)
9. [Cross-Border Transfers](#cross-border-transfers)
10. [Audit & Reporting](#audit--reporting)
11. [API Specification](#api-specification)
12. [Testing Scenarios](#testing-scenarios)
13. [Metrics & Monitoring](#metrics--monitoring)

---

## Overview

Compliance and privacy are foundational to responsible data handling. This document covers GDPR compliance, data subject rights, consent management, retention policies, and privacy controls.

### The Compliance Landscape

```
┌─────────────────────────────────────────────────────────────┐
│                Regulatory Requirements                       │
├─────────────────────────────────────────────────────────────┤
│  GDPR        (EU)     - Personal data protection            │
│  DPDP        (India)  - Digital Personal Data Protection    │
│  CCPA        (California) - Consumer privacy rights         │
│  PDPB        (Philippines) - Data privacy Act              │
│  PDPA        (Singapore) - Personal data protection         │
│                                                              │
│  Common principles across all regulations:                  │
│  - Lawful basis for processing                              │
│  - Purpose limitation                                       │
│  - Data minimization                                        │
│  - Accuracy and retention limits                             │
│  - Security measures                                        │
│  - Individual rights (access, delete, correct, port)        │
└─────────────────────────────────────────────────────────────┘
```

### Compliance Framework

```
┌─────────────────────────────────────────────────────────────┐
│                    Compliance Layers                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Legal                                             │
│    - Regulatory requirements mapping                        │
│    - Lawful basis documentation                             │
│    - Contractual obligations                                │
│                                                              │
│  Layer 2: Technical                                         │
│    - Access controls                                         │
│    - Encryption at rest/in transit                          │
│    - Audit logging                                          │
│    - Data retention automation                              │
│                                                              │
│  Layer 3: Operational                                       │
│    - Data subject request handling                          │
│    - Consent management                                     │
│    - Breach response procedures                            │
│    - Staff training and awareness                           │
│                                                              │
│  Layer 4: Monitoring                                        │
│    - Compliance dashboards                                  │
│    - Automated alerts                                       │
│    - Regular audits                                         │
│    - Continuous improvement                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## GDPR Compliance Framework

### Legal Basis Mapping

```typescript
// compliance/gdpr/legal-basis.ts

export enum LawfulBasis {
  CONSENT = 'consent',                          // Explicit consent given
  CONTRACT = 'contract',                        // Performance of contract
  LEGAL_OBLIGATION = 'legal_obligation',       // Legal requirement
  VITAL_INTERESTS = 'vital_interests',         // Protect life
  PUBLIC_TASK = 'public_task',                 // Public interest task
  LEGITIMATE_INTERESTS = 'legitimate_interests' // Legitimate business interest
}

export interface LegalBasisRecord {
  entityId: string;
  entityType: 'customer' | 'booking' | 'inquiry';
  basisType: LawfulBasis;
  description: string;
  consentDetails?: ConsentDetails;
  contractDetails?: ContractDetails;
  documentedAt: Date;
  documentedBy: string;
  reviewedAt?: Date;
  reviewFrequency: number; // days
}

export interface ConsentDetails {
  consentGiven: boolean;
  consentDate: Date;
  consentMethod: 'email' | 'web_form' | 'paper' | 'verbal';
  withdrawalDate?: Date;
  withdrawalMethod?: string;
}

export interface ContractDetails {
  contractId: string;
  contractType: 'service_agreement' | 'booking_contract';
  counterparty: string;
  obligationDescription: string;
}

// Legal basis for common data processing activities
export const processingActivityBasis: Record<string, LawfulBasis> = {
  // Customer contact information
  'customer.email': LawfulBasis.LEGITIMATE_INTERESTS,
  'customer.phone': LawfulBasis.LEGITIMATE_INTERESTS,
  'customer.address': LawfulBasis.CONTRACT,
  'customer.date_of_birth': LawfulBasis.LEGITIMATE_INTERESTS,

  // Travel documents
  'customer.passport_number': LawfulBasis.CONTRACT,
  'customer.passport_expiry': LawfulBasis.CONTRACT,
  'customer.pan_card': LawfulBasis.LEGITIMATE_INTERESTS,

  // Payment information
  'payment.card_number': LawfulBasis.CONTRACT,
  'payment.bank_account': LawfulBasis.CONTRACT,
  'payment.upi_id': LawfulBasis.LEGITIMATE_INTERESTS,

  // Travel preferences
  'customer.preferences': LawfulBasis.CONSENT,
  'customer.dietary_requirements': LawfulBasis.LEGITIMATE_INTERESTS,

  // Marketing communications
  'marketing.consent': LawfulBasis.CONSENT,
  'newsletter.subscription': LawfulBasis.CONSENT
};

export class LegalBasisService {
  private records: Map<string, LegalBasisRecord> = new Map();

  async recordLegalBasis(record: LegalBasisRecord): Promise<void> {
    this.records.set(`${record.entityType}:${record.entityId}`, record);
  }

  async getLegalBasis(
    entityType: string,
    entityId: string
  ): Promise<LegalBasisRecord | undefined> {
    return this.records.get(`${entityType}:${entityId}`);
  }

  async getProcessingBasis(
    entityType: string,
    field: string
  ): Promise<LawfulBasis> {
    const key = `${entityType}.${field}`;
    return processingActivityBasis[key] || LawfulBasis.LEGITIMATE_INTERESTS;
  }

  async validateProcessing(
    entityType: string,
    entityId: string,
    processingPurpose: string
  ): Promise<{ valid: boolean; gaps: string[] }> {
    const record = await this.getLegalBasis(entityType, entityId);
    const gaps: string[] = [];

    if (!record) {
      gaps.push(`No legal basis recorded for ${entityType}:${entityId}`);
      return { valid: false, gaps };
    }

    // Validate consent if applicable
    if (record.basisType === LawfulBasis.CONSENT) {
      if (!record.consentDetails?.consentGiven) {
        gaps.push('Consent recorded but not given');
      }

      // Check if consent was withdrawn
      if (record.consentDetails?.withdrawalDate) {
        gaps.push('Consent was withdrawn on ' + record.consentDetails.withdrawalDate);
      }
    }

    // Check review date
    if (record.reviewedAt) {
      const daysSinceReview = (Date.now() - record.reviewedAt.getTime()) / (1000 * 60 * 60 * 24);
      if (daysSinceReview > record.reviewFrequency) {
        gaps.push(`Legal basis review overdue by ${Math.floor(daysSinceReview - record.reviewFrequency)} days`);
      }
    }

    return { valid: gaps.length === 0, gaps };
  }

  async getRecordsNeedingReview(daysThreshold = 30): Promise<LegalBasisRecord[]> {
    const now = Date.now();
    const threshold = daysThreshold * 24 * 60 * 60 * 1000;

    return Array.from(this.records.values()).filter(record => {
      const lastReviewed = record.reviewedAt?.getTime() || record.documentedAt.getTime();
      return (now - lastReviewed) > (record.reviewFrequency * 24 * 60 * 60 * 1000);
    });
  }
}
```

### Data Classification

```typescript
// compliance/gdpr/classification.ts

export enum DataClassification {
  PUBLIC = 'public',           // Can be shared freely
  INTERNAL = 'internal',       // Internal business use only
  CONFIDENTIAL = 'confidential', // Sensitive business information
  RESTRICTED = 'restricted',   // Highly sensitive, need-to-know
  CRITICAL = 'critical'        // Most sensitive, breach causes severe harm
}

export enum GDPRRelevance {
  NOT_RELEVANT = 'not_relevant',     // Doesn't contain personal data
  PERSONAL_DATA = 'personal_data',   // Basic personal data (name, email)
  SPECIAL_CATEGORY = 'special_category', // Sensitive data (health, biometric)
  CRIMINAL_OFFENSE = 'criminal_offense' // Criminal conviction data
}

export interface DataClassificationRecord {
  entityId: string;
  entityType: string;
  classification: DataClassification;
  gdprRelevant: GDPRRelevance;
  fields: ClassifiedField[];
  assessedAt: Date;
  assessedBy: string;
}

export interface ClassifiedField {
  fieldName: string;
  classification: DataClassification;
  gdprRelevant: boolean;
  specialCategory: boolean;
  pseudonymized: boolean;
  encrypted: boolean;
  accessRestricted: boolean;
}

export class DataClassificationService {
  async classifyEntity(
    entityType: string,
    entityId: string,
    data: Record<string, any>
  ): Promise<DataClassificationRecord> {
    const fields: ClassifiedField[] = [];

    for (const [fieldName, value] of Object.entries(data)) {
      fields.push(this.classifyField(fieldName, value));
    }

    const overallClassification = this.determineOverallClassification(fields);
    const gdprRelevant = this.determineGDPRRelevance(fields);

    return {
      entityId,
      entityType,
      classification: overallClassification,
      gdprRelevant,
      fields,
      assessedAt: new Date(),
      assessedBy: 'system'
    };
  }

  private classifyField(fieldName: string, value: any): ClassifiedField {
    const nameLower = fieldName.toLowerCase();

    // Determine classification
    let classification = DataClassification.INTERNAL;

    if (nameLower.includes('password') || nameLower.includes('secret') || nameLower.includes('token')) {
      classification = DataClassification.CRITICAL;
    } else if (
      nameLower.includes('card') ||
      nameLower.includes('bank_account') ||
      nameLower.includes('pan') ||
      nameLower.includes('passport')
    ) {
      classification = DataClassification.RESTRICTED;
    } else if (
      nameLower.includes('email') ||
      nameLower.includes('phone') ||
      nameLower.includes('address') ||
      nameLower.includes('dob') ||
      nameLower.includes('name')
    ) {
      classification = DataClassification.CONFIDENTIAL;
    }

    // Determine GDPR relevance
    const gdprRelevant = this.isGDPRRelevant(fieldName);
    const specialCategory = this.isSpecialCategory(fieldName);

    return {
      fieldName,
      classification,
      gdprRelevant,
      specialCategory,
      pseudonymized: false,
      encrypted: classification === DataClassification.RESTRICTED || classification === DataClassification.CRITICAL,
      accessRestricted: classification !== DataClassification.PUBLIC
    };
  }

  private isGDPRRelevant(fieldName: string): boolean {
    const personalDataPatterns = [
      'name', 'email', 'phone', 'address', 'dob', 'birth',
      'passport', 'id_proof', 'pan', 'aadhaar', 'ssn',
      'location', 'ip', 'cookie', 'device'
    ];

    const nameLower = fieldName.toLowerCase();
    return personalDataPatterns.some(pattern => nameLower.includes(pattern));
  }

  private isSpecialCategory(fieldName: string): boolean {
    const specialCategories = [
      'health', 'medical', 'biometric', 'genetic',
      'race', 'ethnic', 'religion', 'political',
      'union', 'sexual', 'criminal'
    ];

    const nameLower = fieldName.toLowerCase();
    return specialCategories.some(category => nameLower.includes(category));
  }

  private determineOverallClassification(fields: ClassifiedField[]): DataClassification {
    if (fields.length === 0) return DataClassification.INTERNAL;

    // Return highest classification
    const classificationOrder = [
      DataClassification.PUBLIC,
      DataClassification.INTERNAL,
      DataClassification.CONFIDENTIAL,
      DataClassification.RESTRICTED,
      DataClassification.CRITICAL
    ];

    let highest = DataClassification.PUBLIC;

    for (const field of fields) {
      const currentIndex = classificationOrder.indexOf(highest);
      const fieldIndex = classificationOrder.indexOf(field.classification);
      if (fieldIndex > currentIndex) {
        highest = field.classification;
      }
    }

    return highest;
  }

  private determineGDPRRelevance(fields: ClassifiedField[]): GDPRRelevance {
    const hasSpecialCategory = fields.some(f => f.specialCategory);
    const hasPersonalData = fields.some(f => f.gdprRelevant);

    if (hasSpecialCategory) return GDPRRelevance.SPECIAL_CATEGORY;
    if (hasPersonalData) return GDPRRelevance.PERSONAL_DATA;
    return GDPRRelevance.NOT_RELEVANT;
  }
}
```

---

## Data Subject Rights

### Rights Management

```typescript
// compliance/gdpr/data-subject-rights.ts

export enum DataSubjectRight {
  ACCESS = 'access',                       // Right to access
  RECTIFICATION = 'rectification',         // Right to correction
  ERASURE = 'erasure',                     // Right to be forgotten
  PORTABILITY = 'portability',             // Right to data portability
  OBJECTION = 'objection',                 // Right to object
  RESTRICTION = 'restriction'              // Right to restrict processing
}

export interface DataSubjectRequest {
  id: string;
  subjectId: string;
  subjectType: 'customer' | 'lead' | 'prospect';
  right: DataSubjectRight;
  status: 'pending' | 'processing' | 'completed' | 'rejected' | 'partially_completed';
  requestDate: Date;
  responseDeadline: Date;
  completedDate?: Date;
  verificationMethod: string;
  verificationStatus: 'pending' | 'verified' | 'failed';
  scope: string[]; // Entities/systems included
  findings: RequestFinding[];
  actionsTaken: ActionTaken[];
  rejectionReason?: string;
  notes: string[];
  assignedTo: string;
}

export interface RequestFinding {
  entityId: string;
  entityType: string;
  dataFound: boolean;
  dataSummary: string;
  dataLocation: string[];
  retentionStatus: string;
}

export interface ActionTaken {
  action: string;
  description: string;
  executedAt: Date;
  executedBy: string;
}

export class DataSubjectRightsService {
  private requests: Map<string, DataSubjectRequest> = new Map();
  private legalBasis: LegalBasisService;

  constructor(legalBasis: LegalBasisService) {
    this.legalBasis = legalBasis;
  }

  async submitRequest(
    subjectId: string,
    right: DataSubjectRight,
    scope: string[] = []
  ): Promise<DataSubjectRequest> {
    const request: DataSubjectRequest = {
      id: `DSR_${Date.now()}`,
      subjectId,
      subjectType: 'customer',
      right,
      status: 'pending',
      requestDate: new Date(),
      responseDeadline: this.calculateDeadline(right),
      verificationMethod: 'email',
      verificationStatus: 'pending',
      scope: scope.length > 0 ? scope : await this.getDefaultScope(right),
      findings: [],
      actionsTaken: [],
      assignedTo: 'privacy-team@travel-agency.com',
      notes: []
    };

    this.requests.set(request.id, request);

    // Trigger verification
    await this.initiateVerification(request);

    return request;
  }

  async processAccessRequest(requestId: string): Promise<DataSubjectRequest> {
    const request = this.requests.get(requestId);
    if (!request) throw new Error('Request not found');

    request.status = 'processing';

    // Gather all data for subject
    const findings = await this.gatherSubjectData(request.subjectId, request.scope);
    request.findings = findings;

    // Prepare data export
    const exportData = await this.prepareDataExport(findings);

    // Send to subject
    await this.sendDataExport(request.subjectId, exportData);

    request.status = 'completed';
    request.completedDate = new Date();

    // Log action
    request.actionsTaken.push({
      action: 'data_export_sent',
      description: `Exported ${findings.length} entities with data`,
      executedAt: new Date(),
      executedBy: 'system'
    });

    return request;
  }

  async processErasureRequest(requestId: string): Promise<DataSubjectRequest> {
    const request = this.requests.get(requestId);
    if (!request) throw new Error('Request not found');

    request.status = 'processing';

    // Check legal basis retention requirements
    const validation = await this.validateErasure(request);
    if (!validation.canErase) {
      request.status = 'rejected';
      request.rejectionReason = validation.reason;
      return request;
    }

    // Gather data
    const findings = await this.gatherSubjectData(request.subjectId, request.scope);
    request.findings = findings;

    // Erase or anonymize data
    const actions: ActionTaken[] = [];

    for (const finding of findings) {
      const action = await this.eraseEntityData(finding.entityId, finding.entityType);
      actions.push(action);
    }

    request.actionsTaken = actions;
    request.status = actions.every(a => a.description.includes('erased'))
      ? 'completed'
      : 'partially_completed';
    request.completedDate = new Date();

    return request;
  }

  async processRectificationRequest(
    requestId: string,
    corrections: Record<string, any>
  ): Promise<DataSubjectRequest> {
    const request = this.requests.get(requestId);
    if (!request) throw new Error('Request not found');

    request.status = 'processing';

    // Apply corrections
    const actions: ActionTaken[] = [];

    for (const [entityId, data] of Object.entries(corrections)) {
      const action = await this.correctEntityData(entityId, data);
      actions.push(action);
    }

    request.actionsTaken = actions;
    request.status = 'completed';
    request.completedDate = new Date();

    return request;
  }

  async processPortabilityRequest(requestId: string): Promise<DataSubjectRequest> {
    const request = this.requests.get(requestId);
    if (!request) throw new Error('Request not found');

    request.status = 'processing';

    // Gather data in portable format
    const findings = await this.gatherSubjectData(request.subjectId, request.scope);
    const portableData = await this.preparePortableFormat(findings);

    // Send to subject
    await this.sendPortableData(request.subjectId, portableData);

    request.findings = findings;
    request.status = 'completed';
    request.completedDate = new Date();

    request.actionsTaken.push({
      action: 'data_portability_export',
      description: `Exported portable data for ${findings.length} entities`,
      executedAt: new Date(),
      executedBy: 'system'
    });

    return request;
  }

  async processObjectionRequest(
    requestId: string,
    objectionReason: string
  ): Promise<DataSubjectRequest> {
    const request = this.requests.get(requestId);
    if (!request) throw new Error('Request not found');

    request.status = 'processing';

    // Evaluate objection
    const evaluation = await this.evaluateObjection(request, objectionReason);

    if (evaluation.granted) {
      // Stop processing
      await this.stopProcessing(request.subjectId, request.scope);
      request.status = 'completed';
      request.notes.push(`Objection granted: ${objectionReason}`);
    } else {
      request.status = 'rejected';
      request.rejectionReason = evaluation.reason;
    }

    request.completedDate = new Date();

    return request;
  }

  private calculateDeadline(right: DataSubjectRight): Date {
    const deadline = new Date();
    deadline.setDate(deadline.getDate() + 30); // 30 days for most requests
    return deadline;
  }

  private async initiateVerification(request: DataSubjectRequest): Promise<void> {
    // Send verification email/code
    console.log(`Verification initiated for request ${request.id}`);
  }

  private async getDefaultScope(right: DataSubjectRight): Promise<string[]> {
    // Default scope includes all systems
    return ['customers', 'bookings', 'inquiries', 'payments'];
  }

  private async gatherSubjectData(
    subjectId: string,
    scope: string[]
  ): Promise<RequestFinding[]> {
    const findings: RequestFinding[] = [];

    // Query each system in scope
    for (const system of scope) {
      const systemData = await this.querySystemData(system, subjectId);
      findings.push(...systemData);
    }

    return findings;
  }

  private async querySystemData(
    system: string,
    subjectId: string
  ): Promise<RequestFinding[]> {
    // Implementation depends on system
    return [];
  }

  private async prepareDataExport(findings: RequestFinding[]): Promise<any> {
    return {
      generatedAt: new Date(),
      subjectId: findings[0]?.dataSummary || '',
      data: findings
    };
  }

  private async sendDataExport(subjectId: string, data: any): Promise<void> {
    // Send encrypted export to subject
  }

  private async validateErasure(request: DataSubjectRequest): Promise<{
    canErase: boolean;
    reason?: string;
  }> {
    // Check legal basis for retention
    const legalBases = await Promise.all(
      request.scope.map(async (entityType) => {
        const records = await this.gatherSubjectData(request.subjectId, [entityType]);
        const validations = await Promise.all(
          records.map(async (record) => {
            const basis = await this.legalBasis.getLegalBasis(record.entityType, record.entityId);
            return this.legalBasis.validateProcessing(
              record.entityType,
              record.entityId,
              'erasure'
            );
          })
        );
        return validations;
      })
    );

    const hasRetentionRequirement = legalBases
      .flat()
      .some(v => !v.valid && v.gaps.some(g => g.includes('legal obligation')));

    if (hasRetentionRequirement) {
      return {
        canErase: false,
        reason: 'Data must be retained for legal/tax obligations (typically 7-8 years)'
      };
    }

    return { canErase: true };
  }

  private async eraseEntityData(
    entityId: string,
    entityType: string
  ): Promise<ActionTaken> {
    // Anonymize or delete the entity
    return {
      action: 'erasure',
      description: `Anonymized ${entityType}:${entityId}`,
      executedAt: new Date(),
      executedBy: 'system'
    };
  }

  private async correctEntityData(
    entityId: string,
    corrections: any
  ): Promise<ActionTaken> {
    // Apply corrections to entity
    return {
      action: 'rectification',
      description: `Corrected data for ${entityId}`,
      executedAt: new Date(),
      executedBy: 'system'
    };
  }

  private async preparePortableFormat(findings: RequestFinding[]): Promise<any> {
    // Convert to JSON/CSV portable format
    return {
      format: 'json',
      schema: 'https://example.com/schemas/portability/v1',
      data: findings
    };
  }

  private async sendPortableData(subjectId: string, data: any): Promise<void> {
    // Send portable data to subject
  }

  private async evaluateObjection(
    request: DataSubjectRequest,
    reason: string
  ): Promise<{ granted: boolean; reason?: string }> {
    // Check if processing can be stopped
    const legalBasis = await this.legalBasis.getLegalBasis(
      request.subjectType,
      request.subjectId
    );

    if (legalBasis?.basisType === LawfulBasis.LEGITIMATE_INTERESTS) {
      // Can stop processing if legitimate interests don't override subject's interests
      return { granted: true };
    }

    if (legalBasis?.basisType === LawfulBasis.CONTRACT) {
      return {
        granted: false,
        reason: 'Cannot stop processing required for contract performance'
      };
    }

    return { granted: false };
  }

  private async stopProcessing(subjectId: string, scope: string[]): Promise<void> {
    // Mark records for processing exclusion
  }

  async getRequest(requestId: string): Promise<DataSubjectRequest | undefined> {
    return this.requests.get(requestId);
  }

  async listRequests(filters?: {
    subjectId?: string;
    status?: string;
    right?: DataSubjectRight;
    from?: Date;
    to?: Date;
  }): Promise<DataSubjectRequest[]> {
    let results = Array.from(this.requests.values());

    if (filters) {
      if (filters.subjectId) {
        results = results.filter(r => r.subjectId === filters.subjectId);
      }
      if (filters.status) {
        results = results.filter(r => r.status === filters.status);
      }
      if (filters.right) {
        results = results.filter(r => r.right === filters.right);
      }
    }

    return results.sort((a, b) => b.requestDate.getTime() - a.requestDate.getTime());
  }
}
```

---

## Consent Management

### Consent Tracking

```typescript
// compliance/consent/service.ts

export enum ConsentPurpose {
  MARKETING_EMAILS = 'marketing_emails',
  MARKETING_SMS = 'marketing_sms',
  NEWSLETTER = 'newsletter',
  ANALYTICS = 'analytics',
  PERSONALIZATION = 'personalization',
  THIRD_PARTY_SHARING = 'third_party_sharing',
  COOKIES = 'cookies',
  LOCATION_TRACKING = 'location_tracking'
}

export interface ConsentRecord {
  id: string;
  subjectId: string;
  subjectType: string;
  purpose: ConsentPurpose;
  status: 'granted' | 'denied' | 'revoked' | 'expired';
  grantedAt: Date;
  grantedMethod: 'email_link' | 'web_form' | 'checkbox' | 'written';
  grantedIP?: string;
  revokedAt?: Date;
  revokedMethod?: string;
  expiresAt?: Date;
  version: string; // For consent policy versioning
  preferences: ConsentPreferences;
  metadata: ConsentMetadata;
}

export interface ConsentPreferences {
  frequency?: 'daily' | 'weekly' | 'monthly' | 'never';
  categories?: string[];
  channels?: ('email' | 'sms' | 'push' | 'whatsapp')[];
}

export interface ConsentMetadata {
  created: Date;
  modified: Date;
  modifiedBy: string;
  source: string;
  documentationUrl?: string;
}

export class ConsentManagementService {
  private records: Map<string, ConsentRecord[]> = new Map();
  private currentPolicyVersion = '1.0';

  async grantConsent(
    subjectId: string,
    purpose: ConsentPurpose,
    method: string,
    preferences?: ConsentPreferences,
    ip?: string
  ): Promise<ConsentRecord> {
    const record: ConsentRecord = {
      id: `CONSENT_${subjectId}_${purpose}_${Date.now()}`,
      subjectId,
      subjectType: 'customer',
      purpose,
      status: 'granted',
      grantedAt: new Date(),
      grantedMethod: method,
      grantedIP: ip,
      version: this.currentPolicyVersion,
      preferences: preferences || {},
      metadata: {
        created: new Date(),
        modified: new Date(),
        modifiedBy: subjectId,
        source: 'customer'
      }
    };

    const subjectRecords = this.records.get(subjectId) || [];
    subjectRecords.push(record);
    this.records.set(subjectId, subjectRecords);

    return record;
  }

  async revokeConsent(
    subjectId: string,
    purpose: ConsentPurpose,
    method: string
  ): Promise<ConsentRecord> {
    const subjectRecords = this.records.get(subjectId) || [];

    // Find active consent for purpose
    const activeConsent = subjectRecords.find(
      r => r.purpose === purpose && r.status === 'granted'
    );

    if (!activeConsent) {
      throw new Error(`No active consent found for ${purpose}`);
    }

    activeConsent.status = 'revoked';
    activeConsent.revokedAt = new Date();
    activeConsent.revokedMethod = method;
    activeConsent.metadata.modified = new Date();
    activeConsent.metadata.modifiedBy = subjectId;

    return activeConsent;
  }

  async checkConsent(
    subjectId: string,
    purpose: ConsentPurpose
  ): Promise<{ hasConsent: boolean; record?: ConsentRecord }> {
    const subjectRecords = this.records.get(subjectId) || [];

    const activeConsent = subjectRecords.find(
      r => r.purpose === purpose &&
      r.status === 'granted' &&
      (!r.expiresAt || r.expiresAt > new Date())
    );

    return {
      hasConsent: !!activeConsent,
      record: activeConsent
    };
  }

  async getConsentPreferences(subjectId: string): Promise<Map<ConsentPurpose, ConsentRecord>> {
    const subjectRecords = this.records.get(subjectId) || [];
    const preferences = new Map<ConsentPurpose, ConsentRecord>();

    for (const record of subjectRecords) {
      if (record.status === 'granted' && (!record.expiresAt || record.expiresAt > new Date())) {
        preferences.set(record.purpose, record);
      }
    }

    return preferences;
  }

  async updatePreferences(
    subjectId: string,
    purpose: ConsentPurpose,
    preferences: ConsentPreferences
  ): Promise<ConsentRecord> {
    const subjectRecords = this.records.get(subjectId) || [];
    const record = subjectRecords.find(
      r => r.purpose === purpose && r.status === 'granted'
    );

    if (!record) {
      throw new Error(`No active consent found for ${purpose}`);
    }

    record.preferences = { ...record.preferences, ...preferences };
    record.metadata.modified = new Date();

    return record;
  }

  async withdrawAllConsent(subjectId: string, method: string): Promise<ConsentRecord[]> {
    const subjectRecords = this.records.get(subjectId) || [];
    const revoked: ConsentRecord[] = [];

    for (const record of subjectRecords) {
      if (record.status === 'granted') {
        record.status = 'revoked';
        record.revokedAt = new Date();
        record.revokedMethod = method;
        record.metadata.modified = new Date();
        revoked.push(record);
      }
    }

    return revoked;
  }

  async handlePolicyVersionChange(
    newVersion: string,
    requiresReconsent: ConsentPurpose[]
  ): Promise<Set<string>> // Returns subject IDs requiring re-consent
  {
    const subjectsNeedingReconsent = new Set<string>();

    for (const [subjectId, records] of this.records) {
      for (const record of records) {
        if (requiresReconsent.includes(record.purpose) && record.status === 'granted') {
          // Mark as expired if policy changed
          record.status = 'expired';
          subjectsNeedingReconsent.add(subjectId);
        }
      }
    }

    this.currentPolicyVersion = newVersion;
    return subjectsNeedingReconsent;
  }

  async getConsentAudit(subjectId: string): Promise<ConsentRecord[]> {
    return this.records.get(subjectId) || [];
  }
}
```

### Consent UI Components

```typescript
// compliance/consent/ui-components.ts

export interface ConsentBannerConfig {
  title: string;
  description: string;
  purposes: ConsentPurposeOption[];
  acceptAllLabel: string;
  customizeLabel: string;
  rejectAllLabel: string;
  policyUrl: string;
}

export interface ConsentPurposeOption {
  purpose: ConsentPurpose;
  title: string;
  description: string;
  required: boolean;
  defaultValue: boolean;
  preferences?: ConsentPreferences;
}

export const defaultConsentBanner: ConsentBannerConfig = {
  title: 'We value your privacy',
  description: 'We use cookies and process your data to provide better travel experiences. You can choose which purposes you consent to.',
  purposes: [
    {
      purpose: ConsentPurpose.ANALYTICS,
      title: 'Analytics',
      description: 'Help us improve our services by analyzing how you use them',
      required: false,
      defaultValue: true
    },
    {
      purpose: ConsentPurpose.MARKETING_EMAILS,
      title: 'Marketing Emails',
      description: 'Receive personalized travel deals and offers via email',
      required: false,
      defaultValue: false,
      preferences: {
        frequency: 'weekly',
        categories: ['deals', 'destinations', 'tips']
      }
    },
    {
      purpose: ConsentPurpose.MARKETING_SMS,
      title: 'Marketing SMS',
      description: 'Get urgent deal alerts and booking updates via SMS',
      required: false,
      defaultValue: false
    },
    {
      purpose: ConsentPurpose.PERSONALIZATION,
      title: 'Personalization',
      description: 'Get personalized recommendations based on your preferences',
      required: false,
      defaultValue: true
    },
    {
      purpose: ConsentPurpose.COOKIES,
      title: 'Essential Cookies',
      description: 'Required for the website to function properly',
      required: true,
      defaultValue: true
    }
  ],
  acceptAllLabel: 'Accept All',
  customizeLabel: 'Customize',
  rejectAllLabel: 'Reject All',
  policyUrl: '/privacy-policy'
};
```

---

## Data Retention Policies

### Retention Management

```typescript
// compliance/retention/service.ts

export enum RetentionPeriod {
  IMMEDIATE = 'immediate',           // Delete immediately after purpose
  THIRTY_DAYS = '30_days',
  NINETY_DAYS = '90_days',
  SIX_MONTHS = '6_months',
  ONE_YEAR = '1_year',
  TWO_YEARS = '2_years',
  SEVEN_YEARS = '7_years',          // Legal/tax requirement
  EIGHT_YEARS = '8_years',           // Legal requirement (India)
  TEN_YEARS = '10_years',
  INDEFINITE = 'indefinite'          // Keep until explicitly deleted
}

export interface RetentionPolicy {
  id: string;
  name: string;
  entityType: string;
  retentionPeriod: RetentionPeriod;
  retentionTrigger: 'contract_end' | 'last_interaction' | 'account_closure' | 'fixed_date';
  action: 'delete' | 'anonymize' | 'archive';
  legalBasis: string;
  exceptions: RetentionException[];
}

export interface RetentionException {
  condition: string;
  action: 'extend' | 'retain';
  reason: string;
}

export interface RetentionSchedule {
  entityId: string;
  entityType: string;
  policyId: string;
  triggerDate: Date;
  actionDate: Date;
  status: 'pending' | 'processed' | 'exception' | 'deferred';
  processedAt?: Date;
}

export class DataRetentionService {
  private policies: Map<string, RetentionPolicy> = new Map();
  private schedules: Map<string, RetentionSchedule> = new Map();

  constructor() {
    this.initializePolicies();
  }

  private initializePolicies(): void {
    const policies: RetentionPolicy[] = [
      {
        id: 'RET_INQUIRY',
        name: 'Customer Inquiry Retention',
        entityType: 'inquiry',
        retentionPeriod: RetentionPeriod.TWO_YEARS,
        retentionTrigger: 'last_interaction',
        action: 'delete',
        legalBasis: 'No longer needed for business purpose; customer not converted',
        exceptions: [
          {
            condition: 'inquiry_converted_to_booking',
            action: 'extend',
            reason: 'Linked to active booking, retain according to booking policy'
          }
        ]
      },
      {
        id: 'RET_LEAD',
        name: 'Lead Retention',
        entityType: 'lead',
        retentionPeriod: RetentionPeriod.TWO_YEARS,
        retentionTrigger: 'last_interaction',
        action: 'delete',
        legalBasis: 'Marketing consent validity period',
        exceptions: [
          {
            condition: 'lead_opted_in',
            action: 'extend',
            reason: 'Consent given, extend until consent withdrawn'
          }
        ]
      },
      {
        id: 'RET_BOOKING',
        name: 'Booking Retention',
        entityType: 'booking',
        retentionPeriod: RetentionPeriod.EIGHT_YEARS,
        retentionTrigger: 'contract_end',
        action: 'anonymize',
        legalBasis: 'Legal and tax requirement (Income Tax Act)',
        exceptions: [
          {
            condition: 'open_dispute',
            action: 'extend',
            reason: 'Legal dispute in progress'
          },
          {
            condition: 'ongoing_litigation',
            action: 'retain',
            reason: 'Hold for legal proceedings'
          }
        ]
      },
      {
        id: 'RET_CUSTOMER',
        name: 'Customer Data Retention',
        entityType: 'customer',
        retentionPeriod: RetentionPeriod.EIGHT_YEARS,
        retentionTrigger: 'account_closure',
        action: 'anonymize',
        legalBasis: 'Legal and tax requirement',
        exceptions: [
          {
            condition: 'active_bookings',
            action: 'extend',
            reason: 'Customer has active bookings'
          }
        ]
      },
      {
        id: 'RET_PAYMENT',
        name: 'Payment Record Retention',
        entityType: 'payment',
        retentionPeriod: RetentionPeriod.EIGHT_YEARS,
        retentionTrigger: 'fixed_date',
        action: 'archive',
        legalBasis: 'Financial record keeping requirement',
        exceptions: []
      },
      {
        id: 'RET_MARKETING_CONSENT',
        name: 'Marketing Consent Retention',
        entityType: 'consent_record',
        retentionPeriod: RetentionPeriod.TWO_YEARS,
        retentionTrigger: 'consent_revoked',
        action: 'anonymize',
        legalBasis: 'GDPR consent record retention',
        exceptions: []
      }
    ];

    for (const policy of policies) {
      this.policies.set(policy.id, policy);
    }
  }

  async scheduleRetention(
    entityId: string,
    entityType: string,
    triggerDate: Date
  ): Promise<RetentionSchedule> {
    const policy = this.getPolicyForType(entityType);
    if (!policy) {
      throw new Error(`No retention policy for entity type: ${entityType}`);
    }

    const actionDate = this.calculateActionDate(triggerDate, policy.retentionPeriod);

    const schedule: RetentionSchedule = {
      entityId,
      entityType,
      policyId: policy.id,
      triggerDate,
      actionDate,
      status: 'pending'
    };

    this.schedules.set(`${entityType}:${entityId}`, schedule);

    return schedule;
  }

  async processDueRetentions(): Promise<RetentionSchedule[]> {
    const now = new Date();
    const due: RetentionSchedule[] = [];

    for (const schedule of this.schedules.values()) {
      if (schedule.status === 'pending' && schedule.actionDate <= now) {
        const processed = await this.executeRetention(schedule);
        due.push(processed);
      }
    }

    return due;
  }

  private async executeRetention(schedule: RetentionSchedule): Promise<RetentionSchedule> {
    const policy = this.policies.get(schedule.policyId);

    // Check for exceptions
    const exception = await this.checkExceptions(schedule, policy);
    if (exception) {
      schedule.status = 'exception';
      return schedule;
    }

    // Execute retention action
    switch (policy.action) {
      case 'delete':
        await this.deleteEntity(schedule.entityId, schedule.entityType);
        break;
      case 'anonymize':
        await this.anonymizeEntity(schedule.entityId, schedule.entityType);
        break;
      case 'archive':
        await this.archiveEntity(schedule.entityId, schedule.entityType);
        break;
    }

    schedule.status = 'processed';
    schedule.processedAt = new Date();

    return schedule;
  }

  private getPolicyForType(entityType: string): RetentionPolicy | undefined {
    return Array.from(this.policies.values()).find(p => p.entityType === entityType);
  }

  private calculateActionDate(triggerDate: Date, period: RetentionPeriod): Date {
    const actionDate = new Date(triggerDate);

    switch (period) {
      case RetentionPeriod.IMMEDIATE:
        return new Date(triggerDate);
      case RetentionPeriod.THIRTY_DAYS:
        actionDate.setDate(actionDate.getDate() + 30);
        break;
      case RetentionPeriod.NINETY_DAYS:
        actionDate.setDate(actionDate.getDate() + 90);
        break;
      case RetentionPeriod.SIX_MONTHS:
        actionDate.setMonth(actionDate.getMonth() + 6);
        break;
      case RetentionPeriod.ONE_YEAR:
        actionDate.setFullYear(actionDate.getFullYear() + 1);
        break;
      case RetentionPeriod.TWO_YEARS:
        actionDate.setFullYear(actionDate.getFullYear() + 2);
        break;
      case RetentionPeriod.SEVEN_YEARS:
        actionDate.setFullYear(actionDate.getFullYear() + 7);
        break;
      case RetentionPeriod.EIGHT_YEARS:
        actionDate.setFullYear(actionDate.getFullYear() + 8);
        break;
      case RetentionPeriod.TEN_YEARS:
        actionDate.setFullYear(actionDate.getFullYear() + 10);
        break;
      case RetentionPeriod.INDEFINITE:
        actionDate.setFullYear(2099, 11, 31);
        break;
    }

    return actionDate;
  }

  private async checkExceptions(
    schedule: RetentionSchedule,
    policy?: RetentionPolicy
  ): Promise<boolean> {
    if (!policy || policy.exceptions.length === 0) return false;

    for (const exception of policy.exceptions) {
      const applies = await this.evaluateException(exception, schedule);
      if (applies) {
        return true;
      }
    }

    return false;
  }

  private async evaluateException(
    exception: RetentionException,
    schedule: RetentionSchedule
  ): Promise<boolean> {
    // Check if exception condition applies
    switch (exception.condition) {
      case 'inquiry_converted_to_booking':
        return await this.hasBooking(schedule.entityId);
      case 'lead_opted_in':
        return await this.hasOptedIn(schedule.entityId);
      case 'open_dispute':
        return await this.hasOpenDispute(schedule.entityId);
      case 'ongoing_litigation':
        return await this.hasOngoingLitigation(schedule.entityId);
      case 'active_bookings':
        return await this.hasActiveBookings(schedule.entityId);
      default:
        return false;
    }
  }

  private async deleteEntity(entityId: string, entityType: string): Promise<void> {
    // Delete entity from database
    console.log(`Deleting ${entityType}:${entityId}`);
  }

  private async anonymizeEntity(entityId: string, entityType: string): Promise<void> {
    // Anonymize PII fields
    console.log(`Anonymizing ${entityType}:${entityId}`);
  }

  private async archiveEntity(entityId: string, entityType: string): Promise<void> {
    // Move to archive storage
    console.log(`Archiving ${entityType}:${entityId}`);
  }

  // Exception check helpers
  private async hasBooking(inquiryId: string): Promise<boolean> {
    return false;
  }

  private async hasOptedIn(leadId: string): Promise<boolean> {
    return false;
  }

  private async hasOpenDispute(entityId: string): Promise<boolean> {
    return false;
  }

  private async hasOngoingLitigation(entityId: string): Promise<boolean> {
    return false;
  }

  private async hasActiveBookings(customerId: string): Promise<boolean> {
    return false;
  }

  async getRetentionSchedule(entityId: string, entityType: string): Promise<RetentionSchedule | undefined> {
    return this.schedules.get(`${entityType}:${entityId}`);
  }

  async getDueSchedules(daysAhead = 30): Promise<RetentionSchedule[]> {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() + daysAhead);

    return Array.from(this.schedules.values()).filter(
      s => s.status === 'pending' && s.actionDate <= cutoff
    );
  }
}
```

---

## Data Minimization

### Minimization Engine

```typescript
// compliance/minimization/service.ts

export interface MinimizationRule {
  id: string;
  name: string;
  description: string;
  entityType: string;
  fields: MinimizedField[];
  applyWhen: string; // Condition for applying minimization
}

export interface MinimizedField {
  fieldName: string;
  action: 'exclude' | 'mask' | 'truncate' | 'hash' | 'generalize';
  params?: Record<string, any>;
}

export class DataMinimizationService {
  private rules: MinimizationRule[] = [
    {
      id: 'MIN_MARKETING_EXPORT',
      name: 'Marketing Data Export Minimization',
      description: 'Limit data shared with marketing tools',
      entityType: 'customer',
      fields: [
        { fieldName: 'passport_number', action: 'exclude' },
        { fieldName: 'pan_card', action: 'exclude' },
        { fieldName: 'date_of_birth', action: 'generalize', params: { precision: 'year' } },
        { fieldName: 'phone', action: 'mask', params: { mask: '***-***-****', showLast: 4 } },
        { fieldName: 'address', action: 'truncate', params: { to: 'city' } }
      ],
      applyWhen: 'purpose = marketing_export'
    },
    {
      id: 'MIN_ANALYTICS',
      name: 'Analytics Data Minimization',
      description: 'Anonymize data for analytics platforms',
      entityType: 'booking',
      fields: [
        { fieldName: 'customer_name', action: 'hash' },
        { fieldName: 'customer_email', action: 'hash' },
        { fieldName: 'customer_phone', action: 'hash' },
        { fieldName: 'special_requests', action: 'exclude' }
      ],
      applyWhen: 'purpose = analytics'
    },
    {
      id: 'MIN_CUSTOMER_PORTAL',
      name: 'Customer Portal Data Minimization',
      description: 'Limit sensitive data in customer portal',
      entityType: 'booking',
      fields: [
        { fieldName: 'supplier_cost', action: 'exclude' },
        { fieldName: 'commission_amount', action: 'exclude' },
        { fieldName: 'agent_notes', action: 'exclude' }
      ],
      applyWhen: 'purpose = customer_access'
    }
  ];

  async minimizeData(
    entityType: string,
    data: Record<string, any>,
    purpose: string
  ): Promise<Record<string, any>> {
    const applicableRules = this.rules.filter(
      r => r.entityType === entityType && this.shouldApply(r, purpose)
    );

    let result = { ...data };

    for (const rule of applicableRules) {
      result = this.applyRule(result, rule);
    }

    return result;
  }

  private shouldApply(rule: MinimizationRule, purpose: string): boolean {
    // Simple condition evaluation
    return rule.applyWhen.includes(purpose);
  }

  private applyRule(
    data: Record<string, any>,
    rule: MinimizationRule
  ): Record<string, any> {
    const result = { ...data };

    for (const field of rule.fields) {
      if (field.fieldName in result) {
        result[field.fieldName] = this.minimizeField(
          result[field.fieldName],
          field.action,
          field.params
        );
      }
    }

    return result;
  }

  private minimizeField(
    value: any,
    action: string,
    params?: Record<string, any>
  ): any {
    switch (action) {
      case 'exclude':
        return undefined;

      case 'mask':
        return this.maskValue(value, params);

      case 'truncate':
        return this.truncateValue(value, params);

      case 'hash':
        return this.hashValue(value);

      case 'generalize':
        return this.generalizeValue(value, params);

      default:
        return value;
    }
  }

  private maskValue(value: any, params?: Record<string, any>): string {
    const str = String(value);
    const showLast = params?.showLast || 0;
    const mask = params?.mask || '*';

    if (showLast > 0) {
      const visible = str.slice(-showLast);
      return mask.repeat(str.length - showLast) + visible;
    }

    return mask.repeat(str.length);
  }

  private truncateValue(value: any, params?: Record<string, any>): any {
    if (params?.to === 'city' && typeof value === 'string') {
      // Extract city from address
      const parts = value.split(',').map(p => p.trim());
      return parts[parts.length - 2] || parts[parts.length - 1] || value;
    }

    if (params?.precision === 'year' && value instanceof Date) {
      return value.getFullYear();
    }

    return value;
  }

  private hashValue(value: any): string {
    const crypto = require('crypto');
    return crypto
      .createHash('sha256')
      .update(String(value))
      .digest('hex')
      .substring(0, 16);
  }

  private generalizeValue(value: any, params?: Record<string, any>): any {
    if (params?.precision === 'year' && value instanceof Date) {
      return value.getFullYear();
    }

    if (typeof value === 'number' && params?.bucket) {
      const bucketSize = params.bucket;
      return Math.floor(value / bucketSize) * bucketSize;
    }

    return value;
  }
}
```

---

## Privacy by Design

### Privacy Controls

```typescript
// compliance/privacy/controls.ts

export interface PrivacyControl {
  id: string;
  name: string;
  description: string;
  type: 'access' | 'encryption' | 'anonymization' | 'retention' | 'monitoring';
  implementation: string;
  enabled: boolean;
}

export class PrivacyByDesignService {
  private controls: PrivacyControl[] = [
    {
      id: 'PC_ACCESS_MINIMUM',
      name: 'Minimum Privilege Access',
      description: 'Users have minimum access required for their role',
      type: 'access',
      implementation: 'role_based_access_control',
      enabled: true
    },
    {
      id: 'PC_ENCRYPTION_AT_REST',
      name: 'Encryption at Rest',
      description: 'All sensitive data encrypted at rest',
      type: 'encryption',
      implementation: 'aes_256_gcm',
      enabled: true
    },
    {
      id: 'PC_ENCRYPTION_TRANSIT',
      name: 'Encryption in Transit',
      description: 'All data encrypted during transmission',
      type: 'encryption',
      implementation: 'tls_1_3',
      enabled: true
    },
    {
      id: 'PC_PSEUDONYMIZATION',
      name: 'Pseudonymization',
      description: 'Personal data pseudonymized where possible',
      type: 'anonymization',
      implementation: 'customer_id_hash',
      enabled: true
    },
    {
      id: 'PC_DATA_MINIMIZATION',
      name: 'Data Minimization',
      description: 'Collect only necessary data',
      type: 'access',
      implementation: 'form_field_validation',
      enabled: true
    },
    {
      id: 'PC_PRIVACY_BY_DEFAULT',
      name: 'Privacy by Default',
      description: 'Highest privacy settings by default',
      type: 'access',
      implementation: 'opt_in_consent',
      enabled: true
    },
    {
      id: 'PC_AUDIT_LOGGING',
      name: 'Comprehensive Audit Logging',
      description: 'All data access logged for audit',
      type: 'monitoring',
      implementation: 'structured_logs',
      enabled: true
    },
    {
      id: 'PC_AUTOMATIC_RETENTION',
      name: 'Automatic Data Retention',
      description: 'Data automatically deleted per retention policy',
      type: 'retention',
      implementation: 'retention_scheduler',
      enabled: true
    }
  ];

  async applyPrivacyControls(data: Record<string, any>, context: {
    purpose: string;
    userRole: string;
    consentLevel: string;
  }): Promise<Record<string, any>> {
    let result = { ...data };

    // Apply pseudonymization
    result = await this.pseudonymize(result, context);

    // Apply minimization
    result = await this.minimize(result, context);

    // Apply masking for non-production
    if (context.purpose === 'testing') {
      result = await this.maskForTesting(result);
    }

    return result;
  }

  private async pseudonymize(
    data: Record<string, any>,
    context: any
  ): Promise<Record<string, any>> {
    const result = { ...data };

    // Replace identifying values with pseudonyms
    if (result.email && context.purpose !== 'service_delivery') {
      result.email_pseudonym = this.hash(result.email);
      delete result.email;
    }

    if (result.phone && context.purpose !== 'service_delivery') {
      result.phone_pseudonym = this.hash(result.phone);
      delete result.phone;
    }

    return result;
  }

  private async minimize(
    data: Record<string, any>,
    context: any
  ): Promise<Record<string, any>> {
    const minimizationService = new DataMinimizationService();
    return minimizationService.minimizeData(
      'customer',
      data,
      context.purpose
    );
  }

  private async maskForTesting(data: Record<string, any>): Promise<Record<string, any>> {
    const result = { ...data };

    // Mask all PII for testing
    if (result.email) {
      result.email = this.maskEmail(result.email);
    }

    if (result.phone) {
      result.phone = 'XXXXXXXXXX';
    }

    if (result.name) {
      result.name = 'Test User';
    }

    return result;
  }

  private hash(value: string): string {
    const crypto = require('crypto');
    return crypto
      .createHash('sha256')
      .update(value)
      .digest('hex')
      .substring(0, 16);
  }

  private maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    return `${local[0]}***@${domain}`;
  }

  async getPrivacyControls(): Promise<PrivacyControl[]> {
    return this.controls;
  }

  async updateControlStatus(controlId: string, enabled: boolean): Promise<void> {
    const control = this.controls.find(c => c.id === controlId);
    if (control) {
      control.enabled = enabled;
    }
  }
}
```

---

## Data Protection Impact Assessment

### DPIA Framework

```typescript
// compliance/dpia/service.ts

export enum DPIARiskLevel {
  NEGLIGIBLE = 'negligible',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  VERY_HIGH = 'very_high'
}

export interface DPIA {
  id: string;
  projectName: string;
  projectDescription: string;
  dataTypes: string[];
  dataSubjects: string[];
  processingPurposes: string[];
  riskLevel: DPIARiskLevel;
  risks: DPIARisk[];
  mitigationMeasures: string[];
  assessmentDate: Date;
  assessor: string;
  reviewer: string;
  approvalStatus: 'pending' | 'approved' | 'approved_with_conditions' | 'rejected';
  approvedBy?: string;
  approvedAt?: Date;
  conditions?: string[];
}

export interface DPIARisk {
  id: string;
  category: 'confidentiality' | 'integrity' | 'availability' | 'accountability';
  description: string;
  likelihood: 'rare' | 'unlikely' | 'possible' | 'likely' | 'certain';
  impact: 'negligible' | 'minor' | 'moderate' | 'major' | 'severe';
  riskLevel: DPIARiskLevel;
  mitigation?: string;
}

export class DPIAService {
  private assessments: Map<string, DPIA> = new Map();

  async createAssessment(
    projectName: string,
    projectDescription: string,
    processingPurposes: string[]
  ): Promise<DPIA> {
    const assessment: DPIA = {
      id: `DPIA_${Date.now()}`,
      projectName,
      projectDescription,
      dataTypes: [],
      dataSubjects: [],
      processingPurposes,
      riskLevel: DPIARiskLevel.LOW,
      risks: [],
      mitigationMeasures: [],
      assessmentDate: new Date(),
      assessor: 'data-protection-officer',
      reviewer: 'compliance-team',
      approvalStatus: 'pending'
    };

    this.assessments.set(assessment.id, assessment);

    return assessment;
  }

  async assessRisks(assessmentId: string): Promise<DPIARisk[]> {
    const assessment = this.assessments.get(assessmentId);
    if (!assessment) throw new Error('Assessment not found');

    const risks: DPIARisk[] = [];

    // Analyze risks based on data types and purposes
    if (assessment.processingPurposes.includes('profiling')) {
      risks.push({
        id: 'risk_001',
        category: 'confidentiality',
        description: 'Profiling may lead to discriminatory outcomes',
        likelihood: 'possible',
        impact: 'moderate',
        riskLevel: DPIARiskLevel.MEDIUM,
        mitigation: 'Implement profiling safeguards and manual review for significant decisions'
      });
    }

    if (assessment.processingPurposes.includes('automated_decision')) {
      risks.push({
        id: 'risk_002',
        category: 'accountability',
        description: 'Automated decision making may lack transparency',
        likelihood: 'likely',
        impact: 'moderate',
        riskLevel: DPIARiskLevel.HIGH,
        mitigation: 'Provide right to human intervention and explanation of decisions'
      });
    }

    if (assessment.dataTypes.includes('special_category')) {
      risks.push({
        id: 'risk_003',
        category: 'confidentiality',
        description: 'Processing special category data requires explicit consent',
        likelihood: 'unlikely',
        impact: 'major',
        riskLevel: DPIARiskLevel.HIGH,
        mitigation: 'Obtain explicit consent for special category data processing'
      });
    }

    if (assessment.processingPurposes.includes('cross_border_transfer')) {
      risks.push({
        id: 'risk_004',
        category: 'confidentiality',
        description: 'Cross-border data transfer may not provide adequate protection',
        likelihood: 'unlikely',
        impact: 'major',
        riskLevel: DPIARiskLevel.MEDIUM,
        mitigation: 'Use standard contractual clauses or adequacy decision'
      });
    }

    assessment.risks = risks;
    assessment.riskLevel = this.calculateOverallRisk(risks);

    return risks;
  }

  private calculateOverallRisk(risks: DPIARisk[]): DPIARiskLevel {
    if (risks.length === 0) return DPIARiskLevel.NEGLIGIBLE;

    const riskScores = {
      [DPIARiskLevel.NEGLIGIBLE]: 1,
      [DPIARiskLevel.LOW]: 2,
      [DPIARiskLevel.MEDIUM]: 3,
      [DPIARiskLevel.HIGH]: 4,
      [DPIARiskLevel.VERY_HIGH]: 5
    };

    const maxRisk = risks.reduce((max, risk) => {
      const score = riskScores[risk.riskLevel];
      const maxScore = riskScores[max];
      return score > maxScore ? risk.riskLevel : max;
    }, DPIARiskLevel.NEGLIGIBLE);

    return maxRisk;
  }

  async submitAssessment(assessmentId: string): Promise<DPIA> {
    const assessment = this.assessments.get(assessmentId);
    if (!assessment) throw new Error('Assessment not found');

    // Route for review based on risk level
    if (assessment.riskLevel === DPIARiskLevel.HIGH || assessment.riskLevel === DPIARiskLevel.VERY_HIGH) {
      // Requires full review
      assessment.approvalStatus = 'pending';
    } else {
      // Can be auto-approved
      assessment.approvalStatus = 'approved';
      assessment.approvedBy = 'system';
      assessment.approvedAt = new Date();
    }

    return assessment;
  }

  async reviewAssessment(
    assessmentId: string,
    decision: 'approve' | 'approve_with_conditions' | 'reject',
    reviewer: string,
    conditions?: string[]
  ): Promise<DPIA> {
    const assessment = this.assessments.get(assessmentId);
    if (!assessment) throw new Error('Assessment not found');

    switch (decision) {
      case 'approve':
        assessment.approvalStatus = 'approved';
        break;
      case 'approve_with_conditions':
        assessment.approvalStatus = 'approved_with_conditions';
        assessment.conditions = conditions;
        break;
      case 'reject':
        assessment.approvalStatus = 'rejected';
        break;
    }

    assessment.approvedBy = reviewer;
    assessment.approvedAt = new Date();

    return assessment;
  }

  async getAssessment(assessmentId: string): Promise<DPIA | undefined> {
    return this.assessments.get(assessmentId);
  }

  async listAssessments(filters?: {
    riskLevel?: DPIARiskLevel;
    status?: string;
    assessor?: string;
  }): Promise<DPIA[]> {
    let results = Array.from(this.assessments.values());

    if (filters) {
      if (filters.riskLevel) {
        results = results.filter(a => a.riskLevel === filters.riskLevel);
      }
      if (filters.status) {
        results = results.filter(a => a.approvalStatus === filters.status);
      }
      if (filters.assessor) {
        results = results.filter(a => a.assessor === filters.assessor);
      }
    }

    return results.sort((a, b) => b.assessmentDate.getTime() - a.assessmentDate.getTime());
  }
}
```

---

## Cross-Border Transfers

### Transfer Compliance

```typescript
// compliance/cross-border/service.ts

export enum TransferMechanism {
  ADEQUACY_DECISION = 'adequacy_decision',     // EU has adequacy decision for country
  STANDARD_CONTRACTUAL_CLAUSES = 'scc',        // Standard contractual clauses
  BINDING_CORPORATE_RULES = 'bcr',            // Binding corporate rules
  LEGAL_EXCEPTION = 'legal_exception'          // Specific legal exception
}

export interface CrossBorderTransfer {
  id: string;
  dataIdentifier: string;
  fromCountry: string;
  toCountry: string;
  dataTypes: string[];
  dataCategories: string[];
  mechanism: TransferMechanism;
  mechanismDetails: string;
  legalBasis: string;
  riskAssessment: string;
  approved: boolean;
  approvedBy: string;
  approvedAt: Date;
  reviewDate: Date;
}

export class CrossBorderTransferService {
  private transfers: Map<string, CrossBorderTransfer> = new Map();

  // Countries with adequacy decisions (as of 2024)
  private adequacyCountries = new Set([
    'JP', // Japan
    'UK', // United Kingdom
    'CA', // Canada (commercial)
    'CH', // Switzerland
    'IS', // Iceland
    'NO', // Norway
    'LI', // Liechtenstein
    'KR', // South Korea (limited)
    'US'  // United States (Data Privacy Framework - limited)
  ]);

  async registerTransfer(
    dataIdentifier: string,
    fromCountry: string,
    toCountry: string,
    dataTypes: string[],
    mechanism: TransferMechanism
  ): Promise<CrossBorderTransfer> {
    const transfer: CrossBorderTransfer = {
      id: `XBT_${Date.now()}`,
      dataIdentifier,
      fromCountry,
      toCountry,
      dataTypes,
      dataCategories: this.categorizeData(dataTypes),
      mechanism,
      mechanismDetails: this.getMechanismDetails(mechanism, toCountry),
      legalBasis: await this.determineLegalBasis(fromCountry, toCountry),
      riskAssessment: await this.assessTransferRisk(toCountry, dataTypes),
      approved: false,
      approvedBy: 'pending',
      approvedAt: new Date(),
      reviewDate: this.calculateReviewDate()
    };

    this.transfers.set(transfer.id, transfer);

    return transfer;
  }

  private categorizeData(dataTypes: string[]): string[] {
    const categories: string[] = [];

    if (dataTypes.some(t => t.includes('name') || t.includes('email'))) {
      categories.push('personal_data');
    }

    if (dataTypes.some(t => t.includes('health') || t.includes('medical'))) {
      categories.push('special_category');
    }

    if (dataTypes.some(t => t.includes('card') || t.includes('bank'))) {
      categories.push('financial_data');
    }

    return categories;
  }

  private getMechanismDetails(mechanism: TransferMechanism, toCountry: string): string {
    switch (mechanism) {
      case TransferMechanism.ADEQUACY_DECISION:
        return `Adequacy decision exists for ${toCountry}`;

      case TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES:
        return 'European Commission Standard Contractual Clauses (SCC)';

      case TransferMechanism.BINDING_CORPORATE_RULES:
        return 'Internal binding corporate rules approved by DPA';

      case TransferMechanism.LEGAL_EXCEPTION:
        return 'Legal exception under Article 49 GDPR';

      default:
        return 'No mechanism specified';
    }
  }

  private async determineLegalBasis(fromCountry: string, toCountry: string): Promise<string> {
    // Check if adequacy decision exists
    if (this.adequacyCountries.has(toCountry)) {
      return `Adequacy decision for ${toCountry} under Article 45 GDPR`;
    }

    // Check if within same economic area
    if (fromCountry === toCountry) {
      return 'Domestic transfer - no cross-border mechanism required';
    }

    return 'Standard contractual clauses required';
  }

  private async assessTransferRisk(toCountry: string, dataTypes: string[]): Promise<string> {
    let risk = 'low';

    // Assess based on destination country
    const highRiskCountries = ['CN', 'RU', 'IR', 'KP'];
    if (highRiskCountries.includes(toCountry)) {
      risk = 'high';
    }

    // Assess based on data types
    if (dataTypes.some(t => t.includes('special_category'))) {
      risk = risk === 'high' ? 'very_high' : 'medium';
    }

    return risk;
  }

  private calculateReviewDate(): Date {
    const reviewDate = new Date();
    reviewDate.setFullYear(reviewDate.getFullYear() + 1);
    return reviewDate;
  }

  async getTransfer(transferId: string): Promise<CrossBorderTransfer | undefined> {
    return this.transfers.get(transferId);
  }

  async approveTransfer(
    transferId: string,
    approver: string
  ): Promise<CrossBorderTransfer> {
    const transfer = this.transfers.get(transferId);
    if (!transfer) throw new Error('Transfer not found');

    transfer.approved = true;
    transfer.approvedBy = approver;
    transfer.approvedAt = new Date();

    return transfer;
  }

  async getTransfersRequiringReview(): Promise<CrossBorderTransfer[]> {
    const now = new Date();

    return Array.from(this.transfers.values()).filter(
      t => !t.approved || t.reviewDate <= now
    );
  }
}
```

---

## Audit & Reporting

### Compliance Audit

```typescript
// compliance/audit/service.ts

export interface ComplianceAudit {
  id: string;
  auditType: 'internal' | 'external' | 'dpa' | 'customer';
  scope: string[];
  period: {
    from: Date;
    to: Date;
  };
  findings: AuditFinding[];
  recommendations: string[];
  auditedBy: string;
  auditedAt: Date;
  status: 'in_progress' | 'completed' | 'remediation_required';
}

export interface AuditFinding {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  description: string;
  evidence: string[];
  affectedSystems: string[];
  remediationRequired: boolean;
  remediationPlan?: string;
  dueDate?: Date;
}

export class ComplianceAuditService {
  private audits: Map<string, ComplianceAudit> = new Map();

  async performAudit(
    auditType: ComplianceAudit['auditType'],
    scope: string[],
    period: { from: Date; to: Date }
  ): Promise<ComplianceAudit> {
    const audit: ComplianceAudit = {
      id: `AUDIT_${Date.now()}`,
      auditType,
      scope,
      period,
      findings: [],
      recommendations: [],
      auditedBy: 'compliance-team',
      auditedAt: new Date(),
      status: 'in_progress'
    };

    // Run audit checks
    audit.findings = await this.runAuditChecks(audit);
    audit.recommendations = this.generateRecommendations(audit.findings);
    audit.status = audit.findings.some(f => f.severity === 'critical') ? 'remediation_required' : 'completed';

    this.audits.set(audit.id, audit);

    return audit;
  }

  private async runAuditChecks(audit: ComplianceAudit): Promise<AuditFinding[]> {
    const findings: AuditFinding[] = [];

    // Check 1: Legal basis documentation
    const legalBasisCheck = await this.checkLegalBasisCoverage(audit.period);
    if (legalBasisCheck.gaps > 0) {
      findings.push({
        id: 'find_001',
        severity: 'high',
        category: 'legal_basis',
        description: `${legalBasisCheck.gaps} entities missing legal basis documentation`,
        evidence: legalBasisCheck.evidence,
        affectedSystems: ['customers', 'bookings'],
        remediationRequired: true,
        remediationPlan: 'Document legal basis for all processing activities',
        dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
      });
    }

    // Check 2: Data retention compliance
    const retentionCheck = await this.checkRetentionCompliance(audit.period);
    if (retentionCheck.violations > 0) {
      findings.push({
        id: 'find_002',
        severity: 'high',
        category: 'retention',
        description: `${retentionCheck.violations} records past retention period`,
        evidence: retentionCheck.evidence,
        affectedSystems: ['database'],
        remediationRequired: true,
        remediationPlan: 'Execute retention policies for expired records',
        dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000)
      });
    }

    // Check 3: Data subject request response time
    const dsrCheck = await this.checkDSRResponseTimes(audit.period);
    if (dsrCheck.overdue > 0) {
      findings.push({
        id: 'find_003',
        severity: 'medium',
        category: 'dsr_response',
        description: `${dsrCheck.overdue} data subject requests exceeded 30-day deadline`,
        evidence: dsrCheck.evidence,
        affectedSystems: ['dsr_portal'],
        remediationRequired: true,
        remediationPlan: 'Implement workflow automation for faster DSR processing'
      });
    }

    // Check 4: Consent management
    const consentCheck = await this.checkConsentCompliance(audit.period);
    if (consentCheck.issues > 0) {
      findings.push({
        id: 'find_004',
        severity: 'medium',
        category: 'consent',
        description: `${consentCheck.issues} consent records missing or invalid`,
        evidence: consentCheck.evidence,
        affectedSystems: ['consent_db'],
        remediationRequired: true,
        remediationPlan: 'Implement consent validation and renewal process'
      });
    }

    // Check 5: Access control
    const accessCheck = await this.checkAccessControls(audit.period);
    if (accessCheck.violations > 0) {
      findings.push({
        id: 'find_005',
        severity: 'critical',
        category: 'access_control',
        description: `${accessCheck.violations} unauthorized access attempts detected`,
        evidence: accessCheck.evidence,
        affectedSystems: ['api', 'database'],
        remediationRequired: true,
        remediationPlan: 'Review and tighten access controls; investigate violations',
        dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      });
    }

    return findings;
  }

  private generateRecommendations(findings: AuditFinding[]): string[] {
    const recommendations: string[] = [];

    if (findings.some(f => f.category === 'legal_basis')) {
      recommendations.push('Implement automated legal basis capture at data entry points');
    }

    if (findings.some(f => f.category === 'retention')) {
      recommendations.push('Schedule automated retention policy execution');
    }

    if (findings.some(f => f.category === 'dsr_response')) {
      recommendations.push('Deploy DSR automation workflow');
    }

    if (findings.some(f => f.category === 'consent')) {
      recommendations.push('Implement consent management platform');
    }

    if (findings.some(f => f.category === 'access_control')) {
      recommendations.push('Conduct quarterly access reviews');
    }

    return recommendations;
  }

  private async checkLegalBasisCoverage(period: any): Promise<any> {
    return { gaps: 0, evidence: [] };
  }

  private async checkRetentionCompliance(period: any): Promise<any> {
    return { violations: 0, evidence: [] };
  }

  private async checkDSRResponseTimes(period: any): Promise<any> {
    return { overdue: 0, evidence: [] };
  }

  private async checkConsentCompliance(period: any): Promise<any> {
    return { issues: 0, evidence: [] };
  }

  private async checkAccessControls(period: any): Promise<any> {
    return { violations: 0, evidence: [] };
  }

  async getAudit(auditId: string): Promise<ComplianceAudit | undefined> {
    return this.audits.get(auditId);
  }

  async generateComplianceReport(
    period: { from: Date; to: Date }
  ): Promise<ComplianceReport> {
    return {
      period,
      generatedAt: new Date(),
      summary: {
        totalAudits: 0,
        criticalFindings: 0,
        highFindings: 0,
        mediumFindings: 0,
        lowFindings: 0,
        overallScore: 100
      },
      dataSubjectRequests: {
        total: 0,
        completed: 0,
        pending: 0,
        overdue: 0,
        averageResponseTime: 0
      },
      consentManagement: {
        totalRecords: 0,
        granted: 0,
        denied: 0,
        revoked: 0
      },
      dataRetention: {
        entitiesProcessed: 0,
        entitiesDeleted: 0,
        entitiesAnonymized: 0
      },
      crossBorderTransfers: {
        total: 0,
        approved: 0,
        pending: 0
      },
      recommendations: []
    };
  }
}

export interface ComplianceReport {
  period: { from: Date; to: Date };
  generatedAt: Date;
  summary: {
    totalAudits: number;
    criticalFindings: number;
    highFindings: number;
    mediumFindings: number;
    lowFindings: number;
    overallScore: number;
  };
  dataSubjectRequests: {
    total: number;
    completed: number;
    pending: number;
    overdue: number;
    averageResponseTime: number;
  };
  consentManagement: {
    totalRecords: number;
    granted: number;
    denied: number;
    revoked: number;
  };
  dataRetention: {
    entitiesProcessed: number;
    entitiesDeleted: number;
    entitiesAnonymized: number;
  };
  crossBorderTransfers: {
    total: number;
    approved: number;
    pending: number;
  };
  recommendations: string[];
}
```

---

## API Specification

### Compliance API

```typescript
// api/compliance/routes.ts

import { z } from 'zod';

// Schemas
const DataSubjectRequestSchema = z.object({
  id: z.string(),
  subjectId: z.string(),
  right: z.enum(['access', 'rectification', 'erasure', 'portability', 'objection', 'restriction']),
  status: z.enum(['pending', 'processing', 'completed', 'rejected', 'partially_completed']),
  requestDate: z.date(),
  responseDeadline: z.date(),
  findings: z.array(z.any()),
  actionsTaken: z.array(z.any())
});

const ConsentRecordSchema = z.object({
  id: z.string(),
  subjectId: z.string(),
  purpose: z.string(),
  status: z.enum(['granted', 'denied', 'revoked', 'expired']),
  grantedAt: z.date(),
  preferences: z.record(z.any())
});

const DPIASchema = z.object({
  id: z.string(),
  projectName: z.string(),
  riskLevel: z.enum(['negligible', 'low', 'medium', 'high', 'very_high']),
  risks: z.array(z.object({
    category: z.string(),
    description: z.string(),
    likelihood: z.string(),
    impact: z.string(),
    riskLevel: z.string()
  })),
  approvalStatus: z.enum(['pending', 'approved', 'approved_with_conditions', 'rejected'])
});

// Routes
export const complianceRoutes = {
  // Data Subject Rights
  'POST /api/compliance/dsr': {
    summary: 'Submit data subject request',
    request: z.object({
      subjectId: z.string(),
      right: z.enum(['access', 'rectification', 'erasure', 'portability', 'objection', 'restriction']),
      scope: z.array(z.string()).optional()
    }),
    response: DataSubjectRequestSchema
  },

  'GET /api/compliance/dsr/:requestId': {
    summary: 'Get data subject request status',
    params: z.object({
      requestId: z.string()
    }),
    response: DataSubjectRequestSchema
  },

  'GET /api/compliance/dsr': {
    summary: 'List data subject requests',
    query: z.object({
      subjectId: z.string().optional(),
      status: z.string().optional(),
      right: z.string().optional()
    }),
    response: z.array(DataSubjectRequestSchema)
  },

  // Consent
  'POST /api/compliance/consent': {
    summary: 'Grant consent',
    request: z.object({
      subjectId: z.string(),
      purpose: z.enum(['marketing_emails', 'marketing_sms', 'newsletter', 'analytics', 'personalization', 'third_party_sharing', 'cookies']),
      method: z.string(),
      preferences: z.record(z.any()).optional()
    }),
    response: ConsentRecordSchema
  },

  'DELETE /api/compliance/consent/:subjectId/:purpose': {
    summary: 'Revoke consent',
    params: z.object({
      subjectId: z.string(),
      purpose: z.string()
    }),
    response: ConsentRecordSchema
  },

  'GET /api/compliance/consent/:subjectId': {
    summary: 'Get consent preferences',
    params: z.object({
      subjectId: z.string()
    }),
    response: z.record(z.boolean())
  },

  // Retention
  'GET /api/compliance/retention/schedule': {
    summary: 'Get retention schedule',
    query: z.object({
      entityId: z.string().optional(),
      entityType: z.string().optional()
    }),
    response: z.array(z.object({
      entityId: z.string(),
      entityType: z.string(),
      actionDate: z.date(),
      status: z.string()
    }))
  },

  // DPIA
  'POST /api/compliance/dpia': {
    summary: 'Create DPIA',
    request: z.object({
      projectName: z.string(),
      projectDescription: z.string(),
      processingPurposes: z.array(z.string())
    }),
    response: DPIASchema
  },

  'POST /api/compliance/dpia/:assessmentId/assess': {
    summary: 'Assess DPIA risks',
    params: z.object({
      assessmentId: z.string()
    }),
    response: z.array(z.object({
      category: z.string(),
      description: z.string(),
      riskLevel: z.string(),
      mitigation: z.string()
    }))
  },

  'POST /api/compliance/dpia/:assessmentId/submit': {
    summary: 'Submit DPIA for approval',
    params: z.object({
      assessmentId: z.string()
    }),
    response: DPIASchema
  },

  // Reports
  'GET /api/compliance/report': {
    summary: 'Generate compliance report',
    query: z.object({
      from: z.string().datetime(),
      to: z.string().datetime()
    }),
    response: z.object({
      period: z.object({
        from: z.date(),
        to: z.date()
      }),
      summary: z.object({
        totalAudits: z.number(),
        criticalFindings: z.number(),
        overallScore: z.number()
      }),
      dataSubjectRequests: z.object({
        total: z.number(),
        completed: z.number(),
        averageResponseTime: z.number()
      })
    })
  },

  // Audit
  'POST /api/compliance/audit': {
    summary: 'Perform compliance audit',
    request: z.object({
      auditType: z.enum(['internal', 'external', 'dpa', 'customer']),
      scope: z.array(z.string()),
      from: z.string().datetime(),
      to: z.string().datetime()
    }),
    response: z.object({
      id: z.string(),
      findings: z.array(z.object({
        severity: z.string(),
        category: z.string(),
        description: z.string()
      })),
      recommendations: z.array(z.string())
    })
  }
};
```

---

## Testing Scenarios

### Compliance Tests

```typescript
// tests/compliance/scenarios.ts

interface TestScenario {
  name: string;
  description: string;
  test: () => Promise<void>;
}

export const complianceTests: TestScenario[] = [
  {
    name: 'DSR Access Request',
    description: 'Verify data subject access request processing',
    test: async () => {
      const service = new DataSubjectRightsService(new LegalBasisService());
      const request = await service.submitRequest('customer-123', DataSubjectRight.ACCESS);

      expect(request.status).toBe('pending');
      expect(request.responseDeadline).toBeDefined();
    }
  },

  {
    name: 'Consent Granting',
    description: 'Verify consent can be granted and checked',
    test: async () => {
      const service = new ConsentManagementService();
      await service.grantConsent('customer-123', ConsentPurpose.MARKETING_EMAILS, 'web_form');

      const check = await service.checkConsent('customer-123', ConsentPurpose.MARKETING_EMAILS);
      expect(check.hasConsent).toBe(true);
    }
  },

  {
    name: 'Consent Revocation',
    description: 'Verify consent can be revoked',
    test: async () => {
      const service = new ConsentManagementService();
      await service.grantConsent('customer-123', ConsentPurpose.NEWSLETTER, 'email_link');
      await service.revokeConsent('customer-123', ConsentPurpose.NEWSLETTER, 'email');

      const check = await service.checkConsent('customer-123', ConsentPurpose.NEWSLETTER);
      expect(check.hasConsent).toBe(false);
    }
  },

  {
    name: 'Data Minimization',
    description: 'Verify data is minimized for export',
    test: async () => {
      const service = new DataMinimizationService();
      const data = {
        name: 'John Doe',
        email: 'john@example.com',
        phone: '+91 98765 43210',
        passport: 'A1234567',
        address: '123 Main St, Mumbai, MH 400001'
      };

      const minimized = await service.minimizeData('customer', data, 'marketing_export');

      expect(minimized.name).toBeDefined();
      expect(minimized.email).toBeDefined();
      expect(minimized.passport).toBeUndefined();
      expect(minimized.phone).toMatch(/\*{8,}/);
    }
  },

  {
    name: 'Retention Scheduling',
    description: 'Verify retention schedules are created',
    test: async () => {
      const service = new DataRetentionService();
      const schedule = await service.scheduleRetention('booking-123', 'booking', new Date());

      expect(schedule.entityId).toBe('booking-123');
      expect(schedule.status).toBe('pending');
      expect(schedule.actionDate).toBeDefined();
    }
  }
];
```

---

## Metrics & Monitoring

### Compliance KPIs

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| **DSR Response Time** | Average time to respond to DSRs | < 15 days | > 25 days |
| **DSR Overdue Rate** | % of DSRs past 30-day deadline | 0% | > 5% |
| **Consent Coverage** | % of contacts with consent recorded | 100% | < 95% |
| **Retention Compliance** | % of records processed on time | 100% | < 98% |
| **Legal Basis Coverage** | % of entities with legal basis | 100% | < 95% |
| **DPIA Completion** | % of high-risk projects with DPIA | 100% | < 100% |
| **Audit Findings Closed** | % of audit findings remediated | > 90% | < 80% |

### Dashboard Queries

```promql
# DSR response time
histogram_quantile(0.95, sum(rate(dsr_response_time_seconds_bucket[30d])) by (le))

# Consent coverage
sum(consent_records_total) / sum(customer_contacts_total) * 100

# Retention compliance
sum(retention_processed_total) / sum(retention_scheduled_total) * 100

# DSRs by status
sum by (status) (dsr_requests_total)

# Compliance score
compliance_overall_score{domain="gdpr"}
```

---

**Document Version:** 1.0

**Last Updated:** 2026-04-26

**Related Documents:**
- [DATA_GOVERNANCE_MASTER_INDEX.md](./DATA_GOVERNANCE_MASTER_INDEX.md)
- [DATA_GOVERNANCE_01_QUALITY.md](./DATA_GOVERNANCE_01_QUALITY.md)
- [DATA_GOVERNANCE_02_LINEAGE.md](./DATA_GOVERNANCE_02_LINEAGE.md)
- [DATA_GOVERNANCE_03_CATALOG.md](./DATA_GOVERNANCE_03_CATALOG.md)
