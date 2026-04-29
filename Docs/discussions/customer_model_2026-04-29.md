# Customer Model — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — after defining enquiry types, channels, acquisition sources  
**Approach:** Independent analysis — current schema treats customer as ID reference, not first-class entity

---

## 1. The Core Problem: Customer is Not a First-Class Entity

### Current Schema State

The schema treats `customer_id` as a **FieldSlot inside facts**:
```json
"facts": {
  "customer_id": { "$ref": "#/$defs/FieldSlot" },
  "past_trips": { "$ref": "#/$defs/FieldSlot" },
  "traveler_details": { "$ref": "#/$defs/FieldSlot" },
  "party_composition": { "$ref": "#/$defs/FieldSlot" },
  "sub_groups": { "$ref": "#/$defs/FieldSlot" }
}
```

And `derived_signals` has:
```json
"is_repeat_customer": { "$ref": "#/$defs/FieldSlot" }
```

### Why This is Wrong (First Principles)

A **Customer** is a **first-class entity** with its own:
1. **Lifecycle** — prospect → active → dormant → churned
2. **Profile** — name, contact, preferences, VIP status
3. **Relationships** — enquiries, bookings, referrals given/received
4. **Value** — lifetime spend, profit margin, cost to serve
5. **Health** — satisfaction score, complaint history, at-risk signals

Burying this in `facts.customer_id` as a FieldSlot is a **procedural mindset** (customer as a reference) vs **entity mindset** (customer as a thing with behavior).

---

## 2. My Customer Entity Model

### Level 1: Customer Identity

```json
{
  "customer_id": "string (UUID)",
  "customer_type": "INDIVIDUAL | CORPORATE | TRAVEL_AGENT_PARTNER",
  
  // Individuals
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "phone_primary": "string",
  "phone_whatsapp": "string | null",
  "preferred_channel": "whatsapp | email | telegram | wechat | voice_call",
  
  // Corporates
  "company_name": "string | null",
  "gst_number": "string | null",  // India
  "billing_address": "string | null",
  "corporate_contract_tier": "NONE | BRONZE | SILVER | GOLD | PLATINUM",
  
  // Shared
  "acquisition_source": "referral | repeat_customer | inbound_organic | ...",
  "referred_by_customer_id": "string | null",
  "referral_code": "string | null"
}
```

---

### Level 2: Customer Value & Segmentation

```json
{
  // Lifetime value
  "first_enquiry_date": "string (ISO8601)",
  "total_bookings": "integer",
  "total_spend_lifetime": "number (float, in base currency)",
  "average_booking_value": "number (float)",
  "customer_lifetime_value": "number (float)",
  "profit_margin_avg": "number (float, 0.0-1.0)",
  
  // Segmentation
  "customer_segment": "VIP | HIGH_VALUE | STANDARD | PRICE_SENSITIVE | AT_RISK",
  "churn_risk": "LOW | MEDIUM | HIGH",
  "health_score": "number (0.0-1.0)",  // satisfaction-based
  
  // Service level
  "priority_level": "STANDARD | PRIORITY | VIP",
  "dedicated_agent_id": "string | null",  // Assigned agent for VIPs
  "sla_level": "STANDARD | EXPRESS | IMMEDIATE"
}
```

**My insight:**  
`customer_segment` should be **computed**, not manual. But `priority_level` can be manually overridden (VIP status).

---

### Level 3: Customer Preferences & Behavior

```json
{
  // Travel preferences
  "preferred_destinations": ["string"],  // Historical pattern
  "preferred_trip_types": ["leisure", "family", "adventure"],
  "budget_range_typical": {
    "min": "number",
    "max": "number",
    "currency": "string"
  },
  "accommodation_preference": "BUDGET | STANDARD | LUXURY | ULTRA_LUXURY",
  "meal_preference": "veg" | "non-veg" | "vegan" | "jain" | "halal" | null,
  
  // Communication preferences
  "marketing_opt_in": "boolean",
  "communication_style": "FORMAL | CASUAL | FRIENDLY",  // Affects AI draft tone
  "language_preference": "string (ISO 639-1)",  // "en", "hi", "zh", etc.
  
  // Behavior patterns
  "typical_lead_time_days": "integer",  // How far in advance they book
  "cancellation_rate": "number (0.0-1.0)",  // Historical cancel %
  "modification_rate": "number (0.0-1.0)",  // How often they change bookings
  "payment_behavior": "ALWAYS_ON_TIME | SOMETIMES_DELAYED | ALWAYS_EMI"
}
```

**My insight:**  
`cancellation_rate` and `modification_rate` are **risk signals**. High-cancellation customers should trigger stricter payment terms or higher margins.

---

### Level 4: Customer Relationships

```json
{
  // Enquiries & Bookings
  "enquiry_ids": ["string"],  // All enquiries from this customer
  "active_booking_ids": ["string"],  // Current in-progress bookings
  "completed_booking_ids": ["string"],
  "cancelled_booking_ids": ["string"],
  
  // Referral network
  "referrals_made_customer_ids": ["string"],  // Customers they referred
  "referral_reward_balance": "number (float)",
  "referral_reward_redeemed": "number (float)",
  
  // Service history
  "complaint_count": "integer",
  "complaint_resolved_count": "integer",
  "average_satisfaction_rating": "number (1.0-5.0)",
  "feedback_count": "integer"
}
```

---

## 3. How Customer Model Affects Enquiry Handling

### Workflow Branching Based on Customer Segment

| Customer Segment | Enquiry Priority | Agent Assignment | Draft Tone | Follow-up Intensity |
|-----------------|-------------------|-------------------|-------------|----------------------|
| **VIP / PLATINUM** | IMMEDIATE | Dedicated agent | Formal, personalized | High-touch, 2h SLA |
| **HIGH_VALUE** | HIGH | Senior agent | Professional, warm | Standard, 4h SLA |
| **STANDARD** | NORMAL | Any available agent | Friendly, efficient | Automated, 24h SLA |
| **PRICE_SENSITIVE** | NORMAL | Junior agent | Value-focused | Template-heavy |
| **AT_RISK** | HIGH | Senior agent + manager | Apologetic, solution-focused | High-touch recovery |

### My Key Insight: Customer Context Should Auto-Populate Enquiry

When a **repeat customer** submits a new enquiry:
1. Auto-populate `facts` from customer profile (name, passport status, dietary, preferences)
2. Pre-fill `facts.past_trips` from customer history
3. Set `derived_signals.is_repeat_customer = true`
4. Adjust `derived_signals.urgency` based on customer segment
5. Suggest `agency_notes` based on past complaints/special requests

**This is automation that helps human agents, not replaces them.**

---

## 4. Customer Health & Early Warning System

### Health Score Components

```json
{
  "health_score": "number (0.0-1.0)",
  "health_breakdown": {
    "satisfaction_weight": "0.4",
    "complaint_weight": "0.3",
    "payment_weight": "0.2",
    "engagement_weight": "0.1"
  },
  "health_signals": {
    "recent_complaints": "integer (last 90 days)",
    "payment_delays": "integer (last 90 days)",
    "unresponsive_enquiries": "integer (last 90 days)",
    "negative_feedback_count": "integer"
  }
}
```

### At-Risk Customer Detection

```
Triggers for "AT_RISK" segment:
  ├─ health_score < 0.4
  ├─ recent_complaints > 2 (in 90 days)
  ├─ payment_delays > 1 (in 90 days)
  ├─ unresponsive_enquiries > 3 (consecutive)
  └─ negative_feedback_count > 0 (with no positive since)
```

**My insight:**  
At-risk customers need **manager involvement** on their next enquiry. The system should auto-escalate.

---

## 5. Corporate Customer Model (Special Case)

### Additional Fields for `customer_type = CORPORATE`

```json
{
  "company_name": "string",
  "registration_number": "string | null",
  "gst_number": "string | null",
  "billing_address": "string",
  "corporate_tier": "BRONZE | SILVER | GOLD | PLATINUM",
  
  // Contacts (multiple people)
  "primary_contact": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "designation": "string"
  },
  "finance_contact": {
    "name": "string",
    "email": "string",
    "phone": "string"
  },
  "authorized_travelers": [
    {
      "employee_id": "string",
      "name": "string",
      "designation": "string",
      "travel_policy_tier": "ECONOMY | BUSINESS | FIRST"
    }
  ],
  
  // Contract terms
  "payment_terms_days": "integer",  // Net-30, Net-45, etc.
  "credit_limit": "number (float)",
  "volume_discount_percent": "number (0.0-100.0)",
  "contract_expiry": "string (ISO8601) | null"
}
```

**My insight:**  
Corporate customers have **multiple human contacts** (primary, finance, travelers). The `enquiry` must track **which contact** submitted it, not just the company.

---

## 6. Customer Model vs Current Schema

| Concept | Current Schema | My Proposed Model |
|---------|---------------|-------------------|
| Customer identity | `facts.customer_id` (FieldSlot) | Top-level `Customer` entity |
| Repeat status | `derived_signals.is_repeat_customer` (FieldSlot) | `total_bookings > 0` (computed) |
| Past trips | `facts.past_trips` (FieldSlot) | `completed_booking_ids` (array of references) |
| Traveler details | `facts.traveler_details` (FieldSlot) | Structured `Customer` fields |
| Preferences | Buried in `facts.soft_preferences` | Explicit preference fields |
| VIP status | None | `customer_segment = VIP` + `priority_level` |
| Health score | None | `health_score` + `churn_risk` |
| Referrals | None | `referred_by_customer_id` + `referrals_made_customer_ids` |
| Corporate | None | `customer_type = CORPORATE` + corporate fields |

---

## 7. Migration Path (Non-Destructive)

### Phase 1: Add Customer Entity (Parallel)
1. Create new `Customer` model in `spine_api/models/customer.py`
2. Create `frontend/src/types/customer.ts`
3. New API endpoints: `/api/customers/*`
4. Keep `facts.customer_id` as-is (backward compatibility)

### Phase 2: Link Enquiries to Customer
1. On new enquiry: check if `customer_id` exists in Customer table
2. If not, auto-create Customer from enquiry `facts`
3. Link enquiry to Customer via foreign key

### Phase 3: Migrate Old Data
1. Backfill Customer table from historical `facts.customer_id`
2. Compute `total_bookings`, `total_spend_lifetime` from booking history
3. Calculate `health_score` from complaints/feedback

### Phase 4: Deprecate Old Fields
1. Mark `facts.customer_id` as deprecated
2. Update all references to use Customer entity
3. Remove after 2 release cycles

---

## 8. Decisions Needed

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Customer as top-level entity? | Yes / No | **YES** — it's a first-class thing with behavior |
| Corporate as separate model? | Separate / Same with `type` field | **Same model** with `customer_type` discriminator |
| Health score computed? | Real-time / Daily batch | **Real-time** on enquiry/booking events |
| Auto-create customer on enquiry? | Yes / No | **YES** — zero-friction for agents |
| VIP override manual? | Yes / Computed only | **Manual override** — business may know things system doesn't |

---

## 9. Next Discussion: Human Agent Model

Now that we know:
- **Enquiry types** (new tour, in-progress issue, post-trip)
- **Channels & acquisition** (WhatsApp, email, Telegram, WeChat, etc.)
- **Trip types** (family, solo, corporate, medical, etc.)
- **Customer model** (individual vs corporate, VIP, health score)

We need to discuss: **Who handles these enquiries?**

Key questions for next discussion:
1. Human agent as entity — what fields? (name, email, expertise, workload)
2. Agent skills/domains — who handles medical tourism? Who handles corporate?
3. Workload management — how many enquiries can an agent handle?
4. Agent-customer matching — VIP customers get senior agents?
5. Agent performance tracking — conversion rate, response time, customer satisfaction?
6. Senior/junior agents — approval chains, escalation paths?

---

**Next file:** `Docs/discussions/human_agent_model_2026-04-29.md`
