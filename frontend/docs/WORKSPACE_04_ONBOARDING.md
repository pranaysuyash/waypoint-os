# Workspace Customization & Agent Productivity — Onboarding, Presets & Progressive Disclosure

> Research document for new agent workspace setup, progressive feature disclosure, workspace onboarding flows, and role-based default configurations.

---

## Key Questions

1. **How do new agents get productive quickly with a well-configured workspace?**
2. **What progressive disclosure system prevents feature overload?**
3. **How do role-based presets give agents a strong starting configuration?**
4. **What guided tour and training system accelerates onboarding?**
5. **How do workspaces evolve as agents gain expertise?**

---

## Research Areas

### New Agent Workspace Setup

```typescript
interface OnboardingSystem {
  flow: OnboardingFlow;
  presets: RolePreset[];
  progressiveDisclosure: ProgressiveDisclosure;
  guidedTour: GuidedTour;
  mentorship: MentorshipLink;
}

interface OnboardingFlow {
  steps: OnboardingStep[];
  personalization: PersonalizationSurvey;
  workspaceSetup: WorkspaceSetup;
  firstTrip: FirstTripGuide;
}

// Onboarding flow stages:
//
// STAGE 1: Welcome & Role Selection (2 min)
// ┌─────────────────────────────────────────┐
// │  Welcome to Waypoint OS! 🎉              │
// │                                            │
// │  What's your role?                         │
// │                                            │
// │  ┌──────────────┐  ┌──────────────┐       │
// │  │ 🗺️ Travel    │  │ 📊 Senior    │       │
// │  │    Agent     │  │    Agent     │       │
// │  │  Handle trips│  │  Lead + mentor│      │
// │  └──────────────┘  └──────────────┘       │
// │  ┌──────────────┐  ┌──────────────┐       │
// │  │ 👔 Manager   │  │ 🔧 Admin     │       │
// │  │  Team ops    │  │  System cfg  │       │
// │  └──────────────┘  └──────────────┘       │
// │                                            │
// │  How much experience do you have?          │
// │  ○ Less than 1 year                       │
// │  ○ 1-3 years                              │
// │  ● 3-5 years                              │
// │  ○ 5+ years                               │
// └─────────────────────────────────────────────┘
//
// STAGE 2: Workspace Personalization (3 min)
// ┌─────────────────────────────────────────┐
// │  Personalize Your Workspace               │
// │                                            │
// │  What destinations do you specialize in?   │
// │  [☑ Kerala] [☑ Goa] [☐ Rajasthan]        │
// │  [☐ Thailand] [☑ Dubai] [☐ Europe]       │
// │  [+ Add more]                             │
// │                                            │
// │  How do you prefer to work?                │
// │  ○ Single trip at a time (focused)        │
// │  ● Multiple trips (power user)            │
// │  ○ Communication-first (inbox driven)     │
// │                                            │
// │  Which channels do you use most?           │
// │  [☑ WhatsApp] [☑ Phone] [☐ Email]        │
// │  [☐ SMS] [☐ In-app chat]                 │
// │                                            │
// │  What's your primary device?               │
// │  ○ Desktop (large monitor)                │
// │  ● Laptop (13-15")                        │
// │  ○ Tablet                                 │
// │                                            │
// │  [Back] [Set Up My Workspace →]           │
// └─────────────────────────────────────────────┘
//
// STAGE 3: First Tour (5 min)
// Guided tour of workspace with highlights:
// 1. "This is your inbox — all trips appear here"
// 2. "Click any trip to open the workspace"
// 3. "The timeline shows trip activities"
// 4. "Use the decision panel for risk assessment"
// 5. "Generate documents from the output panel"
// 6. "Press '?' anytime to see keyboard shortcuts"
//
// STAGE 4: First Trip (Assisted)
// Walk through creating a test trip:
// 1. "Let's create your first trip!"
// 2. Provides sample customer data
// 3. Guides through intake → quote → itinerary
// 4. Shows how to send to customer
// 5. Marks onboarding complete

interface PersonalizationSurvey {
  role: AgentRole;
  experience: ExperienceLevel;
  specializations: string[];
  workStyle: WorkStyle;
  channels: string[];
  primaryDevice: DeviceType;
  language: string;                    // Preferred UI language
}

type AgentRole = 'junior_agent' | 'agent' | 'senior_agent' | 'manager' | 'admin';
type ExperienceLevel = 'new' | '1-3_years' | '3-5_years' | '5+_years';
type WorkStyle = 'focused' | 'power_user' | 'communication_first' | 'methodical';
type DeviceType = 'desktop' | 'laptop' | 'tablet';

// Workspace setup based on personalization:
// NEW + JUNIOR AGENT:
// - Simplified layout: Inbox + Trip Detail (2 panels)
// - Limited sidebar: Inbox, Trips, Help
// - Guided mode: Tooltips on every action
// - Template-heavy: Encourage template usage
// - Mentor linked: Senior agent assigned
//
// EXPERIENCED AGENT:
// - Power layout: 3-panel (Inbox + Active + Context)
// - Full sidebar: All items visible
// - Keyboard shortcuts enabled
// - Custom views: Suggested based on specializations
// - Advanced features: Batch operations, quick actions
//
// MANAGER:
// - Dashboard layout: Team overview + Analytics
// - Manager sidebar: Team, Analytics, Approvals, Reports
// - Team management tools visible
// - Workload balance dashboard
// - Audit trail access
```

### Progressive Disclosure System

```typescript
interface ProgressiveDisclosure {
  levels: DisclosureLevel[];
  triggers: DisclosureTrigger[];
  tracking: FeatureUsageTracking;
  ui: DisclosureUI;
}

interface DisclosureLevel {
  level: number;                       // 1-5
  name: string;                        // "Essentials", "Standard", "Advanced"
  description: string;
  features: string[];                  // Feature IDs available at this level
  uiElements: UIElementConfig[];       // What's shown/hidden
}

// Progressive disclosure levels:
//
// LEVEL 1: "Essentials" (Day 1-3 for new agents, always for observers)
// ─────────────────────────────────────────
// Features available:
// - Inbox (trip list, basic filters)
// - Trip detail view (read-only initially)
// - Send message (pre-approved templates only)
// - Basic status changes (draft → pending)
// - View customer info
// - View itinerary
//
// UI Simplifications:
// - No keyboard shortcuts shown
// - No batch operations
// - No custom views
// - Limited filter options (status, assigned to me)
// - No quick actions bar
// - Tooltips on all actions
// - "Need help?" button always visible
//
// LEVEL 2: "Standard" (Day 3-14, or immediately for experienced hires)
// ─────────────────────────────────────────
// Unlocks:
// - Full filter builder
// - Create and save views
// - Message composition (free text)
// - All status changes
// - Basic quick actions
// - Templates and snippets
// - Basic keyboard shortcuts (j/k, enter, escape)
// - Export (PDF, Excel)
// - Calendar view
//
// LEVEL 3: "Advanced" (Day 14-30)
// ─────────────────────────────────────────
// Unlocks:
// - Custom views with complex filters
// - Batch operations
// - All keyboard shortcuts
// - Command palette
// - Custom templates
// - Dashboard widgets
// - Advanced search
// - Trip duplication
//
// LEVEL 4: "Power User" (Day 30+)
// ─────────────────────────────────────────
// Unlocks:
// - Workspace layout customization
// - Sidebar customization
// - Keyboard shortcut customization
// - Smart filter suggestions
// - Productivity analytics
// - API access (if permitted)
// - Plugin installation
//
// LEVEL 5: "Expert" (Manual unlock by manager)
// ─────────────────────────────────────────
// Unlocks:
// - Team view sharing
// - Mentoring tools
// - Advanced analytics
// - Custom report builder
// - Bulk import/export
// - Automation rules

interface DisclosureTrigger {
  featureId: string;
  trigger: TriggerType;
  condition: TriggerCondition;
}

type TriggerType =
  | 'time_based'                       // After X days since account creation
  | 'usage_based'                      // After using related feature Y times
  | 'skill_based'                      // After completing training module
  | 'manager_approval'                 // Manager explicitly unlocks
  | 'achievement';                     // After reaching a milestone

// Trigger examples:
//
// TIME-BASED:
// - Level 2 unlocks after 3 days (regardless of usage)
// - Level 3 unlocks after 14 days
// - Level 4 unlocks after 30 days
//
// USAGE-BASED:
// - "You've sent 20 messages — try quick reply templates!"
//   Trigger: message_count >= 20 → Unlock snippets
// - "You use filters often — try saving a custom view"
//   Trigger: filter_usage >= 10 → Unlock saved views
// - "You handle multiple trips — try batch operations"
//   Trigger: trips_handled >= 15 → Unlock batch
//
// SKILL-BASED:
// - After completing "Advanced Filtering" tutorial → Unlock complex filters
// - After completing "Keyboard Shortcuts" tutorial → Unlock shortcut hints
// - After completing "Templates" tutorial → Unlock template creation
//
// ACHIEVEMENT:
// - First trip confirmed → "Great job! Try the command palette (ctrl+k)"
// - 10 trips handled → "You're a natural! Customize your workspace"
// - First 5-star review → "Amazing! Check your productivity dashboard"

interface FeatureUsageTracking {
  // Track which features each agent uses:
  // - Feature ID + timestamp + context
  // - Aggregate: Daily/weekly usage counts per feature
  // - Pattern detection: "Uses keyboard shortcuts 80% of the time"
  //
  // Privacy:
  // - Only aggregate usage patterns, not individual actions
  // - Agent can opt out of tracking
  // - Data used for: disclosure triggers, UX improvements
  // - Data NOT used for: performance evaluation (separate system)
  // - Auto-delete tracking data after 90 days
}

interface DisclosureUI {
  // How new features are revealed:
  //
  // SPOTLIGHT:
  // ┌─────────────────────────────────────────┐
  // │  ✨ New Feature Available                 │
  // │                                            │
  // │  You can now save custom views to quickly  │
  // │  access your most common filters.          │
  // │                                            │
  // │  [Try It Now] [Show Me How] [Maybe Later] │
  // └─────────────────────────────────────────────┘
  //
  // INLINE HINT:
  // ┌─────────────────────────────────────────┐
  // │  Filters: [Status ▼] [Agent ▼]  [💾Save]│ ← New button appeared
  // │                        ↑                  │
  // │            "Save this filter as a view"   │ ← Tooltip on hover
  // └─────────────────────────────────────────────┘
  //
  // BADGE:
  // ┌─────────────────────────────────────────┐
  // │  Sidebar:                                 │
  // │  Inbox                            [5]    │
  // │  ✨ Keyboard Shortcuts        [NEW]      │ ← New item with badge
  // │  Trips                                    │
  // └─────────────────────────────────────────────┘
  //
  // PROGRESSIVE HINTS (non-blocking):
  // - First time using a feature: Brief tooltip
  // - Third time: "Pro tip: You can also use keyboard shortcut 's'"
  // - Tenth time: No more hints (feature is learned)
}
```

### Role-Based Workspace Presets

```typescript
interface WorkspacePreset {
  id: string;
  name: string;                        // "Standard Agent Setup"
  description: string;
  role: AgentRole;
  experience: ExperienceLevel;
  layout: WorkspaceLayout;
  sidebar: SidebarConfig;
  views: SavedView[];
  shortcuts: KeyboardProfile;
  features: FeatureConfig;
  mandatory: boolean;                  // Cannot be modified (compliance)
  customizable: string[];              // Features agent can customize
  createdAt: Date;
  createdBy: string;                   // Manager who created preset
}

// Role-based presets:
//
// JUNIOR AGENT PRESET:
// Layout: 2-panel (Inbox + Trip Detail)
// Sidebar: Inbox, Trips, Help (minimal)
// Default view: "My Trips" (assignedAgent = me)
// Features: Template-heavy, guided mode
// Keyboard: Basic only (j/k, enter, escape)
// Restrictions:
//   - Cannot modify trip price beyond 10% of template
//   - Cannot confirm trips (requires senior approval)
//   - Cannot send free-text messages (templates only, day 1-3)
//   - Cannot delete trips
//   - Max 15 active trips at a time
//
// AGENT PRESET:
// Layout: 3-panel (Inbox + Active + Context)
// Sidebar: Full (Inbox, Messages, Calendar, Customers, Templates, Help)
// Default view: "My Active Trips"
// Features: Full feature set at Level 3
// Keyboard: Full shortcut set
// Customizable:
//   - Layout (can switch to power agent layout)
//   - Views (create/edit own views)
//   - Sidebar (reorder, hide items)
//   - Shortcuts (can remap)
//
// SENIOR AGENT PRESET:
// Layout: Power Agent (3-panel + analytics widget)
// Sidebar: Full + Mentoring, Advanced Analytics
// Default view: "My Priority Queue" (custom sort)
// Additional features:
//   - Mentor tools (view mentee trips)
//   - Approval queue (approve junior agent trips)
//   - Advanced analytics (personal + mentee)
//   - Custom report builder
//
// MANAGER PRESET:
// Layout: Dashboard + Team view
// ┌──────────┬──────────────────────┬──────────────────┐
// │ [Team]   │  Team Dashboard      │  Trip Detail     │
// │          │                      │  (when selected) │
// │ Agents ● │  Workload balance    │                  │
// │ Trips    │  Pipeline metrics    │  [Intake]        │
// │ Approvals│  Revenue tracker     │  [Timeline]      │
// │ Reports  │  Alerts & flags      │  [Decision]      │
// │ Audit    │                      │  [Output]        │
// │ Settings │                      │                  │
// └──────────┴──────────────────────┴──────────────────┘
// Additional features:
//   - Team management (add/remove agents)
//   - View all agents' trips
//   - Reassign trips between agents
//   - Set team targets
//   - Audit trail access
//   - Preset management
//   - Mandatory view creation
//
// ADMIN PRESET:
// Layout: Full admin console
// Additional features:
//   - System configuration
//   - User management
//   - Integration settings
//   - Billing and subscription
//   - Data export/import
//   - Audit logs
//   - Plugin management

// Preset application flow:
// 1. Manager creates preset → Saves to organization
// 2. New agent added → Role selected → Preset auto-applied
// 3. Agent sees configured workspace on first login
// 4. Agent can customize non-mandatory elements
// 5. Manager can push preset updates → Agents notified
// 6. Customizations preserved unless element is mandatory
//
// Preset conflict resolution:
// Manager updates preset: "Added 'Compliance Flags' as mandatory sidebar item"
// Agent had hidden this item → Item restored, cannot be hidden
// Agent's other customizations (sidebar order, views) preserved
// Notification: "Your workspace was updated. 1 mandatory change applied."
```

### Guided Tours & Training

```typescript
interface GuidedTourSystem {
  tours: Tour[];
  contextualHelp: ContextualHelp;
  trainingModules: TrainingModule[];
  certifications: Certification[];
}

interface Tour {
  id: string;
  name: string;                        // "Inbox Mastery"
  description: string;
  steps: TourStep[];
  duration: number;                    // Minutes
  prerequisite?: string;               // Tour ID
  reward?: TourReward;
}

interface TourStep {
  target: string;                      // CSS selector for element
  position: 'top' | 'bottom' | 'left' | 'right';
  title: string;
  content: string;
  action?: TourAction;                 // Optional interaction required
  skipIf?: string;                     // Condition to skip step
}

type TourAction =
  | { type: 'click'; target: string }
  | { type: 'type'; target: string; value: string }
  | { type: 'observe' }                // Just read and acknowledge
  | { type: 'keyboard'; keys: string };

// Tour catalog:
//
// BEGINNER TOURS (Day 1):
// 1. "Welcome Tour" (5 min) — Layout overview
// 2. "Your Inbox" (3 min) — Trip list navigation
// 3. "Opening a Trip" (3 min) — Trip detail workspace
// 4. "Sending a Message" (2 min) — Message composer
//
// INTERMEDIATE TOURS (Week 1):
// 5. "Filters & Views" (5 min) — Building filtered views
// 6. "Trip Templates" (4 min) — Using and customizing templates
// 7. "Customer Communication" (5 min) — WhatsApp, email, phone
// 8. "Generating Documents" (4 min) — Itinerary, invoice, voucher
//
// ADVANCED TOURS (Month 1):
// 9. "Keyboard Shortcuts" (5 min) — Power user navigation
// 10. "Batch Operations" (4 min) — Multi-trip actions
// 11. "Custom Views" (5 min) — Complex filter composition
// 12. "Command Palette" (3 min) — Quick actions and search
//
// EXPERT TOURS (Month 2+):
// 13. "Workspace Customization" (5 min) — Layout, sidebar, widgets
// 14. "Analytics & Insights" (4 min) — Productivity dashboard
// 15. "Automation Rules" (5 min) — Custom workflow automation
// 16. "Plugin System" (4 min) — Installing and using plugins

interface ContextualHelp {
  // Always-available help system:
  //
  // HELP BUTTON (? icon):
  // - Floating button in bottom-right corner
  // - Opens contextual help panel
  // - Shows: Related tours, keyboard shortcuts, FAQ
  //
  // CONTEXT-AWARE:
  // - On inbox: "How to filter trips", "Keyboard shortcuts"
  // - On trip detail: "How to confirm a trip", "Document generation"
  // - On messages: "Templates", "Quick reply shortcuts"
  // - On filters: "Building complex filters", "Saving views"
  //
  // TOOLTIPS:
  // - Hover over any icon → Brief tooltip
  // - Hover + hold (1.5s) → Extended tooltip with link to tour
  //
  // ERROR HELP:
  // - When action fails: "Why did this fail?" link
  // - Explains reason and suggests fix
  // - Links to relevant help article
  //
  // SEARCH HELP:
  // - Search bar in help panel
  // - Searches: Tours, articles, FAQ, keyboard shortcuts
  // - Shows results with relevance ranking

  helpArticles: HelpArticle[];
  faq: FAQEntry[];
  shortcuts: ShortcutReference;
}

interface TrainingModule {
  id: string;
  name: string;                        // "Kerala Destination Specialist"
  description: string;
  type: 'product' | 'destination' | 'skill' | 'compliance';
  lessons: Lesson[];
  assessment?: Assessment;
  certification?: string;              // Certification ID on completion
  duration: number;                    // Minutes
  mandatory: boolean;
}

// Training modules:
// PRODUCT TRAINING:
// - "Waypoint OS Basics" (30 min, mandatory for all)
// - "Advanced Trip Builder" (45 min)
// - "Customer Communication" (30 min)
// - "Document Generation" (20 min)
// - "Analytics & Reporting" (25 min)
//
// DESTINATION TRAINING:
// - "Kerala Specialist" (60 min) — Destinations, hotels, activities, seasons
// - "Goa Expert" (45 min)
// - "Rajasthan Heritage" (60 min)
// - "International: Thailand" (45 min)
// - "International: Dubai" (40 min)
//
// SKILL TRAINING:
// - "Effective Customer Communication" (30 min)
// - "Upselling Techniques" (25 min)
// - "Handling Complaints" (20 min)
// - "Travel Insurance Sales" (15 min)
//
// COMPLIANCE TRAINING:
// - "DPDP Act Compliance" (20 min, mandatory)
// - "GST for Travel Services" (25 min, mandatory for billing)
// - "Anti-Money Laundering" (15 min, mandatory)
// - "Customer Data Handling" (20 min, mandatory)

interface Certification {
  id: string;
  name: string;                        // "Kerala Destination Specialist"
  issuedAt: Date;
  expiresAt: Date;                     // Renewal required annually
  badge: string;                       // Badge shown on profile
  visible: boolean;                    // Show on customer-facing profile
}

// Certification display:
// Agent profile in trip shows badges:
// ┌─────────────────────────────────────────┐
// │  Priya Sharma                             │
// │  Travel Agent · 3 years experience       │
// │                                            │
// │  🏅 Kerala Specialist                     │
// │  🏖️ Goa Expert                            │
// │  📞 Customer Communication                │
// │                                            │
// │  Customer Rating: ⭐⭐⭐⭐⭐ (4.8)        │
// │  Trips handled: 340                       │
// └─────────────────────────────────────────────┘
```

### Workspace Evolution & Maturity Model

```typescript
interface WorkspaceMaturity {
  levels: MaturityLevel[];
  transitions: MaturityTransition[];
  tracking: MaturityTracking;
}

interface MaturityLevel {
  level: number;                       // 1-5
  name: string;                        // "Novice", "Competent", "Proficient"
  description: string;
  workspaceConfig: WorkspaceLayout;
  featureAccess: string[];             // Feature IDs
  expectedDuration: string;            // "1-2 weeks"
  indicators: string[];                // Behavioral indicators
}

// Maturity model:
//
// LEVEL 1: NOVICE (Day 1-7)
// Workspace: Simplified 2-panel, tooltips enabled, template-heavy
// Indicators:
//   - Uses mouse for all navigation
//   - Sends only template messages
//   - Processes <5 trips per day
//   - Asks mentor frequently
//
// LEVEL 2: COMPETENT (Week 2-4)
// Workspace: Standard 3-panel, basic shortcuts enabled
// Indicators:
//   - Starts using keyboard for navigation (j/k)
//   - Customizes some messages beyond templates
//   - Processes 5-10 trips per day
//   - Creates first saved view
//   - Completes destination training
//
// LEVEL 3: PROFICIENT (Month 2-3)
// Workspace: Power layout, full shortcuts, custom views
// Indicators:
//   - Uses keyboard shortcuts regularly
//   - Creates custom templates and snippets
//   - Processes 10-15 trips per day
//   - Uses batch operations
//   - Mentions keyboard shortcuts to colleagues
//   - Customizes workspace layout
//
// LEVEL 4: EXPERT (Month 4-6)
// Workspace: Fully customized, analytics visible
// Indicators:
//   - Uses command palette fluently
//   - Creates automation rules
//   - Processes 15-20 trips per day
//   - Trains newer agents
//   - Suggests product improvements
//   - Achieves top-quartile conversion rate
//
// LEVEL 5: MENTOR (Month 6+)
// Workspace: Full access, mentoring tools enabled
// Indicators:
//   - Mentors 1-3 junior agents
//   - Creates team views and templates
//   - Contributes to template library
//   - Participates in product feedback
//   - Helps shape agency workflows

interface MaturityTransition {
  fromLevel: number;
  toLevel: number;
  trigger: 'auto' | 'manual';         // Auto-detected or manager-approved
  criteria: TransitionCriteria;
  notification: TransitionNotification;
}

interface TransitionCriteria {
  minDuration: string;                 // Minimum time at current level
  featureUsage: Record<string, number>; // Feature → min usage count
  tripsHandled: number;                // Min trips handled
  trainingCompleted: string[];         // Required training modules
  managerApproval?: boolean;           // Some transitions need approval
}

// Transition example: Level 2 → Level 3
// Criteria:
// - At Level 2 for at least 14 days
// - Used keyboard shortcuts 50+ times
// - Handled 30+ trips
// - Completed "Filters & Views" training
// - No compliance violations
// Auto-triggered when criteria met
// Agent gets notification:
// "You've leveled up! Your workspace now has advanced features.
//  [What's New] [Take the Tour] [Dismiss]"

interface MaturityTracking {
  // Automated tracking:
  // - Feature usage frequency (per session, per day)
  // - Trip handling metrics (count, time, conversion)
  // - Training completion status
  // - Time at current level
  //
  // Privacy:
  // - Tracking is transparent (agent sees own data)
  // - Manager sees aggregate team maturity, not individual granular data
  // - Tracking data auto-deleted after 1 year
  // - Agent can request data export
  //
  // Dashboard:
  // ┌─────────────────────────────────────────┐
  // │  Your Growth                             │
  // │                                            │
  // │  Level: ★★★☆☆ Proficient                 │
  // │  Next: Expert (60% criteria met)          │
  // │                                            │
  // │  Progress to Expert:                       │
  // │  ✅ 14+ days at Proficient    (23 days)   │
  // │  ✅ Command palette 100+ uses  (145)      │
  // │  ✅ 50+ trips this month       (62)       │
  // │  ⬜ "Automation Rules" training            │
  // │  ⬜ Manager approval                       │
  // │                                            │
  // │  [Complete Remaining] [View Full Report]  │
  // └─────────────────────────────────────────────┘
}
```

---

## Open Problems

1. **Onboarding drop-off** — Long onboarding flows (even 5 minutes) cause drop-off. Agents want to start working immediately. Balancing thorough setup with speed requires a "setup later" option that doesn't leave agents with a suboptimal workspace.

2. **Progressive disclosure timing** — Revealing features too early overwhelms; too late frustrates agents who already know what they want. A "show me everything" toggle for experienced hires is needed alongside the progressive system.

3. **Preset rigidity vs. personalization** — Mandatory preset elements (compliance views, required training) are necessary but feel restrictive. Framing them as "safety features" rather than "restrictions" affects adoption.

4. **Training relevance** — Generic training modules don't match every agent's daily work. A travel agent specializing in domestic Rajasthan trips may not value international Thailand training. Adaptive training paths based on specialization would help but add complexity.

5. **Maturity measurement accuracy** — Behavioral indicators (keyboard usage, template usage) are proxies for actual proficiency. An agent might use few keyboard shortcuts but be highly effective. Maturity metrics should be advisory, not evaluative.

---

## Next Steps

- [ ] Design onboarding flow with role selection and workspace personalization
- [ ] Build progressive disclosure engine with time, usage, and skill-based triggers
- [ ] Create role-based preset system with mandatory and customizable elements
- [ ] Implement guided tour framework with interactive step-by-step tutorials
- [ ] Study onboarding UX (Linear onboarding, Notion workspace setup, Slack first-run experience)
