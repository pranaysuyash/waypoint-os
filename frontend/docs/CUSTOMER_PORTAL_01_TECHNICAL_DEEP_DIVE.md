# CUSTOMER_PORTAL_01: Technical Deep Dive

> Customer Portal — Architecture, Authentication, and Data Security

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Authentication and Authorization](#authentication-and-authorization)
4. [Data Access Control](#data-access-control)
5. [API Design](#api-design)
6. [State Management](#state-management)
7. [Security Considerations](#security-considerations)
8. [Performance Optimization](#performance-optimization)

---

## Overview

The Customer Portal is a secure, customer-facing interface that allows travelers to:
- View trip details and itineraries
- Access booking confirmations and documents
- Communicate with their travel agent
- Make payments and view invoices
- Provide feedback and reviews
- Update travel preferences

### Key Design Principles

```
┌────────────────────────────────────────────────────────────────────────────┐
│                      CUSTOMER PORTAL DESIGN PRINCIPLES                     │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  1. SECURITY FIRST                                                        │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Customer data isolation — no cross-customer visibility        │  │
│     │ • RBAC with least privilege                                    │  │
│     │ • Audit logging for all data access                            │  │
│     │ • Secure document storage with expiring links                  │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  2. SIMPLICITY OVER POWER                                                 │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Limited, focused feature set                                 │  │
│     │ • No editing capability — view only                            │  │
│     │ • Clear calls-to-action for agent communication                │  │
│     │ • Mobile-first responsive design                               │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  3. AGENCY BRANDING                                                       │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • White-label customization                                    │  │
│     │ • Agency logo, colors, domain                                  │  │
│     │ • Custom email templates                                       │  │
│     │ • Branded mobile apps (optional)                               │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  4. SELF-SERVICE WHERE APPROPRIATE                                        │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Document downloads                                            │  │
│     │ • Payment links                                                 │  │
│     │ • Preference updates                                            │  │
│     │ • Messaging                                                     │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  5. AGENT COLLABORATION                                                   │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Real-time sync with agent workspace                          │  │
│     │ • Shared message history                                       │  │
│     │ • Agent notifications for customer actions                     │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Scope and Boundaries

| Feature | Included | Excluded |
|---------|----------|----------|
| Trip viewing | ✅ | Trip editing |
| Document access | ✅ | Document creation |
| Messaging | ✅ | Direct agent calls |
| Payments | ✅ (via links) | Refunds |
| Preferences | ✅ | Account deletion |
| Reviews | ✅ | Dispute resolution |
| Trip history | ✅ | Cancellation (via request) |

---

## System Architecture

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER PORTAL ARCHITECTURE                        │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                        CLIENT LAYER                                │  │
│   │                                                                    │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│   │  │   Web App   │  │ Mobile Web  │  │  Native App │               │  │
│   │  │  (React)    │  │ (PWA/React) │  │ (Optional)  │               │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘               │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                      API GATEWAY / CDN                              │  │
│   │                                                                    │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│   │  │    CDN      │  │   WAF       │  │   DDoS      │               │  │
│   │  │ (Static)    │  │ (Security)  │  │ Protection  │               │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘               │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                    CUSTOMER PORTAL API                             │  │
│   │                                                                    │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│   │  │     Auth    │  │   Trips     │  │  Messages   │               │  │
│   │  │   Service   │  │   Service   │  │   Service   │               │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘               │  │
│   │                                                                    │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│   │  │  Documents  │  │  Payments   │  │  Profile    │               │  │
│   │  │   Service   │  │   Service   │  │   Service   │               │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘               │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                      SHARED SERVICES LAYER                          │  │
│   │                                                                    │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│   │  │   Spine     │  │  Document   │  │  Payment    │               │  │
│   │  │    API      │  │   Store     │  │  Gateway    │               │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘               │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│                                  ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                       DATA LAYER                                   │  │
│   │                                                                    │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │
│   │  │ PostgreSQL  │  │    Redis    │  │   S3/MinIO  │               │  │
│   │  │  (Trips)    │  │  (Cache)    │  │ (Documents) │               │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘               │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

```typescript
// tech-stack.ts
const CUSTOMER_PORTAL_STACK = {
  // Frontend
  frontend: {
    framework: 'React 18',
    routing: 'React Router v6',
    state: 'Zustand + React Query',
    styling: 'Tailwind CSS',
    ui: 'shadcn/ui (customized)',
    forms: 'React Hook Form + Zod',
    i18n: 'i18next',
    testing: 'Vitest + Testing Library',
    build: 'Vite',
    pwa: 'Vite PWA Plugin',
  },

  // Backend
  backend: {
    runtime: 'Node.js 20 LTS',
    framework: 'Fastify',
    validation: 'Zod',
    orm: 'Prisma',
    auth: 'Auth.js (custom adapter)',
  },

  // Infrastructure
  infrastructure: {
    hosting: 'Vercel / AWS Lambda',
    cdn: 'Cloudflare',
    database: 'Amazon RDS PostgreSQL',
    cache: 'Amazon ElastiCache Redis',
    storage: 'Amazon S3',
    dns: 'Amazon Route 53',
    ssl: 'Let\'s Encrypt / AWS ACM',
  },

  // Monitoring
  monitoring: {
    logs: 'Datadog / CloudWatch',
    metrics: 'Datadog / Prometheus',
    errors: 'Sentry',
    uptime: 'Pingdom / UptimeRobot',
  },
};
```

---

## Authentication and Authorization

### Authentication Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER AUTH FLOW                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     │
│  │   CUSTOMER      │────▶│   PORTAL APP    │────▶│   AUTH SERVICE  │     │
│  │                 │     │                 │     │                 │     │
│  │  • Email        │     │  • Initiate     │     │  • Verify      │     │
│  │  • Phone        │     │  • Handle       │     │  • Generate    │     │
│  │  • Magic Link   │     │    Callback    │     │    Token       │     │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘     │
│           │                       │                       │               │
│           │                       │                       │               │
│           ▼                       ▼                       ▼               │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     │
│  │   CHANNEL       │     │    SESSION      │     │    TOKEN        │     │
│  │                 │     │    STORE        │     │    STORE        │     │
│  │  • Email        │     │  • HTTP-only   │     │  • Access      │     │
│  │  • SMS          │     │    Cookie      │     │    Token       │     │
│  │  • WhatsApp     │     │  • Secure      │     │  • Refresh     │     │
│  │                 │     │    Flag        │     │    Token       │     │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘     │
│                                                                            │
│  FLOW:                                                                     │
│  1. Customer enters email/phone → Request OTP/Magic Link                  │
│  2. System sends OTP via email/WhatsApp/SMS                               │
│  3. Customer submits OTP                                                  │
│  4. System validates → Creates session → Sets cookie → Redirects          │
│  5. Subsequent requests include session cookie                            │
│  6. Session validated on each request                                     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Authentication Implementation

```typescript
// auth/customer_auth.service.ts
import { JWTPayload, SignJWT, jwtVerify } from 'jose';
import { TimeSpan } from 'oslo';

interface CustomerAuthConfig {
  tokenSecret: string;
  accessTokenTTL: TimeSpan;
  refreshTokenTTL: TimeSpan;
  otpTTL: TimeSpan;
  maxAttempts: number;
  lockoutDuration: TimeSpan;
}

class CustomerAuthService {
  private config: CustomerAuthConfig;

  constructor(config: CustomerAuthConfig) {
    this.config = config;
  }

  // === OTP Generation and Verification ===

  async initiateLogin(identifier: string, channel: 'email' | 'phone' | 'whatsapp'): Promise<void> {
    // Check rate limiting
    const attempts = await this.getRecentAttempts(identifier);
    if (attempts >= this.config.maxAttempts) {
      throw new AuthError('Too many attempts. Please try again later.');
    }

    // Generate OTP
    const otp = this.generateOTP();
    const expiry = new Date(Date.now() + this.config.otpTTL.inMilliseconds());

    // Store OTP hash
    await this.storeOTP(identifier, otp, expiry);

    // Send via appropriate channel
    switch (channel) {
      case 'email':
        await this.emailService.send({
          to: identifier,
          template: 'otp-login',
          data: { otp },
        });
        break;
      case 'phone':
        await this.smsService.send({
          to: identifier,
          message: `Your verification code is: ${otp}`;
        });
        break;
      case 'whatsapp':
        await this.whatsappService.send({
          to: identifier,
          template: 'otp_login',
          data: { otp },
        });
        break;
    }

    // Log attempt
    await this.logAttempt(identifier, 'initiated');
  }

  async verifyOTP(identifier: string, otp: string): Promise<AuthResult> {
    // Retrieve stored OTP
    const stored = await this.getStoredOTP(identifier);
    if (!stored) {
      throw new AuthError('Invalid or expired code');
    }

    // Verify OTP
    const isValid = await this.compareOTP(otp, stored.hash);
    if (!isValid) {
      await this.logAttempt(identifier, 'failed');
      throw new AuthError('Invalid code');
    }

    // Check expiry
    if (stored.expiry < new Date()) {
      throw new AuthError('Code expired');
    }

    // Get or create customer
    let customer = await this.customerService.findByIdentifier(identifier);
    if (!customer) {
      customer = await this.customerService.create({ identifier, channel: identifier.includes('@') ? 'email' : 'phone' });
    }

    // Generate tokens
    const accessToken = await this.generateAccessToken(customer);
    const refreshToken = await this.generateRefreshToken(customer);

    // Create session
    const session = await this.createSession(customer.id, refreshToken);

    // Clear OTP
    await this.clearOTP(identifier);

    // Log successful login
    await this.logAttempt(identifier, 'success');

    return {
      accessToken,
      refreshToken,
      customer: this.sanitizeCustomer(customer),
      expiresAt: new Date(Date.now() + this.config.accessTokenTTL.inMilliseconds()),
    };
  }

  // === Token Management ===

  private async generateAccessToken(customer: Customer): Promise<string> {
    const payload: JWTPayload = {
      sub: customer.id,
      typ: 'access',
      iat: Date.now(),
      exp: Date.now() + this.config.accessTokenTTL.inMilliseconds(),
      // Customer-specific claims
      'https://travel.app/customer': true,
      'https://travel.app/agency': customer.agencyId,
    };

    const secret = new TextEncoder().encode(this.config.tokenSecret);
    return await new SignJWT(payload)
      .setProtectedHeader({ alg: 'HS256', typ: 'JWT' })
      .setIssuedAt()
      .setExpirationTime(this.config.accessTokenTTL.inSeconds() + 's')
      .sign(secret);
  }

  private async generateRefreshToken(customer: Customer): Promise<string> {
    const payload: JWTPayload = {
      sub: customer.id,
      typ: 'refresh',
      iat: Date.now(),
      exp: Date.now() + this.config.refreshTokenTTL.inMilliseconds(),
    };

    const secret = new TextEncoder().encode(this.config.tokenSecret);
    return await new SignJWT(payload)
      .setProtectedHeader({ alg: 'HS256', typ: 'JWT' })
      .setIssuedAt()
      .setExpirationTime(this.config.refreshTokenTTL.inSeconds() + 's')
      .sign(secret);
  }

  async refreshAccessToken(refreshToken: string): Promise<string> {
    // Verify refresh token
    const secret = new TextEncoder().encode(this.config.tokenSecret);
    const { payload } = await jwtVerify(refreshToken, secret);

    if (payload.typ !== 'refresh') {
      throw new AuthError('Invalid token type');
    }

    // Check if session is valid
    const session = await this.getSession(payload.sub as string, refreshToken);
    if (!session || session.revoked) {
      throw new AuthError('Invalid session');
    }

    // Get customer
    const customer = await this.customerService.getById(payload.sub as string);
    if (!customer) {
      throw new AuthError('Customer not found');
    }

    // Generate new access token
    return await this.generateAccessToken(customer);
  }

  async revokeSession(customerId: string, refreshToken: string): Promise<void> {
    await this.db.query(
      'UPDATE customer_sessions SET revoked = true WHERE customer_id = $1 AND refresh_token = $2',
      [customerId, refreshToken]
    );
  }

  async revokeAllSessions(customerId: string): Promise<void> {
    await this.db.query(
      'UPDATE customer_sessions SET revoked = true WHERE customer_id = $1',
      [customerId]
    );
  }

  // === Session Management ===

  private async createSession(customerId: string, refreshToken: string): Promise<CustomerSession> {
    const session: CustomerSession = {
      id: crypto.randomUUID(),
      customerId,
      refreshToken,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + this.config.refreshTokenTTL.inMilliseconds()),
      revoked: false,
      userAgent: '', // From request context
      ipAddress: '', // From request context
    };

    await this.db.query(`
      INSERT INTO customer_sessions (id, customer_id, refresh_token, expires_at, user_agent, ip_address)
      VALUES ($1, $2, $3, $4, $5, $6)
    `, [session.id, customerId, refreshToken, session.expiresAt, session.userAgent, session.ipAddress]);

    return session;
  }

  async validateSession(accessToken: string): Promise<Customer | null> {
    try {
      const secret = new TextEncoder().encode(this.config.tokenSecret);
      const { payload } = await jwtVerify(accessToken, secret);

      if (payload.typ !== 'access') {
        return null;
      }

      // Verify customer still exists and is active
      const customer = await this.customerService.getById(payload.sub as string);
      if (!customer || customer.status !== 'active') {
        return null;
      }

      return customer;
    } catch {
      return null;
    }
  }

  // === OTP Helpers ===

  private generateOTP(): string {
    // Generate 6-digit numeric OTP
    return Math.floor(100000 + Math.random() * 900000).toString();
  }

  private async storeOTP(identifier: string, otp: string, expiry: Date): Promise<void> {
    const hash = await this.hashOTP(otp);
    await this.redis.setex(
      `otp:${identifier}`,
      Math.floor(this.config.otpTTL.inSeconds()),
      JSON.stringify({ hash, expiry })
    );
  }

  private async getStoredOTP(identifier: string): Promise<{ hash: string; expiry: Date } | null> {
    const data = await this.redis.get(`otp:${identifier}`);
    return data ? JSON.parse(data) : null;
  }

  private async clearOTP(identifier: string): Promise<void> {
    await this.redis.del(`otp:${identifier}`);
  }

  private async hashOTP(otp: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(otp + this.config.tokenSecret);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  private async compareOTP(otp: string, hash: string): Promise<boolean> {
    const otpHash = await this.hashOTP(otp);
    return otpHash === hash;
  }

  // === Rate Limiting ===

  private async getRecentAttempts(identifier: string): Promise<number> {
    const key = `attempts:${identifier}`;
    const count = await this.redis.get(key);
    return parseInt(count || '0', 10);
  }

  private async logAttempt(identifier: string, result: 'initiated' | 'success' | 'failed'): Promise<void> {
    const key = `attempts:${identifier}`;

    if (result === 'success') {
      // Clear on success
      await this.redis.del(key);
    } else if (result === 'failed') {
      // Increment counter
      await this.redis.incr(key);
      await this.redis.expire(key, this.config.lockoutDuration.inSeconds());
    }
  }

  // === Sanitization ===

  private sanitizeCustomer(customer: Customer): Partial<Customer> {
    const { passwordHash, ...sanitized } = customer;
    return sanitized;
  }
}

interface AuthResult {
  accessToken: string;
  refreshToken: string;
  customer: Partial<Customer>;
  expiresAt: Date;
}

interface Customer {
  id: string;
  agencyId: string;
  email?: string;
  phone?: string;
  whatsapp?: string;
  status: 'active' | 'suspended' | 'deleted';
  name?: string;
  createdAt: Date;
}

interface CustomerSession {
  id: string;
  customerId: string;
  refreshToken: string;
  createdAt: Date;
  expiresAt: Date;
  revoked: boolean;
  userAgent: string;
  ipAddress: string;
}

class AuthError extends Error {
  constructor(message: string, public code: string = 'AUTH_ERROR') {
    super(message);
    this.name = 'AuthError';
  }
}
```

### Authorization Model

```typescript
// auth/authorization.ts
interface CustomerPermissions {
  // Trip permissions
  canViewTrip: (tripId: string) => Promise<boolean>;
  canViewTrips: (filter: TripFilter) => Promise<boolean>;

  // Document permissions
  canViewDocument: (documentId: string) => Promise<boolean>;
  canDownloadDocument: (documentId: string) => Promise<boolean>;

  // Message permissions
  canSendMessage: () => boolean;
  canViewMessages: (tripId: string) => Promise<boolean>;

  // Payment permissions
  canViewPayment: (paymentId: string) => Promise<boolean>;
  canInitiatePayment: (tripId: string) => Promise<boolean>;

  // Profile permissions
  canUpdateProfile: () => boolean;
  canDeleteAccount: () => boolean;
}

class CustomerAuthorizationService implements CustomerPermissions {
  constructor(
    private db: Database,
    private customer: Customer
  ) {}

  async canViewTrip(tripId: string): Promise<boolean> {
    // Customer can view trip if they are linked to it
    const result = await this.db.query(`
      SELECT 1 FROM trip_customers
      WHERE trip_id = $1 AND customer_id = $2
      LIMIT 1
    `, [tripId, this.customer.id]);

    return result.length > 0;
  }

  async canViewTrips(filter: TripFilter): Promise<boolean> {
    // Customer can only view their own trips
    // Filter is automatically scoped to customer's trips
    return true;
  }

  async canViewDocument(documentId: string): Promise<boolean> {
    // Customer can view document if it's attached to their trip
    const result = await this.db.query(`
      SELECT 1 FROM trip_documents td
      JOIN trip_customers tc ON tc.trip_id = td.trip_id
      WHERE td.document_id = $1 AND tc.customer_id = $2
      LIMIT 1
    `, [documentId, this.customer.id]);

    return result.length > 0;
  }

  async canDownloadDocument(documentId: string): Promise<boolean> {
    // Same as view for now, but could add additional restrictions
    return await this.canViewDocument(documentId);
  }

  async canSendMessage(): Promise<boolean> {
    // All authenticated customers can send messages
    return true;
  }

  async canViewMessages(tripId: string): Promise<boolean> {
    // Customer can view messages for their trips
    const result = await this.db.query(`
      SELECT 1 FROM trip_customers
      WHERE trip_id = $1 AND customer_id = $2
      LIMIT 1
    `, [tripId, this.customer.id]);

    return result.length > 0;
  }

  async canViewPayment(paymentId: string): Promise<boolean> {
    // Customer can view payment if it's for their trip
    const result = await this.db.query(`
      SELECT 1 FROM payments p
      JOIN trip_customers tc ON tc.trip_id = p.trip_id
      WHERE p.id = $1 AND tc.customer_id = $2
      LIMIT 1
    `, [paymentId, this.customer.id]);

    return result.length > 0;
  }

  async canInitiatePayment(tripId: string): Promise<boolean> {
    // Customer can initiate payment if:
    // 1. Trip belongs to them
    // 2. Trip is in appropriate status
    // 3. There's an outstanding balance

    const trip = await this.db.query(`
      SELECT t.status, t.total_amount, t.paid_amount
      FROM trips t
      JOIN trip_customers tc ON tc.trip_id = t.id
      WHERE t.id = $1 AND tc.customer_id = $2
    `, [tripId, this.customer.id]);

    if (trip.length === 0) return false;

    const { status, total_amount, paid_amount } = trip[0];
    const balance = total_amount - paid_amount;

    return (
      ['quoted', 'confirmed', 'partially_paid'].includes(status) &&
      balance > 0
    );
  }

  async canUpdateProfile(): Promise<boolean> {
    return true;
  }

  async canDeleteAccount(): Promise<boolean> {
    // Account deletion requires additional confirmation
    // and verification that there are no active trips
    const activeTrips = await this.db.query(`
      SELECT COUNT(*) as count
      FROM trip_customers tc
      JOIN trips t ON t.id = tc.trip_id
      WHERE tc.customer_id = $1
        AND t.status NOT IN ('completed', 'cancelled', 'lost')
    `, [this.customer.id]);

    return activeTrips[0].count === 0;
  }
}

// Authorization middleware
export function authorizeCustomer(permission: keyof CustomerPermissions) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const customer = req.customer; // Set by auth middleware
    const authz = new CustomerAuthorizationService(req.db, customer);

    // Get the tripId/messageId/paymentId from request params
    const resourceId = req.params.tripId || req.params.documentId || req.params.paymentId;

    // Check permission
    const hasPermission = await authz[permission](resourceId);
    if (!hasPermission) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'You do not have permission to access this resource',
      });
    }

    next();
  };
}
```

---

## Data Access Control

### Data Filtering Layer

```typescript
// data/customer_data_filter.ts
class CustomerDataFilter {
  /**
   * Filters trip data to only include what the customer should see
   * This is a critical security function — never skip this!
   */
  filterTrip(trip: Trip): CustomerTripView {
    return {
      // Always include
      id: trip.id,
      status: trip.status,
      createdAt: trip.createdAt,

      // Trip details (filtered)
      name: trip.name,
      destination: trip.destination,
      departureDate: trip.departureDate,
      returnDate: trip.returnDate,
      duration: trip.duration,
      travelers: trip.travelers,

      // Pricing (show only if status >= quoted)
      totalAmount: this.shouldShowPrice(trip.status) ? trip.totalAmount : undefined,
      paidAmount: this.shouldShowPrice(trip.status) ? trip.paidAmount : undefined,

      // Agent info (anonymized if needed)
      agent: trip.agent ? {
        id: trip.agent.id,
        name: trip.agent.name,
        photo: trip.agent.photo,
        email: trip.agency.settings.showAgentEmail ? trip.agent.email : undefined,
      } : undefined,

      // Agency info
      agency: {
        name: trip.agency.name,
        logo: trip.agency.logo,
        phone: trip.agency.phone,
        email: trip.agency.email,
      },

      // Exclude internal fields
      // - priority
      // - assignedTo
      // - source
      // - tags
      // - internalNotes
      // - commission
      // - costPrice
      // - margin
    };
  }

  /**
   * Filters document access based on customer visibility settings
   */
  filterDocument(document: Document): CustomerDocumentView | null {
    // Check if document is customer-visible
    if (!document.customerVisible) {
      return null;
    }

    return {
      id: document.id,
      name: document.name,
      type: document.type,
      category: document.category,
      createdAt: document.createdAt,

      // Download link is generated on-demand with expiry
      downloadUrl: null,

      // Thumbnails for images
      thumbnailUrl: document.thumbnailUrl,

      // Exclude internal fields
      // - internalPath
      // - storageLocation
      // - checksum
    };
  }

  /**
   * Filters messages — customers see all communications
   */
  filterMessage(message: Message): CustomerMessageView {
    return {
      id: message.id,
      tripId: message.tripId,
      direction: message.direction, // 'inbound' | 'outbound'
      channel: message.channel,
      content: message.content,

      // Sender info
      sender: message.sender.role === 'agent'
        ? { name: message.sender.name, role: 'agent' }
        : { name: 'You', role: 'customer' },

      sentAt: message.sentAt,
      readAt: message.readAt,

      // Attachments (filtered)
      attachments: message.attachments
        .filter(a => a.customerVisible)
        .map(a => ({
          id: a.id,
          name: a.name,
          type: a.type,
          size: a.size,
          downloadUrl: null, // Generated on-demand
        })),
    };
  }

  /**
   * Filters payment data
   */
  filterPayment(payment: Payment): CustomerPaymentView {
    return {
      id: payment.id,
      tripId: payment.tripId,
      amount: payment.amount,
      currency: payment.currency,
      status: payment.status,
      createdAt: payment.createdAt,

      // Show payment method if completed
      method: payment.status === 'completed' ? {
        type: payment.method.type,
        last4: payment.method.last4,
        brand: payment.method.brand,
      } : undefined,

      // Exclude internal fields
      // - transactionId
      // - fee
      // - refundInfo
      // - metadata
    };
  }

  private shouldShowPrice(status: TripStatus): boolean {
    return ['quoted', 'confirmed', 'partially_paid', 'paid', 'completed'].includes(status);
  }
}

// Type definitions for filtered views
interface CustomerTripView {
  id: string;
  status: TripStatus;
  createdAt: Date;
  name: string;
  destination: Destination;
  departureDate: Date;
  returnDate: Date;
  duration: number;
  travelers: Traveler[];
  totalAmount?: number;
  paidAmount?: number;
  agent?: {
    id: string;
    name: string;
    photo?: string;
    email?: string;
  };
  agency: {
    name: string;
    logo?: string;
    phone?: string;
    email?: string;
  };
}

interface CustomerDocumentView {
  id: string;
  name: string;
  type: string;
  category: string;
  createdAt: Date;
  downloadUrl: string | null;
  thumbnailUrl?: string;
}

interface CustomerMessageView {
  id: string;
  tripId: string;
  direction: 'inbound' | 'outbound';
  channel: 'email' | 'whatsapp' | 'sms' | 'web';
  content: string;
  sender: { name: string; role: 'agent' | 'customer' };
  sentAt: Date;
  readAt: Date | null;
  attachments: Array<{
    id: string;
    name: string;
    type: string;
    size: number;
    downloadUrl: string | null;
  }>;
}

interface CustomerPaymentView {
  id: string;
  tripId: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  createdAt: Date;
  method?: {
    type: string;
    last4?: string;
    brand?: string;
  };
}
```

### Database Row-Level Security

```sql
-- PostgreSQL Row-Level Security for customer data

-- Enable RLS on trips table
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;

-- Policy: Customers can only view trips they're associated with
CREATE POLICY customer_trips_select ON trips
  FOR SELECT
  TO authenticated_customer_role
  USING (
    id IN (
      SELECT trip_id FROM trip_customers WHERE customer_id = current_customer_id()
    )
  );

-- Enable RLS on documents
ALTER TABLE trip_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY customer_documents_select ON trip_documents
  FOR SELECT
  TO authenticated_customer_role
  USING (
    customer_visible = true
    AND trip_id IN (
      SELECT trip_id FROM trip_customers WHERE customer_id = current_customer_id()
    )
  );

-- Enable RLS on messages
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY customer_messages_select ON messages
  FOR SELECT
  TO authenticated_customer_role
  USING (
    trip_id IN (
      SELECT trip_id FROM trip_customers WHERE customer_id = current_customer_id()
    )
  );

-- Enable RLS on payments
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

CREATE POLICY customer_payments_select ON payments
  FOR SELECT
  TO authenticated_customer_role
  USING (
    trip_id IN (
      SELECT trip_id FROM trip_customers WHERE customer_id = current_customer_id()
    )
  );

-- Function to get current customer ID from JWT
CREATE OR REPLACE FUNCTION current_customer_id()
RETURNS uuid AS $$
  SELECT NULLIF(current_setting('jwt.claims', true)::json->>'sub', '')::uuid;
$$ LANGUAGE sql SECURITY DEFINER;
```

---

## API Design

### API Structure

```
/api/v1/customer
├── /auth
│   ├── POST   /initiate          - Start login (send OTP)
│   ├── POST   /verify            - Verify OTP and get tokens
│   ├── POST   /refresh           - Refresh access token
│   └── POST   /logout            - Revoke session
├── /trips
│   ├── GET    /                  - List customer's trips
│   ├── GET    /:id               - Get trip details
│   ├── GET    /:id/itinerary     - Get trip itinerary
│   └── GET    /:id/timeline      - Get trip timeline
├── /documents
│   ├── GET    /                  - List accessible documents
│   ├── GET    /:id               - Get document metadata
│   └── GET    /:id/download      - Get download link
├── /messages
│   ├── GET    /                  - List message threads
│   ├── GET    /:tripId           - Get messages for trip
│   ├── POST   /:tripId           - Send message
│   └── POST   /:tripId/read      - Mark messages as read
├── /payments
│   ├── GET    /                  - List payment history
│   ├── GET    /:id               - Get payment details
│   ├── POST   /:tripId/link      - Generate payment link
│   └── GET    /:tripId/balance   - Get outstanding balance
├── /profile
│   ├── GET    /                  - Get customer profile
│   ├── PUT    /                  - Update profile
│   ├── PUT    /preferences       - Update preferences
│   └── POST   /deactivate        - Request account deactivation
└── /reviews
    ├── GET    /:tripId           - Get review form
    └── POST   /:tripId           - Submit review
```

### API Implementation

```typescript
// api/customer/trips.ts
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';

export async function customerTripsRoutes(fastify: FastifyInstance) {
  const dataFilter = new CustomerDataFilter();

  // GET /api/v1/customer/trips - List customer's trips
  fastify.get('/trips', {
    preHandler: [fastify.authenticate, fastify.authorizeCustomer],
    schema: {
      querystring: z.object({
        status: z.enum(['all', 'active', 'upcoming', 'completed', 'cancelled']).optional(),
        sort: z.enum(['created', 'departure', 'name']).optional(),
        order: z.enum(['asc', 'desc']).optional(),
        limit: z.coerce.number().min(1).max(100).optional(),
        offset: z.coerce.number().min(0).optional(),
      }),
    },
  }, async (req, reply) => {
    const customer = req.customer;
    const { status = 'active', sort = 'departure', order = 'asc', limit = 20, offset = 0 } = req.query;

    // Build query with customer scoping
    const result = await fastify.db.query(`
      SELECT t.*
      FROM trips t
      JOIN trip_customers tc ON tc.trip_id = t.id
      WHERE tc.customer_id = $1
        ${status !== 'all' ? 'AND t.status = $2' : ''}
      ORDER BY ${sort === 'departure' ? 't.departure_date' : sort === 'created' ? 't.created_at' : 't.name'} ${order}
      LIMIT $${status !== 'all' ? 3 : 2} OFFSET $${status !== 'all' ? 4 : 3}
    `, status !== 'all' ? [customer.id, status, limit, offset] : [customer.id, limit, offset]);

    // Filter data for customer consumption
    const trips = result.map(trip => dataFilter.filterTrip(trip));

    reply.send({
      trips,
      pagination: {
        limit,
        offset,
        total: result.length,
      },
    });
  });

  // GET /api/v1/customer/trips/:id - Get trip details
  fastify.get('/trips/:id', {
    preHandler: [fastify.authenticate, fastify.authorizeCustomer],
  }, async (req, reply) => {
    const customer = req.customer;
    const tripId = req.params.id;

    // Verify customer has access to this trip
    const hasAccess = await fastify.db.query(`
      SELECT 1 FROM trip_customers
      WHERE trip_id = $1 AND customer_id = $2
      LIMIT 1
    `, [tripId, customer.id]);

    if (hasAccess.length === 0) {
      return reply.status(404).send({
        error: 'Not Found',
        message: 'Trip not found',
      });
    }

    // Get trip with related data
    const trip = await fastify.db.query(`
      SELECT t.*,
        json_build_object(
          'id', a.id,
          'name', a.name,
          'photo', a.photo,
          'email', CASE WHEN ag.show_agent_email THEN a.email ELSE NULL END
        ) as agent,
        json_build_object(
          'name', ag.name,
          'logo', ag.logo,
          'phone', ag.phone,
          'email', ag.email
        ) as agency
      FROM trips t
      LEFT JOIN agents a ON a.id = t.assigned_to
      LEFT JOIN agencies ag ON ag.id = t.agency_id
      WHERE t.id = $1
    `, [tripId]);

    if (trip.length === 0) {
      return reply.status(404).send({
        error: 'Not Found',
        message: 'Trip not found',
      });
    }

    // Filter and send
    reply.send(dataFilter.filterTrip(trip[0]));
  });

  // GET /api/v1/customer/trips/:id/itinerary - Get trip itinerary
  fastify.get('/trips/:id/itinerary', {
    preHandler: [fastify.authenticate, fastify.authorizeCustomer],
  }, async (req, reply) => {
    const customer = req.customer;
    const tripId = req.params.id;

    // Verify access
    const trip = await fastify.getTripForCustomer(tripId, customer.id);
    if (!trip) {
      return reply.status(404).send({ error: 'Not Found' });
    }

    // Get itinerary items
    const items = await fastify.db.query(`
      SELECT
        id,
        type,
        name,
        description,
        start_time,
        end_time,
        location,
        booking_reference,
        status
      FROM itinerary_items
      WHERE trip_id = $1
      ORDER BY start_time ASC
    `, [tripId]);

    reply.send({
      tripId,
      items,
    });
  });

  // GET /api/v1/customer/trips/:id/timeline - Get trip timeline
  fastify.get('/trips/:id/timeline', {
    preHandler: [fastify.authenticate, fastify.authorizeCustomer],
  }, async (req, reply) => {
    const customer = req.customer;
    const tripId = req.params.id;

    // Verify access
    const trip = await fastify.getTripForCustomer(tripId, customer.id);
    if (!trip) {
      return reply.status(404).send({ error: 'Not Found' });
    }

    // Get timeline events (filtered for customer)
    const events = await fastify.db.query(`
      SELECT
        id,
        type,
        title,
        description,
        created_at,
        created_by,
        visible_to_customer
      FROM trip_events
      WHERE trip_id = $1 AND visible_to_customer = true
      ORDER BY created_at ASC
    `, [tripId]);

    // Map to customer-friendly format
    const timeline = events.map(event => ({
      id: event.id,
      type: event.type,
      title: event.title,
      description: event.description,
      timestamp: event.created_at,
      actor: event.created_by === 'system' ? 'System' : 'Agent',
    }));

    reply.send({ timeline });
  });
}

// api/customer/documents.ts
export async function customerDocumentsRoutes(fastify: FastifyInstance) {
  const dataFilter = new CustomerDataFilter();
  const documentStore = new DocumentStore();

  // GET /api/v1/customer/documents - List accessible documents
  fastify.get('/documents', {
    preHandler: [fastify.authenticate, fastify.authorizeCustomer],
    schema: {
      querystring: z.object({
        tripId: z.string().uuid().optional(),
        category: z.enum(['invoice', 'itinerary', 'ticket', 'visa', 'passport', 'other']).optional(),
        limit: z.coerce.number().min(1).max(100).optional(),
      }),
    },
  }, async (req, reply) => {
    const customer = req.customer;
    const { tripId, category, limit = 50 } = req.query;

    // Build query
    let query = `
      SELECT DISTINCT td.*
      FROM trip_documents td
      JOIN trip_customers tc ON tc.trip_id = td.trip_id
      WHERE tc.customer_id = $1
        AND td.customer_visible = true
    `;
    const params: unknown[] = [customer.id];

    let paramIndex = 2;
    if (tripId) {
      query += ` AND td.trip_id = $${paramIndex++}`;
      params.push(tripId);
    }
    if (category) {
      query += ` AND td.category = $${paramIndex++}`;
      params.push(category);
    }

    query += ` ORDER BY td.created_at DESC LIMIT $${paramIndex++}`;
    params.push(limit);

    const documents = await fastify.db.query(query, params);

    // Filter for customer
    const filtered = documents
      .map(doc => dataFilter.filterDocument(doc))
      .filter((doc): doc is CustomerDocumentView => doc !== null);

    reply.send({ documents: filtered });
  });

  // GET /api/v1/customer/documents/:id/download - Get download link
  fastify.get('/documents/:id/download', {
    preHandler: [fastify.authenticate, fastify.authorizeCustomer],
  }, async (req, reply) => {
    const customer = req.customer;
    const documentId = req.params.id;

    // Get document with access check
    const document = await fastify.db.query(`
      SELECT td.*
      FROM trip_documents td
      JOIN trip_customers tc ON tc.trip_id = td.trip_id
      WHERE td.id = $1
        AND tc.customer_id = $2
        AND td.customer_visible = true
      LIMIT 1
    `, [documentId, customer.id]);

    if (document.length === 0) {
      return reply.status(404).send({
        error: 'Not Found',
        message: 'Document not found',
      });
    }

    const doc = document[0];

    // Generate expiring download link
    const downloadUrl = await documentStore.getExpiringLink(doc.storage_key, {
      expiresIn: 300, // 5 minutes
      disposition: 'attachment',
    });

    // Log download
    await fastify.db.query(`
      INSERT INTO document_access_logs (document_id, customer_id, accessed_at, ip_address)
      VALUES ($1, $2, NOW(), $3)
    `, [documentId, customer.id, req.ip]);

    reply.send({
      documentId,
      downloadUrl,
      expiresAt: new Date(Date.now() + 300000).toISOString(),
    });
  });
}
```

---

## State Management

### Client State Architecture

```typescript
// client/stores/useCustomerPortal.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CustomerPortalState {
  // Auth state
  auth: {
    isAuthenticated: boolean;
    accessToken: string | null;
    customer: Customer | null;
  };

  // UI state
  ui: {
    sidebarOpen: boolean;
    currentTripId: string | null;
    messagePanelOpen: boolean;
  };

  // Data cache
  trips: {
    items: Trip[];
    loading: boolean;
    lastFetched: Date | null;
  };

  documents: {
    items: Document[];
    loading: boolean;
    lastFetched: Date | null;
  };

  // Actions
  actions: {
    setAuth: (auth: CustomerPortalState['auth']) => void;
    logout: () => void;
    setSidebarOpen: (open: boolean) => void;
    setCurrentTrip: (tripId: string | null) => void;
    setMessagePanelOpen: (open: boolean) => void;
    refreshTrips: () => Promise<void>;
    refreshDocuments: () => Promise<void>;
  };
}

export const useCustomerPortal = create<CustomerPortalState>()(
  persist(
    (set, get) => ({
      // Initial state
      auth: {
        isAuthenticated: false,
        accessToken: null,
        customer: null,
      },
      ui: {
        sidebarOpen: false,
        currentTripId: null,
        messagePanelOpen: false,
      },
      trips: {
        items: [],
        loading: false,
        lastFetched: null,
      },
      documents: {
        items: [],
        loading: false,
        lastFetched: null,
      },

      // Actions
      actions: {
        setAuth: (auth) => set({ auth }),
        logout: () => set({
          auth: {
            isAuthenticated: false,
            accessToken: null,
            customer: null,
          },
        }),
        setSidebarOpen: (open) => set((state) => ({
          ui: { ...state.ui, sidebarOpen: open },
        })),
        setCurrentTrip: (tripId) => set((state) => ({
          ui: { ...state.ui, currentTripId: tripId },
        })),
        setMessagePanelOpen: (open) => set((state) => ({
          ui: { ...state.ui, messagePanelOpen: open },
        })),
        refreshTrips: async () => {
          const { accessToken } = get().auth;
          if (!accessToken) return;

          set((state) => ({
            trips: { ...state.trips, loading: true },
          }));

          try {
            const response = await fetch('/api/v1/customer/trips', {
              headers: {
                Authorization: `Bearer ${accessToken}`,
              },
            });

            const data = await response.json();

            set((state) => ({
              trips: {
                items: data.trips,
                loading: false,
                lastFetched: new Date(),
              },
            }));
          } catch (error) {
            set((state) => ({
              trips: { ...state.trips, loading: false },
            }));
          }
        },
        refreshDocuments: async () => {
          const { accessToken } = get().auth;
          if (!accessToken) return;

          set((state) => ({
            documents: { ...state.documents, loading: true },
          }));

          try {
            const response = await fetch('/api/v1/customer/documents', {
              headers: {
                Authorization: `Bearer ${accessToken}`,
              },
            });

            const data = await response.json();

            set((state) => ({
              documents: {
                items: data.documents,
                loading: false,
                lastFetched: new Date(),
              },
            }));
          } catch (error) {
            set((state) => ({
              documents: { ...state.documents, loading: false },
            }));
          }
        },
      },
    }),
    {
      name: 'customer-portal-storage',
      partialize: (state) => ({
        auth: state.auth,
      }), // Only persist auth state
    }
  )
);
```

### React Query Integration

```typescript
// client/queries/useCustomerTrips.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCustomerPortal } from '@/stores/useCustomerPortal';

export function useCustomerTrips(options?: {
  status?: 'all' | 'active' | 'upcoming' | 'completed';
  enabled?: boolean;
}) {
  const { auth } = useCustomerPortal();

  return useQuery({
    queryKey: ['customer', 'trips', options?.status],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/customer/trips${options?.status ? `?status=${options.status}` : ''}`,
        {
          headers: {
            Authorization: `Bearer ${auth.accessToken}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch trips');
      }

      return response.json();
    },
    enabled: auth.isAuthenticated && (options?.enabled ?? true),
    staleTime: 60000, // 1 minute
    gcTime: 300000, // 5 minutes
  });
}

export function useTripDetails(tripId: string) {
  const { auth } = useCustomerPortal();

  return useQuery({
    queryKey: ['customer', 'trips', tripId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/customer/trips/${tripId}`, {
        headers: {
          Authorization: `Bearer ${auth.accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch trip details');
      }

      return response.json();
    },
    enabled: !!tripId && auth.isAuthenticated,
    staleTime: 120000, // 2 minutes
  });
}

export function useSendMessage(tripId: string) {
  const { auth } = useCustomerPortal();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (message: { content: string; attachments?: string[] }) => {
      const response = await fetch(`/api/v1/customer/messages/${tripId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${auth.accessToken}`,
        },
        body: JSON.stringify(message),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate messages query
      queryClient.invalidateQueries({
        queryKey: ['customer', 'messages', tripId],
      });
    },
  });
}
```

---

## Security Considerations

### Security Headers

```typescript
// middleware/security.ts
import fp from 'fastify-plugin';

export const securityHeaders = fp(async (fastify) => {
  fastify.addHook('onSend', async (request, reply) => {
    // Standard security headers
    reply.header('X-Content-Type-Options', 'nosniff');
    reply.header('X-Frame-Options', 'DENY');
    reply.header('X-XSS-Protection', '1; mode=block');
    reply.header('Referrer-Policy', 'strict-origin-when-cross-origin');

    // Content Security Policy
    reply.header('Content-Security-Policy', [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plaid.com",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https: blob:",
      "font-src 'self' data:",
      "connect-src 'self' https://api.stripe.com",
      "frame-src 'none'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join('; '));

    // HSTS (only in production)
    if (process.env.NODE_ENV === 'production') {
      reply.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
    }

    // Permissions Policy
    reply.header('Permissions-Policy', [
      'camera=()',
      'microphone=()',
      'geolocation=()',
      'payment=(self)',
    ].join(', '));
  });
});
```

### Rate Limiting

```typescript
// middleware/rate-limit.ts
import fp from 'fastify-plugin';
import { createRateLimit } from '@fastify/rate-limit';

export const customerRateLimit = fp(async (fastify) => {
  fastify.register(createRateLimit, {
    max: 100, // 100 requests per window
    timeWindow: '1 minute',
    cache: 10000,
    allowList: [], // Optional whitelist
    redis: fastify.redis,
    skipOnError: false,
    continueExceeding: false,
    keyGenerator: (request) => {
      // Use customer ID if authenticated, otherwise IP
      return (request.customer as Customer)?.id || request.ip;
    },
    errorResponseBuilder: (request, context) => ({
      error: 'Too Many Requests',
      message: `Rate limit exceeded. Try again in ${Math.round(context.after / 1000)} seconds.`,
      retryAfter: context.after,
    }),
  });

  // Stricter limits for sensitive endpoints
  fastify.register(createRateLimit, {
    name: 'auth-rate-limit',
    max: 10,
    timeWindow: '1 minute',
    redis: fastify.redis,
    routes: ['/api/v1/customer/auth/initiate', '/api/v1/customer/auth/verify'],
  });

  // Stricter for message sending
  fastify.register(createRateLimit, {
    name: 'message-rate-limit',
    max: 20,
    timeWindow: '1 hour',
    redis: fastify.redis,
    routes: ['/api/v1/customer/messages/:tripId'],
  });
});
```

### Audit Logging

```typescript
// services/audit_log.ts
interface AuditEvent {
  eventType: string;
  customerId: string;
  tripId?: string;
  resourceId?: string;
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

class AuditLogService {
  async log(event: AuditEvent): Promise<void> {
    await this.db.query(`
      INSERT INTO customer_audit_log (
        event_type, customer_id, trip_id, resource_id,
        ip_address, user_agent, timestamp, metadata
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    `, [
      event.eventType,
      event.customerId,
      event.tripId || null,
      event.resourceId || null,
      event.ipAddress,
      event.userAgent,
      event.timestamp,
      event.metadata ? JSON.stringify(event.metadata) : null,
    ]);

    // Also send to logging service
    this.loggingService.info('customer_audit', event);
  }

  // Common audit helpers
  async logLogin(customerId: string, ipAddress: string, userAgent: string): Promise<void> {
    await this.log({
      eventType: 'login',
      customerId,
      ipAddress,
      userAgent,
      timestamp: new Date(),
    });
  }

  async logDocumentView(customerId: string, documentId: string, tripId: string, ipAddress: string): Promise<void> {
    await this.log({
      eventType: 'document_viewed',
      customerId,
      tripId,
      resourceId: documentId,
      ipAddress,
      userAgent: '',
      timestamp: new Date(),
    });
  }

  async logPaymentInitiated(customerId: string, tripId: string, amount: number, ipAddress: string): Promise<void> {
    await this.log({
      eventType: 'payment_initiated',
      customerId,
      tripId,
      ipAddress,
      userAgent: '',
      timestamp: new Date(),
      metadata: { amount },
    });
  }
}
```

---

## Performance Optimization

### Caching Strategy

```typescript
// cache/customer_cache.ts
class CustomerCacheService {
  private cachePrefix = 'customer';

  // Trip caching
  async cacheTrip(tripId: string, data: unknown, ttl: number = 300): Promise<void> {
    await this.redis.setex(
      `${this.cachePrefix}:trip:${tripId}`,
      ttl,
      JSON.stringify(data)
    );
  }

  async getTrip(tripId: string): Promise<unknown | null> {
    const data = await this.redis.get(`${this.cachePrefix}:trip:${tripId}`);
    return data ? JSON.parse(data) : null;
  }

  async invalidateTrip(tripId: string): Promise<void> {
    await this.redis.del(`${this.cachePrefix}:trip:${tripId}`);
  }

  // Document list caching (per customer)
  async cacheDocumentList(customerId: string, data: unknown, ttl: number = 600): Promise<void> {
    await this.redis.setex(
      `${this.cachePrefix}:docs:${customerId}`,
      ttl,
      JSON.stringify(data)
    );
  }

  async getDocumentList(customerId: string): Promise<unknown | null> {
    const data = await this.redis.get(`${this.cachePrefix}:docs:${customerId}`);
    return data ? JSON.parse(data) : null;
  }

  async invalidateCustomerData(customerId: string): Promise<void> {
    // Invalidate all customer-specific caches
    const keys = await this.redis.keys(`${this.cachePrefix}:*:${customerId}*`);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }

  // Cache invalidation on updates
  async onTripUpdated(tripId: string, affectedCustomers: string[]): Promise<void> {
    await this.invalidateTrip(tripId);
    for (const customerId of affectedCustomers) {
      await this.invalidateCustomerData(customerId);
    }
  }
}
```

### CDN Configuration

```typescript
// config/cdn.ts
export const customerPortalCDNConfig = {
  // Static assets
  staticAssets: {
    ttl: 31536000, // 1 year
    paths: ['/assets/*', '/images/*'],
  },

  // HTML pages (cache but revalidate)
  pages: {
    ttl: 300, // 5 minutes
    staleWhileRevalidate: 86400, // 1 day
    paths: ['/*'],
  },

  // API responses (short cache)
  api: {
    ttl: 60, // 1 minute
    paths: ['/api/v1/customer/trips', '/api/v1/customer/documents'],
  },

  // No cache for sensitive operations
  noCache: {
    paths: [
      '/api/v1/customer/auth/*',
      '/api/v1/customer/messages/*',
      '/api/v1/customer/payments/*',
    ],
  },
};
```

---

**Next:** [CUSTOMER_PORTAL_02_UX_UI_DEEP_DIVE](./CUSTOMER_PORTAL_02_UX_UI_DEEP_DIVE.md) — Customer portal interface design and user experience
