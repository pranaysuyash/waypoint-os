# Payment Processing — Compliance Deep Dive

> PCI DSS compliance, RBI regulations, data security, and fraud prevention

---

## Document Overview

**Series:** Payment Processing Deep Dive
**Document:** 3 of 4
**Last Updated:** 2026-04-25
**Status:** ✅ Complete

**Related Documents:**
- [Technical Deep Dive](./PAYMENT_PROCESSING_01_TECHNICAL_DEEP_DIVE.md) — Architecture, gateways
- [UX/UI Deep Dive](./PAYMENT_PROCESSING_02_UX_UI_DEEP_DIVE.md) — Payment flow design
- [Reconciliation Deep Dive](./PAYMENT_PROCESSING_04_RECONCILIATION_DEEP_DIVE.md) — Accounting, settlements

---

## Table of Contents

1. [Regulatory Framework](#regulatory-framework)
2. [PCI DSS Compliance](#pci-dss-compliance)
3. [RBI Guidelines](#rbi-guidelines)
4. [Data Security](#data-security)
5. [Tokenization](#tokenization)
6. [Fraud Prevention](#fraud-prevention)
7. [Audit & Logging](#audit--logging)

---

## Regulatory Framework

### Compliance Landscape

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PAYMENT COMPLIANCE FRAMEWORK                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  GLOBAL STANDARDS                                                    │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │    │
│  │  │   PCI DSS       │  │  GDPR           │  │  ISO 27001      │       │    │
│  │  │  (Card Data)    │  │  (EU Privacy)   │  │  (Security)     │       │    │
│  │  │  Level 2/3      │  │                 │  │                 │       │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  INDIA-SPECIFIC                                                      │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │    │
│  │  │   RBI Master    │  │  RBI Payment    │  │  DPDP Act 2023  │       │    │
│  │  │   Direction     │  │  Security       │  │  (Privacy)      │       │    │
│  │  │   (2021)        │  │  Guidelines     │  │                 │       │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  OPERATIONAL CONTROLS                                               │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │    │
│  │  │  Data           │  │  Access         │  │  Incident       │       │    │
│  │  │  Retention      │  │  Control        │  │  Response       │       │    │
│  │  │  Policies       │  │  (RBAC)         │  │  Plan            │       │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Compliance Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COMPLIANCE CHECKLIST                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PCI DSS REQUIREMENTS                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Never store CVV/CVC codes                                        │   │
│  │  ☐ Never store full PAN (track data)                                │   │
│  │  ☐ Use tokenization for card storage                                │   │
│  │  ☐ Encrypt data in transit (TLS 1.2+)                               │   │
│  │  ☐ Encrypt data at rest (AES-256)                                   │   │
│  │  ☐ Maintain vulnerability management program                        │   │
│  │  ☐ Implement access controls (least privilege)                      │   │
│  │  ☐ Regular security testing                                         │   │
│  │  ☐ Maintain information security policy                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RBI GUIDELINES                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Card tokenization mandatory for recurring payments               │   │
│  │  ☐ No storage of CVV/CVC                                            │   │
│  │  ☐ Secure authentication for card transactions                       │   │
│  │  ☐ Compliance with SOX (for listed entities)                        │   │
│  │  ☐ Regular security audits                                          │   │
│  │  ☐ Fraud monitoring and reporting                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATA PRIVACY (DPDP Act 2023)                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Clear consent for payment data collection                       │   │
│  │  ☐ Data minimization (collect only required)                       │   │
│  │  ☐ Right to erasure for payment data                               │   │
│  │  ☐ Data localization (India)                                       │   │
│  │  ☐ Breach notification within 72 hours                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PCI DSS Compliance

### PCI DSS Applicability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PCI DSS LEVEL DETERMINATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Transaction Volume determines validation level:                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Level 1: > 6M transactions/year                                    │   │
│  │          → Annual ROC by QSA                                        │   │
│  │          → Network scan by ASV                                      │   │
│  │                                                                   │   │
│  │  Level 2: 1M - 6M transactions/year                                │   │
│  │          → Annual SAQ (Self-Assessment Questionnaire)              │   │
│  │          → Quarterly network scan by ASV                           │   │
│  │                                                                   │   │
│  │  Level 3: 20K - 1M e-commerce transactions/year                    │   │
│  │          → Annual SAQ                                              │   │
│  │                                                                   │   │
│  │  Level 4: < 20K e-commerce transactions/year                       │   │
│  │          → Annual SAQ                                              │   │
│  │          → Recommended network scan                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Our Status: Level 4 (Start) → Level 3 as we scale                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PCI Data Handling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PCI DSS DATA HANDLING RULES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CARDHOLDER DATA (CHD)                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Data Element              │ Storage Allowed │ Display Allowed    │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  Primary Account Number    │ Token only     │ Last 4 digits only  │   │
│  │  (PAN)                    │                │                      │   │
│  │                           │                │                      │   │
│  │  Cardholder Name          │ Token only     │ Full name            │   │
│  │                           │                │                      │   │
│  │  Expiration Date          │ Token only     │ MM/YY               │   │
│  │                           │                │                      │   │
│  │  Service Code              │ Never          │ Never                │   │
│  │  (CVV/CVC)                │                │                      │   │
│  │                           │                │                      │   │
│  │  Full Track Data          │ Never          │ Never                │   │
│  │  (Magnetic stripe)        │                │                      │   │
│  │                           │                │                      │   │
│  │  PIN/PIN Block            │ Never          │ Never                │   │
│  │                           │                │                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SENSITIVE AUTHENTICATION DATA (SAD)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Full track data from magnetic stripe or chip                     │   │
│  │  • CAV2/CVC2/CID (card verification codes/values)                   │   │
│  │  • PINs/PIN blocks                                                  │   │
│  │                                                                     │   │
│  │  RULE: Never store SAD after authorization                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PCI Compliance Implementation

```typescript
/**
 * PCI DSS compliance utilities
 */

/**
 * Mask PAN for display (show first 6 and last 4)
 * PCI DSS allows display of first 6/major industry identifier + last 4
 */
function maskPAN(pan: string): string {
  if (!pan || pan.length < 10) return '****';
  return `${pan.substring(0, 6)}${'*'.repeat(pan.length - 10)}${pan.substring(pan.length - 4)}`;
}

/**
 * Mask PAN for logs (show last 4 only)
 * More restrictive for security
 */
function maskPANForLogs(pan: string): string {
  if (!pan || pan.length < 4) return '****';
  return `****${pan.substring(pan.length - 4)}`;
}

/**
 * Validate that we're not storing prohibited data
 */
function validateCardData(data: CardData): ValidationResult {
  const errors: string[] = [];

  // Never store CVV
  if (data.cvv) {
    errors.push('CVV must never be stored');
  }

  // Never store full track data
  if (data.trackData) {
    errors.push('Track data must never be stored');
  }

  // Never store PIN
  if (data.pin) {
    errors.push('PIN must never be stored');
  }

  // PAN must be tokenized
  if (data.pan && !isToken(data.pan)) {
    errors.push('PAN must be tokenized before storage');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Check if value is a token (not real PAN)
 */
function isToken(value: string): boolean {
  // Our tokens start with specific prefixes
  return value.startsWith('tok_') || value.startsWith('card_');
}

/**
 * Card data interface (what we CAN store)
 */
interface CardData {
  // Token (from gateway)
  token: string;

  // Display data (allowed)
  last4: string;
  brand: string;
  holderName?: string;
  expiryMonth?: number;
  expiryYear?: number;

  // Prohibited data (for validation only)
  cvv?: never;
  trackData?: never;
  pin?: never;
  pan?: never;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Payment gateway handles actual card data
 * We only receive and store tokens
 */
interface GatewayTokenResponse {
  id: string;              // Token ID (e.g., card_abc123)
  entity: 'card';
  name: string;            // Cardholder name
  last4: string;           // Last 4 digits
  network: string;         // Brand (Visa, Mastercard)
  expiry_month: number;
  expiry_year: number;
  // No CVV, no full PAN
}

/**
 * Convert gateway token to our stored format
 */
function toStoredCardData(response: GatewayTokenResponse): CardData {
  return {
    token: response.id,
    last4: response.last4,
    brand: response.network,
    holderName: response.name,
    expiryMonth: response.expiry_month,
    expiryYear: response.expiry_year
  };
}
```

### PCI Compliance Controls

```typescript
/**
 * PCI compliance middleware
 */

/**
 * Request interceptor - strip card data before logging
 */
export function pciComplianceLogger(
  logger: winston.Logger
): winston.Logger {
  return logger.child({
    transformer: (logData: any) => {
      // Deep scan and mask card data
      return sanitizeLogData(logData);
    }
  });
}

/**
 * Sanitize log data for PCI compliance
 */
function sanitizeLogData(obj: any): any {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(sanitizeLogData);
  }

  const sanitized: any = {};

  for (const [key, value] of Object.entries(obj)) {
    // Check for card data patterns
    const lowerKey = key.toLowerCase();

    if (PROHIBITED_KEYS.includes(lowerKey)) {
      // Skip entirely
      continue;
    }

    if (CARD_DATA_KEYS.includes(lowerKey)) {
      // Mask appropriately
      sanitized[key] = maskSensitiveValue(lowerKey, value as string);
      continue;
    }

    // Recurse into nested objects
    sanitized[key] = sanitizeLogData(value);
  }

  return sanitized;
}

const PROHIBITED_KEYS = [
  'cvv', 'cvc', 'cid', 'cvv2', 'cvc2',
  'pin', 'pinblock', 'pin_block',
  'trackdata', 'track_data', 'magnetic_stripe',
  'securecode', 'security_code'
];

const CARD_DATA_KEYS = [
  'cardnumber', 'card_number', 'pan', 'accountnumber',
  'card', 'paymentmethod'
];

function maskSensitiveValue(key: string, value: string): string {
  if (!value) return '';

  // PAN pattern (14-19 digits)
  if (/^\d{14,19}$/.test(value)) {
    return maskPANForLogs(value);
  }

  // Already masked
  if (value.includes('*')) {
    return value;
  }

  // Other sensitive - mask all but last 4
  if (value.length > 4) {
    return '****' + value.substring(value.length - 4);
  }

  return '****';
}

/**
 * Response interceptor - ensure no card data leaks
 */
export function pciComponseResponseInterceptor() {
  return (response: any): any => {
    // Remove any accidental card data from response
    // This is defense in depth
    return sanitizeLogData(response);
  };
}

/**
 * File upload scanner for card data
 */
export async function scanForCardData(file: File): Promise<boolean> {
  const text = await file.text();

  // Scan for potential PAN patterns
  const panPatterns = [
    /\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b/g, // Visa, MC, Amex, Discover
    /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g // Generic 16-digit
  ];

  for (const pattern of panPatterns) {
    const matches = text.match(pattern);
    if (matches && matches.length > 0) {
      // Verify these are likely card numbers (Luhn check)
      for (const match of matches) {
        const digits = match.replace(/\D/g, '');
        if (luhnCheck(digits)) {
          logger.warn('Potential card data found in upload', {
            file: file.name,
            matches: matches.length
          });
          return true;
        }
      }
    }
  }

  return false;
}

/**
 * Luhn algorithm for card number validation
 */
function luhnCheck(cardNumber: string): boolean {
  let sum = 0;
  let isEven = false;

  for (let i = cardNumber.length - 1; i >= 0; i--) {
    let digit = parseInt(cardNumber[i], 10);

    if (isEven) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }

    sum += digit;
    isEven = !isEven;
  }

  return sum % 10 === 0;
}
```

---

## RBI Guidelines

### RBI Payment Security Guidelines

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RBI PAYMENT SECURITY GUIDELINES                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MASTER DIRECTION – PAYMENT SECURITY CONTROLS (2021)                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  1. TOKENIZATION OF CARD TRANSACTIONS                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Tokenization mandatory for all card transactions                  │   │
│  │  • Token reference must not be valid PAN                            │   │
│  │  • Token requestor must be certified                                │   │
│  │  • Token can be used at any merchant                                 │   │
│  │  • Cardholder consent required                                       │   │
│  │  • Token must be mapped to original PAN at issuer                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. CARD DATA STORAGE                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • CVV/CVC must not be stored                                       │   │
│  │  • PIN must not be stored                                          │   │
│  │  • Sensitive data must be encrypted                                │   │
│  │  • Encryption key management controls                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. TRANSACTION AUTHENTICATION                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Two-factor authentication for card transactions                  │   │
│  │  • OTP-based authentication for internet banking                    │   │
│  │  • Secure encryption for data transmission                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. FRAUD MONITORING                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Real-time fraud monitoring system                               │   │
│  │  • Transaction velocity checks                                     │   │
│  │  • Device fingerprinting                                           │   │
│  │  • Geolocation validation                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  5. SECURITY TESTING                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Annual security audit by certified auditor                      │   │
│  │  • Penetration testing at least annually                           │   │
│  │  • Vulnerability assessment quarterly                              │   │
│  │  • Compliance with ISO 27001                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RBI Compliance Implementation

```typescript
/**
 * RBI compliance utilities
 */

/**
 * Tokenization service wrapper
 * Ensures all card data is tokenized per RBI guidelines
 */
class RBITokenizationService {
  constructor(
    private gateway: PaymentGatewayAdapter,
    private auditLog: AuditLogger
  ) {}

  /**
   * Tokenize card for recurring payments
   * Requires explicit customer consent
   */
  async tokenizeCard(
    cardDetails: CardDetails,
    consent: TokenizationConsent,
    customerId: string
  ): Promise<TokenizedCard> {
    // Validate consent
    if (!consent.given || !consent.timestamp) {
      throw new ConsentRequiredError('Customer consent required for tokenization');
    }

    // Check consent is recent (within 30 days)
    const consentAge = Date.now() - consent.timestamp.getTime();
    if (consentAge > 30 * 24 * 60 * 60 * 1000) {
      throw new ExpiredConsentError('Consent expired. Please obtain fresh consent.');
    }

    // Log tokenization request
    await this.auditLog.log({
      event: 'TOKENIZATION_REQUEST',
      customerId,
      consentGiven: consent.given,
      consentTimestamp: consent.timestamp,
      ipAddress: consent.ipAddress
    });

    try {
      // Call gateway tokenization endpoint
      const token = await this.gateway.tokenizeCard({
        card_number: cardDetails.cardNumber,
        card_holder_name: cardDetails.holderName,
        card_expiry: `${cardDetails.expiryMonth}${cardDetails.expiryYear}`,
        customer_id: customerId,
        consent: {
          agreed: true,
          agreed_at: Math.floor(consent.timestamp.getTime() / 1000)
        }
      });

      // Log successful tokenization
      await this.auditLog.log({
        event: 'TOKENIZATION_SUCCESS',
        customerId,
        tokenId: token.id,
        last4: token.last4,
        brand: token.brand
      });

      return {
        token: token.id,
        last4: token.last4,
        brand: token.brand,
        expiryMonth: token.expiry_month,
        expiryYear: token.expiry_year,
        tokenizedAt: new Date()
      };

    } catch (error) {
      await this.auditLog.log({
        event: 'TOKENIZATION_FAILED',
        customerId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * Detokenize (for refunds/disputes only)
   * Restricted access, audit logged
   */
  async detokenizeCard(
    tokenId: string,
    reason: 'refund' | 'dispute' | 'chargeback',
    requesterId: string,
    requesterRole: string
  ): Promise<CardInfo> {
    // Verify authorization
    if (!this.isAuthorizedForDetokenization(requesterRole)) {
      throw new UnauthorizedError('Not authorized for detokenization');
    }

    // Log detokenization request
    await this.auditLog.log({
      event: 'DETOKENIZATION_REQUEST',
      tokenId,
      reason,
      requesterId,
      requesterRole
    });

    try {
      const cardInfo = await this.gateway.getCardInfo(tokenId);

      await this.auditLog.log({
        event: 'DETOKENIZATION_SUCCESS',
        tokenId,
        reason,
        requesterId
      });

      return cardInfo;

    } catch (error) {
      await this.auditLog.log({
        event: 'DETOKENIZATION_FAILED',
        tokenId,
        reason,
        requesterId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  private isAuthorizedForDetokenization(role: string): boolean {
    return ['admin', 'finance', 'support_lead'].includes(role);
  }
}

interface TokenizationConsent {
  given: boolean;
  timestamp: Date;
  ipAddress: string;
  method: 'checkbox' | 'signature' | 'clickwrap';
}

interface TokenizedCard {
  token: string;
  last4: string;
  brand: string;
  expiryMonth: number;
  expiryYear: number;
  tokenizedAt: Date;
}

interface CardDetails {
  cardNumber: string;
  holderName: string;
  expiryMonth: number;
  expiryYear: number;
}

interface CardInfo {
  last4: string;
  brand: string;
  holderName: string;
  expiryMonth: number;
  expiryYear: number;
}
```

---

## Data Security

### Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PAYMENT DATA SECURITY ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CLIENT BROWSER                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Card data entered on gateway hosted page                         │   │
│  │  • No card data touches our servers                                  │   │
│  │  • HTTPS/TLS 1.3 enforced                                           │   │
│  │  • CSP headers prevent XSS                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  API LAYER                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Request validation                                               │   │
│  │  • Rate limiting                                                   │   │
│  │  • IP whitelisting for webhooks                                     │   │
│  │  • Request signing verification                                     │   │
│  │  • Card data sanitization                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  APPLICATION LAYER                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Token storage only (never raw PAN)                               │   │
│  │  • Encryption at rest (AES-256-GCM)                                 │   │
│  │  • Database access controls (least privilege)                       │   │
│  │  • Application-level encryption for sensitive fields                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  GATEWAY INTEGRATION                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • API keys stored in secrets manager                               │   │
│  │  • Webhook signature verification                                   │   │
│  │  • IP whitelisting                                                  │   │
│  │  • Mutual TLS for sensitive operations                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  INFRASTRUCTURE                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • VPC isolation                                                   │   │
│  │  • Security groups (least access)                                  │   │
│  │  • KMS for encryption keys                                         │   │
│  │  • Secrets manager for credentials                                 │   │
│  │  • Audit logging (CloudTrail, etc.)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Encryption Configuration

```typescript
/**
 * Encryption service for sensitive payment data
 */
import crypto from 'crypto';

class PaymentEncryptionService {
  private readonly algorithm = 'aes-256-gcm';
  private readonly keyLength = 32; // 256 bits
  private readonly ivLength = 16;
  private readonly saltLength = 32;
  private readonly tagLength = 16;

  constructor(
    private kms: KMSClient,
    private keyId: string
  ) {}

  /**
   * Encrypt sensitive payment data
   * Uses envelope encryption (KMS + AES)
   */
  async encrypt(data: string): Promise<EncryptedData> {
    // Generate data key from KMS
    const dataKey = await this.generateDataKey();

    // Generate random IV
    const iv = crypto.randomBytes(this.ivLength);

    // Create cipher
    const cipher = crypto.createCipheriv(
      this.algorithm,
      dataKey.plaintext,
      iv
    );

    // Encrypt data
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    // Get auth tag
    const tag = cipher.getAuthTag();

    return {
      ciphertext: encrypted,
      iv: iv.toString('hex'),
      tag: tag.toString('hex'),
      encryptedKey: dataKey.ciphertext,
      keyId: this.keyId
    };
  }

  /**
   * Decrypt sensitive payment data
   */
  async decrypt(encryptedData: EncryptedData): Promise<string> {
    // Decrypt data key from KMS
    const dataKey = await this.decryptDataKey(encryptedData.encryptedKey);

    // Create decipher
    const decipher = crypto.createDecipheriv(
      this.algorithm,
      dataKey,
      Buffer.from(encryptedData.iv, 'hex')
    );

    // Set auth tag
    decipher.setAuthTag(Buffer.from(encryptedData.tag, 'hex'));

    // Decrypt data
    let decrypted = decipher.update(encryptedData.ciphertext, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }

  /**
   * Generate data key from KMS
   */
  private async generateDataKey(): Promise<DataKey> {
    const response = await this.kms.generateDataKey({
      KeyId: this.keyId,
      KeySpec: 'AES_256'
    });

    return {
      plaintext: response.Plaintext as Uint8Array,
      ciphertext: response.CiphertextKeyBlob?.toString('hex') || ''
    };
  }

  /**
   * Decrypt data key from KMS
   */
  private async decryptDataKey(encryptedKey: string): Promise<Buffer> {
    const response = await this.kms.decrypt({
      CiphertextBlob: Buffer.from(encryptedKey, 'hex'),
      KeyId: this.keyId
    });

    return Buffer.from(response.Plaintext as Uint8Array);
  }

  /**
   * Encrypt payment token for storage
   */
  async encryptToken(token: string): Promise<string> {
    const encrypted = await this.encrypt(token);
    return JSON.stringify(encrypted);
  }

  /**
   * Decrypt payment token for use
   */
  async decryptToken(encryptedToken: string): Promise<string> {
    const encrypted: EncryptedData = JSON.parse(encryptedToken);
    return await this.decrypt(encrypted);
  }
}

interface EncryptedData {
  ciphertext: string;
  iv: string;
  tag: string;
  encryptedKey: string;
  keyId: string;
}

interface DataKey {
  plaintext: Uint8Array;
  ciphertext: string;
}
```

### Access Control

```typescript
/**
 * Payment data access control
 */
class PaymentAccessControl {
  constructor(
    private rbac: RBACService,
    private auditLog: AuditLogger
  ) {}

  /**
   * Check if user can access payment data
   */
  async canAccessPaymentData(
    userId: string,
    paymentId: string,
    operation: 'read' | 'write' | 'delete'
  ): Promise<boolean> {
    // Get user roles
    const roles = await this.rbac.getUserRoles(userId);

    // Check role-based permissions
    const hasPermission = await this.rbac.checkPermission({
      roles,
      resource: 'payment_data',
      action: operation,
      context: { paymentId }
    });

    if (!hasPermission) {
      await this.auditLog.log({
        event: 'ACCESS_DENIED',
        userId,
        paymentId,
        operation,
        roles
      });
      return false;
    }

    // Check data ownership (agency-level isolation)
    const payment = await this.getPayment(paymentId);
    const userAgencies = await this.rbac.getUserAgencies(userId);

    if (!userAgencies.includes(payment.agencyId)) {
      await this.auditLog.log({
        event: 'ACCESS_DENIED_AGENCY',
        userId,
        paymentId,
        operation,
        userAgencies,
        paymentAgency: payment.agencyId
      });
      return false;
    }

    return true;
  }

  /**
   * Grant access with MFA for sensitive operations
   */
  async requireMFAForSensitiveAccess(
    userId: string,
    operation: string
  ): Promise<boolean> {
    const sensitiveOperations = [
      'view_full_card',
      'process_refund',
      'delete_payment',
      'export_payment_data'
    ];

    if (sensitiveOperations.includes(operation)) {
      // Require MFA verification
      return await this.rbac.verifyMFA(userId);
    }

    return true;
  }

  private async getPayment(paymentId: string): Promise<Payment> {
    // Implementation
    throw new Error('Not implemented');
  }
}
```

---

## Tokenization

### Token Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOKENIZATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FIRST PAYMENT                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Customer ──► Enters Card ──► Gateway ──► Token Generated ──► Us   │   │
│  │                             │                   │                     │   │
│  │                             ▼                   ▼                     │   │
│  │                        Card Processed      Token Stored             │   │
│  │                        (Payment Done)      (for reuse)              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SUBSEQUENT PAYMENTS (Saved Card)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Customer ──► Selects Saved Card ──► We Send Token ──► Gateway      │   │
│  │                                      │               │               │   │
│  │                                      ▼               ▼               │   │
│  │                                 CVV Required   Token → PAN          │   │
│  │                                 (Security)     (Internal)            │   │
│  │                                                      │              │   │
│  │                                                      ▼              │   │
│  │                                             Card Processed          │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TOKEN STRUCTURE                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Format: {gateway}_{customer_id}_{timestamp}_{random}               │   │
│  │  Example: razorpay_cus_abc123_1234567890_xyz321                    │   │
│  │                                                                     │   │
│  │  Properties:                                                        │   │
│  │  • Unique per customer-card combination                            │   │
│  │  • No card data embedded                                           │   │
│  │  • Cannot be reverse-engineered to PAN                             │   │
│  │  • Can be invalidated (detokenized)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Token Service

```typescript
/**
 * Token management service
 */
class TokenService {
  constructor(
    private gateway: PaymentGatewayAdapter,
    private store: TokenStore,
    private encryption: PaymentEncryptionService
  ) {}

  /**
   * Save card token after payment
   */
  async saveTokenFromPayment(
    gatewayPaymentId: string,
    customerId: string,
    label?: string,
    consent?: TokenizationConsent
  ): Promise<SavedCard> {
    // Get payment details from gateway
    const payment = await this.gateway.getPaymentStatus(gatewayPaymentId);

    if (!payment.card) {
      throw new Error('No card details in payment');
    }

    // Check if already saved
    const existing = await this.store.findByCardHash(
      customerId,
      this.hashCardData(payment.card)
    );

    if (existing) {
      return existing;
    }

    // Generate internal token
    const internalToken = this.generateInternalToken();

    // Encrypt gateway token
    const encryptedToken = await this.encryption.encryptToken(payment.methodId);

    // Save to database
    const savedCard: SavedCard = {
      id: internalToken,
      customerId,
      label: label || this.generateLabel(payment.card),
      last4: payment.card.last4,
      brand: payment.card.brand,
      expiryMonth: payment.card.expiryMonth,
      expiryYear: payment.card.expiryYear,
      gatewayToken: encryptedToken,
      cardHash: this.hashCardData(payment.card),
      isDefault: !(await this.store.hasDefaultCard(customerId)),
      createdAt: new Date(),
      consentGivenAt: consent?.timestamp
    };

    await this.store.create(savedCard);

    return savedCard;
  }

  /**
   * Get saved cards for customer
   */
  async getSavedCards(customerId: string): Promise<SavedCard[]> {
    const cards = await this.store.findByCustomer(customerId);

    // Return without exposing gateway tokens
    return cards.map(card => ({
      ...card,
      gatewayToken: undefined // Never expose
    }));
  }

  /**
   * Charge using saved card
   */
  async chargeSavedCard(
    cardId: string,
    amount: number,
    currency: string,
    cvv?: string
  ): Promise<PaymentResult> {
    // Get saved card
    const card = await this.store.get(cardId);

    if (!card) {
      throw new NotFoundError('Card not found');
    }

    // Decrypt gateway token
    const gatewayToken = await this.encryption.decryptToken(card.gatewayToken);

    // Charge via gateway
    return await this.gateway.chargeToken({
      token: gatewayToken,
      amount,
      currency,
      cvv // CVV required for card-on-file per RBI
    });
  }

  /**
   * Delete saved card
   */
  async deleteSavedCard(cardId: string, customerId: string): Promise<void> {
    const card = await this.store.get(cardId);

    if (!card || card.customerId !== customerId) {
      throw new NotFoundError('Card not found');
    }

    // Delete from our store
    await this.store.delete(cardId);

    // Optionally detokenize at gateway
    try {
      const gatewayToken = await this.encryption.decryptToken(card.gatewayToken);
      await this.gateway.detokenizeCard(gatewayToken);
    } catch (error) {
      logger.warn('Failed to detokenize at gateway', { cardId, error });
    }
  }

  /**
   * Generate internal token ID
   */
  private generateInternalToken(): string {
    return `card_${crypto.randomBytes(16).toString('hex')}`;
  }

  /**
   * Generate card label
   */
  private generateLabel(card: CardInfo): string {
    return `${card.brand} ending in ${card.last4}`;
  }

  /**
   * Hash card data for deduplication
   */
  private hashCardData(card: CardInfo): string {
    const data = `${card.brand}-${card.last4}-${card.expiryMonth}-${card.expiryYear}`;
    return crypto.createHash('sha256').update(data).digest('hex');
  }
}

interface SavedCard {
  id: string;
  customerId: string;
  label: string;
  last4: string;
  brand: string;
  expiryMonth: number;
  expiryYear: number;
  gatewayToken: string; // Encrypted
  cardHash: string;
  isDefault: boolean;
  createdAt: Date;
  consentGivenAt?: Date;
}
```

---

## Fraud Prevention

### Fraud Detection Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRAUD DETECTION RULES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VELOCITY CHECKS                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • More than 3 payment attempts in 5 minutes                        │   │
│  │  • More than 5 failed payments in 1 hour                           │   │
│  │  • Multiple cards from same IP/device                              │   │
│  │  • Same amount, different cards (card testing)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ANOMALY DETECTION                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Unusual location (IP geolocation mismatch)                      │   │
│  │  • Unusual time (transactions at odd hours)                         │   │
│  │  • Amount deviation (outside normal range)                         │   │
│  │  • New device fingerprint                                          │   │
│  │  • High-risk country/region                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BLACKLIST CHECKS                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Blacklisted IP addresses                                        │   │
│  │  • Blacklisted email domains                                      │   │
│  │  • Known stolen card numbers                                       │   │
│  │  • Previous fraud attempts                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RESPONSE TO FRAUD                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Block payment                                                   │   │
│  │  • Require additional verification (OTP, 3DS)                      │   │
│  │  • Flag for manual review                                          │   │
│  │  • Add to monitoring list                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fraud Detection Engine

```typescript
/**
 * Fraud detection engine
 */
class FraudDetectionEngine {
  private rules: FraudRule[] = [
    new VelocityCheckRule(),
    new LocationAnomalyRule(),
    new AmountAnomalyRule(),
    new BlacklistRule(),
    new CardTestingRule()
  ];

  constructor(
    private riskScoreStore: RiskScoreStore,
    private alertService: AlertService
  ) {}

  /**
   * Analyze payment for fraud
   */
  async analyzePayment(
    paymentRequest: PaymentRequest,
    context: PaymentContext
  ): Promise<FraudAnalysisResult> {
    const riskFactors: RiskFactor[] = [];
    let totalScore = 0;

    // Run all rules
    for (const rule of this.rules) {
      const result = await rule.evaluate(paymentRequest, context);

      if (result.isTriggered) {
        riskFactors.push({
          rule: rule.name,
          score: result.score,
          description: result.description,
          severity: result.severity
        });
        totalScore += result.score;
      }
    }

    // Determine overall risk level
    const riskLevel = this.calculateRiskLevel(totalScore);

    // Store risk score
    await this.riskScoreStore.record({
      paymentId: paymentRequest.id,
      customerId: context.customerId,
      totalScore,
      riskLevel,
      riskFactors,
      timestamp: new Date()
    });

    // Determine action
    const action = this.determineAction(riskLevel);

    // Alert if high risk
    if (riskLevel === 'HIGH' || riskLevel === 'CRITICAL') {
      await this.alertService.send({
        type: 'FRAUD_ALERT',
        paymentId: paymentRequest.id,
        riskLevel,
        riskFactors,
        context
      });
    }

    return {
      riskLevel,
      totalScore,
      riskFactors,
      action
    };
  }

  private calculateRiskLevel(score: number): RiskLevel {
    if (score >= 80) return 'CRITICAL';
    if (score >= 50) return 'HIGH';
    if (score >= 20) return 'MEDIUM';
    return 'LOW';
  }

  private determineAction(riskLevel: RiskLevel): FraudAction {
    switch (riskLevel) {
      case 'CRITICAL':
        return { type: 'BLOCK', reason: 'Critical fraud risk detected' };
      case 'HIGH':
        return { type: 'REQUIRE_VERIFICATION', reason: 'High fraud risk, additional verification required' };
      case 'MEDIUM':
        return { type: 'ALLOW_WITH_MONITORING', reason: 'Medium risk, transaction monitored' };
      case 'LOW':
        return { type: 'ALLOW', reason: 'Low risk' };
    }
  }
}

/**
 * Velocity check rule
 */
class VelocityCheckRule implements FraudRule {
  name = 'VELOCITY_CHECK';
  weight = 30;

  constructor(private store: VelocityStore) {}

  async evaluate(
    request: PaymentRequest,
    context: PaymentContext
  ): Promise<RuleResult> {
    // Check payment attempts in last 5 minutes
    const recentAttempts = await this.store.countAttempts({
      customerId: context.customerId,
      since: new Date(Date.now() - 5 * 60 * 1000)
    });

    if (recentAttempts > 3) {
      return {
        isTriggered: true,
        score: this.weight,
        description: `${recentAttempts} payment attempts in 5 minutes`,
        severity: 'high'
      };
    }

    // Check failed payments
    const recentFailures = await this.store.countFailures({
      customerId: context.customerId,
      since: new Date(Date.now() - 60 * 60 * 1000)
    });

    if (recentFailures > 5) {
      return {
        isTriggered: true,
        score: this.weight,
        description: `${recentFailures} failed payments in 1 hour`,
        severity: 'high'
      };
    }

    return { isTriggered: false, score: 0 };
  }
}

/**
 * Location anomaly rule
 */
class LocationAnomalyRule implements FraudRule {
  name = 'LOCATION_ANOMALY';
  weight = 25;

  constructor(
    private geoService: GeoLocationService,
    private customerStore: CustomerStore
  ) {}

  async evaluate(
    request: PaymentRequest,
    context: PaymentContext
  ): Promise<RuleResult> {
    // Get current location from IP
    const currentLocation = await this.geoService.getLocation(context.ipAddress);

    // Get customer's typical locations
    const customer = await this.customerStore.get(context.customerId);
    const typicalLocations = customer.typicalLocations || [];

    // Check if current location is unusual
    const isUnusual = !typicalLocations.some(loc =>
      this.isNearby(currentLocation, loc, 500) // 500km radius
    );

    if (isUnusual && typicalLocations.length > 0) {
      // Check if high-risk country
      const isHighRisk = await this.geoService.isHighRiskCountry(currentLocation.countryCode);

      return {
        isTriggered: true,
        score: isHighRisk ? this.weight : this.weight * 0.5,
        description: `Payment from unusual location: ${currentLocation.city}, ${currentLocation.country}`,
        severity: isHighRisk ? 'high' : 'medium'
      };
    }

    return { isTriggered: false, score: 0 };
  }

  private isNearby(loc1: Location, loc2: Location, thresholdKm: number): boolean {
    const distance = this.calculateDistance(loc1, loc2);
    return distance <= thresholdKm;
  }

  private calculateDistance(loc1: Location, loc2: Location): number {
    // Haversine formula
    const R = 6371; // Earth's radius in km
    const dLat = this.toRad(loc2.latitude - loc1.latitude);
    const dLon = this.toRad(loc2.longitude - loc1.longitude);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(loc1.latitude)) * Math.cos(this.toRad(loc2.latitude)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  private toRad(degrees: number): number {
    return degrees * Math.PI / 180;
  }
}

/**
 * Card testing rule
 */
class CardTestingRule implements FraudRule {
  name = 'CARD_TESTING';
  weight = 40;

  constructor(private store: PaymentStore) {}

  async evaluate(
    request: PaymentRequest,
    context: PaymentContext
  ): Promise<RuleResult> {
    // Check for multiple different cards, same amount
    const recentPayments = await this.store.findRecent({
      ipAddress: context.ipAddress,
      since: new Date(Date.now() - 30 * 60 * 1000) // 30 minutes
    });

    // Count unique cards (by last 4)
    const uniqueCards = new Set(
      recentPayments
        .filter(p => p.status === 'FAILED')
        .map(p => p.cardLast4)
    );

    if (uniqueCards.size >= 3) {
      // Check if amounts are similar
      const amounts = recentPayments.map(p => p.amount);
      const avgAmount = amounts.reduce((a, b) => a + b, 0) / amounts.length;
      const isSimilarAmount = amounts.every(a => Math.abs(a - avgAmount) < avgAmount * 0.1);

      if (isSimilarAmount) {
        return {
          isTriggered: true,
          score: this.weight,
          description: `Potential card testing: ${uniqueCards.size} different cards with similar amounts`,
          severity: 'critical'
        };
      }
    }

    return { isTriggered: false, score: 0 };
  }
}

// Interfaces
interface FraudRule {
  name: string;
  weight: number;
  evaluate(request: PaymentRequest, context: PaymentContext): Promise<RuleResult>;
}

interface RuleResult {
  isTriggered: boolean;
  score: number;
  description?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

interface FraudAnalysisResult {
  riskLevel: RiskLevel;
  totalScore: number;
  riskFactors: RiskFactor[];
  action: FraudAction;
}

type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

interface RiskFactor {
  rule: string;
  score: number;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface FraudAction {
  type: 'BLOCK' | 'REQUIRE_VERIFICATION' | 'ALLOW_WITH_MONITORING' | 'ALLOW';
  reason: string;
}
```

---

## Audit & Logging

### Audit Log Schema

```typescript
/**
 * Payment audit log entry
 */
interface PaymentAuditLog {
  id: string;
  timestamp: Date;

  // Event details
  eventType: AuditEventType;
  category: 'payment' | 'refund' | 'token' | 'dispute' | 'fraud';

  // Entities involved
  paymentId?: string;
  transactionId?: string;
  customerId?: string;
  agencyId?: string;
  userId?: string;

  // Event data
  eventData: {
    status?: TransactionStatus;
    amount?: number;
    currency?: string;
    gateway?: string;
    [key: string]: unknown;
  };

  // Request context
  requestContext: {
    ipAddress: string;
    userAgent: string;
    sessionId?: string;
    requestId: string;
  };

  // Security
  securityContext: {
    authenticated: boolean;
    userId?: string;
    roles: string[];
    mfaVerified?: boolean;
  };

  // Result
  result: 'SUCCESS' | 'FAILURE' | 'PARTIAL';
  errorMessage?: string;

  // Data retention
  retentionUntil: Date; // Typically 7 years for financial data
}

type AuditEventType =
  | 'PAYMENT_LINK_CREATED'
  | 'PAYMENT_INITIATED'
  | 'PAYMENT_COMPLETED'
  | 'PAYMENT_FAILED'
  | 'PAYMENT_CANCELLED'
  | 'REFUND_INITIATED'
  | 'REFUND_COMPLETED'
  | 'TOKEN_CREATED'
  | 'TOKEN_DELETED'
  | 'CARD_SAVED'
  | 'CARD_DELETED'
  | 'FRAUD_FLAGGED'
  | 'FRAUD_REVIEWED'
  | 'DISPUTE_OPENED'
  | 'DISPUTE_RESOLVED'
  | 'WEBHOOK_RECEIVED'
  | 'WEBHOOK_PROCESSED';
```

### Audit Logger

```typescript
/**
 * Payment audit logger
 */
class PaymentAuditLogger {
  constructor(
    private store: AuditLogStore,
    private logger: winston.Logger
  ) {}

  /**
   * Log payment event
   */
  async log(event: AuditEvent): Promise<void> {
    const logEntry: PaymentAuditLog = {
      id: this.generateId(),
      timestamp: new Date(),
      eventType: event.type,
      category: event.category,
      paymentId: event.paymentId,
      transactionId: event.transactionId,
      customerId: event.customerId,
      agencyId: event.agencyId,
      userId: event.userId,
      eventData: event.data || {},
      requestContext: event.context || await this.getDefaultContext(),
      securityContext: event.security || await this.getDefaultSecurity(),
      result: event.result || 'SUCCESS',
      errorMessage: event.error,
      retentionUntil: this.calculateRetention(event.type)
    };

    // Store in audit database
    await this.store.insert(logEntry);

    // Also log to application logger
    this.logger.info('Payment audit event', {
      eventType: event.type,
      paymentId: event.paymentId,
      result: logEntry.result
    });

    // Send to SIEM if critical
    if (this.isCriticalEvent(event.type)) {
      await this.sendToSIEM(logEntry);
    }
  }

  /**
   * Query audit logs
   */
  async query(filters: AuditFilters): Promise<PaymentAuditLog[]> {
    return await this.store.query(filters);
  }

  /**
   * Generate audit report
   */
  async generateReport(params: ReportParams): Promise<AuditReport> {
    const logs = await this.query({
      startDate: params.startDate,
      endDate: params.endDate,
      agencyId: params.agencyId,
      eventTypes: params.eventTypes
    });

    return {
      period: { start: params.startDate, end: params.endDate },
      totalEvents: logs.length,
      summary: this.summarizeLogs(logs),
      events: logs
    };
  }

  private calculateRetention(eventType: AuditEventType): Date {
    // Financial records: 7 years
    const sevenYears = 7 * 365 * 24 * 60 * 60 * 1000;
    return new Date(Date.now() + sevenYears);
  }

  private isCriticalEvent(eventType: AuditEventType): boolean {
    return [
      'FRAUD_FLAGGED',
      'DISPUTE_OPENED',
      'PAYMENT_FAILED',
      'REFUND_INITIATED'
    ].includes(eventType);
  }

  private async sendToSIEM(logEntry: PaymentAuditLog): Promise<void> {
    // Send to SIEM (e.g., Splunk, DataDog)
  }

  private summarizeLogs(logs: PaymentAuditLog[]): LogSummary {
    return {
      byEventType: this.groupBy(logs, 'eventType'),
      byStatus: this.groupBy(logs, 'result'),
      byAmount: {
        total: logs.reduce((sum, l) => sum + (l.eventData.amount as number || 0), 0),
        count: logs.length
      },
      fraudEvents: logs.filter(l => l.category === 'fraud').length
    };
  }

  private groupBy(logs: PaymentAuditLog[], key: string): Record<string, number> {
    return logs.reduce((acc, log) => {
      const value = (log as any)[key] || 'unknown';
      acc[value] = (acc[value] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }

  private generateId(): string {
    return `audit_${Date.now()}_${crypto.randomBytes(8).toString('hex')}`;
  }

  private async getDefaultContext(): Promise<RequestContext> {
    return {
      ipAddress: '0.0.0.0',
      userAgent: 'system',
      requestId: 'system'
    };
  }

  private async getDefaultSecurity(): Promise<SecurityContext> {
    return {
      authenticated: false,
      roles: ['system']
    };
  }
}

interface AuditEvent {
  type: AuditEventType;
  category: 'payment' | 'refund' | 'token' | 'dispute' | 'fraud';
  paymentId?: string;
  transactionId?: string;
  customerId?: string;
  agencyId?: string;
  userId?: string;
  data?: Record<string, unknown>;
  context?: RequestContext;
  security?: SecurityContext;
  result?: 'SUCCESS' | 'FAILURE' | 'PARTIAL';
  error?: string;
}

interface RequestContext {
  ipAddress: string;
  userAgent: string;
  sessionId?: string;
  requestId: string;
}

interface SecurityContext {
  authenticated: boolean;
  userId?: string;
  roles: string[];
  mfaVerified?: boolean;
}

interface AuditFilters {
  startDate?: Date;
  endDate?: Date;
  agencyId?: string;
  customerId?: string;
  eventTypes?: AuditEventType[];
}

interface ReportParams {
  startDate: Date;
  endDate: Date;
  agencyId?: string;
  eventTypes?: AuditEventType[];
}

interface AuditReport {
  period: { start: Date; end: Date };
  totalEvents: number;
  summary: LogSummary;
  events: PaymentAuditLog[];
}

interface LogSummary {
  byEventType: Record<string, number>;
  byStatus: Record<string, number>;
  byAmount: { total: number; count: number };
  fraudEvents: number;
}
```

---

## Summary

This document covers compliance requirements for payment processing:

1. **Regulatory Framework** — PCI DSS, RBI guidelines, DPDP Act 2023
2. **PCI DSS Compliance** — Data handling rules, masking, validation
3. **RBI Guidelines** — Tokenization, card storage, authentication
4. **Data Security** — Encryption, access controls, security architecture
5. **Tokenization** — Token flow, token service, saved cards
6. **Fraud Prevention** — Detection rules, velocity checks, anomaly detection
7. **Audit & Logging** — Audit schema, logging service, reporting

**Key Takeaways:**

- Never store CVV, PIN, or full PAN
- Use gateway tokenization for all card storage
- Encrypt all sensitive data at rest (AES-256) and in transit (TLS 1.3)
- Implement comprehensive fraud detection
- Log all payment events for 7-year retention
- Follow RBI guidelines for Indian market

**Related Documents:**
- [Technical Deep Dive](./PAYMENT_PROCESSING_01_TECHNICAL_DEEP_DIVE.md) — Backend architecture
- [Reconciliation Deep Dive](./PAYMENT_PROCESSING_04_RECONCILIATION_DEEP_DIVE.md) — Settlement, accounting
