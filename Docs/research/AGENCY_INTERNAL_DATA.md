# Research: Agency Internal Data Assets

**Status**: 🟡 Exploration - Problem Domain Deep Dive  
**Topic ID**: 16 (New)  
**Parent**: [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)  
**Last Updated**: 2026-04-09

---

## The Insight

**Current focus**: How to process customer inputs  
**Missing focus**: What internal data do agencies ALREADY have that can:
- Reduce search space dramatically
- Improve recommendation quality
- Preserve agency margins
- Capture institutional knowledge

**The realization**: Agencies aren't starting from zero. They have:
- Preferred suppliers (hotels, airlines, guides)
- Historical patterns (what works, what doesn't)
- Hidden knowledge (not in any database, in agents' heads)
- Negotiated rates (better than public prices)

**Question**: How do we capture, structure, and USE this internal data?

---

## 1. The Preferred Supplier Network

### What It Is
Every agency has a shortlist of "go-to" suppliers they trust and have relationships with.

### Examples by Category

**Hotels**:
```
PREFERRED_HOTELS = {
    "Singapore": [
        {
            "name": "Hard Rock Sentosa",
            "why_preferred": "Kid-friendly, Indian food nearby, 15% commission",
            "best_for": ["families_with_children", "mid_budget"],
            "avoid_for": ["couples_seeking_quiet"],
            "agent_notes": "Book ocean wing, not pool wing (noise)",
            "reliability_score": 9.5,
            "last_booked": "2026-03-15",
            "avg_margin": "12%"
        },
        {
            "name": "Marina Bay Sands",
            "why_preferred": "Iconic, good for honeymooners",
            "best_for": ["luxury", "honeymoon"],
            "avoid_for": ["families_with_toddlers", "budget_conscious"],
            "agent_notes": "Infinity pool requires room key, book 3+ nights",
            "reliability_score": 9.0,
            "commission": "10%"
        }
    ]
}
```

**Airlines**:
```
PREFERRED_AIRLINES = {
    "India-Singapore": [
        {
            "carrier": "Singapore Airlines",
            "why_preferred": "Direct, reliable, vegetarian meals good",
            "best_for": ["premium", "elderly"],
            "avoid_for": ["budget_tight"],
            "margin": "5% commission",
            "reliability_score": 9.8
        },
        {
            "carrier": "IndiGo",
            "why_preferred": "Price competitive, frequent flights",
            "best_for": ["budget", "flexible_dates"],
            "avoid_for": ["comfort_first", "long_legs"],
            "margin": "3%",
            "notes": "No frills, charge extra for everything"
        }
    ]
}
```

**Local Guides/Transport**:
```
PREFERRED_VENDORS = {
    "Singapore": {
        "guide_rajesh": {
            "name": "Rajesh Kumar",
            "specialty": "Indian heritage tours",
            "languages": ["hindi", "tamil", "english"],
            "reliability": 9.5,
            "price_per_day": "₹8000",
            "agent_notes": "Elderly customers love him, very patient, knows vegetarian restaurants"
        }
    }
}
```

### How It Helps Decision Making

**Without Preferred List**:
- Customer: "Hotel in Singapore"
- System: Searches ALL 400+ hotels in Singapore
- Analysis paralysis
- May recommend hotel agency has never used

**With Preferred List**:
- Customer: "Hotel in Singapore"
- System: Considers only 8 preferred hotels
- Ranked by: customer fit, margin, reliability
- Recommendation: "Based on your family + budget, Hard Rock Sentosa is our top pick"

**Search Space Reduction**: 400 hotels → 8 hotels (98% reduction)

---

## 2. The "Tribal Knowledge" Database

### What It Is
Information that's never written down but agents know. The "moat" of experienced agencies.

### Categories

**Hotel Reality Checks**:
```
HOTEL_INSIDER_INFO = {
    "Marina Bay Sands": {
        "official_description": "Luxury 5-star, infinity pool",
        "agent_reality": [
            "Pool is crowded 9 AM - 6 PM, impossible to get chair",
            "Rooms are small for the price",
            "Breakfast is mediocre for ₹4000",
            "Casino noise reaches some rooms",
        ],
        "when_to_sell": "Couples who want the Instagram photo",
        "when_to_avoid": "Families who need space, light sleepers",
        "better_alternative": "Fullerton Bay (same area, better value)"
    },
    
    "Hotel_X_Bangkok": {
        "official": "4-star boutique, great reviews",
        "agent_reality": [
            "Construction next door until 2027",
            "Staff doesn't speak English well",
            "AC is noisy in rooms 401-410",
        ],
        "blacklist": True,
        "reason": "Too many complaints, not worth the margin"
    }
}
```

**Destination Timing**:
```
DESTINATION_INSIGHTS = {
    "Singapore": {
        "best_months": ["February", "March", "October"],
        "avoid_months": ["December"],  # Expensive, crowded
        "monsoon": "November-January (short bursts, manageable)",
        "local_events": {
            "Chinese_New_Year": "Avoid unless customer specifically wants",
            "Great_Singapore_Sale": "Good for shoppers, June-July"
        }
    }
}
```

**Activity Suitability**:
```
ACTIVITY_REALITY = {
    "Universal_Studios_Singapore": {
        "official": "Fun for all ages",
        "agent_reality": {
            "toddlers": "Wasted money - can go on 2-3 rides max",
            "elderly": "Lots of walking, minimal seating",
            "teens": "Perfect demographic",
            "budget_families": "Consider Gardens by the Bay instead (free, equally impressive)"
        },
        "wasted_spend_detector": True,
        "better_alternatives": ["Sentosa_Beach", "Gardens_by_the_Bay", "Singapore_Zoo"]
    }
}
```

### How It Helps

**The "Wasted Spend" Detection**:
- Customer: "Family of 5, Universal Studios please"
- System sees: 2 adults + 2 elderly + 1 toddler
- Tribal knowledge: USS wasted on elderly + toddler
- System flags: "High wasted spend risk - 3/5 people won't enjoy"
- Suggests: Split day (adults do USS, elderly/toddler do Gardens)

**The Reality Check**:
- Customer: "Marina Bay Sands looks amazing"
- System sees: Family with light-sleeping 6-year-old
- Tribal knowledge: "Casino noise, crowded pool"
- System suggests: "Marina Bay is iconic, but for families we prefer Hard Rock - quieter, better pool for kids"

---

## 3. Historical Booking Patterns

### What It Is
What has the agency actually booked before? What worked?

### Data Points

```
BOOKING_HISTORY_ANALYTICS = {
    "destinations": {
        "Singapore": {
            "total_bookings": 145,
            "customer_satisfaction": 4.6/5,
            "avg_budget": "₹3.2L",
            "most_common_group": "family_with_children",
            "peak_booking_months": ["November", "December", "March"],
            "most_booked_hotel": "Hard Rock Sentosa (42% of bookings)",
            "common_complaints": ["Food expensive", "Weather humid"],
            "common_praises": ["Clean", "Safe", "Kid-friendly"]
        }
    },
    
    "customer_segments": {
        "family_with_toddler": {
            "preferred_destinations": ["Singapore", "Dubai", "Malaysia"],
            "avg_trip_length": "5 nights",
            "avg_budget": "₹2.8L",
            "must_haves": ["pool", "near attractions", "kid-friendly food"],
            "conversion_rate": "65%"  # Quote to booking
        }
    }
}
```

### How It Helps

**Predictive Recommendations**:
- Customer: "Family with 4-year-old, 5 nights, ₹3L budget"
- Historical pattern: Similar families → Singapore, 5 nights, Hard Rock
- System suggests: "Families like yours loved this package: Singapore..."

**Conversion Optimization**:
- Historical data: Packages with pool + nearby attractions = 70% conversion
- Packages without = 40% conversion
- System prioritizes: Pool + proximity in recommendations

---

## 4. Margin & Commercial Data

### What It Is
Not all bookings are equally profitable. What's the real margin?

```
COMMERCIAL_INTELLIGENCE = {
    "hotels": {
        "Hard_Rock_Sentosa": {
            "public_rate": "₹12,000/night",
            "agency_net_rate": "₹10,200/night",
            "margin": "15%",
            "commission_paid": "On time, reliable",
            "upsell_opportunities": ["breakfast", "airport_transfer"]
        },
        
        "Marina_Bay_Sands": {
            "public_rate": "₹25,000/night",
            "agency_net_rate": "₹22,500/night",
            "margin": "10%",
            "commission_paid": "Delayed 60 days",
            "notes": "High revenue, low margin, slow payment"
        }
    },
    
    "optimization_rules": {
        "if_budget_conscious": "Recommend Hard Rock (better value, higher margin)",
        "if_luxury_seeking": "Recommend Marina Bay (brand prestige, lower margin but high ticket)",
        "if_family_mid_budget": "Hard Rock is sweet spot (customer happy, margin good)"
    }
}
```

### How It Helps

**Margin Preservation**:
- Customer: "What do you recommend?"
- Options A, B, C all fit
- System ranks: A (12% margin), B (8% margin), C (15% margin)
- Suggests: C first (best for agency), A second (best for customer)

**Cash Flow Management**:
- Marina Bay: 10% margin, pays in 60 days
- Hard Rock: 15% margin, pays in 15 days
- System preference: Hard Rock (better cash flow)

---

## 5. Customer Preference Memory

### What It Is
Not just booking history, but PREFERENCES learned over time.

```
CUSTOMER_PREFERENCE_PROFILE = {
    "customer_id": "sharma_family",
    
    "explicitly_stated": {
        "dietary": "strict_jain",
        "pace": "relaxed",
        "hotel_style": "resort_over_city"
    },
    
    "implicitly_learned": {
        "actually_prefers": "Hotels with pools over beach access",
        "booked_pool_hotels": "8/10 trips",
        "ignored_beach_recommendations": True,
        "willing_to_pay_more_for": "Direct flights, good breakfast"
    },
    
    "pain_points_from_past_trips": [
        {
            "trip": "Dubai_2024",
            "issue": "Hotel too far from attractions",
            "lesson": "Always prioritize location for this family"
        },
        {
            "trip": "Thailand_2023",
            "issue": "Flight had long layover",
            "lesson": "Never suggest flights with >2 hour layover"
        }
    ],
    
    "decision_maker": "Mrs. Sharma (she decides, Mr. Sharma pays)",
    "booking_pattern": "Books 3 months in advance, pays 50% upfront",
    "communication_preference": "WhatsApp, evenings after 7 PM"
}
```

### How It Helps

**Personalized Without Asking**:
- Customer: "Planning another trip"
- System knows: Jain food essential, pool required, location critical
- Quotes: Already filtered for these constraints

**Pain Point Prevention**:
- Learning: "Last time long layover was painful"
- System: Filters out all multi-stop flights
- Customer: "You remembered!"

---

## 6. Package Templates

### What It Is
Proven, repeatable packages that are operationally easy and high-converting.

```
PACKAGE_TEMPLATES = {
    "singapore_family_classic": {
        "name": "Singapore Family Classic (5 nights)",
        "target_segment": "family_with_children_5_12",
        "components": {
            "hotel": "Hard Rock Sentosa (Deluxe Room)",
            "flights": "Singapore Airlines (direct)",
            "transfers": "Private car",
            "activities": [
                "Universal Studios (Day 2)",
                "Singapore Zoo + Night Safari (Day 3)",
                "Sentosa Beach + Palawan (Day 4)"
            ]
        },
        "base_price": "₹2.8L",
        "margin": "14%",
        "conversion_rate": "75%",
        "satisfaction_score": "4.7/5",
        "ease_of_execution": "High (booked 40+ times)",
        "flexibility": "Hotel can change, activities can swap"
    },
    
    "singapore_luxury_honeymoon": {
        "target_segment": "honeymoon_couples",
        "base_price": "₹5.5L",
        "margin": "12%",
        "conversion_rate": "60%"
    }
}
```

### How It Helps

**Fast Quoting**:
- Customer: "Family of 4, Singapore, 5 nights"
- System: "Our most popular package is Singapore Family Classic..."
- Minor customization: Dates, room type
- Quote ready in 5 minutes, not 2 hours

**Operational Efficiency**:
- Same hotel, same transfers, same activities
- Agent has done it 40 times
- Less chance of mistakes
- Better vendor relationships

---

## 7. Reliability & Risk Scores

### What It Is
Not all vendors are equal. Some are reliable, some are risky.

```
VENDOR_RELIABILITY_SCORES = {
    "hotels": {
        "Hard_Rock_Sentosa": {
            "reliability_score": 9.5,
            "booking_honored_rate": "99%",
            "upgrade_frequency": "Often (loyalty program)",
            "issue_resolution": "Fast",
            "last_minitchanges": "Accommodating",
            "years_working_together": 5,
            "total_bookings": 60
        },
        
        "Hotel_Y_Bangkok": {
            "reliability_score": 6.0,
            "booking_honored_rate": "85%",
            "common_issues": ["Overbooks", "Room type changes"],
            "status": "USE_WITH_CAUTION"
        }
    },
    
    "guides": {
        "rajesh_singapore": {
            "reliability_score": 9.8,
            "show_rate": "100%",
            "customer_rating": "4.9/5",
            "issue_history": "None in 45 bookings"
        }
    }
}
```

### How It Helps

**Risk Mitigation**:
- Customer: "That hotel looks cheaper"
- System: "Hotel Y is ₹5000 cheaper but has 85% honor rate vs 99% for Hard Rock. We've had 3 issues with overbooking."
- Customer: "Hard Rock it is"

**Operational Safety**:
- High-stakes booking (honeymoon, anniversary)
- System filters: Only vendors with >9.0 reliability
- Reduces disaster risk

---

## Integration: How Internal Data Flows Through System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERNAL DATA INTEGRATION FLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CUSTOMER INPUT                    INTERNAL DATA             OUTPUT         │
│  ─────────────                     ─────────────             ───────        │
│                                                                             │
│  "Family, Singapore,              PREFERRED_HOTELS          "Based on       │
│   5 nights, ₹3L"                  Filter: family-friendly   your profile    │
│                                    + good margin            and our         │
│                                   [8 hotels]                experience      │
│                                      ↓                      with families   │
│  │                            TRIBAL_KNOWLEDGE              like yours...   │
│  │                            "Hard Rock best for          Hard Rock       │
│  │                             families"                   Sentosa"        │
│  │                                  ↓                                        │
│  │                            HISTORICAL_DATA                                │
│  │                            "Similar families                            │
│  │                             loved Hard Rock"                            │
│  │                                  ↓                                        │
│  │                            MARGIN_DATA                                    │
│  │                            "15% margin,                                  │
│  │                             reliable payment"                            │
│  │                                  ↓                                        │
│  │                            CUSTOMER_MEMORY                                │
│  │                            "They need pool,                             │
│  │                             Jain food"                                   │
│  │                                  ↓                                        │
│  └────────────────────────────────────────────────────────► FINAL           │
│                                                              RECOMMENDATION  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Capture Strategies

### How to Get This Internal Data

**1. Preferred Suppliers** (Structured)
- Agent fills form: "Top 5 hotels in Singapore"
- Rate each: Commission, reliability, notes
- Update quarterly

**2. Tribal Knowledge** (Semi-structured)
- Post-trip debrief: "What went wrong?"
- Agent notes: "Marina Bay pool crowded"
- System captures: Hotel_X.reality_check += "pool crowded"

**3. Historical Patterns** (Automatic)
- Extract from booking database
- Analytics: "What do families actually book?"
- No manual entry needed

**4. Margin Data** (Sensitive)
- Owner enters net rates (not visible to agents)
- System uses for optimization
- Kept confidential

**5. Customer Preferences** (Hybrid)
- Explicit: Customer states preferences
- Implicit: System observes behavior
- Combined: Rich preference profile

---

## Implementation Priority

### Phase 1: Quick Wins (Week 1-2)
1. **Preferred Suppliers List**
   - Simple form: "Top 10 hotels per destination"
   - Immediate 90% search space reduction
   
2. **Package Templates**
   - 5 proven packages per top destination
   - Fast quoting

### Phase 2: Learning System (Month 2-3)
3. **Historical Pattern Analytics**
   - Auto-extract from past bookings
   - "Customers like you chose..."

4. **Customer Preference Memory**
   - Track stated + observed preferences
   - "You preferred pool hotels before"

### Phase 3: Advanced (Month 4-6)
5. **Tribal Knowledge Capture**
   - Post-trip agent debriefs
   - Reality check database

6. **Margin Optimization**
   - Net rate entry (owner only)
   - Smart recommendation ranking

---

## Open Questions

- [ ] How much of this data is explicit (can be entered) vs implicit (must be learned)?
- [ ] What's the incentive for agents to share tribal knowledge?
- [ ] How do we prevent "gaming" the margin optimization?
- [ ] Should customer see why something is recommended ("Based on families like yours")?
- [ ] How often should preferred supplier lists be updated?
- [ ] What happens when a preferred supplier fails? (Reputation damage)

---

## Related Topics

- [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) - Master index
- Persona scenarios - All scenarios benefit from internal data
- DATA_STRATEGY.md - How to store this data

---

*This is an exploration doc. Add insights as they emerge.*
