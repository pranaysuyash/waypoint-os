# Onboarding & First-Run Experience — Agency Setup

> Research document for new agency onboarding, setup wizard, and initial configuration.

---

## Key Questions

1. **What's the agency onboarding flow from signup to first booking?**
2. **What configuration is needed before an agency can start operating?**
3. **How do we reduce time-to-first-value for new agencies?**
4. **What's the migration-assisted onboarding for existing agencies?**
5. **How do we validate that onboarding is complete and correct?**

---

## Research Areas

### Agency Onboarding Flow

```typescript
interface AgencyOnboarding {
  onboardingId: string;
  agencyId: string;
  status: OnboardingStatus;
  steps: OnboardingStep[];
  startedAt: Date;
  completedAt?: Date;
  onboardingManager?: string;       // Assigned support person
  plan: OnboardingPlan;
}

type OnboardingStatus =
  | 'not_started'
  | 'in_progress'
  | 'paused'
  | 'completed'
  | 'abandoned';

// Onboarding phases:
// Phase 1: Account Setup (10 minutes)
//   - Create account (email, phone, agency name)
//   - Verify email and phone
//   - Choose plan (starter, professional, enterprise)
//   - Enter payment method
//
// Phase 2: Agency Profile (15 minutes)
//   - Agency logo and branding
//   - Business details (GST number, PAN, address)
//   - Contact information
//   - Operating hours and timezone
//   - Supported destinations
//
// Phase 3: Team Setup (10 minutes)
//   - Invite agents (email invites)
//   - Define roles and permissions
//   - Agent profiles and specializations
//
// Phase 4: Supplier Connections (30 minutes)
//   - Connect GDS (Amadeus credentials)
//   - Connect payment gateway (Razorpay setup)
//   - Connect communication (WhatsApp Business)
//   - Connect accounting (Tally optional)
//
// Phase 5: Configuration (20 minutes)
//   - Pricing defaults (margins, markups)
//   - Commission structure
//   - Document templates (branding)
//   - Notification preferences
//   - Workflow rules
//
// Phase 6: Test Drive (30 minutes)
//   - Create a test trip end-to-end
//   - Process a test booking
//   - Generate a test invoice
//   - Send a test notification
//
// Total estimated time: ~2 hours to fully operational

interface OnboardingStep {
  stepId: string;
  name: string;
  description: string;
  status: StepStatus;
  required: boolean;
  estimatedMinutes: number;
  helpArticle?: string;
  videoTutorial?: string;
}

type StepStatus = 'not_started' | 'in_progress' | 'completed' | 'skipped';
```

### Setup Wizard

```typescript
interface SetupWizard {
  wizardId: string;
  agencyId: string;
  currentStep: number;
  totalSteps: number;
  progress: number;                  // 0-100%
  data: Record<string, unknown>;
  savedAt?: Date;
}

// Wizard UX principles:
// 1. Progressive disclosure: Only show what's needed now
// 2. Smart defaults: Pre-fill where possible (timezone from browser, currency from country)
// 3. Inline validation: Validate each field as user types
// 4. Save and resume: Progress saved, can resume later
// 5. Skip optional: Required steps can't be skipped, optional can
// 6. Contextual help: "?" icons with explanations
// 7. Video walkthroughs: Short videos for complex steps

// Smart defaults:
// Country: India (from IP address or phone prefix)
// Currency: INR
// Timezone: IST (+05:30)
// Language: English (with Hindi option)
// Date format: DD/MM/YYYY
// Number format: Indian (1,25,000)
// Tax regime: GST (18% for travel services)

// First-run experience after setup:
// 1. Welcome modal: "Your agency is set up! Here's what to do next."
// 2. Quick-start guide: 3 recommended first actions
//    a. Create your first trip from a template
//    b. Invite your first customer
//    c. Explore the workbench
// 3. Interactive tour: Highlight key areas of the workbench
// 4. Sample data: Pre-loaded sample trip to explore
// 5. Chat support: "Need help? Click here to chat with our team"
```

### Onboarding for Existing Agencies

```typescript
interface MigrationOnboarding extends AgencyOnboarding {
  migrationPlan: DataMigration;
  parallelRunPeriod: DateRange;
  oldSystemAccess: OldSystemConfig;
}

// Migration-assisted onboarding:
// For agencies transitioning from another system:
//
// Week 1: Setup + Planning
//   - Standard onboarding (Phase 1-3)
//   - Migration planning (data assessment)
//   - Custom schema mapping
//
// Week 2: Migration + Testing
//   - Data migration (phased approach)
//   - Validation and spot-checking
//   - Agent training sessions
//
// Week 3: Parallel Run
//   - Run both systems simultaneously
//   - New bookings in platform, old system read-only
//   - Daily reconciliation between systems
//
// Week 4: Go-Live + Support
//   - Full switch to platform
//   - Old system archived (not deleted)
//   - Intensive support period
//   - Daily check-ins with agency admin

// Dedicated onboarding manager:
// Assigned to agencies on Professional and Enterprise plans
// Responsibilities:
//   - Guide through setup wizard
//   - Coordinate data migration
//   - Train agents (remote or on-site for Enterprise)
//   - First week post-go-live support
//   - Monthly check-in for first 3 months
```

### Onboarding Metrics

```typescript
interface OnboardingMetrics {
  // Funnel metrics
  signupToActivationRate: number;    // % who complete setup
  averageTimeToComplete: number;     // Hours from signup to first booking
  stepCompletionRates: Record<string, number>;
  abandonmentPoints: string[];       // Where users drop off

  // Quality metrics
  firstBookingSuccessRate: number;   // % whose first booking works correctly
  supportTicketRate: number;         // Tickets filed during onboarding
  configurationErrorRate: number;    // Errors found in initial config

  // Business metrics
  timeToFirstRevenue: number;        // Days from signup to first paid booking
  trialToPaidConversion: number;     // % who convert from trial
  onboardingNPS: number;             // Onboarding satisfaction score
}

// Onboarding success criteria:
// Setup completion rate > 80%
// Average time to complete < 3 hours
// First booking success rate > 95%
// Time to first revenue < 7 days
// Onboarding NPS > 50
```

---

## Open Problems

1. **Setup complexity vs. flexibility** — Too many configuration options overwhelm new users. Too few restrict power users. Need progressive disclosure.

2. **Integration setup friction** — Connecting Amadeus or Razorpay requires accounts with those providers. The platform can't automate external account creation.

3. **Agency size variation** — A solo agent needs minimal setup. A 50-person agency needs team structure, permissions, and migration. One flow doesn't fit all.

4. **Mobile onboarding** — Some agencies may sign up on mobile. Setup wizard needs to work on small screens.

5. **Onboarding for non-technical users** — Travel agents are not developers. Technical setup (API keys, webhooks) needs simplified UX.

---

## Next Steps

- [ ] Design setup wizard with progressive disclosure
- [ ] Build onboarding flow with save-and-resume
- [ ] Create migration-assisted onboarding for existing agencies
- [ ] Design first-run experience with interactive tour
- [ ] Study onboarding UX (Shopify, Notion, Slack onboarding)
