# SECURITY_03: Data Security Deep Dive

> Encryption, secrets management, PII protection, and data security

---

## Table of Contents

1. [Overview](#overview)
2. [Encryption at Rest](#encryption-at-rest)
3. [Encryption in Transit](#encryption-in-transit)
4. [PII Identification and Handling](#pii-identification-and-handling)
5. [Secret Management](#secret-management)
6. [API Key Security](#api-key-security)
7. [Database Security](#database-security)
8. [Data Retention and Deletion](#data-retention-and-deletion)

---

## Overview

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEFENSE IN DEPTH                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    APPLICATION                           │    │
│  │  • Input validation  • Output encoding  • AuthN/AuthZ   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API GATEWAY                           │    │
│  │  • Rate limiting  • TLS termination  • WAF              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                     SERVICES                             │    │
│  │  • Service mesh  • mTLS  • Service auth                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    DATA LAYER                            │    │
│  │  • Encryption at rest  • Row-level security  • Audits   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   INFRASTRUCTURE                          │    │
│  │  • Network isolation  • Firewall rules  • IAM           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Classification

| Classification | Description | Examples | Protection Level |
|----------------|-------------|----------|------------------|
| **Public** | No restrictions | Marketing content, pricing (public) | Standard |
| **Internal** | Company internal only | Internal docs, non-sensitive configs | Standard |
| **Confidential** | Business sensitive | Financial data, customer lists | Enhanced |
| **Restricted** | PII, regulated data | Passport numbers, payment info | Maximum |

---

## Encryption at Rest

### Database Encryption

```typescript
// Application-level encryption for sensitive fields
import crypto from 'crypto';

export class EncryptionService {
  private algorithm = 'aes-256-gcm';
  private key: Buffer;

  constructor() {
    // Get encryption key from secure storage
    const keyHex = process.env.ENCRYPTION_KEY!;
    this.key = Buffer.from(keyHex, 'hex');
  }

  encrypt(plaintext: string): { ciphertext: string; iv: string; tag: string } {
    const iv = crypto.randomBytes(12); // GCM recommended IV length
    const cipher = crypto.createCipheriv(this.algorithm, this.key, iv);

    let ciphertext = cipher.update(plaintext, 'utf8', 'hex');
    ciphertext += cipher.final('hex');

    const tag = cipher.getAuthTag();

    return {
      ciphertext,
      iv: iv.toString('hex'),
      tag: tag.toString('hex'),
    };
  }

  decrypt(ciphertext: string, iv: string, tag: string): string {
    const decipher = crypto.createDecipheriv(
      this.algorithm,
      this.key,
      Buffer.from(iv, 'hex')
    );

    decipher.setAuthTag(Buffer.from(tag, 'hex'));

    let plaintext = decipher.update(ciphertext, 'hex', 'utf8');
    plaintext += decipher.final('utf8');

    return plaintext;
  }
}

// ORM model with encrypted fields
export class Customer {
  id: string;
  name: string;
  email: string;

  // Encrypted fields
  passportNumberEncrypted: string;
  passportNumberIv: string;
  passportNumberTag: string;

  // Getter/setter for automatic encryption
  get passportNumber(): string {
    if (!this.passportNumberEncrypted) return '';
    return encryptionService.decrypt(
      this.passportNumberEncrypted,
      this.passportNumberIv,
      this.passportNumberTag
    );
  }

  set passportNumber(value: string) {
    if (!value) {
      this.passportNumberEncrypted = '';
      this.passportNumberIv = '';
      this.passportNumberTag = '';
      return;
    }

    const encrypted = encryptionService.encrypt(value);
    this.passportNumberEncrypted = encrypted.ciphertext;
    this.passportNumberIv = encrypted.iv;
    this.passportNumberTag = encrypted.tag;
  }
}
```

### Field-Level Encryption

```typescript
// Decorator for automatic field encryption
function Encrypted() {
  return function (target: any, propertyKey: string) {
    const encryptedKey = `_${propertyKey}Encrypted`;
    const ivKey = `_${propertyKey}Iv`;
    const tagKey = `_${propertyKey}Tag`;

    Object.defineProperty(target, propertyKey, {
      get() {
        if (!this[encryptedKey]) return '';
        return encryptionService.decrypt(
          this[encryptedKey],
          this[ivKey],
          this[tagKey]
        );
      },
      set(value: string) {
        if (!value) {
          this[encryptedKey] = '';
          this[ivKey] = '';
          this[tagKey] = '';
          return;
        }

        const encrypted = encryptionService.encrypt(value);
        this[encryptedKey] = encrypted.ciphertext;
        this[ivKey] = encrypted.iv;
        this[tagKey] = encrypted.tag;
      },
      enumerable: true,
      configurable: true,
    });
  };
}

// Usage
export class PaymentMethod {
  id: string;
  customerId: string;

  @Encrypted()
  cardNumber: string;

  @Encrypted()
  cvv: string;

  expiryMonth: number;
  expiryYear: number;
}
```

### Database Encryption Configuration

```typescript
// PostgreSQL column encryption
// Using pgcrypto extension

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypted column type
CREATE DOMAIN encrypted_text AS text;

-- Function to encrypt
CREATE OR REPLACE FUNCTION encrypt_text(plaintext text)
RETURNS encrypted_text AS $$
  SELECT encode(
    pgp_sym_encrypt(plaintext, current_setting('app.encryption_key')),
    'base64'
  );
$$ LANGUAGE SQL SECURITY DEFINER;

-- Function to decrypt
CREATE OR REPLACE FUNCTION decrypt_text(ciphertext encrypted_text)
RETURNS text AS $$
  SELECT pgp_sym_decrypt(
    decode(ciphertext, 'base64'),
    current_setting('app.encryption_key')
  );
$$ LANGUAGE SQL SECURITY DEFINER;

-- Example table with encrypted columns
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  passport_number encrypted_text,  -- Encrypted
  phone encrypted_text,            -- Encrypted
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query with decryption
SELECT
  id,
  name,
  email,
  decrypt_text(passport_number) as passport_number
FROM customers
WHERE id = $1;
```

### Storage Encryption

```typescript
// S3 client with encryption
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

export class SecureStorage {
  private s3: S3Client;

  constructor() {
    this.s3 = new S3Client({
      region: process.env.AWS_REGION,
      // Enable SSE-KMS (Server-Side Encryption with KMS)
    });
  }

  async uploadEncrypted(
    bucket: string,
    key: string,
    data: Buffer,
    kmsKeyId?: string
  ): Promise<void> {
    const command = new PutObjectCommand({
      Bucket: bucket,
      Key: key,
      Body: data,
      // Server-side encryption
      ServerSideEncryption: 'AES256', // or 'aws:kms' for KMS
      // KMS key ID if using KMS
      SSEKMSKeyId: kmsKeyId,
      // Bucket-level encryption
      BucketKeyEnabled: true,
    });

    await this.s3.send(command);
  }

  // Document storage with encryption
  async uploadDocument(
    tripId: string,
    documentType: string,
    file: Buffer,
    metadata: DocumentMetadata
  ): Promise<string> {
    // Classify document to determine encryption level
    const encryptionLevel = this.classifyDocument(documentType);

    const key = `trips/${tripId}/documents/${documentType}/${Date.now()}`;

    if (encryptionLevel === 'high') {
      // Use KMS for highly sensitive documents
      await this.uploadEncrypted(
        process.env.SECURE_DOCUMENTS_BUCKET!,
        key,
        file,
        process.env.DOCUMENT_KMS_KEY!
      );
    } else {
      // Standard AES-256 for regular documents
      await this.uploadEncrypted(
        process.env.DOCUMENTS_BUCKET!,
        key,
        file
      );
    }

    // Store metadata (without file content)
    await DocumentRepository.create({
      tripId,
      type: documentType,
      storageKey: key,
      encryptionLevel,
      metadata,
      uploadedAt: new Date(),
    });

    return key;
  }

  private classifyDocument(type: string): 'standard' | 'high' {
    const highSecurityTypes = [
      'passport',
      'visa',
      'pan_card',
      'payment_receipt',
    ];

    return highSecurityTypes.includes(type) ? 'high' : 'standard';
  }
}
```

---

## Encryption in Transit

### TLS Configuration

```typescript
// Express HTTPS server with proper TLS configuration
import https from 'https';
import fs from 'fs';

export const createSecureServer = (app: Express) => {
  const tlsOptions = {
    // Certificate
    key: fs.readFileSync(process.env.TLS_KEY_PATH!),
    cert: fs.readFileSync(process.env.TLS_CERT_PATH!),
    ca: fs.readFileSync(process.env.TLS_CA_PATH!), // Certificate chain

    // TLS 1.2+ only, disable weak protocols
    minVersion: 'TLSv1.2',
    maxVersion: 'TLSv1.3',

    // Strong ciphers only
    ciphers: [
      'ECDHE-ECDSA-AES128-GCM-SHA256',
      'ECDHE-RSA-AES128-GCM-SHA256',
      'ECDHE-ECDSA-AES256-GCM-SHA384',
      'ECDHE-RSA-AES256-GCM-SHA384',
      'ECDHE-ECDSA-CHACHA20-POLY1305',
      'ECDHE-RSA-CHACHA20-POLY1305',
    ].join(':'),

    // Prefer server ciphers
    honorCipherOrder: true,

    // Disable client renegotiation
    secureOptions: crypto.constants.SSL_OP_NO_RENEGOTIATION,

    // OCSP stapling
    requestCert: false,
    rejectUnauthorized: true,
  };

  return https.createServer(tlsOptions, app);
};

// HTTP to HTTPS redirect
app.use((req, res, next) => {
  if (!req.secure) {
    return res.redirect(301, `https://${req.headers.host}${req.url}`);
  }
  next();
});

// HSTS header
app.use((req, res, next) => {
  // Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  res.setHeader(
    'Strict-Transport-Security',
    'max-age=31536000; includeSubDomains; preload'
  );
  next();
});
```

### Mutual TLS (mTLS)

```typescript
// mTLS for service-to-service communication
import { Agent } from 'https';

export class ServiceClient {
  private agent: https.Agent;

  constructor() {
    this.agent = new https.Agent({
      // Client certificate for mTLS
      key: fs.readFileSync(process.env.MTLS_CLIENT_KEY!),
      cert: fs.readFileSync(process.env.MTLS_CLIENT_CERT!),
      ca: fs.readFileSync(process.env.MTLS_CA!),

      // Verify server certificate
      rejectUnauthorized: true,

      // Server name indication
      servername: process.env.SERVICE_HOST,

      // TLS configuration
      minVersion: 'TLSv1.2',
      ciphers: [
        'ECDHE-ECDSA-AES128-GCM-SHA256',
        'ECDHE-RSA-AES128-GCM-SHA256',
        'ECDHE-ECDSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES256-GCM-SHA384',
      ].join(':'),
    });
  }

  async request(url: string, options: RequestInit = {}): Promise<Response> {
    return fetch(url, {
      ...options,
      // @ts-ignore - Node fetch types
      agent: this.agent,
    });
  }
}
```

### Service Mesh Security

```typescript
// Istio service mesh authentication
// VirtualService with mTLS

apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: travel-agency
spec:
  mtls:
    mode: STRICT  # Require mTLS for all services
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: payment-service
spec:
  host: payment-service
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL  # mTLS between services
    connectionPool:
      tcp:
        maxConnections: 100
    outlierDetection:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
```

---

## PII Identification and Handling

### PII Classification

```typescript
type PiiCategory =
  | 'identity'        // Name, DOB, government IDs
  | 'contact'         // Email, phone, address
  | 'financial'       // Bank details, card numbers
  | 'travel'          // Passport, visa, itinerary
  | 'health'          // Medical conditions, dietary
  | 'biometric';      // Rarely used

interface PiiField {
  field: string;
  category: PiiCategory;
  sensitivity: 'low' | 'medium' | 'high';
  encrypted: boolean;
  masked: boolean;
  retention: string;  // e.g., "7 years after trip end"
}

export const PII_SCHEMA: Record<string, PiiField[]> = {
  customers: [
    { field: 'name', category: 'identity', sensitivity: 'low', encrypted: false, masked: false, retention: 'forever' },
    { field: 'email', category: 'contact', sensitivity: 'medium', encrypted: false, masked: false, retention: 'forever' },
    { field: 'phone', category: 'contact', sensitivity: 'medium', encrypted: true, masked: true, retention: 'forever' },
    { field: 'address', category: 'contact', sensitivity: 'medium', encrypted: true, masked: false, retention: 'forever' },
    { field: 'dateOfBirth', category: 'identity', sensitivity: 'medium', encrypted: true, masked: true, retention: 'forever' },
    { field: 'passportNumber', category: 'travel', sensitivity: 'high', encrypted: true, masked: true, retention: '5 years after trip' },
    { field: 'panNumber', category: 'financial', sensitivity: 'high', encrypted: true, masked: true, retention: '8 years' },
  ],
  payments: [
    { field: 'cardNumber', category: 'financial', sensitivity: 'high', encrypted: true, masked: true, retention: '12 months' },
    { field: 'cvv', category: 'financial', sensitivity: 'high', encrypted: true, masked: true, retention: '0' }, // Never store CVV
    { field: 'bankAccount', category: 'financial', sensitivity: 'high', encrypted: true, masked: true, retention: '8 years' },
  ],
};
```

### Data Masking

```typescript
export class DataMaskingService {
  // Mask sensitive data for display
  mask(value: string, type: string): string {
    switch (type) {
      case 'email':
        return this.maskEmail(value);

      case 'phone':
        return this.maskPhone(value);

      case 'card':
        return this.maskCard(value);

      case 'passport':
        return this.maskPassport(value);

      case 'pan':
        return this.maskPan(value);

      default:
        return this.maskDefault(value);
    }
  }

  private maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    if (local.length <= 2) {
      return `***@${domain}`;
    }
    return `${local[0]}${'*'.repeat(local.length - 2)}${local[local.length - 1]}@${domain}`;
  }

  private maskPhone(phone: string): string {
    // Show last 4 digits
    return phone.replace(/(\d{3})\d{6}(\d{4})/, '$1******$2');
  }

  private maskCard(card: string): string {
    // Show last 4 digits
    return card.replace(/\d(?=\d{4})/g, '*');
  }

  private maskPassport(passport: string): string {
    // Show first 2 and last 2 characters
    if (passport.length <= 4) return '****';
    return `${passport.slice(0, 2)}${'*'.repeat(passport.length - 4)}${passport.slice(-2)}`;
  }

  private maskPan(pan: string): string {
    // Show last 4 characters
    return pan.replace(/\d(?=\d{4})/g, '*');
  }

  private maskDefault(value: string): string {
    if (value.length <= 4) return '****';
    const visibleChars = Math.ceil(value.length / 4);
    return `${value.slice(0, visibleChars)}${'*'.repeat(value.length - visibleChars * 2)}${value.slice(-visibleChars)}`;
  }

  // Mask entire object based on schema
  maskObject<T extends Record<string, any>>(
    obj: T,
    schema: PiiField[],
    userRole: UserRole
  ): T {
    const masked = { ...obj };
    const permissions = this.getMaskingPermissions(userRole);

    for (const fieldDef of schema) {
      if (!this.shouldMask(fieldDef, permissions)) continue;

      const value = obj[fieldDef.field];
      if (value && typeof value === 'string') {
        masked[fieldDef.field] = this.mask(value, fieldDef.category);
      }
    }

    return masked;
  }

  private shouldMask(field: PiiField, permissions: MaskingPermissions): boolean {
    if (permissions.viewAll) return false;

    switch (field.sensitivity) {
      case 'high':
        return !permissions.viewHighSensitivity;
      case 'medium':
        return !permissions.viewMediumSensitivity;
      case 'low':
        return false;
      default:
        return true;
    }
  }

  private getMaskingPermissions(role: UserRole): MaskingPermissions {
    switch (role) {
      case 'super_admin':
      case 'agency_admin':
        return { viewAll: true };

      case 'senior_agent':
        return {
          viewAll: false,
          viewHighSensitivity: true,
          viewMediumSensitivity: true,
        };

      case 'agent':
        return {
          viewAll: false,
          viewHighSensitivity: false,
          viewMediumSensitivity: true,
        };

      default:
        return {
          viewAll: false,
          viewHighSensitivity: false,
          viewMediumSensitivity: false,
        };
    }
  }
}

interface MaskingPermissions {
  viewAll: boolean;
  viewHighSensitivity: boolean;
  viewMediumSensitivity: boolean;
}
```

### PII Access Logging

```typescript
// Log all access to PII
export class PiiAuditLogger {
  async logAccess(
    userId: string,
    resourceType: string,
    resourceId: string,
    fields: string[],
    context: RequestContext
  ): Promise<void> {
    await AuditLogRepository.create({
      type: 'pii_access',
      userId,
      agencyId: context.agencyId,
      resourceType,
      resourceId,
      fields,
      ip: context.ip,
      userAgent: context.userAgent,
      timestamp: new Date(),
    });
  }

  async logExport(
    userId: string,
    resourceType: string,
    recordCount: number,
    context: RequestContext
  ): Promise<void> {
    await AuditLogRepository.create({
      type: 'pii_export',
      userId,
      agencyId: context.agencyId,
      resourceType,
      recordCount,
      ip: context.ip,
      userAgent: context.userAgent,
      timestamp: new Date(),
    });

    // Alert on large exports
    if (recordCount > 100) {
      await securityAlertService.send({
        type: 'large_pii_export',
        userId,
        agencyId: context.agencyId,
        recordCount,
        severity: recordCount > 1000 ? 'high' : 'medium',
      });
    }
  }
}
```

---

## Secret Management

### HashiCorp Vault Integration

```typescript
import { Vault } from 'node-vault';

export class SecretService {
  private vault: Vault;
  private cache: Map<string, { value: any; expiresAt: number }> = new Map();
  private readonly CACHE_TTL = 300000; // 5 minutes

  constructor() {
    this.vault = new Vault({
      endpoint: process.env.VAULT_ADDR!,
      token: process.env.VAULT_TOKEN!,
    });

    // Rotate token periodically
    this.startTokenRotation();
  }

  async getSecret(path: string): Promise<any> {
    // Check cache first
    const cached = this.cache.get(path);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.value;
    }

    try {
      const result = await this.vault.read(`secret/data/${path}`);
      const secret = result.data.data;

      // Cache the result
      this.cache.set(path, {
        value: secret,
        expiresAt: Date.now() + this.CACHE_TTL,
      });

      return secret;
    } catch (error) {
      throw new Error(`Failed to retrieve secret: ${path}`);
    }
  }

  async getDatabaseCredentials(database: string): Promise<DatabaseCredentials> {
    const secret = await this.getSecret(`database/${database}`);
    return {
      host: secret.host,
      port: secret.port,
      username: secret.username,
      password: secret.password,
      database: secret.database,
    };
  }

  async getApiKey(service: string): Promise<string> {
    const secret = await this.getSecret(`api-keys/${service}`);
    return secret.key;
  }

  async encryptData(data: string, path: string): Promise<string> {
    try {
      const result = await this.vault.write(`transit/encrypt/${path}`, {
        plaintext: Buffer.from(data).toString('base64'),
      });
      return result.data.ciphertext;
    } catch (error) {
      throw new Error(`Encryption failed: ${error.message}`);
    }
  }

  async decryptData(ciphertext: string, path: string): Promise<string> {
    try {
      const result = await this.vault.write(`transit/decrypt/${path}`, {
        ciphertext,
      });
      return Buffer.from(result.data.plaintext, 'base64').toString();
    } catch (error) {
      throw new Error(`Decryption failed: ${error.message}`);
    }
  }

  private startTokenRotation(): void {
    // Renew token periodically
    setInterval(async () => {
      try {
        await this.vault.tokenRenewSelf({ increment: '1h' });
      } catch (error) {
        console.error('Token renewal failed:', error);
      }
    }, 30 * 60 * 1000); // Every 30 minutes
  }
}
```

### Environment Variable Management

```typescript
// Type-safe environment variables with validation
import { z } from 'zod';

const envSchema = z.object({
  // Application
  NODE_ENV: z.enum(['development', 'staging', 'production']),
  PORT: z.string().transform(Number).default(3000),
  APP_URL: z.url(),

  // Database
  DATABASE_URL: z.string().url(),
  DATABASE_POOL_SIZE: z.string().transform(Number).default(10),

  // Redis
  REDIS_URL: z.string().optional(),
  REDIS_TLS_URL: z.string().optional(),

  // Encryption
  ENCRYPTION_KEY: z.string().length(64), // 32 bytes = 64 hex chars

  // JWT
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRY: z.string().default('15m'),
  REFRESH_TOKEN_EXPIRY: z.string().default('7d'),

  // AWS
  AWS_REGION: z.string().default('ap-south-1'),
  AWS_ACCESS_KEY_ID: z.string().optional(),
  AWS_SECRET_ACCESS_KEY: z.string().optional(),
  S3_BUCKET: z.string().optional(),

  // External APIs
  RAZORPAY_KEY_ID: z.string().optional(),
  RAZORPAY_KEY_SECRET: z.string().optional(),
  SENDGRID_API_KEY: z.string().optional(),
  TWILIO_ACCOUNT_SID: z.string().optional(),
  TWILIO_AUTH_TOKEN: z.string().optional(),

  // Vault
  VAULT_ADDR: z.string().optional(),
  VAULT_TOKEN: z.string().optional(),
  VAULT_ROLE: z.string().optional(),

  // OAuth
  GOOGLE_CLIENT_ID: z.string().optional(),
  GOOGLE_CLIENT_SECRET: z.string().optional(),
  MICROSOFT_CLIENT_ID: z.string().optional(),
  MICROSOFT_CLIENT_SECRET: z.string().optional(),
});

export type Env = z.infer<typeof envSchema>;

export function loadEnv(): Env {
  const parsed = envSchema.safeParse(process.env);

  if (!parsed.success) {
    console.error('Invalid environment configuration:');
    parsed.error.errors.forEach((err) => {
      console.error(`  ${err.path.join('.')}: ${err.message}`);
    });
    process.exit(1);
  }

  return parsed.data;
}

// Use in application
const env = loadEnv();
```

---

## API Key Security

### API Key Management

```typescript
interface ApiKey {
  id: string;
  keyId: string;           // Public identifier
  keyHash: string;         // Hashed secret
  keyPrefix: string;       // First 8 chars for identification
  name: string;
  userId: string;
  agencyId: string;
  scopes: string[];        // Permissions
  rateLimit: number;       // Requests per minute
  expiresAt?: Date;
  lastUsedAt?: Date;
  createdAt: Date;
  revokedAt?: Date;
}

export class ApiKeyService {
  // Generate new API key
  async createApiKey(
    userId: string,
    name: string,
    options: {
      scopes?: string[];
      rateLimit?: number;
      expiresAt?: Date;
    } = {}
  ): Promise<{ apiKey: string; keyId: string }> {
    const user = await UserRepository.findById(userId);
    const agencyId = user!.agencyId;

    // Generate cryptographically random key
    const keyBytes = crypto.randomBytes(32);
    const apiKey = `taa_${keyBytes.toString('base64url')}`;

    // Extract parts for storage
    const keyPrefix = apiKey.slice(0, 12); // taa_xxxxxxxx
    const keyHash = crypto.createHash('sha256').update(apiKey).digest('hex');
    const keyId = crypto.randomBytes(8).toString('hex');

    // Store hashed key
    await ApiKeyRepository.create({
      keyId,
      keyHash,
      keyPrefix,
      name,
      userId,
      agencyId,
      scopes: options.scopes || ['read:trips', 'read:customers'],
      rateLimit: options.rateLimit || 100,
      expiresAt: options.expiresAt,
      createdAt: new Date(),
    });

    // Return full key (only time it's shown)
    return { apiKey, keyId };
  }

  // Verify API key
  async verifyApiKey(apiKey: string): Promise<ApiKeyVerification | null> {
    // Format check
    if (!apiKey.startsWith('taa_')) {
      return null;
    }

    const keyHash = crypto.createHash('sha256').update(apiKey).digest('hex');

    const keyRecord = await ApiKeyRepository.findByHash(keyHash);
    if (!keyRecord) {
      return null;
    }

    // Check if revoked
    if (keyRecord.revokedAt) {
      return null;
    }

    // Check if expired
    if (keyRecord.expiresAt && keyRecord.expiresAt < new Date()) {
      return null;
    }

    // Update last used
    await ApiKeyRepository.update(keyRecord.id, {
      lastUsedAt: new Date(),
    });

    return {
      keyId: keyRecord.keyId,
      userId: keyRecord.userId,
      agencyId: keyRecord.agencyId,
      scopes: keyRecord.scopes,
      rateLimit: keyRecord.rateLimit,
    };
  }

  // Revoke API key
  async revokeApiKey(keyId: string, userId: string): Promise<void> {
    const key = await ApiKeyRepository.findById(keyId);

    if (!key || key.userId !== userId) {
      throw new ValidationError('INVALID_KEY', 'API key not found');
    }

    await ApiKeyRepository.update(keyId, {
      revokedAt: new Date(),
    });
  }

  // List user's API keys
  async listApiKeys(userId: string): Promise<ApiKeyInfo[]> {
    const keys = await ApiKeyRepository.findByUser(userId);

    return keys.map((key) => ({
      keyId: key.keyId,
      keyPrefix: key.keyPrefix,
      name: key.name,
      scopes: key.scopes,
      rateLimit: key.rateLimit,
      expiresAt: key.expiresAt,
      lastUsedAt: key.lastUsedAt,
      createdAt: key.createdAt,
    }));
  }
}

interface ApiKeyVerification {
  keyId: string;
  userId: string;
  agencyId: string;
  scopes: string[];
  rateLimit: number;
}

interface ApiKeyInfo {
  keyId: string;
  keyPrefix: string;
  name: string;
  scopes: string[];
  rateLimit: number;
  expiresAt?: Date;
  lastUsedAt?: Date;
  createdAt: Date;
}
```

### API Key Authentication Middleware

```typescript
export const apiKeyAuth = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  // Skip if already authenticated via JWT
  if (req.user) return next();

  // Extract API key from header
  const authHeader = req.headers['x-api-key'];
  if (!authHeader) {
    return res.status(401).json({ error: 'API_KEY_REQUIRED' });
  }

  // Verify key
  const verification = await apiKeyService.verifyApiKey(authHeader);
  if (!verification) {
    return res.status(401).json({ error: 'INVALID_API_KEY' });
  }

  // Check rate limit
  const rateLimitKey = `api_key:${verification.keyId}`;
  const currentUsage = await redis.incr(rateLimitKey);

  if (currentUsage === 1) {
    await redis.expire(rateLimitKey, 60); // 1 minute window
  }

  if (currentUsage > verification.rateLimit) {
    return res.status(429).json({
      error: 'RATE_LIMIT_EXCEEDED',
      message: `Rate limit of ${verification.rateLimit} requests per minute exceeded`,
    });
  }

  // Attach user to request
  const user = await UserRepository.findById(verification.userId);
  req.user = {
    id: user!.id,
    agencyId: user!.agencyId,
    role: user!.role,
    permissions: verification.scopes as Permission[],
    sessionId: verification.keyId,
    isApiKey: true,
  };

  next();
};
```

---

## Database Security

### Row-Level Security

```sql
-- PostgreSQL Row-Level Security (RLS)
-- Each agency can only see their own data

ALTER TABLE trips ENABLE ROW LEVEL SECURITY;

-- Policy: Agencies can only see their own trips
CREATE POLICY agency_isolation_trips ON trips
  FOR ALL
  USING (agency_id = current_setting('app.current_agency_id')::uuid);

-- Policy: Super admins can see all trips
CREATE POLICY super_admin_all_trips ON trips
  FOR ALL
  TO super_admin_role
  USING (true);

-- Function to set agency context
CREATE OR REPLACE FUNCTION set_agency_context(user_id UUID)
RETURNS void AS $$
  DECLARE
    user_agency_id UUID;
  BEGIN
    SELECT agency_id INTO user_agency_id
    FROM users
    WHERE id = user_id;

    PERFORM set_config('app.current_agency_id', user_agency_id::text, true);
  END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Usage in application
await db.query('SELECT set_agency_context($1)', [userId]);
const trips = await db.query('SELECT * FROM trips'); -- Automatically filtered
```

### Database Connection Security

```typescript
// Secure connection pooling with PgBouncer style config
import { Pool } from 'pg';

export const createSecurePool = (): Pool => {
  return new Pool({
    connectionString: process.env.DATABASE_URL,
    // SSL configuration
    ssl: process.env.NODE_ENV === 'production'
      ? {
          rejectUnauthorized: true,
          ca: fs.readFileSync(process.env.DATABASE_CA_PATH!).toString(),
        }
      : undefined,

    // Connection limits
    max: process.env.DATABASE_POOL_SIZE
      ? parseInt(process.env.DATABASE_POOL_SIZE)
      : 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,

    // Statement timeout (prevent long-running queries)
    statement_timeout: 30000,

    // Query timeout
    query_timeout: 30000,
  });
};

// Database query audit logging
export class AuditedPool {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  async query(text: string, params?: any[]): Promise<any> {
    const start = Date.now();

    try {
      const result = await this.pool.query(text, params);
      const duration = Date.now() - start;

      // Log slow queries
      if (duration > 1000) {
        await this.logSlowQuery(text, params, duration);
      }

      // Log sensitive queries
      if (this.isSensitiveQuery(text)) {
        await this.logSensitiveQuery(text, params);
      }

      return result;
    } catch (error) {
      await this.logQueryError(text, params, error);
      throw error;
    }
  }

  private isSensitiveQuery(text: string): boolean {
    const sensitive = [
      'SELECT.*passport',
      'SELECT.*pan',
      'SELECT.*card',
      'SELECT.*bank',
    ];

    return sensitive.some((pattern) =>
      new RegExp(pattern, 'i').test(text)
    );
  }

  private async logSlowQuery(text: string, params: any[], duration: number): Promise<void> {
    await AuditLogRepository.create({
      type: 'slow_query',
      query: text.substring(0, 500),
      duration,
      timestamp: new Date(),
    });
  }

  private async logSensitiveQuery(text: string, params: any[]): Promise<void> {
    await AuditLogRepository.create({
      type: 'sensitive_query',
      query: text.substring(0, 500),
      timestamp: new Date(),
    });
  }

  private async logQueryError(text: string, params: any[], error: any): Promise<void> {
    await AuditLogRepository.create({
      type: 'query_error',
      query: text.substring(0, 500),
      error: error.message,
      timestamp: new Date(),
    });
  }
}
```

---

## Data Retention and Deletion

### Retention Policy

```typescript
interface RetentionPolicy {
  resource: string;
  retentionPeriod: string; // e.g., "7 years", "90 days"
  after: 'archive' | 'delete' | 'anonymize';
  conditions?: string[];
}

export const RETENTION_POLICIES: RetentionPolicy[] = [
  {
    resource: 'trips',
    retentionPeriod: '7 years',
    after: 'archive',
    conditions: ['is_completed = true'],
  },
  {
    resource: 'quotes',
    retentionPeriod: '3 years',
    after: 'delete',
  },
  {
    resource: 'payment_records',
    retentionPeriod: '8 years', // Legal requirement
    after: 'delete',
  },
  {
    resource: 'customers',
    retentionPeriod: '7 years after last interaction',
    after: 'anonymize',
  },
  {
    resource: 'audit_logs',
    retentionPeriod: '2 years',
    after: 'archive',
  },
  {
    resource: 'api_logs',
    retentionPeriod: '90 days',
    after: 'delete',
  },
];
```

### Data Deletion Service

```typescript
export class DataDeletionService {
  // Soft delete (mark as deleted)
  async softDelete(resource: string, id: string): Promise<void> {
    await db.query(`
      UPDATE ${resource}
      SET deleted_at = NOW(),
          deleted_reason = 'user_request'
      WHERE id = $1
    `, [id]);
  }

  // Hard delete (actually remove)
  async hardDelete(resource: string, id: string): Promise<void> {
    // Verify permissions
    // Log deletion
    await AuditLogRepository.create({
      type: 'hard_delete',
      resource,
      resourceId: id,
      timestamp: new Date(),
    });

    await db.query(`DELETE FROM ${resource} WHERE id = $1`, [id]);
  }

  // Anonymize data (GDPR right to be forgotten)
  async anonymizeCustomer(customerId: string): Promise<void> {
    await db.transaction(async (trx) => {
      // Anonymize customer record
      await trx.query(`
        UPDATE customers
        SET name = 'Deleted Customer',
            email = 'deleted-' || id || '@anonymized.local',
            phone = NULL,
            passport_number = NULL,
            pan_number = NULL,
            address = NULL,
            date_of_birth = NULL,
            anonymized_at = NOW()
        WHERE id = $1
      `, [customerId]);

      // Anonymize related trips
      await trx.query(`
        UPDATE trips
        SET customer_name = 'Deleted Customer'
        WHERE customer_id = $1
      `, [customerId]);

      // Log anonymization
      await AuditLogRepository.create({
        type: 'customer_anonymized',
        customerId,
        timestamp: new Date(),
      }, trx);
    });
  }

  // Data retention job
  async processRetentionPolicies(): Promise<void> {
    const results = {
      archived: 0,
      deleted: 0,
      anonymized: 0,
    };

    for (const policy of RETENTION_POLICIES) {
      const cutoffDate = this.calculateCutoffDate(policy.retentionPeriod);

      switch (policy.after) {
        case 'archive':
          results.archived += await this.archiveData(policy, cutoffDate);
          break;

        case 'delete':
          results.deleted += await.deleteOldData(policy, cutoffDate);
          break;

        case 'anonymize':
          results.anonymized += await this.anonymizeData(policy, cutoffDate);
          break;
      }
    }

    return results;
  }

  private calculateCutoffDate(period: string): Date {
    const match = period.match(/(\d+)\s+(year|month|day|hour|week)s?/);
    if (!match) return new Date();

    const [, amount, unit] = match;
    const now = new Date();

    switch (unit) {
      case 'year':
        return new Date(now.getFullYear() - parseInt(amount), now.getMonth(), now.getDate());
      case 'month':
        return new Date(now.getFullYear(), now.getMonth() - parseInt(amount), now.getDate());
      case 'week':
        return new Date(now.getTime() - parseInt(amount) * 7 * 24 * 60 * 60 * 1000);
      case 'day':
        return new Date(now.getTime() - parseInt(amount) * 24 * 60 * 60 * 1000);
      case 'hour':
        return new Date(now.getTime() - parseInt(amount) * 60 * 60 * 1000);
      default:
        return now;
    }
  }

  private async archiveData(policy: RetentionPolicy, cutoffDate: Date): Promise<number> {
    // Move to cold storage (S3 Glacier, etc.)
    const records = await db.query(`
      SELECT * FROM ${policy.resource}
      WHERE created_at < $1
      ${policy.conditions ? `AND ${policy.conditions.join(' AND ')}` : ''}
    `, [cutoffDate]);

    for (const record of records) {
      await coldStorage.archive(policy.resource, record.id, record);
    }

    // Delete from main database
    const result = await db.query(`
      DELETE FROM ${policy.resource}
      WHERE created_at < $1
      ${policy.conditions ? `AND ${policy.conditions.join(' AND ')}` : ''}
    `, [cutoffDate]);

    return result.rowCount || 0;
  }

  private async deleteOldData(policy: RetentionPolicy, cutoffDate: Date): Promise<number> {
    const result = await db.query(`
      DELETE FROM ${policy.resource}
      WHERE created_at < $1
      ${policy.conditions ? `AND ${policy.conditions.join(' AND ')}` : ''}
    `, [cutoffDate]);

    return result.rowCount || 0;
  }

  private async anonymizeData(policy: RetentionPolicy, cutoffDate: Date): Promise<number> {
    // Implementation depends on resource
    if (policy.resource === 'customers') {
      const result = await db.query(`
        UPDATE customers
        SET name = 'Anonymized',
            email = 'anonymized-' || id || '@local',
            phone = NULL,
            address = NULL,
            anonymized_at = NOW()
        WHERE last_interaction_at < $1
      `, [cutoffDate]);

      return result.rowCount || 0;
    }

    return 0;
  }
}
```

### Right to be Forgotten

```typescript
export class GdprService {
  // Handle GDPR data deletion request
  async handleDeletionRequest(
    customerId: string,
    requestId: string
  ): Promise<void> {
    // Verify request is legitimate
    const request = await GdprRequestRepository.findById(requestId);
    if (!request || request.customerId !== customerId) {
      throw new ValidationError('INVALID_REQUEST', 'Invalid deletion request');
    }

    // Check if request is verified (email confirmation)
    if (!request.verifiedAt) {
      throw new ValidationError('REQUEST_NOT_VERIFIED', 'Request not verified');
    }

    // Start deletion process
    await dataDeletionService.anonymizeCustomer(customerId);

    // Update request status
    await GdprRequestRepository.update(requestId, {
      status: 'completed',
      completedAt: new Date(),
    });

    // Send confirmation
    await emailService.send({
      to: request.email,
      subject: 'Your data has been deleted',
      template: 'gdpr-deletion-complete',
    });
  }

  // Export all customer data (GDPR right to data portability)
  async exportCustomerData(customerId: string): Promise<Buffer> {
    const data = await this.collectCustomerData(customerId);

    // Generate JSON export
    const json = JSON.stringify(data, null, 2);

    // Log export
    await piiAuditLogger.logExport(
      customerId,
      'customer',
      1,
      { ip: 'system', userAgent: 'gdpr_export' }
    );

    return Buffer.from(json);
  }

  private async collectCustomerData(customerId: string): Promise<any> {
    const [customer, trips, bookings, payments, documents] = await Promise.all([
      CustomerRepository.findById(customerId),
      TripRepository.findByCustomerId(customerId),
      BookingRepository.findByCustomerId(customerId),
      PaymentRepository.findByCustomerId(customerId),
      DocumentRepository.findByCustomerId(customerId),
    ]);

    return {
      customer: dataMaskingService.maskObject(
        customer!,
        PII_SCHEMA.customers,
        'super_admin' // Full export for GDPR
      ),
      trips,
      bookings,
      payments: payments.map((p) => ({
        ...p,
        // Never include full card details in export
        cardNumber: dataMaskingService.mask(p.cardNumber, 'card'),
      })),
      documents: documents.map((d) => ({
        ...d,
        // Include document metadata, not files
        storageKey: d.storageKey,
      })),
      exportDate: new Date().toISOString(),
    };
  }
}
```

---

**Last Updated:** 2026-04-25

**Next:** SECURITY_04 — Audit Deep Dive (Logging, monitoring, incident response)
