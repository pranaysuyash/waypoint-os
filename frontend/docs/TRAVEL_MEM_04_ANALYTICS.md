# Travel Photography & Memories — Analytics & Engagement

> Research document for memory product analytics, customer engagement tracking, revenue optimization, and the feedback loop between memory products and trip bookings.

---

## Key Questions

1. **How do we measure memory product performance?**
2. **What engagement metrics indicate customer satisfaction?**
3. **How do memory products drive repeat bookings and referrals?**
4. **What analytics inform product improvement decisions?**

---

## Research Areas

### Memory Product Analytics Dashboard

```typescript
interface MemoryAnalytics {
  // Overall metrics
  overview: {
    period: "MONTH" | "QUARTER" | "YEAR";
    trips_with_photos: number;            // trips that uploaded photos
    total_photos_uploaded: number;
    avg_photos_per_trip: number;
    memory_books_generated: number;
    memory_books_downloaded: number;
    highlight_reels_created: number;
    physical_products_ordered: number;
    revenue_from_memory_products: number;
    revenue_per_trip_avg: number;
  };

  // Funnel metrics
  funnel: {
    photo_collection_rate: number;        // % of trips with photos uploaded
    memory_book_generation_rate: number;  // % of trips with memory books
    digital_download_rate: number;        // % of books that get downloaded
    physical_order_rate: number;          // % of books that get printed
    social_share_rate: number;            // % of trips with social content shared
  };
}

// ── Analytics dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Memory Products — Analytics Dashboard                 │
// │  April 2026                                           │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
// │  │  87  │ │ 156  │ │  43  │ │ ₹24K │               │
// │  │Trips │ │Photos│ │Books │ │Revenue│               │
// │  │w/Pho│ │Avg/  │ │Gen   │ │This  │               │
// │  │tos  │ │Trip  │ │      │ │Month │               │
// │  └──────┘ └──────┘ └──────┘ └──────┘               │
// │                                                       │
// │  Funnel:                                              │
// │  Photo uploaded  ████████████████████████ 87 (100%)  │
// │  Book generated  ██████████████         43 (49%)     │
// │  Digital download██████████             31 (36%)     │
// │  Social shared   ██████                 19 (22%)     │
// │  Physical order  ███                     6 (7%)      │
// │                                                       │
// │  Revenue breakdown:                                   │
// │  Digital books:    ₹4,650 (19%)                      │
// │  Physical books:   ₹12,000 (50%)                     │
// │  Canvas prints:    ₹5,400 (23%)                      │
// │  Video reels:      ₹1,800 (8%)                       │
// │  Total:            ₹23,850                            │
// │                                                       │
// │  [This Month ▼] [Export CSV] [Compare Periods]       │
// └─────────────────────────────────────────────────────┘
```

### Customer Engagement Tracking

```typescript
interface EngagementMetrics {
  trip_id: string;
  traveler_id: string;

  // Photo engagement
  photo_engagement: {
    photos_uploaded: number;
    upload_timing_days_post_trip: number; // how quickly they uploaded
    photos_captioned_manually: number;    // edited AI captions
    photos_shared_externally: number;     // shared outside platform
    photos_favorited: number;             // marked as favorite
    album_views: number;                  // how many times they viewed album
    last_album_view: string | null;
  };

  // Memory product engagement
  product_engagement: {
    memory_book_viewed: boolean;
    memory_book_download_count: number;
    memory_book_share_count: number;
    memory_book_view_duration_seconds: number;
    highlight_reel_played: boolean;
    highlight_reel_play_count: number;
    social_pack_downloaded: boolean;
    physical_product_ordered: boolean;
    physical_product_reorder: boolean;
  };

  // Sentiment signals
  sentiment: {
    nps_score: number | null;            // from post-trip survey
    review_mentioned_photos: boolean;    // mentioned photos in review
    referral_made: boolean;             // referred someone after trip
    repeat_booking: boolean;            // booked again after this trip
  };
}

// ── Per-customer engagement score ──
// ┌─────────────────────────────────────────────────────┐
// │  Customer Engagement Score — Memory Products           │
// │                                                       │
// │  Sharma Family (Singapore Trip, Jun 2026)             │
// │  Engagement Score: 87/100 (HIGH)                      │
// │                                                       │
// │  Photo Activity: ██████████████████████ 95/100        │
// │  • Uploaded 127 photos (within 2 days of return)      │
// │  • Viewed album 23 times over 3 months                │
// │  • Edited 8 captions manually                         │
// │  • Marked 15 photos as favorites                      │
// │                                                       │
// │  Product Engagement: ████████████████ 78/100          │
// │  • Memory book viewed 5 times                         │
// │  • Downloaded PDF twice                               │
// │  • Shared on WhatsApp (3 contacts)                    │
// │  • Did NOT order physical book                        │
// │                                                       │
// │  Sentiment: ██████████████████████████ 90/100         │
// │  • NPS: 9/10                                          │
// │  • Mentioned photos in review: "Amazing memory book!" │
// │  • Referred Gupta family (booked Kerala trip)         │
// │  • Repeat booking: Yes (Dubai Dec 2026)               │
// │                                                       │
// │  Recommendation:                                      │
// │  → Offer physical book with 20% discount              │
// │  → Include premium memory book in next trip package   │
// │  → Feature as testimonial (with consent)              │
// └─────────────────────────────────────────────────────┘
```

### Revenue Optimization

```typescript
interface RevenueOptimization {
  // Product performance by segment
  segment_performance: {
    segment: "BUDGET" | "STANDARD" | "PREMIUM" | "LUXURY" | "CORPORATE";
    avg_photos_uploaded: number;
    digital_book_conversion: number;      // % who download
    physical_book_conversion: number;     // % who order
    avg_revenue_per_trip: number;
    top_products: string[];
  }[];

  // Upsell triggers
  upsell_triggers: {
    trigger: string;
    condition: string;
    offer: string;
    expected_conversion: number;
  }[];
}

// ── Revenue optimization engine ──
// ┌─────────────────────────────────────────────────────┐
// │  Memory Products — Revenue Optimization                │
// │                                                       │
// │  Upsell Triggers (Automated):                         │
// │                                                       │
// │  Trigger 1: High photo count (>50 photos)             │
// │  Condition: Customer uploaded 50+ photos              │
// │  Offer: "Your trip has so many great photos!           │
// │          Upgrade to a 40-page premium book"            │
// │  Conversion: ~15% → avg ₹500 upsell                  │
// │                                                       │
// │  Trigger 2: Social sharing detected                   │
// │  Condition: Customer shared memory content externally  │
// │  Offer: "Your photos are getting attention!             │
// │          Get a professional highlight reel"            │
// │  Conversion: ~8% → avg ₹300 upsell                   │
// │                                                       │
// │  Trigger 3: Repeat customer                           │
// │  Condition: Customer has 2+ trips with photos          │
// │  Offer: "Compare your trips side by side!               │
// │          Get a multi-trip memory collection"           │
// │  Conversion: ~12% → avg ₹800 upsell                  │
// │                                                       │
// │  Trigger 4: Group trip (>4 travelers)                  │
// │  Condition: Shared album has multiple contributors     │
// │  Offer: "Everyone loved this trip! Order individual     │
// │          printed books for each family"                │
// │  Conversion: ~20% → avg ₹2,000 (multiple books)      │
// │                                                       │
// │  Revenue impact:                                      │
// │  Without optimization: ₹400 avg/trip                  │
// │  With optimization:   ₹620 avg/trip (+55%)           │
// │  Annual impact:       ₹264K (1200 trips × ₹220 add)  │
// └─────────────────────────────────────────────────────┘
```

### Memory-to-Booking Feedback Loop

```typescript
interface MemoryBookingLoop {
  // How memory products drive new bookings
  attribution: {
    // Direct: customer rebooks after seeing memory products
    repeat_booking_from_memory: {
      attribution_window_days: 90;
      conversion_rate: number;            // ~8% of memory book viewers
    };

    // Referral: customer shares → new customer books
    referral_from_share: {
      attribution_window_days: 60;
      conversion_rate: number;            // ~3% of social shares
    };

    // Testimonial: memory content used as marketing
    testimonial_conversion: {
      attribution_window_days: 30;
      conversion_rate: number;            // ~5% of testimonial viewers
    };
  };

  // Content marketing from memories
  content_marketing: {
    trips_with_marketable_content: number;
    consent_rate: number;                 // % who allow agency to use photos
    social_posts_generated: number;
    social_engagement_rate: number;
    leads_from_social_content: number;
  };
}

// ── Memory → Booking feedback loop ──
// ┌─────────────────────────────────────────────────────┐
// │  Memory Products → New Bookings Attribution            │
// │                                                       │
// │  Month: April 2026                                    │
// │                                                       │
// │  Attribution paths:                                   │
// │                                                       │
// │  Path 1: Memory → Repeat booking                      │
// │  43 memory books → 3 repeat bookings (7%)             │
// │  Revenue: ₹1,35,000 (avg ₹45K/trip)                  │
// │                                                       │
// │  Path 2: Memory → Referral → New booking              │
// │  19 social shares → 2 new bookings (10.5%)            │
// │  Revenue: ₹78,000 (avg ₹39K/trip)                    │
// │                                                       │
// │  Path 3: Memory → Content marketing → Lead             │
// │  8 testimonials → 15 leads → 4 bookings (26.7%)       │
// │  Revenue: ₹1,56,000 (avg ₹39K/trip)                  │
// │                                                       │
// │  Total attributed revenue: ₹3,69,000                  │
// │  Memory product direct revenue: ₹23,850               │
// │  Total ROI: ₹3,93,000 from ₹8,500 investment         │
// │  ROI multiple: 46x                                    │
// │                                                       │
// │  Key insight: Memory products are not a revenue        │
// │  line — they are a marketing engine that happens        │
// │  to generate some direct revenue too.                 │
// └─────────────────────────────────────────────────────┘
```

### Product Quality Analytics

```typescript
interface QualityMetrics {
  // AI-generated content quality
  ai_quality: {
    caption_accuracy: number;             // % rated "good" by customers
    photo_selection_satisfaction: number;  // % who kept AI selection as-is
    book_layout_rating: number;           // 1-5 star rating
    reel_engagement_rate: number;         // % of reel watched
  };

  // Customer satisfaction
  satisfaction: {
    product_nps: number;
    complaint_rate: number;
    reprint_rate: number;                 // % of physical products reprinted
    return_rate: number;                  // % of physical products returned
  };

  // Vendor quality (physical products)
  vendor_quality: {
    on_time_delivery_rate: number;
    print_quality_rating: number;         // 1-5 stars
    packaging_damage_rate: number;
    customer_complaint_rate: number;
  };
}

// ── Quality tracking ──
// ┌─────────────────────────────────────────────────────┐
// │  Product Quality — Monthly Report                      │
// │                                                       │
// │  AI Quality:                                          │
// │  Caption accuracy:     82% rated "good" or "great"   │
// │  Photo selection:      71% kept AI selection as-is    │
// │  Book layout:          4.1/5.0 average rating         │
// │  Reel completion:      68% watched full reel          │
// │                                                       │
// │  Issues flagged:                                      │
// │  • 4 trips: wrong destination detected → wrong tags   │
// │  • 2 trips: food photos misclassified as "landmark"   │
// │  • 1 trip: group photo not selected for cover         │
// │                                                       │
// │  Vendor Quality (physical products):                  │
// │  Printo:      4.2/5.0 · 96% on-time · 2% damage      │
// │  Vistaprint:  3.8/5.0 · 89% on-time · 5% damage      │
// │  Canva Print: 4.0/5.0 · 92% on-time · 3% damage      │
// │                                                       │
// │  Action items:                                        │
// │  → Improve food vs landmark classifier (12 samples)   │
// │  → Add group photo boost for cover selection          │
// │  → Review Vistaprint packaging (5% damage rate)       │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Attribution accuracy** — Tracking whether a memory product actually drove a repeat booking or referral is fuzzy. Multi-touch attribution (memory viewed + WhatsApp conversation + booking) requires careful tracking without being intrusive.

2. **AI quality measurement** — Customers rarely rate AI-generated captions. Need implicit signals (did they edit it? did they remove it?) as proxy for satisfaction.

3. **Content moderation** — User-generated photo content in social shares needs moderation. AI should flag inappropriate content before agency branding is attached.

4. **Privacy vs analytics** — Engagement tracking (album views, download counts) may conflict with privacy expectations. Need clear consent and anonymous aggregation options.

---

## Next Steps

- [ ] Build memory product analytics dashboard with funnel metrics
- [ ] Implement engagement scoring and customer segmentation
- [ ] Create automated upsell trigger system
- [ ] Design attribution tracking for memory-to-booking loop
