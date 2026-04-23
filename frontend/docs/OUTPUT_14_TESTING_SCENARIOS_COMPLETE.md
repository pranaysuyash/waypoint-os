# Output Panel 14: Complete Testing Scenarios

> Comprehensive test scenarios, edge cases, and compliance testing for the Output Panel system

---

## Part 1: Testing Strategy

### 1.1 Testing Pyramid

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TESTING PYRAMID                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        ▲                                                    │
│                      ╱ ╲                                                   │
│                    ╱   E2E ╲   ← 10% (Critical paths, user journeys)        │
│                  ╱─────────╲                                               │
│                ╱           ╲                                              │
│              ╱    INTEGRATION ╲ ← 30% (API, services, templates)           │
│            ╱───────────────────╲                                           │
│          ╱                     ╲                                         │
│        ╱       UNIT TESTS        ╲ ← 60% (helpers, components, utils)     │
│      ╱─────────────────────────────╲                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  COVERAGE TARGETS                                                  │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Unit Tests:         90%+ statements, 85%+ branches, 95%+ functions│   │
│  │  Integration Tests: 80%+ API endpoints, all template types         │   │
│  │  E2E Tests:          All critical user journeys                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Test Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TEST CATEGORIES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FUNCTIONAL TESTS                                                   │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Bundle generation (all types)                                    │   │
│  │  • Template rendering                                               │   │
│  │  • Helper functions                                                 │   │
│  │  • Delivery channels                                                │   │
│  │  • PDF generation                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  INTEGRATION TESTS                                                 │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • API endpoints                                                    │   │
│  │  • Database operations                                             │   │
│  │  • External services (WhatsApp, Email, S3)                          │   │
│  │  • Puppeteer PDF generation                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  VISUAL REGRESSION TESTS                                           │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • PDF output matching                                             │   │
│  │  • Email rendering across clients                                   │   │
│  │  • WhatsApp message formatting                                     │   │
│  │  • Portal display                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PERFORMANCE TESTS                                                 │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Generation time (SLA: <5 seconds)                                │   │
│  │  • Concurrent generation (100+ simultaneous)                         │   │
│  │  • PDF file size optimization                                       │   │
│  │  • API response times                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  COMPLIANCE TESTS                                                  │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • GST invoice format                                              │   │
│  │  • SAC codes                                                       │   │
│  │  • Terms and conditions                                             │   │
│  │  • Data privacy (GDPR, local laws)                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EDGE CASE TESTS                                                   │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Empty/missing data                                               │   │
│  │  • Special characters                                               │   │
│  │  • Large datasets                                                   │   │
│  │  • Timezone handling                                                │   │
│  │  • Currency conversions                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SECURITY TESTS                                                    │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Authentication/authorization                                     │   │
│  │  • Rate limiting                                                    │   │
│  │  • Input validation/sanitization                                    │   │
│  │  • SQL injection prevention                                         │   │
│  │  • XSS prevention                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Unit Test Scenarios

### 2.1 Template Helper Tests

#### Date/Time Helpers

```typescript
// helpers/date.test.ts

describe('formatDate', () => {
  it('formats date with default format', () => {
    const result = formatDate(new Date('2025-01-20'));
    expect(result).toBe('20 Jan 2025');
  });

  it('formats date with custom format', () => {
    const result = formatDate(new Date('2025-01-20'), { format: 'DD/MM/YYYY' });
    expect(result).toBe('20/01/2025');
  });

  it('handles timezone conversion', () => {
    const result = formatDate(new Date('2025-01-20T10:00:00Z'), {
      format: 'HH:mm',
      timezone: 'Asia/Kolkata'
    });
    expect(result).toContain('15:30'); // IST is GMT+5:30
  });

  it('handles invalid dates gracefully', () => {
    const result = formatDate('invalid-date');
    expect(result).toBe('Invalid Date');
  });

  it('handles null/undefined', () => {
    expect(formatDate(null)).toBe('N/A');
    expect(formatDate(undefined)).toBe('N/A');
  });
});

describe('dateRange', () => {
  it('formats same month range', () => {
    const result = dateRange('2025-01-20', '2025-01-25');
    expect(result).toBe('20 - 25 Jan 2025');
  });

  it('formats different month range', () => {
    const result = dateRange('2025-01-20', '2025-02-05');
    expect(result).toBe('20 Jan - 05 Feb 2025');
  });

  it('formats different year range', () => {
    const result = dateRange('2024-12-25', '2025-01-05');
    expect(result).toBe('25 Dec 2024 - 05 Jan 2025');
  });

  it('handles inverted dates', () => {
    const result = dateRange('2025-01-25', '2025-01-20');
    expect(result).toBe('20 - 25 Jan 2025'); // Auto-corrects
  });
});

describe('nightsBetween', () => {
  it('calculates nights correctly', () => {
    expect(nightsBetween('2025-01-20', '2025-01-25')).toBe(5);
    expect(nightsBetween('2025-01-20', '2025-01-21')).toBe(1);
    expect(nightsBetween('2025-01-20', '2025-01-20')).toBe(0);
  });

  it('handles same-day checkout', () => {
    expect(nightsBetween('2025-01-20T14:00:00', '2025-01-20T11:00:00')).toBe(0);
  });
});

describe('flightDuration', () => {
  it('calculates duration correctly', () => {
    expect(flightDuration('06:00', '09:30')).toBe('3h 30m');
    expect(flightDuration('23:45', '02:15')).toBe('2h 30m'); // Crosses midnight
  });

  it('handles 24+ hour flights', () => {
    expect(flightDuration('06:00', '08:00', 2)).toBe('48h 0m'); // With days parameter
  });
});
```

#### Currency/Number Helpers

```typescript
// helpers/currency.test.ts

describe('formatCurrency', () => {
  it('formats INR with Indian numbering', () => {
    expect(formatCurrency(154690, 'INR')).toBe('₹1,54,690');
    expect(formatCurrency(10000000, 'INR')).toBe('₹1,00,00,000');
  });

  it('formats USD with Western numbering', () => {
    expect(formatCurrency(1546.90, 'USD')).toBe('$1,546.90');
    expect(formatCurrency(1000000, 'USD')).toBe('$1,000,000.00');
  });

  it('formats EUR with European numbering', () => {
    expect(formatCurrency(1234.56, 'EUR', 'de-DE')).toBe('1.234,56 €');
  });

  it('handles zero', () => {
    expect(formatCurrency(0, 'INR')).toBe('₹0');
  });

  it('handles negative amounts', () => {
    expect(formatCurrency(-5000, 'INR')).toBe('-₹5,000');
  });

  it('rounds to 2 decimal places', () => {
    expect(formatCurrency(1234.567, 'USD')).toBe('$1,234.57');
    expect(formatCurrency(1234.564, 'USD')).toBe('$1,234.56');
  });
});

describe('gst', () => {
  it('calculates GST correctly', () => {
    expect(gst(100000, 18)).toBe(18000);
    expect(gst(154690, 18)).toBe(27844.20);
  });

  it('handles different rates', () => {
    expect(gst(100000, 5)).toBe(5000);
    expect(gst(100000, 12)).toBe(12000);
    expect(gst(100000, 28)).toBe(28000);
  });
});

describe('perPerson', () => {
  it('divides correctly', () => {
    expect(perPerson(154690, 3)).toBe(51563.33);
    expect(perPerson(100000, 4)).toBe(25000);
  });

  it('handles uneven division', () => {
    expect(perPerson(100, 3)).toBe(33.34);
  });
});
```

#### Conditional Helpers

```typescript
// helpers/conditional.test.ts

describe('eq helper', () => {
  it('compares strings correctly', () => {
    expect(eq('international', 'international')).toBe(true);
    expect(eq('international', 'domestic')).toBe(false);
  });

  it('compares numbers correctly', () => {
    expect(eq(5, 5)).toBe(true);
    expect(eq(5, 10)).toBe(false);
  });

  it('compares with different types', () => {
    expect(eq(5, '5')).toBe(false); // Strict comparison
  });
});

describe('contains helper', () => {
  it('finds string in array', () => {
    expect(contains(['international', 'honeymoon'], 'honeymoon')).toBe(true);
    expect(contains(['international', 'honeymoon'], 'adventure')).toBe(false);
  });

  it('handles empty arrays', () => {
    expect(contains([], 'anything')).toBe(false);
  });
});

describe('passportExpiryStatus', () => {
  const today = new Date('2025-01-01');

  it('returns Valid for >6 months validity', () => {
    const expiry = new Date('2025-08-01');
    expect(passportExpiryStatus(expiry, today)).toBe('Valid');
  });

  it('returns Expiring Soon for 3-6 months', () => {
    const expiry = new Date('2025-04-01');
    expect(passportExpiryStatus(expiry, today)).toBe('Expiring Soon');
  });

  it('returns Critical for <3 months', () => {
    const expiry = new Date('2025-02-01');
    expect(passportExpiryStatus(expiry, today)).toBe('Critical');
  });

  it('returns Expired for past dates', () => {
    const expiry = new Date('2024-11-01');
    expect(passportExpiryStatus(expiry, today)).toBe('Expired');
  });
});
```

### 2.2 Component Tests

```typescript
// components/flight-card.test.tsx

describe('FlightCard Component', () => {
  const mockFlight = {
    airline: 'IndiGo',
    flightNumber: '6E 1475',
    from: { code: 'DEL', city: 'Delhi', terminal: '3', time: '06:00' },
    to: { code: 'DXB', city: 'Dubai', terminal: '1', time: '09:30' },
    class: 'Economy',
    pnr: 'ABC123',
    status: 'confirmed'
  };

  it('renders flight information correctly', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText('IndiGo')).toBeInTheDocument();
    expect(screen.getByText('6E 1475')).toBeInTheDocument();
    expect(screen.getByText('DEL')).toBeInTheDocument();
    expect(screen.getByText('DXB')).toBeInTheDocument();
  });

  it('shows terminal when available', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText(/Terminal 3/)).toBeInTheDocument();
  });

  it('shows confirmed status badge', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText(/confirmed/i)).toBeInTheDocument();
  });

  it('handles missing terminal gracefully', () => {
    const flightWithoutTerminal = { ...mockFlight, from: { ...mockFlight.from, terminal: undefined } };
    render(<FlightCard flight={flightWithoutTerminal} />);
    expect(screen.queryByText(/Terminal/)).not.toBeInTheDocument();
  });
});

// components/price-table.test.tsx

describe('PriceTable Component', () => {
  const mockItems = [
    { description: 'Flights', amount: 37000 },
    { description: 'Hotels', amount: 85000 },
    { description: 'Transfers', amount: 6000 },
  ];

  it('renders all items', () => {
    render(<PriceTable items={mockItems} subtotal={128000} taxes={13190} total={141190} />);
    expect(screen.getByText('Flights')).toBeInTheDocument();
    expect(screen.getByText('Hotels')).toBeInTheDocument();
    expect(screen.getByText('Transfers')).toBeInTheDocument();
  });

  it('formats currency correctly', () => {
    render(<PriceTable items={mockItems} subtotal={128000} taxes={13190} total={141190} />);
    expect(screen.getByText('₹37,000')).toBeInTheDocument();
    expect(screen.getByText('₹1,41,190')).toBeInTheDocument();
  });

  it('shows tax breakdown when provided', () => {
    const taxes = [{ name: 'CGST', rate: 9, amount: 6595 }];
    render(<PriceTable items={mockItems} subtotal={128000} taxes={13190} total={141190} taxDetails={taxes} />);
    expect(screen.getByText('CGST (9%)')).toBeInTheDocument();
    expect(screen.getByText('₹6,595')).toBeInTheDocument();
  });

  it('handles empty items array', () => {
    render(<PriceTable items={[]} subtotal={0} taxes={0} total={0} />);
    expect(screen.getByText(/no items/i)).toBeInTheDocument();
  });
});
```

---

## Part 3: Integration Test Scenarios

### 3.1 API Integration Tests

```typescript
// api/bundles.generate.test.ts

describe('POST /api/bundles/generate', () => {
  let authToken: string;

  beforeAll(async () => {
    authToken = await authenticateTestUser();
  });

  it('generates a quote bundle successfully', async () => {
    const response = await request(app)
      .post('/api/bundles/generate')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleType: 'QUOTE',
        tripId: 'test-trip-001',
        delivery: { channels: ['PORTAL'] },
        format: { output: 'PDF' }
      });

    expect(response.status).toBe(200);
    expect(response.body.success).toBe(true);
    expect(response.body.data).toHaveProperty('bundleId');
    expect(response.body.data).toHaveProperty('bundleNumber');
    expect(response.body.data.bundleType).toBe('QUOTE');
    expect(response.body.data.status).toBe('COMPLETED');
    expect(response.body.data.downloadUrls).toHaveProperty('pdf');
  });

  it('generates an itinerary bundle', async () => {
    const response = await request(app)
      .post('/api/bundles/generate')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleType: 'ITINERARY',
        tripId: 'test-trip-002',
        template: { variant: 'honeymoon' },
        delivery: { channels: ['PORTAL'] },
        format: { output: 'BOTH' }
      });

    expect(response.status).toBe(200);
    expect(response.body.data.downloadUrls).toHaveProperty('pdf');
    expect(response.body.data.downloadUrls).toHaveProperty('html');
  });

  it('requires authentication', async () => {
    const response = await request(app)
      .post('/api/bundles/generate')
      .send({
        bundleType: 'QUOTE',
        tripId: 'test-trip-001'
      });

    expect(response.status).toBe(401);
    expect(response.body.success).toBe(false);
  });

  it('validates bundle type', async () => {
    const response = await request(app)
      .post('/api/bundles/generate')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleType: 'INVALID_TYPE',
        tripId: 'test-trip-001'
      });

    expect(response.status).toBe(400);
    expect(response.body.error.code).toBe('BUNDLE_TYPE_INVALID');
  });

  it('returns 404 for non-existent trip', async () => {
    const response = await request(app)
      .post('/api/bundles/generate')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleType: 'QUOTE',
        tripId: 'non-existent-trip'
      });

    expect(response.status).toBe(404);
    expect(response.body.error.code).toBe('BUNDLE_TRIP_NOT_FOUND');
  });

  it('returns 422 for incomplete trip data', async () => {
    const response = await request(app)
      .post('/api/bundles/generate')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleType: 'QUOTE',
        tripId: 'test-trip-incomplete'
      });

    expect(response.status).toBe(422);
    expect(response.body.error.code).toBe('BUNDLE_DATA_INCOMPLETE');
  });
});
```

### 3.2 Delivery Integration Tests

```typescript
// api/delivery.whatsapp.test.ts

describe('POST /api/delivery/whatsapp', () => {
  it('sends bundle via WhatsApp successfully', async () => {
    const bundle = await createTestBundle();

    const response = await request(app)
      .post('/api/delivery/whatsapp')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleId: bundle.id,
        recipientPhone: '+919876543210',
        message: 'Your itinerary is ready!'
      });

    expect(response.status).toBe(200);
    expect(response.body.data).toHaveProperty('messageId');
    expect(response.body.data.status).toBe('QUEUED');
  });

  it('validates phone number format', async () => {
    const bundle = await createTestBundle();

    const response = await request(app)
      .post('/api/delivery/whatsapp')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleId: bundle.id,
        recipientPhone: 'invalid-phone'
      });

    expect(response.status).toBe(400);
    expect(response.body.error.code).toBe('DELIVERY_RECIPIENT_INVALID');
  });
});

// api/delivery.email.test.ts

describe('POST /api/delivery/email', () => {
  it('sends bundle via email successfully', async () => {
    const bundle = await createTestBundle();

    const response = await request(app)
      .post('/api/delivery/email')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleId: bundle.id,
        recipientEmail: 'customer@example.com',
        subject: 'Your Travel Itinerary',
        attachments: { includePdf: true }
      });

    expect(response.status).toBe(200);
    expect(response.body.data).toHaveProperty('messageId');
  });

  it('validates email format', async () => {
    const bundle = await createTestBundle();

    const response = await request(app)
      .post('/api/delivery/email')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        bundleId: bundle.id,
        recipientEmail: 'invalid-email'
      });

    expect(response.status).toBe(400);
  });
});
```

### 3.3 Template Integration Tests

```typescript
// lib/template-engine.test.ts

describe('Template Engine', () => {
  it('renders quote template with data', async () => {
    const data = await getMockQuoteData();
    const html = await compileTemplate('quote', data);

    expect(html).toContain(data.customer.name);
    expect(html).toContain(data.trip.destination);
    expect(html).toContain(formatCurrency(data.pricing.total, 'INR'));
    expect(html).toContain(data.quoteNumber);
  });

  it('renders itinerary with day timeline', async () => {
    const data = await getMockItineraryData();
    const html = await compileTemplate('itinerary', data);

    expect(html).toContain('Day 1');
    expect(html).toContain('Day 2');
    expect(html).toContain(data.days[0].timeline[0].activity);
  });

  it('renders invoice with tax breakdown', async () => {
    const data = await getMockInvoiceData();
    const html = await compileTemplate('invoice', data);

    expect(html).toContain(data.invoiceNumber);
    expect(html).toContain('CGST');
    expect(html).toContain('SGST');
    expect(html).toContain(formatCurrency(data.taxSummary.totalTax, 'INR'));
  });

  it('uses agency template when available', async () => {
    const data = await getMockQuoteData();
    data.agency.id = 'test-agency';
    await createAgencyTemplate('test-agency', 'quote', customTemplateSource);

    const html = await compileTemplate('quote', data);
    expect(html).toContain('Custom Agency Header');
  });

  it('falls back to system template', async () => {
    const data = await getMockQuoteData();
    data.agency.id = 'non-existent-agency';

    const html = await compileTemplate('quote', data);
    expect(html).toContain('System Default Header');
  });
});
```

---

## Part 4: E2E Test Scenarios

### 4.1 Critical User Journeys

```typescript
// e2e/bundle-generation.spec.ts

describe('Bundle Generation E2E', () => {
  it('complete quote-to-booking journey', async ({ page }) => {
    // Login as agent
    await page.goto('/login');
    await page.fill('[name="email"]', 'agent@test.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Navigate to trip
    await page.goto('/trips/test-trip-001');

    // Generate quote
    await page.click('[data-testid="generate-quote-button"]');
    await page.waitForSelector('[data-testid="quote-preview"]');

    // Verify quote content
    const customerName = await page.textContent('[data-testid="customer-name"]');
    expect(customerName).toBe('Test Customer');

    const totalAmount = await page.textContent('[data-testid="total-amount"]');
    expect(totalAmount).toContain('₹');

    // Send to customer
    await page.click('[data-testid="send-whatsapp-button"]');
    await page.fill('[name="recipientPhone"]', '+919876543210');
    await page.click('button:has-text("Send")');

    // Verify success message
    await page.waitForSelector('[data-testid="delivery-success"]');
    const successMessage = await page.textContent('[data-testid="delivery-success"]');
    expect(successMessage).toContain('sent successfully');
  });

  it('generate itinerary after booking confirmation', async ({ page }) => {
    await page.goto('/trips/test-trip-002');
    await page.click('[data-testid="generate-itinerary-button"]');

    // Select variant
    await page.click('[data-testid="variant-honeymoon"]');

    // Preview
    await page.click('button:has-text("Preview")');
    await page.waitForSelector('[data-testid="itinerary-preview"]');

    // Verify day cards
    const dayCards = await page.locator('[data-testid^="day-card-"]').count();
    expect(dayCards).toBeGreaterThan(0);

    // Download PDF
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="download-pdf-button"]');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/ITIN-\d+\.pdf/);
  });
});
```

### 4.2 Error Handling E2E

```typescript
// e2e/error-handling.spec.ts

describe('Error Handling E2E', () => {
  it('handles trip data missing gracefully', async ({ page }) => {
    await page.goto('/trips/test-trip-incomplete');

    const errorBanner = await page.textContent('[data-testid="error-banner"]');
    expect(errorBanner).toContain('complete your trip details');

    // Show missing fields
    const missingFields = await page.textContent('[data-testid="missing-fields"]');
    expect(missingFields).toContain('Flight details');
    expect(missingFields).toContain('Hotel booking');
  });

  it('shows delivery failure notification', async ({ page }) => {
    // Mock WhatsApp API failure
    await page.route('**/api/delivery/whatsapp', route => route.fulfill({
      status: 500,
      body: JSON.stringify({ success: false })
    }));

    await page.goto('/trips/test-trip-001');
    await page.click('[data-testid="send-whatsapp-button"]');
    await page.click('button:has-text("Send")');

    // Verify error notification
    await page.waitForSelector('[data-testid="notification-error"]');
    const errorMessage = await page.textContent('[data-testid="notification-error"]');
    expect(errorMessage).toContain('failed to send');
  });
});
```

---

## Part 5: Edge Cases & Boundary Tests

### 5.1 Data Edge Cases

```typescript
// edge-cases/data-edge-cases.test.ts

describe('Data Edge Cases', () => {
  describe('Empty Data Handling', () => {
    it('handles empty activities array', async () => {
      const data = { ...getMockQuoteData(), items: { activities: [] } };
      const html = await compileTemplate('quote', data);

      expect(html).toContain('No activities included');
    });

    it('handles null customer email', async () => {
      const data = { ...getMockQuoteData(), customer: { ...getMockQuoteData().customer, email: null } };
      const html = await compileTemplate('quote', data);

      expect(html).toContain('Email: N/A');
    });

    it('handles missing passport details', async () => {
      const data = await getMockItineraryData();
      data.travelers[0].passport = undefined;

      const html = await compileTemplate('itinerary', data);
      expect(html).toContain('Passport: Not provided');
    });
  });

  describe('Special Characters', () => {
    it('handles names with apostrophes', async () => {
      const data = { ...getMockQuoteData(), customer: { name: "O'Brien" } };
      const html = await compileTemplate('quote', data);

      expect(html).toContain("O'Brien");
    });

    it('handles names with accents', async () => {
      const data = { ...getMockQuoteData(), customer: { name: 'José García' } };
      const html = await compileTemplate('quote', data);

      expect(html).toContain('José García');
    });

    it('handles emojis in descriptions', async () => {
      const data = { ...getMockQuoteData(), trip: { description: 'Beach vacation 🏖️ with family 👨‍👩‍👧‍👦' } };
      const html = await compileTemplate('quote', data);

      expect(html).toContain('🏖️');
      expect(html).toContain('👨‍👩‍👧‍👦');
    });
  });

  describe('Large Datasets', () => {
    it('handles 20+ day itinerary', async () => {
      const data = await getMockItineraryData();
      data.days = Array.from({ length: 25 }, (_, i) => ({
        dayNumber: i + 1,
        date: new Date(2025, 0, i + 1),
        timeline: [{ time: '09:00', activity: 'Sightseeing', type: 'ACTIVITY' }]
      }));

      const html = await compileTemplate('itinerary', data);
      expect(html).toContain('Day 25');
    });

    it('handles 100+ line items', async () => {
      const data = await getMockInvoiceData();
      data.items = Array.from({ length: 150 }, (_, i) => ({
        srNo: i + 1,
        description: `Service Item ${i + 1}`,
        quantity: 1,
        unit: 'each',
        unitPrice: 100,
        total: 100
      }));

      const html = await compileTemplate('invoice', data);
      expect(html).toContain('150');
    });
  });

  describe('Numeric Edge Cases', () => {
    it('handles zero amounts', async () => {
      const data = { ...getMockQuoteData(), pricing: { total: 0, taxes: 0, fees: 0 } };
      const html = await compileTemplate('quote', data);

      expect(html).toContain('₹0');
    });

    it('handles very large amounts', async () => {
      const data = { ...getMockQuoteData(), pricing: { total: 100000000 } };
      const html = await compileTemplate('quote', data);

      expect(html).toContain('₹10,00,00,000');
    });

    it('handles fractional amounts', async () => {
      const data = { ...getMockQuoteData(), pricing: { total: 154690.67 } };
      const html = await compileTemplate('quote', data);

      expect(html).toContain('₹1,54,690.67');
    });
  });
});
```

### 5.2 Timezone Edge Cases

```typescript
// edge-cases/timezone-edge-cases.test.ts

describe('Timezone Edge Cases', () => {
  it('handles flights crossing midnight', async () => {
    const data = await getMockItineraryData();
    data.days[0].timeline.push({
      time: '23:45',
      activity: 'Late night departure',
      type: 'FLIGHT',
      details: { departure: '23:45', arrival: '03:15', arrivalDay: '+1' }
    });

    const html = await compileTemplate('itinerary', data);
    expect(html).toContain('+1 day');
  });

  it('handles multi-timezone trips', async () => {
    const data = await getMockItineraryData();
    data.days[0].timezone = 'Asia/Kolkata';
    data.days[1].timezone = 'Asia/Dubai';
    data.days[2].timezone = 'Europe/London';

    const html = await compileTemplate('itinerary', data);
    expect(html).toContain('GMT+5:30');
    expect(html).toContain('GMT+4');
    expect(html).toContain('GMT+0');
  });

  it('handles DST transitions', async () => {
    const data = await getMockItineraryData();
    data.travelDates = {
      from: new Date('2025-03-08'), // Before DST
      to: new Date('2025-03-10')     // After DST
    };

    const html = await compileTemplate('itinerary', data);
    // Should account for DST change
  });
});
```

### 5.3 Currency Edge Cases

```typescript
// edge-cases/currency-edge-cases.test.ts

describe('Currency Edge Cases', () => {
  it('handles multi-currency trips', async () => {
    const data = await getMockItineraryData();
    data.pricing = {
      baseCurrency: 'INR',
      items: [
        { currency: 'INR', amount: 100000 },
        { currency: 'USD', amount: 1200 },
        { currency: 'EUR', amount: 500 }
      ],
      totalInBase: 952000 // Converted to INR
    };

    const html = await compileTemplate('quote', data);
    expect(html).toContain('₹');
    expect(html).toContain('$');
    expect(html).toContain('€');
  });

  it('handles currency conversion edge cases', async () => {
    // Test with volatile rates
    const converted = convertCurrency(100, 'USD', 'JPY', 149.52);
    expect(converted).toBeCloseTo(14952, 0);
  });

  it('handles zero exchange rate gracefully', async () => {
    const result = convertCurrency(100, 'USD', 'INR', 0);
    expect(result).toBe(0); // Or handle as error
  });
});
```

---

## Part 6: Performance Tests

### 6.1 Generation Performance

```typescript
// performance/generation-performance.test.ts

describe('Bundle Generation Performance', () => {
  it('generates simple quote in under 2 seconds', async () => {
    const startTime = Date.now();
    await generateBundle('QUOTE', 'simple-trip');
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(2000);
  });

  it('generates complex itinerary in under 5 seconds', async () => {
    const data = await getComplexItineraryData(); // 15 days, multiple activities
    const startTime = Date.now();
    await generateBundle('ITINERARY', data);
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(5000);
  });

  it('PDF generation completes in under 3 seconds', async () => {
    const html = await compileTemplate('quote', await getMockQuoteData());
    const startTime = Date.now();
    await generatePDF(html);
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(3000);
  });

  it('handles 100 concurrent generations', async () => {
    const promises = Array.from({ length: 100 }, () =>
      generateBundle('QUOTE', `trip-${Math.random()}`)
    );

    const startTime = Date.now();
    await Promise.all(promises);
    const duration = Date.now() - startTime;

    // Should complete within reasonable time (not 100x sequential)
    expect(duration).toBeLessThan(30000);
  });
});
```

### 6.2 File Size Optimization

```typescript
// performance/file-size.test.ts

describe('PDF File Size', () => {
  it('keeps quote PDF under 500KB', async () => {
    const pdf = await generatePDF('QUOTE', await getMockQuoteData());
    const sizeKB = pdf.length / 1024;

    expect(sizeKB).toBeLessThan(500);
  });

  it('keeps itinerary PDF under 2MB', async () => {
    const pdf = await generatePDF('ITINERARY', await getComplexItineraryData());
    const sizeMB = pdf.length / (1024 * 1024);

    expect(sizeMB).toBeLessThan(2);
  });

  it('optimizes images in PDF', async () => {
    const data = await getMockQuoteData();
    data.agency.logo = 'large-logo.png'; // 5MB image

    const pdf = await generatePDF('QUOTE', data);
    const sizeKB = pdf.length / 1024;

    // PDF should be compressed, not include full 5MB
    expect(sizeKB).toBeLessThan(1000);
  });
});
```

---

## Part 7: Compliance Tests

### 7.1 GST Invoice Compliance

```typescript
// compliance/gst-invoice.test.ts

describe('GST Invoice Compliance', () => {
  it('includes all mandatory fields', async () => {
    const invoice = await generateInvoice(await getMockInvoiceData());
    const text = extractText(invoice);

    // Mandatory fields per GST rules
    expect(text).toContain('Invoice No');
    expect(text).toContain('Invoice Date');
    expect(text).toContain('GSTIN');
    expect(text).toContain('Customer Name');
    expect(text).toContain('Total Invoice Value');
    expect(text).toContain('Authorized Signatory');
  });

  it('shows SAC codes for each item', async () => {
    const data = await getMockInvoiceData();
    data.items[0].sacCode = '9964';
    data.items[1].sacCode = '9963';

    const invoice = await generateInvoice(data);
    const text = extractText(invoice);

    expect(text).toContain('9964');
    expect(text).toContain('9963');
  });

  it('correctly calculates CGST/SGST for intra-state', async () => {
    const data = await getMockInvoiceData();
    data.billTo.state = 'Delhi';
    data.agency.state = 'Delhi';

    const invoice = await generateInvoice(data);
    const text = extractText(invoice);

    // Should show CGST + SGST, not IGST
    expect(text).toContain('CGST');
    expect(text).toContain('SGST');
    expect(text).not.toContain('IGST');
  });

  it('correctly calculates IGST for inter-state', async () => {
    const data = await getMockInvoiceData();
    data.billTo.state = 'Maharashtra';
    data.agency.state = 'Delhi';

    const invoice = await generateInvoice(data);
    const text = extractText(invoice);

    // Should show IGST, not CGST/SGST
    expect(text).toContain('IGST');
    expect(text).not.toContain('CGST');
  });

  it('includes HSN/SAC code description', async () => {
    const invoice = await generateInvoice(await getMockInvoiceData());
    const text = extractText(invoice);

    expect(text).toMatch(/SAC.*9964/);
  });
});
```

### 7.2 Terms & Conditions Tests

```typescript
// compliance/terms-conditions.test.ts

describe('Terms & Conditions', () => {
  it('includes cancellation policy', async () => {
    const quote = await generateQuote(await getMockQuoteData());
    const text = extractText(quote);

    expect(text).toMatch(/cancellation.*policy/i);
    expect(text).toMatch(/\d+.*%.*refund/);
  });

  it('includes payment terms', async () => {
    const quote = await generateQuote(await getMockQuoteData());
    const text = extractText(quote);

    expect(text).toMatch(/payment.*terms/i);
    expect(text).toMatch(/advance.*payment/i);
  });

  it('includes validity period', async () => {
    const quote = await generateQuote(await getMockQuoteData());
    const text = extractText(quote);

    expect(text).toMatch(/valid.*until/i);
    expect(text).toMatch(/\d+.*days?/i);
  });
});
```

### 7.3 Data Privacy Tests

```typescript
// compliance/data-privacy.test.ts

describe('Data Privacy', () => {
  it('masks partial credit card numbers', async () => {
    const data = await getMockInvoiceData();
    data.paymentInfo = {
      cardNumber: '4532015112830366',
      cardHolder: 'Test Customer'
    };

    const invoice = await generateInvoice(data);
    const text = extractText(invoice);

    expect(text).not.toContain('4532015112830366');
    expect(text).toMatch(/\*{12}\d{4}/); // Last 4 digits visible
  });

  it('excludes sensitive internal notes', async () => {
    const data = await getMockQuoteData();
    data.internalNotes = 'Customer is VIP, offer 10% discount';

    const quote = await generateQuote(data);
    const text = extractText(quote);

    expect(text).not.toContain('VIP');
    expect(text).not.toContain('discount');
  });

  it('does not expose other customer data', async () => {
    const data = await getMockItineraryData();
    data.relatedBookings = [
      { customer: { name: 'Other Customer 1' } },
      { customer: { name: 'Other Customer 2' } }
    ];

    const itinerary = await generateItinerary(data);
    const text = extractText(itinerary);

    expect(text).not.toContain('Other Customer');
  });
});
```

---

## Part 8: Visual Regression Tests

### 8.1 PDF Visual Tests

```typescript
// visual-regression/pdf-visual.test.ts

describe('PDF Visual Regression', () => {
  it('matches quote PDF snapshot', async () => {
    const pdf = await generatePDF('QUOTE', await getMockQuoteData());

    await expect(pdf).toMatchPDFSnapshot('quote-standard.pdf');
  });

  it('matches itinerary PDF snapshot', async () => {
    const pdf = await generatePDF('ITINERARY', await getMockItineraryData());

    await expect(pdf).toMatchPDFSnapshot('itinerary-standard.pdf');
  });

  it('matches invoice PDF snapshot', async () => {
    const pdf = await generatePDF('INVOICE', await getMockInvoiceData());

    await expect(pdf).toMatchPDFSnapshot('invoice-standard.pdf');
  });
});
```

### 8.2 Email Rendering Tests

```typescript
// visual-regression/email-rendering.test.ts

describe('Email Rendering', () => {
  it('renders correctly in Gmail', async () => {
    const emailHtml = await generateEmailTemplate('QUOTE', await getMockQuoteData());

    const result = await testEmailRender({
      html: emailHtml,
      clients: ['gmail']
    });

    expect(result.gmail.score).toBeGreaterThan(90);
  });

  it('renders correctly in Outlook', async () => {
    const emailHtml = await generateEmailTemplate('QUOTE', await getMockQuoteData());

    const result = await testEmailRender({
      html: emailHtml,
      clients: ['outlook']
    });

    expect(result.outlook.score).toBeGreaterThan(80);
  });

  it('renders correctly on mobile', async () => {
    const emailHtml = await generateEmailTemplate('QUOTE', await getMockQuoteData());

    const result = await testEmailRender({
      html: emailHtml,
      viewport: { width: 375, height: 667 } // iPhone
    });

    expect(result.mobile.score).toBeGreaterThan(85);
  });
});
```

---

## Part 9: Security Tests

### 9.1 Authentication Tests

```typescript
// security/authentication.test.ts

describe('Authentication', () => {
  it('rejects requests without token', async () => {
    const response = await request(app)
      .post('/api/bundles/generate')
      .send({ bundleType: 'QUOTE', tripId: 'test-001' });

    expect(response.status).toBe(401);
  });

  it('rejects requests with expired token', async () => {
    const expiredToken = generateExpiredToken();

    const response = await request(app)
      .post('/api/bundles/generate')
      .set('Authorization', `Bearer ${expiredToken}`)
      .send({ bundleType: 'QUOTE', tripId: 'test-001' });

    expect(response.status).toBe(401);
  });

  it('validates token signature', async () => {
    const invalidToken = 'invalid.jwt.token';

    const response = await request(app)
      .post('/api/bundles/generate')
      .set('Authorization', `Bearer ${invalidToken}`)
      .send({ bundleType: 'QUOTE', tripId: 'test-001' });

    expect(response.status).toBe(401);
  });
});
```

### 9.2 Authorization Tests

```typescript
// security/authorization.test.ts

describe('Authorization', () => {
  it('prevents accessing other agencies bundles', async () => {
    const agentToken = await authenticateAsAgent('agency-a');
    const bundle = await createBundleForAgency('agency-b');

    const response = await request(app)
      .get(`/api/bundles/${bundle.id}`)
      .set('Authorization', `Bearer ${agentToken}`);

    expect(response.status).toBe(403);
  });

  it('prevents deleting system templates', async () => {
    const agentToken = await authenticateAsAgent('agency-a');

    const response = await request(app)
      .delete('/api/templates/sys-quote-default')
      .set('Authorization', `Bearer ${agentToken}`);

    expect(response.status).toBe(403);
  });
});
```

### 9.3 Input Validation Tests

```typescript
// security/input-validation.test.ts

describe('Input Validation', () => {
  it('sanitizes HTML in user input', async () => {
    const data = await getMockQuoteData();
    data.customer.name = '<script>alert("XSS")</script>John';

    const html = await compileTemplate('quote', data);
    expect(html).not.toContain('<script>');
    expect(html).toContain('John');
  });

  it('prevents SQL injection', async () => {
    const maliciousId = "'; DROP TABLE bundles; --";

    const response = await request(app)
      .get(`/api/bundles/${maliciousId}`)
      .set('Authorization', `Bearer ${authToken}`);

    // Should not cause SQL error
    expect(response.status).toBe(404); // Bundle not found, not 500
  });

  it('validates file upload types', async () => {
    const response = await request(app)
      .post('/api/templates')
      .set('Authorization', `Bearer ${authToken}`)
      .attach('file', 'test.exe', 'template.exe');

    expect(response.status).toBe(400);
    expect(response.body.error.code).toBe('INVALID_FILE_TYPE');
  });
});
```

### 9.4 Rate Limiting Tests

```typescript
// security/rate-limiting.test.ts

describe('Rate Limiting', () => {
  it('enforces rate limit', async () => {
    const requests = Array.from({ length: 105 }, () =>
      request(app)
        .post('/api/bundles/generate')
        .set('Authorization', `Bearer ${authToken}`)
        .send({ bundleType: 'QUOTE', tripId: 'test-001' })
    );

    const responses = await Promise.all(requests);
    const rateLimitedResponses = responses.filter(r => r.status === 429);

    expect(rateLimitedResponses.length).toBeGreaterThan(0);
  });

  it('includes rate limit headers', async () => {
    const response = await request(app)
      .get('/api/bundles')
      .set('Authorization', `Bearer ${authToken}`);

    expect(response.headers['x-ratelimit-limit']).toBeDefined();
    expect(response.headers['x-ratelimit-remaining']).toBeDefined();
  });
});
```

---

## Part 10: Test Data Management

### 10.1 Test Data Fixtures

```typescript
// fixtures/bundle-fixtures.ts

export const bundleFixtures = {
  quote: {
    minimal: {
      bundleType: 'QUOTE',
      tripId: 'test-trip-minimal',
      requiredFieldsOnly: true
    },
    standard: {
      bundleType: 'QUOTE',
      tripId: 'test-trip-standard',
      allFields: true
    },
    international: {
      bundleType: 'QUOTE',
      tripId: 'test-trip-intl',
      tripType: 'international'
    },
    group: {
      bundleType: 'QUOTE',
      tripId: 'test-trip-group',
      pax: { adults: 15, children: 5 }
    }
  },

  itinerary: {
    singleDay: {
      days: [createDayData(1)]
    },
    weekLong: {
      days: Array.from({ length: 7 }, (_, i) => createDayData(i + 1))
    },
    complex: {
      days: Array.from({ length: 14 }, (_, i) => createDayData(i + 1))
    }
  },

  invoice: {
    intraState: {
      agencyState: 'DL',
      customerState: 'DL'
    },
    interState: {
      agencyState: 'DL',
      customerState: 'MH'
    },
    export: {
      agencyState: 'DL',
      customerCountry: 'US'
    }
  }
};
```

### 10.2 Test Data Cleanup

```typescript
// helpers/test-cleanup.ts

export async function cleanupTestData() {
  await Bundle.deleteMany({ testId: { $exists: true } });
  await Template.deleteMany({ category: 'TEST' });
  await clearTestStorage();
}

export async function setupTestData() {
  await cleanupTestData();
  await createTestTrip('test-trip-001');
  await createTestTrip('test-trip-002');
  // ... more test data
}
```

---

## Summary

This document provides comprehensive test coverage:

1. **Testing Strategy** — Testing pyramid, coverage targets, test categories
2. **Unit Tests** — Template helpers, components, utilities
3. **Integration Tests** — API endpoints, services, templates
4. **E2E Tests** — Critical user journeys, error handling
5. **Edge Cases** — Empty data, special characters, large datasets, timezones, currency
6. **Performance Tests** — Generation time, concurrent load, file size
7. **Compliance Tests** — GST invoices, terms, data privacy
8. **Visual Regression** — PDF snapshots, email rendering
9. **Security Tests** — Authentication, authorization, input validation, rate limiting
10. **Test Data** — Fixtures, cleanup, setup

**Next Document**: OUTPUT_15_METRICS_DEFINITIONS_COMPLETE.md — Complete metrics definitions and KPIs

---

**Document**: OUTPUT_14_TESTING_SCENARIOS_COMPLETE.md
**Series**: Output Panel & Bundle Generation Deep Dive
**Status**: ✅ Complete
**Last Updated**: 2026-04-23
