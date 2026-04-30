# Agent Operations Playbook — Daily Operations & SOPs

> Research document for travel agent daily standard operating procedures, shift management, escalation protocols, quality assurance, and operational workflows for the Waypoint OS platform.

---

## Key Questions

1. **What does an agent's daily workflow look like?**
2. **What SOPs ensure consistent service quality?**
3. **How do escalation protocols work for issues?**
4. **What operational metrics track agent effectiveness?**

---

## Research Areas

### Agent Daily Workflow

```typescript
interface AgentDailyWorkflow {
  // Structured daily routine for travel agents
  daily_schedule: {
    MORNING_ROUTINE: {
      time: "9:00 AM - 10:00 AM";
      tasks: [
        {
          task: "Review overnight messages";
          source: "WhatsApp, email, missed calls";
          action: "Respond to urgent queries, acknowledge others, flag for follow-up";
          target: "All overnight messages responded to within 30 minutes of login";
        },
        {
          task: "Check trip status dashboard";
          focus: "Active trips departing today or tomorrow, pending payments, upcoming deadlines";
          action: "Confirm all logistics in place, send final confirmations to travelers";
        },
        {
          task: "Review pipeline";
          focus: "Proposals sent + no response (follow up), new inquiries, bookings to process";
          action: "Prioritize follow-ups by booking probability and travel date urgency";
        },
        {
          task: "Team huddle (if applicable)";
          agenda: "New inquiries, stuck deals, supplier updates, daily targets";
          duration: "10-15 minutes";
        },
      ];
    };

    CORE_WORKING: {
      time: "10:00 AM - 1:00 PM";
      focus: "Customer-facing work — proposals, calls, follow-ups";
      tasks: [
        "Process new inquiries (intake → qualification → response within 2 hours)",
        "Build and send proposals (target: within 24 hours of inquiry)",
        "Follow up on pending proposals (Day 3, Day 7, Day 14 sequence)",
        "Handle booking confirmations and payment collection",
        "Resolve active trip issues (cancellations, changes, complaints)",
      ];
      metrics: {
        proposals_sent: "Target: 3-5 per day (productive agent)";
        calls_made: "Target: 8-12 follow-up calls per day";
        response_time: "Target: <2 hours for new inquiries";
      };
    };

    AFTERNOON: {
      time: "2:00 PM - 5:00 PM";
      focus: "Booking operations, supplier coordination, documentation";
      tasks: [
        "Process confirmed bookings (suppliers, payments, documents)",
        "Coordinate with suppliers (confirm reservations, handle changes)",
        "Prepare travel documents (itineraries, vouchers, tickets)",
        "Update customer records and booking status",
        "Handle visa applications and documentation",
        "Follow up on pending payments",
      ];
    };

    END_OF_DAY: {
      time: "5:00 PM - 6:00 PM";
      tasks: [
        "Review day's work — all inquiries responded, proposals sent, follow-ups done",
        "Update pipeline status for all active trips",
        "Flag any issues for owner/manager review",
        "Set priority list for next morning",
        "Send pending WhatsApp updates to customers",
      ];
    };
  };
}

// ── Agent daily dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Good Morning, Priya · Wednesday, Apr 30                  │
// │                                                       │
// │  🔴 Urgent (do first):                                │
// │  📞 Sharma family — Singapore trip departs tomorrow      │
// │     Final confirmation not sent · [Send Now]               │
// │  💰 Patel booking — ₹45K payment overdue 3 days          │
// │     [Call Customer] [Send Reminder]                        │
// │  📋 Gupta visa — Documents incomplete, deadline May 5     │
// │     [Request Documents]                                    │
// │                                                       │
// │  📊 Today's Targets:                                  │
// │  Proposals: 1 of 4 sent                                   │
// │  Follow-ups: 3 of 8 done                                  │
// │  Calls: 2 of 10 made                                      │
// │  Response time: 1.2h avg ✅                                │
// │                                                       │
// │  📨 Overnight Messages:                               │
// │  3 WhatsApp · 2 Email · 0 Missed calls                    │
// │  [Respond Now]                                             │
// │                                                       │
// │  📋 Pipeline Summary:                                 │
// │  🔥 2 hot leads (call today)                               │
// │  🟡 4 warm proposals (follow up)                           │
// │  🔵 3 new inquiries (respond by 11 AM)                     │
// │                                                       │
// │  [My Trips] [Pipeline] [Messages] [Quick Proposal]        │
// └─────────────────────────────────────────────────────┘
```

### Standard Operating Procedures

```typescript
interface StandardOperatingProcedures {
  // SOPs for common agent scenarios
  sop_library: {
    SOP_NEW_INQUIRY: {
      trigger: "New customer inquiry received via any channel";
      steps: [
        "Acknowledge within 30 minutes (auto-reply acceptable outside business hours)",
        "Capture: destination, dates, travelers, budget range, special requirements",
        "Qualify lead: HOT (traveling <3 months) / WARM (3-6 months) / COLD (>6 months)",
        "If HOT: Agent calls within 2 hours to discuss requirements",
        "If WARM: Send destination info + pricing range via WhatsApp within 4 hours",
        "If COLD: Add to nurture sequence, respond within 24 hours",
        "Create trip in system with all captured details",
        "Assign to self or route to specialist agent",
      ];
      quality_check: "All fields captured, lead qualified, customer acknowledged";
      escalation: "If customer asks for immediate quote and no agent available → auto-send starting price range with agent callback promise";
    };

    SOP_PROPOSAL_CREATION: {
      trigger: "Qualified lead ready for proposal";
      steps: [
        "Select package template or build custom itinerary",
        "Enter confirmed supplier rates (not estimated — use contracted rates)",
        "Apply pricing strategy (cost-plus, value-based, or competitive)",
        "Run margin check — alert if below 8% minimum",
        "Add terms: cancellation policy, payment schedule, validity period",
        "Generate visual proposal PDF from system template",
        "Send via WhatsApp (primary) + email (backup)",
        "Set follow-up reminders: Day 3, Day 7, Day 14",
      ];
      quality_check: "All components priced, margin above minimum, terms included";
      target_time: "<24 hours from inquiry to proposal for HOT leads";
    };

    SOP_BOOKING_CONFIRMATION: {
      trigger: "Customer accepts proposal and pays advance";
      steps: [
        "Collect advance payment (minimum 30% for domestic, 40% for international)",
        "Confirm supplier availability for all components",
        "Make provisional bookings with suppliers",
        "Send booking confirmation to customer with payment receipt",
        "Create detailed day-by-day itinerary",
        "Set payment milestone reminders (balance due dates)",
        "Schedule pre-departure check-in (7 days before travel)",
      ];
      quality_check: "All suppliers confirmed, customer acknowledged, payments tracked";
    };

    SOP_PRE_DEPARTURE: {
      trigger: "7 days before trip departure";
      steps: [
        "Send final itinerary with all confirmations, vouchers, tickets",
        "Weather update for destination",
        "Visa status check (if applicable)",
        "Insurance confirmation (if purchased)",
        "Emergency contact card (agency 24/7 number, local embassy, insurance helpline)",
        "SIM card / connectivity reminder",
        "WhatsApp message: 'Your trip starts in 7 days! Here's everything you need'",
      ];
    };

    SOP_TRIP_DISRUPTION: {
      trigger: "Customer reports issue during trip";
      severity_levels: {
        MINOR: {
          examples: "Hotel room not as expected, activity timing changed";
          response: "Agent handles within 2 hours during business hours";
          resolution: "Contact supplier, arrange alternative, update customer";
        };
        MODERATE: {
          examples: "Flight delayed causing missed connection, hotel overbooked";
          response: "Agent handles within 1 hour; escalate to supplier manager";
          resolution: "Rebook flights, arrange alternative hotel, compensate if needed";
          escalation: "Notify owner if cost impact >₹5,000";
        };
        CRITICAL: {
          examples: "Medical emergency, natural disaster, safety threat";
          response: "Immediate — 24/7 emergency line";
          resolution: "Activate insurance, coordinate with embassy/consulate, arrange evacuation if needed";
          escalation: "Owner notified immediately regardless of cost";
        };
      };
    };
  };
}

// ── SOP quick reference ──
// ┌─────────────────────────────────────────────────────┐
// │  SOP Quick Reference                                       │
// │                                                       │
// │  🆕 New Inquiry                                         │
// │  1. Acknowledge <30min → 2. Capture details             │
// │  3. Qualify (Hot/Warm/Cold) → 4. Route                  │
// │  [Full SOP]                                                │
// │                                                       │
// │  📋 Create Proposal                                      │
// │  1. Template/custom → 2. Supplier rates                  │
// │  3. Price + margin check → 4. Send via WhatsApp          │
// │  Target: <24 hours · [Full SOP]                            │
// │                                                       │
// │  ✅ Booking Confirmation                                 │
// │  1. Collect advance → 2. Confirm suppliers               │
// │  3. Send confirmation → 4. Set milestones                 │
// │  [Full SOP]                                                │
// │                                                       │
// │  ⚠️ Trip Disruption                                      │
// │  Minor: 2h response · Moderate: 1h + escalate           │
// │  Critical: Immediate + owner notification                │
// │  [Full SOP] [Emergency Protocol]                           │
// │                                                       │
// │  [All SOPs] [Training Mode] [New SOP]                      │
// └─────────────────────────────────────────────────────┘
```

### Escalation & Quality Framework

```typescript
interface EscalationFramework {
  // When and how to escalate issues
  escalation_matrix: {
    FINANCIAL: {
      above_margin: "Customer requests discount below minimum margin → Agent offers alternatives, doesn't discount without approval";
      large_booking: "Booking value >₹5L → Owner reviews margin and terms before confirmation";
      payment_default: "Payment overdue >7 days → Escalate to owner for decision (cancel/extend/send notice)";
      refund_request: "Refund >₹10K → Owner approval required";
    };

    OPERATIONAL: {
      supplier_failure: "Supplier cancels confirmed booking → Agent finds alternative, owner notified if cost >₹3K";
      customer_complaint: "Formal complaint → Agent attempts resolution within 24h, escalate to owner if unresolved";
      quality_issue: "Multiple complaints about same supplier → Flag to owner for supplier review";
      safety_concern: "Any safety-related customer report → Immediate escalation to owner regardless of severity";
    };

    TECHNICAL: {
      system_down: "Platform unavailable → Switch to WhatsApp + manual tracking, notify tech support";
      data_loss: "Suspected data loss → Stop all operations, notify owner + tech immediately";
      security_breach: "Suspected breach → Owner + security team, follow incident response protocol";
    };
  };

  quality_metrics: {
    response_time: "New inquiry response <2 hours (target), <30 minutes (excellent)";
    proposal_turnaround: "<24 hours for HOT leads, <48 hours for WARM";
    booking_accuracy: "99%+ correct bookings (wrong dates, wrong hotel = critical error)";
    customer_satisfaction: "NPS 50+ per agent, Google review mention rate >5%";
    payment_collection: "100% advance collected before supplier booking";
    document_delivery: "All travel documents sent 7+ days before departure";
  };
}
```

---

## Open Problems

1. **SOP adherence tracking** — SOPs exist on paper but agents may skip steps under pressure. Need system-level enforcement (e.g., can't send proposal without margin check, can't confirm booking without advance payment).

2. **Agent autonomy vs. control** — Too many escalations slow down service; too few risk costly mistakes. Need clear boundaries: agents handle routine, escalate exceptions.

3. **Workload balancing** — Some agents get 20 inquiries/day, others get 5. Need automatic distribution based on capacity and specialization.

4. **Seasonal scaling** — Peak season (Oct-Feb) requires 2-3x capacity. SOPs must work for both permanent and temporary/seasonal agents with minimal training.

---

## Next Steps

- [ ] Build agent daily dashboard with priority queue
- [ ] Implement SOP enforcement through system workflows
- [ ] Create escalation matrix with automated notifications
- [ ] Design quality metrics tracking per agent
