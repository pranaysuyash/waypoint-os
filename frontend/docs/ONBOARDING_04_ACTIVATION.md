# Onboarding & First-Run Experience — Activation & Retention

> Research document for user activation strategies, engagement loops, and onboarding-to-retention transition.

---

## Key Questions

1. **What defines an "activated" user and how do we measure it?**
2. **What engagement hooks keep agents using the platform?**
3. **How do we transition from onboarding to ongoing usage?**
4. **What's the churn prevention model?**
5. **How do we re-engage agents who become inactive?**

---

## Research Areas

### Activation Model

```typescript
interface ActivationModel {
  activationEvents: ActivationEvent[];
  activationThreshold: ActivationThreshold;
  segments: ActivationSegment[];
}

interface ActivationEvent {
  eventName: string;
  weight: number;                    // Importance in activation score
  category: 'core' | 'engagement' | 'value' | 'social';
}

// Activation events:
// Core (must-do):
//   - Created first trip (weight: 20)
//   - Sent first quote (weight: 15)
//   - Completed first booking (weight: 25)
//   - Processed first payment (weight: 15)
//
// Engagement (stickiness):
//   - Logged in 5+ days in first week (weight: 5)
//   - Used 3+ features (weight: 5)
//   - Completed onboarding tour (weight: 5)
//   - Invited a team member (weight: 3)
//
// Value (business outcome):
//   - Generated first revenue (weight: 15)
//   - Customer gave positive feedback (weight: 5)
//   - Completed trip end-to-end (weight: 10)
//
// Social (community):
//   - Created a template (weight: 2)
//   - Helped another agent (weight: 2)
//   - Gave product feedback (weight: 1)

interface ActivationThreshold {
  minimumScore: number;              // Score needed to be "activated"
  timeWindow: string;                // "first 14 days"
}

// Activation segments:
// Fully Activated: Score > 80, using core features daily
// Partially Activated: Score 40-80, using some features
// At Risk: Score < 40 after 7 days, likely to churn
// Power User: Score > 95, using advanced features
```

### Engagement Loops

```typescript
interface EngagementLoop {
  loopName: string;
  trigger: string;
  action: string;
  reward: string;
  cadence: string;
}

// Core engagement loops:
//
// 1. Daily Check-in Loop
//    Trigger: New trip assigned
//    Action: Agent reviews and processes trip
//    Reward: Trip moves to "processed" with positive feedback
//    Cadence: Multiple times daily
//
// 2. Customer Delight Loop
//    Trigger: Customer asks for modification
//    Action: Agent makes changes, sends updated quote
//    Reward: Customer approves, booking confirmed
//    Cadence: As-needed
//
// 3. Revenue Loop
//    Trigger: Booking confirmed
//    Action: Payment processed, commission earned
//    Reward: Commission visible in dashboard
//    Cadence: Per booking
//
// 4. Learning Loop
//    Trigger: Agent encounters unfamiliar destination
//    Action: Uses knowledge base, asks mentor
//    Reward: Successfully books the trip, gains skill
//    Cadence: Weekly
//
// 5. Achievement Loop
//    Trigger: Milestone reached (10 trips, first MICE, etc.)
//    Action: Badge earned, leaderboard updated
//    Reward: Recognition, potential bonus
//    Cadence: Monthly

// Engagement metrics:
// Daily Active Users (DAU)
// DAU/MAU ratio (stickiness)
// Average sessions per day
// Average session duration
// Feature usage breadth (how many features per user)
// Return rate after first week
```

### Churn Prevention

```typescript
interface ChurnPrevention {
  riskSignals: ChurnRiskSignal[];
  interventions: ChurnIntervention[];
  winBack: WinBackCampaign[];
}

interface ChurnRiskSignal {
  signal: string;
  weight: number;
  detectionQuery: string;
}

// Churn risk signals:
// 1. Login frequency declining (from daily to <3x/week)
// 2. Time-on-platform declining (from 4 hrs/day to <1 hr/day)
// 3. Feature usage narrowing (stopped using advanced features)
// 4. Trip completion rate declining
// 5. Support ticket frequency increasing (frustration)
// 6. No bookings in past 7 days (for active agents)
// 7. Negative feedback from customers
// 8. Team member invitations declining (not growing)

interface ChurnIntervention {
  trigger: string;
  channel: 'in_app' | 'email' | 'phone' | 'whatsapp';
  message: string;
  action: string;
  owner: string;
}

// Intervention examples:
// Signal: Login frequency declining
// Intervention: "We noticed you haven't logged in recently. Here's what you missed: [3 new features]"
// Channel: Email (gentle nudge)
//
// Signal: No bookings in 7 days
// Intervention: "Looking for inspiration? Check out the new Singapore template that's converting at 40%"
// Channel: In-app notification
//
// Signal: Support tickets increasing
// Intervention: Assign dedicated support contact for 1:1 troubleshooting
// Channel: Phone call from account manager

interface WinBackCampaign {
  campaignId: string;
  targetSegment: string;
  steps: WinBackStep[];
}

// Win-back for churned agents:
// Week 1: "We miss you" email with new feature highlights
// Week 2: "Your agency is still active, here's what your team has been doing"
// Week 3: Special offer (discount, free month, extra feature)
// Week 4: Phone call from account manager
```

### Onboarding-to-Retention Transition

```typescript
interface OnboardingToRetention {
  onboardingPhase: OnboardingPhase;
  graduationTriggers: GraduationTrigger[];
  postOnboarding: PostOnboardingPlan;
}

type OnboardingPhase =
  | 'setup'                  // Days 1-2: Account setup
  | 'learning'               // Days 3-7: Core skills
  | 'supervised'             // Days 8-14: Supervised work
  | 'graduated';             // Day 15+: Independent

interface GraduationTrigger {
  trigger: string;
  threshold: number;
}

// Graduation criteria:
// - Completed 5+ trips independently
// - Error rate < 5%
// - Customer satisfaction > 4/5
// - Mentor sign-off received
// - All core features used at least once

// Post-onboarding engagement:
// Month 1: "You've been on the platform for a month!"
//   - Show stats: Trips completed, revenue generated
//   - Suggest advanced features to explore
//   - Invite to agent community
//
// Month 2-3: Skill development
//   - Suggest training modules
//   - Specialist certification available
//   - Community contributions (templates, reviews)
//
// Month 4+: Mastery
//   - Mentor program (become a mentor)
//   - Template marketplace contributions
//   - Feature beta access
//   - Agent advisory board invitation
```

---

## Open Problems

1. **Activation definition variability** — A corporate travel agent and a leisure travel agent have different activation patterns. One-size-fits-all thresholds don't work.

2. **Engagement without pressure** — Agents shouldn't feel surveilled. Engagement metrics should feel helpful ("you're doing great!") not tracking ("we noticed you logged in late today").

3. **Win-back cost** — Re-acquiring a churned user costs 5x more than retaining. Need early intervention, not post-churn campaigns.

4. **Platform dependency** — If agents only use 2 features, they can easily switch. Need increasing value through feature adoption.

5. **Seasonal churn** — Travel has seasonal patterns. A "quiet" agent in monsoon season isn't necessarily churning.

---

## Next Steps

- [ ] Design activation scoring model with weighted events
- [ ] Build churn risk detection with automated interventions
- [ ] Create engagement loop analytics
- [ ] Design onboarding-to-retention transition workflow
- [ ] Study activation and retention patterns (Mixpanel, Amplitude, Heap)
