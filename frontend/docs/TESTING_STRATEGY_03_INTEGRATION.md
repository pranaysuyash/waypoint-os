# Testing Strategy Part 3: Integration Testing

> API routes, database operations, MSW mocking, and service integration

**Series:** Testing Strategy
**Previous:** [Part 2: Unit Testing](./TESTING_STRATEGY_02_UNIT.md)
**Next:** [Part 4: E2E Testing](./TESTING_STRATEGY_04_E2E.md)

---

## Table of Contents

1. [Integration Testing Philosophy](#integration-testing-philosophy)
2. [API Route Testing](#api-route-testing)
3. [MSW for API Mocking](#msw-for-api-mocking)
4. [Database Testing](#database-testing)
5. [State Management Testing](#state-management-testing)
6. [Third-Party Integration](#third-party-integration)
7. [Contract Testing](#contract-testing)

---

## Integration Testing Philosophy

### What is Integration Testing?

Integration tests verify that **multiple parts work together correctly**:

- API routes + database
- Frontend + backend
- Service + external API
- Component + state management + API

### The Sweet Spot

```
Unit Tests          Fast, isolated
    ↓
Integration Tests   ← Target: Key workflows
    ↓
E2E Tests          Slow, expensive
```

**Integration tests give you:**
- ✅ Real database interactions
- ✅ Real HTTP requests/responses
- ✅ Real authentication flows
- ✅ Much faster than E2E
- ✅ More reliable than E2E

---

## API Route Testing

### Setup for Route Testing

```typescript
// src/test/setup/api-test-setup.ts

import { Hono } from 'hono';
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { drizzle } from 'drizzle-orm/neon-http';
import { migrate } from 'drizzle-orm/neon-http/migrator';
import { neon } from '@neondatabase/serverless';
import * as schema from '@/db/schema';

// Test database connection
const sql = neon(process.env.TEST_DATABASE_URL!);
export const db = drizzle(sql, { schema });

// Create test app
export function createTestApp() {
  const app = new Hono();

  // Import and use routes
  app.route('/api/bookings', bookingsRoutes);
  app.route('/api/payments', paymentsRoutes);
  app.route('/api/auth', authRoutes);

  return app;
}

// Setup and teardown
let testDb: ReturnType<typeof drizzle>;

beforeAll(async () => {
  // Use test database
  testDb = drizzle(
    neon(process.env.TEST_DATABASE_URL!),
    { schema }
  );

  // Run migrations
  await migrate(testDb, { migrationsFolder: 'drizzle' });
});

afterAll(async () => {
  // Clean up test database
  await sql.query('DROP SCHEMA public CASCADE');
  await sql.query('CREATE SCHEMA public');
});

// Helper to create authenticated request
export async function createAuthenticatedRequest(
  userId: string
): Promise<string> {
  const token = await generateTestToken({ userId });
  return token;
}
```

### Testing CRUD Operations

```typescript
// src/routes/api/bookings.test.ts

import { describe, it, expect, beforeEach } from 'vitest';
import { createTestApp, db, createAuthenticatedRequest } from '@/test/setup/api-test-setup';
import { bookings } from '@/db/schema';
import { eq } from 'drizzle-orm';

describe('POST /api/bookings', () => {
  let app: Hono;
  let authToken: string;

  beforeEach(async () => {
    app = createTestApp();
    authToken = await createAuthenticatedRequest('user-123');
  });

  describe('authentication', () => {
    it('returns 401 without token', async () => {
      const response = await app.request('/api/bookings', {
        method: 'POST',
        json: { destination: 'Paris' },
      });

      expect(response.status).toBe(401);
      expect(await response.json()).toEqual({
        error: 'Unauthorized',
      });
    });

    it('returns 401 with invalid token', async () => {
      const response = await app.request('/api/bookings', {
        method: 'POST',
        headers: { Authorization: 'Bearer invalid-token' },
        json: { destination: 'Paris' },
      });

      expect(response.status).toBe(401);
    });
  });

  describe('validation', () => {
    it('validates required fields', async () => {
      const response = await app.request('/api/bookings', {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        json: {}, // Missing required fields
      });

      expect(response.status).toBe(400);
      expect(await response.json()).toEqual({
        error: 'Validation failed',
        fields: {
          destination: 'Required',
          dates: 'Required',
        },
      });
    });

    it('validates date range', async () => {
      const response = await app.request('/api/bookings', {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        json: {
          destination: 'Paris',
          dates: { start: '2025-06-07', end: '2025-06-01' }, // End before start
        },
      });

      expect(response.status).toBe(400);
    });
  });

  describe('success', () => {
    it('creates booking and returns details', async () => {
      const bookingData = {
        destination: 'Paris',
        dates: { start: '2025-06-01', end: '2025-06-07' },
        guests: 2,
      };

      const response = await app.request('/api/bookings', {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        json: bookingData,
      });

      expect(response.status).toBe(201);

      const json = await response.json();
      expect(json).toMatchObject({
        id: expect.any(String),
        ...bookingData,
        status: 'pending',
        userId: 'user-123',
        createdAt: expect.any(String),
      });

      // Verify database record
      const dbRecord = await db.query.bookings.findFirst({
        where: eq(bookings.id, json.id),
      });

      expect(dbRecord).toBeDefined();
      expect(dbRecord?.destination).toBe('Paris');
    });

    it('associates booking with authenticated user', async () => {
      const response = await app.request('/api/bookings', {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        json: {
          destination: 'London',
          dates: { start: '2025-07-01', end: '2025-07-05' },
          guests: 4,
        },
      });

      const json = await response.json();

      const dbRecord = await db.query.bookings.findFirst({
        where: eq(bookings.id, json.id),
      });

      expect(dbRecord?.userId).toBe('user-123');
    });
  });
});

describe('GET /api/bookings/:id', () => {
  let app: Hono;
  let authToken: string;
  let bookingId: string;

  beforeEach(async () => {
    app = createTestApp();
    authToken = await createAuthenticatedRequest('user-123');

    // Create test booking
    const [booking] = await db
      .insert(bookings)
      .values({
        destination: 'Paris',
        dates: { start: '2025-06-01', end: '2025-06-07' },
        guests: 2,
        userId: 'user-123',
        status: 'confirmed',
      })
      .returning();

    bookingId = booking.id;
  });

  it('returns booking for owner', async () => {
    const response = await app.request(`/api/bookings/${bookingId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({
      id: bookingId,
      destination: 'Paris',
    });
  });

  it('returns 404 for non-existent booking', async () => {
    const response = await app.request('/api/bookings/non-existent', {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status).toBe(404);
  });

  it('returns 403 for other user\'s booking', async () => {
    // Create booking for different user
    const [otherBooking] = await db
      .insert(bookings)
      .values({
        destination: 'London',
        dates: { start: '2025-07-01', end: '2025-07-05' },
        guests: 2,
        userId: 'other-user',
      })
      .returning();

    const response = await app.request(`/api/bookings/${otherBooking.id}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status).toBe(403);
  });
});
```

### Testing Error Handling

```typescript
// src/routes/api/payments.test.ts

describe('POST /api/payments/refund', () => {
  it('handles Stripe errors gracefully', async () => {
    // Mock Stripe to return error
    stripe.refunds.create.mockRejectedValue(
      new Stripe.errors.CardError('Your card was declined')
    );

    const response = await app.request('/api/payments/refund', {
      method: 'POST',
      headers: { Authorization: `Bearer ${authToken}` },
      json: { paymentIntentId: 'pi_test' },
    });

    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({
      error: 'Refund failed',
      message: 'Your card was declined',
    });
  });

  it('handles partial refunds', async () => {
    stripe.refunds.create.mockResolvedValue({
      id: 're_test',
      amount: 5000, // Partial refund
      status: 'succeeded',
    });

    const response = await app.request('/api/payments/refund', {
      method: 'POST',
      headers: { Authorization: `Bearer ${authToken}` },
      json: {
        paymentIntentId: 'pi_test',
        amount: 5000,
      },
    });

    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({
      refundAmount: 5000,
      status: 'partial_refund',
    });
  });
});
```

---

## MSW for API Mocking

### MSW Setup

```typescript
// src/test/mocks/msw-handler.ts

import { setupServer } from 'msw/node';
import { HttpResponse, http } from 'msw';

// Handlers for external APIs
const handlers = [
  // Supplier API
  http.get('https://api.supplier.com/v1/hotels/:id', async ({ params }) => {
    const { id } = params;

    return HttpResponse.json({
      id,
      name: 'Test Hotel',
      destination: 'Paris',
      price: 100,
      availability: true,
    });
  }),

  // Payment gateway
  http.post('https://api.stripe.com/v1/payment_intents', async () => {
    return HttpResponse.json({
      id: 'pi_test',
      client_secret: 'pi_test_secret',
      amount: 10000,
      currency: 'usd',
      status: 'requires_payment_method',
    });
  }),

  // Exchange rate API
  http.get('https://api.exchangerate.host/latest', () => {
    return HttpResponse.json({
      base: 'USD',
      rates: {
        EUR: 0.85,
        GBP: 0.73,
        INR: 83.5,
      },
    });
  }),

  // Error scenarios
  http.get(
    'https://api.supplier.com/v1/hotels/invalid',
    () => new HttpResponse(null, { status: 404 })
  ),

  http.post(
    'https://api.supplier.com/v1/bookings',
    () => new HttpResponse(null, { status: 503 })
  ),
];

// Create server
export const mswServer = setupServer(...handlers);
```

### MSW in Tests

```typescript
// src/components/HotelSearch/HotelSearch.test.tsx

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { mswServer } from '@/test/mocks/msw-handler';
import { HotelSearch } from './HotelSearch';

describe('HotelSearch', () => {
  beforeAll(() => mswServer.listen());
  afterEach(() => mswServer.resetHandlers());
  afterAll(() => mswServer.close());

  it('displays hotels from API', async () => {
    render(<HotelSearch destination="Paris" />);

    await waitFor(() => {
      expect(screen.getByText('Test Hotel')).toBeInTheDocument();
    });
  });

  it('handles API errors', async () => {
    // Override handler for this test
    mswServer.use(
      http.get('https://api.supplier.com/v1/hotels/*', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    render(<HotelSearch destination="Paris" />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load hotels/i)).toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    // Delay response
    mswServer.use(
      http.get('https://api.supplier.com/v1/hotels/*', async () => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return HttpResponse.json({ hotels: [] });
      })
    );

    const { container } = render(<HotelSearch destination="Paris" />);

    expect(container.querySelector('.skeleton-loader')).toBeInTheDocument();
  });
});
```

### Dynamic MSW Handlers

```typescript
// src/test/mocks/dynamic-handlers.ts

import { http, HttpResponse } from 'msw';

// Stateful handlers
let bookingCounter = 0;

export const createBookingHandler = http.post(
  'https://api.supplier.com/v1/bookings',
  async ({ request }) => {
    const body = await request.json();

    bookingCounter++;

    return HttpResponse.json({
      id: `booking-${bookingCounter}`,
      ...body,
      status: 'pending',
      createdAt: new Date().toISOString(),
    });
  }
);

// Conditional handlers
export const createConditionalHandler = (
  condition: (request: Request) => boolean,
  response: Response | HttpResponse
) => {
  return http.post('*', async ({ request }) => {
    if (condition(request)) {
      return response;
    }
    // Fall through to next handler
    return HttpResponse.json({ error: 'Not handled' }, { status: 500 });
  });
};

// Usage
mswServer.use(
  createConditionalHandler(
    (req) => req.headers.get('test-mode') === 'error',
    HttpResponse.json({ error: 'Test error' }, { status: 400 })
  )
);
```

---

## Database Testing

### Test Database Setup

```typescript
// drizzle.config.ts

import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './src/db/schema.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.TEST_DATABASE_URL,
  },
  verbose: true,
  strict: true,
});
```

### Database Test Utilities

```typescript
// src/test/lib/db-test-utils.ts

import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import * as schema from '@/db/schema';
import { bookings, payments, users } from '@/db/schema';

export const testDb = drizzle(
  neon(process.env.TEST_DATABASE_URL!),
  { schema }
);

// Clean tables between tests
export async function cleanupDatabase() {
  await testDb.delete(payments);
  await testDb.delete(bookings);
  await testDb.delete(users);
}

// Insert test data
export async function insertTestUser(overrides = {}) {
  const [user] = await testDb
    .insert(users)
    .values({
      id: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
      ...overrides,
    })
    .returning();

  return user;
}

export async function insertTestBooking(userId: string, overrides = {}) {
  const [booking] = await testDb
    .insert(bookings)
    .values({
      userId,
      destination: 'Paris',
      dates: { start: '2025-06-01', end: '2025-06-07' },
      guests: 2,
      status: 'pending',
      ...overrides,
    })
    .returning();

  return booking;
}

// Transaction wrapper for rollback
export async function withTestDatabase<T>(
  callback: (db: typeof testDb) => Promise<T>
): Promise<T> {
  await testDb.transaction(async (tx) => {
    try {
      return await callback(tx as any);
    } finally {
      await tx.rollback();
    }
  });
}
```

### Testing Database Operations

```typescript
// src/services/booking.service.test.ts

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  cleanupDatabase,
  insertTestUser,
  insertTestBooking,
  testDb,
} from '@/test/lib/db-test-utils';
import { BookingService } from './booking.service';
import { eq } from 'drizzle-orm';
import { bookings } from '@/db/schema';

describe('BookingService', () => {
  let bookingService: BookingService;
  let testUserId: string;

  beforeEach(async () => {
    await cleanupDatabase();
    bookingService = new BookingService(testDb);

    const user = await insertTestUser();
    testUserId = user.id;
  });

  afterEach(async () => {
    await cleanupDatabase();
  });

  describe('createBooking', () => {
    it('creates booking in database', async () => {
      const bookingData = {
        destination: 'Paris',
        dates: { start: '2025-06-01', end: '2025-06-07' },
        guests: 2,
      };

      const booking = await bookingService.createBooking(testUserId, bookingData);

      expect(booking).toMatchObject({
        id: expect.any(String),
        ...bookingData,
        status: 'pending',
        userId: testUserId,
      });

      // Verify in database
      const dbBooking = await testDb.query.bookings.findFirst({
        where: eq(bookings.id, booking.id),
      });

      expect(dbBooking).toBeDefined();
      expect(dbBooking?.destination).toBe('Paris');
    });

    it('calculates total price correctly', async () => {
      const booking = await bookingService.createBooking(
        testUserId,
        {
          destination: 'Paris',
          dates: { start: '2025-06-01', end: '2025-06-07' }, // 6 nights
          guests: 2,
        }
      );

      // 6 nights * 2 guests * $100/night = $1200
      expect(booking.totalPrice).toBe(1200);
    });
  });

  describe('updateBookingStatus', () => {
    it('updates status and timestamps', async () => {
      const booking = await insertTestBooking(testUserId);

      const updated = await bookingService.updateBookingStatus(
        booking.id,
        'confirmed'
      );

      expect(updated.status).toBe('confirmed');
      expect(updated.updatedAt).not.toBe(booking.updatedAt);

      // Verify in database
      const dbBooking = await testDb.query.bookings.findFirst({
        where: eq(bookings.id, booking.id),
      });

      expect(dbBooking?.status).toBe('confirmed');
    });

    it('throws for non-existent booking', async () => {
      await expect(
        bookingService.updateBookingStatus('non-existent', 'confirmed')
      ).rejects.toThrow('Booking not found');
    });
  });

  describe('getUserBookings', () => {
    beforeEach(async () => {
      // Insert multiple bookings
      await insertTestBooking(testUserId, { destination: 'Paris' });
      await insertTestBooking(testUserId, { destination: 'London' });
      await insertTestBooking(testUserId, { destination: 'Tokyo' });
    });

    it('returns all user bookings', async () => {
      const userBookings = await bookingService.getUserBookings(testUserId);

      expect(userBookings).toHaveLength(3);
      expect(userBookings.map(b => b.destination)).toEqual(
        expect.arrayContaining(['Paris', 'London', 'Tokyo'])
      );
    });

    it('supports pagination', async () => {
      const page1 = await bookingService.getUserBookings(testUserId, {
        limit: 2,
        offset: 0,
      });

      const page2 = await bookingService.getUserBookings(testUserId, {
        limit: 2,
        offset: 2,
      });

      expect(page1).toHaveLength(2);
      expect(page2).toHaveLength(1);
    });
  });
});
```

---

## State Management Testing

### Testing TanStack Query

```typescript
// src/hooks/useBookings.test.ts

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useBookings } from './useBookings';
import { testDb, insertTestUser, insertTestBooking, cleanupDatabase } from '@/test/lib/db-test-utils';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

describe('useBookings', () => {
  let queryClient: QueryClient;
  let testUserId: string;

  beforeEach(async () => {
    await cleanupDatabase();
    queryClient = createTestQueryClient();

    const user = await insertTestUser();
    testUserId = user.id;

    // Insert test bookings
    await insertTestBooking(testUserId, { destination: 'Paris' });
    await insertTestBooking(testUserId, { destination: 'London' });
  });

  it('fetches user bookings', async () => {
    const { result } = renderHook(() => useBookings(testUserId), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0].destination).toBe('Paris');
  });

  it('handles loading state', () => {
    const { result } = renderHook(() => useBookings(testUserId), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

    expect(result.current.isLoading).toBe(true);
  });

  it('handles error state', async () => {
    // Use invalid user ID
    const { result } = renderHook(() => useBookings('invalid-user'), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});
```

### Testing Mutations

```typescript
// src/hooks/useCreateBooking.test.ts

describe('useCreateBooking', () => {
  it('creates booking and invalidates queries', async () => {
    const queryClient = createTestQueryClient();

    const { result } = renderHook(() => useCreateBooking(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

    // Initially no bookings cached
    expect(queryClient.getQueryData(['bookings', testUserId])).toBeUndefined();

    // Create booking
    await act(async () => {
      await result.current.mutateAsync({
        destination: 'Paris',
        dates: { start: '2025-06-01', end: '2025-06-07' },
        guests: 2,
      });
    });

    // Query should be invalidated and refetched
    await waitFor(() => {
      const bookings = queryClient.getQueryData(['bookings', testUserId]);
      expect(bookings).toBeDefined();
      expect(bookings).toHaveLength(1);
    });
  });

  it('handles mutation errors', async () => {
    // Mock API to return error
    bookingApi.create.mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useCreateBooking(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          destination: 'Paris',
          dates: { start: '2025-06-01', end: '2025-06-07' },
          guests: 2,
        });
      } catch (error) {
        // Expected to throw
      }
    });

    expect(result.current.error).toBeDefined();
  });
});
```

---

## Third-Party Integration

### Testing Stripe Integration

```typescript
// src/services/payment/stripe.service.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Stripe } from 'stripe';
import { StripeService } from './stripe.service';

// Mock Stripe
vi.mock('stripe', () => ({
  Stripe: vi.fn().mockImplementation(() => ({
    paymentIntents: {
      create: vi.fn(),
      confirm: vi.fn(),
      cancel: vi.fn(),
    },
    refunds: {
      create: vi.fn(),
    },
  })),
}));

describe('StripeService', () => {
  let stripeService: StripeService;
  let mockStripe: Stripe;

  beforeEach(() => {
    mockStripe = new Stripe('test-key');
    stripeService = new StripeService(mockStripe);
  });

  describe('createPaymentIntent', () => {
    it('creates payment intent with correct amount', async () => {
      mockStripe.paymentIntents.create.mockResolvedValue({
        id: 'pi_test',
        amount: 10000,
        currency: 'usd',
        status: 'requires_payment_method',
      });

      const intent = await stripeService.createPaymentIntent({
        amount: 10000,
        currency: 'usd',
        bookingId: 'booking-123',
      });

      expect(mockStripe.paymentIntents.create).toHaveBeenCalledWith({
        amount: 10000,
        currency: 'usd',
        metadata: { bookingId: 'booking-123' },
      });

      expect(intent).toMatchObject({
        id: 'pi_test',
        amount: 10000,
      });
    });

    it('handles Stripe errors', async () => {
      mockStripe.paymentIntents.create.mockRejectedValue(
        new Stripe.errors.CardError('Your card was declined')
      );

      await expect(
        stripeService.createPaymentIntent({
          amount: 10000,
          currency: 'usd',
        })
      ).rejects.toThrow('Your card was declined');
    });
  });

  describe('processRefund', () => {
    it('creates refund with correct amount', async () => {
      mockStripe.refunds.create.mockResolvedValue({
        id: 're_test',
        amount: 5000,
        status: 'succeeded',
      });

      const refund = await stripeService.processRefund('pi_test', 5000);

      expect(mockStripe.refunds.create).toHaveBeenCalledWith({
        payment_intent: 'pi_test',
        amount: 5000,
      });

      expect(refund).toMatchObject({
        id: 're_test',
        amount: 5000,
      });
    });

    it('handles partial refunds', async () => {
      mockStripe.refunds.create.mockResolvedValue({
        id: 're_test',
        amount: 2500,
        status: 'succeeded',
      });

      const refund = await stripeService.processRefund('pi_test', 2500);

      expect(refund.amount).toBe(2500);
    });
  });
});
```

### Testing Supplier API Integration

```typescript
// src/services/suppliers/supplier.service.test.ts

import { describe, it, expect, beforeEach } from 'vitest';
import { SupplierService } from './supplier.service';
import { mswServer, http } from '@/test/mocks/msw-handler';

describe('SupplierService', () => {
  let supplierService: SupplierService;

  beforeEach(() => {
    supplierService = new SupplierService();
    mswServer.listen();
  });

  afterEach(() => {
    mswServer.resetHandlers();
  });

  afterAll(() => {
    mswServer.close();
  });

  describe('searchHotels', () => {
    it('returns hotels from API', async () => {
      mswServer.use(
        http.get('https://api.supplier.com/v1/hotels', () => {
          return HttpResponse.json({
            hotels: [
              { id: '1', name: 'Hotel Paris', price: 100 },
              { id: '2', name: 'Hotel London', price: 80 },
            ],
          });
        })
      );

      const results = await supplierService.searchHotels('Paris', {
        checkIn: '2025-06-01',
        checkOut: '2025-06-07',
        guests: 2,
      });

      expect(results).toHaveLength(2);
      expect(results[0].name).toBe('Hotel Paris');
    });

    it('handles API errors gracefully', async () => {
      mswServer.use(
        http.get('https://api.supplier.com/v1/hotels', () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      await expect(
        supplierService.searchHotels('Paris', {
          checkIn: '2025-06-01',
          checkOut: '2025-06-07',
          guests: 2,
        })
      ).rejects.toThrow('Failed to fetch hotels');
    });

    it('retries on timeout', async () => {
      let attemptCount = 0;

      mswServer.use(
        http.get('https://api.supplier.com/v1/hotels', async () => {
          attemptCount++;
          if (attemptCount < 3) {
            await new Promise(resolve => setTimeout(resolve, 100));
            return new HttpResponse(null, { status: 504 });
          }
          return HttpResponse.json({ hotels: [] });
        })
      );

      const results = await supplierService.searchHotels('Paris', {
        checkIn: '2025-06-01',
        checkOut: '2025-06-07',
        guests: 2,
      });

      expect(attemptCount).toBe(3);
      expect(results).toEqual([]);
    });
  });
});
```

---

## Contract Testing

### API Contract Tests

```typescript
// src/test/contracts/api-contracts.test.ts

import { describe, it, expect } from 'vitest';
import { createTestApp, createAuthenticatedRequest } from '@/test/setup/api-test-setup';
import { validateSchema } from '@/test/lib/validate-schema';

describe('API Contract Tests', () => {
  let app: Hono;
  let authToken: string;

  beforeEach(async () => {
    app = createTestApp();
    authToken = await createAuthenticatedRequest('user-123');
  });

  describe('POST /api/bookings', () => {
    const bookingSchema = {
      type: 'object',
      required: ['id', 'destination', 'dates', 'guests', 'status', 'createdAt'],
      properties: {
        id: { type: 'string', format: 'uuid' },
        destination: { type: 'string' },
        dates: {
          type: 'object',
          required: ['start', 'end'],
          properties: {
            start: { type: 'string', format: 'date' },
            end: { type: 'string', format: 'date' },
          },
        },
        guests: { type: 'number', minimum: 1 },
        status: {
          type: 'string',
          enum: ['pending', 'confirmed', 'cancelled', 'completed'],
        },
        createdAt: { type: 'string', format: 'date-time' },
      },
    };

    it('returns response matching contract', async () => {
      const response = await app.request('/api/bookings', {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        json: {
          destination: 'Paris',
          dates: { start: '2025-06-01', end: '2025-06-07' },
          guests: 2,
        },
      });

      expect(response.status).toBe(201);

      const json = await response.json();
      const valid = validateSchema(json, bookingSchema);

      expect(valid.errors).toEqual([]);
    });
  });

  describe('GET /api/bookings/:id', () => {
    it('returns 404 response matching error contract', async () => {
      const response = await app.request('/api/bookings/non-existent', {
        headers: { Authorization: `Bearer ${authToken}` },
      });

      expect(response.status).toBe(404);

      const json = await response.json();

      expect(json).toMatchObject({
        error: 'Not found',
        code: 'BOOKING_NOT_FOUND',
      });
    });
  });
});
```

---

## Summary

Integration testing strategy:

- **API routes**: Test with real database, mock external services
- **MSW**: Mock external APIs at network level
- **Database**: Use test database, clean between tests
- **State management**: Test queries and mutations with React Query
- **Third-party**: Mock APIs, test error handling
- **Contract testing**: Validate API responses match schema

---

**Next:** [Part 4: E2E Testing](./TESTING_STRATEGY_04_E2E.md) — Playwright setup, critical user journeys, and test data management
