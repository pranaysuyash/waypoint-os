# In-Trip Upsell Engine — Master Index

> Research on during-trip revenue opportunities, upgrade suggestions, and intelligent upsell timing for the Waypoint OS platform.

---

## Series Overview

This series covers the in-trip upsell engine — the system that identifies, times, and presents upgrade opportunities to travelers during active trips. From room upgrades and activity add-ons to trip extensions and dining experiences, well-timed upsells increase trip value by 5-12% while improving customer satisfaction. The engine balances revenue generation with experience protection through guardrails that prevent upsell fatigue.

**Target Audience:** Product managers, revenue managers, travel agents

**Key Insight:** In-trip upsells have 35-50% margins (higher than base bookings) and 25-35% acceptance rates when personalized and well-timed. A ₹1.2L Singapore trip generates ₹6K-15K in incremental upsell revenue — pure margin that drops directly to the bottom line. The key is timing: offer the night safari when the customer has a free evening, not when they're exhausted from a full day.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [INTRIP_UPSELL_01_ENGINE.md](INTRIP_UPSELL_01_ENGINE.md) | Upsell categories (room, activity, dining, extension, companion, insurance), trigger system (schedule, behavior, occasion, availability), customer communication channels, experience guardrails, revenue analytics |

---

## Key Themes

### 1. Relevance Is the Best Sales Pitch
An upsell that matches the customer's interest isn't selling — it's service. "I noticed your daughter loves animals — the Night Safari has a special feeding experience tomorrow" converts at 40%+ because it feels like the agent is looking out for the customer, not selling to them.

### 2. Guardrails Protect Revenue, Not Just Experience
Annoyed customers don't buy future trips. The max 2 offers/day, cooldown after rejection, and sentiment-aware throttling aren't just nice-to-haves — they prevent the short-term revenue gain of one upsell from costing the long-term revenue of a repeat customer.

### 3. Agent Delivery Beats Automated Delivery
Agent-personalized upsell suggestions convert at 2-3x the rate of automated WhatsApp messages. The AI detects the opportunity; the agent delivers it with personal context. This hybrid approach scales while maintaining the human touch.

### 4. Insurance Is the Highest-Margin Upsell
Travel insurance has 70-80% margins and is genuinely valuable to the customer. Offering coverage upgrades during the trip (when risk feels real) converts at 15-20% — higher than pre-trip insurance sales where risk feels abstract.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Traveler Companion App (TRAVELER_APP_*) | Upsell notifications in companion app |
| Trip Control Room (TRIP_CTRL_*) | Real-time trip context for upsell timing |
| AI Itinerary Generation (AI_ITINERARY_*) | Free time blocks → upsell windows |
| Revenue Architecture (REVENUE_ARCH_*) | Upsell as revenue stream |
| WhatsApp Business (WHATSAPP_BIZ_*) | Primary upsell delivery channel |
| Concierge (CONCIERGE_*) | Premium upsell for elite customers |
| Pricing Engine (PRICING_ENGINE_*) | Dynamic pricing for upsell offers |
| Agency Insurance (AGENCY_INSURE_*) | Insurance product upsells |

---

**Created:** 2026-04-30
