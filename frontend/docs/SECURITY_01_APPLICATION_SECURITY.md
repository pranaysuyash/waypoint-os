# SECURITY_01: Application Security

> OWASP Top 10 mitigation, input validation, output encoding, and secure coding practices

---

## Document Overview

**Series:** Security Hardening
**Document:** 1 of 4
**Focus:** Application Security
**Last Updated:** 2026-04-25

---

## Table of Contents

1. [Introduction](#introduction)
2. [Threat Model](#threat-model)
3. [OWASP Top 10 Mitigation](#owasp-top-10-mitigation)
4. [Input Validation](#input-validation)
5. [Output Encoding](#output-encoding)
6. [Authentication Security](#authentication-security)
7. [Session Management](#session-management)
8. [Security Headers](#security-headers)
9. [File Upload Security](#file-upload-security)
10. [Dependency Security](#dependency-security)
11. [API Specification](#api-specification)
12. [Testing Scenarios](#testing-scenarios)

---

## 1. Introduction

### Application Security Principles

Application security protects the Travel Agency Agent from vulnerabilities that could compromise:

- **Customer Data** - PII, payment information, travel details
- **Business Logic** - Booking flows, pricing, recommendations
- **User Sessions** - Authentication tokens, session data
- **System Integrity** - Preventing unauthorized access

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Validate Input** | Never trust user input |
| **Encode Output** | Prevent injection attacks |
| **Authenticate Properly** | Strong identity verification |
| **Authorize Access** | Least privilege permissions |
| **Encrypt Data** | Protect sensitive information |
| **Log Security Events** | Audit trail for investigations |
| **Update Dependencies** | Patch known vulnerabilities |

---

## 2. Threat Model

### Threat Actors

```typescript
// security/threat-model.ts

export interface ThreatActor {
  type: 'external' | 'internal' | 'partner' | 'automated';
  capabilities: string[];
  motivation: 'financial' | 'data_theft' | 'disruption' | 'espionage';
  likelihood: 'low' | 'medium' | 'high';
}

export interface ThreatScenario {
  id: string;
  name: string;
  description: string;
  actor: ThreatActor;
  attackVector: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  mitigations: string[];
}

/**
 * Threat model for Travel Agency Agent
 */
export const threatModel: ThreatScenario[] = [
  {
    id: 'TM-001',
    name: 'Credential Stuffing',
    description: 'Attacker uses compromised credentials to access customer accounts',
    actor: {
      type: 'external',
      capabilities: ['automation', 'credential_databases'],
      motivation: 'financial',
      likelihood: 'high'
    },
    attackVector: 'Web login endpoint',
    impact: 'high',
    mitigations: [
      'Rate limiting on login',
      'Multi-factor authentication',
      'Password breach detection',
      'Account lockout after failures'
    ]
  },
  {
    id: 'TM-002',
    name: 'SQL Injection',
    description: 'Attacker injects malicious SQL to extract or modify database data',
    actor: {
      type: 'external',
      capabilities: ['sql_knowledge', 'automation'],
      motivation: 'data_theft',
      likelihood: 'medium'
    },
    attackVector: 'API endpoints with database queries',
    impact: 'critical',
    mitigations: [
      'Parameterized queries',
      'ORM usage',
      'Input validation',
      'Least privilege database access'
    ]
  },
  {
    id: 'TM-003',
    name: 'XSS Attack',
    description: 'Attacker injects malicious scripts into user-generated content',
    actor: {
      type: 'external',
      capabilities: ['javascript', 'social_engineering'],
      motivation: 'data_theft',
      likelihood: 'medium'
    },
    attackVector: 'User input fields, chat, reviews',
    impact: 'high',
    mitigations: [
      'Content Security Policy',
      'Output encoding',
      'Input sanitization',
      'HttpOnly cookies'
    ]
  },
  {
    id: 'TM-004',
    name: 'CSRF Attack',
    description: 'Attacker tricks users into performing actions they didn\'t intend',
    actor: {
      type: 'external',
      capabilities: ['social_engineering'],
      motivation: 'financial',
      likelihood: 'low'
    },
    attackVector: 'State-changing operations',
    impact: 'medium',
    mitigations: [
      'CSRF tokens',
      'SameSite cookie attribute',
      'Origin verification'
    ]
  },
  {
    id: 'TM-005',
    name: 'Payment Fraud',
    description: 'Attacker attempts to make fraudulent bookings or payments',
    actor: {
      type: 'external',
      capabilities: ['stolen_cards', 'account_takeover'],
      motivation: 'financial',
      likelihood: 'high'
    },
    attackVector: 'Booking and payment endpoints',
    impact: 'critical',
    mitigations: [
      '3D Secure authentication',
      'Address verification',
      'Velocity checks',
      'Fraud scoring',
      'Manual review for high-risk'
    ]
  },
  {
    id: 'TM-006',
    name: 'Data Scraping',
    description: 'Automated scraping of pricing, inventory, or customer data',
    actor: {
      type: 'external',
      capabilities: ['automation', 'bot_networks'],
      motivation: 'data_theft',
      likelihood: 'high'
    },
    attackVector: 'Public API endpoints',
    impact: 'medium',
    mitigations: [
      'Rate limiting',
      'Bot detection',
      'API authentication',
      'Captcha for suspicious activity'
    ]
  }
];
```

---

## 3. OWASP Top 10 Mitigation

### A01: Broken Access Control

```typescript
// security/access-control.ts

/**
 * Enforce access control using authorization middleware
 */
export class AccessControlMiddleware {
  private rbac: RoleBasedAccessControl;

  /**
   * Check if user has permission for resource
   */
  async checkPermission(request: {
    userId: string;
    action: string;
    resource: string;
    resourceId?: string;
  }): Promise<{ allowed: boolean; reason?: string }> {
    // Get user roles
    const roles = await this.getUserRoles(request.userId);

    // Check role-based permissions
    for (const role of roles) {
      const permission = await this.rbac.checkPermission(role, request.action, request.resource);

      if (permission.allowed) {
        // Check resource-level ownership if needed
        if (request.resourceId) {
          const hasOwnership = await this.checkOwnership(request.userId, request.resourceId);
          if (!hasOwnership) {
            return { allowed: false, reason: 'Resource ownership required' };
          }
        }

        return { allowed: true };
      }
    }

    return { allowed: false, reason: 'Insufficient permissions' };
  }

  /**
   * Express middleware for access control
   */
  middleware(action: string, resource: string) {
    return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
      const result = await this.checkPermission({
        userId: req.user.id,
        action,
        resource,
        resourceId: req.params.id
      });

      if (!result.allowed) {
        return res.status(403).json({
          error: 'Access denied',
          reason: result.reason
        });
      }

      next();
    };
  }
}

/**
 * Ownership-based access control
 */
export class OwnershipAccessControl {
  /**
   * Check if user owns or has access to resource
   */
  async checkOwnership(userId: string, resourceId: string, resourceType: string): Promise<boolean> {
    switch (resourceType) {
      case 'trip':
        return await this.checkTripOwnership(userId, resourceId);

      case 'agency':
        return await this.checkAgencyMembership(userId, resourceId);

      case 'document':
        return await this.checkDocumentAccess(userId, resourceId);

      default:
        return false;
    }
  }

  /**
   * Trip ownership: user must be trip owner or agency member
   */
  private async checkTripOwnership(userId: string, tripId: string): Promise<boolean> {
    const trip = await this.tripStore.get(tripId);

    // Direct ownership
    if (trip.customerId === userId) {
      return true;
    }

    // Agency membership
    const userAgency = await this.getUserAgency(userId);
    if (userAgency && trip.agencyId === userAgency.id) {
      return true;
    }

    return false;
  }
}
```

### A02: Cryptographic Failures

```typescript
// security/crypto.ts

import crypto from 'crypto';
import bcrypt from 'bcrypt';
import { encrypt as encryptAes, decrypt as decryptAes } from './aes';

/**
 * Secure password handling
 */
export class PasswordSecurity {
  private readonly SALT_ROUNDS = 12;

  /**
   * Hash password using bcrypt
   */
  async hash(password: string): Promise<string> {
    return await bcrypt.hash(password, this.SALT_ROUNDS);
  }

  /**
   * Verify password against hash
   */
  async verify(password: string, hash: string): Promise<boolean> {
    return await bcrypt.compare(password, hash);
  }

  /**
   * Validate password strength
   */
  validateStrength(password: string): {
    valid: boolean;
    score: number;
    feedback: string[];
  } {
    const feedback: string[] = [];
    let score = 0;

    // Length check
    if (password.length >= 12) {
      score += 2;
    } else if (password.length >= 8) {
      score += 1;
      feedback.push('Use at least 12 characters');
    } else {
      feedback.push('Password is too short (min 8 characters)');
    }

    // Complexity checks
    if (/[a-z]/.test(password)) score += 1;
    else feedback.push('Include lowercase letters');

    if (/[A-Z]/.test(password)) score += 1;
    else feedback.push('Include uppercase letters');

    if (/[0-9]/.test(password)) score += 1;
    else feedback.push('Include numbers');

    if (/[^a-zA-Z0-9]/.test(password)) score += 1;
    else feedback.push('Include special characters');

    // Common password check
    if (this.isCommonPassword(password)) {
      score = 0;
      feedback.push('This is a commonly used password');
    }

    return {
      valid: score >= 4,
      score,
      feedback
    };
  }
}

/**
 * Sensitive data encryption at rest
 */
export class DataEncryption {
  private keyManager: KeyManagementService;

  /**
   * Encrypt sensitive data
   */
  async encrypt(data: string, context: { dataType: string; userId?: string }): Promise<{
    encrypted: string;
    keyId: string;
    algorithm: string;
  }> {
    const key = await this.keyManager.getDataKey(context);
    const encrypted = await encryptAes(data, key);

    return {
      encrypted: encrypted.data,
      keyId: key.id,
      algorithm: 'AES-256-GCM'
    };
  }

  /**
   * Decrypt sensitive data
   */
  async decrypt(
    encryptedData: string,
    keyId: string,
    context: { dataType: string; userId?: string }
  ): Promise<string> {
    // Log decryption attempt for audit
    await this.auditLogger.log({
      event: 'data_decryption',
      keyId,
      dataType: context.dataType,
      userId: context.userId
    });

    const key = await this.keyManager.getKey(keyId, context);
    return await decryptAes(encryptedData, key);
  }

  /**
   * Encrypt PII fields in database records
   */
  encryptPII<T extends Record<string, any>>(
    record: T,
    piiFields: (keyof T)[],
    context: { userId?: string }
  ): Promise<T> {
    const encrypted = { ...record };

    for (const field of piiFields) {
      const value = record[field];
      if (typeof value === 'string') {
        encrypted[field] = this.encrypt(value, {
          dataType: String(field),
          userId: context.userId
        }) as any;
      }
    }

    return encrypted;
  }
}

/**
 * Secure token generation
 */
export class TokenGenerator {
  /**
   * Generate cryptographically secure random token
   */
  generateSecureToken(length: number = 32): string {
    return crypto.randomBytes(length).toString('base64url');
  }

  /**
   * Generate API key with prefix
   */
  generateApiKey(prefix: string = 'ta'): string {
    const random = this.generateSecureToken(24);
    return `${prefix}_${random}`;
  }

  /**
   * Generate session token
   */
  generateSessionToken(): string {
    return crypto.randomBytes(32).toString('hex');
  }

  /**
   * Generate CSRF token
   */
  generateCsrfToken(): string {
    return this.generateSecureToken(32);
  }

  /**
   * Generate secure nonce for CSP
   */
  generateNonce(): string {
    return crypto.randomBytes(16).toString('base64');
  }
}
```

### A03: Injection

```typescript
// security/injection-prevention.ts

import { z } from 'zod';

/**
 * Input validation to prevent injection attacks
 */
export class InputValidator {
  /**
   * Validate and sanitize user input
   */
  validate<T>(schema: z.ZodSchema<T>, input: unknown): {
    valid: boolean;
    data?: T;
    errors?: string[];
  } {
    try {
      const data = schema.parse(input);
      return { valid: true, data };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return {
          valid: false,
          errors: error.errors.map(e => `${e.path.join('.')}: ${e.message}`)
        };
      }
      return { valid: false, errors: ['Validation failed'] };
    }
  }

  /**
   * Sanitize HTML input
   */
  sanitizeHTML(html: string): string {
    // Strip potentially dangerous HTML
    return html
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
      .replace(/on\w+="[^"]*"/gi, '')  // Remove event handlers
      .replace(/javascript:/gi, '');  // Remove javascript: protocol
  }

  /**
   * Sanitize SQL input (when not using parameterized queries)
   */
  sanitizeSQL(input: string): string {
    return input
      .replace(/['"\\]/g, '')  // Remove quotes and backslashes
      .replace(/--/g, '')       // Remove SQL comments
      .replace(/;/g, '');       // Remove statement terminators
  }

  /**
   * Detect and block SQL injection attempts
   */
  detectSQLInjection(input: string): boolean {
    const sqlPatterns = [
      /(\bunion\b.*\bselect\b)/i,
      /(\bselect\b.*\bfrom\b)/i,
      /(\binsert\b.*\binto\b)/i,
      /(\bupdate\b.*\bset\b)/i,
      /(\bdelete\b.*\bfrom\b)/i,
      /(\bdrop\b.*\btable\b)/i,
      /(\bexec\b|\bexecute\b)/i,
      /(;|\bwaitfor\b\bdelay\b)/i,
      /('.*--)/i,
      /(\|.*\|)/i,
      /(\bconcat\b)/i
    ];

    return sqlPatterns.some(pattern => pattern.test(input));
  }

  /**
   * Detect and block XSS attempts
   */
  detectXSS(input: string): boolean {
    const xssPatterns = [
      /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
      /<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi,
      /javascript:/gi,
      /on\w+\s*=/i,  // Event handlers like onclick=
      /<img[^>]+src[^>]*>/gi,
      /<\?php/i,
      /<%/gi
    ];

    return xssPatterns.some(pattern => pattern.test(input));
  }
}

/**
 * Validation schemas for common inputs
 */
export const validationSchemas = {
  // Email validation
  email: z.string().email().max(254).refine(
    (email) => !email.includes('+'),
    'Email aliases not allowed'
  ),

  // Phone number validation
  phone: z.string().regex(/^\+?[\d\s\-\(\)]+$/).min(10).max(15),

  // Destination name (letters, spaces, hyphens, apostrophes)
  destinationName: z.string().regex(/^[a-zA-Z\s\-\']{2,50}$/),

  // Date validation
  date: z.string().refine(
    (date) => !isNaN(Date.parse(date)),
    'Invalid date format'
  ),

  // Budget validation
  budget: z.object({
    min: z.number().min(0).max(1000000),
    max: z.number().min(0).max(1000000)
  }).refine(
    (budget) => budget.max >= budget.min,
    'Max budget must be greater than min'
  ),

  // Traveler count
  travelers: z.object({
    adults: z.number().min(1).max(50),
    children: z.number().min(0).max(20),
    infants: z.number().min(0).max(10)
  }),

  // Trip ID (UUID format)
  tripId: z.string().uuid(),

  // Safe string (no special characters)
  safeString: z.string().regex(/^[a-zA-Z0-9\s\-_\.]+$/),

  // URL validation
  url: z.string().url().refine(
    (url) => url.startsWith('https://'),
    'Only HTTPS URLs allowed'
  )
};
```

### A04: Insecure Design

```typescript
// security/secure-design.ts

/**
 * Business logic security
 */
export class BusinessLogicSecurity {
  /**
   * Validate booking constraints
   */
  async validateBookingConstraints(booking: BookingRequest): Promise<{
    valid: boolean;
    errors: string[];
  }> {
    const errors: string[] = [];

    // Check booking window
    const daysUntilTravel = Math.floor(
      (new Date(booking.startDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    );

    if (daysUntilTravel < 1) {
      errors.push('Cannot book for travel starting within 24 hours');
    }

    if (daysUntilTravel > 365) {
      errors.push('Cannot book more than 365 days in advance');
    }

    // Check duration constraints
    const duration = booking.duration;
    if (duration < 1) {
      errors.push('Minimum trip duration is 1 day');
    }

    if (duration > 90) {
      errors.push('Maximum trip duration is 90 days');
    }

    // Check traveler constraints
    if (booking.travelers.adults < booking.travelers.children + booking.travelers.infants) {
      errors.push('Each child/infant must be accompanied by an adult');
    }

    // Check payment amount matches pricing
    const calculatedPrice = await this.calculatePrice(booking);
    const priceDifference = Math.abs(booking.totalAmount - calculatedPrice);

    if (priceDifference > calculatedPrice * 0.1) {  // 10% tolerance
      errors.push(`Payment amount mismatch. Expected: ${calculatedPrice}, Received: ${booking.totalAmount}`);
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Detect suspicious booking patterns
   */
  async detectSuspiciousPatterns(booking: BookingRequest, userId: string): Promise<{
    suspicious: boolean;
    reasons: string[];
    riskScore: number;
  }> {
    const reasons: string[] = [];
    let riskScore = 0;

    // Check for rapid successive bookings
    const recentBookings = await this.getRecentBookings(userId, 60);  // Last hour
    if (recentBookings.length > 5) {
      reasons.push('Unusual booking frequency');
      riskScore += 30;
    }

    // Check for high-value first booking
    const userHistory = await this.getUserBookingHistory(userId);
    if (userHistory.length === 0 && booking.totalAmount > 10000) {
      reasons.push('High-value first-time booking');
      riskScore += 40;
    }

    // Check for mismatched billing and travel info
    if (booking.billingCountry !== booking.destinationCountry) {
      // Higher risk for certain routes
      const highRiskRoutes = await this.getHighRiskRoutes();
      if (highRiskRoutes.includes(`${booking.billingCountry}-${booking.destinationCountry}`)) {
        reasons.push('High-risk billing-travel country combination');
        riskScore += 25;
      }
    }

    // Check for last-minute booking with premium payment
    if (this.isLastMinute(booking.startDate) && booking.paymentMethod === 'premium') {
      reasons.push('Last-minute premium payment');
      riskScore += 15;
    }

    return {
      suspicious: riskScore > 50,
      reasons,
      riskScore
    };
  }
}
```

### A05: Security Misconfiguration

```typescript
// security/config.ts

/**
 * Secure configuration management
 */
export class SecurityConfig {
  /**
   * Get secure configuration with defaults
   */
  getConfig(): SecurityConfiguration {
    return {
      // Headers
      headers: {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': this.getPermissionsPolicy()
      },

      // Content Security Policy
      csp: this.getCSP(),

      // Session configuration
      session: {
        secret: process.env.SESSION_SECRET,
        resave: false,
        saveUninitialized: false,
        cookie: {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'strict',
          maxAge: 24 * 60 * 60 * 1000,  // 24 hours
          domain: process.env.COOKIE_DOMAIN
        },
        name: 'sessionId'
      },

      // Rate limiting
      rateLimit: {
        windowMs: 15 * 60 * 1000,  // 15 minutes
        max: 100,  // 100 requests per window
        standardHeaders: true,
        legacyHeaders: false
      },

      // File upload
      uploads: {
        maxSize: 5 * 1024 * 1024,  // 5MB
        allowedTypes: ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'],
        allowedExtensions: ['.jpg', '.jpeg', '.png', '.webp', '.pdf']
      },

      // Password policy
      password: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true,
        requireSpecialChars: true,
        preventCommon: true,
        preventUserInfo: true,
        expirationDays: 90,
        preventReuse: 5,
        lockoutThreshold: 5,
        lockoutDuration: 15 * 60 * 1000  // 15 minutes
      }
    };
  }

  /**
   * Generate Content Security Policy
   */
  private getCSP(): string {
    const isDev = process.env.NODE_ENV === 'development';

    return [
      `default-src 'self'`,
      `script-src 'self' ${isDev ? "'unsafe-inline' 'unsafe-eval'" : ''}`,
      `style-src 'self' ${isDev ? "'unsafe-inline'" : ''}`,
      `img-src 'self' data: https: blob:`,
      `font-src 'self' data:`,
      `connect-src 'self' ${process.env.ALLOWED_ORIGINS || ''}`,
      `frame-src 'none'`,
      `object-src 'none'`,
      `base-uri 'self'`,
      `form-action 'self'`,
      `frame-ancestors 'none'`,
      `upgrade-insecure-requests`
    ].filter(Boolean).join('; ');
  }

  /**
   * Generate Permissions-Policy header
   */
  private getPermissionsPolicy(): string {
    return [
      'geolocation=()',
      'microphone=()',
      'camera=()',
      'payment=(self)',
      'usb=()',
      'magnetometer=()',
      'gyroscope=()',
      'accelerometer=()'
    ].join(', ');
  }
}
```

---

## 4. Input Validation

### Request Validation Middleware

```typescript
// middleware/validation.ts

import { z } from 'zod';

/**
 * Request validation middleware using Zod schemas
 */
export function validateRequest<T>(schema: {
  body?: z.ZodSchema<T>;
  query?: z.ZodSchema<any>;
  params?: z.ZodSchema<any>;
}) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      // Validate body
      if (schema.body) {
        req.body = schema.body.parse(req.body);
      }

      // Validate query
      if (schema.query) {
        req.query = schema.query.parse(req.query);
      }

      // Validate params
      if (schema.params) {
        req.params = schema.params.parse(req.params);
      }

      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          error: 'Validation failed',
          details: error.errors.map(e => ({
            field: e.path.join('.'),
            message: e.message,
            code: e.code
          }))
        });
      }

      return res.status(400).json({
        error: 'Invalid request'
      });
    }
  };
}

/**
 * Common validation schemas
 */
export const schemas = {
  trip: {
    create: z.object({
      destinationId: z.string().min(1).max(100),
      startDate: z.string().datetime(),
      endDate: z.string().datetime(),
      travelers: z.object({
        adults: z.number().int().min(1).max(50),
        children: z.number().int().min(0).max(20).default(0),
        infants: z.number().int().min(0).max(10).default(0)
      }),
      budget: z.object({
        min: z.number().min(0).optional(),
        max: z.number().positive().optional()
      }).optional(),
      preferences: z.object({
        interests: z.array(z.string()).max(20).optional(),
        accommodationType: z.enum(['budget', 'standard', 'luxury']).optional(),
        tripType: z.enum(['leisure', 'business', 'adventure', 'family', 'honeymoon']).optional()
      }).optional()
    }).refine(
      (data) => new Date(data.endDate) > new Date(data.startDate),
      'End date must be after start date'
    ),

    update: z.object({
      destinationId: z.string().min(1).max(100).optional(),
      startDate: z.string().datetime().optional(),
      endDate: z.string().datetime().optional(),
      travelers: z.object({
        adults: z.number().int().min(1).max(50),
        children: z.number().int().min(0).max(20).default(0),
        infants: z.number().int().min(0).max(10).default(0)
      }).optional(),
      status: z.enum(['draft', 'inquiry', 'quoted', 'confirmed', 'cancelled']).optional()
    }).partial()
  },

  inquiry: {
    create: z.object({
      source: z.enum(['web', 'email', 'whatsapp', 'phone', 'referral']),
      customerInfo: z.object({
        name: z.string().min(2).max(100),
        email: z.string().email(),
        phone: z.string().regex(/^\+?[\d\s\-\(\)]+$/).optional(),
        userId: z.string().uuid().optional()
      }),
      message: z.string().min(10).max(5000),
      destination: z.string().min(2).max(100).optional(),
      dates: z.object({
        start: z.string().datetime().optional(),
        end: z.string().datetime().optional(),
        flexible: z.boolean().default(false)
      }).optional(),
      travelers: z.object({
        adults: z.number().int().min(1).max(50).default(2),
        children: z.number().int().min(0).max(20).default(0),
        infants: z.number().int().min(0).max(10).default(0)
      }).optional(),
      budget: z.object({
        min: z.number().min(0).optional(),
        max: z.number().positive().optional(),
        currency: z.string().default('USD')
      }).optional()
    })
  },

  search: {
    query: z.object({
      q: z.string().min(2).max(200),
      type: z.enum(['destination', 'activity', 'hotel', 'all']).default('all'),
      limit: z.number().int().min(1).max(100).default(20),
      offset: z.number().int().min(0).default(0),
      filters: z.object({
        country: z.string().optional(),
        budgetMin: z.number().min(0).optional(),
        budgetMax: z.number().positive().optional(),
        durationMin: z.number().int().min(1).optional(),
        durationMax: z.number().int().max(90).optional()
      }).optional()
    })
  }
};
```

---

## 5. Output Encoding

### XSS Prevention

```typescript
// security/xss-prevention.ts

import escapeHtml from 'escape-html';

/**
 * Output encoding for XSS prevention
 */
export class OutputEncoder {
  /**
   * Encode HTML content
   */
  encodeHTML(unsafe: string): string {
    return escapeHtml(unsafe);
  }

  /**
   * Encode HTML attribute
   */
  encodeHTMLAttribute(unsafe: string): string {
    return unsafe
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  }

  /**
   * Encode JavaScript string
   */
  encodeJS(unsafe: string): string {
    return unsafe
      .replace(/\\/g, '\\\\')
      .replace(/ /g, '\\u2028')
      .replace(/ /g, '\\u2029')
      .replace(/'/g, "\\'")
      .replace(/"/g, '\\"')
      .replace(/\n/g, '\\n')
      .replace(/\r/g, '\\r')
      .replace(/\t/g, '\\t')
      .replace(/\f/g, '\\f');
  }

  /**
   * Encode URL parameter
   */
  encodeURL(unsafe: string): string {
    return encodeURIComponent(unsafe);
  }

  /**
   * Sanitize user-generated content for display
   */
  sanitizeUserContent(content: string, options: {
    allowLinks?: boolean;
    allowFormatting?: boolean;
    maxLength?: number;
  } = {}): string {
    let sanitized = this.encodeHTML(content);

    // Truncate if needed
    if (options.maxLength && sanitized.length > options.maxLength) {
      sanitized = sanitized.substring(0, options.maxLength) + '...';
    }

    // Allow basic links if specified
    if (options.allowLinks) {
      sanitized = sanitized.replace(
        /&lt;a href=(&quot;[^&]*&quot;|&#x27;[^&]*&#x27;)&gt;/gi,
        '<a href=$1 rel="noopener noreferrer">'
      );
    }

    // Allow basic formatting if specified
    if (options.allowFormatting) {
      sanitized = sanitized
        .replace(/&lt;b&gt;/gi, '<b>')
        .replace(/&lt;\/b&gt;/gi, '</b>')
        .replace(/&lt;i&gt;/gi, '<i>')
        .replace(/&lt;\/i&gt;/gi, '</i>')
        .replace(/&lt;p&gt;/gi, '<p>')
        .replace(/&lt;\/p&gt;/gi, '</p>');
    }

    return sanitized;
  }

  /**
   * Generate JSONP-safe response
   */
  encodeJSONP(data: any, callback: string): string {
    // Validate callback name
    if (!/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(callback)) {
      throw new Error('Invalid callback name');
    }

    const json = JSON.stringify(data);
    return `${callback}(${json});`;
  }
}

/**
 * Content Security Policy with nonce
 */
export class CSPManager {
  private nonces = new Map<string, string>();

  /**
   * Generate nonce for inline scripts
   */
  generateNonce(): string {
    const nonce = crypto.randomBytes(16).toString('base64');
    const key = Date.now().toString();
    this.nonces.set(key, nonce);
    return nonce;
  }

  /**
   * Get CSP header with nonce
   */
  getCSPHeader(nonce?: string): string {
    const policies = [
      "default-src 'self'",
      "script-src 'self'",
      nonce ? `'nonce-${nonce}'` : '',
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https: blob:",
      "font-src 'self' data:",
      "connect-src 'self'",
      "frame-src 'none'",
      "object-src 'none'"
    ].filter(Boolean).join('; ');

    return policies;
  }

  /**
   * Clean up old nonces
   */
  cleanupNonces(olderThan: number = 60000): void {
    const cutoff = Date.now() - olderThan;

    for (const [key] of this.nonces) {
      if (parseInt(key) < cutoff) {
        this.nonces.delete(key);
      }
    }
  }
}
```

---

## 6. Authentication Security

### Multi-Factor Authentication

```typescript
// auth/mfa.ts

export enum MFAMethod {
  TOTP = 'totp',           // Time-based OTP
  SMS = 'sms',             // SMS code
  EMAIL = 'email',         // Email code
  BACKUP_CODE = 'backup',  // Backup codes
  BIO = 'biometric'        // Biometric (mobile)
}

export interface MFAChallenge {
  userId: string;
  method: MFAMethod;
  challengeId: string;
  expiresAt: Date;
  verified: boolean;
}

/**
 * Multi-factor authentication service
 */
export class MFAService {
  private totpService: TOTPService;
  private smsService: SMSService;
  private emailService: EmailService;

  /**
   * Setup MFA for user
   */
  async setupMFA(userId: string, method: MFAMethod): Promise<{
    secret?: string;
    qrCode?: string;
    backupCodes?: string[];
  }> {
    switch (method) {
      case MFAMethod.TOTP:
        return await this.setupTOTP(userId);

      case MFAMethod.SMS:
      case MFAMethod.EMAIL:
        return await this.setupOTPDelivery(userId, method);

      default:
        throw new Error('Unsupported MFA method');
    }
  }

  /**
   * Setup TOTP (Google Authenticator, etc.)
   */
  private async setupTOTP(userId: string): Promise<{
    secret: string;
    qrCode: string;
    backupCodes: string[];
  }> {
    // Generate secret
    const secret = this.totpService.generateSecret();

    // Store secret (not yet verified)
    await this.mfaStore.setPendingSecret(userId, secret);

    // Generate QR code URL
    const issuer = encodeURIComponent('Travel Agency Agent');
    const account = encodeURIComponent(userId);
    const qrCodeUrl = `otpauth://totp/${issuer}:${account}?secret=${secret}&issuer=${issuer}`;

    // Generate backup codes
    const backupCodes = this.generateBackupCodes(10);
    const hashedBackupCodes = backupCodes.map(code =>
      bcrypt.hash(code, 10)
    );

    await this.mfaStore.setBackupCodes(userId, hashedBackupCodes);

    return {
      secret,
      qrCode: qrCodeUrl,
      backupCodes
    };
  }

  /**
   * Verify MFA code
   */
  async verifyCode(userId: string, method: MFAMethod, code: string): Promise<boolean> {
    const challenge = await this.mfaStore.getActiveChallenge(userId);

    if (!challenge || challenge.expiresAt < new Date()) {
      return false;
    }

    let valid = false;

    switch (method) {
      case MFAMethod.TOTP:
        valid = await this.totpService.verify(userId, code);
        break;

      case MFAMethod.SMS:
      case MFAMethod.EMAIL:
        valid = await this.verifyOTPCode(userId, code);
        break;

      case MFAMethod.BACKUP_CODE:
        valid = await this.verifyBackupCode(userId, code);
        break;
    }

    if (valid) {
      await this.mfaStore.markVerified(challenge.challengeId);
    }

    return valid;
  }

  /**
   * Generate backup codes
   */
  private generateBackupCodes(count: number): string[] {
    const codes: string[] = [];

    for (let i = 0; i < count; i++) {
      const code = crypto.randomBytes(4).toString('hex').toUpperCase();
      codes.push(`${code.substring(0, 4)}-${code.substring(4)}`);
    }

    return codes;
  }
}

/**
 * TOTP (Time-based One-Time Password) service
 */
export class TOTPService {
  /**
   * Generate TOTP secret
   */
  generateSecret(): string {
    return crypto.randomBytes(20).toString('base32');
  }

  /**
   * Verify TOTP code
   */
  async verify(userId: string, token: string): Promise<boolean> {
    const secret = await this.mfaStore.getSecret(userId);

    if (!secret) {
      return false;
    }

    // Check token with time window (allow 1 step before/after)
    for (const offset of [-1, 0, 1]) {
      const validToken = this.generateTOTP(secret, Date.now() + offset * 30000);

      if (token === validToken) {
        return true;
      }
    }

    return false;
  }

  /**
   * Generate TOTP for given timestamp
   */
  private generateTOTP(secret: string, timestamp: number = Date.now()): string {
    const timeStep = 30000;  // 30 seconds
    const counter = Math.floor(timestamp / timeStep);
    const counterBuffer = Buffer.alloc(8);
    counterBuffer.writeBigUInt64BE(BigInt(counter));

    const hmac = crypto.createHmac('sha1', Buffer.from(secret, 'base32'));
    hmac.update(counterBuffer);
    const digest = hmac.digest();

    const offset = digest[digest.length - 1] & 0x0f;
    const code =
      ((digest[offset] & 0x7f) << 24) |
      ((digest[offset + 1] & 0xff) << 16) |
      ((digest[offset + 2] & 0xff) << 8) |
      (digest[offset + 3] & 0xff);

    return String(code % 1000000).padStart(6, '0');
  }
}
```

---

## 7. Session Management

### Secure Session Configuration

```typescript
// auth/session.ts

import session from 'express-session';
import { SessionStore } from './session-store';

/**
 * Secure session configuration
 */
export class SessionManager {
  /**
   * Configure session middleware
   */
  configure(): session.SessionOptions {
    return {
      secret: process.env.SESSION_SECRET || crypto.randomBytes(32).toString('hex'),
      resave: false,
      saveUninitialized: false,
      name: 'sid',  // Generic name instead of 'connect.sid'
      cookie: {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 24 * 60 * 60 * 1000,  // 24 hours
        domain: process.env.SESSION_DOMAIN,
        path: '/'
      },
      store: new SessionStore({
        client: this.redisClient,
        prefix: 'sess:'
      }),
      rolling: true,  // Reset expiration on activity
      unset: 'destroy'
    };
  }

  /**
   * Create session for user
   */
  async createSession(userId: string, request: {
    ip: string;
    userAgent: string;
  }): Promise<string> {
    const sessionId = crypto.randomBytes(32).toString('hex');

    const sessionData = {
      userId,
      createdAt: new Date(),
      lastActivity: new Date(),
      ip: request.ip,
      userAgent: this.hashUserAgent(request.userAgent),
      devices: await this.getUserActiveSessions(userId)
    };

    await this.sessionStore.set(sessionId, sessionData, {
      ttl: 24 * 60 * 60  // 24 hours
    });

    return sessionId;
  }

  /**
   * Validate session
   */
  async validateSession(sessionId: string, request: {
    ip: string;
    userAgent: string;
  }): Promise<{ valid: boolean; userId?: string; reason?: string }> {
    const session = await this.sessionStore.get(sessionId);

    if (!session) {
      return { valid: false, reason: 'Session not found' };
    }

    // Check IP (allow for VPN/proxy changes)
    if (session.ip !== request.ip) {
      const ipChanged = await this.detectSuspiciousIPChange(session.ip, request.ip);
      if (ipChanged) {
        await this.alertSecurityTeam(userId, 'IP address changed');
        return { valid: false, reason: 'Session invalidated: IP changed' };
      }
    }

    // Check user agent
    const hashedUA = this.hashUserAgent(request.userAgent);
    if (session.userAgent !== hashedUA) {
      await this.alertSecurityTeam(userId, 'User agent changed');
      return { valid: false, reason: 'Session invalidated: User agent changed' };
    }

    // Update last activity
    session.lastActivity = new Date();
    await this.sessionStore.set(sessionId, session);

    return { valid: true, userId: session.userId };
  }

  /**
   * Invalidate all user sessions
   */
  async invalidateAllSessions(userId: string): Promise<void> {
    const sessions = await this.sessionStore.findByUserId(userId);

    for (const session of sessions) {
      await this.sessionStore.delete(session.id);
    }
  }

  /**
   * Detect concurrent sessions from different locations
   */
  async detectConcurrentSessions(userId: string): Promise<boolean {
    const sessions = await this.sessionStore.findByUserId(userId);
    const locations = new Set<string>();

    for (const session of sessions) {
      const location = await this.getLocationFromIP(session.ip);
      locations.add(location.country);
    }

    return locations.size > 2;
  }
}
```

---

## 8. Security Headers

### Middleware for Security Headers

```typescript
// middleware/headers.ts

import { Response, NextFunction } from 'express';
import { Request } from '../types';

/**
 * Security headers middleware
 */
export function securityHeaders(nonce?: string) {
  return (_req: Request, res: Response, next: NextFunction) => {
    // Prevent clickjacking
    res.setHeader('X-Frame-Options', 'DENY');

    // Prevent MIME type sniffing
    res.setHeader('X-Content-Type-Options', 'nosniff');

    // Enable XSS filter
    res.setHeader('X-XSS-Protection', '1; mode=block');

    // Restrict referrer information
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

    // Force HTTPS
    if (process.env.NODE_ENV === 'production') {
      res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
    }

    // Content Security Policy
    res.setHeader('Content-Security-Policy', getCSP(nonce));

    // Permissions policy
    res.setHeader('Permissions-Policy', getPermissionsPolicy());

    next();
  };
}

/**
 * Generate Content Security Policy
 */
function getCSP(nonce?: string): string {
  const isDev = process.env.NODE_ENV === 'development';

  const directives = [
    // Default policy
    `default-src 'self'`,

    // Scripts
    `script-src 'self'` +
      (nonce ? ` 'nonce-${nonce}'` : '') +
      (isDev ? " 'unsafe-inline' 'unsafe-eval'" : ""),

    // Styles
    `style-src 'self'` +
      (isDev ? " 'unsafe-inline'" : ""),

    // Images
    `img-src 'self' data: https: blob:`,

    // Fonts
    `font-src 'self' data:`,

    // Connect
    `connect-src 'self' ${process.env.API_URL || ''} ${process.env.WS_URL || ''}`,

    // Objects and embeds (disabled)
    `object-src 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    `frame-ancestors 'none'`,

    // Upgrade insecure requests
    `upgrade-insecure-requests`
  ];

  return directives.join('; ');
}

/**
 * Generate Permissions Policy
 */
function getPermissionsPolicy(): string {
  const policies = [
    'geolocation=()',
    'microphone=()',
    'camera=()',
    'payment=(self)',
    'usb=()',
    'bluetooth=()',
    'magnetometer=()',
    'gyroscope=()',
    'accelerometer=()',
    'ambient-light-sensor=()',
    'autoplay=(self)',
    'encrypted-media=(self)',
    'fullscreen=(self)',
    'picture-in-picture=(self)',
    'publickey-credentials-get=(self)'
  ];

  return policies.join(', ');
}
```

---

## 9. File Upload Security

### Secure File Upload

```typescript
// security/file-upload.ts

import multer from 'multer';
import path from 'path';

/**
 * Secure file upload configuration
 */
export class SecureFileUpload {
  /**
   * Configure multer with security constraints
   */
  configure(): multer.Multer {
    const storage = multer.memoryStorage();

    const fileFilter = (
      req: Request,
      file: Express.Multer.File,
      callback: multer.FileFilterCallback
    ) => {
      // Check file type
      const allowedTypes = [
        'image/jpeg',
        'image/png',
        'image/webp',
        'application/pdf'
      ];

      if (!allowedTypes.includes(file.mimetype)) {
        return callback(new Error('Invalid file type'));
      }

      // Check file extension
      const ext = path.extname(file.originalname).toLowerCase();
      const allowedExts = ['.jpg', '.jpeg', '.png', '.webp', '.pdf'];

      if (!allowedExts.includes(ext)) {
        return callback(new Error('Invalid file extension'));
      }

      // Check file name for path traversal
      if (file.originalname !== path.basename(file.originalname)) {
        return callback(new Error('Invalid filename'));
      }

      callback(null, true);
    };

    return multer({
      storage,
      fileFilter,
      limits: {
        fileSize: 5 * 1024 * 1024,  // 5MB
        files: 5  // Max 5 files
      }
    });
  }

  /**
   * Scan uploaded file for malware
   */
  async scanForMalware(buffer: Buffer): Promise<{
    clean: boolean;
    threats: string[];
  }> {
    // ClamAV integration or similar
    const result = await this.clamAV.scan(buffer);

    return {
      clean: result.isClean,
      threats: result.threats || []
    };
  }

  /**
   * Sanitize uploaded image
   */
  async sanitizeImage(buffer: Buffer, mimeType: string): Promise<Buffer> {
    // Use sharp to re-encode image (removes any malicious content)
    const image = sharp(buffer);

    // Convert to safe format
    const sanitized = await image
      .toFormat(mimeType === 'image/png' ? 'png' : 'jpeg')
      .toBuffer();

    return sanitized;
  }

  /**
   * Validate file content matches declared type
   */
  async validateContentType(
    buffer: Buffer,
    declaredType: string
  ): Promise<boolean> {
    // Detect actual file type from magic bytes
    const actualType = await this.detectFileType(buffer);

    return actualType === declaredType;
  }

  /**
   * Detect file type from magic bytes
   */
  private async detectFileType(buffer: Buffer): Promise<string> {
    const magic = buffer.slice(0, 12);

    // JPEG: FF D8 FF
    if (magic[0] === 0xFF && magic[1] === 0xD8 && magic[2] === 0xFF) {
      return 'image/jpeg';
    }

    // PNG: 89 50 4E 47 0D 0A 1A 0A
    if (magic[0] === 0x89 && magic[1] === 0x50 && magic[2] === 0x4E &&
        magic[3] === 0x47 && magic[4] === 0x0D && magic[5] === 0x0A) {
      return 'image/png';
    }

    // PDF: 25 50 44 46
    if (magic[0] === 0x25 && magic[1] === 0x50 && magic[2] === 0x44 && magic[3] === 0x46) {
      return 'application/pdf';
    }

    return 'application/octet-stream';
  }
}
```

---

## 10. Dependency Security

### Vulnerability Scanning

```typescript
// security/dependencies.ts

/**
 * Dependency vulnerability management
 */
export class DependencySecurity {
  /**
   * Scan dependencies for vulnerabilities
   */
  async scanDependencies(): Promise<VulnerabilityReport> {
    const dependencies = await this.getInstalledDependencies();
    const vulnerabilities: Vulnerability[] = [];

    for (const dep of dependencies) {
      const vulns = await this.checkVulnerabilityDatabase(dep.name, dep.version);
      vulnerabilities.push(...vulns);
    }

    // Group by severity
    const critical = vulnerabilities.filter(v => v.severity === 'critical');
    const high = vulnerabilities.filter(v => v.severity === 'high');
    const medium = vulnerabilities.filter(v => v.severity === 'medium');
    const low = vulnerabilities.filter(v => v.severity === 'low');

    return {
      total: vulnerabilities.length,
      critical: critical.length,
      high: high.length,
      medium: medium.length,
      low: low.length,
      vulnerabilities,
      scanDate: new Date()
    };
  }

  /**
   * Check if dependency has known vulnerabilities
   */
  async checkVulnerabilityDatabase(
    packageName: string,
    version: string
  ): Promise<Vulnerability[]> {
    // Query npm audit, OSV, or Snyk DB
    const response = await fetch(
      `https://osv.dev/v1/query?package=${packageName}&version=${version}`
    );

    const data = await response.json();

    return (data.vulns || []).map((vuln: any) => ({
      id: vuln.id,
      package: packageName,
      affectedVersion: version,
      severity: this.calculateSeverity(vuln),
      description: vuln.details,
      patchedVersions: vuln.affected?.[0]?.versions?.filter((v: string) =>
        this.versionCompare(v, version) > 0
      ),
      references: vuln.references?.map((r: any) => r.url) || []
    }));
  }

  /**
   * Generate security advisory for vulnerabilities
   */
  generateAdvisory(report: VulnerabilityReport): SecurityAdvisory {
    const actions: string[] = [];

    if (report.critical > 0) {
      actions.push('IMMEDIATE ACTION REQUIRED: Critical vulnerabilities detected. Update dependencies immediately.');
    }

    if (report.high > 0) {
      actions.push('Update high-severity vulnerabilities within 7 days.');
    }

    if (report.medium > 0) {
      actions.push('Plan updates for medium-severity vulnerabilities in next sprint.');
    }

    const affectedPackages = [...new Set(report.vulnerabilities.map(v => v.package))];

    return {
      severity: report.critical > 0 ? 'critical' :
               report.high > 0 ? 'high' :
               report.medium > 0 ? 'medium' : 'low',
      summary: `Found ${report.total} vulnerabilities in ${affectedPackages.length} packages`,
      actions,
      affectedPackages,
      vulnerabilities: report.vulnerabilities
    };
  }
}

/**
 * Automated dependency updates
 */
export class DependencyUpdater {
  /**
   * Check for security updates
   */
  async checkSecurityUpdates(): Promise<SecurityUpdate[]> {
    const updates: SecurityUpdate[] = [];

    const dependencies = await this.getDependencies();
    for (const dep of dependencies) {
      const latest = await this.getLatestVersion(dep.name);
      const vulns = await this.checkVulnerabilityDatabase(dep.name, dep.version);

      if (vulns.length > 0 && latest !== dep.version) {
        updates.push({
          package: dep.name,
          currentVersion: dep.version,
          updateVersion: latest,
          vulnerabilities: vulns,
          urgency: vulns.some(v => v.severity === 'critical') ? 'immediate' :
                     vulns.some(v => v.severity === 'high') ? 'high' : 'normal'
        });
      }
    }

    return updates.sort((a, b) => {
      const urgencyOrder = { immediate: 0, high: 1, normal: 2 };
      return urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
    });
  }

  /**
   * Create pull request for security update
   */
  async createSecurityPR(update: SecurityUpdate): Promise<string> {
    const branchName = `security/update-${update.package.replace('/', '-')}-${update.updateVersion}`;

    // Create branch
    await this.git.createBranch(branchName);

    // Update package.json
    await this.packageManager.update(update.package, update.updateVersion);

    // Run tests
    const testsPassed = await this.packageManager.test();

    if (!testsPassed) {
      await this.git.deleteBranch(branchName);
      throw new Error('Tests failed after update');
    }

    // Create PR
    const pr = await this.github.createPR({
      title: `Security: Update ${update.package} to ${update.updateVersion}`,
      body: this.generatePRBody(update),
      branch: branchName,
      labels: ['security', 'dependencies']
    });

    return pr.url;
  }

  private generatePRBody(update: SecurityUpdate): string {
    return `## Security Update

This PR updates \`${update.package}\` to version \`${update.updateVersion}\` to address the following vulnerabilities:

${update.vulnerabilities.map(v => `- **${v.id}**: ${v.description}`).join('\n')}

**Urgency**: ${update.urgency}

Please review and merge this update as soon as possible.
`;
  }
}
```

---

## 11. API Specification

### Security Endpoints

```typescript
// api/security.ts

/**
 * POST /api/auth/login
 * Login with username/password
 */
interface LoginRequest {
  email: string;
  password: string;
  mfaCode?: string;
  rememberMe?: boolean;
}

interface LoginResponse {
  success: boolean;
  requiresMFA?: boolean;
  mfaMethods?: MFAMethod[];
  token?: string;
  refreshToken?: string;
  user?: UserInfo;
}

/**
 * POST /api/auth/mfa/setup
 * Setup MFA for user
 */
interface MFAMethod {
  type: MFAMethod;
  name: string;
  enabled: boolean;
}

interface SetupMFARequest {
  method: MFAMethod;
}

interface SetupMFAResponse {
  qrCode?: string;  // For TOTP
  secret?: string;  // For TOTP
  backupCodes?: string[];  // For all methods
}

/**
 * POST /api/auth/mfa/verify
 * Verify MFA code
 */
interface VerifyMFARequest {
  method: MFAMethod;
  code: string;
}

interface VerifyMFAResponse {
  verified: boolean;
  token?: string;
}

/**
 * POST /api/auth/logout
 * Logout and invalidate session
 */
interface LogoutResponse {
  success: boolean;
}

/**
 * GET /api/auth/sessions
 * Get active sessions
 */
interface GetSessionsResponse {
  sessions: SessionInfo[];
}

interface SessionInfo {
  id: string;
  device: string;
  location: string;
  ip: string;
  lastActivity: string;
  current: boolean;
}

/**
 * DELETE /api/auth/sessions/:id
 * Invalidate specific session
 */
interface InvalidateSessionResponse {
  success: boolean;
}

/**
 * GET /api/security/vulnerabilities
 * Get dependency vulnerability report
 */
interface VulnerabilityReportResponse {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  vulnerabilities: Vulnerability[];
}
```

---

## 12. Testing Scenarios

### Security Tests

```typescript
// __tests__/security/application-security.test.ts

describe('Application Security', () => {
  describe('Input Validation', () => {
    it('should reject SQL injection attempts', async () => {
      const maliciousInput = "'; DROP TABLE users; --";

      const response = await app.request('/api/search', {
        method: 'POST',
        body: JSON.stringify({ query: maliciousInput })
      });

      // Should either reject or sanitize
      expect(response.status).not.toBe(500);  // No SQL error
    });

    it('should reject XSS attempts', async () => {
      const xssPayload = '<script>alert(document.cookie)</script>';

      const response = await app.request('/api/inquiry', {
        method: 'POST',
        body: JSON.stringify({
          customerInfo: { name: 'Test', email: 'test@example.com' },
          message: xssPayload
        })
      });

      const data = await response.json();

      // Message should be sanitized
      if (data.data?.message) {
        expect(data.data.message).not.toContain('<script>');
      }
    });

    it('should validate email format', async () => {
      const response = await app.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: 'not-an-email',
          password: 'password123'
        })
      });

      expect(response.status).toBe(400);
    });
  });

  describe('Authentication Security', () => {
    it('should lock account after failed attempts', async () => {
      const email = 'test@example.com';

      // Attempt 5 failed logins
      for (let i = 0; i < 5; i++) {
        await app.request('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({
            email,
            password: 'wrong-password'
          })
        });
      }

      // 6th attempt should be locked
      const response = await app.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password: 'password123'
        })
      });

      expect(response.status).toBe(429);
    });

    it('should require MFA when configured', async () => {
      const response = await app.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: 'mfa-user@example.com',
          password: 'password123'
        })
      });

      const data = await response.json();

      expect(data.requiresMFA).toBe(true);
      expect(data.mfaMethods).toBeDefined();
    });
  });

  describe('Session Security', () => {
    it('should invalidate session on IP change', async () => {
      const loginResponse = await app.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123'
        })
      });

      const { token } = await loginResponse.json();

      // Try to use session from different IP
      const response = await app.request('/api/user/profile', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Forwarded-For': '1.2.3.4'  // Different IP
        }
      });

      // Should be rejected or trigger security check
      expect([401, 403]).toContain(response.status);
    });

    it('should not allow session fixation', async () => {
      // Attempt to use known session ID
      const response = await app.request('/api/user/profile', {
        headers: {
          'Cookie': 'sid=attacker-controlled-session-id'
        }
      });

      expect(response.status).toBe(401);
    });
  });

  describe('File Upload Security', () => {
    it('should reject executable files', async () => {
      const form = new FormData();
      form.append('file', new File(['malicious'], 'test.exe', { type: 'application/x-msdownload' }));

      const response = await app.request('/api/upload', {
        method: 'POST',
        body: form
      });

      expect(response.status).toBe(400);
    });

    it('should validate file content type', async () => {
      // Upload PNG with JPEG extension
      const pngBuffer = await fs.readFile('test.png');

      const response = await app.request('/api/upload', {
        method: 'POST',
        body: createFormData('file.jpg', pngBuffer, 'image/jpeg')
      });

      // Should reject due to content mismatch
      expect(response.status).toBe(400);
    });
  });

  describe('Rate Limiting', () => {
    it('should rate limit login attempts', async () => {
      const requests = [];

      // Send 20 requests rapidly
      for (let i = 0; i < 20; i++) {
        requests.push(
          app.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({
              email: `test${i}@example.com`,
              password: 'password123'
            })
          })
        );
      }

      const responses = await Promise.all(requests);

      // At least some should be rate limited
      const rateLimited = responses.filter(r => r.status === 429);
      expect(rateLimited.length).toBeGreaterThan(0);
    });
  });
});
```

---

## Summary

This document defines application security practices for the Travel Agency Agent platform:

**Key Components:**
- **Threat Modeling** - Identification of potential security threats
- **OWASP Top 10 Mitigation** - Protection against common vulnerabilities
- **Input Validation** - Comprehensive request validation
- **Output Encoding** - XSS prevention through proper encoding
- **Authentication Security** - MFA, password policies
- **Session Management** - Secure session configuration
- **Security Headers** - CSP, HSTS, X-Frame-Options, etc.
- **File Upload Security** - Type validation, malware scanning
- **Dependency Security** - Vulnerability scanning and updates

**Next:** [SECURITY_02: API Security](./SECURITY_02_API_SECURITY.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-04-25
**Status:** ✅ Complete
