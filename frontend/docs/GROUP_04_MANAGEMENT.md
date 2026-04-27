# Group Travel 04: Management

> Room lists, manifests, and guest coordination

---

## Document Overview

**Focus:** Managing group bookings before travel
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Room List Management
- How do we manage room assignments?
- What about roommate matching?
- How do we handle special requests?
- What about accessibility needs?

### Manifest Management
- What information goes on manifests?
- When are they due?
- How do we share with suppliers?
- What about security requirements?

### Guest Communication
- What updates do guests need?
- How do we share documents?
- What about emergency contacts?
- How do we handle questions?

### Coordination
- How do we coordinate with suppliers?
- What about on-ground coordination?
- What about group activities?
- How do we handle issues?

---

## Research Areas

### A. Room Management

**Room Types:**

| Type | Occupancy | Research Needed |
|------|-----------|-----------------|
| **Single** | 1 person | ? |
| **Double** | 2 people, 1 bed | ? |
| **Twin** | 2 people, 2 beds | ? |
| **Triple** | 3 people | ? |
| **Quad** | 4 people | ? |

**Assignment Logic:**

| Scenario | Approach | Research Needed |
|----------|----------|-----------------|
| **Couples** | Double rooms | ? |
| **Families** | Connecting rooms | ? |
| **Singles** | Single or share | ? |
| **Odd numbers** | Triple or pay single supplement | ? |

### B. Manifest Requirements

**Standard Manifest Data:**

| Data Point | Purpose | Research Needed |
|------------|---------|-----------------|
| **Full name** | Identification | As per ID? |
| **Date of birth** | Age verification | ? |
| **Nationality** | Visa requirements | ? |
| **Passport number** | International travel | ? |
| **Dietary restrictions** | Meals | ? |
| **Special needs** | Accessibility | ? |

**By Supplier:**

| Supplier | Manifest Requirements | Research Needed |
|----------|----------------------|-----------------|
| **Airlines** | Passport, visa, weight | ? |
| **Hotels** | Names, check-in times | ? |
| **Activities** | Counts, ages, restrictions | ? |
| **Transport** | Luggage, special needs | ? |

### C. Communication Plan

**Pre-Trip Timeline:**

| Timing | Communication | Research Needed |
|--------|---------------|-----------------|
| **Booking confirmed** | Confirmation email | ? |
| **60 days before** | Rooming list reminder | ? |
| **30 days before** | Payment reminder | ? |
| **14 days before** | Trip details, packing list | ? |
| **7 days before** | Final updates, emergency info | ? |
| **Day of travel** | Departure information | ? |

### D. On-Ground Coordination

**Services:**

| Service | Description | Research Needed |
|----------|-------------|-----------------|
| **Airport greeter** | Meet on arrival | ? |
| **Group coordinator** | On-ground support | ? |
| **Local guide** | Destination expertise | ? |
| **24/7 support** | Emergency assistance | ? |

---

## Data Model Sketch

```typescript
interface RoomList {
  bookingId: string;
  rooms: RoomAssignment[];
  specialRequests: SpecialRequest[];
}

interface RoomAssignment {
  roomId: string;
  guests: string[]; // Guest IDs
  roomType: string;
  specialRequests?: string[];
}

interface GuestManifest {
  bookingId: string;
  supplierId: string;
  guests: ManifestEntry[];
  generatedAt: Date;
}

interface ManifestEntry {
  guestId: string;
  name: string;
  dateOfBirth?: Date;
  nationality?: string;
  passportNumber?: string;
  dietaryRequirements?: string;
  specialRequirements?: string;
}
```

---

## Open Problems

### 1. Roommate Conflicts
**Challenge:** Guests don't get along

**Options:** Roommate selection, random assignment, changes

### 2. Special Requirements
**Challenge:** Many unique requests

**Options:** Clear policies, additional fees, feasibility check

### 3. Timing Pressure
**Challenge:** Details close to travel

**Options:** Strict deadlines, late fees, flexibility

### 4. Supplier Coordination
**Challenge:** Multiple suppliers need data

**Options:** Standardized formats, automated sharing, confirmations

---

## Next Steps

1. Build room assignment tools
2. Create manifest generator
3. Design communication templates
4. Implement supplier sharing

---

**Status:** Research Phase — Management patterns unknown

**Last Updated:** 2026-04-27
