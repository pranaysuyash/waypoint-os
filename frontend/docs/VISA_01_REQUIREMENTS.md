# Visa & Documentation 01: Requirements Engine

> Determining visa requirements, passport validity, and travel documentation

---

## Document Overview

**Focus:** Understanding and communicating travel documentation requirements
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Visa Requirements
- How do we determine visa requirements by destination?
- What factors affect requirements? (Nationality, purpose, duration?)
- What are the different visa types? (Tourist, business, transit?)
- How do we handle changing rules?

### 2. Data Sources
- Where do we get visa requirement information?
- Are there APIs for this data?
- How do we keep data current?
- What are the reliable sources?

### 3. Passport Validity
- What are the passport validity rules?
- How do we check expiry dates?
- What about blank pages requirements?
- How do we handle renewal reminders?

### 4. Communication
- How do we present requirements to customers?
- When do we communicate requirements?
- What happens if requirements change after booking?
- How do we handle non-compliance?

---

## Research Areas

### A. Visa Requirement Factors

**Determination Factors:**

| Factor | Impact | Examples |
|--------|--------|----------|
| **Citizenship** | Primary | Different rules by passport |
| **Destination** | Primary | Country-specific rules |
| **Purpose** | Secondary | Tourist vs. business vs. student |
| **Duration** | Secondary | Short stay vs. long stay |
| **History** | Tertiary | Previous denials, overstay |
| **Transit** | Special | Transit visa requirements |

**Research:**
- How do these factors interact?
- What are the edge cases?
- How do we handle dual citizenship?

### B. Visa Types

| Visa Type | Purpose | Typical Duration | Research Needed |
|-----------|---------|------------------|-----------------|
| **Tourist** | Leisure travel | 30-90 days | ? |
| **Business** | Work-related meetings | 30-90 days | ? |
| **Transit** | Passing through | Usually < 24 hours | ? |
| **Student** | Study | Duration of course | ? |
| **Work** | Employment | Contract duration | ? |
| **E-visa** | Electronic pre-approval | Varies | ? |
| **Visa on arrival** | Obtain at entry | Varies | ? |

**Research:**
- Which destinations offer e-visas?
- Which offer visa on arrival?
- What are the requirements for each?

### C. Data Sources

**Potential Sources:**

| Source | Type | Reliability | API? |
|--------|------|-------------|------|
| **IATA Travel Centre** | Official | High | ? |
| **Government websites** | Official | High | Rarely |
| **Consulate data** | Official | High | No |
| **Third-party APIs** | Aggregated | Varies | Yes |
| **Manual research** | Curated | Depends | No |

**Research:**
- Which sources offer APIs?
- What are the costs?
- How frequently do rules change?

### D. Passport Requirements

| Requirement | Typical Rule | Research Needed |
|-------------|--------------|-----------------|
| **Validity after travel** | 3-6 months | Varies by country |
| **Blank pages** | 1-4 pages | Varies by country |
| **Issuance** | Usually within last 10 years | Some countries differ |
| **Damage** | Must be intact | No torn pages, etc. |

**Research:**
- What are the exact rules by destination?
- How do we communicate this clearly?

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface VisaRequirement {
  id: string;
  destinationCountry: string;
  citizenship: string;  // Passport-issuing country

  // Requirements
  visaRequired: boolean;
  visaType?: VisaType;
  accessMethod?: VisaAccessMethod;

  // Conditions
  maxDuration?: number;  // Days
  allowedEntries: 'single' | 'double' | 'multiple';
  purposeRestrictions?: string[];

  // Process
  processingTime?: Duration;
  cost?: Money;
  requirements?: DocumentRequirement[];

  // Passport
  passportValidityRequired: Duration;  // Beyond trip end
  blankPagesRequired?: number;

  // Exemptions
  exemptions?: Exemption[];

  // Additional info
  notes?: string[];
  officialSource?: string;
  lastUpdated: Date;
}

type VisaType =
  | 'tourist'
  | 'business'
  | 'transit'
  | 'student'
  | 'work'
  | 'evisa'
  | 'visa_on_arrival';

type VisaAccessMethod =
  | 'embassy'
  | 'evisa_online'
  | 'visa_on_arrival'
  | 'visa_free'
  | 'eta';  // Electronic Travel Authority

interface DocumentRequirement {
  type: string;
  description: string;
  required: boolean;
}

interface Exemption {
  condition: string;  // e.g., "Under 16 years old"
  exemptFrom: string[];
}
```

---

## Requirement Determination Logic

```
For each (destination, citizenship, purpose, duration):
  1. Check visa-free access
  2. If not visa-free, check visa type required
  3. Determine access method (embassy, e-visa, VOA)
  4. Check passport validity requirements
  5. Check additional document requirements
  6. Return requirements + process information
```

---

## Communication Strategy

**When to Communicate:**

| Timing | Content | Urgency |
|--------|---------|---------|
| **At search** | Basic requirements | Low |
| **At booking** | Detailed requirements | Medium |
| **Before departure** | Reminders, check status | High |
| **If rules change** | Immediate notification | Critical |

**Communication Channels:**

| Channel | Use For |
|---------|---------|
| **Trip summary** | Overview of requirements |
| **Email** | Detailed requirements, links |
| **Timeline** | Reminders, deadlines |
| **Dashboard alerts** | Critical changes |

---

## Open Problems

### 1. Rule Changes
**Challenge:** Visa rules change frequently

**Options:**
- Real-time API checks
- Periodic data refresh
- Manual updates
- Link to official sources

**Research:** How often do rules change?

### 2. Edge Cases
**Challenge:** Dual citizenship, residence permits, etc.

**Questions:**
- Which passport should be used?
- Does residence permit matter?
- How do we handle complex cases?

### 3. Liability
**Challenge:** What if we give incorrect information?

**Questions:**
- What are our disclaimers?
- How do we minimize risk?
- What is our liability?

### 4. Non-Standard Travel
**Challenge:** Multi-country trips, cruises, etc.

**Questions:**
- How do we handle complex itineraries?
- What about transit visas?
- How do we check multiple requirements?

---

## Competitor Research Needed

| Competitor | Visa Information Approach | Notable Patterns |
|------------|---------------------------|------------------|
| **Expedia** | ? | ? |
| **Booking.com** | ? | ? |
| **Airline sites** | ? | ? |
| **Visa services** | ? | ? |

---

## Data Sources to Investigate

1. **IATA Travel Centre** - Official industry source
2. **Sherpa** - Visa requirement API
3. **GDS systems** - May have visa data
4. **Government APIs** - Where available
5. **Consulate websites** - Primary source

---

## Experiments to Run

1. **API availability test:** Which sources offer APIs?
2. **Accuracy test:** Compare multiple sources
3. **Change frequency study:** How often do rules change?
4. **User test:** How do customers interpret requirements?

---

## References

- [Safety Systems](./SAFETY_DEEP_DIVE_MASTER_INDEX.md) — Compliance checks
- [Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md) — Pre-trip checklist

---

## Next Steps

1. Audit visa requirement data sources
2. Test API availability
3. Build requirements database
4. Design requirement display
5. Implement change monitoring

---

**Status:** Research Phase — Requirements unknown

**Last Updated:** 2026-04-27
