# Additional Scenarios (21-30)

**Purpose**: Expand coverage to 30 total scenarios  
**Focus**: Edge cases, advanced situations, anti-personas

---

## Scenario 21: The Ghost Customer (No Response)

**Persona**: P1 Solo Agent  
**Situation**: Sent quote 3 days ago, customer not responding  
**Context**: Lead seemed hot initially

### Real-World Situation
- Day 1: Customer messages "Need quote urgently for Bali, travel next month"
- Day 1: Agent responds with 3 options within 2 hours
- Day 2: No response
- Day 3: Agent sends follow-up: "Any questions about the quote?"
- Day 4: Still no response
- Agent wonders: "Should I follow up again? Did they book elsewhere?"

### Without System
- Agent either:
  - Spams customer (annoying)
  - Gives up (lost lead)
  - Has no idea what happened

### With System
```
NOTEBOOK 01: Already completed (quote sent)

NOTEBOOK 02: Lead Tracking Mode
  Input: Quote sent 3 days ago, no response
  
  Process:
    - Track: Quote opened? (email tracking)
    - Track: Links clicked? (hotel pages viewed?)
    - Calculate: Engagement score
    - Detect: Silent for 72 hours
  
  Output:
    decision_state: LEAD_FOLLOWUP_REQUIRED
    
    engagement_analysis:
      quote_opened: true (Day 1, 2:30 PM)
      options_viewed: [option_2_mid_range]  # Only looked at mid option
      time_spent: 4 minutes
      links_clicked: [hotel_detail_page]
      
    interpretation:
      "Customer engaged initially but went silent.
       Showed interest in Option 2 (mid-range).
       Viewed hotel details for 4 minutes.
       Possible: Comparing with competitors,
       or Budget concern (Option 2 was ₹3L)"
    
    suggested_action:
      "Send targeted follow-up:
       'Hi! Noticed you looked at the mid-range option.
        Quick question: Is the ₹3L budget working, 
        or would you like a trimmed version at ₹2.5L?'
       
       Timing: Send tomorrow 11 AM (customer opened Day 1 at 2 PM)"
    
    if_no_response_in_48h:
      "Move to nurture campaign (monthly newsletter)
       Don't spam."
```

### Pipeline Mapping
- **N01**: Capture initial requirements (done)
- **N02**: Monitor engagement, suggest follow-up timing/content
- **Key Feature**: Engagement tracking, interpretation, suggested actions

---

## Scenario 22: The Scope Creep (Free Consulting)

**Persona**: P2 Agency Owner  
**Situation**: Customer keeps asking for revisions but never books  
**Pattern**: 8 revisions over 3 weeks, no commitment

### Real-World Situation
- Customer: "Give me options for Europe"
- Agent: Sends 3 options
- Customer: "What about Asia instead?"
- Agent: Sends 3 Asia options  
- Customer: "Back to Europe but different cities"
- Agent: Sends more options
- ... (8 iterations)
- Customer: "Thanks, I'll think about it"
- Agent: 12 hours of work, ₹0 revenue

### Without System
- Owner doesn't know this is happening
- Agent frustrated but keeps helping
- No tracking of time invested
- No "enough is enough" trigger

### With System
```
NOTEBOOK 01: Track each revision
  Revision 1: Europe (3 options)
  Revision 2: Asia (3 options)  [change: destination]
  Revision 3: Europe v2 (3 options) [change: destination again]
  Revision 4: Europe v2 + different hotels [change: accommodation]
  ...
  Revision 8: Still no booking

NOTEBOOK 02: Pattern Detection
  Input: 8 revisions, 0 bookings, 21 days elapsed
  
  Process:
    - Calculate: Time invested = 12 hours
    - Calculate: Opportunity cost = ₹X (other leads not pursued)
    - Detect: Pattern = scope_creep_no_commitment
    - Risk: High time sink, low conversion probability
  
  Output:
    decision_state: SET_BOUNDARIES
    
    alerts:
      - agent: "You've spent 12 hours on this lead with 8 revisions.
                Average booking time: 4 hours."
      - owner: "Agent Anita has 3 leads with >5 revisions each."
    
    suggested_action:
      "Send closing message:
       'Hi! I've enjoyed helping explore options. 
        To move forward, I'll need a commitment by Friday.
        After that, I'll need to focus on confirmed bookings.
        Let me know if you'd like to proceed!'
      
       Alternative: Offer planning fee
       'For extensive custom planning, we charge ₹5000 
        planning fee (deducted from final booking).'
       "
    
    pipeline_action:
      "Move to 'nurture' status
       Re-engage in 3 months with special offer
       Don't invest more time now."
```

### Pipeline Mapping
- **N01**: Capture each revision's changes
- **N02**: Pattern detection, time tracking, boundary suggestions
- **Key Feature**: Revision counting, ROI calculation, agent protection

---

## Scenario 23: The Influencer Request

**Persona**: P1 Solo Agent  
**Situation**: "I'm a travel influencer with 50K followers, can I get a free trip in exchange for posts?"

### Real-World Situation
- WhatsApp: "Hi! I'm @TravelWithPriya (50K followers). 
           Love to collaborate! Free trip to Maldives?
           Will post 3 reels, tag your agency."
- Agent tempted: "50K followers... could get lots of leads"
- But: Previous influencer gave 2 posts, 0 leads
- Unclear: What's fair exchange? What's the risk?

### Without System
- Agent says yes, pays ₹2L for trip
- Influencer posts 1 story (not reel), poor quality
- Zero leads generated
- Agent loses money and time

### With System
```
NOTEBOOK 01: Capture opportunity
  Input: Influencer proposal
  Facts:
    - follower_count: 50K (claimed)
    - platform: Instagram
    - proposal: free_trip_for_content
    - deliverables: 3 reels + tags
    - destination: Maldives
    - estimated_cost: ₹2L

NOTEBOOK 02: Opportunity Evaluation
  Process:
    - Check: Historical influencer ROI
        * Past influencer 1: 100K followers → 0 leads
        * Past influencer 2: 25K followers → 3 leads, 0 bookings
        * Average conversion: 0.1% of followers = 50 potential
        * Actual booking rate: 0.5% of potential = 0.25 bookings
    
    - Calculate: Expected value
        * Expected bookings: 0.25
        * Average booking value: ₹3L
        * Expected revenue: ₹75K
        * Cost: ₹2L
        * ROI: -62.5% (LOSS)
    
    - Risk assessment:
        * Follower quality: Unknown (could be fake)
        * Content quality: Unknown
        * Brand alignment: Unknown
  
  Output:
    decision_state: BRANCH_OPTIONS
    
    analysis:
      "Based on historical data, expected ROI is -62.5%.
       High risk, low probability of return."
    
    options:
      - option: decline_politely
        response: "Thanks for the interest! Currently not doing 
                  influencer collaborations. Happy to offer 
                  competitive rates for your personal trips though."
      
      - option: negotiate_risk_share
        response: "We can do 50% discount + performance bonus:
                  • 50% off trip (₹1L)
                  • ₹1L additional discount if generates 5+ confirmed leads
                  • Must sign agreement with deliverables"
        note: "Limits downside to ₹1L, upside if they deliver"
      
      - option: small_test_first
        response: "Let's start with a domestic weekend trip (₹20K).
                  If that generates leads, we'll discuss Maldives."
        note: "Test with low investment first"
    
    recommendation: "Option 2 or 3. Never full free trip."
```

### Pipeline Mapping
- **N01**: Capture influencer metrics, proposal details
- **N02**: ROI calculation, risk assessment, decision options
- **Key Feature**: Historical ROI tracking, opportunity evaluation

---

## Scenario 24: The Medical Emergency During Trip

**Persona**: S2 Family Coordinator  
**Situation**: Elderly father has heart issue on day 3 of 7-day trip  
**Context**: International location, language barrier, family panicking

### Real-World Situation
- Day 3: Father complains of chest pain
- Family calls agent (it's 2 AM in India)
- Agent groggy, doesn't have:
  - Travel insurance details
  - Local hospital contacts
  - Emergency protocols
- Family: "What do we do? Where do we go? Who pays?"

### Without System
- Agent scrambles, googles hospitals
- Family waits 30 minutes in panic
- Wrong hospital chosen (not covered by insurance)
- ₹5L medical bill, insurance denies claim
- Family never uses agency again

### With System
```
NOTEBOOK 01: Pre-trip preparation (already done)
  Captured:
    - travel_insurance: Policy #12345, coverage ₹10L
    - emergency_contact: Insurance 24/7: +1-800-XXX
    - medical_conditions: Father - hypertension (on record)
    - local_hospitals: [Singapore General (cashless), 
                        Mount Elizabeth (premium)]

NOTEBOOK 02: Crisis Mode (activated by emergency keyword)
  Input: "Medical emergency, father chest pain, Singapore"
  
  Auto-trigger (detects "emergency" + "medical"):
    - Bypass normal queue
    - Alert on-call agent + owner
    - Pull emergency protocol
  
  Output:
    decision_state: EMERGENCY_PROTOCOL
    
    immediate_actions:
      - step_1:
        action: "Call ambulance: 995 (Singapore emergency)"
        priority: CRITICAL
        time: "NOW"
      
      - step_2:
        action: "Go to Singapore General Hospital (cashless)"
        address: "Outram Road, Singapore"
        insurance: "Direct billing with Policy #12345"
        avoid: "Mount Elizabeth (out-of-network, will pay upfront)"
      
      - step_3:
        action: "Call insurance 24/7"
        number: "+1-800-XXX"
        say: "Medical emergency, Policy #12345, Singapore General Hospital"
      
      - step_4:
        action: "Keep all bills, prescriptions"
        note: "Insurance will reimburse or direct pay"
    
    agent_instructions:
      "STAY ON CALL with family until ambulance arrives.
       Be calm, follow protocol.
       Do NOT guess or improvise.
       
       After stable:
       - Check if trip needs modification
       - Arrange early return if needed
       - Coordinate with insurance for claims"
    
    auto_notifications:
      - family_group: "Emergency protocol activated. 
                      Mrs. Reddy, follow steps above. 
                      Agent calling you now."
      - insurance: "Policy #12345 - Medical emergency notified"
```

### Pipeline Mapping
- **N01**: Pre-capture insurance, medical conditions, emergency contacts
- **N02**: Crisis detection, emergency protocol, step-by-step guidance
- **Key Feature**: Emergency keyword detection, protocol automation, insurance integration

---

## Scenario 25: The Competing Family Priorities

**Persona**: S2 Family Coordinator (Mrs. Reddy)  
**Situation**: 3 families, 3 different budgets, trying to book together

### Real-World Situation
- Family A: "We can do ₹4L, want luxury"
- Family B: "Our max is ₹2.5L, budget option fine"
- Family C: "Flexible, but want value for money"
- Coordinator (Mrs. Reddy): "How do I make everyone happy?"

Current approach:
- Suggests mid-range ₹3L
- Family A: "Too cheap for us"
- Family B: "Too expensive"
- Family C: "Sure, whatever"
- No consensus, trip canceled

### With System
```
NOTEBOOK 01: Capture individual constraints
  Family A:
    - budget: 4L
    - preference: luxury
    - flexibility: can travel separately if needed
  
  Family B:
    - budget: 2.5L
    - preference: budget
    - constraint: cannot exceed 2.5L
  
  Family C:
    - budget: 3.5L
    - preference: value
    - flexibility: medium

NOTEBOOK 02: Consensus Building
  Process:
    - Detect: Budget spread = ₹1.5L (high variance)
    - Detect: Cannot satisfy all with one option
    - Strategy: Split or compromise
  
  Output:
    decision_state: BRANCH_OPTIONS
    
    options:
      - option: tiered_accommodation
        description: "Same destination, different hotels"
        details:
          - Family A: 5-star resort (₹4L)
          - Family B: 3-star nearby (₹2.3L)
          - Family C: 4-star middle option (₹3.2L)
        shared_activities: "Day trips, dinners together"
        benefit: "Everyone gets their budget level, still together"
      
      - option: compromise_mid_range
        description: "Everyone meets at ₹3L"
        details:
          - Family A: Downgrade to 4-star (saves ₹1L)
          - Family B: Stretch to ₹3L (adds ₹50K)
          - Family C: Perfect fit
        benefit: "Same hotel, simpler logistics"
        challenge: "A downgrades, B stretches"
      
      - option: split_trips
        description: "Different dates/destinations"
        details:
          - Family A: Maldives luxury (₹4L)
          - Family B + C: Thailand together (₹2.5L, ₹3L)
        benefit: "Everyone gets exactly what they want"
        challenge: "Not together"
    
    recommendation:
      "Suggest Option 1 (tiered accommodation).
       Family A gets luxury, B stays in budget, C gets value.
       Still together for activities.
       
       Sample message to Mrs. Reddy:
       'I found a way everyone wins! Family A stays at 
        The Oberoi (luxury), Family B at Ginger (budget, 
        same area), Family C at Lemon Tree (mid-range).
        All 10 mins apart. Shared dinners and day trips.
        Everyone happy?'"
```

### Pipeline Mapping
- **N01**: Capture individual family constraints
- **N02**: Variance detection, consensus building, creative solutions
- **Key Feature**: Multi-party optimization, compromise suggestions

---

## Scenario 26: The Last-Minute Cancellation

**Persona**: P1 Solo Agent  
**Situation**: Customer cancels 48 hours before departure  
**Context**: Full trip booked, hotels non-refundable, flights have penalties

### Real-World Situation
- Customer: "Sorry, medical emergency in family, can't travel"
- Agent: Already paid:
  - Hotels: ₹2L (non-refundable)
  - Flights: ₹1.5L (₹50K cancellation fee)
  - Activities: ₹30K (partial refund)
- Customer: "Can I get full refund?"
- Agent dilemma: "Do I absorb ₹2.3L loss or lose customer?"

### Without System
- Agent doesn't have clear policy
- Either:
  - Absorbs loss (business hurt)
  - Says no (customer angry)
- No tracking of cancellation reasons
- No learning from patterns

### With System
```
NOTEBOOK 01: Record cancellation
  Input: Cancellation request, 48 hours before
  Facts:
    - reason: medical_emergency (claimed)
    - notice_period: 48 hours
    - prepaid: hotels ₹2L, flights ₹1.5L, activities ₹30K
    - refund_eligible: flights ₹1L, activities ₹20K
    - non_refundable: hotels ₹2L, flights ₹50K

NOTEBOOK 02: Cancellation Policy Engine
  Process:
    - Check: Cancellation reason category
        * Medical emergency: High sympathy, verify?
        * Personal reasons: Standard policy
        * Force majeure: Full refund
    
    - Check: Insurance coverage
        * Travel insurance included?
        * Medical cancellation covered?
    
    - Calculate: Financial impact options
  
  Output:
    decision_state: BRANCH_OPTIONS (with policy guidance)
    
    options:
      - option: full_refund_absorb_loss
        cost: ₹2.3L (agent loss)
        customer_relationship: Excellent
        when_to_use: "VIP customer, first cancellation, genuine reason"
      
      - option: partial_refund_fair_split
        refund: ₹1.5L (flights + activities refund)
        loss: ₹2L (hotels, non-refundable)
        customer_pays: ₹2L
        message: "Medical emergencies covered by insurance next time. 
                  Hotels non-refundable. Refunding what we can (₹1.5L)."
      
      - option: reschedule_no_loss
        action: "Move dates to future, no fees"
        benefit: "Zero loss for both, keeps booking"
        requirement: "Customer commits to new dates"
      
      - option: insurance_claim
        action: "Help file travel insurance claim"
        potential_recovery: ₹3.8L (full trip)
        timeline: "2-4 weeks"
        condition: "Medical certificate required"
    
    recommendation:
      "Option 2 (partial refund) + Option 4 (insurance help).
       Message: 'So sorry for the emergency. Hotels are 
       non-refundable (₹2L), but I'm refunding flights 
       and activities (₹1.5L). Let me also help you claim 
       from travel insurance - you should get full ₹3.8L 
       back with medical cert. New policy: Always get 
       travel insurance for medical coverage.'"
    
    policy_update:
      "Add to customer profile: Cancellation 48hr notice.
       Recommend insurance emphasis in future."
```

### Pipeline Mapping
- **N01**: Capture cancellation details, financial exposure
- **N02**: Policy application, option generation, recommendation
- **Key Feature**: Policy engine, insurance integration, learning capture

---

## Scenario 27: The Referral Request

**Persona**: P1 Solo Agent  
**Situation**: Happy customer wants to refer friend, asks for "referral discount"

### Real-World Situation
- Customer: "My friend Ravi wants to book with you. Can you give him my referral discount?"
- Agent: "What's a referral discount?"
- No formal program
- Agent either:
  - Makes up discount (hurts margin)
  - Says no (missed opportunity)
  - Doesn't track referrals

### With System
```
NOTEBOOK 01: Capture referral
  Input: Existing customer (Mr. Sharma) refers Ravi
  Facts:
    - referrer: Mr. Sharma (past customer, 2 trips)
    - referee: Ravi (new lead)
    - referrer_satisfaction: High (from history)
    - potential_booking: Family of 4, Europe, ₹6L

NOTEBOOK 02: Referral Program Logic
  Process:
    - Check: Referrer history
        * Loyal customer? Yes (2 trips)
        * High value? Yes (₹5L+ total)
    
    - Calculate: Referral value
        * New booking potential: ₹6L
        * Acquisition cost saved: ₹5K (vs ads)
        * Referrer lifetime value: ₹15K (expected future)
    
    - Apply: Referral policy
  
  Output:
    decision_state: PROCEED_WITH_INCENTIVE
    
    referral_program:
      referrer_reward: "₹3000 credit on next booking"
      referee_discount: "₹3000 off first booking"
      cost: ₹6000
      net_value: ₹6L - ₹6K = ₹5.94L (still profitable)
    
    message_to_referrer:
      "Thank you for referring Ravi! 🎉
       When he books, you get ₹3000 credit 
       and he gets ₹3000 off. Win-win!"
    
    message_to_referee:
      "Hi Ravi! Mr. Sharma recommended us.
       Welcome discount: ₹3000 off your first trip.
       Let's plan your Europe trip!"
    
    tracking:
      - referral_source: Mr. Sharma
      - discount_applied: ₹3000
      - referrer_credit_pending: ₹3000
      - conversion_target: 30 days
```

### Pipeline Mapping
- **N01**: Capture referral relationship
- **N02**: Reward calculation, incentive application, tracking
- **Key Feature**: Referral program automation, value calculation

---

## Scenario 28: The Seasonal Rush

**Persona**: P2 Agency Owner  
**Situation**: December 15, 15 customers want Christmas/New Year bookings  
**Constraint**: Only 5 can be accommodated due to hotel availability

### Real-World Situation
- Peak season: Dec 20-Jan 5
- Limited hotel inventory
- 15 leads, only 5 rooms available
- How to decide who gets booking?
- Current: First-come-first-serve (unfair to high-value customers)

### Without System
- Agent books whoever calls first
- High-value customer calls later: "No rooms?"
- Lost revenue: ₹10L+ from VIP customers
- Junior agent customers get rooms, VIPs turned away

### With System
```
NOTEBOOK 01: Capture all requests
  Queue: 15 requests for Dec 20-Jan 5
  Facts per request:
    - customer_value: [VIP, regular, new]
    - booking_value: [₹8L, ₹5L, ₹3L, ...]
    - margin: [15%, 12%, 8%, ...]
    - request_time: timestamp
    - flexibility: [dates_flexible, fixed_dates]
    - history: [3 past trips, 0 trips, ...]

NOTEBOOK 02: Allocation Optimization
  Process:
    - Objective: Maximize revenue + margin + loyalty
    - Constraints: 5 rooms available
    - Factors:
        * Customer lifetime value (weight: 30%)
        * Booking margin (weight: 30%)
        * Urgency/loyalty (weight: 20%)
        * Flexibility (weight: 20%)
    
    - Algorithm: Score each request, allocate top 5
  
  Output:
    decision_state: ALLOCATION_REQUIRED
    
    allocation:
      confirmed_bookings:
        - rank_1: VIP customer, ₹8L, 15% margin, 3 past trips
        - rank_2: VIP customer, ₹7L, 14% margin, flexible dates
        - rank_3: Regular, ₹6L, 12% margin, long history
        - rank_4: VIP customer, ₹5.5L, 13% margin
        - rank_5: Regular, ₹5L, 12% margin
      
      waitlist:
        - rank_6: New customer, ₹4L (offer alternative dates)
        - rank_7-15: Various (offer alternatives)
    
    alternatives_for_waitlist:
      - "Jan 5-12 dates available (same hotels, lower prices)"
      - "Different destination (Goa instead of Kerala)"
      - "Premium upgrade (5-star instead of 4-star, still available)"
    
    communication:
      confirmed: "Great news! Secured your booking. Details inside..."
      waitlist: "Peak season rush! You're #3 on waitlist. 
                Alternative dates available. Reply with preference."
```

### Pipeline Mapping
- **N01**: Queue all requests, capture flexibility
- **N02**: Optimization algorithm, allocation, alternative generation
- **Key Feature**: Revenue optimization, waitlist management

---

## Scenario 29: The Package Customization Request

**Persona**: P1 Solo Agent  
**Situation**: Customer likes standard package but wants 3 changes  
**Context**: Each change affects price, logistics, and other components

### Real-World Situation
- Customer: "I like your Singapore Family Package, but:
   1. Can we upgrade hotel from 4-star to 5-star?
   2. Skip Universal Studios, add more cultural tours?
   3. Add vegetarian cooking class for wife?"
- Agent: Needs to recalculate:
  - Hotel upgrade: +₹15K/night × 5 nights = +₹75K
  - Remove USS: -₹30K
  - Add cultural tours: +₹15K
  - Add cooking class: +₹8K
  - Net change: +₹68K
  - Also: Check if cooking class available on those dates
  - Check if cultural tours fit revised schedule

### Without System
- Agent spends 1 hour recalculating
- Misses: Cooking class not available Tuesday
- Quotes, then realizes conflict
- Revised quote, customer confused
- Lost time, lost confidence

### With System
```
NOTEBOOK 01: Capture customization requests
  Base package: Singapore Family (₹3L)
  Changes:
    1. hotel_upgrade: 4_star → 5_star
    2. activity_swap: remove_universal_studios, add_cultural_tours
    3. activity_add: vegetarian_cooking_class

NOTEBOOK 02: Customization Engine
  Process:
    - Calculate financial impact:
        + Hotel upgrade: +₹75K
        - Remove USS: -₹30K
        + Cultural tours: +₹15K
        + Cooking class: +₹8K
        = Net: +₹68K
    
    - Check availability:
        * Hotel: 5-star available? Yes
        * Cultural tours: Available on Day 2, 4? Yes
        * Cooking class: Available Day 3? NO (Tuesday closed)
        * Alternative: Day 4? Yes
    
    - Check schedule conflicts:
        * Revised schedule: Day 1 arrival, Day 2 cultural, 
          Day 3 free, Day 4 cooking class + cultural, Day 5 departure
        * No conflicts detected
    
    - Recalculate margin:
        * New package value: ₹3.68L
        * New margin: 13% (down from 14%)
        * Acceptable? Yes (>10% minimum)
  
  Output:
    decision_state: PROCEED_WITH_CUSTOMIZATION
    
    custom_quote:
      base_package: Singapore Family (₹3L)
      customizations:
        - item: "Upgrade to Marina Bay Sands (5-star)"
          cost: +₹75K
        - item: "Replace Universal Studios with Cultural Heritage Tour"
          cost: -₹30K + ₹15K = -₹15K net
        - item: "Add Vegetarian Cooking Class (Day 4)"
          cost: +₹8K
      
      new_total: ₹3.68L
      new_margin: 13%
      
      revised_itinerary:
        Day 1: Arrival, check-in Marina Bay Sands
        Day 2: Cultural Heritage Tour (Little India, Chinatown)
        Day 3: Free day (optional Gardens by the Bay)
        Day 4: Morning Cooking Class, Afternoon Sentosa
        Day 5: Departure
      
      availability_check: ✅ All confirmed available
      
    confirmation_message:
      "Customized package ready! ₹3.68L total.
       Changes: 5-star hotel, cultural focus, cooking class.
       Note: Cooking class moved to Day 4 (Tuesdays closed).
       All confirmed available. Valid for 48 hours."
```

### Pipeline Mapping
- **N01**: Capture customization requests
- **N02**: Impact calculation, availability check, conflict detection, margin validation
- **Key Feature**: Dynamic packaging, constraint satisfaction

---

## Scenario 30: The Review Request (Post-Trip)

**Persona**: S1 Individual Traveler  
**Situation**: Trip completed, agent wants review but doesn't want to annoy customer

### Real-World Situation
- Trip ended 3 days ago
- Agent: "Should I ask for review?"
- If ask too soon: Customer still traveling home, annoyed
- If ask too late: Forgot details, less enthusiastic
- If don't ask: Lost social proof
- Current: Random timing, haphazard approach

### With System
```
NOTEBOOK 01: Capture trip completion
  Event: Return flight landed 3 days ago
  Facts:
    - trip_completed: true
    - return_date: 2026-03-20
    - days_since_return: 3
    - post_trip_survey_sent: false
    - review_requested: false

NOTEBOOK 02: Post-Trip Engagement Timing
  Process:
    - Check: Optimal timing for review request
        * Day 1-2: Too soon (jet lag, unpacking)
        * Day 3-5: Optimal (experience fresh, settled)
        * Day 7+: Too late (details fading)
    
    - Check: Customer sentiment indicators
        * Any complaints during trip? No
        * Emergency issues? No
        * Extra requests handled? Yes
    
    - Predict: Likelihood of positive review
        * Satisfaction score: 9/10 (based on interaction quality)
        * Predicted review: Positive
  
  Output:
    decision_state: PROCEED_TRAVELER_SAFE (for review request)
    
    optimal_timing: "Today (Day 3)"
    
    message:
      "Hi Priya! Hope you're settling back home. 
       How was your Singapore trip? 🌴
       
       If you have 2 minutes, would love a review:
       [Google Review Link]
       
       Your feedback helps other families 
       choose the right trip. Thanks! 🙏"
    
    alternative_if_no_response_in_7_days:
      "Quick check-in: Any feedback on your trip?
       We're always improving!"
    
    if_negative_feedback:
      alert: "Negative sentiment detected"
      action: "Owner call within 24 hours"
      priority: HIGH
```

### Pipeline Mapping
- **N01**: Track trip completion, capture sentiment signals
- **N02**: Timing optimization, review request, escalation for negatives
- **Key Feature**: Post-trip engagement, reputation management

---

## Summary: 30 Scenarios Complete

| # | Scenario | Persona | N01 Role | N02 Role |
|---|----------|---------|----------|----------|
| 1-5 | P1 Solo Agent scenarios | P1 | Intake & memory | Decision & protection |
| 6-10 | P2 Owner scenarios | P2 | Oversight data | Control & analytics |
| 11-15 | P3 Junior scenarios | P3 | Guided intake | Validation & safety |
| 16-20 | S1/S2 Customer scenarios | S1/S2 | Experience capture | Service optimization |
| 21 | Ghost customer | P1 | Initial capture | Lead nurturing |
| 22 | Scope creep | P2 | Revision tracking | Boundary setting |
| 23 | Influencer request | P1 | Opportunity capture | ROI evaluation |
| 24 | Medical emergency | S2 | Pre-capture insurance | Crisis protocol |
| 25 | Competing priorities | S2 | Individual constraints | Consensus building |
| 26 | Last-minute cancellation | P1 | Cancellation details | Policy application |
| 27 | Referral request | P1 | Referral capture | Incentive calculation |
| 28 | Seasonal rush | P2 | Queue management | Optimization |
| 29 | Package customization | P1 | Customization requests | Dynamic pricing |
| 30 | Review request | S1 | Completion tracking | Engagement timing |

**Total: 30 real-world scenarios mapped to pipeline**

---

*Next: Test identification strategy*
