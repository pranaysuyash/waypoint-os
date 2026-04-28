# Calendar & Scheduling — Resource Scheduling

> Research document for venue booking, resource allocation, and capacity planning.

---

## Key Questions

1. **How do we schedule shared resources (meeting rooms, demo units, vehicles)?**
2. **What's the resource booking model for MICE events and group travel?**
3. **How do we handle double-booking prevention and conflict resolution?**
4. **What's the capacity planning model for seasonal peaks?**
5. **How do we schedule supplier meetings and site inspections?**

---

## Research Areas

### Resource Model

```typescript
interface BookableResource {
  resourceId: string;
  name: string;
  type: ResourceType;
  capacity: ResourceCapacity;
  availability: ResourceAvailability;
  bookingRules: BookingRule[];
  location: ResourceLocation;
  owner: string;
}

type ResourceType =
  | 'meeting_room'
  | 'demo_kit'                       // Travel SIM cards, forex cards for demo
  | 'vehicle'                        // For airport pickups, site visits
  | 'equipment'                      // Projector, microphone for MICE
  | 'external_venue'                 // Restaurant, event space
  | 'agent_time'                     // Specialist consultation time
  | 'workspace';                     // Hot desk, quiet room

interface ResourceCapacity {
  maxOccupancy: number;
  assets: string[];                  // Available equipment/features
}

interface ResourceAvailability {
  schedule: AvailabilitySchedule[];
  blackoutDates: Date[];
  minimumBookingDuration: number;    // Minutes
  maximumBookingDuration: number;
  advanceBookingDays: number;        // How far ahead can be booked
  bufferTimeMinutes: number;         // Gap between bookings
}

// Resource scheduling for travel agency:
// Meeting rooms: Customer presentations, team meetings, training
// Vehicles: Airport pickups, site inspections, customer transfers
// Demo kits: Travel SIMs, forex cards for customer demos
// Specialist time: Visa consultant, MICE planner, pricing expert
// External venues: Restaurant for client dinner, event space for launch
```

### Resource Booking

```typescript
interface ResourceBooking {
  bookingId: string;
  resourceId: string;
  tripId?: string;
  bookedBy: string;
  bookedFor: string;                 // Customer name or internal purpose
  startDateTime: Date;
  endDateTime: Date;
  status: BookingStatus;
  recurrence?: RecurrenceRule;
  notes: string;
  setupRequirements?: string[];
  attendees?: string[];
  cost?: number;
  approvalRequired: boolean;
  approvedBy?: string;
}

type BookingStatus =
  | 'tentative'
  | 'confirmed'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'no_show';

// Conflict detection:
// Before creating a booking:
// 1. Check resource availability for the requested time
// 2. Check for overlapping bookings (including buffer time)
// 3. Check blackout dates
// 4. Check advance booking limits
// 5. Check if approval is required for this resource/time
// 6. If conflict found, suggest alternative times or resources

// Double-booking prevention:
// Optimistic locking → Reserve slot for 5 minutes while user completes booking
// Server-side validation → Final check before committing
// Real-time updates → Other users see "being booked" status
// Admin override → Team lead can override for priority bookings
```

### Capacity Planning

```typescript
interface CapacityPlan {
  period: PlanningPeriod;
  resources: ResourceCapacityPlan[];
  staffing: StaffingPlan;
  projections: CapacityProjection[];
}

interface ResourceCapacityPlan {
  resourceType: ResourceType;
  currentCapacity: number;
  projectedDemand: number[];
  gapAnalysis: GapAnalysis;
  recommendedActions: string[];
}

interface StaffingPlan {
  currentAgents: number;
  requiredAgents: number;
  peakSeasonMultiplier: number;
  trainingPipeline: number;
  leaveReserves: number;
}

interface CapacityProjection {
  month: string;
  tripVolume: number;
  agentUtilization: number;
  resourceUtilization: number;
  riskLevel: 'low' | 'medium' | 'high';
}

// Seasonal capacity planning for Indian travel:
// Peak: Oct-Dec (Diwali holidays, year-end trips)
// High: Apr-Jun (summer vacations, school holidays)
// Medium: Jan-Mar (winter travel, honeymoon season)
// Low: Jul-Sep (monsoon season, lower demand)
//
// Planning triggers:
// Projected utilization > 85% → Hire seasonal agents
// Projected utilization > 95% → Stop accepting new trips
// Vehicle utilization > 80% → Arrange additional transport
// Meeting room utilization > 90% → Book external venue
```

### Supplier Scheduling

```typescript
interface SupplierMeeting {
  meetingId: string;
  supplierId: string;
  agentId: string;
  meetingType: SupplierMeetingType;
  scheduledAt: Date;
  location: 'office' | 'supplier_office' | 'virtual' | 'site';
  agenda: string[];
  followUpActions: string[];
}

type SupplierMeetingType =
  | 'onboarding'                     // New supplier relationship kickoff
  | 'rate_negotiation'               // Annual/bi-annual rate discussion
  | 'site_inspection'                // Visit hotel/venue for quality check
  | 'performance_review'             // Quarterly performance discussion
  | 'issue_resolution'               // Address booking/service issues
  | 'training'                       // System integration training
  | 'contract_renewal';              // Discuss contract terms

// Supplier scheduling flow:
// 1. Agent initiates meeting request
// 2. System checks agent and supplier availability
// 3. Propose times to supplier (email/WhatsApp with booking link)
// 4. Supplier confirms time
// 5. Calendar event created for both parties
// 6. Pre-meeting checklist sent to agent (review performance, prepare agenda)
// 7. Meeting happens
// 8. Agent logs meeting notes and action items
// 9. Follow-up tasks created if needed
```

---

## Open Problems

1. **Resource contention during peak season** — Everyone needs meeting rooms and vehicles during October. Need priority-based allocation, not first-come-first-served.

2. **Vehicle tracking** — Drivers and vehicles are shared across trips. Need real-time vehicle tracking and dynamic scheduling for airport pickups.

3. **Site inspection scheduling** — Inspecting a hotel requires the hotel's cooperation. Need supplier-side scheduling integration.

4. **Cost allocation** — External venue bookings cost money. Need cost tracking per trip and cost allocation for shared resources.

5. **Virtual resource scheduling** — Specialist consultations are virtual. Need video call integration with scheduling (auto-generate meeting links).

---

## Next Steps

- [ ] Design resource booking system with conflict detection
- [ ] Build capacity planning model for seasonal variation
- [ ] Create supplier meeting scheduling workflow
- [ ] Design vehicle scheduling for airport pickups and transfers
- [ ] Study resource scheduling systems (Robin, Skedda, Calendly Teams)
