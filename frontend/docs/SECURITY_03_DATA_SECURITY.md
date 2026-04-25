# SECURITY_03: Data Security

> Encryption at rest, encryption in transit, PII handling, and key management

---

## Document Overview

**Series:** Security Hardening
**Document:** 3 of 4
**Focus:** Data Security
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Introduction](#introduction)
2. [Encryption at Rest](#encryption-at-rest)
3. [Encryption in Transit](#encryption-in-transit)
4. [PII Detection & Classification](#pii-detection--classification)
5. [Data Masking & Redaction](#data-masking--redaction)
6. [Key Management](#key-management)
7. [Database Security](#database-security)
8. [Backup Security](#backup-security)
9. [Data Retention & Disposal](#data-retention--disposal)
10. [Compliance](#compliance)

---

## 1. Introduction

### Data Security Principles

Data security protects sensitive information throughout its lifecycle:

| Phase | Threats | Protections |
|-------|---------|-------------|
| **At Rest** | Unauthorized access, theft | Encryption, access controls |
| **In Transit** | Eavesdropping, MITM | TLS, certificate pinning |
| **In Use** | Memory dumps, screenshots | Secure memory, screen protection |
| **Disposal** | Data recovery | Secure deletion, cryptographic erasure |

### Data Classification

```typescript
// security/data-classification.ts

export enum DataClassification {
  PUBLIC = 'public',           // Can be freely shared
  INTERNAL = 'internal',       // Company internal only
  CONFIDENTIAL = 'confidential', // Sensitive business data
  RESTRICTED = 'restricted',    // PII, financial data
  CRITICAL = 'critical'        // Encryption keys, secrets
}

/**
 * Data classification service
 */
export class DataClassificationService {
  /**
   * Classify data based on content
   */
  classify(data: any): DataClassification {
    if (this.isPII(data)) {
      return DataClassification.RESTRICTED;
    }

    if (this.isFinancial(data)) {
      return DataClassification.RESTRICTED;
    }

    if (this.isBusinessSensitive(data)) {
      return DataClassification.CONFIDENTIAL;
    }

    if (this.isInternal(data)) {
      return DataClassification.INTERNAL;
    }

    return DataClassification.PUBLIC;
  }

  /**
   * Detect PII in data
   */
  private isPII(data: any): boolean {
    const piiPatterns = {
      email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/,
      phone: /\+?[\d\s\-\(\)]{10,}/,
      ssn: /\d{3}-\d{2}-\d{4}|\d{9}/,
      creditCard: /\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}/,
      passport: /[A-Z]{2}\d{6,}/,
      ipAddress: /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/
    };

    const dataStr = JSON.stringify(data);

    for (const pattern of Object.values(piiPatterns)) {
      if (pattern.test(dataStr)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Get security requirements for data class
   */
  getSecurityRequirements(classification: DataClassification): {
    encryptionRequired: boolean;
    accessLogging: boolean;
    retentionLimit?: number;
    consentRequired: boolean;
  } {
    const requirements = {
      [DataClassification.PUBLIC]: {
        encryptionRequired: false,
        accessLogging: false,
        consentRequired: false
      },
      [DataClassification.INTERNAL]: {
        encryptionRequired: false,
        accessLogging: true,
        consentRequired: false
      },
      [DataClassification.CONFIDENTIAL]: {
        encryptionRequired: true,
        accessLogging: true,
        consentRequired: false
      },
      [DataClassification.RESTRICTED]: {
        encryptionRequired: true,
        accessLogging: true,
        retentionLimit: 7 * 365,  // 7 years
        consentRequired: true
      },
      [DataClassification.CRITICAL]: {
        encryptionRequired: true,
        accessLogging: true,
        consentRequired: true
      }
    };

    return requirements[classification];
  }
}
```

---

## 2. Encryption at Rest

### Field-Level Encryption

```typescript
// security/encryption.ts

import crypto from 'crypto';

/**
 * Field-level encryption for sensitive data
 */
export class FieldEncryption {
  private keyManager: KeyManagementService;

  /**
   * Encrypt sensitive field
   */
  async encryptField(value: string, context: {
    fieldType: string;
    recordId: string;
    userId?: string;
  }): Promise<EncryptedField> {
    // Get data encryption key
    const dek = await this.keyManager.getDataKey(context);

    // Generate IV
    const iv = crypto.randomBytes(16);

    // Encrypt
    const cipher = crypto.createCipheriv('aes-256-gcm', dek.key, iv);
    let encrypted = cipher.update(value, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    // Get auth tag
    const authTag = cipher.getAuthTag();

    return {
      encryptedData: encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex'),
      keyId: dek.id,
      algorithm: 'aes-256-gcm'
    };
  }

  /**
   * Decrypt sensitive field
   */
  async decryptField(encrypted: EncryptedField, context: {
    fieldType: string;
    recordId: string;
    userId?: string;
  }): Promise<string> {
    // Get data encryption key
    const dek = await this.keyManager.getKey(encrypted.keyId, context);

    // Decrypt
    const decipher = crypto.createDecipheriv(
      'aes-256-gcm',
      dek.key,
      Buffer.from(encrypted.iv, 'hex')
    );

    decipher.setAuthTag(Buffer.from(encrypted.authTag, 'hex'));

    let decrypted = decipher.update(encrypted.encryptedData, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }

  /**
   * Encrypt multiple fields in a record
   */
  async encryptRecord<T extends Record<string, any>>(
    record: T,
    encryptedFields: (keyof T)[],
    context: {
      recordType: string;
      recordId: string;
      userId?: string;
    }
  ): Promise<T> {
    const encrypted = { ...record };

    for (const field of encryptedFields) {
      const value = record[field];

      if (typeof value === 'string') {
        const encryptedValue = await this.encryptField(value, {
          fieldType: String(field),
          recordId: context.recordId,
          userId: context.userId
        });

        (encrypted as any)[`${String(field)}_encrypted`] = encryptedValue;
        delete encrypted[field];
      }
    }

    return encrypted;
  }

  /**
   * Batch encrypt for performance
   */
  async encryptBatch(values: string[], context: {
    fieldType: string;
    userId?: string;
  }): Promise<EncryptedField[]> {
    // Use same key for batch
    const dek = await this.keyManager.getDataKey(context);

    return Promise.all(
      values.map(value => this.encryptWithKey(value, dek))
    );
  }

  private async encryptWithKey(
    value: string,
    dek: DataEncryptionKey
  ): Promise<EncryptedField> {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', dek.key, iv);

    let encrypted = cipher.update(value, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return {
      encryptedData: encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex'),
      keyId: dek.id,
      algorithm: 'aes-256-gcm'
    };
  }
}

interface EncryptedField {
  encryptedData: string;
  iv: string;
  authTag: string;
  keyId: string;
  algorithm: string;
}

interface DataEncryptionKey {
  id: string;
  key: Buffer;
  createdAt: Date;
  expiresAt?: Date;
}
```

### Database Encryption

```typescript
// security/database-encryption.ts

/**
 * Database encryption utilities
 */
export class DatabaseEncryption {
  /**
   * Transparent encryption for PostgreSQL
   */
  static getPgsqlEncryption(column: string, alias: string): string {
    return `
      CASE
        WHEN ${column} IS NULL THEN NULL
        ELSE pgp_sym_decrypt(
          ${column}::bytea,
          (SELECT current_setting('app.encryption_key'))
        )
      END AS ${alias}
    `;
  }

  /**
   * Encrypt value for PostgreSQL storage
   */
  static encryptForPgsql(value: string): string {
    const key = process.env.DB_ENCRYPTION_KEY;
    const iv = crypto.randomBytes(16);

    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    let encrypted = cipher.update(value, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return `\\x${encrypted}${authTag.toString('hex')}${iv.toString('hex')}`;
  }

  /**
   * Sequelize model mixin for encrypted fields
   */
  static encryptedFieldsMixin(sequelize: Sequelize, encryptedFields: string[]) {
    return {
      async beforeSave(record: any) {
        for (const field of encryptedFields) {
          if (record.changed(field)) {
            const value = record.get(field);
            if (value) {
              record.setData(`${field}_encrypted`, this.encryptForPgsql(value));
              record.setData(field, null);
            }
          }
        }
      },

      async afterFind(results: any) {
        const isArray = Array.isArray(results);
        const records = isArray ? results : [results];

        for (const record of records) {
          if (record) {
            for (const field of encryptedFields) {
              const encrypted = record.get(`${field}_encrypted`);
              if (encrypted) {
                record.set(field, this.decryptFromPgsql(encrypted));
                record.set(`${field}_encrypted`, undefined);
              }
            }
          }
        }
      }
    };
  }

  /**
   * Decrypt from PostgreSQL
   */
  static decryptFromPgsql(encrypted: string): string {
    const key = process.env.DB_ENCRYPTION_KEY;
    const data = Buffer.from(encrypted.slice(1), 'hex');

    const authTag = data.slice(-16);
    const iv = data.slice(-32, -16);
    const ciphertext = data.slice(0, -32);

    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(ciphertext, undefined, 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}
```

---

## 3. Encryption in Transit

### TLS Configuration

```typescript
// security/tls.ts

import https from 'https';
import tls from 'tls';

/**
 * TLS configuration for servers
 */
export class TLSConfig {
  /**
   * Get HTTPS server options
   */
  static getServerOptions(): https.ServerOptions {
    return {
      key: fs.readFileSync(process.env.TLS_KEY_PATH),
      cert: fs.readFileSync(process.env.TLS_CERT_PATH),
      ca: this.getCaCertificates(),

      // TLS 1.2 and 1.3 only
      minVersion: 'TLSv1.2',
      maxVersion: 'TLSv1.3',

      // Secure cipher suites
      ciphers: tls.getCiphers().join(':'),

      // Security options
      honorCipherOrder: true,
      secureOptions: crypto.constants.SSL_OP_NO_SSLV3 |
                      crypto.constants.SSL_OP_NO_TLSv1 |
                      crypto.constants.SSL_OP_NO_TLSv1_1 |
                      crypto.constants.SSL_OP_NO_COMPRESSION |
                      crypto.constants.SSL_OP_NO_RENEGOTIATION |
                      crypto.constants.SSL_OP_NO_TICKET,

      // OCSP stapling
      certReq: crypto.constants.SSL_CERT_REQUIRED,

      // Session tickets
      ticketKeys: crypto.randomBytes(48),

      // Client auth (for mTLS)
      requestCert: process.env.MTLS_ENABLED === 'true',
      rejectUnauthorized: process.env.MTLS_STRICT === 'true',
      ca: process.env.MTLS_ENABLED ? fs.readFileSync(process.env.CA_CERT_PATH) : undefined
    };
  }

  /**
   * Get TLS options for outbound connections
   */
  static getClientOptions(): tls.SecureContextOptions {
    return {
      minVersion: 'TLSv1.2',
      maxVersion: 'TLSv1.3',
      ciphers: tls.getCiphers().join(':'),
      secureOptions: crypto.constants.SSL_OP_NO_SSLV3 |
                      crypto.constants.SSL_OP_NO_TLSv1 |
                      crypto.constants.SSL_OP_NO_TLSv1_1 |
                      crypto.constants.SSL_OP_NO_COMPRESSION,
      rejectUnauthorized: true,
      ca: this.getCaCertificates()
    };
  }

  /**
   * Get CA certificates
   */
  private static getCaCertificates(): Buffer | Buffer[] {
    if (process.env.CA_CERT_PATH) {
      return fs.readFileSync(process.env.CA_CERT_PATH);
    }

    // Use system CA store
    return tls.rootCertificates as Buffer[];
  }

  /**
   * Certificate pinning for external APIs
   */
  static getPinnedCerts(hostname: string): string[] {
    const pinnedCerts: Record<string, string[]> = {
      'api.payment-provider.com': [
        'sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',
        'sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB='
      ],
      'api.supplier.com': [
        'sha256/CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC='
      ]
    };

    return pinnedCerts[hostname] || [];
  }
}

/**
 * HTTPS agent with certificate pinning
 */
export class PinnedHTTPSAgent extends https.Agent {
  private pinnedCerts: string[];

  constructor(options: https.AgentOptions & { pinnedCerts: string[] }) {
    super(options);
    this.pinnedCerts = options.pinnedCerts;
  }

  createConnection(options: any, callback: any) {
    const socket = super.createConnection(options, (socket: any) => {
      const cert = socket.getPeerCertificate();

      if (cert) {
        const certFingerprint = crypto
          .createHash('sha256')
          .update(cert.raw)
          .digest('base64');

        if (!this.pinnedCerts.includes(`sha256/${certFingerprint}`)) {
          socket.destroy(new Error('Certificate pinning failed'));
          callback(new Error('Certificate pinning failed'));
          return;
        }
      }

      callback(null, socket);
    });

    return socket;
  }
}
```

### Mutual TLS

```typescript
// security/mtls.ts

/**
 * Mutual TLS authentication
 */
export class MutualTLS {
  /**
   * Validate client certificate
   */
  static validateClientCertificate(cert: tls.PeerCertificate): {
    valid: boolean;
    clientID?: string;
    error?: string;
  } {
    // Check if certificate is expired
    if (new Date(cert.valid_to) < new Date()) {
      return { valid: false, error: 'Certificate expired' };
    }

    // Check if certificate is not yet valid
    if (new Date(cert.valid_from) > new Date()) {
      return { valid: false, error: 'Certificate not yet valid' };
    }

    // Extract client ID from certificate
    const cn = cert.subject.CN;

    if (!cn || !cn.startsWith('client-')) {
      return { valid: false, error: 'Invalid client ID format' };
    }

    const clientID = cn.replace('client-', '');

    // Check revocation
    if (this.isRevoked(cert)) {
      return { valid: false, error: 'Certificate revoked' };
    }

    return { valid: true, clientID };
  }

  /**
   * Check if certificate is revoked
   */
  private static isRevoked(cert: tls.PeerCertificate): boolean {
    // Check CRL or OCSP
    const serial = cert.serialNumber;
    return this.revocationStore.has(serial);
  }

  /**
   * Express middleware for mTLS
   */
  static middleware() {
    return (req: Request, res: Response, next: NextFunction) => {
      const socket = req.socket as any;
      const cert = socket.getPeerCertificate();

      if (!cert || Object.keys(cert).length === 0) {
        return res.status(401).json({ error: 'Client certificate required' });
      }

      const validation = this.validateClientCertificate(cert);

      if (!validation.valid) {
        return res.status(403).json({
          error: 'Invalid client certificate',
          reason: validation.error
        });
      }

      // Add client info to request
      (req as AuthenticatedRequest).client = {
        cert,
        id: validation.clientID
      };

      next();
    };
  }
}
```

---

## 4. PII Detection & Classification

### PII Scanner

```typescript
// security/pii-scanner.ts

/**
 * PII detection and classification
 */
export class PIIScanner {
  private patterns: PIIPattern[];

  constructor() {
    this.patterns = [
      {
        type: 'email',
        category: 'contact',
        confidence: 'high',
        pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi,
        sample: 'user@example.com'
      },
      {
        type: 'phone',
        category: 'contact',
        confidence: 'medium',
        pattern: /(\+?1[-.\s]?)?(\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}([-\.\s]?[0-9]{4})?/g,
        sample: '+1 (555) 123-4567'
      },
      {
        type: 'ssn',
        category: 'government_id',
        confidence: 'high',
        pattern: /\d{3}-\d{2}-\d{4}|\d{9}/g,
        sample: '123-45-6789'
      },
      {
        type: 'credit_card',
        category: 'financial',
        confidence: 'high',
        pattern: /\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}/g,
        sample: '4111 1111 1111 1111'
      },
      {
        type: 'passport',
        category: 'government_id',
        confidence: 'high',
        pattern: /[A-Z]{2}\d{6,}/g,
        sample: 'US12345678'
      },
      {
        type: 'drivers_license',
        category: 'government_id',
        confidence: 'medium',
        pattern: /[A-Z]{1,2}\d{6,8}/g,
        sample: 'CA1234567'
      },
      {
        type: 'iban',
        category: 'financial',
        confidence: 'high',
        pattern: /[A-Z]{2}\d{2}[A-Z0-9]{11,30}/g,
        sample: 'GB82WEST12345698765432'
      },
      {
        type: 'ip_address',
        category: 'technical',
        confidence: 'low',
        pattern: /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/g,
        sample: '192.168.1.1'
      },
      {
        type: 'address',
        category: 'location',
        confidence: 'low',
        pattern: /\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)[\s,]+[A-Z][a-z]+/gi,
        sample: '123 Main Street, Springfield'
      },
      {
        type: 'dob',
        category: 'personal',
        confidence: 'medium',
        pattern: /\b(0[1-9]|1[0-2])[-/.](0[1-9]|[12][0-9]|3[01])[-/.](19|20)\d{2}\b/g,
        sample: '01/15/1980'
      }
    ];
  }

  /**
   * Scan text for PII
   */
  scan(text: string): PIIScanResult {
    const findings: PIIFinding[] = [];

    for (const pattern of this.patterns) {
      const matches = text.matchAll(pattern.pattern);

      for (const match of matches) {
        findings.push({
          type: pattern.type,
          category: pattern.category,
          confidence: pattern.confidence,
          value: this.maskValue(match[0], pattern.type),
          startIndex: match.index,
          endIndex: match.index + match[0].length
        });
      }
    }

    // Remove overlapping findings (keep highest confidence)
    const nonOverlapping = this.removeOverlaps(findings);

    return {
      hasPII: nonOverlapping.length > 0,
      findings: nonOverlapping,
      summary: this.summarizeFindings(nonOverlapping)
    };
  }

  /**
   * Scan database records for PII
   */
  async scanRecords(records: Record<string, any>[]): Promise<PIIScanResult[]> {
    const results: PIIScanResult[] = [];

    for (const record of records) {
      const text = JSON.stringify(record);
      results.push(this.scan(text));
    }

    return results;
  }

  /**
   * Mask value for display
   */
  private maskValue(value: string, type: string): string {
    const length = value.length;

    switch (type) {
      case 'email':
        return value.replace(/(.{2})[^@]+(@.*)/, '$1***$2');

      case 'phone':
        return value.replace(/(\d{3})\d{3,}/, '$1***');

      case 'ssn':
      case 'passport':
      case 'drivers_license':
        return value.slice(0, 3) + '***' + value.slice(-4);

      case 'credit_card':
        return '****' + value.slice(-4);

      case 'iban':
        return value.slice(0, 4) + '****' + value.slice(-4);

      default:
        return value.slice(0, 2) + '*'.repeat(length - 4) + value.slice(-2);
    }
  }

  /**
   * Remove overlapping findings
   */
  private removeOverlaps(findings: PIIFinding[]): PIIFinding[] {
    const sorted = [...findings].sort((a, b) => a.startIndex - b.startIndex);
    const nonOverlapping: PIIFinding[] = [];

    for (const finding of sorted) {
      const overlaps = nonOverlapping.some(existing =>
        finding.startIndex < existing.endIndex &&
        finding.endIndex > existing.startIndex
      );

      if (!overlaps) {
        nonOverlapping.push(finding);
      }
    }

    return nonOverlapping;
  }

  /**
   * Summarize findings
   */
  private summarizeFindings(findings: PIIFinding[]): PIISummary {
    const byType = new Map<string, number>();
    const byCategory = new Map<string, number>();

    for (const finding of findings) {
      byType.set(finding.type, (byType.get(finding.type) || 0) + 1);
      byCategory.set(finding.category, (byCategory.get(finding.category) || 0) + 1);
    }

    return {
      total: findings.length,
      byType: Object.fromEntries(byType),
      byCategory: Object.fromEntries(byCategory),
      highConfidence: findings.filter(f => f.confidence === 'high').length,
      mediumConfidence: findings.filter(f => f.confidence === 'medium').length,
      lowConfidence: findings.filter(f => f.confidence === 'low').length
    };
  }
}

interface PIIFinding {
  type: string;
  category: string;
  confidence: 'high' | 'medium' | 'low';
  value: string;
  startIndex: number;
  endIndex: number;
}

interface PIIScanResult {
  hasPII: boolean;
  findings: PIIFinding[];
  summary: PIISummary;
}

interface PIISummary {
  total: number;
  byType: Record<string, number>;
  byCategory: Record<string, number>;
  highConfidence: number;
  mediumConfidence: number;
  lowConfidence: number;
}
```

---

## 5. Data Masking & Redaction

### Dynamic Data Masking

```typescript
// security/data-masking.ts

/**
 * Dynamic data masking for display
 */
export class DataMasking {
  /**
   * Mask PII fields in object
   */
  maskObject<T extends Record<string, any>>(
    obj: T,
    maskRules: MaskRule[],
    context: {
      userRole: string;
      userPermissions: string[];
      dataType: string;
    }
  ): T {
    const masked = { ...obj };

    for (const rule of maskRules) {
      if (this.shouldMask(rule, context)) {
        const field = rule.field as keyof T;

        if (obj[field] !== undefined) {
          (masked as any)[field] = this.maskValue(
            obj[field],
            rule.maskType,
            rule.unmaskedChars
          );
        }
      }
    }

    return masked;
  }

  /**
   * Determine if field should be masked
   */
  private shouldMask(rule: MaskRule, context: {
    userRole: string;
    userPermissions: string[];
    dataType: string;
  }): boolean {
    // Check if user has permission to view unmasked data
    if (context.userPermissions.includes(`view:${rule.field}`)) {
      return false;
    }

    // Check role-based access
    if (rule.allowedRoles && !rule.allowedRoles.includes(context.userRole)) {
      return true;
    }

    // Check data type restrictions
    if (rule.restrictedDataTypes && rule.restrictedDataTypes.includes(context.dataType)) {
      return true;
    }

    return rule.maskByDefault;
  }

  /**
   * Mask value according to mask type
   */
  private maskValue(value: any, maskType: MaskType, unmaskedChars: number = 0): any {
    if (typeof value !== 'string') {
      return value;
    }

    switch (maskType) {
      case 'full':
        return '***';

      case 'partial':
        if (value.length <= unmaskedChars * 2) {
          return '*'.repeat(value.length);
        }
        return value.slice(0, unmaskedChars) +
               '*'.repeat(value.length - unmaskedChars * 2) +
               value.slice(-unmaskedChars);

      case 'email':
        return value.replace(/(.{2})[^@]+(@.*)/, '$1***$2');

      case 'phone':
        return value.replace(/(\d{3})\d{3,}/, '$1***');

      case 'credit_card':
        return value.length >= 4 ? '****' + value.slice(-4) : '****';

      case 'name':
        return value.charAt(0) + '***';

      case 'address':
        const parts = value.split(' ');
        return parts.slice(0, 2).join(' ') + ' ***';

      default:
        return '***';
    }
  }

  /**
   * Generate masked view for logging
   */
  maskForLogging(obj: any): any {
    const piiFields = [
      'email', 'phone', 'mobile', 'ssn', 'password',
      'creditCard', 'cvv', 'iban', 'passport', 'driversLicense',
      'firstName', 'lastName', 'address', 'dob'
    ];

    const masked = { ...obj };

    for (const field of piiFields) {
      if (masked[field]) {
        masked[field] = this.maskValue(masked[field], this.inferMaskType(field));
      }
    }

    return masked;
  }

  private inferMaskType(field: string): MaskType {
    if (field.includes('email')) return 'email';
    if (field.includes('phone') || field.includes('mobile')) return 'phone';
    if (field.includes('creditCard') || field.includes('cvv')) return 'credit_card';
    if (field.includes('name')) return 'name';
    if (field.includes('address')) return 'address';
    return 'partial';
  }
}

type MaskType = 'full' | 'partial' | 'email' | 'phone' | 'credit_card' | 'name' | 'address';

interface MaskRule {
  field: string;
  maskType: MaskType;
  maskByDefault: boolean;
  allowedRoles?: string[];
  restrictedDataTypes?: string[];
  unmaskedChars?: number;
}
```

---

## 6. Key Management

### Key Management Service

```typescript
// security/kms.ts

/**
 * Key Management Service integration
 */
export class KeyManagementService {
  private kmsClient: KMSClient;
  private cache: Map<string, CachedKey>;

  /**
   * Generate new data key
   */
  async generateDataKey(context: {
    fieldType: string;
    userId?: string;
  }): Promise<DataEncryptionKey> {
    // Generate key locally
    const key = crypto.randomBytes(32);  // 256-bit

    // Encrypt key with KMS master key
    const masterKeyId = process.env.KMS_MASTER_KEY_ID;
    const encryptedKey = await this.kmsClient.encrypt({
      KeyId: masterKeyId,
      Plaintext: key
    });

    const dek: DataEncryptionKey = {
      id: crypto.randomUUID(),
      key,
      encryptedKey: encryptedKey.CiphertextBlob,
      masterKeyId,
      createdAt: new Date(),
      context
    };

    // Store encrypted key
    await this.keyStore.save(dek);

    // Cache plaintext key (in memory only)
    this.cache.set(dek.id, {
      key,
      expiresAt: Date.now() + 60 * 60 * 1000  // 1 hour
    });

    return dek;
  }

  /**
   * Get data key (decrypt if needed)
   */
  async getKey(
    keyId: string,
    context: {
      fieldType: string;
      userId?: string;
    }
  ): Promise<DataEncryptionKey> {
    // Check cache first
    const cached = this.cache.get(keyId);
    if (cached && cached.expiresAt > Date.now()) {
      return {
        id: keyId,
        key: cached.key,
        context
      };
    }

    // Get encrypted key from storage
    const stored = await this.keyStore.findById(keyId);

    if (!stored) {
      throw new Error('Key not found');
    }

    // Decrypt key using KMS
    const decrypted = await this.kmsClient.decrypt({
      CiphertextBlob: stored.encryptedKey
    });

    const key: DataEncryptionKey = {
      id: stored.id,
      key: decrypted.Plaintext as Buffer,
      masterKeyId: stored.masterKeyId,
      createdAt: stored.createdAt,
      context: stored.context
    };

    // Cache decrypted key
    this.cache.set(keyId, {
      key: key.key,
      expiresAt: Date.now() + 60 * 60 * 1000
    });

    return key;
  }

  /**
   * Rotate data key
   */
  async rotateKey(keyId: string): Promise<DataEncryptionKey> {
    const oldKey = await this.keyStore.findById(keyId);

    if (!oldKey) {
      throw new Error('Key not found');
    }

    // Generate new key
    const newKey = await this.generateDataKey(oldKey.context);

    // Schedule old key for deletion (after re-encryption period)
    await this.scheduleKeyDeletion(keyId, {
      delay: 7 * 24 * 60 * 60 * 1000  // 7 days
    });

    return newKey;
  }

  /**
   * Schedule key deletion
   */
  private async scheduleKeyDeletion(
    keyId: string,
    options: { delay: number }
  ): Promise<void> {
    setTimeout(async () => {
      await this.keyStore.delete(keyId);
      this.cache.delete(keyId);
    }, options.delay);
  }

  /**
   * Generate HMAC for data integrity
   */
  async generateHMAC(data: string, keyId: string): Promise<string> {
    const key = await this.getKey(keyId, { fieldType: 'hmac' });

    const hmac = crypto.createHmac('sha256', key.key);
    hmac.update(data);

    return hmac.digest('hex');
  }

  /**
   * Verify HMAC
   */
  async verifyHMAC(data: string, signature: string, keyId: string): Promise<boolean> {
    const expected = await this.generateHMAC(data, keyId);

    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected)
    );
  }
}

interface CachedKey {
  key: Buffer;
  expiresAt: number;
}
```

### Key Rotation

```typescript
// security/key-rotation.ts

/**
 * Automated key rotation
 */
export class KeyRotationService {
  /**
   * Check keys due for rotation
   */
  async getKeysNeedingRotation(): Promise<string[]> {
    const keys = await this.keyStore.findAll();
    const needingRotation: string[] = [];

    for (const key of keys) {
      const age = Date.now() - key.createdAt.getTime();
      const maxAge = 90 * 24 * 60 * 60 * 1000;  // 90 days

      if (age > maxAge) {
        needingRotation.push(key.id);
      }
    }

    return needingRotation;
  }

  /**
   * Rotate all keys for a field
   */
  async rotateFieldKeys(fieldType: string): Promise<void> {
    const keys = await this.keyStore.findByFieldType(fieldType);

    for (const key of keys) {
      await this.rotateKey(key.id);
    }
  }

  /**
   * Rotate key and re-encrypt data
   */
  async rotateKey(keyId: string): Promise<void> {
    // 1. Generate new key
    const kms = new KeyManagementService();
    const newKey = await kms.generateDataKey({ fieldType: 'rotation' });

    // 2. Get all records encrypted with old key
    const records = await this.encryptedDataStore.findByKeyId(keyId);

    // 3. Re-encrypt each record with new key
    for (const record of records) {
      const decrypted = await this.decryptRecord(record, keyId);
      const reencrypted = await this.encryptRecord(decrypted, newKey.id);

      await this.encryptedDataStore.update(record.id, reencrypted);
    }

    // 4. Mark old key for deletion
    await this.keyStore.markForDeletion(keyId);

    // 5. Log rotation
    await this.auditLogger.log({
      action: 'key_rotated',
      oldKeyId: keyId,
      newKeyId: newKey.id,
      recordsRotated: records.length
    });
  }
}
```

---

## 7. Database Security

### Database Access Control

```typescript
// security/database-security.ts

/**
 * Database security utilities
 */
export class DatabaseSecurity {
  /**
   * Create read-only database connection
   */
  static getReadOnlyConnection(): ConnectionConfig {
    return {
      host: process.env.DB_HOST,
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME,
      user: process.env.DB_READONLY_USER || 'app_readonly',
      password: process.env.DB_READONLY_PASSWORD,
      ssl: {
        rejectUnauthorized: true,
        ca: fs.readFileSync(process.env.DB_CA_PATH).toString()
      },
      // Read-only user has SELECT only
      readonly: true
    };
  }

  /**
   * Row-level security policies
   */
  static enableRLS(): string {
    return `
      -- Enable Row Level Security
      ALTER TABLE trips ENABLE ROW LEVEL SECURITY;

      -- Policy: Users can only see their own trips or their agency's trips
      CREATE POLICY user_trips ON trips
        FOR SELECT
        USING (
          customer_id = current_user_id()
          OR agency_id = (SELECT agency_id FROM users WHERE id = current_user_id())
        );

      -- Policy: Agents can see all trips in their agency
      CREATE POLICY agency_trips ON trips
        TO authenticated
        USING (
          agency_id = (SELECT agency_id FROM users WHERE id = current_user_id())
        );

      -- Policy: Users can only update their own profile
      CREATE POLICY user_profile ON users
        FOR UPDATE
        USING (id = current_user_id());
    `;
  }

  /**
   * Audit trigger for sensitive tables
   */
  static auditTrigger(tableName: string): string {
    return `
      -- Create audit table if not exists
      CREATE TABLE IF NOT EXISTS ${tableName}_audit (
        id SERIAL PRIMARY KEY,
        table_name TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        old_data JSONB,
        new_data JSONB,
        changed_by TEXT NOT NULL,
        changed_at TIMESTAMP DEFAULT NOW()
      );

      -- Create trigger function
      CREATE OR REPLACE FUNCTION audit_${tableName}()
      RETURNS TRIGGER AS $$
      BEGIN
        IF TG_OP = 'INSERT' THEN
          INSERT INTO ${tableName}_audit (table_name, record_id, action, new_data, changed_by)
          VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW), current_user);
          RETURN NEW;

        ELSIF TG_OP = 'UPDATE' THEN
          INSERT INTO ${tableName}_audit (table_name, record_id, action, old_data, new_data, changed_by)
          VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), current_user);
          RETURN NEW;

        ELSIF TG_OP = 'DELETE' THEN
          INSERT INTO ${tableName}_audit (table_name, record_id, action, old_data, changed_by)
          VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD), current_user);
          RETURN OLD;

        END IF;
      END;
      $$ LANGUAGE plpgsql;

      -- Create trigger
      DROP TRIGGER IF EXISTS ${tableName}_audit ON ${tableName};
      CREATE TRIGGER ${tableName}_audit
        AFTER INSERT OR UPDATE OR DELETE ON ${tableName}
        FOR EACH ROW EXECUTE FUNCTION audit_${tableName}();
    `;
  }
}
```

---

## 8. Backup Security

### Encrypted Backups

```typescript
// security/backup-security.ts

/**
 * Secure backup service
 */
export class SecureBackupService {
  private encryption: FieldEncryption;

  /**
   * Create encrypted backup
   */
  async createBackup(backup: {
    name: string;
    data: any;
    metadata: BackupMetadata;
  }): Promise<SecureBackup> {
    // Serialize data
    const jsonData = JSON.stringify(backup.data);

    // Compress
    const compressed = await this.compress(jsonData);

    // Encrypt
    const encrypted = await this.encryption.encryptField(compressed, {
      fieldType: 'backup',
      recordId: backup.name
    });

    // Generate HMAC
    const hmac = await this.generateHMAC(encrypted.encryptedData, 'backup');

    const secureBackup: SecureBackup = {
      id: crypto.randomUUID(),
      name: backup.name,
      version: backup.metadata.version || 1,
      encryptedData: encrypted.encryptedData,
      iv: encrypted.iv,
      authTag: encrypted.authTag,
      keyId: encrypted.keyId,
      hmac,
      algorithm: encrypted.algorithm,
      metadata: {
        ...backup.metadata,
        createdAt: new Date(),
        size: compressed.length,
        checksum: this.calculateChecksum(compressed)
      }
    };

    // Store backup
    await this.backupStore.save(secureBackup);

    // Log to audit
    await this.auditLogger.log({
      action: 'backup_created',
      backupId: secureBackup.id,
      name: backup.name,
      metadata: backup.metadata
    });

    return secureBackup;
  }

  /**
   * Restore backup
   */
  async restoreBackup(backupId: string): Promise<{
    data: any;
    metadata: BackupMetadata;
  }> {
    const backup = await this.backupStore.findById(backupId);

    if (!backup) {
      throw new Error('Backup not found');
    }

    // Verify HMAC
    const hmacValid = await this.verifyHMAC(
      backup.encryptedData,
      backup.hmac,
      'backup'
    );

    if (!hmacValid) {
      throw new Error('Backup integrity check failed');
    }

    // Decrypt
    const decrypted = await this.encryption.decryptField({
      encryptedData: backup.encryptedData,
      iv: backup.iv,
      authTag: backup.authTag,
      keyId: backup.keyId,
      algorithm: backup.algorithm
    }, {
      fieldType: 'backup',
      recordId: backup.name
    });

    // Decompress
    const decompressed = await this.decompress(decrypted);

    // Parse
    const data = JSON.parse(decompressed);

    // Verify checksum
    const calculatedChecksum = this.calculateChecksum(decompressed);
    if (calculatedChecksum !== backup.metadata.checksum) {
      throw new Error('Backup checksum mismatch');
    }

    // Log restore
    await this.auditLogger.log({
      action: 'backup_restored',
      backupId,
      name: backup.name
    });

    return {
      data,
      metadata: backup.metadata
    };
  }

  /**
   * List backups
   */
  async listBackups(filters?: {
    name?: string;
    before?: Date;
    after?: Date;
  }): Promise<SecureBackupInfo[]> {
    const backups = await this.backupStore.findAll();

    let filtered = backups;

    if (filters?.name) {
      filtered = filtered.filter(b => b.name.includes(filters.name));
    }

    if (filters?.before) {
      filtered = filtered.filter(b => b.metadata.createdAt < filters.before);
    }

    if (filters?.after) {
      filtered = filtered.filter(b => b.metadata.createdAt > filters.after);
    }

    // Return without encrypted data
    return filtered.map(b => ({
      id: b.id,
      name: b.name,
      version: b.version,
      metadata: b.metadata,
      createdAt: b.metadata.createdAt,
      size: b.metadata.size
    }));
  }

  /**
   * Delete old backups
   */
  async deleteOldBackups(retentionDays: number): Promise<number> {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - retentionDays);

    const backups = await this.backupStore.findAll();
    const toDelete = backups.filter(b => b.metadata.createdAt < cutoff);

    for (const backup of toDelete) {
      await this.backupStore.delete(backup.id);

      // Log deletion
      await this.auditLogger.log({
        action: 'backup_deleted',
        backupId: backup.id,
        name: backup.name,
        reason: 'retention_policy'
      });
    }

    return toDelete.length;
  }

  private calculateChecksum(data: Buffer): string {
    return crypto
      .createHash('sha256')
      .update(data)
      .digest('hex');
  }

  private async compress(data: string): Promise<Buffer> {
    return new Promise((resolve, reject) => {
      zlib.gzip(data, (err, compressed) => {
        if (err) reject(err);
        else resolve(compressed);
      });
    });
  }

  private async decompress(data: Buffer): Promise<string> {
    return new Promise((resolve, reject) => {
      zlib.gunzip(data, (err, decompressed) => {
        if (err) reject(err);
        else resolve(decompressed.toString());
      });
    });
  }
}

interface SecureBackup {
  id: string;
  name: string;
  version: number;
  encryptedData: string;
  iv: string;
  authTag: string;
  keyId: string;
  hmac: string;
  algorithm: string;
  metadata: BackupMetadata & {
    createdAt: Date;
    size: number;
    checksum: string;
  };
}

interface BackupMetadata {
  version: number;
  description?: string;
  createdBy?: string;
}
```

---

## 9. Data Retention & Disposal

### Retention Policy

```typescript
// security/retention.ts

/**
 * Data retention and disposal
 */
export class DataRetentionService {
  /**
   * Apply retention policies
   */
  async applyRetentionPolicies(): Promise<RetentionReport> {
    const policies = [
      {
        dataType: 'trip_inquiries',
        retentionDays: 365 * 2,  // 2 years
        action: 'anonymize'
      },
      {
        dataType: 'trips_not_booked',
        retentionDays: 180,  // 6 months
        action: 'delete'
      },
      {
        dataType: 'completed_trips',
        retentionDays: 365 * 7,  // 7 years
        action: 'archive'
      },
      {
        dataType: 'user_sessions',
        retentionDays: 30,
        action: 'delete'
      },
      {
        dataType: 'audit_logs',
        retentionDays: 365 * 2,  // 2 years
        action: 'archive'
      },
      {
        dataType: 'payment_data',
        retentionDays: 180,  // 6 months
        action: 'delete'
      }
    ];

    const results: RetentionActionResult[] = [];

    for (const policy of policies) {
      const result = await this.applyPolicy(policy);
      results.push(result);
    }

    return {
      executedAt: new Date(),
      policies: policies.length,
      results,
      totalRecordsProcessed: results.reduce((sum, r) => sum + r.recordsAffected, 0)
    };
  }

  /**
   * Apply single retention policy
   */
  private async applyPolicy(policy: RetentionPolicy): Promise<RetentionActionResult> {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - policy.retentionDays);

    let recordsAffected = 0;

    switch (policy.action) {
      case 'delete':
        recordsAffected = await this.deleteOldRecords(policy.dataType, cutoff);
        break;

      case 'anonymize':
        recordsAffected = await this.anonymizeOldRecords(policy.dataType, cutoff);
        break;

      case 'archive':
        recordsAffected = await this.archiveOldRecords(policy.dataType, cutoff);
        break;
    }

    return {
      policy: policy.dataType,
      action: policy.action,
      cutoff,
      recordsAffected
    };
  }

  /**
   * Anonymize old records (remove PII but keep analytics data)
   */
  private async anonymizeOldRecords(
    dataType: string,
    cutoff: Date
  ): Promise<number> {
    const records = await this.getRecordsOlderThan(dataType, cutoff);

    for (const record of records) {
      const anonymized = this.anonymizeRecord(record);

      await this.dataStore.update(record.id, anonymized);
    }

    return records.length;
  }

  /**
   * Anonymize a single record
   */
  private anonymizeRecord(record: any): any {
    const anonymized = { ...record };

    // Remove direct identifiers
    delete anonymized.email;
    delete anonymized.phone;
    delete anonymized.firstName;
    delete anonymized.lastName;
    delete anonymized.address;

    // Replace with pseudonymous identifier
    anonymized.pseudonymousId = this.generatePseudonymousId(record.id);

    // Generalize dates (keep month/year only)
    if (record.createdAt) {
      const date = new Date(record.createdAt);
      anonymized.createdYear = date.getFullYear();
      anonymized.createdMonth = date.getMonth() + 1;
      delete anonymized.createdAt;
    }

    // Keep analytics data
    return anonymized;
  }

  /**
   * Securely delete data
   */
  async secureDelete(dataType: string, recordId: string): Promise<void> {
    // 1. Soft delete (mark as deleted)
    await this.dataStore.softDelete(recordId);

    // 2. Schedule hard deletion (after grace period)
    setTimeout(async () => {
      await this.hardDelete(recordId);

      // 3. Overwrite storage (if using custom storage)
      await this.overwriteStorage(recordId);
    }, 30 * 24 * 60 * 60 * 1000);  // 30 days
  }

  /**
   * Cryptographic erasure
   */
  private async overwriteStorage(recordId: string): Promise<void> {
    // For encrypted storage, just delete the encryption key
    // This makes the data permanently unrecoverable
    const keyId = await this.dataStore.getEncryptionKeyId(recordId);

    if (keyId) {
      await this.keyManager.destroyKey(keyId);
    }
  }
}
```

---

## 10. Compliance

### GDPR Compliance

```typescript
// compliance/gdpr.ts

/**
 * GDPR compliance utilities
 */
export class GDPRCompliance {
  /**
   * Handle data subject access request (DSAR)
   */
  async handleAccessRequest(userId: string): Promise<DataSubjectCopy> {
    // Collect all user data
    const userData = await this.collectUserData(userId);

    // Remove data about other users (third-party data)
    const filtered = this.filterThirdPartyData(userData);

    // Generate report
    return {
      userId,
      generatedAt: new Date(),
      dataCategories: this.categorizeData(filtered),
      records: filtered,
      summary: this.generateDataSummary(filtered)
    };
  }

  /**
   * Handle data erasure request (right to be forgotten)
   */
  async handleErasureRequest(userId: string): Promise<ErasureReport> {
    const erasureLog: ErasureLogEntry[] = [];

    // Get all user data
    const userData = await this.collectUserData(userId);

    // Erase from each system
    for (const [system, records] of Object.entries(userData)) {
      for (const record of records) {
        try {
          await this.eraseRecord(system, record.id);
          erasureLog.push({
            system,
            recordId: record.id,
            status: 'erased',
            timestamp: new Date()
          });
        } catch (error) {
          erasureLog.push({
            system,
            recordId: record.id,
            status: 'failed',
            reason: error.message,
            timestamp: new Date()
          });
        }
      }
    }

    return {
      userId,
      requestedAt: new Date(),
      log: erasureLog,
      summary: {
        total: erasureLog.length,
        erased: erasureLog.filter(e => e.status === 'erased').length,
        failed: erasureLog.filter(e => e.status === 'failed').length
      }
    };
  }

  /**
   * Handle data portability request
   */
  async handlePortabilityRequest(userId: string): Promise<PortableData> {
    const userData = await this.collectUserData(userId);

    // Convert to portable formats
    const formats = {
      json: JSON.stringify(userData, null, 2),
      csv: this.convertToCSV(userData),
      pdf: await this.generatePDFReport(userData)
    };

    return {
      userId,
      generatedAt: new Date(),
      formats,
      summary: this.generateDataSummary(userData)
    };
  }

  /**
   * Track consent
   */
  async recordConsent(userId: string, consent: {
    type: 'marketing' | 'analytics' | 'cookies';
    given: boolean;
    timestamp?: Date;
  }): Promise<void> {
    await this.consentStore.save({
      userId,
      ...consent,
      timestamp: consent.timestamp || new Date(),
      ipAddress: null,  // Will be filled from request
      userAgent: null
    });

    // Log to audit
    await this.auditLogger.log({
      action: 'consent_recorded',
      userId,
      consentType: consent.type,
      given: consent.given
    });
  }

  /**
   * Check consent status
   */
  async hasConsent(userId: string, consentType: string): Promise<boolean> {
    const consent = await this.consentStore.findLatest(userId, consentType);

    return consent?.given || false;
  }
}
```

---

## Summary

This document defines data security practices for the Travel Agency Agent platform:

**Key Components:**
- **Data Classification** - Public to restricted data categorization
- **Encryption at Rest** - AES-256-GCM field-level encryption
- **Encryption in Transit** - TLS 1.3, certificate pinning
- **PII Detection** - Automated PII scanning and classification
- **Data Masking** - Dynamic masking based on user permissions
- **Key Management** - KMS integration, key rotation
- **Database Security** - Row-level security, audit triggers
- **Backup Security** - Encrypted, compressed, HMAC-verified backups
- **Data Retention** - Automated retention policies and disposal
- **Compliance** - GDPR data subject rights

**Next:** [SECURITY_04: Infrastructure Security](./SECURITY_04_INFRASTRUCTURE_SECURITY.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-04-25
**Status:** ✅ Complete
