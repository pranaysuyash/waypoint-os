# Testing Strategy Part 1: Testing Philosophy

> Principles, culture, and strategy for quality assurance

**Series:** Testing Strategy
**Next:** [Part 2: Unit Testing](./TESTING_STRATEGY_02_UNIT.md)

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [The Test Pyramid](#the-test-pyramid)
3. [What to Test](#what-to-test)
4. [What NOT to Test](#what-not-to-test)
5. [Testing Culture](#testing-culture)
6. [Quality Gates](#quality-gates)
7. [Metrics](#metrics)
8. [Anti-Patterns](#anti-patterns)

---

## Philosophy

### Core Principles

```typescript
// Testing principles manifest

interface TestingPhilosophy {
  // Tests are code, treat them with same care as production
  testsAreCode: boolean;

  // Tests should be readable and maintainable
  readabilityFirst: boolean;

  // Tests should fail for the right reasons
  meaningfulFailures: boolean;

  // Tests should be fast enough to run frequently
  feedbackSpeed: 'instant' | 'seconds' | 'minutes';

  // Tests should cover user behavior, not implementation
  userCentric: boolean;

  // Tests should be deterministic
  noFlakiness: boolean;
}
```

### Our Testing Mantra

> "We test **behavior**, not **implementation**. We test **risk**, not **coverage**."

**Behavior vs Implementation:**
- ✅ Test: "Clicking search shows results matching the query"
- ❌ Test: "Component renders SearchResults with props.query"

**Risk vs Coverage:**
- ✅ High-value: Booking flow, payment processing, auth
- ❌ Low-value: Static components, trivial getters

---

## The Test Pyramid

```
           ▲
          /E\          Few, slow, expensive
         /E2E\         Critical user journeys only
        /-----\
       /Integ\        More, medium speed
      /ration\        API routes, state, DB
     /-------\
    /  Unit  \       Most, fast, cheap
   /  Tests  \       Components, hooks, utilities
  /-----------\
```

### Ideal Ratios

| Layer | Target | Rationale |
|-------|--------|-----------|
| **E2E** | 5% | Slow, expensive, brittle. Critical paths only. |
| **Integration** | 25% | API routes, state management, DB operations |
| **Unit** | 70% | Fast, cheap, maintainable. Business logic. |

### Travel Agency Context

```typescript
// High-risk areas = More E2E coverage
const highRiskFlows = [
  'booking-creation',     // Revenue impact
  'payment-processing',   // Money transaction
  'authentication',       // Security
  'supplier-integration', // External dependency
];

// Low-risk areas = Unit tests only
const lowRiskAreas = [
  'formatting-currency', // Pure function
  'date-calculations',   // Well-tested library
  'ui-components',       // Visual tests handle this
];
```

---

## What to Test

### The Risk Matrix

```
           │ High Impact
           │
           │  ┌─────────────────┐
    High   │  │  E2E + Unit     │
   Risk    │  │  (Booking,      │
           │  │   Payment)      │
           │  └─────────────────┘
           │
           │  ┌─────────────────┐
    Low    │  │  Unit Only      │
   Risk    │  │  (Formatting,   │
           │  │   Utilities)    │
           │  └─────────────────┘
           │
           └───────────────────────►
              Low         High
           Frequency of Change
```

### Testing Guidelines by Layer

#### Components (Unit Tests)

**Test these:**
- User interactions (clicks, form submissions)
- Conditional rendering based on props/state
- Error handling and edge cases
- Integration with hooks and context

**Example:**
```typescript
// ✅ Good: Tests user behavior
describe('BookingForm', () => {
  it('submits booking when valid data provided', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<BookingForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/destination/i), 'Paris');
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        destination: 'Paris',
        email: 'test@example.com',
      })
    );
  });
});

// ❌ Bad: Tests implementation
describe('BookingForm', () => {
  it('calls handleSubmit when submit clicked', () => {
    const wrapper = shallow(<BookingForm />);
    const instance = wrapper.instance();
    vi.spyOn(instance, 'handleSubmit');
    // Don't test internal methods!
  });
});
```

#### Hooks (Unit Tests)

**Test these:**
- State changes on actions
- Effect triggers and cleanup
- Return value changes
- Error handling

**Example:**
```typescript
describe('useBooking', () => {
  it('creates booking and updates state', async () => {
    const { result } = renderHook(() => useBooking());

    await act(async () => {
      await result.current.createBooking({ destination: 'Paris' });
    });

    expect(result.current.booking).toEqual(
      expect.objectContaining({ destination: 'Paris' })
    );
    expect(result.current.status).toBe('created');
  });
});
```

#### API Routes (Integration Tests)

**Test these:**
- Request validation
- Authentication/authorization
- Response format
- Error handling
- Database operations

**Example:**
```typescript
describe('POST /api/bookings', () => {
  it('creates booking with valid data', async () => {
    const response = await app.request('/api/bookings', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      json: { destination: 'Paris', dates: ['2025-06-01'] },
    });

    expect(response.status).toBe(201);
    expect(await response.json()).toEqual(
      expect.objectContaining({
        id: expect.any(String),
        destination: 'Paris',
      })
    );
  });

  it('returns 401 without auth', async () => {
    const response = await app.request('/api/bookings', {
      method: 'POST',
      json: { destination: 'Paris' },
    });

    expect(response.status).toBe(401);
  });
});
```

---

## What NOT to Test

### Don't Test Third-Party Code

```typescript
// ❌ Don't test
describe('moment', () => {
  it('formats dates correctly', () => {
    expect(moment('2025-01-01').format('YYYY')).toBe('2025');
  });
});

// ✅ Do test your wrapper
describe('formatTravelDate', () => {
  it('formats date for travel display', () => {
    expect(formatTravelDate('2025-01-01')).toBe('Jan 1, 2025');
  });
});
```

### Don't Test Implementation Details

```typescript
// ❌ Don't test
it('uses useState hook', () => {
  // How it's implemented doesn't matter
});

it('renders a div with class booking', () => {
  // Class names are implementation
});

// ✅ Do test
it('displays booking confirmation after submission', () => {
  // What the user experiences matters
});
```

### Don't Test Trivial Code

```typescript
// ❌ Don't test
export const add = (a: number, b: number) => a + b;

// The type system and JS engine test this enough

// ✅ Do test business logic
export const calculateBookingTotal = (
  basePrice: number,
  guests: number,
  discount?: Discount
): number => {
  const subtotal = basePrice * guests;
  const discountAmount = discount
    ? calculateDiscount(subtotal, discount)
    : 0;
  return subtotal - discountAmount;
};
```

### Don't Test Static Content

```typescript
// ❌ Don't test
it('renders "Welcome" text', () => {
  // This is fragile and low value
});

// ✅ Use visual tests for static content
// ✅ Use i18n tests for translations
```

---

## Testing Culture

### Shared Ownership

```typescript
// No "Test Team" — Everyone tests

interface TeamResponsibilities {
  developer: {
    writes: ['unit', 'integration', 'e2e'];
    reviews: 'all tests in PR';
    fixes: 'failing tests before merge';
  };
  designer: {
    reviews: 'visual regression tests';
    defines: 'interaction behavior';
  };
  pm: {
    defines: 'critical user journeys';
    reviews: 'e2e test coverage';
  };
  qa: {
    defines: 'testing strategy';
    builds: 'test infrastructure';
    analyzes: 'quality metrics';
  };
}
```

### Test-First vs Test-After

| Approach | When to Use | Pros | Cons |
|----------|-------------|------|------|
| **TDD** | Complex logic, new features | Better design, fewer bugs | Slower initially |
| **Test-After** | UI components, prototypes | Faster to start | Missed edge cases |
| **Test-Along** | Most development work | Balanced | None |

**Our approach: Test-Along**
- Write the component interface first
- Write tests for key behaviors
- Implement and iterate
- Add edge case tests as you find them

### Test Maintenance

```typescript
// Treat tests as first-class code

// ✅ Good: Helper functions for common setup
function setupBookingForm(overrides = {}) {
  const defaultProps = {
    onSubmit: vi.fn(),
    destinations: ['Paris', 'London'],
  };

  return {
    user: userEvent.setup(),
    ...render(<BookingForm {...defaultProps} {...overrides} />),
  };
}

// ✅ Good: Reusable test data
export const testBookings = {
  paris: {
    destination: 'Paris',
    dates: ['2025-06-01', '2025-06-07'],
    guests: 2,
  },
  london: {
    destination: 'London',
    dates: ['2025-07-01', '2025-07-05'],
    guests: 4,
  },
};

// ❌ Bad: Duplicated setup
describe('BookingForm', () => {
  it('does X', () => {
    const onSubmit = vi.fn();
    const destinations = ['Paris', 'London'];
    render(<BookingForm onSubmit={onSubmit} destinations={destinations} />);
    // ...
  });

  it('does Y', () => {
    const onSubmit = vi.fn();
    const destinations = ['Paris', 'London'];
    render(<BookingForm onSubmit={onSubmit} destinations={destinations} />);
    // ...
  });
});
```

---

## Quality Gates

### CI Pipeline Stages

```yaml
# Example CI flow

stages:
  - name: lint
    run: eslint && tsc
    timeout: 1m

  - name: unit-tests
    run: vitest run
    timeout: 3m
    coverage: 70%

  - name: integration-tests
    run: vitest run --config vitest.integration.config.ts
    timeout: 5m

  - name: visual-tests
    run: chromatic test
    timeout: 2m

  - name: e2e-tests
    run: playwright test
    timeout: 10m

  - name: performance
    run: lighthouse-ci && bundle-size check
    timeout: 3m
```

### Merge Criteria

| Type | Requirement | Fails If |
|------|-------------|----------|
| **Lint** | No errors | Any error |
| **Type** | No errors | Any error |
| **Unit** | 70% coverage | Below threshold |
| **E2E** | All critical pass | Any critical fails |
| **Visual** | No changes | Unexpected diffs |
| **Perf** | Within budget | Budget exceeded |

### PR Requirements

```typescript
// Pull request checklist

interface PRChecklist {
  tests: {
    new_code: 'has unit tests';
    bug_fix: 'has regression test';
    feature: 'has e2e test';
  };
  reviews: {
    code: '1 approval required';
    tests: 'tests reviewed separately';
  };
  quality: {
    coverage: 'not decreased';
    flaky: 'no flaky tests';
    slow: 'no slow tests added';
  };
}
```

---

## Metrics

### Key Quality Indicators

```typescript
interface QualityMetrics {
  // Coverage (with grain of salt)
  coverage: {
    unit: 0.70;        // Target: 70%
    integration: 0.40; // Target: 40% of key paths
  };

  // Test health
  health: {
    flakyRate: 0.01;   // Target: < 1%
    failureRate: 0.02; // Target: < 2%
    avgDuration: 300;  // Target: < 5 min full suite
  };

  // Defect escape rate
  defects: {
    caughtInUnit: 0.60;      // Target: 60%
    caughtInIntegration: 0.25; // Target: 25%
    caughtInE2E: 0.10;       // Target: 10%
    escaped: 0.05;           // Target: < 5%
  };

  // Time to feedback
  feedback: {
    prTests: 300;      // Target: < 5 min
    fullSuite: 1800;   // Target: < 30 min
  };
}
```

### Coverage Goals

| Area | Target | Notes |
|------|--------|-------|
| **Business Logic** | 90% | High value, complex code |
| **Components** | 70% | User interactions only |
| **Utilities** | 80% | Pure functions are easy to test |
| **API Routes** | 80% | Critical for data integrity |
| **Overall** | 70% | Diminishing returns beyond |

### Flaky Test Management

```typescript
// Flaky test detection and handling

interface FlakyTestPolicy {
  detection: {
    rerun: 3;           // Retry 3 times before failing
    quarantine: 5;      // Quarantine after 5 flakes
  };

  quarantine: {
    label: 'flaky';     // Add GitHub label
    comment: '@author test is flaky';
    exclude: true;      // Don't block merge
  };

  resolution: {
    priority: 'high';   // Fix within 1 week
    assignment: 'author'; // Assign to author
  };
}
```

---

## Anti-Patterns

### The "Test induced damage"

```typescript
// ❌ Breaking encapsulation for testing

class BookingService {
  // Private implementation detail
  private calculateTax(amount: number): number {
    return amount * 0.1;
  }
}

// Don't expose private just to test it!
// Instead, test the public API that uses it.

describe('BookingService', () => {
  it('includes tax in total', () => {
    const service = new BookingService();
    const total = service.calculateTotal({ amount: 100 });

    expect(total).toBe(110); // Tests tax indirectly
  });
});
```

### The "Mock everything"

```typescript
// ❌ Over-mocking leads to false confidence

describe('BookingForm', () => {
  it('submits form', () => {
    const mockApi = {
      booking: {
        create: vi.fn().mockResolvedValue({ id: '123' }),
        validate: vi.fn().mockReturnValue(true),
        calculate: vi.fn().mockReturnValue(100),
        // ... mocking everything
      },
    };

    // Tests pass but integration might be broken!
  });
});

// ✅ Use MSW for realistic API mocking
// ✅ Let some tests hit real dependencies (integration tests)
```

### The "Fragile test"

```typescript
// ❌ Brittle selector
it('shows confirmation', () => {
  expect(container.querySelector('.booking-form > div > p.confirm')).toBeInTheDocument();
});

// ✅ User-centric selector
it('shows confirmation', () => {
  expect(screen.getByText(/booking confirmed/i)).toBeInTheDocument();
});
```

### The "Slow test suite"

```typescript
// ❌ Running full E2E for every change

// ✅ Smart test selection
// - Unit tests on every file change
// - Integration tests on related file changes
// - E2E only on PR or before merge

// vitest.config.ts
export default defineConfig({
  test: {
    watch: true,
    related: true, // Only run related tests
  },
});
```

---

## Summary

Testing philosophy for the travel agency platform:

- **Test behavior, not implementation** — User experience matters most
- **Test based on risk** — High-value features get more coverage
- **Fast feedback loop** — Most tests should complete in seconds
- **Shared ownership** — Developers write tests, QA builds infrastructure
- **Quality gates** — Automated checks prevent regressions
- **Measure what matters** — Coverage is a tool, not a goal

---

**Next:** [Part 2: Unit Testing](./TESTING_STRATEGY_02_UNIT.md) — Component testing, hooks, utilities, and Vitest configuration
