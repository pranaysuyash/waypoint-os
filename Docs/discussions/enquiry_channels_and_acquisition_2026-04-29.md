# Enquiry Channels, Acquisition Sources & Trip Types — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — expanding enquiry model with real-world detail  
**Approach:** Independent analysis of 4 distinct dimensions blurred in current schema

---

## 1. The Core Insight: 4 Distinct Dimensions

The current schema blurs these into `source_type` and `operating_mode`. They need to be **separate, explicit fields**:

```
Enquiry arrives
  ├─ Channel: HOW did the message arrive? (WhatsApp, email, chatbot)
  ├─ Acquisition Source: HOW did they find us? (referral, repeat, inbound)
  ├─ Enquiry Type: WHAT is this about? (new tour, complaint, change request)
  └─ Trip Type: WHAT kind of trip? (family, corporate, medical)
```

These answers affect **completely different things**:
- **Channel** → Which agent skills needed? (WhatsApp = informal, phone = immediate, chatbot = structured)
- **Acquisition Source** → Priority, pricing, follow-up intensity (referral = high value, inbound = nurture)
- **Enquiry Type** → Workflow, SLA, approval chains (emergency = immediate, feedback = low priority)
- **Trip Type** → Vendor selection, risk rules, drafting templates (medical = specialized vendors)

---

## 2. Dimension 1: Channels (How did the message arrive?)

### Current Schema State
`source_type` in SourceEnvelope has:
```json
["freeform_notes", "structured_form", "partner_api", "whatsapp_transcript", 
 "voice_transcript", "crm_import", "manual_entry", "email_thread", 
 "attachment_extract", "hybrid"]
```

### My Analysis: What's Missing

| Channel | Why it matters | Current coverage |
|---------|------------------|---------------------|
| **WhatsApp** | Global, especially Asia/Latin America. Informal, media-rich (voice notes, photos) | ✅ `whatsapp_transcript` |
| **Telegram** | Eastern Europe, Russia, tech crowds. Bots, channels, groups | ❌ **Missing** |
| **WeChat** | China market. Mini-programs, WeChat Pay integration | ❌ **Missing** |
| **Email** | Corporate clients, formal communication, attachments | ✅ `email_thread` |
| **Voice/Phone** | High-touch, immediate, elderly clients | ✅ `voice_transcript` |
| **Live Chat / Widget** | Website visitors, inbound leads, instant engagement | ❌ **Missing** |
| **Chatbot** | Qualified leads, structured data capture | ❌ **Missing** |
| **Browser Extension** | Corporate clients with self-service | ❌ **Missing** |
| **In-Person** | High-value clients, luxury segment | ❌ `manual_entry` (catches it, but not explicit) |
| **Social Media DM** | Instagram, Facebook, TikTok DMs — younger demographic | ❌ **Missing** |
| **Partner API** | Other agencies, affiliates, B2B | ✅ `partner_api` |
| **CRM Import** | Bulk imports, migrations | ✅ `crm_import` |

### My Proposed `channel` Enum

```json
"channel": {
  "type": "string",
  "enum": [
    // Messaging apps
    "whatsapp",
    "telegram",
    "wechat",
    "line",           // Japan, Thailand
    "viber",          // Eastern Europe
    "social_dm",      // Instagram, Facebook, TikTok DMs
    
    // Traditional
    "email",
    "voice_call",
    "in_person",
    
    // Digital
    "website_widget",
    "chatbot",
    "browser_extension",
    "mobile_app",
    
    // B2B
    "partner_api",
    "crm_import",
    
    // Internal
    "manual_entry",
    "internal_note"
  ]
}
```

**Key decision:** `source_type` in SourceEnvelope stays as "what format is the data in?" (`whatsapp_transcript`, `email_thread`).  
New top-level `channel` field = "which platform delivered this?"

---

## 3. Dimension 2: Acquisition Source (How did they find us?)

### Why This Matters

This drives business logic:
- **Referral** → Higher trust, faster conversion, ask who referred
- **Repeat customer** → Fast-track, skip some validation, VIP treatment
- **Inbound (organic)** → Nurture required, send marketing drip
- **Paid ads** → Track ROAS, aggressive follow-up
- **Walk-in** → Immediate attention, close same day

### My Proposed `acquisition_source` Enum

```json
"acquisition_source": {
  "type": "string",
  "enum": [
    // High-value sources
    "repeat_customer",   // Has booked before
    "vip_repeat",        // High-value repeat customer
    
    // Referrals (explicit tracking)
    "customer_referral",     // Past customer referred
    "team_referral",         // Internal agent/team member referred
    "vendor_referral",       // Hotel/airline referred a customer
    "offer_referral",        // Came via a promotional offer code
    "hotel_tieup_referral", // Tied-up hotel specifically referred
    "partner_agency_referral", // Other travel agency referred
    
    // Organic
    "inbound_organic",   // SEO, direct website visit
    "inbound_social",    // Instagram, Facebook, TikTok organic
    "inbound_content",    // Blog, guide, YouTube
    
    // Paid
    "paid_search",       // Google Ads
    "paid_social",       // Facebook/Instagram Ads
    "paid_display",      // Banners
    "paid_partnership",   // Sponsored hotel/airline listing
    
    // Partnerships & Contracts
    "affiliate",            // Commission-based affiliate
    "corporate_contract",   // Signed B2B contract
    "hotel_tieup_partner", // Formal hotel partnership
    
    // Physical
    "walk_in",          // Physical office visit
    "event_lead",       // Trade show, wedding expo
    "airport_kiosk",     // Airport promotional booth
    
    // Unknown
    "unknown"
  ]
}
```

**My insight:**  
`vendor_referral` and `hotel_tieup_referral` need **special handling** — the referring vendor should be auto-linked to the enquiry (future cross-vendor tracking).  
`team_referral` should credit the internal agent (bonus/commission tracking).

---

## 6. Dimension 5: Geography Scope (NEW — Added 2026-04-29)

### Why This Matters (Your Insight)

Trips differ fundamentally by **geography scope**:
- **Local** (within same country) → no visa, minimal documentation
- **International** → visa required/visa-free, currency exchange, travel insurance
- **Blocked destinations** → some countries don't allow visitors from certain passports (e.g., India → XYZ)

### My Proposed `geography_scope` Field

```json
"geography_scope": {
  "type": "string",
  "enum": [
    "LOCAL",          // Within same city/state/country
    "DOMESTIC",       // Within country, different region
    "INTERNATIONAL",  // Cross-border
    "MULTI_COUNTRY"   // Multi-country itinerary
  ]
}
```

### Visa Status Tracking (Critical for International)

```json
"visa_requirements": {
  "scope": "LOCAL | DOMESTIC | INTERNATIONAL | MULTI_COUNTRY",
  "destinations": [
    {
      "country": "Indonesia",
      "visa_status": "VISA_FREE | VISA_ON_ARRIVAL | E_VISA | VISA_REQUIRED | BLOCKED",
      "visa_type": "string | null",  // "B-1 Tourist", "ETA"
      "processing_days": "integer | null",
      "blocked_reason": "string | null",  // If BLOCKED: "passport_not_allowed"
      "passport_issued_by": "string",  // "India", "US", etc.
      "eligible": "boolean"  // Final verdict
    }
  ],
  "blocked_destinations": ["string"],  // Countries that won't allow this passport
  "warning_flags": [
    {
      "country": "XYZ",
      "reason": "Indian passport holders not permitted for tourism",
      "severity": "CRITICAL"
    }
  ]
}
```

**My insight:**  
`blocked_destinations` should **auto-flag** in `decision_policy` as `STOP_NEEDS_REVIEW` with reason "destination_blocked_for_passport".  
`visa_status = BLOCKED` is a **hard blocker** — no point drafting itinerary if customer can't enter.

---

## 7. Dimension 6: Trip Pattern (NEW — Added 2026-04-29)

### What You Told Me

> "hopping, single destination, multi, or just a layover"

### My Proposed `trip_pattern` Enum

```json
"trip_pattern": {
  "type": "string",
  "enum": [
    "SINGLE_DESTINATION",  // One place only (stay in one hotel)
    "MULTI_DESTINATION",   // Multiple places (Bali → Phuket → Dubai)
    "ISLAND_HOPPING",     // Specific type of multi-destination
    "CITY_HOPPING",       // European/US city tours
    "LAYOVER_ONLY",         // Just transiting, no tourism
    "OPEN_JAW",            // Fly into A, leave from B (different cities)
    "ROAD_TRIP",           // Self-drive, multiple stops
    "CRUISE_ITINERARY"     // Ship-based, ports of call
  ]
}
```

**My insight:**  
`LAYOVER_ONLY` should **skip hotel booking** in drafting — only need airport transfer + lounge access.  
`OPEN_JAW` increases complexity (one-way flights, different drop-off/pickup).

---

## 8. Dimension 7: Destination Type (NEW — Added 2026-04-29)

### What You Told Me

> "publicly famous places or nomadic or country visit or secluded custom etc"

### My Proposed `destination_type` Array

```json
"destination_type": {
  "type": "array",
  "items": {
    "type": "string",
    "enum": [
      // Popularity
      "PUBLICLY_FAMOUS",    // Tourist hotspots (Eiffel Tower, Bali beaches)
      "TRENDING",             // Instagram/TikTok trending places
      "OFF_BEAT",            // Less-known, nomadic style
      "SECULDED_CUSTOM",      // Private, tailor-made, exclusive
      
      // Tourism style
      "TOURISTY",             // High infrastructure, tour buses
      "NOMADIC",              // Digital nomad friendly, co-working
      "LOCAL_EXPERIENCE",      // Live like a local
      "COUNTRYSIDE_VISIT",    // Rural, agricultural, village
      "METROPOLITAN",         // Big cities, business districts
      
      // Specialty
      "UNESCO_SITE",          // World heritage sites
      "ADVENTURE_BASE",        // Trekking, diving hubs
      "WELLNESS_RETREAT",     // Spa, yoga, medical
      "LUXURY_ENCLAVE"        // High-end resorts, private islands
    ]
  }
}
```

**My insight:**  
`PUBLICLY_FAMOUS` → higher prices, must book early, crowded → system should warn about **peak season pricing**.  
`SECULDED_CUSTOM` → higher coordination effort, needs bespoke drafting, senior agent preferred.  
`NOMADIC` → needs reliable WiFi, co-working spaces → system should check `amenities` in vendor selection.

**Key insight:** This is different from `channel`. You can be a **repeat customer** (acquisition source) calling on **WhatsApp** (channel). The schema must track both.

---

## 4. Dimension 3: Enquiry Type (What is this about?)

You listed: new, followup, issue, addon request, emergencies, change requests, complaints, feedback, pricing related, service related.

### My Analysis: Two-Level Hierarchy

**Level 1: Primary Type** (drives workflow selection)
```
NEW_TOUR
IN_PROGRESS_ISSUE
POST_TRIP
```

**Level 2: Subtype** (drives specific behavior)
```
NEW_TOUR:
  ├─ SIMPLE_ENQUIRY        (quick question, no booking yet)
  ├─ PACKAGE_REQUEST       (flight+hotel bundle)
  ├─ BESPOKE_ITINERARY     (fully custom, high-touch)
  ├─ GROUP_TOUR            (weddings, corporate retreats)
  └─ SPECIALIZED          (medical, adventure, educational)

IN_PROGRESS_ISSUE:
  ├─ CHANGE_REQUEST       (dates, names, room type)
  ├─ ADDON_REQUEST        (add airport transfer, upgrade meal plan)
  ├─ PRICING_QUERY        (why is this so expensive, match competitor)
  ├─ SERVICE_ISSUE       (hotel not as described, missed pickup)
  ├─ COMPLAINT           (formal complaint, needs escalation)
  ├─ EMERGENCY           (medical, lost passport, stranded)
  └─ CANCELLATION        (full or partial refund)

POST_TRIP:
  ├─ FEEDBACK            (positive or negative, for improvement)
  ├─ REVIEW_REQUEST      (ask to post on Google/TripAdvisor)
  └─ REFERRAL_REQUEST    (ask to refer friends)
```

### My Proposed Schema

```json
"enquiry_type": {
  "type": "string",
  "enum": ["NEW_TOUR", "IN_PROGRESS_ISSUE", "POST_TRIP"]
},
"enquiry_subtype": {
  "type": "string",
  "enum": [
    // NEW_TOUR subtypes
    "simple_enquiry",
    "package_request", 
    "bespoke_itinerary",
    "group_tour",
    "specialized",
    
    // IN_PROGRESS_ISSUE subtypes
    "change_request",
    "addon_request",
    "pricing_query",
    "service_issue",
    "complaint",
    "emergency",
    "cancellation",
    
    // POST_TRIP subtypes
    "feedback",
    "review_request",
    "referral_request"
  ]
}
```

**Key decision:** `enquiry_subtype` values are NOT all valid for all `enquiry_type`.  
- `emergency` only valid when `enquiry_type = IN_PROGRESS_ISSUE`
- `bespoke_itinerary` only valid when `enquiry_type = NEW_TOUR`

This constraint should be enforced in the decision engine, not just schema validation.

---

## 5. Dimension 4: Trip Type (What kind of trip?)

You listed: family, solo, leisure, corporate, group, medical.

### My Expanded Taxonomy

```
By Traveler Composition:
  ├─ SOLO
  ├─ COUPLE
  ├─ FAMILY              (with children)
  ├─ MULTI_GENERATION    (grandparents + parents + kids)
  ├─ GROUP               (friends, reunions)
  
By Purpose:
  ├─ LEISURE             (vacation, relax)
  ├─ ADVENTURE            (trekking, diving, safari)
  ├─ HONEYMOON           (romantic, special)
  ├─ MEDICAL             (surgery, wellness, dental)
  ├─ EDUCATIONAL         (student trips, cultural exchange)
  ├─ CORPORATE           (business travel, conferences)
  ├─ MICE                (Meetings, Incentives, Conferences, Exhibitions)
  ├─ WEDDING             (destination wedding)
  └─ RELOCATION          (moving, long-term stay)
```

### My Proposed Schema

```json
"trip_type": {
  "type": "array",
  "items": {
    "type": "string",
    "enum": [
      // Composition
      "solo", "cuple", "family", "multi_generational", "group",
      // Purpose
      "leisure", "adventure", "honeymoon", "medical", 
      "educational", "corporate", "mice", "wedding", "relocation"
    ]
  },
  "description": "Can be multiple (e.g., ['family', 'leisure', 'honeymoon'])"
}
```

**Key insight:** Trip type is an **array**, not a single value. A trip can be `family` + `leisure` + `adventure`.

---

## 6. How These Dimensions Interact

### Example 1: High-Value Corporate Client
```
Channel: email
Acquisition Source: corporate_contract
Enquiry Type: NEW_TOUR
Enquiry Subtype: group_tour
Trip Type: ["corporate", "mice"]
```
→ **Workflow:** Assign senior agent, use corporate pricing, MICE drafting template

### Example 2: Repeat Customer with Emergency
```
Channel: whatsapp
Acquisition Source: repeat_customer
Enquiry Type: IN_PROGRESS_ISSUE
Enquiry Subtype: emergency
Trip Type: ["family", "leisure"]
```
→ **Workflow:** Skip triage, immediate agent attention, pull full customer history

### Example 3: New Instagram Lead
```
Channel: social_dm
Acquisition Source: inbound_social
Enquiry Type: NEW_TOUR
Enquiry Subtype: simple_enquiry
Trip Type: ["couple", "leisure"]
```
→ **Workflow:** Nurture sequence, casual tone, quick response expected

---

## 7. What Current Schema Gets Wrong

| Issue | Current State | My Fix |
|-------|---------------|------|
| Channel vs Source blurred | `source_type` mixes both | Split into `channel` + `acquisition_source` |
| No Telegram/WeChat | Not in enum | Add all major regional platforms |
| No acquisition tracking | Only `is_repeat_customer` boolean | Add `acquisition_source` with full taxonomy |
| Enquiry type buried | In `operating_mode` | Promote to top-level `enquiry_type` + `enquiry_subtype` |
| Trip type is free-text | `trip_purpose` as FieldSlot | Add `trip_type` as typed enum array |

---

## 8. Decisions Needed Before Implementation

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Keep `source_type` as-is? | Yes / Migrate to `channel` | **Migrate** — `source_type` name is confusing, rename to `channel` |
| `trip_type` as array? | Single / Array | **Array** — trips can be multiple types |
| Subtype validation? | Runtime only / Schema enum | **Both** — enum for known values, runtime for cross-field validation |
| Acquisition source required? | Yes / No | **Yes** — default to `unknown`, but track it |

---

## 9. Next Discussion: Customer Model

Now that we know:
- **How enquiries arrive** (channel)
- **Where customers come from** (acquisition source)
- **What they want** (enquiry type + subtype)
- **What trip they need** (trip type)

We need to discuss: **Who is the customer?**

Key questions for next discussion:
1. Individual vs Company (corporate accounts)?
2. What fields does a customer profile need?
3. How do we link repeat enquiries to same customer?
4. What's the VIP/high-value customer definition?
5. How do we track customer lifetime value?

---

**Next file:** `Docs/discussions/customer_model_2026-04-29.md`
