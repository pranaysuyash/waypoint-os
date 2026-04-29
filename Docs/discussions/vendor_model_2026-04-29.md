# Vendor Model — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — after human agent model  
**Approach:** Independent analysis — MAJOR gap, no vendor entity exists yet  

---

## 1. The Core Problem: Vendors Don't Exist in the Schema**

### Current Schema State

Only 2 vendor-related fields exist, both as FieldSlots inside `facts` or `derived_signals`:
```json
"facts": {
  "hotel_preferences": { "$ref": "#/$defs/FieldSlot" }
}
"derived_signals": {
  "preferred_supplier_available": { "$ref": "#/$defs/FieldSlot" }
}
```

### Why This is a CRITICAL Gap (First Principles)

The business description says:
> "they talk to and process diff. stuff with agents (travel agents not ai agents), **vendors**, send drafts and other comms."

**Vendors are 50% of the business workflow**:
1. **Human agents coordinate with vendors** to get quotes, check availability, negotiate rates
2. **Drafts sent to customers** include vendor bookings (hotels, flights, activities)
3. **Issues/complaints** often involve vendor performance (hotel not as described, missed pickup)
4. **Revenue** comes from vendor commissions, not just customer payments

Burying this in `facts.hotel_preferences` is a **catastrophic design error**.

---

## 2. My Vendor Entity Model**

### Level 1: Vendor Identity & Type**

```json
{
  "vendor_id": "string (UUID)",
  "vendor_type": "ACCOMODATION | AIR_TRANSPORT | GROUND_TRANSPORT | ACTIVITY | CRUISE | INSURANCE | VISA_PROCESSING | DMC | AGGREGATOR | MEETING_VENUE",
  
  // Basic info
  "company_name": "string",
  "brand_name": "string | null",  // "Marriott" vs "JW Marriott Bali"
  "registration_number": "string | null",
  "tax_id": "string | null",  // GST, VAT, etc.
  "website": "string | null",
  "logo_url": "string | null",
  
  // Contact
  "primary_contact": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "whatsapp": "string | null",
    "wechat": "string | null"
  },
  "emergency_contact": {
    "name": "string",
    "phone": "string",
    "available_24x7": "boolean"
  },
  
  // Geography
  "headquarters": {
    "city": "string",
    "country": "string",
    "address": "string"
  },
  "operating_regions": ["SE_ASIA", "EUROPE", "MIDDLE_EAST"],
  "operating_countries": ["Thailand", "Indonesia", "UAE"],
  "operating_cities": ["Bali", "Phuket", "Dubai"]
}
```

---

### Level 2: Contract & Commercials**

```json
{
  "contract": {
    // Contract status
    "status": "ACTIVE | EXPIRED | PENDING_RENEWAL | TERMINATED",
    "contract_id": "string | null",
    "signed_date": "string (ISO8601)",
    "expiry_date": "string (ISO8601) | null",
    "auto_renewal": "boolean",
      
    // Relationship tier
    "vendor_tier": "PREFERRED | CONTRACTED | AD_HOC | BLACKLISTED",
    "exclusivity": "EXCLUSIVE | PREFERRED | NON_EXCLUSIVE",  // Are we the only agency with this rate?
    "preferred_since": "string (ISO8601)",
      
    // Payment terms
    "payment_terms_days": "integer",  // Net-30, Net-45, etc.
    "credit_limit": "number (float) | null",
    "advance_payment_percent": "number (0.0-100.0)",  // 0 = full credit, 100 = full advance
      
    // Commission structure
    "commission_rate_default": "number (0.0-100.0)",  // Agency earns this %
    "commission_structure": [  // Tiered commissions
      {
        "volume_threshold": "number (float)",  // Annual booking volume
        "commission_rate": "number (0.0-100.0)"
      }
    ],
      
    // Pricing
    "pricing_model": "STATIC | DYNAMIC | SEASONAL",
    "rate_parity_clause": "boolean",  // Can't offer lower rates elsewhere
    "last_rate_update": "string (ISO8601)"
  }
}
```

**My insight:**  
`vendor_tier = PREFERRED` should auto-populate in `derived_signals.preferred_supplier_available`.  
`exclusivity = EXCLUSIVE` is a competitive advantage — system should flag this to agents.

---

### Level 3: Performance & Reliability**

```json
{
  "performance": {
    // Overall scores
    "overall_rating": "number (1.0-5.0)",
    "reliability_score": "number (0.0-1.0)",  // Do they deliver what they promise?
    "response_time_avg_hours": "number",
    "cancellation_rate": "number (0.0-1.0)",  // How often they cancel on us
      
    // Issue tracking
    "total_bookings": "integer",
    "complaint_count": "integer",
    "complaint_resolved_count": "integer",
    "complaint_rate": "number (0.0-1.0)",  // complaints / total_bookings
    "average_resolution_hours": "number",
      
    // Recent performance (last 90 days)
    "recent_complaints": "integer",
    "recent_cancellations": "integer",
    "recent_issues": [
      {
        "date": "string (ISO8601)",
        "issue_type": "NO_SHOW | POOR_QUALITY | WRONG_ROOM | MISSED_TRANSFER",
        "severity": "LOW | MEDIUM | HIGH | CRITICAL",
        "resolved": "boolean",
        "notes": "string"
      }
    ],
      
    // Agent feedback
    "agent_ratings": [
      {
        "agent_id": "string",
        "rating": "number (1.0-5.0)",
        "comment": "string | null",
        "rated_at": "string (ISO8601)"
      }
    ]
  }
}
```

**My insight:**  
`complaint_rate > 0.05` (5%+) should **auto-flag** in `derived_signals.document_risk` when drafting itineraries with this vendor.  
Agents should see a **warning badge** on high-complaint vendors.

---

### Level 4: Inventory & Services**

```json
{
  "services": [
    {
      "service_id": "string",
      "service_type": "ROOM | FLIGHT | TRANSFER | TOUR | ACTIVITY | MEAL",
      "name": "Deluxe Ocean View Room",
      "description": "string | null",
        
      // Geography
      "city": "Bali",
      "country": "Indonesia",
      "specific_location": "Nusa Dua",
        
      // Capacity
      "max_occupancy": "integer | null",
      "min_occupancy": "integer",  // Default 1
      "room_count": "integer | null",  // For hotels
      "vehicle_type": "string | null",  // For transfers
        
      // Pricing
      "base_price": "number (float)",
      "currency": "string",
      "seasonal_pricing": [
        {
          "season": "PEAK | HIGH | SHOULDER | LOW",
          "start_month": "integer (1-12)",
          "end_month": "integer (1-12)",
          "price_multiplier": "number (float)"  // 1.5 = 50% markup
        }
      ],
        
      // Availability
      "availability_status": "AVAILABLE | LIMITED | SOLD_OUT | NOT_BOOKABLE",
      "last_availability_check": "string (ISO8601)",
        
      // Attributes
      "amenities": ["wifi", "pool", "spa", "gym"],
      "accessibility_features": ["wheelchair_access", "elevator"],
      "child_friendly": "boolean",
      "pet_friendly": "boolean"
    }
  ]
}
```

**My insight:**  
This is a **lightweight inventory model**. Full inventory management (like a GDS) is overkill.  
Agents mostly need: **what they offer, at what price, with what quality**.

---

## 3. Vendor-Agent-Customer Triangle**

### How Vendors Fit in the Workflow

```
Customer submits enquiry
  └─ Human Agent receives it
       ├─ Checks Customer profile (preferences, past trips)
       ├─ Searches Vendors by:
       │    ├─ Geography (destination = Bali)
       │    ├─ Type (hotel, flight)
       │    ├─ Tier (PREFERRED > CONTACTED > AD_HOC)
       │    ├─ Capacity (family of 4, 2 rooms)
       │    └─ Dates (available during travel window)
       ├─ Contacts Vendors (WhatsApp, email, phone)
       ├─ Negotiates rates (uses contract rates as baseline)
       ├─ Gets quotes + availability
       ├─ Drafts itinerary (AI assists)
       └─ Sends to Customer
            └─ If complaint/issue:
                 └─ Agent contacts Vendor for resolution
```

---

## 4. Vendor in Enquiry & Booking**

### Vendor References in CanonicalPacket**

Currently: NONE. My proposal:

```json
{
  "facts": {
    "preferred_vendors": {  // Auto-populated from vendor database
      "value": [
        {
          "vendor_id": "string",
          "vendor_name": "string",
          "service_type": "hotel",
          "city": "Bali"
        }
      ],
      "confidence": 1.0,
      "authority_level": "derived_signal",
      "extraction_mode": "derived",
      "evidence_refs": []
    },
    "hotel_preferences": { /* stays as-is, but enhanced */ }
  }
}
```

### Vendor in Booking (New Model Needed)**

```json
{
  "booking_id": "string (UUID)",
  "vendor_bookings": [
    {
      "vendor_id": "string",
      "service_id": "string",
      "booking_reference": "string",  // Vendor's confirmation number
      "status": "QUOTED | CONFIRMED | CANCELLED | COMPLETED",
      "price_quoted": "number (float)",
      "price_final": "number (float)",
      "commission_earned": "number (float)",
      "booked_by_agent_id": "string",
      "booked_at": "string (ISO8601)",
      "cancellation_policy": "string",
      "special_requests": "string | null"
    }
  ]
}
```

---

## 5. Vendor Risk & Compliance**

### Risk Flags Related to Vendors**

```json
{
  "vendor_risks": [
    {
      "vendor_id": "string",
      "risk_type": "HIGH_COMPLAINT | FINANCIAL_INSTABILITY | BLACKLISTED | CONTRACT_EXPIRED",
      "severity": "LOW | MEDIUM | HIGH | CRITICAL",
      "detected_at": "string (ISO8601)",
      "detected_by": "system | agent_id",
      "action_taken": "FLAGGED | SUSPENDED | BLACKLISTED",
      "notes": "3 complaints in last 30 days"
    }
  ]
}
```

**My insight:**  
`vendor_risks` with `severity = CRITICAL` should **block** vendor selection in drafting.  
System should auto-suggest alternative vendors.

---

## 6. Current Schema vs Vendor Model**

| Concept | Current Schema | My Proposed Model |
|---------|---------------|-------------------|
| Vendor identity | None | `Vendor` entity with full profile |
| Vendor type | None | `vendor_type` enum (10+ types) |
| Contract status | None | `contract.status`, `vendor_tier` |
| Performance | None | `performance.overall_rating`, `complaint_rate` |
| Commission | None | `contract.commission_rate_default` |
| Inventory | None | `services[]` array with geography + pricing |
| Risk flagging | None | `vendor_risks[]` with severity |
| Preferred status | `derived_signals.preferred_supplier_available` | Promoted to `contract.vendor_tier = PREFERRED` |

---

## 7. Vendor Search & Matching Logic**

### How Agents Find Vendors**

```
Agent searches for: "Bali family hotel, 2 rooms, June 15-20"
  ├─ Filter 1: vendor_type = ACCOMODATION
  ├─ Filter 2: operating_cities includes "Bali"
  ├─ Filter 3: services.city = "Bali"
  ├─ Filter 4: services.max_occupancy >= 4 (family)
  ├─ Filter 5: services.availability_status != SOLD_OUT
  ├─ Sort 1: vendor_tier (PREFERRED > CONTACTED > AD_HOC)
  ├─ Sort 2: performance.overall_rating (descending)
  └─ Sort 3: performance.complaint_rate (ascending)
```

**My insight:**  
Search should **auto-boost PREFERRED vendors** to top, even if slightly more expensive.  
Agents should see `commission_rate` — it affects their earnings.

---

## 8. Decisions Needed**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Vendor as top-level entity? | Yes / No | **YES** — they're 50% of the business workflow |
| Inventory model depth? | Lightweight / Full GDS | **Lightweight** — store what agents need to draft |
| Auto-flag high-complaint vendors? | Yes / No | **YES** — protect customer experience |
| Commission tracking? | Yes / No | **YES** — agents care about earnings |
| Vendor-Aent relationship? | Yes / No | **YES** — `agent_ratings[]` for preference |

---

## 9. Next Discussion: Communication Model**

Now that we know:
- **Enquiry types** (new tour, in-progress issue, post-trip)
- **Channels** (WhatsApp, Telegram, WeChat, email, etc.)
- **Customer model** (individual vs corporate, VIP, health score)
- **Human Agent model** (skills, workload, performance)
- **Vendor model** (types, contracts, performance, inventory)

We need to discuss: **How does communication flow between all these entities?**

Key questions for next discussion:
1. Communication as first-class entity? (track ALL comms)
2. Comms channels per entity (customer prefers WhatsApp, vendor prefers email)
3. Comms templates (drafts, follow-ups, complaints, confirmations)
4. AI assistance in comms (draft generation, tone adjustment)
5. Comms tracking (who said what, when, channel)
6. Internal comms (agent-to-agent, agent-to-manager)
7. Comms audit trail (required for complaints/disputes)

---

**Next file:** `Docs/discussions/communication_model_2026-04-29.md`
