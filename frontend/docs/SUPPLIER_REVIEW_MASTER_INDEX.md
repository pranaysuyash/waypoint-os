# Supplier Ratings & Reviews — Master Index

> Research on customer-driven supplier quality ratings, supplier scorecards, quality-driven supplier selection, and rating-informed itinerary generation for the Waypoint OS platform.

---

## Series Overview

This series covers supplier ratings and reviews — the system that captures customer feedback on hotels, activities, transport, and restaurants, then uses that data to drive supplier selection, negotiation, and quality management. Every customer rating makes the next customer's trip better: A-rated suppliers are prioritized, C-rated suppliers are monitored, and F-rated suppliers are replaced.

**Target Audience:** Operations managers, product managers, supplier managers

**Key Insight:** Agencies that systematically collect and act on supplier ratings deliver 20-30% better customer satisfaction than those that don't. A customer who stays at an A-rated hotel (4.6 stars from 89 previous travelers) has a fundamentally different experience than one who stays at a C-rated hotel (3.2 stars with recent complaints). The rating system ensures every customer gets the best available option.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [SUPPLIER_REVIEW_01_RATINGS.md](SUPPLIER_REVIEW_01_RATINGS.md) | Rating dimensions (hotel, activity, transport, restaurant), supplier scorecard with grading (A-F), rating-driven itinerary generation, quality alerts, rating collection strategy |

---

## Key Themes

### 1. Every Rating Improves the Next Trip
Customer ratings feed directly into the itinerary generation engine. A hotel that consistently scores 4.5+ gets prioritized; one that drops below 3.5 gets flagged. The system learns and improves with every trip.

### 2. Rate in the Moment, Not Weeks Later
Companion app ratings captured during the trip (right after each activity) are more accurate than retrospective surveys. The customer rates the Gardens by the Bay while still excited, not two weeks later when details have faded.

### 3. Supplier Grading Drives Business Decisions
A supplier's grade (A through F) directly affects how often they're booked, what price the agency negotiates, and whether they remain in the network. Ratings are not vanity metrics — they're operational levers.

### 4. Minimum Data Before Trust
New suppliers start with a provisional grade and need 5+ ratings before being fully trusted. Established suppliers need sustained quality to maintain their grade. No free passes.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Supplier Management (SUPPLIER_MASTER_*) | Supplier database and contracts |
| AI Itinerary Generation (AI_ITINERARY_*) | Rating-informed supplier selection |
| Post-Trip Ecosystem (POST_TRIP_*) | Post-trip feedback collection |
| Surveys & Feedback (SURVEYS_FEEDBACK_*) | Survey instrument design |
| Accommodation Catalog (ACCOMMODATION_CATALOG_*) | Hotel quality data |
| Activities (ACTIVITIES_*) | Activity provider quality data |
| Help Desk (HELP_DESK_*) | Complaint data feeds quality scores |

---

**Created:** 2026-04-30
