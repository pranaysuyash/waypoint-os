# Booking Model — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — after communication model, completing core entity discussion  
**Approach:** Independent analysis — booking is the financial/legal contract, not just a trip plan  

---

## 1. The Core Problem: Booking Doesn't Exist as an Entity**

### Current Schema State

Bookings are **implied** but not explicit:
```json
// In CanonicalPacket facts:
"existing_itinerary": { "$ref": "#/$defs/FieldSlot" },
"selected_itinerary": { "$ref": "#/$defs/FieldSlot" },

// In derived_signals:
"booking_readiness": { "$ref": "#/$defs/FieldSlot" }

// In decision_policy.md:
stage: "discovery" → "shortlist" → "proposal" → "booking"
```

### Why This is Wrong (First Principles)

A **Booking** is a **legal/financial contract** with:
1. **Payment obligation** — customer owes money, agency owes services
2. **Vendor commitments** — hotels/airlines have confirmed inventory
3. **Cancellation terms** — what happens if someone cancels?
4. **Documents issued** — vouchers, tickets, confirmations
5. **Multiple travellers** — each with their own passport/visa status
6. **Modification history** — what changed, who approved it, when?

Burying this in `stage = "booking"` is a **category error**. Stage is a state, booking is an **entity**.

---

## 2. My Booking Entity Model**

### Level 1: Booking Identity & Status**

```json
{
  "booking_id": "string (UUID)",
  "enquiry_id": "string",  // Links back to original enquiry
  "booking_type": "NEW | MODIFICATION | CANCELLATION | REBOOKING",
  
  // Status lifecycle
  "status": "QUOTED | CONFIRMED | TICKETED | IN_PROGRESS | COMPLETED | CANCELLED | PARTIALLY_CANCELLED",
  "sub_status": "PAYMENT_PENDING | VENDOR_CONFIRMING | DOCUMENTS_PENDING | TRAVELLER_CHECKED_IN",
  
  // Dates
  "created_at": "string (ISO8601)",
  "confirmed_at": "string | null",
  "start_date": "string (ISO8601)",  // First travel date
  "end_date": "string (ISO8601)",    // Last travel date
  "cancelled_at": "string | null",
  
  // People
  "customer_id": "string",
  "primary_traveller_id": "string",
  "traveller_count": "integer",
  "assigned_agent_id": "string",  // Agent handling this booking
  
  // References
  "booking_reference": "string",  // Internal ref (TA-2026-0042)
  "amadeus_pnr": "string | null",
  "third_party_ref": "string | null"  // Partner/aggregator ref
}
```

**My insight:**  
`booking_type = MODIFICATION` creates a **new booking** linked to the old one (not just editing the old). This preserves audit trail.

---

### Level 2: Travellers (Per-Person Details)**

```json
{
  "travellers": [
    {
      "traveller_id": "string (UUID)",
      "given_name": "string",
      "surname": "string",
      "date_of_birth": "string (ISO8601)",
      "gender": "M | F | OTHER | PREFER_NOT_TO_SAY",
      "nationality": "string",  // "Indian", "American"
      "passport_number": "string",
      "passport_expiry": "string (ISO8601)",
      "visa_status": "NOT_REQUIRED | APPLIED | APPROVED | REJECTED | BLOCKED",
      "visa_expiry": "string | null",
      
      // Health & Special needs
      "medical_conditions": ["string"],  // "diabetes", "pacemaker"
      "mobility_constraints": ["string"],  // "wheelchair", "walker"
      "dietary_restrictions": ["string"],  // "vegan", "nut-allergy"
      "emergency_contact": {
        "name": "string",
        "phone": "string",
        "relationship": "spouse | parent | sibling | friend"
      },
      
      // Documents
      "documents": [
        {
          "type": "PASSPORT | VISA | VACCINATION | MEDICAL_CLEARANCE",
          "document_url": "string",
          "verified_at": "string | null",
          "verified_by_agent_id": "string | null"
        }
      ]
    }
  ]
}
```

**My insight:**  
`visa_status = BLOCKED` should **auto-cancel** the booking with full refund (legal impossibility).  
`passport_expiry` < `end_date + 6 months` = **compliance warning** (many countries require 6-month validity).

---

### Level 3: Booking Items (What's Actually Booked)**

```json
{
  "booking_items": [
    {
      "item_id": "string (UUID)",
      "item_type": "FLIGHT | HOTEL | TRANSFER | ACTIVITY | MEAL | INSURANCE | VISA_PROCESSING | CRUISE",
      "vendor_id": "string",
      "vendor_booking_ref": "string | null",  // Hotel conf #, airline PNR
      
      // What
      "description": "string",  // "Deluxe Ocean View Room", "SQ 321 Economy"
      "details": {
        // For flights
        "flight_number": "string | null",
        "origin": "string",
        "destination": "string",
        "departure_time": "string (ISO8601)",
        "arrival_time": "string (ISO8601)",
        "cabin_class": "ECONOMY | PREMIUM_ECONOMY | BUSINESS | FIRST",
        
        // For hotels
        "hotel_name": "string",
        "room_type": "string",
        "meal_plan": "RO | BB | HB | FB | AI",  // Room only, Bed&Breakfast, Half board, Full board, All inclusive
        "check_in": "string (ISO8601)",
        "check_out": "string (ISO8601)",
        "nights": "integer"
      },
      
      // Money
      "currency": "string",
      "base_price": "number (float)",
      "taxes": "number (float)",
      "fees": "number (float)",
      "total_price": "number (float)",
      "commission_earned": "number (float)",
      
      // Status
      "status": "QUOTED | CONFIRMED | CANCELLED | COMPLETED",
      "cancellation_policy": "string",  // "Non-refundable", "50% if 7+ days"
      "cancellation_deadline": "string (ISO8601) | null",
      
      // Vouchers
      "voucher_issued_at": "string | null",
      "voucher_url": "string | null",
      "eticket_url": "string | null"
    }
  ]
}
```

**My insight:**  
`booking_items` is the **source of truth** for "what was promised".  
Complaints should reference specific `item_id`, not just "the hotel was bad".

---

### Level 4: Payment & Financials**

```json
{
  "payment": {
    // Total
    "currency": "string",
    "total_booking_value": "number (float)",
    "total_paid_to_date": "number (float)",
    "balance_due": "number (float)",
    "agency_commission_total": "number (float)",
    
    // Payment plan
    "payment_type": "FULL | INSTALLMENTS | EMI",
    "installments": [
      {
        "installment_number": "integer",
        "due_date": "string (ISO8601)",
        "amount": "number (float)",
        "status": "PENDING | PAID | OVERDUE",
        "paid_at": "string | null",
        "payment_method": "CREDIT_CARD | BANK_TRANSFER | UPI | CASH | EMIs",
        "transaction_id": "string | null"
      }
    ],
    
    // Invoicing
    "invoices": [
      {
        "invoice_id": "string",
        "invoice_number": "string",  // "INV-2026-0042"
        "issued_at": "string (ISO8601)",
        "due_date": "string (ISO8601)",
        "amount": "number (float)",
        "status": "PENDING | PAID | OVERDUE | CANCELLED",
        "pdf_url": "string | null"
      }
    ],
    
    // Refunds (if cancelled)
    "refunds": [
      {
        "refund_id": "string",
        "reason": "CUSTOMER_REQUEST | VENDOR_CANCELLATION | AGENCY_ERROR | FORCE_MAJEURE",
        "requested_at": "string (ISO8601)",
        "approved_at": "string | null",
        "approved_by_agent_id": "string | null",
        "refund_amount": "number (float)",
        "refund_method": "ORIGINAL_PAYMENT | BANK_TRANSFER | WALLET",
        "status": "PENDING | PROCESSING | COMPLETED | REJECTED",
        "completed_at": "string | null"
      }
    ]
  }
}
```

**My insight:**  
`balance_due > 0` when `status = CONFIRMED` should **block voucher issuance**.  
`payment_type = EMI` needs **dedicated agent approval** (credit risk).

---

### Level 5: Modification History (Critical for In-Progress Issues)**

```json
{
  "modifications": [
    {
      "modification_id": "string (UUID)",
      "modification_type": "DATE_CHANGE | TRAVELLER_CHANGE | HOTEL_CHANGE | FLIGHT_CHANGE | CANCELLATION | ADDON",
      "requested_by": "CUSTOMER | AGENT | VENDOR",
      "requested_at": "string (ISO8601)",
      "requested_by_id": "string",  // customer_id, agent_id, or vendor_id
      
      // What changed
      "changes": [
        {
          "field": "start_date",
          "old_value": "2026-07-15",
          "new_value": "2026-07-20",
          "reason": "Customer requested later dates"
        }
      ],
      
      // Approval
      "status": "PENDING | APPROVED | REJECTED | COMPLETED",
      "approved_by_agent_id": "string | null",
      "approved_at": "string | null",
      "rejection_reason": "string | null",
      
      // Financial impact
      "price_delta": "number (float)",  // Positive = customer pays more
      "commission_delta": "number (float)",
      
      // Vendor coordination
      "vendor_notified_at": "string | null",
      "vendor_confirmed_at": "string | null",
      "vendor_confirmation_ref": "string | null"
    }
  ]
}
```

**My insight:**  
`modifications[]` is the **audit trail** for complaints.  
"Why did my dates change?" → Check `modifications[]` with timestamps and approvals.

---

## 3. Booking Lifecycle Stages**

### Status Flow (State Machine)**

```
QUOTED
  └─ (payment received, vendor confirmed) → CONFIRMED
       └─ (tickets/vouchers issued) → TICKETED
            └─ (travel starts) → IN_PROGRESS
                 └─ (travel ends) → COMPLETED
                      └─ (post-trip follow-up done) → CLOSED

Alternative paths:
  QUOTED ── (customer rejects) → ABANDONED
  CONFIRMED ── (cancellation request) → CANCELLATION_PENDING
                    └─ (approved) → CANCELLED
                              └─ (refund processed) → REFUNDED
```

**My insight:**  
`IN_PROGRESS` status should **auto-activate** features like:
- Emergency contact mode (24x7 agent available)
- Location tracking (optional, for family safety)
- Real-time vendor check-ins

---

## 4. Booking vs Enquiry Relationship**

### One Enquiry → Many Bookings (My Model)**

```
Enquiry (enquiry_id: "eq-001")
  ├─ Booking #1: NEW (booking_id: "bk-001") — Main trip
  ├─ Booking #2: ADDON (booking_id: "bk-002") — Added airport transfer
  └─ Booking #3: MODIFICATION (booking_id: "bk-003") — Date change, links to bk-001
```

### Why This Matters

1. **Enquiry is the conversation** — all comms, drafts, negotiations
2. **Booking is the contract** — legally binding, financial, vendor-committed
3. **One enquiry can spawn multiple bookings** — add-ons, modifications, cancellations

**My insight:**  
`BOOKING` should be a **separate API resource** (`/api/bookings/:id`), not buried in `CanonicalPacket`.

---

## 5. Complaint/Issue Linking to Bookings**

### How In-Progress Issues Map to Bookings**

```json
{
  "enquiry_type": "IN_PROGRESS_ISSUE",
  "enquiry_subtype": "complaint",
  "related_booking_ids": ["bk-001"],  // Which booking is the issue about?
  "issue_details": {
    "affected_item_ids": ["item-123"],  // Which specific hotel/flight?
    "issue_type": "SERVICE_NOT_AS_DESCRIBED | MISSED_TRANSFER | ROOM_NOT_READY",
    "severity": "LOW | MEDIUM | HIGH | CRITICAL",
    "evidence_attachments": ["string (url)"],  // Photos, receipts
    "witness_traveller_ids": ["string"]
  }
}
```

**My insight:**  
Linking complaint to `affected_item_ids` lets system **auto-notify the vendor** (`vendor_id` on that item).  
`severity = CRITICAL` should **wake up manager** + dedicated agent via WhatsApp.

---

## 6. Current Schema vs Booking Model**

| Concept | Current Schema | My Proposed Model |
|---------|---------------|-------------------|
| Booking identity | None | `Booking` entity with `booking_id` |
| Booking status | `stage = "booking"` | `status` enum (QUOTED → CONFIRMED → ...) |
| Travellers | `facts.party_composition` (FieldSlot) | `travellers[]` array with full details |
| Items booked | `facts.selected_itinerary` (FieldSlot) | `booking_items[]` with vendor + price + status |
| Payments | None | `payment` object with installments + invoices |
| Modifications | None | `modifications[]` audit trail |
| Cancellations | None | `modifications[]` with `type = CANCELLATION` |
| Refunds | None | `payment.refunds[]` with status tracking |
| Vouchers | None | `booking_items[].voucher_url` |
| Documents | `facts.passport_status` (FieldSlot) | Per-traveller `documents[]` |

---

## 7. Decisions Needed**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Booking as top-level entity? | Yes / No | **YES** — it's a legal/financial contract |
| Separate API resource? | Yes / No | **YES** — `/api/bookings/` with full CRUD |
| Modification = new booking? | Yes / Edit old | **NEW booking** with `links_to_booking_id` (audit trail) |
| Auto-link complaint to vendor? | Yes / No | **YES** — `affected_item_ids` → auto-notify vendor |
| Voucher generation? | System / Vendor | **VENDOR** — system stores URL, vendor generates |
| EMI needs approval? | Yes / No | **YES** — credit risk, manager approval |

---

## 8. Next Step: System Architecture Planning**

We've now defined ALL core entities from first principles:
1. ✅ **Enquiry** (types, stages, channels, acquisition)
2. ✅ **Customer** (individual, corporate, VIP, health)
3. ✅ **Human Agent** (skills, workload, performance)
4. ✅ **Vendor** (types, contracts, performance)
5. ✅ **Communication** (comms tracking, drafts, templates)
6. ✅ **Booking** (contracts, payments, modifications)

### What's Next?

We can now plan the **System Architecture**:
- How do these entities relate in a database schema?
- What API endpoints do we need?
- How does the AI Engine (spine_api) orchestrate across these entities?
- What's the frontend information architecture?
- How do we migrate from the current broken schema to this new model?

---

**Next file:** `Docs/discussions/system_architecture_plan_2026-04-29.md`
