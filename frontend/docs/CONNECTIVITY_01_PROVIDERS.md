# SIM Cards & Connectivity 01: Provider Landscape

> Travel SIM cards, eSIM providers, and roaming options

---

## Document Overview

**Focus:** Understanding the travel connectivity ecosystem
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Provider Types
- Who are the eSIM providers? (Airalo, Nomad, etc.)
- Who are the physical SIM providers?
- How do carrier roaming plans compare?
- What about regional providers?

### 2. Technology
- How does eSIM work? (Device support, provisioning)
- Which devices support eSIM?
- What are the limitations?
- How does activation work?

### 3. Coverage & Quality
- How do providers differ by region?
- Who has the best coverage in key destinations?
- How do we measure network quality?
- What about roaming agreements?

### 4. Pricing Models
- How are data plans priced? (Per GB, per day, unlimited?)
- What about voice/SMS?
- How do we compare across providers?
- What are the hidden costs?

---

## Research Areas

### A. eSIM Providers

**Global Players:**

| Provider | Coverage | Pricing Model | Notes |
|----------|----------|---------------|-------|
| **Airalo** | 200+ countries | Per GB, regional | ? |
| **Nomad** | 100+ countries | Per GB, daily | ? |
| **Holafly** | 160+ countries | Unlimited daily | ? |
| **GigSky** | 190+ countries | Per GB | ? |
| **Ubigi** | 140+ countries | Per GB, regional | ? |
| **Truely** | Select countries | Per GB | ? |

**Research Needed:**
- API availability for each
- Commission structures
- Integration complexity
- Quality of service

### B. Physical SIM Providers

**Provider Types:**

| Type | Examples | Delivery Method |
|------|----------|-----------------|
| **Online specialists** | OneSIMCard, WorldSIM | Mail delivery |
| **Airport kiosks** | Various | Pickup at airport |
| **Local carriers** | Destination providers | In-country purchase |
| **Travel retailers** | Travel agencies, exchange | Various |

**Research:**
- Which providers ship to India?
- What are delivery times?
- How do we handle activation?

### C. Carrier Roaming

**Indian Carriers:**

| Carrier | Roaming Plans | Activation | Research Needed |
|---------|---------------|------------|-----------------|
| **Airtel** | Pre-packaged plans | App/ USSD | ? |
| **Jio** | Roaming plans | App | ? |
| **Vi** | Roaming plans | App | ? |

**Questions:**
- How do customers activate roaming?
- What are the costs?
- How do we compare roaming vs. local SIM?

### D. Device Compatibility

**eSIM Support:**

| Device Category | eSIM Support | Penetration |
|----------------|--------------|-------------|
| **iPhones** | XS and newer | High |
| **Samsung** | S20 and newer | Growing |
| **Google Pixel** | 3 and newer | Medium |
| **Other Android** | Varies | Low |
| **Older devices** | None | N/A |

**Research:**
- What percentage of travelers have eSIM-compatible devices?
- How do we check device compatibility?
- What alternatives for non-eSIM devices?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface ConnectivityProvider {
  id: string;
  name: string;
  type: ProviderType;

  // Coverage
  regions: string[];
  countries: string[];

  // Integration
  hasApi: boolean;
  integrationStatus: IntegrationStatus;

  // Commercial
  commissionRate?: number;
  pricingModel: PricingModel;

  // Capabilities
    esimSupported: boolean;
  physicalSimSupported: boolean;
  instantActivation: boolean;

  // Plans
  plans: ConnectivityPlan[];
}

type ProviderType =
  | 'esim_provider'
  | 'physical_sim_provider'
  | 'carrier_roaming'
  | 'aggregator';

interface ConnectivityPlan {
  id: string;
  providerId: string;
  name: string;

  // Coverage
  region: string;
  countries: string[];

  // Data
  dataAllowance: DataAllowance;
  validity: Duration;

  // Pricing
  pricing: {
    amount: Money;
    currency: string;
    includes?: string[];  // Voice minutes, SMS
  };

  // Technical
  esim: boolean;
  physicalSim: boolean;
  networkSpeed: '3G' | '4G' | '4G_LTE' | '5G';

  // Restrictions
  fairUsagePolicy?: string;
  tetheringAllowed?: boolean;
}

type DataAllowance =
  | { type: 'limited', gb: number }
  | { type: 'unlimited', fairUsageGb?: number }
  | { type: 'daily', gbPerDay: number };
```

---

## Comparison Framework

**Factors to Compare:**

| Factor | Weight | Research Needed |
|--------|--------|-----------------|
| **Price per GB** | High | How to calculate? |
| **Coverage quality** | High | How to measure? |
| **Ease of activation** | Medium | Time to activate? |
| **Network speed** | Medium | Actual vs. advertised? |
| **Customer support** | Low | How to assess? |
| **Validity period** | Medium | Flexibility? |

---

## Integration Approaches

### 1. Direct eSIM Provider API
**Best for:** Airalo, Nomad, etc.

**Flow:**
```
Customer selects plan → Create order with provider → Get QR code → Customer scans → Activated
```

**Considerations:**
- Real-time availability
- Instant activation
- API documentation quality

### 2. Affiliate/Referral
**Best for:** Providers without APIs

**Flow:**
```
Customer selects plan → Redirect to provider → Earn commission
```

**Pros:** Simple
**Cons:** Customer leaves platform

### 3. White Label
**Best for:** Full control

**Flow:**
```
Customer buys from us → We provision via backend → We handle support
```

**Pros:** Best experience
**Cons:** High operational cost

---

## Open Problems

### 1. Device Compatibility Detection
**Challenge:** How do we know if customer's device supports eSIM?

**Options:**
- Ask customer (self-report)
- Detect from user agent (unreliable)
- Assume and offer refund if doesn't work

**Research:** What are the best practices?

### 2. Network Quality Claims
**Challenge:** Providers claim 4G/5G, but actual experience varies

**Questions:**
- How do we validate claims?
- What do we tell customers?
- How do we handle complaints?

### 3. Multi-Destination Trips
**Challenge:** Customer visiting 3 countries

**Options:**
- Regional plan (covers multiple)
- Separate plans per country
- Global plan

**Research:** Which is most economical?

### 4. Refunds for Unused Data
**Challenge:** Customer uses 1GB of 5GB plan

**Questions:**
- Is any refund possible?
- Can plans be modified mid-trip?
- What about rollover?

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **Airalo directly** | ? | ? |
| **Travel agents** | ? | ? |
| **Airline sites** | ? | ? |

---

## Experiments to Run

1. **API availability test:** Which eSIM providers have bookable APIs?
2. **Device compatibility study:** What % of travelers have eSIM phones?
3. **Price comparison:** How do providers compare on price?
4. **Network quality test:** How to measure actual performance?

---

## References

- [Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md) — Add-on component
- [Activities](./ACTIVITIES_MASTER_INDEX.md) — Similar add-on patterns

---

## Next Steps

1. Audit eSIM provider APIs
2. Test device compatibility detection
3. Compare pricing across providers
4. Design recommendation engine
5. Build ordering flow

---

**Status:** Research Phase — Provider landscape unknown

**Last Updated:** 2026-04-27
