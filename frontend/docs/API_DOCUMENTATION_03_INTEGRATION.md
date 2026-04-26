# API Documentation Part 3: Integration Guide

> Authentication, SDKs, webhooks, and best practices

**Series:** API Documentation
**Previous:** [Part 2: API Design Guidelines](./API_DOCUMENTATION_02_DESIGN.md)
**Next:** [Part 4: Error Handling](./API_DOCUMENTATION_04_ERRORS.md)

---

## Table of Contents

1. [Authentication Flow](#authentication-flow)
2. [API Keys and Tokens](#api-keys-and-tokens)
3. [JavaScript SDK](#javascript-sdk)
4. [Python SDK](#python-sdk)
5. [Webhook Integration](#webhook-integration)
6. [Rate Limiting](#rate-limiting)
7. [Best Practices](#best-practices)

---

## Authentication Flow

### Authentication Overview

```typescript
// Authentication architecture

interface AuthArchitecture {
  // Registration flow
  registration: 'email/password → verification → access/refresh tokens';

  // Login flow
  login: 'credentials → access/refresh tokens → authenticated requests';

  // Token refresh flow
  refresh: 'expired access → refresh token → new access/refresh tokens';

  // Token types
  tokens: {
    access_token: 'JWT, 15min expiry, used for API requests';
    refresh_token: 'HTTP-only cookie, 7d expiry, used for refresh';
  };
}
```

### Registration Flow

```typescript
// Step 1: Register new user

interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: 'customer' | 'agent' | 'admin';
}

interface RegisterResponse {
  user: User;
  tokens: {
    access_token: string;
    expires_in: number; // seconds
  };
}

// Example registration
async function register(credentials: RegisterRequest) {
  const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  const data = await response.json();

  // Store access token (refresh token is HTTP-only cookie)
  localStorage.setItem('access_token', data.tokens.access_token);

  return data;
}
```

### Login Flow

```typescript
// Step 2: Login with credentials

interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

interface LoginResponse {
  user: User;
  tokens: {
    access_token: string;
    expires_in: number;
  };
}

async function login(credentials: LoginRequest) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Include cookies
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  const data = await response.json();

  // Store access token
  localStorage.setItem('access_token', data.tokens.access_token);

  return data;
}
```

### Token Refresh Flow

```typescript
// Step 3: Refresh expired access token

interface RefreshResponse {
  access_token: string;
  expires_in: number;
}

async function refreshToken(): Promise<string> {
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    credentials: 'include', // Include HTTP-only refresh cookie
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    // Refresh token is invalid or expired
    logout();
    throw new Error('Session expired. Please login again.');
  }

  const data = await response.json();

  // Store new access token
  localStorage.setItem('access_token', data.access_token);

  return data.access_token;
}
```

### Authenticated Requests

```typescript
// Making authenticated API requests

interface ApiClientConfig {
  baseURL: string;
  onTokenExpired?: () => Promise<void>;
}

class ApiClient {
  private config: ApiClientConfig;

  constructor(config: ApiClientConfig) {
    this.config = config;
  }

  private async getAccessToken(): Promise<string> {
    let token = localStorage.getItem('access_token');

    // Check if token is expired
    if (token && this.isTokenExpired(token)) {
      token = await this.config.onTokenExpired?.() || await refreshToken();
    }

    return token || '';
  }

  private isTokenExpired(token: string): boolean {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getAccessToken();

    const response = await fetch(`${this.config.baseURL}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    // Handle 401 - token expired
    if (response.status === 401 && !options.headers?.['X-Retry']) {
      const newToken = await this.config.onTokenExpired?.() || await refreshToken();

      // Retry request with new token
      return this.request<T>(endpoint, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${newToken}`,
          'X-Retry': 'true',
        },
      });
    }

    if (!response.ok) {
      throw new ApiError(response);
    }

    return response.json();
  }

  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  patch<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(response: Response) {
    super('API request failed');
    this.name = 'ApiError';
    this.status = response.status;
  }
}

// Usage
const api = new ApiClient({
  baseURL: 'https://api.travelagency.com',
  onTokenExpired: async () => {
    return await refreshToken();
  },
});

// Get user bookings
const bookings = await api.get<Booking[]>('/api/bookings');

// Create booking
const booking = await api.post<Booking>('/api/bookings', {
  destination: 'Paris',
  check_in: '2025-06-01',
  check_out: '2025-06-07',
  guests: 2,
});
```

---

## API Keys and Tokens

### API Keys for Service Accounts

```typescript
// API key authentication for server-to-server communication

interface ApiKey {
  key_id: string;
  secret: string;
  name: string;
  scopes: string[];
  created_at: string;
  last_used?: string;
}

// Creating API keys
async function createApiKey(name: string, scopes: string[]): Promise<ApiKey> {
  const response = await fetch('/api/api-keys', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, scopes }),
  });

  return response.json();
}

// Using API keys
class ServiceClient {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new ApiError(response);
    }

    return response.json();
  }
}

// Usage
const serviceClient = new ServiceClient('pk_live_1234567890abcdef');
const bookings = await serviceClient.get('/api/bookings');
```

### JWT Token Structure

```typescript
// JWT access token payload

interface JwtPayload {
  // Standard claims
  iss: string;      // Issuer (api.travelagency.com)
  sub: string;      // Subject (user ID)
  aud: string;      // Audience (api)
  exp: number;      // Expiration time
  iat: number;      // Issued at
  jti: string;      // JWT ID (unique token identifier)

  // Custom claims
  user_id: string;
  email: string;
  role: 'customer' | 'agent' | 'admin';
  agency_id?: string;
  scopes: string[];
}

// Example decoded token
const examplePayload: JwtPayload = {
  iss: 'https://api.travelagency.com',
  sub: 'usr_1234567890abcdef',
  aud: 'api',
  exp: 1745649600,
  iat: 1745648700,
  jti: 'tok_1234567890abcdef',

  user_id: 'usr_1234567890abcdef',
  email: 'user@example.com',
  role: 'customer',
  scopes: ['booking:read', 'booking:write', 'payment:write'],
};
```

### Token Security Best Practices

```typescript
// Token security guidelines

interface TokenSecurity {
  storage: {
    access_token: 'Memory or localStorage (XSS risk, use httpOnly if possible)';
    refresh_token: 'HTTP-only, secure, same-site cookie';
    api_key: 'Environment variable (server-side only)';
  };

  transmission: {
    header: 'Authorization: Bearer {token}';
    cookie: 'HTTP-only, secure, same-site cookie';
  };

  validation: {
    signature: 'Verify JWT signature';
    expiration: 'Check exp claim';
    issuer: 'Verify iss claim';
    audience: 'Verify aud claim';
  };
}

// Secure token storage
class TokenManager {
  private memoryTokens = new Map<string, string>();

  // Store in memory (most secure for SPA)
  setMemoryToken(key: string, value: string): void {
    this.memoryTokens.set(key, value);
  }

  getMemoryToken(key: string): string | undefined {
    return this.memoryTokens.get(key);
  }

  clearMemoryTokens(): void {
    this.memoryTokens.clear();
  }

  // Store in localStorage (fallback)
  setLocalToken(key: string, value: string): void {
    localStorage.setItem(key, value);
  }

  getLocalToken(key: string): string | null {
    return localStorage.getItem(key);
  }

  clearLocalTokens(): void {
    localStorage.removeItem('access_token');
  }
}
```

---

## JavaScript SDK

### SDK Installation

```bash
# npm
npm install @travelagency/sdk

# yarn
yarn add @travelagency/sdk

# pnpm
pnpm add @travelagency/sdk
```

### SDK Initialization

```typescript
// SDK initialization

import { TravelAgencyClient } from '@travelagency/sdk';

const client = new TravelAgencyClient({
  apiKey: process.env.TRAVEL_AGENCY_API_KEY,
  baseURL: 'https://api.travelagency.com',
  environment: 'production', // or 'staging', 'development'
  timeout: 30000, // 30 seconds
  maxRetries: 3,
});

// Or with user authentication
const authenticatedClient = new TravelAgencyClient({
  baseURL: 'https://api.travelagency.com',
  getAccessToken: async () => {
    // Custom token retrieval logic
    return localStorage.getItem('access_token') || '';
  },
  onTokenExpired: async () => {
    // Custom refresh logic
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    return data.access_token;
  },
});
```

### Booking API

```typescript
// Booking operations

import { BookingStatus, PaymentMethod } from '@travelagency/sdk';

// Create booking
const booking = await client.bookings.create({
  destination_id: 'dest_paris_france',
  check_in: '2025-06-01',
  check_out: '2025-06-07',
  guests: {
    adults: 2,
    children: 0,
  },
  accommodation: {
    type: 'hotel',
    id: 'hotel_123',
    room_type: 'deluxe',
  },
});

// List bookings with filtering
const bookings = await client.bookings.list({
  status: BookingStatus.CONFIRMED,
  limit: 20,
  sort: '-created_at',
});

// Get single booking
const booking = await client.bookings.get('bk_1234567890abcdef');

// Update booking
const updated = await client.bookings.update('bk_1234567890abcdef', {
  guests: { adults: 3, children: 1 },
});

// Cancel booking
await client.bookings.cancel('bk_1234567890abcdef', {
  reason: 'Change of plans',
  refund_requested: true,
});
```

### Payment API

```typescript
// Payment operations

// Create payment intent
const paymentIntent = await client.payments.createIntent({
  booking_id: 'bk_1234567890abcdef',
  amount: 1000,
  currency: 'USD',
  payment_method: PaymentMethod.CREDIT_CARD,
  return_url: 'https://example.com/booking/confirm',
});

// Confirm payment
const payment = await client.payments.confirm({
  payment_intent_id: paymentIntent.id,
  payment_method: 'pm_1234567890abcdef',
});

// Get payment status
const status = await client.payments.getStatus('pay_1234567890abcdef');

// List booking payments
const payments = await client.payments.listByBooking('bk_1234567890abcdef');

// Refund payment
const refund = await client.payments.createRefund('pay_1234567890abcdef', {
  amount: 500,
  reason: 'Customer request',
});
```

### Search API

```typescript
// Search operations

// Search destinations
const destinations = await client.search.destinations({
  query: 'Paris',
  check_in: '2025-06-01',
  check_out: '2025-06-07',
  guests: 2,
  limit: 10,
});

// Search accommodations
const accommodations = await client.search.accommodations({
  destination_id: 'dest_paris_france',
  check_in: '2025-06-01',
  check_out: '2025-06-07',
  guests: 2,
  amenities: ['wifi', 'pool', 'parking'],
  price_range: { min: 100, max: 500 },
});

// Get autocomplete suggestions
const suggestions = await client.search.suggest('Pa');
// ['Paris, France', 'Pasadena, CA', 'Palo Alto, CA', ...]
```

### Webhook Management

```typescript
// Webhook operations

// Create webhook
const webhook = await client.webhooks.create({
  url: 'https://example.com/webhooks',
  events: ['booking.created', 'booking.updated', 'payment.succeeded'],
  secret: 'whsec_1234567890abcdef',
});

// List webhooks
const webhooks = await client.webhooks.list();

// Update webhook
const updated = await client.webhooks.update('wh_1234567890abcdef', {
  events: ['booking.created', 'booking.updated', 'booking.cancelled'],
});

// Delete webhook
await client.webhooks.delete('wh_1234567890abcdef');

// Verify webhook signature
const isValid = client.webhooks.verifySignature({
  payload: rawBody,
  signature: headers['x-webhook-signature'],
  secret: webhook.secret,
});
```

---

## Python SDK

### SDK Installation

```bash
# pip
pip install travelagency-sdk

# poetry
poetry add travelagency-sdk

# pipenv
pipenv install travelagency-sdk
```

### SDK Initialization

```python
# SDK initialization

from travelagency import TravelAgencyClient
from travelagency.exceptions import ApiError, AuthError

# With API key
client = TravelAgencyClient(
    api_key="pk_live_1234567890abcdef",
    base_url="https://api.travelagency.com",
    environment="production",
    timeout=30,
    max_retries=3,
)

# With access token
client = TravelAgencyClient(
    base_url="https://api.travelagency.com",
    access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
)

# With custom token refresh
def get_token():
    return "your_access_token"

def refresh_token():
    response = requests.post(
        "https://api.travelagency.com/api/auth/refresh",
        cookies={"refresh_token": "your_refresh_token"}
    )
    return response.json()["access_token"]

client = TravelAgencyClient(
    base_url="https://api.travelagency.com",
    access_token_callback=get_token,
    refresh_token_callback=refresh_token,
)
```

### Booking API

```python
# Booking operations

from travelagency import BookingStatus

# Create booking
booking = client.bookings.create(
    destination_id="dest_paris_france",
    check_in="2025-06-01",
    check_out="2025-06-07",
    guests={
        "adults": 2,
        "children": 0,
    },
    accommodation={
        "type": "hotel",
        "id": "hotel_123",
        "room_type": "deluxe",
    },
)

# List bookings with filtering
bookings = client.bookings.list(
    status=BookingStatus.CONFIRMED,
    limit=20,
    sort="-created_at",
)

# Get single booking
booking = client.bookings.get("bk_1234567890abcdef")

# Update booking
updated = client.bookings.update(
    "bk_1234567890abcdef",
    guests={"adults": 3, "children": 1}
)

# Cancel booking
client.bookings.cancel(
    "bk_1234567890abcdef",
    reason="Change of plans",
    refund_requested=True
)
```

### Payment API

```python
# Payment operations

from travelagency import PaymentMethod

# Create payment intent
payment_intent = client.payments.create_intent(
    booking_id="bk_1234567890abcdef",
    amount=1000,
    currency="USD",
    payment_method=PaymentMethod.CREDIT_CARD,
    return_url="https://example.com/booking/confirm",
)

# Confirm payment
payment = client.payments.confirm(
    payment_intent_id=payment_intent.id,
    payment_method="pm_1234567890abcdef",
)

# Get payment status
status = client.payments.get_status("pay_1234567890abcdef")

# List booking payments
payments = client.payments.list_by_booking("bk_1234567890abcdef")

# Refund payment
refund = client.payments.create_refund(
    "pay_1234567890abcdef",
    amount=500,
    reason="Customer request"
)
```

### Error Handling

```python
# Error handling

from travelagency.exceptions import (
    ApiError,
    AuthError,
    NotFoundError,
    ValidationError,
    RateLimitError,
)

try:
    booking = client.bookings.get("bk_1234567890abcdef")
except NotFoundError as e:
    print(f"Booking not found: {e}")
    # Handle 404
except ValidationError as e:
    print(f"Validation error: {e.errors}")
    # Handle 422
except AuthError as e:
    print(f"Authentication failed: {e}")
    # Handle 401
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
    # Handle 429
except ApiError as e:
    print(f"API error: {e.status_code} - {e.message}")
    # Handle other errors
```

---

## Webhook Integration

### Webhook Overview

```typescript
// Webhook delivery model

interface WebhookDelivery {
  // Event payload
  event: {
    id: string;
    type: string;
    timestamp: string;
    data: unknown;
  };

  // Delivery metadata
  delivery: {
    id: string;
    attempt: number;
    timestamp: string;
  };

  // Signature
  signature: string;
}

// Webhook events
type WebhookEvent =
  | 'booking.created'
  | 'booking.updated'
  | 'booking.cancelled'
  | 'booking.confirmed'
  | 'payment.succeeded'
  | 'payment.failed'
  | 'payment.refunded'
  | 'user.created'
  | 'user.updated';
```

### Setting Up Webhooks

```typescript
// Server-side webhook handler (Node.js/Express)

import crypto from 'crypto';
import express from 'express';

const app = express();

// Verify webhook signature
function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(payload).digest('base64');

  // Signature format: sha256=<digest>
  const receivedHash = signature.replace('sha256=', '');

  return crypto.timingSafeEqual(
    Buffer.from(digest),
    Buffer.from(receivedHash)
  );
}

// Webhook endpoint
app.post('/webhooks', express.raw({ type: 'application/json' }), (req, res) => {
  const signature = req.headers['x-webhook-signature'] as string;
  const payload = req.body.toString();

  // Verify signature
  if (!verifyWebhookSignature(payload, signature, process.env.WEBHOOK_SECRET!)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const event = JSON.parse(payload);

  // Handle event
  handleWebhookEvent(event)
    .then(() => res.status(200).json({ received: true }))
    .catch((err) => {
      console.error('Webhook handling failed:', err);
      res.status(500).json({ error: 'Webhook processing failed' });
    });
});

// Event handler
async function handleWebhookEvent(event: WebhookEvent): Promise<void> {
  switch (event.type) {
    case 'booking.created':
      await handleBookingCreated(event.data);
      break;
    case 'booking.updated':
      await handleBookingUpdated(event.data);
      break;
    case 'booking.cancelled':
      await handleBookingCancelled(event.data);
      break;
    case 'payment.succeeded':
      await handlePaymentSucceeded(event.data);
      break;
    case 'payment.failed':
      await handlePaymentFailed(event.data);
      break;
    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
}

// Example handlers
async function handleBookingCreated(booking: Booking): Promise<void> {
  // Send confirmation email
  await sendEmail({
    to: booking.user.email,
    template: 'booking-confirmation',
    data: { booking },
  });

  // Update internal systems
  await updateCRM({ type: 'booking_created', booking });

  // Log analytics
  await analytics.track('booking_created', {
    booking_id: booking.id,
    destination: booking.destination,
    total_price: booking.total_price,
  });
}

async function handlePaymentSucceeded(payment: Payment): Promise<void> {
  // Update booking status
  await updateBookingStatus(payment.booking_id, 'confirmed');

  // Send payment confirmation
  await sendEmail({
    to: payment.booking.user.email,
    template: 'payment-confirmation',
    data: { payment },
  });

  // Generate invoice
  await generateInvoice(payment);
}

app.listen(3000, () => {
  console.log('Webhook server listening on port 3000');
});
```

### Webhook Testing

```typescript
// Local webhook testing with ngrok/smee

// 1. Start your local server
// npm run dev:server

// 2. Create tunnel
// ngrok http 3000

// 3. Register webhook with tunnel URL
const webhook = await client.webhooks.create({
  url: 'https://abc123.ngrok.io/webhooks',
  events: ['booking.created', 'payment.succeeded'],
  secret: 'test_secret',
});

// 4. Test webhook delivery
await client.webhooks.test(webhook.id, {
  event: 'booking.created',
  data: testBookingData,
});

// 5. Check delivery logs
const logs = await client.webhooks.getLogs(webhook.id);
```

### Webhook Retry Logic

```typescript
// Webhook retry strategy

interface RetryConfig {
  maxAttempts: number;
  backoffMultiplier: number;
  initialDelay: number;
}

const retryConfig: RetryConfig = {
  maxAttempts: 5,
  backoffMultiplier: 2,
  initialDelay: 1000, // 1 second
};

// Retry schedule:
// Attempt 1: Immediate
// Attempt 2: 1 second delay
// Attempt 3: 2 second delay
// Attempt 4: 4 second delay
// Attempt 5: 8 second delay

// Server-side webhook acknowledgment
app.post('/webhooks', async (req, res) => {
  // Process webhook asynchronously
  processWebhookAsync(req.body)
    .then(() => console.log('Webhook processed successfully'))
    .catch((err) => console.error('Webhook processing failed:', err));

  // Acknowledge immediately (prevents timeout)
  res.status(200).json({ received: true });
});
```

---

## Rate Limiting

### Rate Limit Overview

```typescript
// Rate limit headers

interface RateLimitHeaders {
  'X-RateLimit-Limit': string;      // Total requests allowed
  'X-RateLimit-Remaining': string;  // Requests remaining in window
  'X-RateLimit-Reset': string;      // Unix timestamp when limit resets
  'Retry-After': string;            // Seconds to wait (429 response)
}

// Rate limits by tier
interface RateLimits {
  free: {
    requests: 100;
    window: '1 hour';
  };

  pro: {
    requests: 1000;
    window: '1 hour';
  };

  enterprise: {
    requests: 10000;
    window: '1 hour';
  };
}
```

### Handling Rate Limits

```typescript
// Rate limit-aware client

class RateLimitedClient {
  private rateLimit: {
    limit: number;
    remaining: number;
    reset: number;
  } = {
    limit: 100,
    remaining: 100,
    reset: Date.now() + 3600000,
  };

  private requestQueue: Array<() => Promise<void>> = [];
  private isProcessingQueue = false;

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // Check if we need to wait for reset
    if (this.rateLimit.remaining === 0) {
      const waitTime = this.rateLimit.reset - Date.now();
      if (waitTime > 0) {
        await this.delay(waitTime);
      }
    }

    const response = await fetch(endpoint, options);

    // Update rate limit info from headers
    this.updateRateLimit(response.headers);

    // Handle rate limit response
    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '60', 10);
      await this.delay(retryAfter * 1000);
      return this.request<T>(endpoint, options);
    }

    this.rateLimit.remaining--;

    if (!response.ok) {
      throw new ApiError(response);
    }

    return response.json();
  }

  private updateRateLimit(headers: Headers): void {
    const limit = headers.get('X-RateLimit-Limit');
    const remaining = headers.get('X-RateLimit-Remaining');
    const reset = headers.get('X-RateLimit-Reset');

    if (limit) this.rateLimit.limit = parseInt(limit, 10);
    if (remaining) this.rateLimit.remaining = parseInt(remaining, 10);
    if (reset) this.rateLimit.reset = parseInt(reset, 10) * 1000;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
```

### Rate Limit Best Practices

```typescript
// Rate limit best practices

interface RateLimitGuidelines {
  // Handle 429 responses gracefully
  handling: 'Retry after Retry-After delay';

  // Implement exponential backoff
  backoff: 'Increase delay on consecutive 429s';

  // Queue requests when approaching limit
  queuing: 'Throttle requests before hitting limit';

  // Monitor rate limit usage
  monitoring: 'Track remaining quota in dashboards';

  // Prioritize critical requests
  prioritization: 'Process important requests first';
}

// Request prioritization
type RequestPriority = 'critical' | 'high' | 'normal' | 'low';

interface PrioritizedRequest {
  priority: RequestPriority;
  execute: () => Promise<void>;
}

class RequestQueue {
  private queues: Map<RequestPriority, PrioritizedRequest[]> = new Map([
    ['critical', []],
    ['high', []],
    ['normal', []],
    ['low', []],
  ]);

  add(request: PrioritizedRequest): void {
    this.queues.get(request.priority)?.push(request);
  }

  async process(rateLimit: number): Promise<void> {
    const priorityOrder: RequestPriority[] = ['critical', 'high', 'normal', 'low'];
    let processed = 0;

    for (const priority of priorityOrder) {
      const queue = this.queues.get(priority)!;

      while (queue.length > 0 && processed < rateLimit) {
        const request = queue.shift()!;
        await request.execute();
        processed++;
      }
    }
  }
}
```

---

## Best Practices

### Security Best Practices

```typescript
// Security guidelines

interface SecurityBestPractices {
  // Never expose API keys in client-side code
  apiKeyStorage: 'Server-side environment variables only';

  // Use HTTPS for all API calls
  transport: 'HTTPS required, TLS 1.2+';

  // Validate all input data
  validation: 'Validate on client and server';

  // Implement proper error handling
  errorHandling: 'Don\'t expose sensitive data in errors';

  // Rotate credentials regularly
  rotation: 'Rotate API keys and secrets quarterly';

  // Use read-only keys when possible
  scopes: 'Principle of least privilege';

  // Log all API activity
  auditing: 'Log requests with user context';
}
```

### Performance Best Practices

```typescript
// Performance guidelines

interface PerformanceBestPractices {
  // Use pagination for large datasets
  pagination: 'Cursor-based for large lists';

  // Request only needed fields
  fieldSelection: 'Use sparse fieldsets';

  // Cache responses when appropriate
  caching: 'Cache GET requests with ETags';

  // Use compression
  compression: 'Accept-Encoding: gzip, br';

  // Batch requests when possible
  batching: 'Combine multiple operations';

  // Use webhooks for events
  webhooks: 'Prefer webhooks over polling';

  // Implement retries with backoff
  retries: 'Exponential backoff for failures';
}

// Caching example
class CachedApiClient {
  private cache = new Map<string, { data: unknown; expiry: number }>();

  async get<T>(endpoint: string, maxAge = 60000): Promise<T> {
    const cached = this.cache.get(endpoint);

    if (cached && cached.expiry > Date.now()) {
      return cached.data as T;
    }

    const response = await fetch(endpoint);

    if (!response.ok) {
      throw new ApiError(response);
    }

    const data = await response.json();

    this.cache.set(endpoint, {
      data,
      expiry: Date.now() + maxAge,
    });

    return data as T;
  }

  invalidate(endpoint: string): void {
    this.cache.delete(endpoint);
  }

  clear(): void {
    this.cache.clear();
  }
}
```

### Monitoring and Debugging

```typescript
// API monitoring

interface ApiMonitoring {
  // Track request metrics
  metrics: {
    requestCount: number;
    errorRate: number;
    latency: number;
    rateLimitHits: number;
  };

  // Log important events
  logging: {
    errors: boolean;
    slowRequests: boolean;
    rateLimits: boolean;
  };

  // Alert on issues
  alerting: {
    highErrorRate: boolean;
    highLatency: boolean;
    rateLimitExceeded: boolean;
  };
}

// Monitoring wrapper
class MonitoredApiClient extends ApiClient {
  private metrics = {
    requests: 0,
    errors: 0,
    latency: [] as number[],
  };

  override async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const start = Date.now();
    this.metrics.requests++;

    try {
      const response = await super.request<T>(endpoint, options);

      const latency = Date.now() - start;
      this.metrics.latency.push(latency);

      // Log slow requests
      if (latency > 1000) {
        console.warn(`Slow API request: ${endpoint} took ${latency}ms`);
      }

      return response;
    } catch (error) {
      this.metrics.errors++;

      // Log errors
      console.error(`API request failed: ${endpoint}`, error);

      // Send to monitoring service
      this.reportError(endpoint, error);

      throw error;
    }
  }

  private reportError(endpoint: string, error: unknown): void {
    // Send to error tracking service
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.captureException(error, {
        tags: { endpoint },
        extra: { metrics: this.metrics },
      });
    }
  }

  getMetrics() {
    return {
      ...this.metrics,
      errorRate: this.metrics.errors / this.metrics.requests,
      avgLatency: this.metrics.latency.reduce((a, b) => a + b, 0) / this.metrics.latency.length,
    };
  }
}
```

### Testing Integration

```typescript
// Testing API integration

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchMock } from 'vitest-fetch-mock';

describe('ApiClient', () => {
  beforeEach(() => {
    fetchMock.resetMocks();
  });

  it('should make authenticated requests', async () => {
    const mockData = { id: 'bk_123', destination: 'Paris' };
    fetchMock.mockResponseOnce(JSON.stringify(mockData));

    const client = new ApiClient({
      baseURL: 'https://api.test.com',
      getAccessToken: async () => 'test_token',
    });

    const result = await client.get('/api/bookings/bk_123');

    expect(result).toEqual(mockData);
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.test.com/api/bookings/bk_123',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test_token',
        }),
      })
    );
  });

  it('should retry on 401 with token refresh', async () => {
    fetchMock
      .mockResponseOnce(JSON.stringify({ message: 'Unauthorized' }), { status: 401 })
      .mockResponseOnce(JSON.stringify({ access_token: 'new_token' }))
      .mockResponseOnce(JSON.stringify({ id: 'bk_123' }));

    const client = new ApiClient({
      baseURL: 'https://api.test.com',
      getAccessToken: async () => 'old_token',
      onTokenExpired: async () => 'new_token',
    });

    const result = await client.get('/api/bookings/bk_123');

    expect(result).toEqual({ id: 'bk_123' });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('should throw ApiError on non-4xx responses', async () => {
    fetchMock.mockResponseOnce(
      JSON.stringify({ error: 'Not found' }),
      { status: 404 }
    );

    const client = new ApiClient({
      baseURL: 'https://api.test.com',
      getAccessToken: async () => 'test_token',
    });

    await expect(client.get('/api/bookings/bk_123')).rejects.toThrow(ApiError);
  });
});
```

---

## Summary

API integration guidelines for the travel agency platform:

- **Authentication**: JWT access tokens with HTTP-only refresh cookies
- **SDKs**: JavaScript and Python SDKs with automatic token refresh
- **Webhooks**: Real-time event notifications with signature verification
- **Rate Limiting**: Tiered limits with graceful handling
- **Security**: HTTPS, scoped API keys, credential rotation
- **Performance**: Caching, pagination, field selection
- **Monitoring**: Metrics, logging, error tracking

**Key Integration Points:**
1. Implement token refresh before making requests
2. Handle rate limits with exponential backoff
3. Verify webhook signatures before processing
4. Use SDKs to reduce boilerplate
5. Monitor API usage and errors
6. Test integration thoroughly

---

**Next:** [Part 4: Error Handling](./API_DOCUMENTATION_04_ERRORS.md) — Error codes, responses, and troubleshooting
