# MICE Planning — Event Planning Workflows

> Research document for event planning workflows, timeline management, and logistics coordination.

---

## Key Questions

1. **What's the typical planning timeline for different MICE event types?**
2. **How do we manage the dependencies between venue, catering, AV, decor, and transport?**
3. **What collaboration model works for multi-stakeholder event planning (client, agency, vendors)?**
4. **How do we handle scope changes mid-planning without derailing timelines?**
5. **What's the right level of automation vs. human coordination for event planning?**

---

## Research Areas

### Planning Timeline by Event Type

```typescript
interface PlanningTimeline {
  eventType: MICEType;
  attendeeRange: AttendeeRange;
  phases: PlanningPhase[];
  totalLeadTime: string;
}

interface PlanningPhase {
  phase: string;
  startWeeksBefore: number;
  endWeeksBefore: number;
  tasks: PlanningTask[];
  dependencies: string[];
  approvalRequired: boolean;
}

interface PlanningTask {
  taskId: string;
  name: string;
  category: TaskCategory;
  owner: string;
  status: TaskStatus;
  dueDate: Date;
  dependencies: string[];
}

type TaskCategory =
  | 'venue'           // Venue booking and coordination
  | 'catering'        // F&B planning
  | 'av_technology'   // Audio-visual and tech setup
  | 'decor'           // Decoration and theming
  | 'transport'       // Attendee and VIP transport
  | 'accommodation'   // Room blocks and assignments
  | 'registration'    // Attendee registration and communication
  | 'content'         // Agenda, speakers, materials
  | 'marketing'       // Event promotion and communications
  | 'logistics'       // General logistics and operations
  | 'compliance'      // Permits, insurance, safety
  | 'budget';         // Budget tracking and approvals
```

### Typical Planning Timelines

| Event Type | Lead Time | Complexity | Key Milestones |
|-----------|-----------|------------|----------------|
| Small meeting (10-30) | 2-4 weeks | Low | Venue, catering, AV |
| Board meeting | 1-2 weeks | Low | Venue, catering |
| Team offsite (30-100) | 4-8 weeks | Medium | Venue, accommodation, activities, transport |
| Incentive trip | 8-16 weeks | High | Destination, flights, hotel, activities, dining |
| Conference (100-500) | 12-24 weeks | Very High | Venue, speakers, registration, AV, F&B, accommodation |
| Exhibition | 16-32 weeks | Very High | Venue, booth design, logistics, marketing |
| Destination wedding | 16-52 weeks | Extreme | Venue, decor, catering, accommodation, events, transport |

### Logistics Coordination

**Event-day logistics model:**

```typescript
interface EventLogistics {
  eventId: string;
  runOfShow: RunOfShowItem[];
  vendorSchedule: VendorSchedule[];
  floorPlan: FloorPlan;
  contacts: EmergencyContact[];
  contingencyPlan: ContingencyPlan;
}

interface RunOfShowItem {
  time: string;
  duration: number;    // Minutes
  activity: string;
  location: string;
  responsiblePerson: string;
  avRequirements: string[];
  notes: string;
}

interface VendorSchedule {
  vendorId: string;
  vendorName: string;
  serviceType: string;
  arrivalTime: Date;
  setupCompleteBy: Date;
  serviceStartTime: Date;
  serviceEndTime: Date;
  teardownCompleteBy: Date;
  contactPerson: string;
  specialInstructions: string;
}
```

### Budget Management

```typescript
interface EventBudget {
  eventId: string;
  totalBudget: number;
  approvedBudget: number;
  categories: BudgetCategory[];
  contingencyPercent: number;
  currency: string;
}

interface BudgetCategory {
  category: string;
  allocated: number;
  committed: number;
  spent: number;
  remaining: number;
  lineItems: BudgetLineItem[];
}

interface BudgetLineItem {
  itemId: string;
  description: string;
  vendorId: string;
  quantity: number;
  unitPrice: number;
  total: number;
  status: 'estimated' | 'quoted' | 'approved' | 'committed' | 'invoiced' | 'paid';
  approvalRequired: boolean;
  approvedBy?: string;
}
```

**Questions:**
- What budget approval thresholds make sense (auto-approve under ₹X, manager for ₹Y, director for ₹Z)?
- How do we handle budget overruns mid-event?
- What's the standard contingency percentage (typically 10-15%)?

---

## Open Problems

1. **Dependency tracking** — A single event has 50-200+ tasks with complex dependencies. Changes cascade unpredictably. Need robust dependency modeling.

2. **Real-time coordination** — On event day, things change rapidly. How to provide real-time status visibility to all stakeholders?

3. **Scope creep management** — Clients frequently add requirements mid-planning. How to model scope changes with budget and timeline impact analysis?

4. **Multi-event programs** — An incentive trip may have 5 sub-events (welcome dinner, team activities, gala, farewell, departure). How to model programs with sub-events?

5. **Template-driven planning** — Experienced planners reuse checklists from past events. How to capture and templatize planning workflows?

---

## Next Steps

- [ ] Research event planning software workflows (Cvent, Planning Pod, Social Tables)
- [ ] Design planning timeline templates for top 5 event types
- [ ] Study task dependency modeling patterns (Gantt, PERT, Kanban)
- [ ] Investigate real-time event coordination tools and patterns
- [ ] Prototype budget management with approval workflows
