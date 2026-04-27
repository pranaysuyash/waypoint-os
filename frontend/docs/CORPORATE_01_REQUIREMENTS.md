# Corporate Travel 01: Requirements & Policies

> Understanding corporate travel needs and policy frameworks

---

## Document Overview

**Focus:** Corporate travel requirements and policy structures
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Corporate Needs
- What do companies need from travel management?
- What are the different user types? (Travelers, managers, admins?)
- How do requirements vary by company size?
- What about industry-specific needs?

### 2. Travel Policies
- What are typical travel policy components?
- How do policies vary by employee level?
- What about approval rules?
- How do we enforce policies?

### 3. User Types & Roles
- What are the different user roles?
- What permissions does each role have?
- How do we handle external travelers?
- What about travel management companies (TMCs)?

### 4. Company Types
- How do requirements vary by company size?
- What about startups vs. enterprises?
- What industry-specific requirements exist?
- How do MNCs differ from domestic companies?

---

## Research Areas

### A. Corporate Travel Needs

**Core Needs:**

| Need | Priority | Description | Research Needed |
|------|----------|-------------|-----------------|
| **Policy enforcement** | High | Ensure compliance with company rules | ? |
| **Approval workflows** | High | Multi-level approvals for bookings | ? |
| **Cost control** | High | Budget management, negotiated rates | ? |
| **Duty of care** | High | Track traveler location, safety | ? |
| **Reporting** | High | Spend analysis, traveler tracking | ? |
| **Ease of use** | Medium | Employee adoption | ? |
| **Integration** | Medium | ERP, expense systems | ? |

**By Company Size:**

| Size | Needs | Research Needed |
|------|-------|-----------------|
| **Startup (< 50)** | Simple, low cost, self-service | ? |
| **SMB (50-500)** | Policies, some approvals, reporting | ? |
| **Mid (500-2000)** | Full policies, multi-level approval, integration | ? |
| **Enterprise (2000+)** | Full TMS, global, negotiated rates, duty of care | ? |

### B. Travel Policy Components

**Standard Policy Elements:**

| Component | Description | Options | Research Needed |
|-----------|-------------|---------|-----------------|
| **Booking window** | How far in advance to book | X days before travel | ? |
| **Class of service** | Flight class allowed | Economy, business, first | Varies by level? |
| **Hotel category** | Star rating allowed | 3-star, 4-star, etc. | ? |
| **Daily allowances** | Per diem for meals, incidentals | Fixed amounts | ? |
| **Advance booking** | How early to book for best rates | 14, 21, 30 days? | ? |
| **Preferred suppliers** | Required vs. recommended | Airlines, hotels | ? |

**Approval Rules:**

| Rule | Trigger | Research Needed |
|------|---------|-----------------|
| **Manager approval** | All bookings or threshold? | ? |
| **Budget owner approval** | Exceeds budget | ? |
| **Senior management** | International or business class | ? |
| **Finance approval** | Above certain amount | ? |
| **Auto-approval** | Within policy, below threshold | ? |

**By Employee Level:**

| Level | Flight Class | Hotel Category | Other | Research Needed |
|-------|--------------|---------------|-------|-----------------|
| **Junior/Entry** | Economy | 3-star | Shared accommodation? | ? |
| **Mid-level** | Economy | 3-4 star | ? | ? |
| **Senior/Manager** | Business (long-haul) | 4-5 star | ? | ? |
| **Executive** | Business/First | 5-star | Airport transfers, lounge | ? |

### C. User Roles & Permissions

**Standard Roles:**

| Role | Description | Permissions | Research Needed |
|------|-------------|--------------|-----------------|
| **Traveler** | Books own travel | Book, view own trips, expenses | ? |
| **Manager** | Approves team travel | Approve, view team trips, reports | ? |
| **Travel Admin** | Manages travel program | Full access, policy setup | ? |
| **Finance** | Manages expenses | Access to all financial data | ? |
| **Executive** | Senior leadership | View all, override policy | ? |

**External Roles:**

| Role | Description | Permissions | Research Needed |
|------|-------------|--------------|-----------------|
| **Travel Agent** | TMC agent | Book on behalf, manage trips | ? |
| **Admin Assistant** | Books for executives | Book on behalf | ? |
| **Contractor/Consultant** | External traveler | Limited access | ? |

**Research:**
- What are the exact permission sets?
- How do we handle external users securely?
- What about SSO integration?

### D. Company Types & Industries

**By Company Type:**

| Type | Characteristics | Needs | Research Needed |
|------|----------------|-------|-----------------|
| **Startup** | Limited budget, flexible | Low cost, self-service | ? |
| **SME** | Growing, some structure | Policies, reporting | ? |
| **Enterprise** | Complex, global | Full TMS, duty of care | ? |
| **MNC** | Multi-country | Local policies, global oversight | ? |

**By Industry:**

| Industry | Special Needs | Research Needed |
|----------|--------------|-----------------|
| **IT/Services** | Frequent client visits | Flexible booking | ? |
| **Consulting** | Heavy travel, client billing | Detailed cost allocation | ? |
| **Manufacturing** | Factory visits, remote locations | Regional travel, safety | ? |
| **Finance** | Client meetings, roadshows | Premium travel, last-minute | ? |
| **Pharma** | Field reps, conferences | Compliance tracking | ? |
| **NGO** | Field work, limited budget | Budget control, safety | ? |

### E. Duty of Care

**Duty of Care Requirements:**

| Need | Description | Research Needed |
|------|-------------|-----------------|
| **Traveler tracking** | Know where employees are | Real-time? |
| **Emergency contact** | Contact travelers in crisis | Automated? |
| **Risk assessment** | Evaluate destination risks | Integration? |
| **Travel insurance** | Mandatory coverage | Group policies? |
| **Incident response** | Protocol for emergencies | ? |

**Risk Management:**

| Risk Type | Mitigation | Research Needed |
|-----------|------------|-----------------|
| **Health** | Travel health advisories | CDC integration? |
| **Security** | Political unrest, terrorism | Alert systems? |
| **Natural disaster** | Weather, earthquakes | Alerts? |
| **Location-based** | High-risk destinations | Restrictions? |

---

## Data Model Sketch

```typescript
// Research-level model - not final

interface Company {
  id: string;
  name: string;
  type: CompanyType;
  size: CompanySize;
  industry?: string;

  // Settings
  settings: CompanySettings;
  travelPolicy: TravelPolicy;

  // Integration
  integrations: CompanyIntegration[];

  // Commercial
  billingPlan: BillingPlan;
}

type CompanyType =
  | 'startup'
  | 'smb'
  | 'mid_market'
  | 'enterprise'
  | 'mnc';

type CompanySize =
  | '1_50' // 1-50 employees
  | '51_200'
  | '201_500'
  | '501_2000'
  | '2000_plus';

interface TravelPolicy {
  companyId: string;

  // General
  advanceBookingDays: number;
  canBookOutsidePolicy: boolean;
  requireApproval: boolean;

  // Flights
  flightClass: FlightClassPolicy;
  preferredAirlines?: string[];
  maxFlightCost?: Money;

  // Hotels
  hotelStarRating: HotelRatingPolicy;
  preferredHotels?: string[];
  maxHotelCost?: Money;

  // Other
  dailyAllowance: Money;
  carRentalPolicy: CarRentalPolicy;

  // Approvals
  approvalRules: ApprovalRule[];
}

interface FlightClassPolicy {
  byLevel: Map<EmployeeLevel, 'economy' | 'business' | 'first'>;
  exceptions: {
    longHaulHours?: number;
    allowedClass?: string;
  };
}

interface ApprovalRule {
  id: string;
  name: string;
  condition: ApprovalCondition;
  requiredApprover: ApproverType;
}

type ApprovalCondition =
  | { type: 'all_bookings' }
  | { type: 'amount_exceeds'; amount: Money }
  | { type: 'international' }
  | { type: 'business_class' }
  | { type: 'outside_policy' }
  | { type: 'specific_level'; levels: EmployeeLevel[] };

type ApproverType =
  | 'manager'
  | 'budget_owner'
  | 'finance'
  | 'travel_admin'
  | 'specific_user'; // userId

interface User {
  id: string;
  companyId: string;
  email: string;

  // Profile
  profile: UserProfile;

  // Roles
  roles: UserRole[];
  permissions: Permission[];

  // Employee details
  employeeLevel: EmployeeLevel;
  managerId?: string;
  department?: string;
  costCenter?: string;

  // Traveler preferences
  travelProfile?: TravelerProfile;
}

type UserRole =
  | 'traveler'
  | 'manager'
  | 'travel_admin'
  | 'finance'
  | 'executive'
  | 'travel_agent'
  | 'admin_assistant';

type EmployeeLevel =
  | 'entry'
  | 'junior'
  | 'mid'
  | 'senior'
  | 'manager'
  | 'director'
  | 'executive';
```

---

## Open Problems

### 1. Policy Complexity
**Challenge:** Policies are complex and vary widely

**Options:**
- Flexible policy engine
- Templates for common scenarios
- Policy builder UI
- Expert setup for enterprise

### 2. User Adoption
**Challenge:** Employees may bypass corporate tools

**Options:**
- User-friendly interface
- Incentives for compliance
- Mobile app
- Clear communication

### 3. Integration Complexity
**Challenge:** Companies use many different systems

**Options:**
- Common integrations (major ERPs)
- API for custom integrations
- Import/export capabilities
- Integration partners

### 4. Global Companies
**Challenge:** Different rules, currencies, languages

**Options:**
- Multi-language support
- Local policy support
- Currency conversion
- Regional compliance

---

## Competitor Research Needed

| Competitor | Approach | Notable Patterns |
|------------|----------|------------------|
| **Concur** | ? | ? |
| **Egencia** | ? | ? |
| **TravelPerk** | ? | ? |
| **Navan** | ? | ? |

---

## Experiments to Run

1. **Policy complexity study:** How complex are real policies?
2. **User interview:** What do corporate travelers want?
3. **Admin interview:** What do travel managers need?
4. **Integration study:** What systems do companies use?

---

## References

- [Trip Builder - Collaboration](./TRIP_BUILDER_04_COLLABORATION.md) — Similar multi-user patterns
- [Payment Processing](./PAYMENT_PROCESSING_MASTER_INDEX.md) — Corporate payments

---

## Next Steps

1. Interview travel managers
2. Analyze policy patterns
3. Design policy engine
4. Build role system
5. Create policy templates

---

**Status:** Research Phase — Requirements unknown

**Last Updated:** 2026-04-27
