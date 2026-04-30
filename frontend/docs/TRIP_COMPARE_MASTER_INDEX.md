# Trip Comparison Engine — Master Index

> Research on side-by-side itinerary comparison, proposal comparison tools, decision support aids, co-decision sharing, and comparison-driven booking conversion for the Waypoint OS platform.

---

## Series Overview

This series covers the trip comparison engine — the tool that helps customers make confident decisions when choosing between 2-3 travel options. From side-by-side pricing breakdowns and hotel photo comparisons to recommendation tags ("Best for Honeymoon") and personalized match scores, the comparison engine is the critical bridge between proposal and booking. It's the most important UX in the sales funnel: the moment of decision where comparison clarity wins the booking and confusion loses it.

**Target Audience:** Product managers, UX designers, agents

**Key Insight:** The average customer spends 4-7 days comparing proposals before booking. A clear, visual side-by-side comparison that highlights differences and provides recommendation tags reduces this to 1-2 days. Every day of decision delay is a day the customer might choose a competitor. The comparison tool is not a nice-to-have — it's the conversion mechanism.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [TRIP_COMPARE_01_ENGINE.md](TRIP_COMPARE_01_ENGINE.md) | Side-by-side comparison (pricing, accommodation, activities, logistics, reviews), decision aids (recommendation tags, highlight differences, value score, match score), comparison builder for agents, co-decision sharing with voting, comparison analytics |

---

## Key Themes

### 1. Highlight Differences, Not Sameness
Customers assume proposals are mostly similar. The comparison should make the KEY differences immediately visible: "Option A has a pool villa; Option B doesn't. Option B includes 3 more activities than Option A."

### 2. Recommendation Tags Guide Decisions
"Best for Honeymoon" on Option A and "Best Value" on Option B gives customers a frame of reference. The tag answers "which one should I choose?" — the customer's most anxious question.

### 3. Mobile Comparison Must Work
Most customers view comparisons on their phone. Side-by-side tables don't work on small screens. Card-based swipe comparison with tabbed dimension navigation is the mobile-native approach.

### 4. Co-Decision Reduces Back-and-Forth
When couples or families can view and vote on the same comparison independently, the group reaches consensus faster. The agency wins the booking sooner.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Proposal (PROPOSAL_*) | Proposals feed into comparison |
| Pricing Engine (PRICING_*) | Price data for comparison |
| Accommodation Catalog (ACCOMMODATION_CATALOG_*) | Hotel data and photos |
| Destination (DESTINATION_*) | Destination-level comparison |
| CRO & Optimization (CRO_*) | Comparison page conversion optimization |
| Trip Builder (TRIP_BUILDER_*) | Itinerary assembly for proposals |
| Widget Engine (WIDGET_ENGINE_*) | Embeddable comparison widget |
| WhatsApp Business (WHATSAPP_BIZ_*) | Comparison delivery via WhatsApp |
| Honeymoon (HONEYMOON_*) | Honeymoon-specific comparison |
| Travel Wishlist (TRAVEL_WISHLIST_*) | Compare wishlisted destinations |
| Reviews (REVIEWS_*) | Review data in comparison |

---

**Created:** 2026-04-30
