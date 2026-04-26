# Testing Strategy Part 2: Unit Testing

> Component testing, hooks, utilities, and Vitest configuration

**Series:** Testing Strategy
**Previous:** [Part 1: Testing Philosophy](./TESTING_STRATEGY_01_PHILOSOPHY.md)
**Next:** [Part 3: Integration Testing](./TESTING_STRATEGY_03_INTEGRATION.md)

---

## Table of Contents

1. [Vitest Setup](#vitest-setup)
2. [React Testing Library](#react-testing-library)
3. [Component Testing](#component-testing)
4. [Hook Testing](#hook-testing)
5. [Utility Testing](#utility-testing)
6. [Mocking Strategies](#mocking-strategies)
7. [Test Data](#test-data)
8. [Coverage](#coverage)

---

## Vitest Setup

### Configuration

```typescript
// vitest.config.ts

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/stories/**',
        '**/mockData/**',
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 65,
        statements: 70,
      },
    },
    include: ['**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache'],
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        minThreads: 1,
        maxThreads: 4,
      },
    },
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@test': path.resolve(__dirname, './src/test'),
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@test': path.resolve(__dirname, './src/test'),
    },
  },
});
```

### Test Setup

```typescript
// src/test/setup.ts

import { vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));
```

### Package Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage",
    "test:watch": "vitest --watch"
  }
}
```

---

## React Testing Library

### Helper Utilities

```typescript
// src/test/lib/test-utils.tsx

import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/features/auth/providers/AuthProvider';
import { ThemeProvider } from '@/theme';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/test/lib/i18n';

// Create test QueryClient
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

// Custom render with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  route?: string;
  authState?: AuthState;
}

function renderWithProviders(
  ui: ReactElement,
  {
    queryClient = createTestQueryClient(),
    route = '/',
    authState,
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  // Set route
  window.history.pushState({}, 'Test page', route);

  // Wrapper with all providers
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <AuthProvider initialState={authState}>
            <ThemeProvider>
              <I18nextProvider i18n={i18n}>
                {children}
              </I18nextProvider>
            </ThemeProvider>
          </AuthProvider>
        </QueryClientProvider>
      </BrowserRouter>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

// Re-export everything
export * from '@testing-library/react';
export { renderWithProviders as render };
```

### Custom Queries

```typescript
// src/test/lib/queries.ts

import { within } from '@testing-library/react';

// Travel-specific queries
const travelQueries = {
  // Find by data attribute (preferred)
  findByDataAttr: (container: HTMLElement, attr: string) =>
    container.querySelector(`[data-${attr}]`) as HTMLElement | null,

  // Find booking card
  findBookingCard: (container: HTMLElement, bookingId: string) =>
    within(container).queryByTestId(`booking-${bookingId}`),

  // Find trip status
  findTripStatus: (container: HTMLElement) =>
    within(container).queryByTestId('trip-status'),

  // Find currency display
  findCurrency: (container: HTMLElement, amount: string) =>
    within(container).queryByText(new RegExp(`\\$${amount}`)),
};

// Extend queries
export const queries = {
  ...travelQueries,
};
```

---

## Component Testing

### Testing User Interactions

```typescript
// src/components/BookingForm/BookingForm.test.tsx

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BookingForm } from './BookingForm';

describe('BookingForm', () => {
  describe('form submission', () => {
    it('submits with valid data', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();

      render(<BookingForm onSubmit={onSubmit} />);

      // Fill form
      await user.type(
        screen.getByLabelText(/destination/i),
        'Paris'
      );
      await user.type(
        screen.getByLabelText(/check-in/i),
        '2025-06-01'
      );
      await user.type(
        screen.getByLabelText(/email/i),
        'test@example.com'
      );

      // Submit
      await user.click(
        screen.getByRole('button', { name: /create booking/i })
      );

      // Assert
      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            destination: 'Paris',
            email: 'test@example.com',
          })
        );
      });
    });

    it('shows validation errors for invalid email', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();

      render(<BookingForm onSubmit={onSubmit} />);

      await user.type(screen.getByLabelText(/email/i), 'not-an-email');
      await user.click(screen.getByRole('button', { name: /submit/i }));

      expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  describe('conditional rendering', () => {
    it('shows guest count when accommodation selected', async () => {
      const user = userEvent.setup();
      render(<BookingForm />);

      // Initially hidden
      expect(
        screen.queryByLabelText(/number of guests/i)
      ).not.toBeInTheDocument();

      // Select accommodation
      await user.selectOptions(
        screen.getByLabelText(/service type/i),
        'accommodation'
      );

      // Now visible
      expect(
        screen.getByLabelText(/number of guests/i)
      ).toBeInTheDocument();
    });
  });
});
```

### Testing Error States

```typescript
// src/components/BookingCard/BookingCard.test.tsx

describe('BookingCard', () => {
  describe('error states', () => {
    it('display API error message', () => {
      render(
        <BookingCard
          booking={testBookings.paris}
          error="Failed to load booking details"
        />
      );

      expect(
        screen.getByRole('alert')
      ).toHaveTextContent(/failed to load/i);
    });

    it('allows retry on error', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();

      render(
        <BookingCard
          booking={testBookings.paris}
          error="Failed to load"
          onRetry={onRetry}
        />
      );

      await user.click(screen.getByRole('button', { name: /retry/i }));

      expect(onRetry).toHaveBeenCalled();
    });
  });

  describe('loading states', () => {
    it('shows skeleton while loading', () => {
      const { container } = render(
        <BookingCard booking={testBookings.paris} loading />
      );

      expect(
        container.querySelector('.skeleton')
      ).toBeInTheDocument();
    });
  });
});
```

### Testing Async Behavior

```typescript
// src/components/TripSearch/TripSearch.test.tsx

import { defer } from 'react-router-dom';

describe('TripSearch', () => {
  it('displays search results after API call', async () => {
    const results = [
      { id: '1', name: 'Paris Trip', price: 1000 },
      { id: '2', name: 'London Trip', price: 800 },
    ];

    // Mock router data
    const loader = () => defer({ results });

    render(<TripSearch />, {
      wrapper: ({ children }) => (
        <MemoryRouter initialEntries={['/search?q=paris']}>
          <Routes>
            <Route path="/search" element={<TripSearch />} loader={loader} />
          </Routes>
        </MemoryRouter>
      ),
    });

    // Loading state
    expect(screen.getByText(/searching/i)).toBeInTheDocument();

    // Results appear
    await waitFor(() => {
      expect(screen.getByText('Paris Trip')).toBeInTheDocument();
      expect(screen.getByText('London Trip')).toBeInTheDocument();
    });
  });

  it('handles empty results', async () => {
    render(<TripSearch />, {
      wrapper: () => (
        <MemoryRouter>
          <Routes>
            <Route path="/search" element={<TripSearch />} loader={() => ({ results: [] })} />
          </Routes>
        </MemoryRouter>
      ),
    );

    await waitFor(() => {
      expect(screen.getByText(/no trips found/i)).toBeInTheDocument();
    });
  });
});
```

---

## Hook Testing

### Testing Custom Hooks

```typescript
// src/hooks/useBookingForm.test.ts

import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useBookingForm } from './useBookingForm';
import { bookingApi } from '@/api/booking';

vi.mock('@/api/booking');

describe('useBookingForm', () => {
  it('initializes with default values', () => {
    const { result } = renderHook(() => useBookingForm());

    expect(result.current.values).toEqual({
      destination: '',
      dates: { start: null, end: null },
      guests: 1,
    });
    expect(result.current.errors).toEqual({});
  });

  it('validates required fields', async () => {
    const { result } = renderHook(() => useBookingForm());

    await act(async () => {
      await result.current.submit();
    });

    expect(result.current.errors).toEqual({
      destination: 'Destination is required',
      'dates.start': 'Check-in date is required',
    });
  });

  it('submits valid booking', async () => {
    bookingApi.create.mockResolvedValue({ id: 'booking-123' });

    const { result } = renderHook(() => useBookingForm());

    await act(async () => {
      result.current.setField('destination', 'Paris');
      result.current.setField('dates.start', '2025-06-01');
      result.current.setField('dates.end', '2025-06-07');
      await result.current.submit();
    });

    await waitFor(() => {
      expect(result.current.status).toBe('success');
      expect(result.current.bookingId).toBe('booking-123');
    });
  });

  it('handles API errors', async () => {
    bookingApi.create.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useBookingForm());

    await act(async () => {
      result.current.setField('destination', 'Paris');
      result.current.setField('dates.start', '2025-06-01');
      result.current.setField('dates.end', '2025-06-07');
      await result.current.submit();
    });

    await waitFor(() => {
      expect(result.current.status).toBe('error');
      expect(result.current.errors.api).toBe('Network error');
    });
  });
});
```

### Testing Context Hooks

```typescript
// src/hooks/useAuth.test.ts

import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './useAuth';

describe('useAuth', () => {
  it('provides auth state', () => {
    const wrapper = ({ children }) => (
      <AuthProvider>
        {children}
      </AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('handles login', async () => {
    const wrapper = ({ children }) => (
      <AuthProvider>
        {children}
      </AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login('user@example.com', 'password');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(
      expect.objectContaining({ email: 'user@example.com' })
    );
  });

  it('handles logout', async () => {
    const wrapper = ({ children }) => (
      <AuthProvider>
        {children}
      </AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Login first
    await act(async () => {
      await result.current.login('user@example.com', 'password');
    });

    expect(result.current.isAuthenticated).toBe(true);

    // Logout
    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
});
```

---

## Utility Testing

### Pure Function Tests

```typescript
// src/utils/currency.test.ts

import { describe, it, expect } from 'vitest';
import { formatCurrency, convertCurrency } from './currency';

describe('formatCurrency', () => {
  it('formats USD correctly', () => {
    expect(formatCurrency(1000, 'USD')).toBe('$1,000.00');
    expect(formatCurrency(0, 'USD')).toBe('$0.00');
    expect(formatCurrency(-100, 'USD')).toBe('-$100.00');
  });

  it('formats EUR correctly', () => {
    expect(formatCurrency(1000, 'EUR')).toBe('1.000,00 €');
    expect(formatCurrency(1000.50, 'EUR')).toBe('1.000,50 €');
  });

  it('formats INR with Indian numbering', () => {
    expect(formatCurrency(100000, 'INR')).toBe('₹1,00,000');
    expect(formatCurrency(10000000, 'INR')).toBe('₹1,00,00,000');
  });

  it('respects locale options', () => {
    expect(
      formatCurrency(1000, 'USD', { minimumFractionDigits: 0 })
    ).toBe('$1,000');
  });
});

describe('convertCurrency', () => {
  const mockRates = {
    USD: 1,
    EUR: 0.85,
    GBP: 0.73,
    INR: 83.5,
  };

  it('converts between currencies', () => {
    expect(convertCurrency(100, 'USD', 'EUR', mockRates)).toBe(85);
    expect(convertCurrency(100, 'EUR', 'GBP', mockRates)).toBeCloseTo(85.88, 2);
  });

  it('handles zero amount', () => {
    expect(convertCurrency(0, 'USD', 'EUR', mockRates)).toBe(0);
  });

  it('rounds appropriately', () => {
    expect(convertCurrency(10, 'USD', 'EUR', mockRates)).toBe(8.5);
    expect(convertCurrency(1.23, 'USD', 'INR', mockRates)).toBeCloseTo(102.71, 2);
  });
});
```

### Date Utility Tests

```typescript
// src/utils/dates.test.ts

import { describe, it, expect } from 'vitest';
import {
  formatTravelDate,
  calculateNights,
  isValidDateRange,
  addDays,
} from './dates';

describe('formatTravelDate', () => {
  it('formats date range', () => {
    expect(
      formatTravelDate('2025-06-01', '2025-06-07', 'en-US')
    ).toBe('Jun 1 - 7, 2025');
  });

  it('handles same-day range', () => {
    expect(
      formatTravelDate('2025-06-01', '2025-06-01', 'en-US')
    ).toBe('Jun 1, 2025');
  });

  it('supports other locales', () => {
    expect(
      formatTravelDate('2025-06-01', '2025-06-07', 'fr-FR')
    ).toBe('1 juin 2025');
  });
});

describe('calculateNights', () => {
  it('calculates nights between dates', () => {
    expect(calculateNights('2025-06-01', '2025-06-07')).toBe(6);
    expect(calculateNights('2025-06-01', '2025-06-02')).toBe(1);
  });

  it('handles invalid ranges', () => {
    expect(calculateNights('2025-06-07', '2025-06-01')).toBe(0);
  });
});

describe('isValidDateRange', () => {
  it('validates date ranges', () => {
    expect(isValidDateRange('2025-06-01', '2025-06-07')).toBe(true);
    expect(isValidDateRange('2025-06-07', '2025-06-01')).toBe(false);
    expect(isValidDateRange('2025-06-01', '2025-06-01')).toBe(true);
  });

  it('rejects past dates', () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    expect(isValidDateRange(yesterday.toISOString(), '2025-06-01')).toBe(false);
  });
});
```

---

## Mocking Strategies

### API Mocking

```typescript
// src/test/mocks/api.ts

import { vi } from 'vitest';
import { bookingApi, paymentApi, searchApi } from '@/api';

// Mock implementations
export const mockBookingApi = {
  create: vi.fn(),
  get: vi.fn(),
  update: vi.fn(),
  cancel: vi.fn(),
};

export const mockPaymentApi = {
  createIntent: vi.fn(),
  confirm: vi.fn(),
  refund: vi.fn(),
};

export const mockSearchApi = {
  search: vi.fn(),
  suggest: vi.fn(),
};

// Apply mocks
vi.mock('@/api/booking', () => ({ bookingApi: mockBookingApi }));
vi.mock('@/api/payment', () => ({ paymentApi: mockPaymentApi }));
vi.mock('@/api/search', () => ({ searchApi: mockSearchApi }));

// Helper to reset mocks
export const resetApiMocks = () => {
  Object.values(mockBookingApi).forEach(mock => mock.mockReset());
  Object.values(mockPaymentApi).forEach(mock => mock.mockReset());
  Object.values(mockSearchApi).forEach(mock => mock.mockReset());
};

// Helper to setup default responses
export const setupDefaultMocks = () => {
  mockBookingApi.create.mockResolvedValue({
    id: 'booking-123',
    status: 'pending',
  });

  mockPaymentApi.createIntent.mockResolvedValue({
    clientSecret: 'pi_test',
    amount: 1000,
  });

  mockSearchApi.search.mockResolvedValue({
    results: [],
    total: 0,
  });
};
```

### Component Mocking

```typescript
// src/test/mocks/components.tsx

import { ReactElement } from 'react';

// Mock complex child components
export const MockDatePicker = ({ value, onChange }: any) => (
  <input
    type="date"
    value={value}
    onChange={(e) => onChange(e.target.value)}
    data-testid="date-picker"
  />
);

export const MockMap = ({ location }: any) => (
  <div data-testid="map" data-location={location}>
    Map Placeholder
  </div>
);

// Mock in tests
vi.mock('@/components/DatePicker', () => ({
  DatePicker: MockDatePicker,
}));

vi.mock('@/components/Map', () => ({
  Map: MockMap,
}));
```

### Router Mocking

```typescript
// src/test/mocks/router.tsx

import { MemoryRouter } from 'react-router-dom';

export const createRouterWrapper = (initialEntries = ['/']) => {
  return ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={initialEntries}>
      {children}
    </MemoryRouter>
  );
};

// Usage
render(<Component />, {
  wrapper: createRouterWrapper(['/booking/123']),
});
```

---

## Test Data

### Factory Functions

```typescript
// src/test/factories/bookings.ts

import { Booking } from '@/types';

export const createBooking = (overrides: Partial<Booking> = {}): Booking => ({
  id: 'booking-' + Math.random().toString(36).substr(2, 9),
  destination: 'Paris',
  dates: {
    start: '2025-06-01',
    end: '2025-06-07',
  },
  guests: 2,
  status: 'pending',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  ...overrides,
});

// Preset test data
export const testBookings = {
  pending: createBooking({ status: 'pending' }),
  confirmed: createBooking({ status: 'confirmed' }),
  cancelled: createBooking({ status: 'cancelled' }),
  paris: createBooking({ destination: 'Paris' }),
  london: createBooking({ destination: 'London' }),
};
```

### Sequence Builders

```typescript
// src/test/factories/sequences.ts

export const createBookingSequence = (count: number) =>
  Array.from({ length: count }, (_, i) =>
    createBooking({
      id: `booking-${i + 1}`,
      createdAt: new Date(Date.now() - i * 86400000).toISOString(),
    })
  );

export const createDateSequence = (
  start: string,
  days: number
): string[] =>
  Array.from({ length: days }, (_, i) => {
    const date = new Date(start);
    date.setDate(date.getDate() + i);
    return date.toISOString().split('T')[0];
  });
```

---

## Coverage

### Coverage Configuration

```typescript
// vitest.config.ts (coverage section)

coverage: {
  provider: 'v8',
  reporter: ['text', 'json', 'html', 'lcov'],
  reportsDirectory: './coverage',
  exclude: [
    'node_modules/',
    'src/test/',
    '**/*.d.ts',
    '**/*.config.*',
    '**/stories/**',
    '**/mockData/**',
    'src/main.tsx', // Entry point
  ],
  thresholds: {
    lines: 70,
    functions: 70,
    branches: 65,
    statements: 70,
    perFile: true,
  },
  // Auto-generate coverage after tests
  all: true,
  include: ['src/**/*.ts', 'src/**/*.tsx'],
},
```

### Coverage by Area

```typescript
// Target coverage by directory

const coverageTargets = {
  'src/components/': { lines: 75, branches: 70 }, // UI components
  'src/hooks/': { lines: 80, branches: 75 },      // Business logic
  'src/utils/': { lines: 90, branches: 85 },      // Pure functions
  'src/api/': { lines: 70, branches: 65 },        // API calls
  'src/features/*/': { lines: 75, branches: 70 }, // Feature modules
};
```

---

## Summary

Unit testing strategy for the travel agency platform:

- **Vitest** for fast unit tests with native ESM support
- **React Testing Library** for user-centric component testing
- **renderHook** for testing custom hooks
- **Helper functions** to reduce boilerplate
- **Mock strategically** — prefer MSW for API, real dependencies when possible
- **Test factories** for maintainable test data
- **70% coverage target** — diminishing returns beyond

---

**Next:** [Part 3: Integration Testing](./TESTING_STRATEGY_03_INTEGRATION.md) — API routes, database, MSW, and service integration
