# Visa & Documentation 02: Service Providers

> Visa facilitation, attestation services, and documentation assistance

---

## Document Overview

**Focus:** Helping customers obtain visas and travel documents
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Service Provider Landscape
- Who provides visa facilitation services?
- What services do they offer? (Application help, expedited processing, etc.)
- Which providers operate in our key markets?
- What are the service levels and costs?

### 2. Integration Options
- Can we integrate with visa service providers?
- What APIs exist?
- How does the handoff work?
- What is the revenue model?

### 3. Service Types
- What types of visa assistance exist?
- What about document attestation?
- What about passport services?
- What about photo services?

### 4. Customer Experience
- How do we present visa services?
- When do we offer them?
- How do we track application status?
- What happens if applications are rejected?

---

## Research Areas

### A. Service Provider Types

**Provider Categories:**

| Type | Description | Examples |
|------|-------------|----------|
| **Visa facilitators** | Help with applications, expedited processing | VFS Global, BLS International |
| **Travel document services** | Passport, photos, attestation | Cox & Kings, Thomas Cook |
| **Online platforms** | Digital-first visa assistance | iVisa, VisaHQ |
| **Specialized services** | Complex cases, corporate | Specialist agencies |

**Research:**
- Who operates in India?
- Who operates in key destinations?
- What are the service levels?

### B. Service Offerings

| Service | Description | Typical Cost | Research Needed |
|---------|-------------|--------------|-----------------|
| **Application assistance** | Help filling forms | $10-$50 | ? |
| **Document verification** | Check documents before submission | $20-$100 | ? |
| **Expedited processing** | Faster processing | $50-$200+ | ? |
| **Attestation** | Document authentication | Varies | ? |
| **Passport photos** | compliant photos | $5-$20 | ? |
| **Courier services** | Document pickup/delivery | $10-$50 | ? |
| **Consultation** | Advice on complex cases | $50-$200 | ? |

**Research:**
- Which services are most in demand?
- What are the actual costs?
- What are the margins?

### C. Integration Models

**Model 1: Referral**

```
We identify need → Refer customer to provider → Customer engages provider → We earn referral fee
```

**Pros:** Simple, no operational overhead
**Cons:** Lower revenue, customer leaves platform

**Model 2: Embedded**

```
We identify need → Customer starts process on our site → Hand off to provider → Provider manages → Status back to us
```

**Pros:** Better experience, higher revenue
**Cons:** Integration complexity, dependency

**Model 3: Full-Service**

```
We manage entire process → Use provider as backend → We own customer relationship
```

**Pros:** Full control, best experience
**Cons:** High operational cost, compliance burden

**Research:**
- Which model fits our stage?
- What are the economics of each?

### D. Application Tracking

**Tracking Requirements:**

| Status | Meaning | Customer Communication |
|--------|---------|------------------------|
| **Documents submitted** | We have documents | "Documents received, under review" |
| **Submitted to embassy** | Application submitted | "Application submitted to embassy" |
| **Under processing** | Embassy processing | "Visa under processing" |
| **Approved** | Visa granted | "Visa approved, passport returned" |
| **Rejected** | Visa denied | "Visa rejected, reason: X" |

**Research:**
- How do we get status updates?
- What if there's no tracking?
- How do we handle delays?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface VisaService {
  id: string;
  name: string;
  type: ServiceProviderType;

  // Coverage
  destinations: string[];
  origins: string[];

  // Services
  services: VisaServiceType[];

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;

  // Commercial
  commissionRate?: number;
  pricing?: ServicePricing;
}

type ServiceProviderType =
  | 'facilitator'
  | 'online_platform'
  | 'document_specialist'
  | 'full_service';

type VisaServiceType =
  | 'application_assistance'
  | 'document_verification'
  | 'expedited_processing'
  | 'attestation'
  | 'passport_service'
  | 'photo_service'
  | 'consultation';

interface VisaApplication {
  id: string;
  tripId: string;
  customerId: string;

  // Destination
  destinationCountry: string;
  visaType: VisaType;

  // Service
  provider: string;
  services: VisaServiceType[];

  // Status
  status: ApplicationStatus;
  submittedAt: Date;
  expectedCompletion?: Date;
  completedAt?: Date;

  // Documents
  documents: ApplicationDocument[];

  // Tracking
  tracking: ApplicationTracking[];

  // Financial
  cost: {
    serviceFee: Money;
    governmentFee: Money;
    total: Money;
    currency: string;
  };
}

type ApplicationStatus =
  | 'draft'
  | 'documents_collected'
  | 'submitted_to_provider'
  | 'submitted_to_embassy'
  | 'under_processing'
  | 'approved'
  | 'rejected'
  | 'cancelled';
```

---

## Customer Flow

**Typical Journey:**

```
1. Trip booked → Visa requirement identified
2. Offer visa services → Customer accepts
3. Collect documents → Upload or pickup
4. Submit to provider → Application processed
5. Track status → Updates to customer
6. Receive passport → Visa granted or rejected
```

**Research:**
- When is the best time to offer services?
- How do we collect documents?
- What are the common failure points?

---

## Open Problems

### 1. Application Rejection
**Challenge:** Customer's visa application is rejected

**Questions:**
- What is our liability?
- How do we handle refunds?
- What about the trip booking?

### 2. Document Privacy
**Challenge:** Handling sensitive documents (passports, bank statements)

**Questions:**
- How do we protect customer data?
- Where are documents stored?
- Who has access?

### 3. Timing Uncertainty
**Challenge:** Visa processing times vary

**Options:**
- Build in buffer time
- Offer expedited processing
- Warn customers of uncertainty

**Research:** What are typical processing times?

### 4. Regional Complexity
**Challenge:** Different processes by region

**Questions:**
- How do we handle regional variations?
- Can we have one integration per region?
- What are the common patterns?

---

## Competitor Research Needed

| Competitor | Visa Services Approach | Notable Patterns |
|------------|-----------------------|------------------|
| **Expedia** | ? | ? |
| **Booking.com** | ? | ? |
| **Airlines** | ? | ? |
| **Local agents** | ? | ? |

---

## Service Providers to Investigate

**Global:**
- VFS Global
- BLS International
- iVisa
- VisaHQ

**India:**
- Cox & Kings
- Thomas Cook
- VFS Global (India)

**Research:** What APIs exist? What are the terms?

---

## Experiments to Run

1. **API availability test:** Which providers offer APIs?
2. **Service audit:** What services are most needed?
3. **Pricing analysis:** What are typical costs?
4. **Customer interview:** What are pain points?

---

## References

- [Safety Systems](./SAFETY_DEEP_DIVE_MASTER_INDEX.md) — Risk and compliance
- [Timeline](./TIMELINE_DEEP_DIVE_MASTER_INDEX.md) — Event tracking

---

## Next Steps

1. Audit visa service providers
2. Test API availability
3. Design service offering
4. Build integration
5. Launch pilot program

---

**Status:** Research Phase — Services unknown

**Last Updated:** 2026-04-27
