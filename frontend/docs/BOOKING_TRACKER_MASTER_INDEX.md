# Customer Booking Tracker — Master Index

> Research on customer-facing booking progress tracking, real-time status visualization, milestone notifications, document pipeline status, and the "pizza tracker" for travel bookings on the Waypoint OS platform.

---

## Series Overview

This series covers the customer booking tracker — the visual progress indicator that shows travelers exactly where their booking stands at every stage. From "Inquiry Received" through "Documents Collected", "Visa Processing", "Hotels Confirmed", "Tickets Issued", to "Ready to Travel", the booking tracker is the customer's window into what's happening behind the scenes. It's the Domino's pizza tracker applied to travel: instead of wondering "is anything happening?", the customer sees real-time progress with estimated completion times.

**Target Audience:** Product managers, UX designers, agents

**Key Insight:** The #1 customer complaint during the pre-trip phase isn't that things are slow — it's that things are opaque. "I paid ₹2 lakh and haven't heard anything in 5 days" creates anxiety. A booking tracker that shows "Visa application submitted — expected response by April 18" eliminates this anxiety entirely. Customers who can see progress are 60% less likely to call the agency for status updates, saving hours of agent time per booking.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [BOOKING_TRACKER_01_PROGRESS.md](BOOKING_TRACKER_01_PROGRESS.md) | Booking milestones (8 stages), visual progress bar, per-milestone notifications, document pipeline status, estimated completion dates, agent notes visibility, delay alerts, companion app integration, WhatsApp status updates |

---

## Key Themes

### 1. Visibility Eliminates Anxiety
A customer who sees "Hotel confirmed ✓ — Activity booking in progress (est. 2 days)" feels informed. A customer who sees nothing for 2 days feels ignored. Progress visibility is the simplest trust builder.

### 2. Set Expectations With Estimated Dates
Every milestone should have an estimated completion date. "Visa expected by April 18" gives the customer a specific date to watch for, instead of vague anxiety about "will I get my visa in time?"

### 3. Delay Alerts Before the Customer Asks
When a milestone is delayed (visa taking longer than expected), proactively notify the customer with an explanation and updated timeline. Proactive delay communication builds trust; reactive "we're working on it" erodes it.

### 4. Different Views for Different People
The customer sees simplified progress ("Visa processing ✓"). The agent sees detailed status ("VFS appointment completed April 12, passport submitted, tracking ID VFS-782341, expected return April 18"). One status, two views.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Traveler Companion App (TRAVELER_APP_*) | Tracker in companion app |
| Trip Control (TRIP_CTRL_*) | Agent's monitoring view (backstage) |
| WhatsApp Business (WHATSAPP_BIZ_*) | Status update notifications |
| Notification Messaging (NOTIFICATION_MESSAGING_*) | Push notifications for milestones |
| Travel Document (TRAVEL_DOC_*) | Document pipeline stages |
| Travel Preparation (TRAVEL_PREP_*) | Pre-trip readiness score |
| Proposal (PROPOSAL_*) | Proposal acceptance triggers tracker start |
| Payment Automation (PAYMENT_AUTO_*) | Payment milestones in tracker |
| Customer Portal (CUSTOMER_PORTAL_*) | Portal-based tracker view |
| Travel Ops (TRAVEL_OPS_*) | Visa processing status feed |

---

**Created:** 2026-04-30
