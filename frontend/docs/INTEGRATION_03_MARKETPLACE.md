# Integration Hub & Connectors — Integration Marketplace

> Research document for third-party connector marketplace, partner integrations, and community connectors.

---

## Key Questions

1. **How do agencies discover and enable integrations?**
2. **What's the partner integration model for suppliers?**
3. **How do we enable custom connectors built by agencies?**
4. **What's the marketplace governance model?**
5. **How do we handle integration billing and cost tracking?**

---

## Research Areas

### Marketplace Model

```typescript
interface IntegrationMarketplace {
  categories: MarketplaceCategory[];
  featured: string[];
  popular: string[];
  recentlyAdded: string[];
  search: MarketplaceSearch;
}

interface MarketplaceListing {
  listingId: string;
  name: string;
  provider: string;
  category: IntegrationCategory;
  description: string;
  logo: string;
  screenshots: string[];
  pricing: ListingPricing;
  capabilities: string[];
  requirements: string[];
  setupTime: string;                 // "5 minutes", "1 hour"
  rating: number;
  reviewCount: number;
  usageCount: number;                // Agencies using this integration
  status: ListingStatus;
  documentation: string;
  supportContact: string;
}

type ListingPricing =
  | { type: 'free' }
  | { type: 'freemium'; freeLimit: string; paidFrom: string }
  | { type: 'paid'; price: string; billing: 'monthly' | 'annual' | 'per_use' }
  | { type: 'included' };            // Included in platform subscription

type ListingStatus =
  | 'verified'                       // Platform-verified connector
  | 'community'                      // Community-contributed
  | 'beta'                           // In beta testing
  | 'deprecated';                    // No longer maintained

// Marketplace UX:
// Browse by category: "Payments", "Accounting", "Suppliers"
// Search: "Tally" → Shows Tally integration
// Filter: Free only, verified only, specific capabilities
// Compare: Side-by-side comparison of similar integrations
// Reviews: Agent reviews and ratings
// Setup wizard: Step-by-step setup guide per integration
```

### Partner Integration Program

```typescript
interface PartnerIntegration {
  partnerId: string;
  partnerName: string;
  partnerType: PartnerType;
  integrationLevel: IntegrationLevel;
  technicalContact: string;
  businessContact: string;
  sli: SLIConfig;                    // Service Level Indicator
  support: SupportConfig;
}

type PartnerType =
  | 'supplier'                       // Hotel chain, airline, tour operator
  | 'technology'                     // GDS, payment gateway, CRM
  | 'service'                        // Insurance, visa, forex
  | 'platform';                      // Other travel platforms

type IntegrationLevel =
  | 'certified'                      // Meets all platform standards
  | 'standard'                       // Basic integration working
  | 'pilot';                         // In pilot/testing phase

// Partner integration tiers:
// Certified (gold standard):
//   - Full API coverage (search, book, cancel, modify)
//   - SLA: 99.9% uptime, <2s response time
//   - Real-time availability sync
//   - Dedicated support channel
//   - Co-marketing agreement
//
// Standard:
//   - Core API coverage (search, book, cancel)
//   - SLA: 99.5% uptime, <5s response time
//   - Periodic availability sync
//   - Standard support
//
// Pilot:
//   - Basic API coverage (search, book)
//   - Testing with select agencies
//   - No SLA commitment
//   - Email support only
```

### Custom Connector SDK

```typescript
interface CustomConnector {
  connectorId: string;
  agencyId: string;
  name: string;
  type: 'custom';
  config: CustomConnectorConfig;
  code: string;                      // JavaScript/TypeScript connector code
  status: 'development' | 'testing' | 'production';
  createdBy: string;
  createdAt: Date;
}

// Custom connector SDK features:
// 1. Template: Start from a connector template
// 2. Sandbox: Test against sandbox environment
// 3. Validation: Auto-validate against connector specification
// 4. Logging: Built-in logging and error reporting
// 5. Publishing: Share with own agency or submit to marketplace

// SDK example (simplified):
// export default class MySupplierConnector extends BaseConnector {
//   async authenticate() {
//     // Implement auth logic
//   }
//
//   async searchHotels(params: HotelSearchParams): Promise<Hotel[]> {
//     // Map internal params to supplier API
//     const response = await this.client.get('/hotels', { params });
//     // Map supplier response to internal format
//     return response.data.map(this.mapHotel);
//   }
//
//   async bookHotel(params: BookHotelParams): Promise<BookResult> {
//     // Implement booking logic
//   }
// }
```

### Integration Cost Tracking

```typescript
interface IntegrationCost {
  integrationId: string;
  agencyId: string;
  period: string;                    // "2026-04"
  costs: CostEntry[];
  totalCost: number;
  budget: number;
  budgetUtilization: number;
}

interface CostEntry {
  date: Date;
  operation: string;                 // "hotel_search", "flight_book"
  volume: number;                    // Number of calls
  costPerCall: number;
  totalCost: number;
  currency: string;
}

// Cost tracking for common integrations:
// Amadeus: $0.01-0.05 per API call (varies by endpoint)
// Hotelbeds: Free for search, commission on booking
// Razorpay: 2% per transaction (domestic), 3% (international)
// WhatsApp Business: ₹0.50-2.00 per business-initiated message
// SendGrid: $0.01 per 100 emails
// Google Maps: $0.005 per geocoding request, $0.007 per directions

// Cost control:
// Monthly budget per integration
// Alert at 80% budget utilization
// Auto-disable at 100% budget (with override option)
// Cost optimization suggestions (cache more, batch requests)
// Cost per booking metric (how much integration cost per completed booking)
```

---

## Open Problems

1. **Integration quality variance** — Certified integrations are high quality, but community connectors may be unreliable. Need quality tiers that are visible to users.

2. **Supplier onboarding friction** — Every new supplier needs a connector. Building connectors is engineering work. Need low-code/no-code connector builder.

3. **Integration overlap** — Three hotel aggregators (Hotelbeds, Expedia, Booking.com) for the same property. Need deduplication and best-price selection.

4. **Cost visibility** — Agencies don't know how much they spend on integrations until the bill arrives. Need real-time cost tracking with budget alerts.

5. **Integration dependency risk** — If a partner integration goes down, the platform feature breaks. Need graceful degradation per integration.

---

## Next Steps

- [ ] Design integration marketplace UI with discovery and setup
- [ ] Build partner integration program framework
- [ ] Create custom connector SDK with templates
- [ ] Design integration cost tracking with budget alerts
- [ ] Study integration marketplaces (Zapier, Shopify App Store, Salesforce AppExchange)
