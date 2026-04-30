# Travel Document Expiry Tracking — Master Index

> Research on passport expiry tracking, visa validity monitoring, driving license and ID expiry alerts, vaccination certificate management, and document-readiness booking gates for the Waypoint OS platform.

---

## Series Overview

This series covers travel document expiry tracking — the system that monitors passport validity, visa expiration, driving license status, vaccination certificates, and all other travel-critical documents to ensure travelers are never blocked at immigration because of an expired document. From pre-booking passport validity checks and Schengen 90/180 day calculators to automated renewal reminders and booking gates that prevent booking when documents are insufficient, document tracking is the compliance layer that prevents the most preventable travel disruption.

**Target Audience:** Product managers, agents, operations managers

**Key Insight:** The #1 reason Indian travelers are denied boarding is insufficient passport validity (less than 6 months remaining). A simple passport expiry alert 6 months before a planned trip prevents a catastrophic travel disruption. The agency that catches this proactively ("Your passport expires in April — your May trip needs renewal first") saves the customer from the worst travel experience possible and earns deep trust.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [DOC_EXPIRY_01_TRACKING.md](DOC_EXPIRY_01_TRACKING.md) | Passport/visa/DL/vaccination tracking, expiry alert schedule, booking-document integration (pre-booking, at-booking, pre-trip gates), renewal assistance, Schengen day calculator, family document management, OCR for document scanning |

---

## Key Themes

### 1. Catch Problems Before They Become Disasters
An expired passport discovered at the airport is a disaster. An expiring passport caught 6 months early is a simple renewal. Proactive tracking prevents the worst-case scenario.

### 2. Booking Gates Prevent Revenue Loss
Allowing a customer to book a trip they can't take (expired passport, no visa) leads to cancellation, refund processing, and customer frustration. A booking gate that checks documents upfront prevents both revenue loss and customer disappointment.

### 3. Visa Complexity Demands Automation
Schengen's 90/180 rule, US visa entry limits, UAE visa types — visa rules are complex and country-specific. Automated checking against a visa rules database prevents manual errors that could strand travelers.

### 4. Documents Are the Family's Collective Responsibility
A family trip fails if any one member's passport is insufficient. Tracking documents for all travelers in a booking (not just the primary booker) is essential for group and family travel.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Travel Document (TRAVEL_DOC_*) | Document generation and delivery |
| Customer Identity (CUSTOMER_IDENTITY_*) | KYC and identity verification |
| Travel Preparation (TRAVEL_PREP_*) | Document readiness as part of trip prep |
| Visa (VISA_*) | Visa requirements and processing |
| Trip Builder (TRIP_BUILDER_*) | Document check at booking gate |
| Insurance (INSURANCE_*) | Travel insurance policy validity |
| Companion App (TRAVELER_APP_*) | Document tracker in app |
| Identity (IDENTITY_*) | Passport data and verification |
| Group Travel (GROUP_*) | Multi-person document management |

---

**Created:** 2026-04-30
