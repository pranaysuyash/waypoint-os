# Deals, Flash Sales & Promotions — Deal Engine

> Research document for promotional pricing, flash sales, last-minute deals, early bird discounts, personalized deal recommendations, and promotional campaign management for the Waypoint OS platform.

---

## Key Questions

1. **How do we create and manage time-limited travel deals?**
2. **What types of promotions drive the highest conversion?**
3. **How do we personalize deals for individual customers?**
4. **How do flash sales and last-minute deals integrate with supplier inventory?**

---

## Research Areas

### Deals & Promotions Engine

```typescript
interface DealsPromotionsEngine {
  // Time-limited offers, flash sales, and promotional pricing for travel products
  deal_types: {
    FLASH_SALE: {
      description: "Ultra-short duration deals (6-72 hours) at deep discounts";
      characteristics: {
        duration: "6-72 hours; countdown timer visible to customers";
        discount: "30-50% off regular price";
        inventory: "Limited inventory (5-20 seats/rooms per deal)";
        urgency: "Real-time availability counter + countdown timer";
        channels: "WhatsApp broadcast + Instagram Story + push notification";
      };
      triggers: {
        distressed_inventory: "Hotel has 10 unsold rooms for next weekend → flash sale to fill";
        supplier_promotion: "Airline offers 48-hour fare sale → agency packages with hotel";
        seasonal_push: "Monsoon season Goa deals to maintain demand in off-season";
        anniversary_sale: "Agency anniversary week — curated deals across destinations";
      };
    };

    LAST_MINUTE_DEALS: {
      description: "Departures within 7-21 days at reduced prices";
      characteristics: {
        departure_window: "7-21 days from booking to departure";
        discount: "20-40% off regular package price";
        source: "Unsold group allocations, cancelled bookings, supplier distressed inventory";
        target: "Flexible travelers, spontaneous bookers, budget-conscious customers";
      };
      mechanism: "Agency monitors unsold inventory weekly → packages into last-minute deals → broadcasts to flexible customer segment";
    };

    EARLY_BIRD: {
      description: "Discounted pricing for bookings made 60-120 days in advance";
      characteristics: {
        advance_requirement: "60-120 days before departure";
        discount: "10-20% off regular price";
        benefit: "Locks in customer early; helps agency with advance inventory commitment";
        non_refundable: "Higher cancellation penalty (early bird = commitment discount)";
      };
      use_cases: [
        "Summer holiday early bird (book by Feb for May travel)",
        "Diwali vacation early bird (book by July for Oct travel)",
        "Christmas/New Year early bird (book by Sept for Dec travel)",
        "Honeymoon season early bird (book 4 months before wedding)",
      ];
    };

    SEASONAL_PROMOTIONS: {
      description: "Campaign-based promotions aligned with Indian travel calendar";
      examples: [
        "Republic Day Sale (January long weekend trips)",
        "Summer Holiday Sale (April-May, advance bookings for June travel)",
        "Monsoon Getaway Sale (July-August, hill station and Kerala promotions)",
        "Ganesh Chaturthi Long Weekend (September)",
        "Diwali Vacation Sale (October)",
        "Christmas/New Year Sale (November-December)",
        "Valentine's Day Honeymoon Special (February)",
        "Women's Day Solo Travel Deals (March)",
        "Raksha Bandhan Sibling Trip (August)",
      ];
    };
  };

  // ── Flash sale — customer view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  ⚡ FLASH SALE · Bali Romantic Escape                     │
  // │                                                       │
  // │  🔥 45% OFF · ₹1.75L → ₹96,000/couple                   │
  // │                                                       │
  // │  ⏰ Ends in: 14h 23m 07s                                 │
  // │  🎫 Only 4 packages left                                  │
  // │                                                       │
  // │  Includes:                                            │
  // │  · Return flights ex-Delhi (Garuda Indonesia)            │
  // │  · 5 nights pool villa, Jimbaran                         │
  // │  · Daily breakfast + 2 dinners                           │
  // │  · Couple spa + candlelight dinner                       │
  // │  · Airport transfers + SIM card                          │
  // │  · Travel insurance                                      │
  // │                                                       │
  // │  Travel dates: Aug 15-20 (fixed)                      │
  // │  Non-refundable · No date changes                        │
  // │                                                       │
  // │  23 people viewing this deal                             │
  // │  Priya just booked! 🎉                                   │
  // │                                                       │
  // │  [⚡ GRAB THIS DEAL]    [Share with Friends]              │
  // └─────────────────────────────────────────────────────────┘
}
```

### Deal Personalization & Distribution

```typescript
interface DealPersonalization {
  // Matching deals to the right customers at the right time
  personalization_engine: {
    CUSTOMER_MATCHING: {
      signals: [
        "Past destinations (visited Thailand → offer Vietnam/Cambodia as next)",
        "Search history (searched Maldives 3 times → Maldives deal notification)",
        "Budget range (₹1-2L traveler → deals in that range only)",
        "Travel season (family traveler → summer holiday deals)",
        "Lifecycle stage (just returned → next trip early bird offer)",
        "Anniversary/birthday month (celebration trip deals)",
        "Wishlist destinations (saved Maldives → price drop alert)",
      ];
      scoring: "Each deal scored against customer profile; only show deals >70% match score";
    };

    SEGMENT_TARGETING: {
      segments: {
        honeymoon_couples: "Romance deals 3-6 months before peak wedding season";
        family_travelers: "Summer vacation deals during April-May school booking window";
        budget_youth: "Last-minute deals and budget destination flash sales";
        luxury_travelers: "Premium upgrades and luxury hotel flash sales";
        repeat_customers: "Loyalty-exclusive deals (early access to flash sales)";
        inactive_customers: "Re-engagement deals with extra discount for returning";
      };
    };

    OPTIMAL_TIMING: {
      description: "Send deals when customers are most likely to engage";
      patterns: {
        whatsapp: "Tuesday-Thursday 7-9 PM (post-work browsing)";
        email: "Saturday morning (weekend trip dreaming)";
        instagram: "Friday evening (weekend wanderlust)";
        push: "Lunch time 12-1 PM (casual browsing)";
      };
    };
  };

  distribution_channels: {
    WHATSAPP_BROADCAST: {
      description: "Primary deal distribution channel for Indian market";
      format: "Rich message with deal image, price, countdown, and book-now button";
      segmentation: "Broadcast lists by segment (honeymoon, family, budget, luxury)";
      frequency: "Max 2 deal broadcasts per week to avoid spam fatigue";
    };

    INSTAGRAM: {
      formats: ["Story with swipe-up link", "Reel showcasing destination", "Carousel with deal details"];
      timing: "Flash sale announcement 24h before; reminder during sale";
    };

    COMPANION_APP: {
      placement: "Deals tab on home screen; push notification for personalized deals";
      urgency: "Live countdown timer; real-time availability counter";
    };

    WEBSITE: {
      placement: "Homepage banner; dedicated deals page; exit-intent popup with last-minute deal";
    };
  };
}
```

### Deal Operations & Analytics

```typescript
interface DealOperations {
  // Managing deals from creation to post-sale analysis
  deal_lifecycle: {
    CREATION: {
      inputs: [
        "Supplier inventory (unsold rooms, seats, packages)",
        "Pricing engine (calculate margin at promotional price)",
        "Target segment (who is this deal for?)",
        "Duration (flash: 6-72h; last-minute: until departure; early bird: 30-60 days)",
        "Inventory cap (how many units available at deal price)",
      ];
      approval: "Manager approval for deals below minimum margin threshold";
    };

    DURING_SALE: {
      monitoring: [
        "Real-time booking count vs. inventory",
        "Conversion rate (views → bookings)",
        "Revenue vs. target",
        "Customer feedback/questions",
      ];
      actions: ["Extend duration if underperforming", "Boost to broader segment if inventory remaining", "Pause if overbooked"];
    };

    POST_SALE: {
      analytics: [
        "Total revenue generated vs. regular price revenue",
        "Customer acquisition (new vs. repeat customers)",
        "Margin analysis (deal price vs. cost)",
        "Channel performance (WhatsApp vs. Instagram vs. app)",
        "Conversion funnel (impressions → views → bookings)",
      ];
      learnings: "What worked, what didn't, optimal discount depth, best timing, best segment";
    };
  };

  margin_protection: {
    MINIMUM_MARGIN_RULE: {
      description: "No deal can be published below minimum margin";
      thresholds: {
        flash_sale: "Minimum 8% margin (accept lower for customer acquisition)";
        last_minute: "Minimum 5% margin (better to sell at thin margin than unsold)";
        early_bird: "Minimum 12% margin (advance commitment deserves full margin)";
        seasonal: "Minimum 10% margin (campaign pricing balanced with profitability)",
      };
    };

    LOSS_LEADER_STRATEGY: {
      description: "Occasionally run a deal at cost or slight loss for customer acquisition";
      rules: [
        "Loss leader only for NEW customers (not existing)",
        "Maximum 5% of total deals can be loss leaders",
        "Must calculate expected CLV to justify acquisition cost",
        "Track conversion from loss-leader customer to repeat customer",
      ];
    };
  };
}
```

---

## Open Problems

1. **Deal fatigue** — Too many deals too often trains customers to only book on sale. Need balance: quality deals at right frequency, not constant discounting.

2. **Cannibalization** — A 40% flash sale on Bali packages means customers who were about to book at full price now wait for deals. Smart targeting (deals only to price-sensitive segments) prevents this.

3. **Supplier relationship strain** — Repeatedly asking suppliers for flash sale inventory can strain relationships. Deals must benefit suppliers too (fill distressed inventory, increase volume).

4. **Fake urgency** — Customers are skeptical of "only 3 left!" claims. Real-time inventory counters and honest communication build trust. False scarcity destroys credibility.

5. **Margin pressure** — Promotional pricing compresses margins. The deals engine must enforce minimum margin rules and track deal profitability over time.

---

## Next Steps

- [ ] Build deals engine with flash sale, last-minute, early bird, and seasonal promotion types
- [ ] Create deal personalization engine with customer segment matching
- [ ] Implement real-time countdown timer and availability counter for flash sales
- [ ] Design WhatsApp-first deal distribution with segmented broadcast lists
- [ ] Build deal analytics dashboard with margin tracking and channel performance
- [ ] Implement minimum margin protection rules with manager approval workflow
- [ ] Create deal calendar aligned with Indian travel demand seasons
