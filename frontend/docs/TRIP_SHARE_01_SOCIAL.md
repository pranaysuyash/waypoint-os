# Trip Sharing & Social — Customer-Driven Brand Amplification

> Research document for trip sharing features, social media integration, trip countdown sharing, photo journal sharing, referral-embedded sharing, and brand amplification through customer-generated content for the Waypoint OS platform.

---

## Key Questions

1. **How do customers share their trip experiences with friends and family?**
2. **What sharing features drive referral and brand awareness?**
3. **How do we encourage sharing without being pushy?**
4. **What content is shareable and what needs privacy controls?**

---

## Research Areas

### Trip Sharing Features

```typescript
interface TripSharingSocial {
  // Customer-driven sharing and brand amplification
  sharing_types: {
    TRIP_COUNTDOWN: {
      description: "Shareable countdown to trip departure";
      format: "Beautiful card with destination image, countdown timer, and agency branding";
      content: "'12 days until Singapore! 🌏 — Waypoint Travel'";
      channels: "WhatsApp status, Instagram story, Facebook";
      tracking: "Each share includes referral link — viewers who click become leads";
      // ┌─────────────────────────────────────────────────────┐
      // │  🌏 12 Days Until Singapore!                                │
      // │                                                       │
      // │  ✈️ Delhi → Singapore · June 15-20                        │
      // │  🏨 Grand Mercure Singapore · 5 nights                    │
      // │  🎯 Gardens by the Bay · Sentosa · Night Safari           │
      // │                                                       │
      // │  Planned by Waypoint Travel ✈️                           │
      // │  [Plan Your Trip → waypoint.travel/share/abc123]          │
      // └─────────────────────────────────────────────────────┘
    };

    TRIP_JOURNAL: {
      description: "Post-trip photo journal sharing";
      format: "Auto-compiled day-by-day photo journal with trip highlights";
      content: "'5 Days in Singapore — Sharma Family Adventure'";
      features: {
        auto_compile: "Photos attached to activities during trip create the journal automatically";
        day_by_day: "Each day shows activity name + best photo + short caption";
        stats: "5 days · 3 cities · 15 activities · 87 photos";
        branding: "Subtle 'Planned by Waypoint Travel' footer with referral link";
      };
      sharing: "PDF download, WhatsApp forward, Instagram carousel, social media post";
      privacy: "Customer chooses: public (shareable link) or private (only via direct message)";
    };

    LIVE_TRIP_MOMENTS: {
      description: "Real-time trip moment sharing during travel";
      format: "Instagram story-style moment capture in companion app";
      flow: "Customer takes photo → selects 'Share Moment' → auto-stamped with location and activity → share to WhatsApp/Instagram";
      content: "'At Gardens by the Bay! 🌿 Day 2 of Singapore trip'";
      agency_visibility: "Agency can repost customer moments (with consent) to official social media";
    };

    TRIP_REVIEW_CARD: {
      description: "Post-trip review formatted as a shareable card";
      format: "Visual card with destination image, star rating, and customer quote";
      content: "'⭐⭐⭐⭐⭐ Best family trip ever! Waypoint Travel made it effortless. — Rajesh S.'";
      sharing: "Agency uses on social media; customer shares with friends";
      dual_purpose: "Social proof for marketing + referral trigger for viewers";
    };
  };

  sharing_infrastructure: {
    REFERRAL_LINK_EMBEDDING: {
      description: "Every shared item includes a trackable referral link";
      mechanism: {
        unique_link: "Each customer has a unique referral code embedded in share links";
        tracking: "Click on shared link → land on agency page → inquiry → booking → attributed to referrer";
        reward: "Referrer earns ₹1,000-2,000 credit when someone books through their shared link";
      };
    };

    BRANDING_CONTROLS: {
      description: "Agency branding on all shared content";
      elements: {
        logo: "Subtle agency logo watermark on photos and cards";
        tagline: "Agency name + tagline in footer";
        cta: "'Plan your own trip' button with referral link";
        colors: "Agency brand colors on all generated share cards";
      };
      balance: "Branding must be visible but not overwhelming — the customer's experience is the story";
    };

    PRIVACY_CONTROLS: {
      description: "Customer controls what is shared and with whom";
      settings: {
        default_private: "All trip content is private by default — customer explicitly shares",
        selective_sharing: "Choose which photos and moments to share (not all automatically)",
        audience: "Share with: everyone (public link) / friends only (WhatsApp) / agency only (for testimonial use)";
        revoke: "Customer can revoke shared links at any time";
        consent: "Explicit consent required before agency uses customer content on official channels";
      };
    };
  };
}
```

### Social Sharing Optimization

```typescript
interface SocialSharingOptimization {
  // Maximizing share rate and referral conversion
  share_triggers: {
    NATURAL_MOMENTS: {
      description: "Moments when customers naturally want to share";
      moments: [
        "Booking confirmed → excitement ('We're going to Singapore!')",
        "Countdown milestones (30 days, 7 days, 1 day)",
        "First activity of the trip completed",
        "Particularly scenic or impressive moment during trip",
        "Trip completed → reflection and nostalgia",
        "Trip journal auto-compiled → pride in the experience",
      ];
    };

    SHARE_PROMPTS: {
      description: "System prompts sharing at natural moments";
      examples: {
        booking_confirmed: {
          trigger: "Booking payment completed";
          prompt: "🎉 Your Singapore trip is confirmed! Share the excitement with friends?";
          format: "Countdown card with booking details";
        };
        trip_day_1: {
          trigger: "First activity completed on trip";
          prompt: "Hope Day 1 was amazing! Share a highlight moment?";
          format: "Photo with location stamp + activity name";
        };
        trip_complete: {
          trigger: "Trip ends (last day)";
          prompt: "Your trip journal is ready! 5 days, 87 photos — want to share it?";
          format: "Photo journal card with trip stats";
        };
      };
      principle: "Prompt, don't push. One prompt per natural moment; customer always says no without friction";
    };
  };

  analytics: {
    SHARE_METRICS: {
      shares_per_trip: "Average shares per trip (target: 3-5)";
      share_to_click_rate: "How many people click shared links (target: 10-20% of viewers)";
      click_to_inquiry: "How many clicks become inquiries (target: 5-10%)";
      inquiry_to_booking: "How many social inquiries convert (target: 20-30%)";
      referral_revenue: "Total revenue from socially-attributed bookings";
    };

    VIRAL_COEFFICIENT: {
      description: "How many new customers each existing customer brings";
      formula: "Avg shares per customer × click rate × inquiry rate × booking rate";
      target: "K > 0.3 (each customer brings 0.3 new customers through sharing)";
      if_k_gt_1: "Viral growth — more customers from sharing than from paid marketing";
    };
  };
}
```

---

## Open Problems

1. **Share fatigue** — Prompting customers to share at every moment becomes annoying. Need to limit prompts to 3-4 per trip at genuinely exciting moments, not routine ones.

2. **Privacy expectations** — Customers may not realize that sharing a countdown card reveals their travel dates and destination. Clear privacy disclosure needed before sharing.

3. **Brand representation** — When customers share trip content, they're representing the agency brand. Negative experiences shared publicly damage the brand. Need to ensure only positive experiences are prompted for sharing.

4. **Photo quality** — Auto-compiled journals depend on customers taking good photos during the trip. Bad photos make for unimpressive journals. Optional "travel photographer" add-on could improve quality.

5. **Attribution tracking** — A shared link viewed on WhatsApp → opened in browser → customer closes → later Googles agency name → books. The share initiated but gets no credit. Multi-touch attribution is technically difficult.

---

## Next Steps

- [ ] Build shareable content generator (countdown cards, trip journals, review cards)
- [ ] Create referral link embedding and tracking system
- [ ] Implement share prompt engine at natural trip moments
- [ ] Design privacy controls and consent management for sharing
- [ ] Build social sharing analytics dashboard with viral coefficient tracking
