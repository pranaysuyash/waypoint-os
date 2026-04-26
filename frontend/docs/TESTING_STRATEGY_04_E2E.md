# Testing Strategy Part 4: E2E Testing

> Playwright setup, critical user journeys, and test data management

**Series:** Testing Strategy
**Previous:** [Part 3: Integration Testing](./TESTING_STRATEGY_03_INTEGRATION.md)
**Next:** [Part 5: Visual Regression](./TESTING_STRATEGY_05_VISUAL.md)

---

## Table of Contents

1. [E2E Philosophy](#e2e-philosophy)
2. [Playwright Setup](#playwright-setup)
3. [Test Data Management](#test-data-management)
4. [Critical User Journeys](#critical-user-journeys)
5. [Authentication Flows](#authentication-flows)
6. [Payment Testing](#payment-testing)
7. [Flaky Test Mitigation](#flaky-test-mitigation)

---

## E2E Philosophy

### What to Test End-to-End

E2E tests are **expensive and slow**. Reserve them for:

| Priority | What | Example |
|----------|------|---------|
| **P0** | Revenue-critical flows | Booking, payment |
| **P0** | Security-critical flows | Login, logout, password reset |
| **P1** | Core user journeys | Search, trip management |
| **P2** | Important integrations | Supplier sync, notifications |

**Don't E2E test:**
- Individual components (use unit tests)
- Simple forms (use integration tests)
- Static pages (use visual tests)
- Edge cases (use unit tests)

### The E2E Sweet Spot

```
┌─────────────────────────────────────────┐
│  Browser E2E (Playwright)               │
│  ┌───────────────────────────────────┐  │
│  │ Critical User Journeys Only       │  │
│  │ - Booking creation                │  │
│  │ - Payment processing              │  │
│  │ - Authentication                  │  │
│  │ - Trip management                 │  │
│  └───────────────────────────────────┘  │
│  ~20 tests, ~10 minutes                   │
└─────────────────────────────────────────┘
```

---

## Playwright Setup

### Installation

```bash
npm install -D @playwright/test
npx playwright install
```

### Configuration

```typescript
// playwright.config.ts

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Parallel execution
  workers: process.env.CI ? 4 : undefined,

  // Timeout
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },

  // Reporter
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'junit-results.xml' }],
  ],

  // Use
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
  },

  // Projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // Dev server
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
```

### Global Setup

```typescript
// e2e/setup.ts

import { test as base } from '@playwright/test';

// Extend test with fixtures
export const test = base.extend<{
  authenticatedPage: Page;
}>({
  authenticatedPage: async ({ page }, use) => {
    // Login before test
    await page.goto('/login');
    await page.fill('[name="email']', 'test@example.com');
    await page.fill('[name="password"]', 'test-password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    await use(page);

    // Cleanup after test
    // page.close() is automatic
  },
});

export { expect } from '@playwright/test';
```

### Custom Helpers

```typescript
// e2e/helpers/auth.ts

export async function login(page: Page, email?: string) {
  await page.goto('/login');
  await page.fill('[name="email"]', email || 'test@example.com');
  await page.fill('[name="password"]', 'test-password');
  await page.click('button[type="submit"]');
  await page.waitForURL('/dashboard');
}

export async function logout(page: Page) {
  await page.click('[data-testid="user-menu"]');
  await page.click('[data-testid="logout-button"]');
  await page.waitForURL('/login');
}

export async function signup(
  page: Page,
  email: string,
  password: string,
  name: string
) {
  await page.goto('/signup');
  await page.fill('[name="name"]', name);
  await page.fill('[name="email"]', email);
  await page.fill('[name="password"]', password);
  await page.fill('[name="confirmPassword"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('/onboarding');
}
```

```typescript
// e2e/helpers/bookings.ts

export async function createBooking(
  page: Page,
  bookingData: {
    destination: string;
    checkIn: string;
    checkOut: string;
    guests: number;
  }
) {
  await page.goto('/booking/new');

  // Fill form
  await page.fill('[name="destination"]', bookingData.destination);
  await page.fill('[name="checkIn"]', bookingData.checkIn);
  await page.fill('[name="checkOut"]', bookingData.checkOut);
  await page.fill('[name="guests"]', bookingData.guests.toString());

  // Submit
  await page.click('button[type="submit"]');

  // Wait for confirmation
  await page.waitForSelector('[data-testid="booking-confirmation"]');
}

export async function cancelBooking(page: Page, bookingId: string) {
  await page.goto(`/bookings/${bookingId}`);
  await page.click('[data-testid="cancel-booking-button"]');
  await page.click('[data-testid="confirm-cancel-button"]');
  await page.waitForSelector('[data-testid="booking-cancelled"]');
}
```

---

## Test Data Management

### Test Database Strategy

```typescript
// e2e/setup/db.ts

import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import * as schema from '@/db/schema';

const TEST_DB_URL = process.env.E2E_TEST_DATABASE_URL;
const sql = neon(TEST_DB_URL);
export const e2eDb = drizzle(sql, { schema });

// Clean database before test run
export async function resetDatabase() {
  await sql.query('DROP SCHEMA public CASCADE');
  await sql.query('CREATE SCHEMA public');

  // Run migrations
  await migrate(e2eDb, { migrationsFolder: 'drizzle' });
}

// Seed test data
export async function seedTestData() {
  // Create test users
  await e2eDb.insert(schema.users).values([
    {
      id: 'user-agent',
      email: 'agent@example.com',
      role: 'agent',
      name: 'Test Agent',
    },
    {
      id: 'user-customer',
      email: 'customer@example.com',
      role: 'customer',
      name: 'Test Customer',
    },
  ]);

  // Create test agency
  await e2eDb.insert(schema.agencies).values({
    id: 'agency-1',
    name: 'Test Agency',
    slug: 'test-agency',
  });
}

// Create unique test user per test
export async function createTestUser(suffix: string) {
  const userId = `user-${suffix}`;
  const email = `test-${suffix}@example.com`;

  const [user] = await e2eDb
    .insert(schema.users)
    .values({
      id: userId,
      email,
      name: `Test User ${suffix}`,
    })
    .returning();

  return { userId, email, password: 'test-password' };
}
```

### Fixtures

```typescript
// e2e/fixtures/fixtures.ts

import { test as base } from '@playwright/test';

type TestUser = {
  id: string;
  email: string;
  password: string;
};

export const test = base.extend<{
  testUser: TestUser;
}>({
  testUser: async ({ }, use, testInfo) => {
    // Create unique user for this test
    const suffix = `${testInfo.parallelIndex}-${Date.now()}`;
    const user = await createTestUser(suffix);

    await use(user);

    // Cleanup: delete user
    await e2eDb.delete(schema.users).where(eq(schema.users.id, user.id));
  },
});

export { expect } from '@playwright/test';
```

### API-First Test Data

```typescript
// e2e/helpers/api.ts

import { request } from '@playwright/test';

const API_BASE = 'http://localhost:3000/api';

export async function createBookingViaAPI(accessToken: string, bookingData: any) {
  const context = await request.newContext({
    baseURL: API_BASE,
    extraHTTPHeaders: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  const response = await context.post('/bookings', {
    data: bookingData,
  });

  return await response.json();
}

export async function getAccessToken(email: string, password: string) {
  const context = await request.newContext({ baseURL: API_BASE });

  const response = await context.post('/auth/login', {
    data: { email, password },
  });

  const { token } = await response.json();
  return token;
}
```

---

## Critical User Journeys

### Journey 1: New Booking Creation

```typescript
// e2e/journeys/booking-creation.spec.ts

import { test, expect } from '../fixtures/fixtures';
import { login } from '../helpers/auth';

test.describe('Booking Creation Journey', () => {
  test('agent creates new booking from inquiry', async ({ page, testUser }) => {
    // Login
    await login(page, testUser.email);

    // Start from inquiry
    await page.goto('/inbox/inquiry-123');

    // Verify inquiry details
    await expect(page.locator('[data-testid="inquiry-destination"]')).toHaveText('Paris');
    await expect(page.locator('[data-testid="inquiry-dates"]')).toHaveText('Jun 1-7, 2025');

    // Click "Create Booking"
    await page.click('[data-testid="create-booking-button"]');

    // Verify booking form pre-filled
    await expect(page.locator('[name="destination"]')).toHaveValue('Paris');
    await expect(page.locator('[name="checkIn"]')).toHaveValue('2025-06-01');
    await expect(page.locator('[name="checkOut"]')).toHaveValue('2025-06-07');

    // Add accommodation
    await page.click('[data-testid="add-accommodation"]');
    await page.click('[data-testid="hotel-option-0"]'); // Select first hotel

    // Add transport
    await page.click('[data-testid="add-transport"]');
    await page.click('[data-testid="flight-option-0"]');

    // Review and confirm
    await page.click('[data-testid="review-button"]');

    // Verify summary
    await expect(page.locator('[data-testid="total-price"]')).toBeVisible();
    await expect(page.locator('[data-testid="booking-summary"]')).toContainText('Paris');

    // Create booking
    await page.click('[data-testid="confirm-booking-button"]');

    // Verify success
    await expect(page.locator('[data-testid="booking-confirmation"]')).toBeVisible();
    await expect(page.locator('[data-testid="booking-id"]')).toContainText('BK-');

    // Verify redirect to booking detail
    await expect(page).toHaveURL(/\/bookings\/BK-\d+/);
  });

  test('validates form before submission', async ({ page, testUser }) => {
    await login(page, testUser.email);
    await page.goto('/booking/new');

    // Try to submit without required fields
    await page.click('[data-testid="confirm-booking-button"]');

    // Verify validation errors
    await expect(page.locator('[data-testid="error-destination"]')).toHaveText('Destination is required');
    await expect(page.locator('[data-testid="error-dates"]')).toHaveText('Dates are required');
  });

  test('handles supplier API errors gracefully', async ({ page, testUser }) => {
    await login(page, testUser.email);
    await page.goto('/booking/new');

    // Fill form
    await page.fill('[name="destination"]', 'Paris');
    await page.fill('[name="checkIn"]', '2025-06-01');
    await page.fill('[name="checkOut"]', '2025-06-07');

    // Mock supplier API error
    await page.route('**/api/suppliers/hotels**', route => {
      route.fulfill({
        status: 503,
        body: JSON.stringify({ error: 'Supplier unavailable' }),
      });
    });

    // Search for hotels
    await page.click('[data-testid="search-hotels"]');

    // Verify error display
    await expect(page.locator('[data-testid="api-error"]')).toHaveText(/supplier unavailable/i);

    // Verify retry option
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });
});
```

### Journey 2: Payment Processing

```typescript
// e2e/journeys/payment.spec.ts

import { test, expect } from '../fixtures/fixtures';

test.describe('Payment Journey', () => {
  test('customer pays booking deposit', async ({ page, testUser }) => {
    // Create booking first
    const { bookingId } = await createTestBooking(page, testUser);

    // Go to payment
    await page.goto(`/bookings/${bookingId}/payment`);

    // Verify amount
    await expect(page.locator('[data-testid="deposit-amount"]')).toContainText('$200.00');

    // Enter card details (test card)
    await page.fill('[name="cardNumber"]', '4242424242424242');
    await page.fill('[name="expiry"]', '12/25');
    await page.fill('[name="cvc"]', '123');
    await page.fill('[name="name"]', 'Test User');

    // Submit payment
    await page.click('[data-testid="pay-button"]');

    // Verify processing state
    await expect(page.locator('[data-testid="payment-processing"]')).toBeVisible();

    // Verify success
    await expect(page.locator('[data-testid="payment-success"]')).toBeVisible();

    // Verify booking status updated
    await page.goto(`/bookings/${bookingId}`);
    await expect(page.locator('[data-testid="booking-status"]')).toHaveText('Deposit Paid');
  });

  test('handles payment failure', async ({ page, testUser }) => {
    const { bookingId } = await createTestBooking(page, testUser);

    await page.goto(`/bookings/${bookingId}/payment`);

    // Use declined card
    await page.fill('[name="cardNumber"]', '4000000000000002');
    await page.fill('[name="expiry"]', '12/25');
    await page.fill('[name="cvc"]', '123');
    await page.click('[data-testid="pay-button"]');

    // Verify error
    await expect(page.locator('[data-testid="payment-error"]')).toHaveText(/card declined/i);

    // Verify retry option
    await expect(page.locator('[name="cardNumber"]')).toBeEditable();
  });

  test('saves payment method for future', async ({ page, testUser }) => {
    const { bookingId } = await createTestBooking(page, testUser);

    await page.goto(`/bookings/${bookingId}/payment`);

    // Check "Save for future"
    await page.check('[name="saveCard"]');

    // Enter card
    await page.fill('[name="cardNumber"]', '4242424242424242');
    await page.fill('[name="expiry"]', '12/25');
    await page.fill('[name="cvc"]', '123');
    await page.click('[data-testid="pay-button"]');

    // Verify success
    await expect(page.locator('[data-testid="payment-success"]')).toBeVisible();

    // Verify saved
    await page.goto('/settings/payment-methods');
    await expect(page.locator('[data-testid="saved-card"]')).toContainText('4242');
  });
});
```

### Journey 3: Trip Management

```typescript
// e2e/journeys/trip-management.spec.ts

import { test, expect } from '../fixtures/fixtures';

test.describe('Trip Management Journey', () => {
  test('agent updates booking details', async ({ page, testUser }) => {
    await login(page, testUser.email);

    // Go to existing booking
    await page.goto('/bookings/booking-123');

    // Click edit
    await page.click('[data-testid="edit-booking-button"]');

    // Change dates
    await page.fill('[name="checkIn"]', '2025-06-15');
    await page.fill('[name="checkOut"]', '2025-06-20');

    // Save
    await page.click('[data-testid="save-button"]');

    // Verify success message
    await expect(page.locator('[data-testid="toast-success"]')).toHaveText(/updated/i);

    // Verify new dates displayed
    await expect(page.locator('[data-testid="booking-dates"]')).toHaveText('Jun 15-20, 2025');
  });

  test('customer views trip timeline', async ({ page, testUser }) => {
    await loginAsCustomer(page, testUser.email);
    await page.goto('/trips/trip-123');

    // Verify timeline
    await expect(page.locator('[data-testid="timeline-item"]')).toHaveCount(5);

    // Verify events in order
    const events = await page.locator('[data-testid="timeline-item"]').allTextContents();
    expect(events[0]).toContain('Inquiry received');
    expect(events[1]).toContain('Quote sent');
    expect(events[2]).toContain('Booking confirmed');
    expect(events[3]).toContain('Deposit paid');
    expect(events[4]).toContain('Documents sent');
  });

  test('agent sends message to customer', async ({ page, testUser }) => {
    await login(page, testUser.email);
    await page.goto('/bookings/booking-123');

    // Open communication panel
    await page.click('[data-testid="communication-button"]');

    // Type message
    await page.fill('[data-testid="message-input"]', 'Your booking is confirmed!');

    // Send
    await page.click('[data-testid="send-button"]');

    // Verify message appears
    await expect(page.locator('[data-testid="message-sent"]')).toBeVisible();

    // Verify in thread
    await expect(page.locator('[data-testid="message-thread"]')).toContainText('Your booking is confirmed!');
  });
});
```

---

## Authentication Flows

### Login Flow

```typescript
// e2e/auth/login.spec.ts

import { test, expect } from '../fixtures/fixtures';

test.describe('Authentication', () => {
  test('successful login', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'agent@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');

    // Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Verify user menu shows logged in state
    await expect(page.locator('[data-testid="user-menu"]')).toContainText('Agent');
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'agent@example.com');
    await page.fill('[name="password"]', 'wrong-password');
    await page.click('button[type="submit"]');

    // Verify error message
    await expect(page.locator('[data-testid="login-error"]')).toHaveText(/invalid credentials/i);

    // Verify still on login page
    await expect(page).toHaveURL('/login');
  });

  test('redirects to intended page after login', async ({ page }) => {
    // Try to access protected page
    await page.goto('/bookings/booking-123');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login.*/);

    // Login
    await page.fill('[name="email"]', 'agent@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');

    // Should redirect back to intended page
    await expect(page).toHaveURL('/bookings/booking-123');
  });

  test('logout', async ({ page, testUser }) => {
    await login(page, testUser.email);

    // Click logout
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');

    // Verify redirect to login
    await expect(page).toHaveURL('/login');

    // Verify cannot access protected routes
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });
});
```

### Password Reset Flow

```typescript
// e2e/auth/password-reset.spec.ts

test.describe('Password Reset', () => {
  test('requests password reset', async ({ page }) => {
    await page.goto('/login');
    await page.click('[data-testid="forgot-password-link"]');

    await expect(page).toHaveURL('/forgot-password');

    await page.fill('[name="email"]', 'agent@example.com');
    await page.click('[data-testid="send-reset-link"]');

    // Verify success message
    await expect(page.locator('[data-testid="reset-sent"]')).toHaveText(/check your email/i);
  });

  test('resets password with valid token', async ({ page, testUser }) => {
    // Get reset token from API
    const resetToken = await getPasswordResetToken(testUser.email);

    await page.goto(`/reset-password?token=${resetToken}`);

    await page.fill('[name="password"]', 'new-password');
    await page.fill('[name="confirmPassword"]', 'new-password');
    await page.click('[data-testid="reset-password"]');

    // Verify success
    await expect(page.locator('[data-testid="reset-success"]')).toHaveText(/password updated/i);

    // Verify can login with new password
    await page.click('[data-testid="login-link"]');
    await page.fill('[name="email"]', testUser.email);
    await page.fill('[name="password"]', 'new-password');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
  });
});
```

---

## Payment Testing

### Stripe Test Cards

```typescript
// e2e/payment/test-cards.ts

export const testCards = {
  // Success cards
  visa: '4242424242424242',
  visaDebit: '4000056655665556',
  mastercard: '5555555555554444',

  // Failure cards
  declined: '4000000000000002',
  insufficientFunds: '4000000000009995',
  lostCard: '4000000000009987',
  stolenCard: '4000000000009979',

  // Requires action
  requires3DS: '4000002760003184',
  requiresOfflinePin: '4000002760003184',
};

export const cardResults = {
  success: 'succeeded',
  requiresAction: 'requires_action',
  declined: 'card_declined',
};
```

### Payment Scenarios

```typescript
// e2e/payment/scenarios.spec.ts

test.describe('Payment Scenarios', () => {
  test('handles 3D Secure authentication', async ({ page }) => {
    await page.goto('/booking/test-booking/payment');

    // Use card that requires 3DS
    await page.fill('[name="cardNumber"]', testCards.requires3DS);
    await page.fill('[name="expiry"]', '12/25');
    await page.fill('[name="cvc"]', '123');
    await page.click('[data-testid="pay-button"]');

    // Should show 3D Secure modal
    await expect(page.locator('[data-testid="3ds-modal"]')).toBeVisible();

    // Complete 3DS
    await page.fill('[name="3ds-otp"]', '123456');
    await page.click('[data-testid="3ds-submit"]');

    // Verify payment success
    await expect(page.locator('[data-testid="payment-success"]')).toBeVisible();
  });

  test('handles partial refund', async ({ page, testUser }) => {
    // Create and pay for booking
    const { bookingId } = await createAndPayBooking(page, testUser);

    // Go to booking detail
    await page.goto(`/bookings/${bookingId}`);
    await page.click('[data-testid="refund-button"]');

    // Enter partial amount
    await page.fill('[name="refundAmount"]', '100');
    await page.click('[data-testid="process-refund"]');

    // Verify success
    await expect(page.locator('[data-testid="refund-success"]')).toBeVisible();

    // Verify refund status
    await expect(page.locator('[data-testid="refund-status"]')).toHaveText('Partial Refund');
  });

  test('processes full refund', async ({ page, testUser }) => {
    const { bookingId } = await createAndPayBooking(page, testUser);

    await page.goto(`/bookings/${bookingId}`);
    await page.click('[data-testid="refund-button"]');

    // Select full refund
    await page.check('[name="fullRefund"]');

    await page.click('[data-testid="process-refund"]');

    // Verify success
    await expect(page.locator('[data-testid="refund-success"]')).toBeVisible();

    // Verify booking status
    await expect(page.locator('[data-testid="booking-status"]')).toHaveText('Refunded');
  });
});
```

---

## Flaky Test Mitigation

### Waiting Strategies

```typescript
// ✅ Good: Use explicit waits
await page.waitForSelector('[data-testid="booking-confirmed"]');
await page.waitForURL(/\/bookings\/.*/);
await page.waitForResponse(resp => resp.url().includes('/api/bookings'));

// ❌ Bad: Fixed timeouts
await page.waitForTimeout(5000); // Too brittle
```

### Selectors

```typescript
// ✅ Good: Stable data attributes
await page.click('[data-testid="submit-button"]');

// ✅ Good: Accessible names
await page.click('button', { name: 'Submit Booking' });

// ❌ Bad: CSS classes
await page.click('.btn-primary.btn-submit'); // Can change

// ❌ Bad: Text content
await page.click('text=Submit'); // Can change with i18n
```

### Retry Logic

```typescript
// playwright.config.ts

export default defineConfig({
  retries: process.env.CI ? 2 : 0,

  // Test-specific retries
  use: {
    trace: 'retain-on-failure',
  },
});
```

### Test Isolation

```typescript
// ✅ Good: Each test creates its own data
test('creates booking', async ({ page }) => {
  const bookingId = `test-${Date.now()}`;
  await createBooking(page, { id: bookingId });
});

// ❌ Bad: Tests share state
test('creates booking', async ({ page }) => {
  await createBooking(page, { id: 'shared-id' });
});
```

### Network Conditions

```typescript
// Test slow networks
test.use({
  offline: false,
  serviceWorkers: 'block',
});

test('handles slow network', async ({ page }) => {
  // Simulate slow API
  await page.route('**/api/**', route => {
    setTimeout(() => route.continue(), 2000);
  });

  // Verify loading state
  await page.goto('/booking/new');
  await expect(page.locator('[data-testid="loading"]')).toBeVisible();
});
```

---

## Summary

E2E testing strategy for the travel agency platform:

- **Playwright** for cross-browser E2E tests
- **Critical journeys only** — booking, payment, auth
- **Test data management** — unique per test, cleanup after
- **Flaky test prevention** — explicit waits, stable selectors, isolation
- **~20 tests** covering critical paths
- **~10 minute** target for full suite

---

**Next:** [Part 5: Visual Regression](./TESTING_STRATEGY_05_VISUAL.md) — Chromatic, Storybook, and screenshot testing
