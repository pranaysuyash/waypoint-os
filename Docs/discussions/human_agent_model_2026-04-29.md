# Human Agent Model — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — after customer model, before vendor model  
**Approach:** Independent analysis — critical distinction between Human Agents vs AI Agents

---

## 1. The Critical Distinction: Human Agent vs AI Agent

### What the Business Description Says

> "they talk to and process diff. stuff with **agents (travel agents not ai agents)**, vendors, send drafts and other comms."

### What the Current Code Does

The codebase uses "agent" for **BOTH**:
- **AI Agents** = software components (`spine_api`, `NB01`, `NB02`, decision engine)
- **Human Agents** = travel agency staff (the actual users of this system)

This is **confusing and wrong**. They are fundamentally different things:

| Aspect | Human Agent | AI Agent (Software) |
|--------|--------------|---------------------|
| **What they are** | Travel agency staff | Software components |
| **Role** | Uses the system | Powers the system |
| **Makes decisions?** | Yes — approvals, overrides | Assists — suggestions only |
| **Communicates with customers?** | Yes — sends comms, drafts | No — generates text for humans |
| **Coordinates with vendors?** | Yes — human relationships | No — only via API/email |
| **Learns from experience?** | Yes — intuition, memory | Only via retraining |

### My Key Insight

**Rename the software to "AI Engine" or "Decision Engine" — reserve "Agent" for human travel agents.**

The system should be:
```
Human Agent (travel staff) 
  └─ uses ─→ AI Engine (spine_api, decision engine)
                    ├─ ingests enquiries
                    ├─ drafts suggestions
                    └─ flags risks
```

---

## 2. Human Agent Entity Model

### Core Identity

```json
{
  "agent_id": "string (UUID)",
  "agent_type": "INTERNAL_STAFF | FREELANCER | PARTNER_AGENT",
  
  // Personal
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "phone_whatsapp": "string | null",
  "phone_office": "string | null",
  "profile_photo_url": "string | null",
  
  // Professional
  "employee_id": "string | null",  // Internal HR ID
  "date_joined": "string (ISO8601)",
  "seniority": "JUNIOR | SENIOR | TEAM_LEAD | MANAGER",
  "status": "ACTIVE | ON_LEAVE | TERMINATED",
  
  // Languages (critical for WhatsApp/WeChat)
  "languages": [
    {
      "language": "en",
      "proficiency": "BASIC | FLUENT | NATIVE",
      "can_support": "boolean"  // False = only understands, can't support customers
    },
    {
      "language": "zh",
      "proficiency": "FLUENT",
      "can_support": true
    }
  ],
  
  // System access
  "role": "AGENT | SUPERVISOR | MANAGER | ADMIN",
  "permissions": ["VIEW_ALL_ENQUIRIES", "APPROVE_REFUND", "OVERRIDE_BUDGET", ...]
}
```

---

### Skills & Expertise

```json
{
  "skills": {
    // Geographic expertise
    "regions": ["SE_ASIA", "EUROPE", "MIDDLE_EAST", "EAST_ASIA"],
    "countries_expert": ["Thailand", "Indonesia", "UAE"],
    "destinations_certified": ["Bali", "Phuket", "Dubai"],
    
    // Trip type expertise
    "trip_types": ["leisure", "honeymoon", "adventure", "corporate", "medical"],
    "specializations": ["scuba_diving", "destination_weddings", "medical_tourism"],
    
    // Vendor relationships
    "preferred_vendors": ["string (vendor_id)"],  // Hotels/airlines they work with
    "vendor_negotiation_authorized": "boolean",
    
    // Customer segment expertise
    "customer_segments": ["VIP", "CORPORATE", "GROUPS"],
    "medical_certified": "boolean",  // For medical tourism
    "halal_certified": "boolean"  // For halal travel
  },
  
  "certifications": [
    {
      "name": "IATA Certification",
      "issued_by": "IATA",
      "issued_date": "2024-01-15",
      "expiry_date": "2026-01-15",
      "certification_id": "IATA-12345"
    }
  ]
}
```

**My insight:**  
Skills should **drive auto-assignment**. A `medical` enquiry should route to `medical_certified = true` agents. A `WeChat` enquiry from China should route to `languages includes zh + can_support = true` agents.

---

### Workload Management

```json
{
  "workload": {
    // Current state
    "status": "AVAILABLE | BUSY | AWAY | OFFLINE",
    "active_enquiries_count": "integer",
    "max_concurrent_enquiries": "integer",  // Hard limit
    "active_booking_count": "integer",
    
    // Queues
    "assigned_enquiry_ids": ["string"],
    "watched_enquiry_ids": ["string"],  // Supervisor watching
    "escalated_enquiry_ids": ["string"],  // Awaiting their approval
    
    // Time tracking
    "average_response_time_minutes": "number",
    "last_activity_at": "string (ISO8601)",
    "total_active_minutes_today": "integer"
  },
  
  "schedule": {
    "timezone": "Asia/Kolkata",
    "working_hours": {
      "monday": { "start": "09:00", "end": "18:00" },
      "saturday": { "start": "10:00", "end": "14:00" },
      "sunday": null
    },
    "is_available_now": "boolean"  // Computed from schedule + current time
  }
}
```

**My insight:**  
`max_concurrent_enquiries` should vary by seniority:
- **Junior:** 15 enquiries
- **Senior:** 25 enquiries  
- **Team Lead:** 10 enquiries (also manages others)
- **Manager:** 5 enquiries (also approves, escalations)

---

### Performance & Quality

```json
{
  "performance": {
    // Conversion metrics
    "total_enquiries_handled": "integer",
    "total_bookings_created": "integer",
    "conversion_rate": "number (0.0-1.0)",  // bookings / enquiries
    "average_booking_value": "number (float)",
    
    // Speed metrics
    "average_first_response_minutes": "number",
    "average_resolution_hours": "number",
    "sla_breach_count": "integer",
    
    // Quality metrics
    "customer_satisfaction_avg": "number (1.0-5.0)",
    "complaints_received": "integer",
    "complaints_resolved": "integer",
    
    // Financial
    "total_revenue_generated": "number (float)",
    "commission_earned_lifetime": "number (float)",
    "bonus_eligible": "boolean"
  },
  
  "quality_score": {
    "overall": "number (0.0-1.0)",
    "breakdown": {
      "response_speed": "number (0.0-1.0)",
      "customer_satisfaction": "number (0.0-1.0)",
      "booking_value": "number (0.0-1.0)",
      "complaint_rate": "number (0.0-1.0)"
    },
    "last_calculated": "string (ISO8601)"
  }
}
```

**My insight:**  
Quality score should affect **assignment priority**. Higher quality agents get VIP/enquiry assignments.

---

### Approval Chains & Escalation

```json
{
  "approval_authority": {
    // Financial limits
    "max_refund_without_approval": "number (float)",
    "max_discount_percent": "number (0.0-100.0)",
    "max_upgrade_cost": "number (float)",
    
    // What they can approve
    "can_approve_refund": "boolean",
    "can_approve_cancellation": "boolean",
    "can_override_budget": "boolean",
    "can_override_risk_flag": "boolean",
    
    // Escalation target
    "reports_to_agent_id": "string | null",
    "can_escalate_to": ["string (agent_id)"],  // Who they can escalate to
    
    // Supervisor duties
    "supervises_agent_ids": ["string"],
    "approval_queue_enquiry_ids": ["string"]
  }
}
```

**My insight:**  
`reports_to_agent_id` creates **hierarchy**. VIP customer enquiries should auto-escalate to `seniority = MANAGER` if `customer_segment = VIP`.

---

## 3. Agent-Enquiry Matching Logic

### Auto-Assignment Rules (My Proposed Logic)

```
Enquiry arrives
  ├─ Filter 1: Agent status = AVAILABLE?
  ├─ Filter 2: Agent languages match enquiry channel language?
  ├─ Filter 3: Agent skills match trip_type?
  │     └─ medical enquiry → medical_certified = true
  ├─ Filter 4: Agent workload < max_concurrent_enquiries?
  ├─ Filter 5: Customer segment vs agent seniority?
  │     └─ VIP customer → seniority >= SENIOR
  ├─ Filter 6: Agent working_hours match current time?
  └─ Score & Assign: Highest score gets the enquiry
```

### Matching Score Formula

```
Score = 
  (workload_factor * 0.3) +       // Lower workload = higher score
  (skill_match * 0.3) +            // More matching skills = higher
  (performance_score * 0.2) +       // Higher quality = higher
  (language_match * 0.1) +         // Language match = bonus
  (seniority_bonus * 0.1)          // Senior gets slight bonus for VIP
```

---

## 4. Agent-Customer Relationship

### Dedicated Agent Assignment

```json
{
  "dedicated_agent_assignments": [
    {
      "customer_id": "string",
      "agent_id": "string",
      "assignment_type": "VIP_AUTO | CORPORATE_CONTRACT | PREFERRED | MANAGER_OVERRIDE",
      "assigned_by": "string (agent_id of manager)",
      "assigned_at": "string (ISO8601)",
      "notes": "string | null"
    }
  ]
}
```

**My insight:**  
VIP customers should have a **dedicated agent** (relationship building). Corporate contracts may specify which agent handles their employees.

---

## 5. Agent-Vendor Coordination

### Vendor Relationship Tracking

```json
{
  "vendor_relationships": [
    {
      "vendor_id": "string",
      "relationship_type": "PREFERRED | CONTRACTED | OWNER_PREFERRED",
      "rating_given": "number (1.0-5.0)",  // How this agent rates the vendor
      "last_booking_at": "string (ISO8601)",
      "total_bookings_with": "integer",
      "commission_rate": "number (0.0-100.0)",  // Their personal commission
      "notes": "They're reliable for last-minute changes"
    }
  ]
}
```

**My insight:**  
Agents build **personal relationships with vendors**. The system should track which agent works best with which vendor (for escalation paths).

---

## 6. Current Schema vs Human Agent Model

| Concept | Current Schema | My Proposed Model |
|---------|---------------|-------------------|
| Agent identity | `facts.coordinator_id` (FieldSlot) | Top-level `HumanAgent` entity |
| Agent type | None | `INTERNAL_STAFF | FREELANCER | PARTNER_AGENT` |
| Skills/expertise | None | `skills.regions`, `skills.trip_types`, `skills.languages` |
| Workload | None | `workload.active_enquiries_count`, `max_concurrent` |
| Performance | None | `performance.conversion_rate`, `quality_score` |
| Approval authority | None | `approval_authority.max_refund_without_approval` |
| Schedule | None | `schedule.working_hours`, `is_available_now` |
| Vendor relationships | None | `vendor_relationships[]` |

---

## 7. Decisions Needed

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Rename AI "agents" in code? | Yes / No | **YES** — rename to "AI Engine" or "Decision Engine" |
| Human Agent as top-level entity? | Yes / No | **YES** — they're the primary users |
| Auto-assignment mandatory? | Yes / Optional | **Optional** — manager can override |
| Dedicated agent for VIP? | Yes / No | **YES** — relationship building |
| Quality score affects assignment? | Yes / No | **YES** — higher quality gets priority |

---

## 8. Next Discussion: Vendor Model

Now that we know:
- **Enquiry types** (new tour, in-progress issue, post-trip)
- **Channels & acquisition** (WhatsApp, Telegram, WeChat, etc.)
- **Trip types** (family, solo, corporate, medical, etc.)
- **Customer model** (individual vs corporate, VIP, health score)
- **Human Agent model** (skills, workload, performance, approval chains)

We need to discuss: **Who do agents coordinate with?**

Key questions for next discussion:
1. Vendor as entity — what fields? (name, contact, services, regions)
2. Vendor types — hotel, airline, DMC, ground handler, activity provider?
3. Vendor relationships — preferred, contracted, commission rates?
4. Vendor performance — reliability, response time, complaint rate?
5. Vendor negotiations — who can negotiate, discount authority?
6. Vendor payments — terms, credit, invoicing?

---

**Next file:** `Docs/discussions/vendor_model_2026-04-29.md`
