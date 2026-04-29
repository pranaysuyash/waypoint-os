# CRM Approach — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent = CRM for travel agencies  
**Approach:** Discussion format — questions first, shape together  

---

## 1. The Core Insight: This IS a CRM

### Why This Changes Things

A CRM isn't just "customer records." It's:

- **Contact management** → who are your customers
- **Deal pipeline** → what stage is each enquiry
- **Communication history** → every WhatsApp, email, call with Ravi
- **Activity timeline** → ALL interactions in ONE chronological feed
- **Task management** → follow up with Ravi, send voucher
- **Automated triggers** → "4h no reply → reminder"

### What a Standard CRM Has (Salesforce, HubSpot, Zoho)

| Feature | HubSpot | Zoho | SalesForce |
|---------|---------|------|------------|
| Contact management | ✅ | ✅ | ✅ |
| Deal pipeline | ✅ Kanban | ✅ Kanban | ✅ Kanban |
| Activity timeline | ✅ | ✅ | ✅ |
| Email integration | ✅ | ✅ | ✅ |
| Task management | ✅ | ✅ | ✅ |
| Workflow automation | ✅ | ✅ | ✅ |
| Reporting | ✅ | ✅ | ✅ |
| Mobile app | ✅ | ✅ | ✅ |

### What We Have vs What's Missing

| Feature | Our Status | Standard CRM |
|---------|-----------|--------------|
| Customer model | ✅ `customer_model.md` | ✅ Contacts |
| Enquiry stages | ✅ `enquiry_types_and_stages.md` | ✅ Pipeline |
| Communications | ✅ `communication_model.md` | ✅ Activity log |
| Tasks | ✅ `dashboard_homepage.md` | ✅ Tasks |
| **Activity Timeline (Customer 360)** | ❌ **NOT DISCUSSED** | ✅ Timeline |
| **Pipeline Kanban View** | ❌ **NOT DISCUSSED** | ✅ Deal board |
| **Automated Triggers/Workflows** | ❌ **NOT DISCUSSED** | ✅ Workflows |
| **Internal Notes** | ❌ **NOT DISCUSSED** | ✅ Notes |
| **Lead Scoring** | ❌ **NOT DISCUSSED** | ✅ Scoring |
| **Customer Segmentation** | ❌ **NOT DISCUSSED** | ✅ Lists |

---

## 2. Activity Timeline — Discussion

### What Is It?

Every interaction with Ravi in ONE chronological feed:

```
Ravi's Activity Timeline
========================
Apr 29, 2:30pm — You sent voucher PDF
Apr 29, 2:15pm — Ravi paid ₹1.2L (UPI confirmed)
Apr 29, 10:00am — Status changed: DRAFT SENT → BOOKING CONFIRMED
Apr 28, 6:00pm — You added internal note: "VIP, call directly for changes"
Apr 28, 4:00pm — Ravi replied: "Looks good, let's book!"
Apr 28, 2:00pm — AI draft sent to Ravi
Apr 27, 10:00am — Ravi WhatsApp: "Bali trip for 4 nights"
Apr 27, 9:30am — Ravi created as new customer
```

### My Questions to You:

1. **What should appear on this timeline?**
   - System events? (status change, AI analysis done)
   - Agent actions? (sent draft, added note, called)
   - Customer actions? (replied on WhatsApp, paid)
   - ALL of the above?

2. **Should it be per-customer or per-enquiry?**
   - Ravi has 3 enquiries (Bali 2025, Bali 2026, Singapore 2026) — one timeline per customer?
   - Or each enquiry has its own timeline?

3. **What's the minimum to make it useful for YOU?**
   - Just WhatsApp messages + status changes?
   - Or full activity (notes, calls, documents)?

---

## 3. Pipeline Kanban — Discussion

### What Is It?

Visual board where you drag enquiries between stages:

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ RECEIVED │ → │ ANALYZED │ → │ DRAFTING │ → │ SENT     │ → │ BOOKED   │
├──────────┤   ├──────────┤   ├──────────┤   ├──────────┤   ├──────────┤
│ Ravi     │   │          │   │ Meena    │   │ Priya    │   │          │
│ Bali     │   │          │   │ Phuket   │   │ Bali     │   │          │
├──────────┤   ├──────────┤   ├──────────┤   ├──────────┤   ├──────────┤
│ Anil     │   │          │   │          │   │          │   │          │
│ Dubai    │   │          │   │          │   │          │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### My Questions to You:

1. **What stages should be on the kanban?**
   - RECEIVED → ANALYZING → DRAFTING → SENT → NEGOTIATING → BOOKED → CANCELLED?
   - Or simpler: RECEIVED → IN PROGRESS → BOOKED?

2. **Drag to change status?** — does that feel useful or gimmicky?

3. **Should we show the kanban on the main dashboard?**

4. **What information on each card?**
   - Customer name + destination + value + days since last update?
   - Or just name + status?

---

## 4. Automated Triggers — Discussion

### What Are They?

"If X happens → automatically do Y"

| Trigger | Action | Standard CRM |
|---------|--------|--------------|
| Enquiry received → 4h no reply | Send WhatsApp reminder | ✅ Workflow |
| VIP customer starts enquiry | Send YOU alert | ✅ Workflow |
| Status → BOOKED | Generate invoice | ✅ Workflow |
| Payment confirmed | Send voucher PDF | ✅ Workflow |
| 7 days before travel | Send trip reminder | ✅ Workflow |
| Trip completed → 3 days | Send review request | ✅ Workflow |

### My Questions to You:

1. **Which triggers would YOU actually use?**
   - 4h follow-up reminder?
   - Automatic invoice on booking?
   - Pre-travel reminder to customer?

2. **Should triggers be configurable?** (like "turn on/off")
   - Via feature flags? (we have `feature_flags.md`)
   - Or hardcoded for now?

3. **Any travel-specific triggers I'm missing?**
   - Visa expiry reminder?
   - Flight schedule change → re-check?
   - Hotel payment due date?

---

## 5. Internal Notes — Discussion

### What Is It?

Private notes YOU write about a customer/enquiry:

```
Internal Note on Ravi (Bali Trip)
==================================
Date: Apr 28
Note: VIP customer (CEO of Zeta Corp). 
      Prefers WhatsApp over calls.
      Wife is vegetarian.
      DO NOT book shared transfers.
      ---Ravi
```

### My Questions to You:

1. **Per-customer notes** (about Ravi generally) or **per-enquiry notes** (about this specific Bali trip)?

2. **Should notes support:**
   - Attachments? (screenshot of conversation)
   - Tags? (#VIP, #vegetarian, #urgent)
   - Pinned notes? (always visible on top)

3. **Would you USE notes** or is WhatsApp history enough?

---

## 6. Lead Scoring / Prioritization — Discussion

### What Is It?

Score each enquiry by value/urgency so YOU know what to work on first:

```
Enquiry Priority Score
======================
Ravi - Bali     → 95/100 (VIP, ₹1.2L, replied in 2h)
Meena - Phuket  → 70/100 (New customer, ₹80k, not urgent)
Anil - Dubai    → 30/100 (Just asking, no dates, low intent)
Priya - Bali    → 85/100 (Returning, ₹90k, booking tomorrow)
```

### My Questions to You:

1. **Would this help you prioritize?** or is your volume low enough that you know already?

2. **What should determine priority?**
   - Enquiry value (₹50k+ = high)
   - Customer segment (VIP > new > one-time)
   - Days since last action (4h no reply = urgent)
   - Destination (Bali peak season = urgent)

3. **Should AI calculate the score automatically?**

---

## 7. Customer Segmentation / Lists — Discussion

### What Is It?

Group customers for marketing/referrals:

```
Segment: Bali Lovers
====================
- Ravi (been twice)
- Priya (once, loved it)
- Anil (asked but didn't book)

Segment: VIP
======
- Ravi (CEO, ₹3L+ total)
- Meena (pending large booking)

Segment: Domestic Travelers
=====================
- 15 customers who only book India trips
```

### My Questions to You:

1. **Would you ever use segments?** or is total customer count too low right now?

2. **If yes, what segments make sense for a travel agency?**
   - By destination (Bali, Dubai, Kerala)?
   - By value (VIP > ₹2L, Mid ₹50k-2L, Budget < ₹50k)?
   - By status (returning, one-time, lead)?

3. **What would you DO with a segment?**
   - Send bulk WhatsApp: "Bali special offer for past Bali travelers"?
   - Or just for reporting?

---

## Next Steps

Answer these questions, and I'll write the CRM discussion doc accordingly. Then we update the implementation roadmap with CRM features.

**Key decision needed:** Is this a CRM-first app (customer 360, kanban, triggers) or a booking-first app (enquiry → itenerary → document)?
