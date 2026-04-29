# Agent Performance & Workforce Management — Scheduling System

> Research document for agent shift management, coverage planning, workload balancing, skill-based routing, overtime tracking, holiday staffing, and India labor law compliance.

---

## Key Questions

1. **How do we design a shift management system that covers 7 AM - 11 PM customer inquiry windows across Indian time zones?**
2. **What workload balancing algorithms ensure fair trip distribution without sacrificing customer experience?**
3. **How do we implement skill-based routing (destination expertise, language, trip type) for optimal agent-customer matching?**
4. **How do we track overtime, manage leave, and handle holiday-season staffing surges?**
5. **What India labor law compliance requirements affect scheduling (Shops & Establishments Act, working hours, rest periods)?**

---

## Research Areas

### Shift Management

```typescript
interface ShiftManagementSystem {
  agencyId: string;
  branches: BranchSchedule[];
  shiftTemplates: ShiftTemplate[];
  rotations: ShiftRotation[];
  overrideRules: OverrideRule[];
}

interface BranchSchedule {
  branchId: string;
  location: string;                   // "Delhi - Connaught Place"
  timezone: string;                   // "Asia/Kolkata" (IST for all India)
  operatingHours: {
    weekdays: TimeWindow;             // Typically 9:00 AM - 8:00 PM
    saturdays: TimeWindow;            // Typically 9:00 AM - 5:00 PM
    sundays: TimeWindow;              // Typically closed or 10:00 AM - 2:00 PM
  };
  customerInquiryWindow: TimeWindow;  // 7:00 AM - 11:00 PM (WhatsApp/email)
}

interface TimeWindow {
  start: string;                      // "07:00"
  end: string;                        // "23:00"
}

interface ShiftTemplate {
  id: string;
  name: string;                       // "Morning Shift", "Evening Shift"
  startTime: string;                  // "07:00"
  endTime: string;                    // "15:00"
  duration: number;                   // Hours (8)
  breakDuration: number;              // Minutes (60, including 30-min lunch)
  breakWindow: TimeWindow;            // Break must fall within this window
  applicableDays: number[];           // [1,2,3,4,5] = Mon-Fri
  staffingLevel: number;              // Minimum agents required
  premiumMultiplier: number;          // 1.0x for regular, 1.25x for early/late
}

// Shift templates for Indian travel agency:
//
// SHIFT A: "Early Bird" (7:00 AM - 3:00 PM)
// - Covers morning inquiry spike (9-11 AM)
// - 30-min break between 11:30 AM - 1:00 PM
// - Staffing: 3-4 agents (covers walk-ins + WhatsApp)
//
// SHIFT B: "Core Day" (9:00 AM - 6:00 PM)
// - Primary shift, most walk-in customers
// - 60-min break (12:00 - 2:00 PM rotating)
// - Staffing: 5-8 agents (heaviest shift)
//
// SHIFT C: "Extended" (11:00 AM - 8:00 PM)
// - Covers afternoon spike + evening inquiries
// - 30-min break between 2:00 - 4:00 PM
// - Staffing: 3-5 agents
//
// SHIFT D: "Evening Support" (2:00 PM - 11:00 PM)
// - Remote shift, handles WhatsApp/email after office hours
// - Staffing: 2-3 agents (work from home acceptable)
// - Premium: 1.25x (late hours)
//
// SHIFT E: "Weekend Cover" (10:00 AM - 6:00 PM)
// - Saturday + Sunday
// - Rotational (each agent does 1 weekend per month)
// - Staffing: 3-4 agents
// - Premium: 1.5x (Sunday), 1.25x (Saturday)

interface ShiftRotation {
  id: string;
  name: string;                       // "Monthly Rotation", "Weekly Rotation"
  cycle: 'weekly' | 'biweekly' | 'monthly';
  rules: RotationRule[];
}

interface RotationRule {
  agentGroup: string;                 // "Senior Agents", "Weekend Pool"
  shiftSequence: string[];            // ["A", "B", "C"] rotate through
  fixedDays: string[];                // Days that don't rotate
  blackoutDays: string[];             // Days agent cannot be assigned
}

// Rotation example:
// Agent "Vikram" in weekly rotation:
// Week 1: Shift A (Mon-Fri)
// Week 2: Shift B (Mon-Fri)
// Week 3: Shift C (Mon-Fri)
// Week 4: Shift A (Mon-Fri) + Weekend Cover (Sat-Sun)
// Repeat
//
// Seniority preference:
// Senior agents get first pick of preferred shift
// Junior agents fill remaining slots
// All agents must do at least 1 evening/weekend per month

interface OverrideRule {
  condition: string;                  // "Agent on leave", "Spike in inquiries"
  action: 'swap_shift' | 'extend_shift' | 'call_backup' | 'redistribute';
  approvalRequired: 'auto' | 'manager' | 'hr';
}
```

### Coverage Planning

```typescript
interface CoveragePlan {
  branchId: string;
  weekStartDate: Date;
  dailyCoverage: DailyCoverage[];
  gaps: CoverageGap[];
  recommendations: CoverageRecommendation[];
}

interface DailyCoverage {
  date: Date;
  shifts: ShiftAssignment[];
  totalAgents: number;
  requiredAgents: number;
  surplus: number;                    // Positive = overstaffed, Negative = understaffed
}

interface ShiftAssignment {
  shiftId: string;
  templateId: string;
  assignedAgents: AgentShiftAssignment[];
  coverageMetrics: {
    destinationExpertise: string[];   // Destinations covered this shift
    languages: string[];              // Languages available this shift
    tripTypes: string[];              // Trip types handled this shift
    seniorOnDuty: boolean;            // At least one senior agent present
  };
}

interface AgentShiftAssignment {
  agentId: string;
  role: AgentRole;
  skills: AgentSkill[];
  location: 'office' | 'remote';
  swapAvailable: boolean;             // Agent willing to swap
}

interface CoverageGap {
  date: Date;
  shift: string;
  type: 'understaffed' | 'skill_missing' | 'language_missing' | 'no_senior';
  severity: 'low' | 'medium' | 'high';
  affectedCustomers: number;          // Estimated
  suggestion: string;                 // "Offer ₹500 overtime bonus to Arjun"
}

// Coverage planning scenarios:
//
// SCENARIO: "Kerala Peak Season (December)"
// Required: 2 agents with Kerala expertise per shift
// Problem: Only 3 agents certified for Kerala, 1 on leave
// Solution: Prioritize Shift B (peak hours), accept lower coverage in Shift A/D
//
// SCENARIO: "Monday Morning Spike"
// Pattern: 30% more inquiries Monday 9-11 AM (weekend queries pile up)
// Solution: Overstaff Monday Shift A by 1-2 agents
// Auto-detect from historical data and suggest adjustment
//
// SCENARIO: "Agent sick leave (same day)"
// Trigger: Agent calls in sick at 8:30 AM for 9:00 AM shift
// Response: Notify manager → check backup pool → offer overtime → redistribute trips
// Time target: Coverage restored within 30 minutes

interface CoverageRecommendation {
  type: 'hire_temp' | 'overtime' | 'shift_swap' | 'cross_train' | 'outsource';
  description: string;
  cost: number;                       // INR
  impact: string;                     // "Resolves 80% of evening coverage gaps"
  priority: number;                   // 1 (highest) - 5 (lowest)
}
```

### Workload Balancing

```typescript
interface WorkloadBalancer {
  strategy: BalancingStrategy;
  weights: WorkloadWeights;
  constraints: BalancingConstraints;
}

interface BalancingStrategy {
  algorithm: 'round_robin' | 'weighted_random' | 'skill_match' | 'availability_first' | 'hybrid';
  parameters: Record<string, number>;
}

// Algorithm comparison:
//
// ROUND ROBIN:
// Pros: Simple, fair distribution
// Cons: Ignores skill, current workload, customer relationship
// Best for: Initial assignment when all leads are equal
//
// WEIGHTED RANDOM:
// Pros: Statistical fairness, configurable
// Cons: Can have clusters, not deterministic
// Best for: Distributing similar inbound leads
//
// SKILL MATCH (recommended primary):
// Pros: Best customer experience, higher conversion
// Cons: Specialists get overloaded, skill gaps create bottlenecks
// Best for: Qualified leads with known destination/type
//
// AVAILABILITY FIRST:
// Pros: Always assigns to available agent
// Cons: Ignores fit, creates imbalances for busy agents
// Best for: Urgent requests, walk-in customers
//
// HYBRID (recommended):
// 1. Filter by availability (must be on shift)
// 2. Filter by skill (destination, language, trip type)
// 3. Among eligible, pick agent with lowest current workload
// 4. If tie, prefer agent with existing customer relationship
// 5. If no relationship, use weighted random among eligible

interface WorkloadWeights {
  skillMatch: number;                 // 0-1, default: 0.35
  currentLoad: number;                // 0-1, default: 0.25
  customerRelationship: number;       // 0-1, default: 0.20
  conversionProbability: number;      // 0-1, default: 0.10
  fairnessScore: number;              // 0-1, default: 0.10
}

interface WorkloadMetrics {
  agentId: string;
  activeTrips: number;                // Trips currently being handled
  pendingQuotes: number;              // Quotes awaiting preparation
  unreadMessages: number;             // Unread customer messages
  tasksDueToday: number;              // Tasks with today's deadline
  upcomingDepartures: number;         // Trips departing within 7 days
  estimatedCapacity: number;          // % of capacity used (0-100)
}

// Workload capacity model:
// Agent capacity = base_capacity × experience_modifier × time_of_day_modifier
//
// Base capacity: 12-15 active trips (senior), 6-8 (junior)
// Experience modifier: L1=0.6, L2=0.8, L3=1.0, L4=1.2, L5=1.3
// Time modifier: Morning=1.0, Afternoon=0.9, Evening=0.8 (fatigue)
//
// Overload threshold:
// 85% = Yellow (no new leads assigned unless skill-critical)
// 95% = Red (no new leads, manager alerted)
// 100% = Hard cap (system blocks new assignment)

interface BalancingConstraints {
  maxActiveTrips: Record<AgentLevel, number>;
  maxPendingQuotes: number;
  maxUnreadMessages: number;
  minBreakBetweenTrips: number;       // Minutes
  maxConsecutiveHours: number;        // Before mandatory break (6 hours)
  preferExistingRelationship: boolean;
}
```

### Skill-Based Routing

```typescript
interface SkillBasedRouter {
  agentSkills: AgentSkillProfile[];
  routingRules: RoutingRule[];
  customerMatching: CustomerMatchStrategy;
}

interface AgentSkillProfile {
  agentId: string;
  destinations: DestinationExpertise[];
  languages: LanguageSkill[];
  tripTypes: TripTypeExpertise[];
  certifications: Certification[];
  customerSegments: CustomerSegment[];
}

interface DestinationExpertise {
  destination: string;                // "Kerala", "Thailand", "Europe"
  level: 'basic' | 'intermediate' | 'expert';
  tripsBooked: number;                // Total bookings to this destination
  lastBookingDate: Date;
  familiarityScore: number;           // 0-100, based on bookings + training
  personalVisit: boolean;             // Agent has visited personally
}

// Destination expertise levels:
// BASIC: Can handle standard packages, needs supplier support for custom
// INTERMEDIATE: Can customize itineraries, knows 3+ hotels, 5+ activities
// EXPERT: Can create unique experiences, has personal contacts, visited 2+ times
//
// India-specific destination clusters:
// Domestic: Kerala, Goa, Rajasthan, Himachal, North-East, J&K, Gujarat
// South-East Asia: Thailand, Bali, Singapore, Malaysia, Vietnam
// Middle East: Dubai, Abu Dhabi, Oman, Turkey
// Europe: France, Italy, Switzerland, UK, Greece
// Far East: Japan, South Korea
// Exotics: Maldives, Mauritius, Seychelles
// Pilgrimage: Char Dham, Vaishno Devi, Amarnath, Varanasi, Tirupati

interface LanguageSkill {
  language: string;                   // "Hindi", "English", "Tamil"
  proficiency: 'basic' | 'conversational' | 'fluent' | 'native';
  written: boolean;                   // Can communicate in writing
  spoken: boolean;                    // Can handle phone calls
}

// Language routing priority:
// 1. Match customer's preferred language (if known)
// 2. English + customer's regional language
// 3. English only (fallback)
//
// Common Indian language requirements:
// Hindi (mandatory for North India agencies)
// English (mandatory for international bookings)
// Regional: Tamil, Telugu, Kannada, Malayalam (South)
//          Marathi (Maharashtra), Gujarati (Gujarat), Bengali (East)
//          Punjabi (Punjab/Delhi)
// Foreign: Arabic (Middle East packages), French (Europe packages)

interface TripTypeExpertise {
  type: TripType;
  level: 'basic' | 'intermediate' | 'expert';
  bookingsCompleted: number;
}

type TripType =
  | 'honeymoon'
  | 'family_vacation'
  | 'adventure'
  | 'pilgrimage'
  | 'corporate_mice'
  | 'group_tour'
  | 'luxury'
  | 'budget_backpacking'
  | 'destination_wedding'
  | 'educational_tour'
  | 'senior_citizen'
  | 'solo_travel'
  | 'medical_tourism';

interface RoutingRule {
  id: string;
  name: string;                       // "Kerala Honeymoon → Expert"
  condition: RoutingCondition;
  action: RoutingAction;
  priority: number;                   // Higher = evaluated first
}

interface RoutingCondition {
  destination?: string;
  tripType?: TripType;
  customerTier?: 'standard' | 'premium' | 'vip';
  language?: string;
  tripValue?: { min?: number; max?: number };
  urgency?: 'normal' | 'high' | 'critical';
}

interface RoutingAction {
  assignTo?: string;                  // Specific agent ID
  skillRequired?: string;             // "expert" destination knowledge
  escalationTimeout?: number;         // Minutes before auto-escalation
  fallbackAction: RoutingAction;
}

// Routing scenarios:
//
// "Kerala Honeymoon, ₹2L+, Hindi-speaking customer"
// → Match: Kerala expert + honeymoon specialist + Hindi speaker
// → If no exact match: Kerala expert + Hindi speaker (drop honeymoon)
// → If still no match: Hindi speaker + any honeymoon specialist
// → Fallback: Least busy agent + flag for Kerala training needed
//
// "Corporate MICE, 50 pax, Mumbai"
// → Match: MICE specialist + corporate experience
// → Must be senior agent (L4+) for groups >30 pax
// → Language not critical (corporate = English)
//
// "Emergency: Customer stranded at Bangkok airport"
// → Route to: Most experienced agent available NOW (any shift)
// → Override workload limits
// → Notify team lead
```

### Leave Management

```typescript
interface LeaveManagementSystem {
  leaveTypes: LeaveType[];
  leaveBalances: Record<string, LeaveBalance>; // agentId → balance
  requests: LeaveRequest[];
  calendar: LeaveCalendar;
}

interface LeaveType {
  id: string;
  name: string;
  code: string;                       // "CL", "SL", "EL", "ML", "PL"
  annualEntitlement: number;          // Days per year
  carryForward: number;               // Max days carried to next year
  encashable: boolean;                // Can be converted to cash
  paid: boolean;
  documentation: string;              // Required docs (medical cert, etc.)
  notice: number;                     // Days advance notice required
}

// Leave types for Indian travel agency:
// Casual Leave (CL): 12 days/year, 0 carry forward, not encashable
// Sick Leave (SL): 12 days/year, 0 carry forward, medical cert for >2 days
// Earned Leave (EL): 15 days/year, 10 carry forward, encashable at exit
// Maternity Leave (ML): 26 weeks (per Maternity Benefit Act, 2017)
// Paternity Leave (PL): 15 days (company policy)
// Compensatory Off: 1 day per weekend/holiday worked, use within 30 days
// Bereavement Leave: 3-5 days (company policy)
// Marriage Leave: 3-5 days (company policy, once during tenure)

interface LeaveBalance {
  agentId: string;
  year: number;
  balances: Record<string, {
    entitled: number;
    used: number;
    planned: number;                  // Approved but not yet taken
    available: number;                // entitled - used - planned
    carriedForward: number;
  }>;
}

interface LeaveRequest {
  id: string;
  agentId: string;
  leaveType: string;
  startDate: Date;
  endDate: Date;
  totalDays: number;
  reason: string;
  status: 'draft' | 'submitted' | 'manager_approved' | 'hr_approved' | 'rejected' | 'cancelled';
  approvalChain: LeaveApproval[];
  coveragePlan: string;               // How workload is handled during absence
  urgentContact: string;              // Phone number during leave
}

// Leave approval workflow:
// 1. Agent submits request (minimum notice: 3 days for CL, 1 day for SL)
// 2. System checks:
//    - Leave balance available
//    - No blackout period (peak season: Oct-Mar blocks 2+ day leaves)
//    - Coverage available (at least minimum staffing)
// 3. Manager reviews:
//    - Approve / Reject / Suggest alternate dates
//    - Consider team impact
// 4. HR approves (for >5 days or ML/PL)
// 5. System triggers:
//    - Reassign active trips to backup agent
//    - Update routing rules (remove from assignment pool)
//    - Notify team and customers (if needed)
//    - Set up email/WhatsApp auto-responder
//
// Blackout periods:
// Peak season: Oct 1 - Dec 31 (limited leaves, max 2 consecutive days)
// Summer rush: Apr 1 - Jun 30 (moderate restriction)
// Festival period: Diwali week, Dussehra week (no leaves for senior agents)

interface LeaveCalendar {
  branchId: string;
  month: Date;
  agentLeaves: Record<string, Date[]>; // agentId → dates on leave
  holidays: PublicHoliday[];
  staffingLevels: DailyStaffingLevel[];
}

interface PublicHoliday {
  date: Date;
  name: string;                       // "Republic Day", "Diwali"
  type: 'national' | 'state' | 'local' | 'restricted';
  mandatory: boolean;                 // Agency must close (national holidays)
}

// Indian public holidays (national, mandatory):
// Jan 26: Republic Day
// Aug 15: Independence Day
// Oct 2: Gandhi Jayanti
//
// Major festivals (agency typically closed):
// Diwali (2-3 days, varies)
// Dussehra (1-2 days)
// Holi (1 day)
// Eid ul-Fitr (1 day)
// Christmas (1 day)
//
// Restricted holidays (agent can choose 2-3 from list):
// Makar Sankranti, Pongal, Guru Nanak Jayanti, Mahavir Jayanti,
// Buddha Purnima, Janmashtami, Maha Shivaratri, Raksha Bandhan, etc.
//
// State-specific holidays (depend on branch location):
// Maharashtra Day (May 1, Mumbai/Pune)
// Karnataka Rajyotsava (Nov 1, Bangalore)
// Kerala Piravi (Nov 1, Kochi)
```

### Overtime & Holiday Season Staffing

```typescript
interface OvertimeTracker {
  agentId: string;
  period: MetricPeriod;
  overtimeEntries: OvertimeEntry[];
  compensatoryOffs: CompOffEntry[];
  compliance: OvertimeCompliance;
}

interface OvertimeEntry {
  id: string;
  date: Date;
  startTime: string;                  // "18:00"
  endTime: string;                    // "21:30"
  duration: number;                   // Minutes
  reason: string;                     // "Customer inquiry surge", "Trip deadline"
  type: 'pre_approved' | 'retro_approved' | 'unapproved';
  compensation: 'pay' | 'comp_off';
  rate: number;                       // 1.5x regular rate (statutory minimum)
  approvedBy?: string;
}

// Overtime rules (India - Shops & Establishments Act):
// Maximum overtime: 50 hours per quarter (varies by state)
// Overtime rate: 2x regular wage (most states)
// Mandatory rest: 30 minutes break for every 5 hours worked
// Weekly rest: 1 full day off per week (cannot accumulate)
// Daily limit: 9 hours normal + 1-2 hours overtime (state-dependent)
//
// Compensatory off rules:
// Sunday work: 1 comp off within 3 days before or after
// Public holiday work: 1 comp off within 30 days OR double pay
// Agent chooses: comp off or pay (must declare before working)

interface CompOffEntry {
  id: string;
  earnedDate: Date;
  reason: string;                     // "Worked Sunday Oct 12"
  expiryDate: Date;                   // 30 days from earned date
  status: 'available' | 'planned' | 'used' | 'expired';
  usedDate?: Date;
}

// Holiday season staffing surge:
//
// Peak demand periods:
// 1. October-December: International bookings (Europe, Middle East)
//    - Staffing need: +30-40% above normal
//    - Duration: 12 weeks
//    - Strategy: Temp hires + overtime + shift extensions
//
// 2. April-June: Domestic summer vacation
//    - Staffing need: +20-30% above normal
//    - Duration: 12 weeks
//    - Strategy: Interns + part-time + extended hours
//
// 3. Wedding season (Nov-Feb): Destination weddings
//    - Staffing need: +2-3 specialist agents
//    - Strategy: Cross-train existing agents + freelance specialists
//
// Surge staffing strategies:
// a) Temporary hires: 3-6 month contracts for peak season
// b) Part-time agents: 4-hour shifts during peak hours
// c) Freelance agents: Commission-only for overflow leads
// d) Cross-training: Off-season training so more agents can handle peak destinations
// e) Remote agents: Work-from-home for evening/weekend coverage
// f) Agency partnerships: Overflow to partner agencies (revenue share)

interface SurgeStaffingPlan {
  season: string;                     // "International Peak 2026"
  startDate: Date;
  endDate: Date;
  currentAgents: number;
  targetAgents: number;
  tempHires: number;
  overtimeBudget: number;             // INR
  freelancers: number;
  trainingSchedule: {
    destination: string;
    agents: string[];
    completionDeadline: Date;
  }[];
}
```

### India Labor Law Compliance

```typescript
interface LaborLawCompliance {
  centralActs: CentralLaborAct[];
  stateActs: StateLaborAct[];
  complianceCalendar: ComplianceDeadline[];
  inspections: InspectionRecord[];
}

// Central labor acts applicable to travel agencies:
interface CentralLaborAct {
  act: string;
  applicability: string;
  keyRequirements: string[];
  penalties: string;
}

// 1. Shops & Establishments Act (state-level, but pattern is central)
// Applicability: All commercial establishments with 10+ employees
// Requirements:
//   - Register establishment within 30 days of commencement
//   - Display registration certificate prominently
//   - Working hours: Max 9 hours/day, 48 hours/week
//   - Mandatory 1-day weekly rest
//   - Overtime: Max 1 hour/day at 2x rate
//   - Leave: As per state rules (CL, SL, EL)
//   - Opening/closing times: As per local rules
//   - Record keeping: Attendance, wages, leave records
// Penalties: ₹1,000 - ₹5,000 per violation
//
// 2. Payment of Wages Act, 1936
// Requirements:
//   - Pay wages before 7th of following month (<1,000 employees)
//   - Pay wages before 10th of following month (1,000+ employees)
//   - Authorized deductions only (PF, ESI, PT, TDS, advance)
//   - Total deductions ≤ 50% of wages (75% if cooperative society dues)
//   - Issue wage slip with every payment
//
// 3. Minimum Wages Act, 1948
// Requirements:
//   - Pay at least state-notified minimum wage
//   - Travel agent classification: "Commercial establishment" (most states)
//   - Delhi minimum wage (2026): ₹18,066/month (unskilled), ₹19,929 (semi-skilled)
//   - Mumbai minimum wage: Similar range
//   - Must revise when state revises (typically every 6 months)
//
// 4. Employees' Provident Fund (EPF) Act, 1952
// Applicability: 20+ employees
// Requirements:
//   - Register with EPFO, get establishment code
//   - Deduct 12% of basic + DA from employee
//   - Contribute 12% of basic + DA as employer
//   - Deposit by 15th of following month
//   - File monthly return (ECR) on EPFO portal
//   - File annual return
//   - EDLI (Employee Deposit Linked Insurance): 0.5% employer
//   - EPF admin charges: 0.5% employer
//   Total employer cost: ~13.61% of basic + DA
//
// 5. Employees' State Insurance (ESI) Act, 1948
// Applicability: 10+ employees, gross salary ≤ ₹21,000/month
// Requirements:
//   - Register with ESIC within 15 days of applicability
//   - Employee contribution: 0.75% of gross salary
//   - Employer contribution: 3.25% of gross salary
//   - Deposit by 15th of following month
//   - File half-yearly return
//   - Issue e-Pehchan card to employees
//
// 6. Payment of Gratuity Act, 1972
// Applicability: 10+ employees
// Requirements:
//   - Gratuity after 5 years continuous service
//   - Calculation: (15 × last drawn salary × years of service) / 26
//   - Maximum: ₹20 lakh (2026, government ceiling)
//   - Forfeiture: Only for riotous/violent behavior or moral turpitude
//   - Employer must insure or self-insure
//
// 7. Maternity Benefit Act, 2017
// Requirements:
//   - 26 weeks paid leave (first 2 children), 12 weeks (subsequent)
//   - 6 weeks post-natal mandatory
//   - Creche facility: 50+ employees
//   - Work from home: Option for 4 months after delivery (if nature of work allows)
//   - No discharge during maternity leave
//
// 8. Sexual Harassment of Women at Workplace (POSH) Act, 2013
// Requirements:
//   - Internal Complaints Committee (ICC) if 10+ employees
//   - ICC must have at least 50% women members
//   - External member (NGO/legal background) mandatory
//   - Annual report to district officer
//   - Display POSH policy prominently

interface ComplianceDeadline {
  deadline: Date;
  complianceType: string;             // "PF monthly deposit", "ESI return"
  frequency: 'monthly' | 'quarterly' | 'half_yearly' | 'annual';
  authority: string;                  // "EPFO", "ESIC", "Labour Department"
  penalty: string;                    // Fine or imprisonment details
  status: 'pending' | 'completed' | 'overdue';
}
```

---

## Open Problems

1. **Dynamic workload balancing** — Customer inquiries are bursty (10 WhatsApp messages in 5 minutes, then silence for an hour). Static workload caps don't handle bursts well. Need a dynamic capacity model that accounts for conversation complexity, not just trip count.

2. **Skill-based routing cold start** — New agents have no skill history. They either get assigned randomly (poor customer experience) or only get low-value leads (slow skill development). Need a bootstrapping strategy that balances learning with customer satisfaction.

3. **Cross-timezone scheduling for NRI customers** — Indian agencies serve NRIs in US, UK, and Gulf time zones. Evening shifts (2 PM - 11 PM IST) cover Europe and Gulf, but US customers need 9 PM - 6 AM IST coverage. Remote/night shift agents or partnership with US-based agents may be needed.

4. **Predictive staffing** — Weather events, festival dates, and marketing campaigns create demand spikes. Building a demand forecasting model that predicts staffing needs 2-4 weeks ahead would dramatically improve coverage planning.

5. **Shift-swapping fairness** — Informal shift swaps are common ("I'll cover your Saturday if you cover my Tuesday"), but untracked swaps create accountability gaps. A formal swap system needs to be easy enough that agents actually use it.

6. **State-by-state compliance** — India has 28 states with different Shops & Establishment rules, professional tax rates, and holiday lists. A multi-branch agency needs a compliance engine that knows every state's requirements.

---

## Next Steps

- [ ] Design shift management data model with templates and rotations
- [ ] Build skill-based routing algorithm with hybrid matching strategy
- [ ] Model workload capacity by agent level with fatigue adjustment
- [ ] Create leave management system with blackout period support
- [ ] Map labor law compliance requirements for top 5 Indian states
- [ ] Design holiday season surge staffing playbook
- [ ] Study workforce management tools (Kronos, Deputy, Zoho People, Darwinbox)
- [ ] Integrate with WORKFORCE_01_PERFORMANCE for skill-linked performance tracking
