# Onboarding & First-Run Experience — Agent Onboarding

> Research document for new agent onboarding, guided tours, and progressive feature discovery.

---

## Key Questions

1. **What's the agent onboarding flow from invite to productivity?**
2. **How do we teach agents the workbench without overwhelming them?**
3. **What's the progressive disclosure model for complex features?**
4. **How do we measure agent onboarding success?**
5. **What's the experience for agents switching from other platforms?**

---

## Research Areas

### Agent Onboarding Flow

```typescript
interface AgentOnboarding {
  agentId: string;
  agencyId: string;
  status: AgentOnboardingStatus;
  track: OnboardingTrack;
  progress: AgentOnboardingProgress;
  startedAt: Date;
  completedAt?: Date;
  mentor?: string;
}

type OnboardingTrack =
  | 'new_agent'                      // New to travel industry
  | 'experienced_agent'              // Experienced, new to platform
  | 'agency_transfer'                // Transferring from another system
  | 'specialist';                    // Specialist role (visa, MICE, pricing)

// Agent onboarding timeline:
// Day 1: Access & Orientation (1-2 hours)
//   - Accept invite, set password
//   - Complete profile (name, photo, specialization)
//   - Interactive workbench tour
//   - Watch "Getting Started" video (5 minutes)
//   - Create first test trip
//
// Day 2-3: Core Skills (2-3 hours/day)
//   - Practice intake and extraction
//   - Build a trip from template
//   - Generate a quote document
//   - Practice customer communication
//
// Day 4-5: Advanced Features (2-3 hours/day)
//   - Spine pipeline understanding
//   - Pricing and margin management
//   - Booking workflow end-to-end
//   - Payment processing
//
// Day 6-7: Live Operations (with supervision)
//   - Handle real customer inquiries
//   - Mentor reviews all work
//   - Feedback and coaching sessions
//   - Gradual independence

interface AgentOnboardingProgress {
  completedModules: string[];
  currentModule: string;
  assessments: AssessmentResult[];
  practiceTrips: string[];
  supervisedTrips: string[];
  signOffStatus: SignOffStatus;
}

type SignOffStatus =
  | 'pending'                        // Not yet reviewed
  | 'mentor_approved'                // Mentor signed off
  | 'manager_approved'               // Manager signed off
  | 'fully_cleared';                 // Can work independently
```

### Interactive Tour System

```typescript
interface InteractiveTour {
  tourId: string;
  name: string;
  description: string;
  steps: TourStep[];
  targetAudience: string[];
  estimatedMinutes: number;
}

interface TourStep {
  stepId: string;
  targetElement: string;             // CSS selector or component ref
  placement: 'top' | 'bottom' | 'left' | 'right' | 'center';
  title: string;
  description: string;
  action?: TourAction;
  highlightStyle: 'spotlight' | 'tooltip' | 'modal';
}

type TourAction =
  | { type: 'click'; target: string }
  | { type: 'navigate'; url: string }
  | { type: 'wait_for_element'; selector: string }
  | { type: 'input'; target: string; value: string }
  | { type: 'observe'; durationMs: number };

// Tour library:
// Tour 1: "Welcome to the Workbench" (5 min)
//   - Overview of the 4-panel layout
//   - Inbox, Intake, Builder, Output
//   - Where to find help
//
// Tour 2: "Your First Trip" (10 min)
//   - Select a trip from inbox
//   - Review extracted data in intake
//   - Build itinerary in builder
//   - Generate quote in output
//
// Tour 3: "Customer Communication" (5 min)
//   - Send a message to customer
//   - Use templates
//   - Schedule a meeting
//
// Tour 4: "Booking & Payments" (10 min)
//   - Confirm a booking
//   - Process a payment
//   - Generate invoice
//
// Tour 5: "Advanced Features" (10 min)
//   - Spine pipeline settings
//   - Pricing adjustments
//   - Collaboration tools

// Tour UX principles:
// 1. Tours are optional (skip button always visible)
// 2. Tours can be resumed (if interrupted)
// 3. Tours use real data (sample trip, not mock data)
// 4. Tours are interactive (not just tooltips)
// 5. Tours track completion (for onboarding metrics)
```

### Progressive Disclosure

```typescript
interface FeatureDisclosure {
  feature: string;
  disclosedAt: DisclosedWhen;
  disclosureMethod: DisclosureMethod;
}

type DisclosedWhen =
  | 'on_first_use'                   // Show when feature is first relevant
  | 'after_n_trips'                  // After completing N trips
  | 'after_onboarding'               // After onboarding is complete
  | 'on_role_upgrade'                // When agent gets new permissions
  | 'on_feature_flag'                // When admin enables the feature
  | 'on_mentor_recommendation';      // When mentor suggests it

type DisclosureMethod =
  | 'tooltip_pulse'                  // Pulsing dot on new feature
  | 'banner'                         // Top banner: "New: Pricing Override"
  | 'changelog_item'                 // In the changelog/what's new panel
  | 'tour_step'                      // Part of a guided tour
  | 'notification';                  // Push notification

// Progressive disclosure schedule:
// Day 1 (core):
//   - Inbox, Intake panel, Trip Builder, Output panel
//   - Send message, Basic pricing
//
// Day 2-3 (essential):
//   - Spine pipeline, Customer profiles
//   - Template library, Document generation
//
// Day 4-5 (intermediate):
//   - Advanced pricing, Margin management
//   - Booking workflow, Payment processing
//   - Calendar, Task management
//
// Week 2+ (advanced):
//   - Collaboration tools, Workflow automation
//   - Analytics dashboard, Custom reports
//   - Integration settings, API access
//
// Role-specific (on promotion):
//   - Team management (team lead)
//   - Financial reports (manager)
//   - Agency settings (admin)
//   - Audit logs (compliance)

// Feature gating by experience level:
// New agent (0-10 trips): Core features only, simpler UI
// Developing agent (10-50 trips): Intermediate features unlocked
// Experienced agent (50+ trips): Full feature set
// Specialist: Role-specific advanced tools
```

### Agent Onboarding Metrics

```typescript
interface AgentOnboardingMetrics {
  // Completion metrics
  onboardingCompletionRate: number;
  averageDaysToProductive: number;   // Days until first real booking
  moduleCompletionRates: Record<string, number>;

  // Quality metrics
  firstBookingErrorRate: number;     // Errors in first independent booking
  mentorRevisionRate: number;        // % of work revised by mentor
  customerComplaintRate: number;     // Complaints from first 10 customers

  // Engagement metrics
  featureDiscoveryRate: number;      // % of available features discovered
  tourCompletionRate: number;
  helpArticleReadRate: number;

  // Satisfaction metrics
  onboardingSatisfactionScore: number;
  platformConfidenceScore: number;   // "I feel confident using the platform"
  wouldRecommendScore: number;
}

// Onboarding success benchmarks:
// Completion rate > 90%
// Days to productive < 7
// First booking error rate < 10%
// Satisfaction score > 4/5
// Feature discovery > 60% in first month
```

---

## Open Problems

1. **Training quality vs. speed** — Rush onboarding leads to errors. Slow onboarding delays productivity. Need the right balance.

2. **Experienced agent impatience** — Agents switching from other platforms know what they want. They don't want a 7-day onboarding. Need fast-track for experienced agents.

3. **Feature overwhelm** — Progressive disclosure helps, but even core features can be complex. Need contextual help within features, not just tours.

4. **Mentor availability** — Mentoring requires experienced agents' time. They're busy with their own customers. Need scalable mentoring (peer videos, not 1:1).

5. **Retention after onboarding** — Agents complete onboarding but then slowly disengage. Need continued engagement (gamification, challenges, community).

---

## Next Steps

- [ ] Design interactive tour system for workbench
- [ ] Build progressive disclosure framework with feature gating
- [ ] Create agent onboarding tracks for different experience levels
- [ ] Design mentor assignment and supervision workflow
- [ ] Study onboarding UX (Slack, Figma, Notion first-run experiences)
