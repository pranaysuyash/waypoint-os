# CUSTOMER_PORTAL_05: Security Deep Dive

> Customer Portal — Privacy, Consent, Data Protection, and Security Compliance

---

## Table of Contents

1. [Overview](#overview)
2. [Security Architecture](#security-architecture)
3. [Data Privacy](#data-privacy)
4. [Consent Management](#consent-management)
5. [Compliance](#compliance)
6. [Threat Model](#threat-model)
7. [Security Best Practices](#security-best-practices)
8. [Incident Response](#incident-response)

---

## Overview

The Customer Portal handles sensitive customer data, payment information, and travel documents. Security and privacy are foundational requirements, not afterthoughts.

### Security Principles

```
┌────────────────────────────────────────────────────────────────────────────┐
│                      CUSTOMER PORTAL SECURITY PRINCIPLES                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  1. DEFENSE IN DEPTH                                                      │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Multiple security layers                                     │  │
│     │ • No single point of failure                                   │  │
│     │ • Compromise containment                                      │  │
│     │ • Redundant controls                                          │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  2. LEAST PRIVILEGE                                                       │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Minimum required access                                       │  │
│     │ • Customer-scoped data only                                    │  │
│     │ • Time-limited sessions                                        │  │
│     │ • Role-based permissions                                       │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  3. PRIVACY BY DESIGN                                                     │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Data minimization                                             │  │
│     │ • Privacy-preserving defaults                                  │  │
│     │ • Customer control over data                                   │  │
│     │ • Transparent data usage                                       │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  4. SECURE BY DEFAULT                                                    │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Secure defaults, opt-in for changes                           │  │
│     │ • Encryption everywhere                                         │  │
│     │ • Authentication required                                       │  │
│     │ • Audit logging enabled                                         │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  5. COMPLIANCE READINESS                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • GDPR compliance                                               │  │
│     │ • PCI DSS for payments                                         │  │
│     │ • Data protection regulations                                   │  │
│     │ • Industry best practices                                      │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Layered Security Model

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       SECURITY LAYERS                                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 1: PERIMETER                                                   │  │
│  │  • DDoS protection (Cloudflare/AWS Shield)                          │  │
│  │  • WAF (Web Application Firewall)                                   │  │
│  │  • Rate limiting per IP and per user                                │  │
│  │  • Bot detection and mitigation                                    │  │
│  │  • Geo-blocking (optional)                                         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 2: TRANSPORT                                                   │  │
│  │  • TLS 1.3 only (no SSL, no TLS 1.0-1.2)                          │  │
│  │  • HSTS headers with preload                                       │  │
│  │  • Certificate pinning (mobile apps)                               │  │
│  │  • Encrypted DNS (DoH/DoT)                                         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 3: APPLICATION                                                 │  │
│  │  • JWT-based authentication with short expiry                       │  │
│  │  • CSRF protection for state-changing operations                    │  │
│  │  • Input validation and sanitization                                │  │
│  │  • Output encoding and escaping                                     │  │
│  │  • SQL injection prevention (parameterized queries)                │  │
│  │  • XSS prevention (Content Security Policy)                        │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 4: AUTHORIZATION                                              │  │
│  │  • Customer data isolation (row-level security)                    │  │
│  │  • Permission checks on every data access                          │  │
│  │  • API rate limiting per customer                                  │  │
│  │  • Session management with revocation                              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 5: DATA                                                        │  │
│  │  • Encryption at rest (AES-256)                                    │  │
│  │  • PII data encryption in database                                  │  │
│  │  • Secure document storage with signed URLs                        │  │
│  │  • Payment data via PCI-compliant processors only                   │  │
│  │  • Regular backups with encryption                                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 6: MONITORING & AUDIT                                          │  │
│  │  • Comprehensive audit logging                                     │  │
│  │  • Real-time threat detection                                     │  │
│  │  • Anomaly detection (behavioral analysis)                        │  │
│  │  • Security event correlation                                      │  │
│  │  • Regular security assessments                                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Security Headers Configuration

```typescript
// security/headers.ts
export const securityHeaders = {
  // Content Security Policy
  'Content-Security-Policy': [
    // Default to same-origin
    "default-src 'self';",

    // Scripts from self and trusted CDNs
    "script-src 'self' 'nonce-{random}' https://cdn.plaid.com https://js.stripe.com;",

    // Styles can include inline for nonce
    "style-src 'self' 'nonce-{random}' https://fonts.googleapis.com;",

    // Images can be from any HTTPS source (for travel content)
    "img-src 'self' data: https: blob:;",

    // Connect to specific APIs only
    "connect-src 'self' https://api.stripe.com https://plaid.com;",

    // No frames except for payment processors
    "frame-src https://js.stripe.com https://plaid.com;",

    // No plugins
    "object-src 'none';",

    // Base URI
    "base-uri 'self';",

    // Form actions only to self
    "form-action 'self';",

    // Block mixed content
    "block-all-mixed-content;",

    // Upgrade insecure requests
    "upgrade-insecure-requests;",
  ].join(' '),

  // HSTS
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

  // Prevent clickjacking
  'X-Frame-Options': 'DENY',

  // Prevent MIME type sniffing
  'X-Content-Type-Options': 'nosniff',

  // XSS protection (legacy, CSP is primary)
  'X-XSS-Protection': '1; mode=block',

  // Referrer policy
  'Referrer-Policy': 'strict-origin-when-cross-origin',

  // Permissions policy
  'Permissions-Policy': [
    'geography=()',
    'geolocation=()',
    'camera=()',
    'microphone=()',
    'payment=(self)',
  ].join(', '),

  // Cache control for sensitive pages
  'Cache-Control': 'no-store, no-cache, must-revalidate, private',
};

// CSP nonce middleware
export function addCSPNonce(req: Request, res: Response, next: NextFunction) {
  const nonce = crypto.randomBytes(16).toString('base64');
  res.locals.nonce = nonce;
  next();
}
```

### Request Validation

```typescript
// security/validation.ts
import { z } from 'zod';

// Customer input validation schemas
export const customerSchemas = {
  // Authentication
  loginInitiate: z.object({
    identifier: z.string().email().or(z.string().regex(/^\+?[1-9]\d{1,14}$/)),
    channel: z.enum(['email', 'sms', 'whatsapp']),
  }),

  loginVerify: z.object({
    identifier: z.string(),
    otp: z.string().length(6).regex(/^\d+$/),
  }),

  // Trip viewing
  viewTrip: z.object({
    tripId: z.string().uuid(),
  }),

  // Messaging
  sendMessage: z.object({
    tripId: z.string().uuid(),
    content: z.string().min(1).max(5000),
    attachments: z.array(z.string().url()).max(10).optional(),
  }),

  // Profile updates
  updateProfile: z.object({
    name: z.string().min(1).max(100).optional(),
    phone: z.string().regex(/^\+?[1-9]\d{1,14}$/).optional(),
    passportNumber: z.string().regex(/^[A-Z0-9<]{9}$/).optional(),
    passportExpiry: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  }),

  // Payment initiation
  initiatePayment: z.object({
    tripId: z.string().uuid(),
    amount: z.number().positive().max(1000000),
    currency: z.string().length(3).regex(/^[A-Z]{3}$/),
    method: z.enum(['card', 'bank_transfer', 'upi']),
  }),
};

// Sanitization helpers
export function sanitizeHtml(input: string): string {
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
}

export function sanitizeSql(input: string): string {
  return input.replace(/['"\\]/g, '');
}

// File upload validation
export function validateDocumentUpload(file: File): { valid: boolean; error?: string } {
  const maxSize = 10 * 1024 * 1024; // 10MB
  const allowedTypes = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/webp',
  ];

  if (file.size > maxSize) {
    return { valid: false, error: 'File size exceeds 10MB limit' };
  }

  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: 'Only PDF, JPEG, PNG, and WebP files are allowed' };
  }

  // Scan for malware (placeholder)
  // await scanForMalware(file);

  return { valid: true };
}
```

---

## Data Privacy

### Data Classification

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        DATA CLASSIFICATION                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  PUBLIC                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  • Agency name and logo                                            │  │
│  │  • Public destination information                                   │  │
│  │  • General travel advice                                           │  │
│  │  • Marketing content (with consent)                                │  │
│  │                                                                     │  │
│  │  Protection: None required                                          │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  INTERNAL                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  • Trip status (non-sensitive)                                     │  │
│  │  • Booking references (non-PII)                                    │  │
│  │  • General itinerary                                               │  │
│  │  • Agent information (business contact)                            │  │
│  │                                                                     │  │
│  │  Protection: Customer access only, no external sharing              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  CONFIDENTIAL                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  • Customer PII (name, email, phone)                               │  │
│  │  • Trip details (dates, destinations)                              │  │
│  │  • Traveler information (names, relationships)                      │  │
│  │  • Payment history (amounts, dates)                                │  │
│  │  • Messages between customer and agent                             │  │
│  │  • Preferences and profile data                                    │  │
│  │                                                                     │  │
│  │  Protection: Encryption at rest + in transit, access logging       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  RESTRICTED                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  • Passport numbers                                                │  │
│  │  • National ID numbers                                             │  │
│  │  • Payment card details (processed, not stored)                    │  │
│  │  • Full payment details                                            │  │
│  │  • Travel document images                                         │  │
│  │  • Special category data (health, religion)                        │  │
│  │                                                                     │  │
│  │  Protection: Strong encryption, strict access controls, audit trail │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Data Encryption

```typescript
// security/encryption.ts
import crypto from 'crypto';

// Encryption configuration
const ENCRYPTION_CONFIG = {
  algorithm: 'aes-256-gcm',
  keyLength: 32, // bytes
  ivLength: 16, // bytes
  saltLength: 32, // bytes
  tagLength: 16, // bytes
  authTagLength: 16, // bytes
};

export class DataEncryption {
  private masterKey: Buffer;

  constructor(masterKey: string) {
    // Master key should come from environment variable or KMS
    this.masterKey = Buffer.from(masterKey, 'hex');
  }

  // Encrypt sensitive data for storage
  encrypt(plaintext: string): { encrypted: string; iv: string; tag: string } {
    const iv = crypto.randomBytes(ENCRYPTION_CONFIG.ivLength);
    const salt = crypto.randomBytes(ENCRYPTION_CONFIG.saltLength);

    // Derive key using HKDF
    const key = crypto.deriveKey(
      'hkdf-sha256',
      this.masterKey,
      { salt, info: Buffer.from('customer-portal-encryption') },
      ENCRYPTION_CONFIG.keyLength,
      CryptoKeyHandle
    );

    // Encrypt
    const cipher = crypto.createCipheriv(
      ENCRYPTION_CONFIG.algorithm,
      key,
      iv
    );

    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return {
      encrypted,
      iv: iv.toString('hex'),
      tag: authTag.toString('hex'),
    };
  }

  // Decrypt data from storage
  decrypt(encrypted: string, iv: string, tag: string): string {
    const ivBuffer = Buffer.from(iv, 'hex');
    const tagBuffer = Buffer.from(tag, 'hex');

    // For simplicity, using same master key derivation
    // In production, use proper key management
    const key = this.masterKey; // Should be derived properly

    const decipher = crypto.createDecipheriv(
      ENCRYPTION_CONFIG.algorithm.replace('gm', 'gcm'),
      key,
      ivBuffer
    );

    decipher.setAuthTag(tagBuffer);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}

// Field-level encryption for database
export const encryptedFields = [
  'passportNumber',
  'nationalId',
  'dateOfBirth',
  'phoneNumber',
  'emailAddress',
  'emergencyContact',
];

// Encrypted column type for Prisma/SQL
export const encryptedColumnDefinition = `
  CREATE TABLE customers_encrypted (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    email_encrypted BYTEA,  -- Encrypted email
    email_iv BYTEA,         -- IV for email
    email_tag BYTEA,        -- Auth tag for email
    phone_encrypted BYTEA,
    phone_iv BYTEA,
    phone_tag BYTEA,
    passport_number_encrypted BYTEA,
    passport_number_iv BYTEA,
    passport_number_tag BYTEA,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
`;
```

### Data Minimization

```typescript
// privacy/data_minimization.ts
interface DataRetentionPolicy {
  dataType: string;
  retentionPeriod: string;
  deletionAction: 'hard_delete' | 'anonymize' | 'archive';
  rationale: string;
}

export const retentionPolicies: DataRetentionPolicy[] = [
  {
    dataType: 'authentication_logs',
    retentionPeriod: '90 days',
    deletionAction: 'hard_delete',
    rationale: 'Security audit requirements',
  },
  {
    dataType: 'access_logs',
    retentionPeriod: '1 year',
    deletionAction: 'anonymize',
    rationale: 'Usage analytics',
  },
  {
    dataType: 'messages',
    retentionPeriod: '7 years after trip completion',
    deletionAction: 'hard_delete',
    rationale: 'Legal/compliance requirements',
  },
  {
    dataType: 'payment_records',
    retentionPeriod: '7 years',
    deletionAction: 'anonymize',
    rationale: 'Tax compliance',
  },
  {
    dataType: 'trip_documents',
    retentionPeriod: '7 years after trip completion',
    deletionAction: 'archive',
    rationale: 'Customer access, legal requirements',
  },
  {
    dataType: 'inactive_customer_data',
    retentionPeriod: '3 years after last activity',
    deletionAction: 'anonymize',
    rationale: 'GDPI right to be forgotten (with retention for legal)',
  },
];

// Data anonymization
export class DataAnonymizer {
  anonymizeCustomer(customer: Customer): AnonymizedCustomer {
    return {
      originalId: this.hashId(customer.id),
      name: this.anonymizeName(customer.name),
      email: this.anonymizeEmail(customer.email),
      phone: this.anonymizePhone(customer.phone),
      createdAt: customer.createdAt,
      // Remove sensitive fields
      passportNumber: null,
      nationalId: null,
      dateOfBirth: null,
    };
  }

  private hashId(id: string): string {
    return crypto.createHash('sha256').update(id + process.env.ANONYMIZATION_SALT).digest('hex');
  }

  private anonymizeName(name: string): string {
    const parts = name.split(' ');
    return parts[0].charAt(0) + parts[0].slice(1).replace(/./g, '*') +
           (parts.length > 1 ? ' ' + parts[parts.length - 1].charAt(0) + '***' : '');
    // "John Doe" → "J*** D***"
  }

  private anonymizeEmail(email: string): string {
    const [local, domain] = email.split('@');
    const firstChar = local.charAt(0);
    const stars = '*'.repeat(Math.max(local.length - 1, 3));
    return `${firstChar}${stars}@${domain}`;
    // "john@example.com" → "j***@example.com"
  }

  private anonymizePhone(phone: string): string {
    // Keep country code and last 4 digits
    return phone.replace(/(\+\d{1,3})?\d*(\d{4})/, '$1***$2');
    // "+1234567890" → "+1***7890"
  }
}
```

---

## Consent Management

### Consent Framework

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          CONSENT FRAMEWORK                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  CONENT CATEGORIES:                                                        │
│                                                                            │
│  1. ESSENTIAL CONSENTS (Required for Service)                              │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Terms of Service acceptance                                     │  │
│     │ • Privacy Policy acknowledgment                                   │  │
│     │ • Authentication data processing                                  │  │
│     │ • Trip data processing for booking fulfillment                    │  │
│     │                                                                 │  │
│     │ Required: YES │ Can be withdrawn: PARTIAL                       │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  2. MARKETING CONSENTS (Optional)                                         │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Email marketing (newsletters, offers)                        │  │
│     │ • SMS notifications (trip updates, promotions)                   │  │
│     │ • Push notifications (app alerts)                                │  │
│     │ • WhatsApp messaging                                            │  │
│     │                                                                 │  │
│     │ Required: NO │ Can be withdrawn: YES, ANY TIME                  │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  3. ANALYTICS CONSENTS (Optional)                                        │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Usage analytics (product improvement)                         │  │
│     │ • Personalized recommendations                                  │  │
│     │ • Behavioral tracking                                           │  │
│     │                                                                 │  │
│     │ Required: NO │ Can be withdrawn: YES, ANY TIME                  │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  4. SHARING CONSENTS (Optional)                                          │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Share with trip partners (airlines, hotels)                   │  │
│     │ • Share with travel insurance provider                           │  │
│     │ • Share for loyalty programs                                     │  │
│     │                                                                 │  │
│     │ Required: NO │ Can be withdrawn: YES (may affect service)       │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Consent Management Implementation

```typescript
// consent/consent_manager.ts
export interface ConsentRecord {
  id: string;
  customerId: string;
  category: ConsentCategory;
  granted: boolean;
  grantedAt?: Date;
  withdrawnAt?: Date;
  ipAddress: string;
  userAgent: string;
  version: string; // To track which policy version
}

type ConsentCategory =
  | 'terms_of_service'
  | 'privacy_policy'
  | 'email_marketing'
  | 'sms_marketing'
  | 'push_notifications'
  | 'whatsapp_messaging'
  | 'analytics'
  | 'personalization'
  | 'share_partners'
  | 'share_insurance';

export class ConsentManager {
  async grantConsent(
    customerId: string,
    category: ConsentCategory,
    metadata: { ipAddress: string; userAgent: string }
  ): Promise<ConsentRecord> {
    // Check if consent already exists
    const existing = await this.getConsent(customerId, category);
    if (existing && existing.granted) {
      return existing;
    }

    // Create new consent record
    const record: ConsentRecord = {
      id: crypto.randomUUID(),
      customerId,
      category,
      granted: true,
      grantedAt: new Date(),
      ipAddress: metadata.ipAddress,
      userAgent: metadata.userAgent,
      version: await this.getCurrentPolicyVersion(category),
    };

    await this.db.query(`
      INSERT INTO consents (id, customer_id, category, granted, granted_at, ip_address, user_agent, version)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    `, [record.id, record.customerId, record.category, record.granted, record.grantedAt,
        record.ipAddress, record.userAgent, record.version]);

    // Log for audit
    await this.auditLog.log({
      action: 'consent_granted',
      customerId,
      category,
      timestamp: new Date(),
    });

    return record;
  }

  async withdrawConsent(
    customerId: string,
    category: ConsentCategory
  ): Promise<ConsentRecord> {
    const existing = await this.getConsent(customerId, category);
    if (!existing) {
      throw new Error('Consent not found');
    }

    // Check if essential consent
    if (this.isEssentialConsent(category)) {
      throw new Error('Cannot withdraw essential consent without closing account');
    }

    // Update record
    await this.db.query(`
      UPDATE consents
      SET granted = false, withdrawn_at = NOW()
      WHERE id = $1
    `, [existing.id]);

    // Execute withdrawal actions
    await this.executeWithdrawalActions(customerId, category);

    return { ...existing, granted: false, withdrawnAt: new Date() };
  }

  async getConsent(
    customerId: string,
    category: ConsentCategory
  ): Promise<ConsentRecord | null> {
    const result = await this.db.query(`
      SELECT * FROM consents
      WHERE customer_id = $1 AND category = $2
      ORDER BY granted_at DESC
      LIMIT 1
    `, [customerId, category]);

    return result[0] || null;
  }

  async hasConsent(
    customerId: string,
    category: ConsentCategory
  ): Promise<boolean> {
    const consent = await this.getConsent(customerId, category);
    return consent?.granted ?? false;
  }

  async getAllConsents(customerId: string): Promise<Record<ConsentCategory, boolean>> {
    const results = await this.db.query(`
      SELECT DISTINCT ON (category) category, granted
      FROM consents
      WHERE customer_id = $1
      ORDER BY category, granted_at DESC
    `, [customerId]);

    const categories: ConsentCategory[] = [
      'terms_of_service', 'privacy_policy', 'email_marketing', 'sms_marketing',
      'push_notifications', 'whatsapp_messaging', 'analytics', 'personalization',
      'share_partners', 'share_insurance',
    ];

    return categories.reduce((acc, cat) => {
      const record = results.find(r => r.category === cat);
      acc[cat] = record?.granted ?? false;
      return acc;
    }, {} as Record<ConsentCategory, boolean>);
  }

  private isEssentialConsent(category: ConsentCategory): boolean {
    return ['terms_of_service', 'privacy_policy'].includes(category);
  }

  private async executeWithdrawalActions(
    customerId: string,
    category: ConsentCategory
  ): Promise<void> {
    switch (category) {
      case 'email_marketing':
        await this.unsubscribeFromMarketingEmails(customerId);
        break;
      case 'sms_marketing':
        await this.unsubscribeFromMarketingSMS(customerId);
        break;
      case 'push_notifications':
        await this.disablePushNotifications(customerId);
        break;
      case 'analytics':
        await this.anonymizeHistoricalData(customerId);
        break;
      case 'share_partners':
        await this.notifyPartnersOfWithdrawal(customerId);
        break;
    }
  }

  private async getCurrentPolicyVersion(category: ConsentCategory): Promise<string> {
    // In production, this would come from a policy version table
    return '1.0';
  }
}

// Consent UI component
export function ConsentBanner({ required, onAccept, onReject }: {
  required: boolean;
  onAccept: () => void;
  onReject: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`
      fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg p-4 z-50
      ${required ? 'border-red-500' : ''}
    `}>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            {required ? (
              <AlertCircleIcon className="w-6 h-6 text-red-500" />
            ) : (
              <InfoIcon className="w-6 h-6 text-blue-500" />
            )}
          </div>

          <div className="flex-1">
            <h3 className="font-semibold">
              {required ? 'Action Required' : 'We use cookies'}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {required
                ? 'Please accept our Terms of Service and Privacy Policy to continue.'
                : 'We use cookies and similar technologies to improve your experience.'}
            </p>

            {expanded && (
              <div className="mt-4 space-y-2 text-sm">
                <ConsentCheckbox
                  category="essential"
                  label="Essential (required)"
                  checked={true}
                  disabled={true}
                  description="Required for the portal to function"
                />
                <ConsentCheckbox
                  category="analytics"
                  label="Analytics"
                  checked={false}
                  description="Help us improve the portal"
                />
                <ConsentCheckbox
                  category="marketing"
                  label="Marketing"
                  checked={false}
                  description="Receive special offers and travel tips"
                />
              </div>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <Button onClick={onAccept} size="sm">
              {required ? 'Accept' : 'Accept Selected'}
            </Button>
            {!required && (
              <Button onClick={onReject} variant="ghost" size="sm">
                Reject
              </Button>
            )}
            <Button
              onClick={() => setExpanded(!expanded)}
              variant="ghost"
              size="sm"
              className="text-xs"
            >
              {expanded ? 'Less' : 'More'} info
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Compliance

### GDPR Compliance

```typescript
// compliance/gdpr.ts
export class GDPRCompliance {
  // Right to Access (Article 15)
  async provideDataAccessReport(customerId: string): Promise<CustomerDataReport> {
    const [customer, trips, documents, messages, payments, consents] = await Promise.all([
      this.getCustomerData(customerId),
      this.getTripsData(customerId),
      this.getDocumentsData(customerId),
      this.getMessagesData(customerId),
      this.getPaymentsData(customerId),
      this.getConsentsData(customerId),
    ]);

    return {
      personalData: customer,
      tripData: trips,
      documentData: documents,
      messageData: messages,
      paymentData: payments,
      consentData: consents,
      generatedAt: new Date(),
      format: 'JSON',
    };
  }

  // Right to Rectification (Article 16)
  async rectifyData(
    customerId: string,
    corrections: Partial<Customer>
  ): Promise<void> {
    await this.db.query(`
      UPDATE customers
      SET
        name = COALESCE($2, name),
        email = COALESCE($3, email),
        phone = COALESCE($4, phone),
        updated_at = NOW()
      WHERE id = $1
    `, [customerId, corrections.name, corrections.email, corrections.phone]);

    await this.auditLog.log({
      action: 'data_rectified',
      customerId,
      corrections,
      timestamp: new Date(),
    });
  }

  // Right to Erasure (Article 17)
  async requestErasure(customerId: string): Promise<{ canDelete: boolean; reason?: string }> {
    // Check if deletion is allowed
    const activeTrips = await this.db.query(`
      SELECT COUNT(*) as count
      FROM trip_customers tc
      JOIN trips t ON t.id = tc.trip_id
      WHERE tc.customer_id = $1
        AND t.status NOT IN ('completed', 'cancelled')
    `, [customerId]);

    if (activeTrips[0].count > 0) {
      return {
        canDelete: false,
        reason: 'Cannot delete account while trips are active',
      };
    }

    // Check for legal hold requirements
    const legalHold = await this.hasLegalHold(customerId);
    if (legalHold) {
      return {
        canDelete: false,
        reason: 'Account is under legal hold',
      };
    }

    // Proceed with deletion
    await this.executeErasure(customerId);
    return { canDelete: true };
  }

  private async executeErasure(customerId: string): Promise<void> {
    await this.db.transaction(async (trx) => {
      // Anonymize instead of hard delete for legal reasons
      await this.anonymizer.anonymizeCustomer(customerId);

      // Delete authentication data
      await trx.query('DELETE FROM customer_sessions WHERE customer_id = $1', [customerId]);
      await trx.query('DELETE FROM customer_auth WHERE customer_id = $1', [customerId]);

      // Delete consents
      await trx.query('DELETE FROM consents WHERE customer_id = $1', [customerId]);

      // Mark customer as deleted
      await trx.query(`
        UPDATE customers
        SET status = 'deleted', deleted_at = NOW()
        WHERE id = $1
      `, [customerId]);
    });
  }

  // Right to Portability (Article 20)
  async exportData(customerId: string): Promise<Buffer> {
    const report = await this.provideDataAccessReport(customerId);

    // Create machine-readable format (JSON)
    return Buffer.from(JSON.stringify(report, null, 2));
  }

  // Right to Object (Article 21)
  async objectToProcessing(
    customerId: string,
    grounds: 'marketing' | 'analytics' | 'sharing'
  ): Promise<void> {
    switch (grounds) {
      case 'marketing':
        await this.consentManager.withdrawConsent(customerId, 'email_marketing');
        await this.consentManager.withdrawConsent(customerId, 'sms_marketing');
        break;
      case 'analytics':
        await this.consentManager.withdrawConsent(customerId, 'analytics');
        break;
      case 'sharing':
        await this.consentManager.withdrawConsent(customerId, 'share_partners');
        break;
    }
  }
}
```

### PCI DSS Compliance for Payments

```typescript
// compliance/pci_dss.ts
/**
 * IMPORTANT: We do NOT store, process, or transmit cardholder data.
 * All payment processing is handled by PCI-certified processors (Stripe).
 * This document outlines how we maintain PCI compliance while using third-party processors.
 */

export class PCIComplianceHandler {
  /**
   * Payment flow that maintains PCI compliance:
   * 1. Customer enters card details on Stripe-hosted page
   * 2. Stripe tokenizes the card details
   * 3. Stripe returns a token to our server
   * 4. We use the token to process the payment
   * 5. We store ONLY the last 4 digits and token identifier
   */

  async initiatePayment(
    customerId: string,
    tripId: string,
    amount: number,
    currency: string
  ): Promise<PaymentIntent> {
    // Create payment intent with Stripe
    // Customer card details never touch our servers
    const intent = await this.stripe.paymentIntents.create({
      amount: amount * 100, // cents
      currency,
      metadata: {
        customerId,
        tripId,
      },
      // Return URL for 3D Secure
      return_url: `${process.env.APP_URL}/payments/confirm`,
    });

    return {
      intentId: intent.id,
      clientSecret: intent.client_secret,
      amount: intent.amount / 100,
      currency: intent.currency,
      status: intent.status,
    };
  }

  async confirmPayment(intentId: string): Promise<PaymentResult> {
    const intent = await this.stripe.paymentIntents.retrieve(intentId);

    if (intent.status === 'succeeded') {
      // Store ONLY non-sensitive payment info
      await this.db.query(`
        INSERT INTO payments (
          id,
          trip_id,
          customer_id,
          amount,
          currency,
          status,
          payment_method_id,
          card_last4,
          card_brand,
          created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
      `, [
        crypto.randomUUID(),
        intent.metadata.tripId,
        intent.metadata.customerId,
        intent.amount / 100,
        intent.currency,
        'completed',
        intent.payment_method,
        intent.charges.data[0].payment_method_details.card.last4,
        intent.charges.data[0].payment_method_details.card.brand,
      ]);

      return {
        success: true,
        paymentId: intent.id,
        amount: intent.amount / 100,
      };
    }

    return {
      success: false,
      error: intent.last_payment_error?.message || 'Payment failed',
    };
  }

  /**
   * PCI DSS Requirements we maintain:
   *
   * ✅ Install and maintain a firewall configuration
   * ✅ Do not use vendor-supplied defaults for system passwords
   * ✅ Protect stored cardholder data (we don't store any)
   * ✅ Encrypt transmission of cardholder data (TLS 1.3)
   * ✅ Use and regularly update anti-virus software
   * ✅ Develop and maintain secure systems and applications
   * ✅ Restrict access to cardholder data by business need-to-know
   * ✅ Assign a unique ID to each person with computer access
   * ✅ Restrict physical access to cardholder data
   * ✅ Track and monitor all access to network resources and cardholder data
   * ✅ Regularly test security systems and processes
   * ✅ Maintain an Information Security Policy
   *
   * Since we use Stripe for payment processing, our SAQ A-EP scope is significantly reduced.
   */
}
```

---

## Threat Model

### Threat Analysis

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         THREAT ANALYSIS                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  THREAT: Account Takeover (ATO)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Likelihood: MEDIUM                                                    │  │
│  │ Impact: HIGH                                                         │  │
│  │                                                                     │  │
│  │ Attack Vector:                                                      │  │
│  │ • Credential stuffing (reusing breached passwords)                  │  │
│  │ • Phishing attacks targeting customers                                │  │
│  │ • Session hijacking via stolen tokens                               │  │
│  │                                                                     │  │
│  │ Mitigations:                                                        │  │
│  │ • OTP-based authentication (no passwords)                          │  │
│  │ • Short-lived tokens (15 min access, 30 day refresh)                │  │
│  │ • Device fingerprinting for anomaly detection                        │  │
│  │ • IP-based rate limiting                                             │  │
│  │ • Session invalidation on password reset                           │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  THREAT: Data Breach (Customer Data)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Likelihood: LOW                                                     │  │
│  │ Impact: CRITICAL                                                    │  │
│  │                                                                     │  │
│  │ Attack Vector:                                                      │  │
│  │ • SQL injection                                                    │  │
│  │ • API exploitation                                                  │  │
│  │ • Database access via compromised credentials                        │  │
│  │                                                                     │  │
│  │ Mitigations:                                                        │  │
│  │ • Parameterized queries (no SQL injection)                          │  │
│  │ • Row-level security (customers see only their data)                │  │
│  │ • Encryption at rest for PII                                        │  │
│  │ • Regular security audits and penetration testing                   │  │
│  │ • Principle of least privilege for database access                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  THREAT: Session Hijacking                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Likelihood: LOW                                                     │  │
│  │ Impact: HIGH                                                         │  │
│  │                                                                     │  │
│  │ Attack Vector:                                                      │  │
│  │ • XSS stealing cookies/tokens                                      │  │
│  │ • Network interception (MITM)                                       │  │
│  │ • CSRF forcing actions                                              │  │
│  │                                                                     │  │
│  │ Mitigations:                                                        │  │
│  │ • HttpOnly cookies (no JS access to session tokens)                 │  │
│  │ • SameSite cookies (CSRF protection)                               │  │
│  │ • CSRF tokens for state-changing operations                         │  │
│  │ • Content Security Policy (no inline scripts)                       │  │
│  │ • Token binding to IP/User-Agent                                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  THREAT: Document Exposure (Unauthorized Access)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Likelihood: MEDIUM                                                    │  │
│  │ Impact: HIGH                                                         │  │
│  │                                                                     │  │
│  │ Attack Vector:                                                      │  │
│  │ • Predictable download URLs                                         │  │
│  │ • Shared links forwarded to unauthorized users                       │  │
│  │ • Direct object enumeration                                         │  │
│  │                                                                     │  │
│  │ Mitigations:                                                        │  │
│  │ • Signed expiring URLs (HMAC with timestamp)                       │  │
│  │ • Per-customer access validation                                    │  │
│  │ • Access logging for all document downloads                         │  │
│  │ • Rate limiting on document downloads                              │  │
│  │ • Watermarking of sensitive documents                              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  THREAT: Denial of Service (DoS)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Likelihood: HIGH                                                     │  │
│  │ Impact: MEDIUM                                                       │  │
│  │                                                                     │  │
│  │ Attack Vector:                                                      │  │
│  │ • Volumetric request flood                                          │  │
│  │ • Resource exhaustion attacks                                       │  │
│  │ • Distributed bot attacks                                           │  │
│  │                                                                     │  │
│  │ Mitigations:                                                        │  │
│  │ • CDN/Cloudflare for DDoS protection                               │  │
│  │ • Rate limiting per IP and per user                                  │  │
│  │ • Request throttling and queuing                                   │  │
│  │ • Auto-scaling infrastructure                                      │  │
│  │ • Request validation before expensive operations                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Security Testing

```typescript
// security/testing.ts
export const securityTests = {
  // SQL Injection test
  async testSQLInjection(): Promise<boolean> {
    const payloads = [
      "'; DROP TABLE customers; --",
      "' OR '1'='1",
      "1' UNION SELECT * FROM customers--",
    ];

    for (const payload of payloads) {
      const response = await fetch('/api/v1/customer/trips', {
        method: 'POST',
        body: JSON.stringify({ query: payload }),
      });

      if (response.status === 500) {
        return false; // Vulnerable
      }
    }

    return true; // Passed
  },

  // XSS test
  async testXSS(): Promise<boolean> {
    const payloads = [
      '<script>alert("XSS")</script>',
      '<img src=x onerror="alert(\'XSS\')">',
      '"><script>alert(String.fromCharCode(88,83,83))</script>',
    ];

    for (const payload of payloads) {
      const response = await fetch('/api/v1/customer/profile', {
        method: 'POST',
        body: JSON.stringify({ name: payload }),
      });

      const data = await response.json();
      if (data.name && data.name.includes('script')) {
        return false; // Vulnerable
      }
    }

    return true; // Passed
  },

  // Authentication bypass test
  async testAuthBypass(): Promise<boolean> {
    const tests = [
      // Try accessing without token
      fetch('/api/v1/customer/trips'),
      // Try with invalid token
      fetch('/api/v1/customer/trips', {
        headers: { Authorization: 'Bearer invalid' },
      }),
      // Try with expired token
      fetch('/api/v1/customer/trips', {
        headers: { Authorization: 'Bearer expired.jwt.token' },
      }),
    ];

    const results = await Promise.all(tests);

    // All should return 401 or 403
    return results.every(r => [401, 403].includes(r.status));
  },

  // Rate limiting test
  async testRateLimiting(): Promise<boolean> {
    const requests = Array(100).fill(null).map(() =>
      fetch('/api/v1/customer/auth/initiate', {
        method: 'POST',
        body: JSON.stringify({ identifier: 'test@example.com', channel: 'email' }),
      })
    );

    const results = await Promise.all(requests);
    const blockedCount = results.filter(r => r.status === 429).length;

    return blockedCount > 0; // Should be rate limited
  },
};
```

---

## Security Best Practices

### Development Practices

```typescript
// security/best_practices.ts

/**
 * 1. NEVER log sensitive data
 */
export const logger = {
  info(message: string, meta?: Record<string, unknown>) {
    // Sanitize meta object before logging
    const sanitized = this.sanitize(meta);
    console.info(JSON.stringify({ message, ...sanitized }));
  },

  sanitize(obj: Record<string, unknown> = {}): Record<string, unknown> {
    const sensitiveKeys = ['password', 'token', 'ssn', 'passport', 'creditCard', 'cvv'];
    const sanitized = { ...obj };

    for (const key in sanitized) {
      if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
        sanitized[key] = '[REDACTED]';
      }
    }

    return sanitized;
  },
};

/**
 * 2. Use prepared statements
 */
export async function getCustomerTrips(customerId: string): Promise<Trip[]> {
  // ✅ GOOD - Parameterized query
  return db.query(
    'SELECT * FROM trips WHERE customer_id = $1',
    [customerId]
  );

  // ❌ BAD - SQL injection vulnerability
  // return db.query(`SELECT * FROM trips WHERE customer_id = '${customerId}'`);
}

/**
 * 3. Validate and sanitize all inputs
 */
export function validateTripId(tripId: unknown): string {
  const schema = z.string().uuid();
  return schema.parse(tripId);
}

/**
 * 4. Use constant-time comparison for sensitive data
 */
import crypto from 'crypto';

export function constantTimeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }

  return crypto.timingSafeEqual(
    Buffer.from(a),
    Buffer.from(b)
  );
}

/**
 * 5. Never expose internal errors to clients
 */
export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction) {
  // Log full error internally
  logger.error('Internal error', {
    error: err.message,
    stack: err.stack,
    requestId: req.id,
  });

  // Return generic error to client
  res.status(500).json({
    error: 'Internal Server Error',
    message: 'An error occurred while processing your request',
    requestId: req.id,
  });
}

/**
 * 6. Implement proper session management
 */
export class SessionManager {
  private readonly SESSION_DURATION = 15 * 60 * 1000; // 15 minutes

  createSession(customerId: string): SessionToken {
    const payload = {
      sub: customerId,
      iat: Date.now(),
      exp: Date.now() + this.SESSION_DURATION,
      // Add binding to prevent token theft
      jti: crypto.randomUUID(),
    };

    return {
      accessToken: this.signToken(payload),
      expiresIn: this.SESSION_DURATION,
    };
  }

  validateSession(token: string): Customer | null {
    try {
      const decoded = this.verifyToken(token);

      // Check expiry
      if (decoded.exp < Date.now()) {
        return null;
      }

      // Check if session was revoked
      return this.db.query(
        'SELECT * FROM customer_sessions WHERE access_token_jti = $1 AND revoked = false',
        [decoded.jti]
      );
    } catch {
      return null;
    }
  }

  revokeSession(token: string): void {
    const decoded = this.verifyToken(token);
    this.db.query(
      'UPDATE customer_sessions SET revoked = true WHERE access_token_jti = $1',
      [decoded.jti]
    );
  }
}
```

### Secure Configuration

```typescript
// config/security.ts
export const securityConfig = {
  // JWT configuration
  jwt: {
    accessTokenExpiry: 15 * 60, // 15 minutes
    refreshTokenExpiry: 30 * 24 * 60 * 60, // 30 days
    issuer: 'customer-portal',
    audience: 'customer-portal-api',
    algorithm: 'HS256',
  },

  // Password/OTP configuration
  otp: {
    length: 6,
    expiry: 5 * 60, // 5 minutes
    maxAttempts: 3,
    lockoutDuration: 15 * 60, // 15 minutes
    alphabet: '0123456789',
  },

  // Rate limiting
  rateLimits: {
    // Per IP
    ip: {
      windowMs: 15 * 60 * 1000, // 15 minutes
      maxRequests: 100,
    },
    // Per user
    user: {
      windowMs: 15 * 60 * 1000,
      maxRequests: 200,
    },
    // Authentication endpoints
    auth: {
      windowMs: 15 * 60 * 1000,
      maxRequests: 10,
    },
    // Sensitive operations
    sensitive: {
      windowMs: 60 * 60 * 1000, // 1 hour
      maxRequests: 5,
    },
  },

  // Document access
  documents: {
    downloadLinkExpiry: 5 * 60, // 5 minutes
    maxDownloadsPerLink: 1,
    watermark: true,
  },

  // Session management
  sessions: {
    maxConcurrentSessions: 3,
    absoluteExpiry: 24 * 60 * 60, // 24 hours
    idleExpiry: 30 * 60, // 30 minutes
  },

  // Data retention
  retention: {
    logs: 90 * 24 * 60 * 60 * 1000, // 90 days
    auditLogs: 365 * 24 * 60 * 60 * 1000, // 1 year
    inactiveData: 3 * 365 * 24 * 60 * 60 * 1000, // 3 years
  },
};
```

---

## Incident Response

### Security Incident Procedures

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    INCIDENT RESPONSE PROCEDURES                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  PHASE 1: DETECTION (0-24 hours)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ • Automated alert from monitoring system                             │  │
│  │ • Initial triage: Is this a real incident?                          │  │
│  │ • Determine severity level (P1/P2/P3/P4)                            │  │
│  │ • Activate incident response team if P1/P2                            │  │
│  │ • Begin incident log                                                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  PHASE 2: CONTAINMENT (0-48 hours)                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ • Identify affected systems                                          │  │
│  │ • Isolate compromised systems                                        │  │
│  │ • Revoke all active sessions                                        │  │
│  │ • Force password reset for affected users                           │  │
│  │ • Preserve evidence (logs, memory dumps)                            │  │
│  │ • Block malicious IPs/accounts                                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  PHASE 3: ERADICATION (1-7 days)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ • Identify root cause                                                │  │
│  │ • Remove malicious code/accounts                                    │  │
│  │ • Patch vulnerabilities                                              │  │
│  │ • Verify no backdoors remain                                        │  │
│  │ • Restore from clean backups                                        │  │
│  │ • Scan for persistence mechanisms                                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  PHASE 4: RECOVERY (7-30 days)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ • Restore services                                                  │  │
│  │ • Monitor for suspicious activity                                   │  │
│  │ • Communicate with affected customers                                │  │
│  │ • Provide credit monitoring if PII exposed                           │  │
│  │ • Implement additional monitoring                                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  PHASE 5: POST-INCIDENT (30+ days)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ • Conduct post-mortem                                                │  │
│  │ • Update security policies                                           │  │
│  │ • Implement lessons learned                                         │  │
│  │ • Update incident response plan                                     │  │
│  │ • Security awareness training                                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Incident Communication Templates

```typescript
// security/incident_communications.ts
export const incidentTemplates = {
  // Data breach notification
  dataBreach: {
    subject: 'Important: Security Notice Regarding Your Account',
    body: `
      Dear {{customer_name}},

      We are writing to inform you of a security incident that may have involved your personal information.

      What happened:
      {{incident_description}}

      What information was affected:
      {{affected_data}}

      What we are doing:
      {{response_actions}}

      What you should do:
      {{customer_actions}}

      We sincerely apologize for any inconvenience or concern this may cause. We take the security of your information very seriously.

      If you have questions, please contact us at {{security_contact}}.

      Sincerely,
      {{agency_name}} Security Team
    `,
  },

  // Service disruption
  serviceDisruption: {
    subject: 'Portal Maintenance Notice',
    body: `
      Dear {{customer_name}},

      We will be performing scheduled maintenance on the customer portal:

      Date: {{maintenance_date}}
      Duration: {{duration}}
      Impact: {{impact_description}}

      During this time, you will not be able to access your trip information or documents. We apologize for any inconvenience.

      If you need urgent assistance during this time, please contact us at {{support_phone}}.

      Thank you for your patience.
    `,
  },

  // Password reset (security event)
  passwordReset: {
    subject: 'Security Action Required: Password Reset',
    body: `
      We noticed suspicious activity on your account. As a security measure, we have reset your password.

      To regain access, please visit:
      {{reset_link}}

      If you did not initiate this action, please contact us immediately at {{security_contact}}.

      For your security, please:
      • Choose a strong, unique password
      • Enable two-factor authentication if available
      • Review your account activity for any unauthorized access
    `,
  },
};
```

---

**This completes the Customer Portal deep dive series.**

**Series Summary:**
- CUSTOMER_PORTAL_01: Technical Architecture, Authentication, Data Access Control
- CUSTOMER_PORTAL_02: UX/UI Design, Mobile Experience, Accessibility
- CUSTOMER_PORTAL_03: Business Value, ROI Analysis, Competitive Advantage
- CUSTOMER_PORTAL_04: Customer Engagement, Feature Adoption, Gamification
- CUSTOMER_PORTAL_05: Security, Privacy, Compliance, Incident Response

**Total Documentation:** 5 documents covering all aspects of the Customer Portal
