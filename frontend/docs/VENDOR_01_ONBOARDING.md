# Vendor Onboarding — Supplier Registration & Qualification

> Research document for supplier onboarding workflows, qualification criteria, and integration patterns.

---

## Key Questions

1. **What's the minimum viable data we need from a supplier before they can be listed?**
2. **How do we verify supplier credentials (licenses, insurance, certifications)?**
3. **What's the right balance between onboarding speed and due diligence?**
4. **How do we handle suppliers who operate across multiple service categories (hotel + transfers)?**
5. **What integration patterns work for onboarding suppliers with existing booking systems?**
6. **How do we tier suppliers (preferred, approved, probationary) during onboarding?**

---

## Research Areas

### Supplier Categories in Travel

```typescript
type SupplierCategory =
  | 'accommodation'     // Hotels, resorts, homestays
  | 'airline'           // Airlines, charters
  | 'ground_transport'  // Transfers, car rentals
  | 'activities'        // Tours, experiences, attractions
  | 'insurance'         // Travel insurance providers
  | 'visa_services'     // Visa processing agencies
  | 'connectivity'      // SIM/eSIM providers
  | 'forex'             // Currency exchange services
  | 'cruise'            // Cruise lines
  | 'rail'              // Rail operators
  | 'catering'          // Meal services, special diets
  | 'event_venue'       // Conference venues, wedding halls
  | 'guide'             // Tour guides, interpreters
  | 'photography'       // Travel photography services
  | 'other';            // Miscellaneous

interface SupplierProfile {
  supplierId: string;
  legalName: string;
  tradingName: string;
  categories: SupplierCategory[];
  tier: SupplierTier;
  status: OnboardingStatus;
  contacts: SupplierContact[];
  credentials: SupplierCredential[];
  integrations: IntegrationConfig[];
  onboardedAt?: Date;
  onboardedBy: string;
}

type SupplierTier =
  | 'preferred'     // Strategic partner, best rates, priority
  | 'approved'      // Standard supplier, meets all criteria
  | 'probationary'  // New or under review, limited exposure
  | 'suspended';    // Temporarily disabled

type OnboardingStatus =
  | 'application'       // Initial application submitted
  | 'document_review'   // Documents under review
  | 'credential_check'  // Credentials being verified
  | 'commercial_terms'  // Negotiating rates and terms
  | 'integration'       // Technical integration in progress
  | 'test_bookings'     // Test transactions being processed
  | 'active'            // Fully onboarded and active
  | 'rejected';         // Application rejected
```

### Qualification Criteria by Category

**Accommodation suppliers:**
- Star rating / classification
- Fire safety certification
- Health and hygiene rating
- Tourism board registration
- Cancellation policy flexibility
- Payment terms

**Transport suppliers:**
- Vehicle fleet details and insurance
- Driver licensing and background checks
- Route permits and licenses
- Safety record and incident history
- 24/7 availability

**Activity providers:**
- Adventure sports certifications
- Insurance coverage details
- Guide qualifications
- Group size limitations
- Safety equipment standards

**Open questions:**
- Who performs physical verification (site visits) for accommodation and venue suppliers?
- How do we handle suppliers in markets where regulatory infrastructure is weak?
- What's the reciprocity policy for suppliers already vetted by major OTAs?

### Onboarding Workflow Design

**Questions:**
- Self-service portal vs. agent-assisted onboarding?
- How to handle multi-category suppliers with different qualification criteria per category?
- What's the SLA for each onboarding stage?

**Potential fast-track paths:**
- Suppliers already verified by global platforms (Booking.com, Expedia)
- Government-licensed entities (airlines, rail operators)
- Referrals from trusted existing suppliers

### Integration Configuration

```typescript
interface IntegrationConfig {
  integrationType: 'api' | 'edi' | 'email' | 'portal' | 'manual';
  connectivity: ConnectivityDetail;
  dataMapping: DataMappingConfig;
  testStatus: 'pending' | 'in_progress' | 'passed' | 'failed';
}

type ConnectivityDetail =
  | { type: 'rest_api'; baseUrl: string; authMethod: string }
  | { type: 'soap'; wsdlUrl: string }
  | { type: 'edi'; protocol: string; endpoint: string }
  | { type: 'email'; address: string; format: 'structured' | 'freeform' }
  | { type: 'portal'; url: string }
  | { type: 'manual'; instructions: string };
```

---

## Open Problems

1. **Credential verification at scale** — Manually verifying licenses, insurance, and certifications for thousands of suppliers is unsustainable. Need automated verification APIs or third-party verification services.

2. **Supplier data freshness** — Credentials expire, insurance lapses, ownership changes. How to maintain continuous verification without creating admin burden?

3. **Cross-border supplier onboarding** — A Thai hotel, a Sri Lankan transfer operator, and an Indian airline all have different regulatory frameworks. Need jurisdiction-aware qualification rules.

4. **Multi-category supplier overhead** — A resort offering accommodation, activities, and transfers triggers three separate qualification flows. How to avoid duplication?

5. **Supplier self-service adoption** — Many small suppliers (local guides, homestay owners) may struggle with digital onboarding portals. What's the minimum viable onboarding path?

---

## Next Steps

- [ ] Research automated credential verification services (Dun & Bradstreet, third-party APIs)
- [ ] Map qualification criteria per supplier category
- [ ] Design fast-track onboarding for pre-verified suppliers
- [ ] Investigate supplier data management platforms ( vendor management systems)
- [ ] Study OTA onboarding patterns (Booking.com extranet, Airbnb host onboarding)
