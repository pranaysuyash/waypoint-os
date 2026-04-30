# Social Media Marketing — Channel Strategy & Content Engine

> Research document for social media marketing strategy, Instagram/Facebook/YouTube content planning, travel content creation, influencer collaboration, and social commerce for the Waypoint OS platform.

---

## Key Questions

1. **How does a travel agency use social media for customer acquisition?**
2. **What content types drive engagement and bookings?**
3. **How does social commerce convert followers to customers?**
4. **What are the platform-specific strategies for travel content?**

---

## Research Areas

### Social Media Marketing Architecture

```typescript
interface SocialMediaMarketing {
  // Social media strategy for travel agency customer acquisition
  channel_strategy: {
    INSTAGRAM: {
      role: "Primary visual inspiration + destination awareness channel";
      audience: "25-45 age group, couples and families planning travel";
      content_types: {
        REELS: {
          format: "15-60 second short videos";
          content: ["Destination walkthroughs", "Trip recap montages", "Travel tips", "Behind-the-scenes at agency"];
          frequency: "4-5 per week";
          target_metrics: "Views: 5K-50K · Save rate: 3%+ · Share rate: 1%+";
        };
        CAROUSELS: {
          format: "5-10 slide image posts";
          content: ["'5 things to do in Singapore'", "Itinerary highlights", "Before/after trip transformation", "Packing guides"];
          frequency: "3-4 per week";
          target_metrics: "Save rate: 5%+ (educational content gets saved)";
        };
        STORIES: {
          format: "24-hour ephemeral content";
          content: ["Daily travel tips", "Customer trip updates (with permission)", "Flash deals", "Polls and Q&A"];
          frequency: "Daily — 3-5 stories per day";
          target_metrics: "Completion rate: 70%+ · Reply rate: 2%+";
        };
        LIVE: {
          format: "Live video broadcasts";
          content: ["Destination walkthroughs with agent", "Q&A sessions", "Customer trip live from destination"];
          frequency: "Weekly or biweekly";
        };
      };
      conversion_path: "Post → DM inquiry → WhatsApp handoff → Booking";
    };

    FACEBOOK: {
      role: "Community building + older demographic reach + ad targeting";
      audience: "35-55 age group, families, decision-makers with higher spending power";
      content_types: {
        posts: "Detailed trip descriptions with pricing; customer reviews; travel tips";
        groups: "'Waypoint Travel Community' — customer-only group for trip photos, tips, questions";
        ads: "Lead generation ads targeting specific demographics and interests";
        events: "Trip information sessions, travel webinars";
      };
      conversion_path: "Ad/Post → Landing page → Inquiry form → Agent callback";
    };

    YOUTUBE: {
      role: "Long-form destination content + SEO-driven discovery";
      audience: "All ages researching destinations before booking";
      content_types: {
        DESTINATION_GUIDES: {
          format: "5-15 minute destination walkthrough videos";
          content: "'Complete Singapore Travel Guide 2026 — Everything You Need to Know'";
          seo_value: "Ranks for 'Singapore travel guide', 'Singapore trip planning' searches";
        };
        TRIP_VLOGS: {
          format: "3-8 minute trip experience videos";
          content: "Agent or customer-trip vlog showing actual experience";
        };
        SHORTS: {
          format: "Under 60 seconds — YouTube's answer to Reels";
          content: "Quick tips, destination teasers, surprising facts";
        };
      };
      conversion_path: "Video → Description link → Website → Inquiry";
    };

    LINKEDIN: {
      role: "Corporate travel + B2B partnerships + employer branding";
      audience: "Corporate travel managers, HR heads, business owners";
      content: "Corporate travel packages, MICE offerings, company culture posts";
      conversion_path: "Post → DM → Corporate travel consultation";
    };
  };

  // ── Social media content calendar ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Social Content Calendar · Week of May 5               │
  // │                                                       │
  // │  Mon  Tue  Wed  Thu  Fri  Sat  Sun                     │
  // │  ───  ───  ───  ───  ───  ───  ───                   │
  // │  📱R  📋C  📱R  📱R  📋C  📱R  📹YT                  │
  // │  SG   BKK  DXB   SG   Tips  MLE  Guide               │
  // │                                                       │
  // │  R = Reel  C = Carousel  YT = YouTube                  │
  // │                                                       │
  // │  Scheduled Posts:                                     │
  // │  Mon: Reel "3 days in Singapore under ₹60K"              │
  // │  Tue: Carousel "10 things Indians don't know about BKK"  │
  // │  Wed: Reel "Dubai on a budget — ₹45K for 4 days"        │
  // │  Thu: Reel "Sentosa Island walkthrough"                   │
  // │  Fri: Carousel "Packing mistakes every traveler makes"    │
  // │  Sat: Reel "Maldives vs Bali — which for you?"            │
  // │  Sun: YouTube "Singapore 2026 Complete Guide"             │
  // │                                                       │
  // │  Stories: Daily tips + customer trip update               │
  // │  Live: Wednesday 7 PM — Singapore Q&A with Priya         │
  // │                                                       │
  // │  Performance (last 7 days):                            │
  // │  Reach: 12.4K · Engagement: 8.2% · DM inquiries: 23      │
  // │  Bookings from social: 4 · Revenue: ₹4.8L                │
  // │                                                       │
  // │  [Schedule Post] [Content Ideas] [Analytics]              │
  // └─────────────────────────────────────────────────────────┘
}
```

### Content Creation Engine

```typescript
interface ContentCreationEngine {
  // Systematic travel content creation
  content_pillars: {
    DESTINATION_CONTENT: {
      weight: "40% of content";
      types: [
        "Destination guides (comprehensive, SEO-optimized)",
        "Hidden gems and offbeat recommendations",
        "Seasonal destination spotlights ('Best places to visit in June')",
        "Destination comparison ('Singapore vs Bangkok for families')",
      ];
    };

    SOCIAL_PROOF: {
      weight: "25% of content";
      types: [
        "Customer trip photos (with permission and tagging)",
        "Testimonial graphics ('Mr. Sharma loved his Singapore trip!')",
        "Live trip updates from customers",
        "Customer count milestones ('500+ happy travelers!')",
      ];
    };

    EDUCATIONAL: {
      weight: "20% of content";
      types: [
        "Travel tips (packing, visa, currency, insurance)",
        "How-to guides ('How to plan your first international trip')",
        "Myth busting ('5 myths about travel agencies')",
        "Budget guides ('Singapore for ₹60K — is it possible?')",
      ];
    };

    PROMOTIONAL: {
      weight: "15% of content";
      types: [
        "Limited-time offers and flash deals",
        "Early-bird campaign announcements",
        "New destination or package launches",
        "Festival and holiday season deals",
      ];
    };
  };

  content_workflow: {
    PLANNING: {
      frequency: "Monthly content calendar planned 2 weeks in advance";
      batch_creation: "Shoot/edit 10-15 pieces of content in one session";
      destination_rotation: "Feature 3-4 destinations per month in rotation";
    };

    CREATION: {
      agent_content: "Agents create authentic, personal content during trip planning and site visits";
      customer_content: "Customer-generated content (trip photos, reviews) with consent and credit";
      stock_enhancement: "Stock footage/images enhanced with agency-specific overlays and branding";
    };

    REPURPOSING: {
      strategies: [
        "YouTube guide → 3 Reels extracted",
        "Customer testimonial → Instagram story + carousel + WhatsApp broadcast",
        "Destination photo → Pinterest pin + Instagram post + Facebook cover",
        "Blog post → Email newsletter + carousel summary + YouTube script",
      ];
    };
  };
}
```

### Social Commerce & Conversion

```typescript
interface SocialCommerce {
  // Converting social media followers to bookings
  conversion_funnel: {
    AWARENESS: {
      channel: "Instagram Reels, YouTube Shorts, Facebook Reach ads";
      metric: "Impressions and reach";
      goal: "Get travel inspiration in front of potential customers";
    };

    CONSIDERATION: {
      channel: "Carousel posts, YouTube guides, Stories with destination details";
      metric: "Saves, shares, comments, profile visits";
      goal: "Establish agency as the expert for this destination";
    };

    INTENT: {
      channel: "DM conversations, WhatsApp handoff, link clicks";
      metric: "DM inquiries, link clicks, landing page visits";
      goal: "Move from social media to direct conversation with agent";
    };

    CONVERSION: {
      channel: "WhatsApp chat with agent → booking proposal → payment";
      metric: "Bookings attributed to social media channel";
      goal: "Convert inquiry to confirmed booking";
    };
  };

  dm_to_booking_workflow: {
    step_1: "Customer DMs: 'How much for Singapore in June?'";
    step_2: "Auto-reply: 'Thanks! Moving to WhatsApp for faster response → [link]'";
    step_3: "WhatsApp: Agent greets + asks qualifying questions";
    step_4: "Proposal sent via WhatsApp within 24 hours";
    step_5: "Follow-up sequence if no immediate response";
    attribution: "UTM tracking from social DM → WhatsApp → booking";
  };

  paid_social: {
    INSTAGRAM_ADS: {
      objective: "Lead generation for destination-specific campaigns";
      targeting: {
        demographic: "Age 25-50, household income ₹10L+, married, parents";
        interest: "Travel, specific destinations, travel photography, airlines";
        lookalike: "Similar to existing customers who booked";
        retargeting: "Visited website but didn't inquire; engaged with content but didn't DM";
      };
      budget: "₹500-2,000/day during campaign periods; ₹200-500/day maintenance";
      cost_per_lead: "₹50-200 per qualified inquiry (varies by destination)";
    };
  };
}
```

---

## Open Problems

1. **Content volume vs. quality** — Social media algorithms reward consistent posting (5-7 posts/week). Creating quality travel content at this volume is challenging for small agencies. Batch creation and repurposing are essential.

2. **Attribution black box** — Customer sees Instagram Reel → Googles agency → Calls phone number → Books. The Instagram Reel initiated but gets no attribution. Cross-channel tracking is technically difficult.

3. **DM management at scale** — 20+ DMs per day from interested prospects requires immediate, personalized responses. Auto-replies that redirect to WhatsApp help, but the handoff must feel seamless, not automated.

4. **Customer photo consent** — Using customer trip photos on social media requires explicit consent. Need a consent mechanism (WhatsApp opt-in) integrated into the post-trip feedback flow.

5. **Platform dependency** — Instagram algorithm changes can destroy reach overnight. Building an email list and WhatsApp subscriber base reduces dependency on any single platform's algorithm.

---

## Next Steps

- [ ] Build social media content calendar with scheduling
- [ ] Create DM-to-WhatsApp handoff automation
- [ ] Implement social commerce attribution tracking
- [ ] Design content creation workflow with batch templates
- [ ] Build social media analytics dashboard with ROI tracking
