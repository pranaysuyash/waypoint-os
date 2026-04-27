# Group Travel 01: Definition & Types

> Understanding group travel categories and requirements

---

## Document Overview

**Focus:** Group travel types and definitions
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Group Types
- What qualifies as group travel?
- What are the different group categories?
- How do requirements vary by type?
- What about MICE vs. leisure groups?

### Group Size Categories
- What are the size thresholds?
- How do requirements change with size?
- What about small groups (10-20)?
- What about large groups (100+)?

### Group Use Cases
- Corporate events and conferences
- Weddings and celebrations
- School and educational groups
- Religious pilgrimages
- Sports teams
- Incentive travel

### Requirements by Type
- What are MICE requirements?
- What do wedding groups need?
- What about school groups?
- What are pilgrimage group needs?

---

## Research Areas

### A. Group Size Definitions

| Size | Category | Special Requirements | Research Needed |
|------|----------|---------------------|-----------------|
| **10-20** | Small group | Minimal | ? |
| **20-50** | Medium group | Some coordination | ? |
| **50-100** | Large group | Dedicated coordination | ? |
| **100+** | Very large | Full group services | ? |

### B. Group Types by Purpose

**MICE (Meetings, Incentives, Conferences, Exhibitions):**

| Type | Description | Needs | Research Needed |
|------|-------------|-------|-----------------|
| **Meetings** | Corporate meetings | Function spaces, AV | ? |
| **Incentives** | Reward travel | Premium experiences | ? |
| **Conferences** | Large gatherings | Venues, catering | ? |
| **Exhibitions** | Trade shows | Booth spaces, logistics | ? |

**Leisure Groups:**

| Type | Description | Needs | Research Needed |
|------|-------------|-------|-----------------|
| **Weddings** | Destination weddings | Coordination, events | ? |
| **Family reunions** | Multi-family | Activities, space | ? |
| **Pilgrimage** | Religious travel | Group coordination | ? |
| **School trips** | Educational | Safety, educational content | ? |
| **Sports** | Tournaments, events | Proximity to venues | ? |
| **Special interest** | Hobby groups | Specific activities | ? |

### C. Group Requirements

**Common Requirements:**

| Requirement | Description | Research Needed |
|-------------|-------------|-----------------|
| **Group pricing** | Discounted rates | Minimum numbers? |
| **Rooming list** | Guest room assignments | Due when? |
| **Contract** | Group agreement | Terms? |
| **Deposit** | Secures space | % of total? |
| **Payment schedule** | Milestone payments | What schedule? |
| **Cancellation policy** | Group terms | Different from individual? |
| **F&B minimum** | Food & beverage spend | Common for MICE? |

**By Supplier Type:**

| Supplier | Group Requirements | Research Needed |
|----------|-------------------|-----------------|
| **Hotels** | Room block, contract, deposit | ? |
| **Airlines** | Group desk, contracts | Minimum seats? |
| **Activities** | Group rates, timing | ? |
| **Transport** | Group vehicles | ? |

### D. Group Booking Process

**Standard Process:**

```
1. Inquiry → Lead details, requirements
2. Quote → Prepare group quote
3. Contract → Sign agreement, deposit
4. Rooming list → Collect guest details
5. Final payment → Balance before travel
6. Manifest → Final guest list
7. Travel → Group travels
8. Post-travel → Feedback, settlement
```

---

## Data Model Sketch

```typescript
interface GroupBooking {
  id: string;
  companyId: string;
  groupType: GroupType;
  groupSize: number;

  // Organizer
  organizer: Contact;
  billing: Contact;

  // Trip details
  destination: string;
  dates: DateRange;

  // Requirements
  requirements: GroupRequirements;

  // Contract
  contractStatus: ContractStatus;
  depositPaid: boolean;
  balancePaid: boolean;

  // Guests
  roomingList?: RoomingList;
  manifest?: GuestManifest;
}

type GroupType =
  | 'corporate_mice'
  | 'wedding'
  | 'family_reunion'
  | 'pilgrimage'
  | 'school'
  | 'sports'
  | 'special_interest';
```

---

## Open Problems

### 1. Definition Ambiguity
**Challenge:** What counts as a "group"?

**Options:** Clear size thresholds, supplier-specific definitions

### 2. Rooming List Complexity
**Challenge:** Managing room assignments for large groups

**Options:** Rooming list tools, guest portal

### 3. Payment Coordination
**Challenge:** Collecting from group members

**Options:** Individual payments, organizer pays, hybrid

### 4. Changes at Scale
**Challenge:** Handling changes for 100+ people

**Options:** Clear change policies, deadlines, fees

---

## Next Steps

1. Define group categories
2. Design quoting process
3. Build rooming list tools
4. Create contract templates

---

**Status:** Research Phase — Group types unknown

**Last Updated:** 2026-04-27
