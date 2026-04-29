# Enquiry Types and Stages — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — core domain model discussion  
**Approach:** First principles, independent analysis of existing schema vs actual business needs

---

## 1. Current Schema Reality Check

### What exists in `canonical_packet.schema.json`

The schema has these fields that touch enquiry handling:

| Field | Values | Problem |
|-------|---------|---------|
| `stage` | `discovery`, `shortlist`, `proposal`, `booking` | Only covers NEW tour booking workflow. No concept of in-progress issue workflows. |
| `operating_mode` | `normal_intake`, `audit`, `emergency`, `follow_up`, `cancellation`, `post_trip`, `coordinator_group`, `owner_review` | **Category error** — mixes enquiry types with internal processing modes. |
| `facts.trip_purpose` | FieldSlot | Exists but not used as a discriminator for enquiry type. |
| `facts.existing_itinerary` | FieldSlot | Hints at in-progress bookings, but not explicit. |

### The Category Error in `operating_mode`

```
operating_mode = {
  // Enquiry types (what is this about?):
  "normal_intake",     → New tour enquiry
  "emergency",         → In-progress urgent issue
  "cancellation",      → In-progress cancellation request
  "post_trip",         → In-progress post-trip issue
  
  // Internal processing modes (how do we handle it?):
  "audit",             → Internal review mode
  "owner_review",      → Internal escalation
  "coordinator_group", → Internal routing
  "follow_up"          → Could be either
}
```

These are conceptually different things merged into one field. That's a design flaw.

---

## 2. First Principles: What is an Enquiry?

From the business description:
> "User is an agency, they get enquiries for new tours and customer issues/complaints/guidance req."

An **enquiry** is the unit of work the agency receives. It has:

1. **A type** — what is this about?
2. **A status** — where is it in its lifecycle?
3. **A customer** — who sent it?
4. **An assignee** — which human agent handles it?
5. **A source** — how did it arrive (email, WhatsApp, form)?
6. **Related bookings** — if it's about an existing booking

---

## 3. My Proposed Enquiry Type Model

### Type 1: `NEW_TOUR` — No booking exists yet

The customer wants something new. The agency must create a booking from scratch.

**Subtypes by purpose (what kind of trip):**
- `LEISURE` — vacation, honeymoon, family trip
- `BUSINESS` — corporate travel, conferences
- `GROUP` — weddings, reunions, corporate retreats
- `SPECIALIZED` — medical tourism, adventure, educational

**Subtypes by complexity (how much work is involved):**
- `SIMPLE` — single component (hotel only, flight only)
- `PACKAGE` — flight + hotel + transfers
- `MULTI_DEST` — multi-city, island hopping
- `BESPOKE` — fully custom, high-touch

**Why this matters:**  
A `SIMPLE` enquiry can go from received → booked in 1 day.  
A `BESPOKE` enquiry might take 3 weeks and 15 drafts.  
The system should adapt the workflow accordingly.

---

### Type 2: `IN_PROGRESS_ISSUE` — Booking exists, something needs attention

The customer has an existing booking that's in-progress (not completed yet). They need support.

**Subtypes by nature (what's wrong):**
- `COMPLAINT` — service not as described, poor hotel, missed transfer
- `CHANGE_REQUEST` — dates, names, room type, flight changes
- `GUIDANCE` — visa questions, documentation help, local info
- `EMERGENCY` — medical, lost passport, stranded, missed flight
- `CANCELLATION` — full or partial refund request

**Why this matters:**  
`EMERGENCY` needs immediate agent attention + vendor coordination.  
`GUIDANCE` can be answered with a template + AI assist.  
`COMPLAINT` needs investigation + evidence + vendor negotiation.  
The workflow and SLA should differ for each.

---

## 4. My Proposed Enquiry Lifecycle Stages

### `NEW_TOUR` Lifecycle

| Stage | Meaning | Key Action | Human Agent Role |
|-------|---------|-------------|-------------------|
| `RECEIVED` | Enquiry just came in | Parse raw input (AI), extract facts | Review AI extraction, correct errors |
| `TRIAGED` | Assessed, prioritized, assigned | Set priority, assign agent | Take ownership, review completeness |
| `SCOPING` | Missing details gathered | Ask customer follow-up questions | Communicate with customer, gather info |
| `RESEARCHING` | Vendor options sourced | Search inventory, get quotes | Contact vendors, compare options |
| `DRAFTING` | Itinerary + quote created | Build draft proposal (AI assist) | Review AI draft, add human touches |
| `PRESENTED` | Draft sent to customer | Send to customer, wait for feedback | Present options clearly, manage expectations |
| `NEGOTIATING` | Revisions back-and-forth | Incorporate feedback, re-quote | Negotiate with vendors, manage customer expectations |
| `CONFIRMED` | Customer accepts, ready to book | Take payment, prepare booking | Verify all details, process payment |
| `BOOKED` | Vendors confirmed, vouchers issued | Send confirmations, vouchers | Ensure all vendors have confirmed |
| `COMPLETED` | Travel done, post-trip follow-up | Collect feedback, close enquiry | Check customer satisfaction |

**Key insight:**  
Stages `RECEIVED` through `TRIAGED` are **intake**.  
Stages `SCOPING` through `RESEARCHING` are **preparation**.  
Stages `DRAFTING` through `NEGOTIATING` are **presentation**.  
Stages `CONFIRMED` through `BOOKED` are **execution**.  
Stage `COMPLETED` is **closure**.

---

### `IN_PROGRESS_ISSUE` Lifecycle

| Stage | Meaning | Key Action | Human Agent Role |
|-------|---------|-------------|-------------------|
| `RECEIVED` | Issue just raised | Parse (AI), categorize urgency | Review, set priority |
| `TRIAGED` | Urgency assessed, categorized | Route to specialist if needed | Take ownership, assess severity |
| `INVESTIGATING` | Root cause + options explored | Contact vendors, gather evidence | Coordinate with vendors, document findings |
| `RESOLVING` | Solution implemented | Vendor action taken, refund processed | Ensure vendor delivers on promise |
| `RESOLVED` | Customer notified + acknowledged | Send resolution comms, get ack | Confirm customer is satisfied |
| `CLOSED` | No further action needed | Archive, update customer record | Final check, close enquiry |

**Key insight:**  
This lifecycle is SHORTER than new tour — there's no drafting/presentation phase.  
The critical path is `INVESTIGATING` → `RESOLVING` — this is where vendor coordination happens.  
`EMERGENCY` subtypes should skip/accelerate `TRIAGED` and go straight to `INVESTIGATING`.

---

## 5. Where the Current Schema is Wrong

### Mistake 1: Using `stage` for booking workflow, not enquiry workflow

The schema's `stage` field (`discovery` → `shortlist` → `proposal` → `booking`) maps to the **booking's** lifecycle, not the **enquiry's** lifecycle.

But an enquiry about a **complaint** doesn't have a "discovery" stage — it has a "received → triaged → investigating" flow.

**Fix:** Separate `enquiry_stage` (enquiry lifecycle) from `booking_stage` (booking lifecycle).

---

### Mistake 2: Burying enquiry type in `operating_mode`

The `operating_mode` field mixes:
- What the enquiry is about (`normal_intake`, `emergency`, `cancellation`)
- How the system should process it (`audit`, `owner_review`)

**Fix:** Create a top-level `enquiry_type` field with values `NEW_TOUR` | `IN_PROGRESS_ISSUE`.  
Move processing modes to a separate `processing_mode` field.

---

### Mistake 3: No explicit link between enquiry and bookings

The schema has `facts.existing_itinerary` but no proper relationship model.

**Fix:** An enquiry should be able to reference:
- Zero bookings (new tour enquiry, no booking yet)
- One booking (simple issue about one booking)
- Multiple bookings (group complaint affecting multiple bookings)

---

## 6. Proposed Schema Changes

### New top-level fields for CanonicalPacket:

```json
{
  "enquiry_id": "string (UUID)",
  "enquiry_type": "NEW_TOUR | IN_PROGRESS_ISSUE",
  "enquiry_subtype": "string (LEISURE|BUSINESS|... or COMPLAINT|EMERGENCY|...)",
  "enquiry_stage": "string (RECEIVED|TRIAGED|...)",
  "enquiry_priority": "LOW|NORMAL|HIGH|URGENT",
  "assigned_agent_id": "string (human agent handling this)",
  "customer_id": "string",
  "related_booking_ids": ["string"],
  "source_type": "string (from SourceEnvelope)",
  "processing_mode": "NORMAL|AUDIT|OWNER_REVIEW"
}
```

### Deprecate/Migrate:
- `stage` → rename to `booking_stage`, move to `facts` or `derived_signals`
- `operating_mode` → split into `enquiry_type` + `processing_mode`

---

## 7. Next Discussion Topics

Before we implement, we should discuss:

1. **Customer model** — who is the buyer? Individual vs company? Repeat vs new?
2. **Human agent model** — workloads, expertise, seniority?
3. **Vendor model** — how do we track vendor relationships and performance?
4. **Communication model** — how do we track all comms (customer, vendor, internal)?
5. **Booking model** — what fields does a booking need? How does it link to enquiry?

---

## 8. Decisions Needed

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Top-level `enquiry_type`? | Yes / No | **YES** — it's the primary discriminator for all downstream logic |
| Separate `enquiry_stage` from `booking_stage`? | Yes / No | **YES** — they have different lifecycles |
| Keep `operating_mode` as-is? | Keep / Split / Remove | **SPLIT** into `enquiry_type` + `processing_mode` |
| Where to store `assigned_agent_id`? | Top-level / facts | **Top-level** — it's not a "fact about the trip", it's workflow metadata |

---

**Next step:** Discuss and document customer model, then human agent model, then vendor model — before touching any code.
