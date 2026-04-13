# UX Dashboards by Persona

**Date**: 2026-04-13
**Purpose**: Define different dashboard views for different user types
**Related**: `UX_AND_USER_EXPERIENCE.md` (overview), `Docs/personas_scenarios/STAKEHOLDER_MAP.md`

---

## Overview

The system serves **three primary agent personas** with different needs:

| Persona | Primary Goal | Time Spent | Dashboard Priority |
|---------|--------------|------------|-------------------|
| **P1 Solo Agent** | Close deals, manage customers | 80% customer details, 20% overview | Customer detail view |
| **P2 Agency Owner** | Oversight, quality, margins | 50% pipeline, 30% quality, 20% customer | Pipeline view |
| **P3 Junior Agent** | Learn, work independently | 60% customer details, 40% guidance | Customer detail + coaching |

All personas see the **same data**, but **different presentations and emphasis**.

---

## P1: Solo Agent Dashboard

### Design Philosophy

**The solo agent is always in customer context.** They jump from customer to customer throughout the day. Dashboard prioritizes:

1. **Quick context switching** - See all active customers at a glance
2. **Blocker visibility** - What's blocking each deal
3. **Action prompts** - What to do next for each customer
4. **Repeat customer recognition** - History at a glance

### Main View: Customer List

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY OS                                                  [New Inquiry] 🔔   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  All (23)  |  Discovery (8)  |  Shortlist (5)  |  Proposal (6)  |  Booking (4)   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MRS. SHARMA                                                  🔴 Urgent     │ │
│  │ ─────────────────────────────────────────────────────────────────────────  │ │
│  │ Europe • 5 people • June/Jul • 4-5L budget                    2 hrs ago    │ │
│  │                                                                          │ │
│  │ Repeat: Singapore 2024 (loved Gardens by the Bay)                        │ │
│  │                                                                          │ │
│  │ 🚫 2 hard blockers: Destination too broad, Party size unclear            │ │
│  │ ⚠️  Budget feasibility: TIGHT (Swiss peak season expensive)              │ │
│  │                                                                          │ │
│  │ [Send Questions] [View Details]                                          │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MR. GUPTA                                                                 🟢 Active  │ │
│  │ ─────────────────────────────────────────────────────────────────────────  │ │
│  │ Thailand • 4 people • Apr 10-15 • 3.5L budget                  Yesterday    │ │
│  │                                                                          │ │
│  │ Repeat: Dubai 2025 (liked Atlantis, complained about heat)                │ │
│  │                                                                          │ │
│  │ ✅ Ready for proposal - generating options                                │ │
│  │                                                                          │ │
│  │ [Send Proposal] [View Details]                                           │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ NEW INQUIRY: RAMESH FAMILY                                                🟡 New     │ │
│  │ ─────────────────────────────────────────────────────────────────────────  │ │
│  │ "Andaman or Sri Lanka" • 6 people • May • Budget flexible   5 mins ago    │ │
│  │                                                                          │ │
│  │ 🚫 3 hard blockers: Ambiguous destination, exact party size, dates        │ │
│  │                                                                          │ │
│  │ [Respond Now] [Snooze]                                                   │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ VERMA FAMILY TRIP                                                        🔵 Waiting │ │
│  │ ─────────────────────────────────────────────────────────────────────────  │ │
│  │ Singapore • 3 families (15 people) • Jun 15-22 • 8L total      3 days ago  │ │
│  │                                                                          │ │
│  │ ⏳ Document collection: 8/15 passports received                          │ │
│  │ ⏳ Payments: Family A (✅), Family B (⚠️ 50%), Family C (❌ 0%)          │ │
│  │                                                                          │ │
│  │ BLOCKED: Cannot proceed until documents complete                         │ │
│  │                                                                          │ │
│  │ [Send Reminders] [View Coordinator Dashboard]                            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [Load more]                                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Customer Detail View (Click into any customer)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to list                                                               │
│                                                                                  │
│  MRS. SHARMA                                    [WhatsApp] [Call] [Email]       │
│  ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  ┌──────────────────────────────────────┬──────────────────────────────────────┐│
│  │ CUSTOMER PROFILE                      │ CURRENT INQUIRY                      ││
│  ├──────────────────────────────────────┼──────────────────────────────────────┤│
│  │ Customer since: 2024                 │ Stage: Discovery                     ││
│  │ Past trips: 2                        │ Mode: Normal intake                   ││
│  │ Last contact: Feb 2024 (Singapore)   │ Confidence: 72%                      ││
│  │                                      │ Urgency: 🔴 HIGH (peak season)       ││
│  │ PREFERENCES FROM HISTORY:            │                                      ││
│  │ • Kid-friendly activities            │ REQUIREMENTS:                        ││
│  │ • Indian food important              │ • Destination: "Europe" (too broad)   ││
│  │ • Gardens by the Bay (loved)         │ • People: 5 (2 adults, 2 kids 8+12,  ││
│  │ • Complained about: Heat in Dubai    │              +1 elderly?)             ││
│  │                                      │ • Dates: June/July, 10-12 days       ││
│  │ DOCUMENT STATUS:                     │ • Budget: 4-5L                       ││
│  │ ✅ Passports: Valid till 2027        │ • Special: Snow for kids,            ││
│  │ ✅ Visas: Not required for SG        │            low walking for parents    ││
│  │                                      │                                      ││
│  └──────────────────────────────────────┴──────────────────────────────────────┘│
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ SYSTEM ANALYSIS                                                              │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ 🚫 HARD BLOCKERS (Must resolve)                                             │ │
│  │    ❌ destination_candidates: "Europe" too broad - need specific country    │ │
│  │       → Affects: Sourcing, pricing, suitability                             │ │
│  │    ❌ party_size: "5 people" - need confirmation on 5th person's age        │ │
│  │       → Affects: Room configuration, pricing, activity suitability          │ │
│  │                                                                              │ │
│  │ ⚠️  SOFT BLOCKERS (Nice to have)                                            │ │
│  │    ⚠ trip_purpose: Family vacation? Anniversary? Something else?           │ │
│  │    ⚠ budget_scope: Per person or total for family?                         │ │
│  │                                                                              │ │
│  │ 🔴 RISK FLAGS                                                               │ │
│  │    • Budget feasibility: TIGHT                                              │ │
│  │      → Stated: 4-5L | Realistic: 5-6.5L for Switzerland peak season         │ │
│  │    • Urgency: HIGH                                                          │ │
│  │      → Peak season, options booking fast                                    │ │
│  │    • Composition risk: ADVISORY                                             │ │
│  │      → Elderly + kids = need balanced itinerary, not packed schedule        │ │
│  │                                                                              │ │
│  │ ▶ RECOMMENDED ACTION: ASK_FOLLOWUP                                         │ │
│  │    Rationale: Clear destination and party ambiguity before researching     │ │
│  │    Estimated time to proposal: 1 day after blockers cleared                │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ SUGGESTED QUESTIONS (Copy to WhatsApp)                                     │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ "Hi Mrs. Sharma! Great to hear from you. I remember your family loved     │ │
│  │  Gardens by the Bay.                                                        │ │
│  │                                                                              │ │
│  │  For the Europe trip, quick questions:                                      │ │
│  │  1. Is the 5th person a grandparent? (affects hotel accessibility)         │ │
│  │  2. When you say 'snow' - see mountains or actually play in snow?         │ │
│  │     (Switzerland has both but very different budgets)                      │ │
│  │  3. Is 4-5L per person or total for the family?                            │ │
│  │                                                                              │ │
│  │  June/July is peak season, so good options book fast! 😊"                  │ │
│  │                                                                              │ │
│  │  [Copy] [Edit] [Send via WhatsApp]                                         │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ INTERNAL NOTES (Agent only - never shared)                                 │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ DESTINATION OPTIONS:                                                         │ │
│  │ • Switzerland: Best for snow, but 5-6.5L realistic budget needed            │ │
│  │ • Paris: Good mix, less walking than Swiss cities                          │ │
│  │ • Amsterdam: Flat (great for elderly), but less "snow" guarantee           │ │
│  │                                                                              │ │
│  │ PRICING CONSIDERATIONS:                                                      │ │
│  │ • If budget is firm at 5L, consider Andaman (similar beach vibe, domestic)  │ │
│  │ • Past pattern: Willing to stretch for right option (2.5L → 2.8L for SG)    │ │
│  │                                                                              │ │
│  │ SUITABILITY NOTES:                                                           │ │
│  │ • Kids 8+12: Old enough for Swiss activities, good age                      │ │
│  │ • Elderly: Need lifts, less walking, accessible rooms                       │ │
│  │ • Snow in July: Only at high altitudes (Titlis, Jungfraujoch)              │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [Mark blockers resolved] [Update budget] [Add notes]                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Proposal View (When ready to send)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to customer details                                                     │
│                                                                                  │
│  PROPOSAL: MRS. SHARMA - SWITZERLAND                                            │
│  ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ TRAVELER-FACING PREVIEW (What she'll see)                                  │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ "Hi Mrs. Sharma! Here are 3 Switzerland options for your family:            │ │
│  │                                                                              │ │
│  │ 🥉 BUDGET (₹5.2L)                                                           │ │
│  │ • Interlaken: 3-star hotel, Swiss Travel Pass                              │ │
│  │ • Great for: First-time Switzerland visitors                                │ │
│  │ • Trade-off: More walking, simpler hotels                                   │ │
│  │                                                                              │ │
│  │ 🥈 RECOMMENDED (₹6.8L) ⭐                                                    │ │
│  │ • Lucerne: 4-star with lifts, less walking for elderly                     │ │
│  │ • Includes: Mount Titlis (guaranteed snow), lake cruise                     │ │
│  │ • Why this price: Peak season + accessible hotels = premium                 │ │
│  │                                                                              │ │
│  │ 🥇 LUXURY (₹9.5L)                                                            │ │
│  │ • Zermatt: 5-star car-free village, Matterhorn views                       │ │
│  │ • Best for: Once-in-a-lifetime experience                                   │ │
│  │                                                                              │ │
│  │ All options include: flights from Mumbai, breakfast, Swiss Travel Pass,     │ │
│  │ travel insurance.                                                           │ │
│  │                                                                              │ │
│  │ I can hold Option 2 for 24 hours while you decide."                         │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ INTERNAL BREAKDOWN (Agent only)                                             │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ OPTION 1 (₹5.2L):                                                           │ │
│  │ • Margin: ₹52K (10%) - Within acceptable range                             │ │
│  │ • Sourcing: Preferred supplier (Hotel ABC)                                  │ │
│  │ • Risk: More walking than ideal for elderly                                 │ │
│  │                                                                              │ │
│  │ OPTION 2 (₹6.8L) ⭐ RECOMMENDED:                                            │ │
│  │ • Margin: ₹68K (10%) - Good margin                                          │ │
│  │ • Sourcing: Preferred supplier (Hotel XYZ)                                  │ │
│  │ • Risk: Low - best fit for family composition                              │ │
│  │ • Past success: Used for 3 similar families, all positive feedback          │ │
│  │                                                                              │ │
│  │ OPTION 3 (₹9.5L):                                                           │ │
│  │ • Margin: ₹1.4L (15%) - Excellent margin                                    │ │
│  │ • Sourcing: Network supplier (high-end)                                    │ │
│  │ • Risk: Budget stretch - may be beyond their comfort                       │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [Edit proposal] [Add custom option] [Send via WhatsApp] [Send via Email]       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## P2: Agency Owner Dashboard

### Design Philosophy

**The agency owner needs visibility, not details.** They're managing multiple agents and worried about:

1. **Pipeline health** - What's in the funnel?
2. **Quality control** - Are agents doing good work?
3. **Margin protection** - Are we giving away money?
4. **Agent performance** - Who needs help?

Dashboard prioritizes **aggregate views** and **exception alerts**.

### Main View: Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY OS - OWNER DASHBOARD                                      [This Month ▼]│
├─────────────────────────────────────────────────────────────────────────────────┤
│  Pipeline  |  Agents  |  Margins  |  Quality  |  Settings                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ PIPELINE SNAPSHOT                                                            ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                              ││
│  │  Discovery (8)  →  Shortlist (5)  →  Proposal (6)  →  Booking (4)  →  Done ││
│  │  ────────────     ─────────────     ────────────     ────────────     ┌───┐││
│  │  █████████        ██████           ████████         █████         █████│││
│  │     8               5                 6                4           12   ││
│  │                                                                              ││
│  │  Total pipeline value: ₹42.5L  |  Weighted (by stage): ₹18.2L                   ││
│  │  This month bookings: ₹12.8L (4 trips)  |  Last month: ₹15.2L (5 trips)       ││
│  │                                                                              ││
│  │  📊 Conversion rate: 23% (5/23 inquiries → booking)  |  Target: 25%            ││
│  │                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌───────────────────────┬───────────────────────┬─────────────────────────────┐│
│  │ ⚠️ ALERTS (5)          │ 👥 AGENT PERFORMANCE   │ 💰 MARGINS                  ││
│  ├───────────────────────┼───────────────────────┼─────────────────────────────┤│
│  │                       │                       │                             ││
│  │ 🔴 Margin risk (2):   │ Priya       8 deals   │ Average margin: 9.8%       ││
│  │ • Dubai trip < 5%     │ ━━━━━━━━━━ 80%       │ Target: 10%                ││
│  │   (Rahul's quote)     │                       │                             ││
│  │ • Maldives 3%         │ Amit        5 deals   │ This month breakdown:      ││
│  │   (new agent error)   │ ━━━━━━━ 50%           │  • 12-15%: 8 trips ✓       ││
│  │                       │                       │  • 8-12%:  5 trips ✓       ││
│  │ 🟡 Quality issues (2):│ New Agent  2 deals    │  • <8%:    2 trips ⚠️      ││
│  │ • No docs collected   │ ━━━ 20%               │                             ││
│  │   (Amit - 3x)         │                       │ Lowest this month:         │
│  │ • Budget reality not  │ Training mode:        │  Dubai (Rahul) - 4.2%      ││
│  │   set (new agent)     │  2 agents active      │  Maldives (New) - 3.1%     ││
│  │                       │                       │                             ││
│  │ 🟢 Ghost customers    │                       │                             ││
│  │   (1): Follow up due  │ [View all agents]     │ [View margin details]      ││
│  │                       │                       │                             ││
│  │ [View all alerts]     │                       │                             ││
│  └───────────────────────┴───────────────────────┴─────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ RECENT ACTIVITY                                                              ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                              ││
│  │  Today, 3:45 PM  │  Priya  │  New inquiry  │  Mrs. Kapoor  │  Europe      ││
│  │  Today, 2:15 PM  │  Amit   │  Proposal     │  Mr. Sharma   │  Thailand    ││
│  │  Today, 11:30 AM │  Priya  │  Booking      │  Verma Family │  Singapore   ││
│  │  Yesterday      │  Rahul  │  Lost lead    │  R. Reddy     │  Dubai       ││
│  │                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Quality Review View (Click into any deal)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to pipeline                                                             │
│                                                                                  │
│  QUALITY REVIEW: MR. MEHTA - DUBAI TRIP                               [Rahul]  │
│  ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ QUOTE QUALITY SCORE: 72/100 ⚠️                                              │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ ✅ PASSING:                                                                 │ │
│  │    • Customer history retrieved (repeat customer)                           │ │
│  │    • Budget reality check performed                                         │ │
│  │    • Document status verified                                               │ │
│  │    • Proposal includes 3 options with clear rationale                       │ │
│  │                                                                              │ │
│  │ ⚠️ NEEDS ATTENTION:                                                         │ │
│  │    • Margin: 4.2% (below 5% threshold)                                       │ │
│  │      → Quote: ₹2.4L | Cost: ₹2.3L | Margin: ₹10K                            │ │
│  │      → Recommendation: Increase price or find cheaper sourcing              │ │
│  │    • Sourcing: Open market (no preferred supplier available)                │ │
│  │      → Higher cost basis, lower margin                                      │ │
│  │    • No follow-up questions asked (ambiguity in party size unresolved)      │ │
│  │                                                                              │ │
│  │ ❌ FAILING:                                                                  │ │
│  │    • Budget feasibility not documented (customer said "flexible" -          │ │
│  │      agent should have set expectations before quoting)                     │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ AGENT NOTES (What Rahul was thinking)                                      │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ "Customer is price-sensitive (compared with MMT). Gave thin margin to       │ │
│  │  close the deal. Preferred supplier doesn't have Dubai inventory for       │ │
│  │  these dates, had to use open market."                                      │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ OWNER ACTIONS                                                                │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  [Approve as-is] [Request revision] [Discuss with agent] [Block low margin] │ │
│  │                                                                              │ │
│  │  Feedback to agent (will be shown next time they quote < 5% margin):        │ │
│  │  ┌──────────────────────────────────────────────────────────────────────┐   │ │
│  │  │ "This quote is below our 5% margin threshold. Before sending:        │   │ │
│  │  │  1. Can you find a cheaper sourcing option?                          │   │ │
│  │  │  2. Is this customer truly price-sensitive or just comparison         │   │ │
│  │  │     shopping?                                                         │   │ │
│  │  │  3. If margin can't be improved, get owner approval before           │   │ │
│  │  │     sending."                                                         │   │ │
│  │  └──────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Performance View

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to pipeline                                                             │
│                                                                                  │
│  AGENT PERFORMANCE: RAHUL                                              This Month│
│  ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ METRICS                                                                      │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  Deals handled: 8                 Team average: 7.5                         │ │
│  │  Conversion rate: 25% (2/8)       Team average: 23%                         │ │
│  │  Average margin: 7.8%             Team average: 9.8%  ⚠️ Below average       │ │
│  │  Response time: 2.3 hrs avg       Team average: 3.1 hrs  ✓ Fast             │ │
│  │  Quality score: 68/100            Team average: 75/100  ⚠️ Below average    │ │
│  │  Customer satisfaction: 4.2/5     Team average: 4.5/5                        │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ STRENGTHS                                                                    │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  ✓ Fast response time - customers appreciate quick replies                  │ │
│  │  ✓ Good at building rapport - repeat customers rate him highly              │ │
│  │  ✓ Strong destination knowledge - especially Europe                         │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ AREAS FOR IMPROVEMENT                                                        │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  ⚠️ Margin compression - 3 quotes below 5% margin this month                  │ │
│  │     → Recommendation: Use system's margin warnings before quoting            │ │
│  │                                                                              │ │
│  │  ⚠️ Budget reality checks - 2 quotes sent without feasibility discussion    │ │
│  │     → Recommendation: Always run feasibility check before proposal           │ │
│  │                                                                              │ │
│  │  ⚠️ Document collection - 1 booking delayed due to missing docs              │ │
│  │     → Recommendation: Use automated document reminders                      │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ RECENT DEALS                                                                 │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  Mehta - Dubai    │  Margin: 4.2%  │  Quality: 72/100  │  Status: Quoted    │ │
│  │  Kapoor - Europe  │  Margin: 11.5% │  Quality: 82/100  │  Status: Booked    │ │
│  │  Singh - Maldives │  Margin: 8.3%  │  Quality: 78/100  │  Status: Lost      │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [View all deals] [Send feedback] [Schedule coaching session]                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## P3: Junior Agent Dashboard

### Design Philosophy

**The junior agent needs guidance, not just data.** They're learning and afraid of making mistakes. Dashboard prioritizes:

1. **Confidence indicators** - "Is this okay to send?"
2. **Explanations** - "Why is this recommended?"
3. **Guardrails** - "Don't forget X"
4. **Escalation paths** - "When to ask senior"

Same data as P1, but **more explicit guidance**.

### Customer Detail View (Junior Agent - Enhanced Guidance)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  TRAINING MODE: ON                                                              │
│  ← Back to list       [Ask senior] [Help]                                       │
│                                                                                  │
│  MRS. SHARMA                                                                   │
│  ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ WHAT YOU SEE (Same as solo agent)                                           │ │
│  │ [Standard customer profile, inquiry details, blockers, risk flags]          │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ COACHING: WHAT TO PAY ATTENTION TO                                          │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ 💡 TRAP ALERT: Budget Reality                                               │ │
│  │    Customer says 4-5L. For Switzerland in June with 5 people, this is      │ │
│  │    TIGHT. Don't quote without setting expectations first!                   │ │
│  │    → Before sending proposal, say: "Switzerland in peak season is          │ │
│  │      premium. Realistic budget is 5-6.5L. Should I proceed or adjust        │ │
│  │      destination?"                                                          │ │
│  │                                                                              │ │
│  │ 💡 TRAP ALERT: Elderly Mobility                                              │ │
│  │    "Parents can't walk too much" = Need hotels with lifts, less            │ │
│  │    walking itineraries. Don't quote hotels without elevators!               │ │
│  │    → Look for: "Accessible", "Lift", "Ground floor" in hotel amenities      │ │
│  │                                                                              │ │
│  │ 💡 LEARNING OPPORTUNITY: Repeat Customer                                     │ │
│  │    She's been to Singapore with you before. Use this!                       │ │
│  │    → Mention: "I remember you loved Gardens by the Bay"                     │ │
│  │    → Pattern: She stretched budget last time (2.5L→2.8L), so might          │ │
│  │      again if you show value                                                 │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ CONFIDENCE CHECKLIST (All must pass before sending)                         │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  ☐ Destination clarified? (Currently: "Europe" - too broad)                 │ │
│  │  ☐ Party size confirmed? (Currently: 5 people - need ages)                  │ │
│  │  ☐ Budget scope confirmed? (Per person or total?)                           │ │
│  │  ☐ Budget reality check done? (If you quote Switzerland at 5L, will         │ │
│  │       she be shocked or is this expected?)                                  │ │
│  │  ☐ Special requirements noted? (Snow for kids, low walking for elderly)     │ │
│  │                                                                              │ │
│  │  CONFIDENCE SCORE: 45/100 - NOT READY TO SEND PROPOSAL                      │ │
│  │  → Clear the blockers above before generating options                        │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ SUGGESTED QUESTIONS (With explanations)                                     │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │ 1. "Is the 5th person a grandparent?"                                       │ │
│  │    WHY: Affects room configuration (connecting rooms vs. separate) and     │ │
│  │         activity suitability (elderly mobility)                            │ │
│  │                                                                              │ │
│  │ 2. "When you say 'snow' - see mountains or actually play in snow?"         │ │
│  │    WHY: "See mountains" = many options, cheaper. "Play in snow" = only     │ │
│  │         high Alps (Titlis, Zermatt), more expensive                        │ │
│  │                                                                              │ │
│  │ 3. "Is 4-5L per person or total for the family?"                            │ │
│  │    WHY: Total = ₹25K/person (doable). Per person = ₹5L/person (luxury).     │ │
│  │         BIG difference for what you should quote!                          │ │
│  │                                                                              │ │
│  │  [Copy all] [Edit] [Send via WhatsApp]                                     │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ WHEN TO ESCALATE                                                             │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  Ask senior agent if:                                                        │ │
│  │  • Customer insists on budget below feasibility (after you've explained)    │ │
│  │  • Complex visa requirements (China, Schengen for certain nationalities)    │ │
│  │  • Multi-party payment disputes (families arguing about money)              │ │
│  │  • Anything you're unsure about (no penalty for asking!)                    │ │
│  │                                                                              │ │
│  │  [Chat with senior] [Request review]                                        │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Proposal View (Junior Agent - Enhanced Review)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to customer details                                                     │
│                                                                                  │
│  PROPOSAL: MRS. SHARMA - SWITZERLAND                                            │
│  ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ PROPOSAL REVIEW CHECKLIST                                                   │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  ☐ All hotels have elevators? (Critical for elderly)                       │ │
│  │     → Check each hotel's amenities before sending                           │ │
│  │                                                                              │ │
│  │  ☐ Snow activities guaranteed? (Kids want snow)                             │ │
│  │     → July snow only at high altitudes (Titlis 3000m+, Jungfraujoch)        │ │
│  │     → Make sure at least one included option has guaranteed snow            │ │
│  │                                                                              │ │
│  │  ☐ Walking levels appropriate? (Parents can't walk much)                    │ │
│  │     → Lucerne better than Interlaken (flatter, less walking)                │ │
│  │     → Consider explaining this in the proposal                              │ │
│  │                                                                              │ │
│  │  ☐ Budget explained? (Prevent sticker shock)                                │ │
│  │     → "Switzerland in June/July is peak season - this affects pricing"      │ │
│  │     → Mention what makes it worth it                                        │ │
│  │                                                                              │ │
│  │  ☐ Margin acceptable? (Minimum 5%)                                          │ │
│  │     → Option 1: 10% ✓    Option 2: 10% ✓    Option 3: 15% ✓                 │ │
│  │                                                                              │ │
│  │  CHECKLIST SCORE: 3/5 COMPLETE                                              │ │
│  │  → Fix: Verify hotel elevators, confirm snow activities, explain budget     │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ COMMON MISTAKES TO AVOID                                                    │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  ❌ Don't promise snow without checking elevation - some Swiss towns        │ │
│  │     have no snow in July!                                                   │ │
│  │                                                                              │ │
│  │  ❌ Don't quote hotels without checking mobility access - many Swiss        │ │
│  │     old town hotels have stairs/no lifts                                     │ │
│  │                                                                              │ │
│  │  ❌ Don't send proposal without budget reality check - if 5L is tight,      │ │
│  │     say so before they see the quote                                        │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [I've fixed everything - Ready to send] [Still need help - Ask senior]        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Shared Components

### Coordinator Dashboard (Multi-Party Trips)

Available to P1 and P3 when `sub_groups` detected:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  GROUP TRIP: VERMA FAMILY + 2 OTHER FAMILIES                                   │
│  ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MASTER ITINERARY: ✅ Ready (Singapore, Jun 15-22)                          │ │
│  │ Total budget: ₹8L | Total people: 15                                       │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ FAMILY A (VERMA) - Coordinator: Mrs. Verma                STATUS: ✅ Ready  │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │  4 people  |  Budget: ₹3L  |  Rooms: Connecting (requested)               │ │
│  │                                                                              │ │
│  │  💰 Payments: ✅ Paid in full                                               │ │
│  │  📄 Documents: ✅ All passports received                                     │ │
│  │  📝 Special: "Vegetarian food, Jain options for mother"                     │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ FAMILY B (KUMAR) - Coordinator: Mr. Kumar                 STATUS: ⚠️ Pending │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │  3 people  |  Budget: ₹2.5L  |  Rooms: 1 Deluxe                            │ │
│  │                                                                              │ │
│  │  💰 Payments: ⚠️ Installment 2/3 (₹83K due Mar 1)                           │ │
│  │  📄 Documents: ⚠️ Missing 1 child passport (reminder sent Feb 18)           │ │
│  │  📝 Special: "Adventure activities, nightlife"                              │ │
│  │                                                                              │ │
│  │  [Send payment reminder] [Send document reminder]                           │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ FAMILY C (SHAH) - Coordinator: Mrs. Shah                   STATUS: ❌ Blocked │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │  4 people  |  Budget: ₹2.5L  |  Rooms: 2 Interconnecting                  │ │
│  │                                                                              │ │
│  │  💰 Payments: ⏳ 50% paid (₹1.25L due Mar 1)                                 │ │
│  │  📄 Documents: ❌ None submitted (First reminder Feb 18, no response)        │ │
│  │  📝 Special: "Kids have never flown - need window seats"                    │ │
│  │                                                                              │ │
│  │  ACTION NEEDED: Escalate to main coordinator (Mrs. Verma)                    │ │
│  │  [Call coordinator] [Send escalation message]                               │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ BOOKING READINESS                                                            │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                              │ │
│  │  Overall: 7/11 documents (64%) - BLOCKED                                    │ │
│  │  Payments: ₹4.5L/₹8L collected (56%)                                        │ │
│  │                                                                              │ │
│  │  🔴 CANNOT PROCEED TO BOOKING until all families submit passports           │ │
│  │  🔴 CANNOT CONFIRM HOTEL until all families pay 50% minimum                 │ │
│  │                                                                              │ │
│  │  DEADLINE: March 1 (15 days) - Risk: Peak season, hotel may sell out        │ │
│  │                                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [Bulk reminders to all] [View coordinator portal link] [Call Mrs. Verma]       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Responsive Design: Mobile vs Desktop

### Desktop (Primary)
- **Multi-column layouts** for comparison
- **Sidebars** for history and context
- **Hover states** for additional info
- **Keyboard shortcuts** for power users

### Mobile (Secondary but critical)
- **Single column** for everything
- **Swipe actions** (swipe right = mark done, swipe left = snooze)
- **Bottom navigation** (thumb-friendly)
- **One-tap WhatsApp integration** (critical)
- **Offline mode** for customer lookups

### Mobile-Specific Features

```
┌─────────────────────────────────┐
│  AGENCY OS           [New] 🔔   │
├─────────────────────────────────┤
│                                 │
│  MRS. SHARMA         🔴 Urgent  │
│  Europe • 5 people             │
│  2 blockers • 2 hrs ago        │
│                                 │
│  [WhatsApp]  → swipe for more  │
│                                 │
│  MR. GUPTA           🟢 Active │
│  Thailand • 4 people            │
│  Ready for proposal            │
│                                 │
│  [WhatsApp]  → swipe for more  │
│                                 │
└─────────────────────────────────┘
```

---

## Design Principles Summary

1. **Show, don't tell** - Use visual indicators (🔴🟢⚠️) not text labels
2. **Progressive disclosure** - Summary first, details on click
3. **Action-oriented** - Every view has clear next action
4. **Context preservation** - Never lose track of who you're working with
5. **Mobile-first messaging** - WhatsApp is primary channel
6. **Confidence signaling** - Show uncertainty clearly
7. **Learning by doing** - Junior agents learn through the system, not separate training

---

## Related Documentation

- `UX_AND_USER_EXPERIENCE.md` - Overall UX philosophy
- `UX_MESSAGE_TEMPLATES_AND_FLOWS.md` - What gets sent to travelers
- `Docs/personas_scenarios/STAKEHOLDER_MAP.md` - Persona definitions
- `specs/canonical_packet.schema.json` - Data structure behind all views
