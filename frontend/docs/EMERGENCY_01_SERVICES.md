# Emergency Assistance 01: Services

> Types of emergency services for travelers

---

## Document Overview

**Focus:** Emergency service types
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Service Types
- What emergency services do travelers need?
- What are the different emergency categories?
- What services do we provide directly?
- What do we outsource?

### Medical Emergencies
- What constitutes a medical emergency?
- How do we provide medical assistance?
- What about evacuation?
- What about pre-existing conditions?

### Travel Emergencies
- What about lost documents?
- What about natural disasters?
- What about political unrest?
- What about terrorism?

### Service Providers
- Who provides emergency services?
- What are the integration points?
- What are the costs?
- What about insurance coverage?

---

## Research Areas

### A. Emergency Categories

**Medical:**

| Type | Description | Response | Research Needed |
|------|-------------|----------|-----------------|
| **Illness/Injury** | Sickness, injury abroad | Local hospital, insurance | ? |
| **Hospitalization** | Admission required | Insurance coordination | ? |
| **Evacuation** | Medical transport home | Complex, expensive | ? |
| **Prescription** | Medication needs | Local pharmacy | ? |
| **Death** | Worst case | Consular, repatriation | ? |

**Travel:**

| Type | Description | Response | Research Needed |
|------|-------------|----------|-----------------|
| **Lost passport** | No travel document | Embassy assistance | ? |
| **Lost tickets** | No bookings | Reissuance | ? |
| **Missed flight** | Connection missed | Rebooking | ? |
| **Stolen belongings** | Theft | Police report, consular | ? |

**Crisis:**

| Type | Description | Response | Research Needed |
|------|-------------|----------|-----------------|
| **Natural disaster** | Earthquake, flood, etc. | Evacuation, alerts | ? |
| **Political unrest** | Protests, violence | Evacuation, travel warning | ? |
| **Terrorism** | Attacks | Lockdown, evacuation | ? |
| **Pandemic** | Disease outbreak | Borders close, quarantine | ? |

### B. Service Components

**Direct Services:**

| Service | Provided By | Research Needed |
|----------|-------------|-----------------|
| **24/7 hotline** | In-house or partner | ? |
| **Travel assistance** | In-house | ? |
| **Coordination** | In-house | ? |
| **Communication** | In-house | ? |

**Partnered Services:**

| Service | Partner Type | Research Needed |
|----------|-------------|-----------------|
| **Medical** | Insurance, assistance companies | ? |
| **Evacuation** | Specialized providers | ? |
| **Legal** | Local lawyers | ? |
| **Translation** | Local services | ? |
| **Security** | Security firms | ? |

### C. Insurance Integration

**Travel Insurance Coverage:**

| Coverage | Typically Included | Research Needed |
|----------|---------------------|-----------------|
| **Medical emergencies** | Yes | Limits? |
| **Medical evacuation** | Sometimes | Threshold? |
| **Trip cancellation** | Yes | Covered reasons? |
| **Lost documents** | Sometimes | Limits? |
| **24/7 assistance** | Yes | Included? |

### D. Response Levels

**Severity Levels:**

| Level | Description | Response Time | Research Needed |
|-------|-------------|---------------|-----------------|
| **Critical** | Life-threatening | Immediate | ? |
| **Urgent** | Needs quick attention | < 1 hour | ? |
| **High** | Important but not urgent | < 4 hours | ? |
| **Medium** | Can wait | < 24 hours | ? |
| **Low** | Routine | Next business day | ? |

---

## Data Model Sketch

```typescript
interface EmergencyCase {
  id: string;
  bookingId: string;
  travelerId: string;

  // Classification
  category: EmergencyCategory;
  severity: SeverityLevel;
  status: CaseStatus;

  // Details
  description: string;
  location: Location;

  // Response
  assignedTo?: string;
  responseStartedAt?: Date;
  resolvedAt?: Date;

  // Actions
  actions: EmergencyAction[];

  // Costs
  costs: EmergencyCost[];
}

type EmergencyCategory =
  | 'medical'
  | 'lost_documents'
  | 'theft'
  | 'natural_disaster'
  | 'political'
  | 'terrorism'
  | 'other';

type SeverityLevel =
  | 'critical'
  | 'urgent'
  | 'high'
  | 'medium'
  | 'low';

type CaseStatus =
  | 'open'
  | 'assigned'
  | 'in_progress'
  | 'resolved'
  | 'closed';
```

---

## Open Problems

### 1. Liability
**Challenge:** Our liability for emergency situations

**Options:** Clear disclaimers, insurance requirements, waivers

### 2. Cost
**Challenge:** Emergency services are expensive

**Options:** Insurance mandates, clear pricing, payment options

### 3. 24/7 Coverage
**Challenge:** Providing round-the-clock support

**Options:** In-house, partners, time-zone distributed teams

### 4. Quality of Care
**Challenge:** Varying quality globally

**Options:** Partner networks, accreditations, reviews

---

## Next Steps

1. Define service scope
2. Identify partners
3. Build response protocols
4. Create training materials

---

**Status:** Research Phase — Service types unknown

**Last Updated:** 2026-04-27
