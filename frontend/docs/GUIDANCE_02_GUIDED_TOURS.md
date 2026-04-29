# User Guidance & Helper System — Guided Tours & Interactive Walkthroughs

> Research document for step-by-step guided tours, interactive walkthroughs, product tours, and feature discovery flows.

---

## Key Questions

1. **How do guided tours teach agents to use the platform effectively?**
2. **What interactive walkthrough system supports complex multi-step flows?**
3. **How do feature discovery tours introduce new capabilities?**
4. **What tour analytics measure effectiveness?**
5. **How do tours adapt to different learning styles?**

---

## Research Areas

### Guided Tour Framework

```typescript
interface GuidedTourSystem {
  tours: Tour[];
  player: TourPlayer;
  builder: TourBuilder;
  analytics: TourAnalytics;
  scheduling: TourScheduling;
}

interface Tour {
  id: string;
  name: string;
  description: string;
  category: TourCategory;
  audience: TourAudience;
  steps: TourStep[];
  duration: number;                    // Estimated minutes
  prerequisites?: string[];            // Tour IDs that should be completed first
  rewards?: TourReward;
  version: number;                     // Tour content version
  active: boolean;
  createdAt: Date;
  updatedAt: Date;
}

type TourCategory =
  | 'onboarding'                       // First-time user introduction
  | 'feature_discovery'                // Introducing a new feature
  | 'workflow'                         // Teaching a specific workflow
  | 'best_practice'                    // Productivity tips and tricks
  | 'compliance';                      // Regulatory training

type TourAudience =
  | 'all_users'
  | 'new_agents'
  | 'experienced_agents'
  | 'managers'
  | 'admins'
  | 'custom';                          // Specific user IDs or roles

// Tour catalog:
// ┌─────────────────────────────────────────┐
// │  🎓 Learning Center                      │
// │                                            │
// │  Getting Started (4 tours)                 │
// │  ├ ✅ Welcome Tour (5 min)          [Done]│
// │  ├ ✅ Your Inbox (3 min)            [Done]│
// │  ├ ⬜ Trip Workspace (5 min)              │
// │  └ ⬜ First Trip (8 min)                  │
// │                                            │
// │  Core Features (6 tours)                   │
// │  ├ ⬜ Trip Builder (5 min)                │
// │  ├ ⬜ Customer Messages (4 min)           │
// │  ├ ⬜ Document Generation (4 min)         │
// │  ├ ⬜ Filtering & Views (5 min)           │
// │  ├ ⬜ Templates & Snippets (3 min)        │
// │  └ ⬜ Calendar & Scheduling (4 min)       │
// │                                            │
// │  Advanced (4 tours)                        │
// │  ├ ⬜ Keyboard Shortcuts (4 min)          │
// │  ├ ⬜ Batch Operations (3 min)            │
// │  ├ ⬜ Custom Views (5 min)                │
// │  └ ⬜ Command Palette (3 min)             │
// │                                            │
// │  🏆 Your Progress: 2/14 complete          │
// └─────────────────────────────────────────────┘
```

### Tour Step Engine

```typescript
interface TourStep {
  id: string;
  order: number;
  target?: string;                     // CSS selector for highlighted element
  title: string;
  content: string;                     // Markdown supported
  media?: TourMedia;
  interaction?: TourInteraction;
  position: StepPosition;
  highlight: HighlightConfig;
  navigation: StepNavigation;
  skipCondition?: string;              // Skip if condition met
  validation?: StepValidation;
}

type StepPosition =
  | 'top' | 'bottom' | 'left' | 'right'
  | 'center'                           // Modal overlay (no target)
  | 'auto';                            // Auto-position based on space

interface HighlightConfig {
  type: 'spotlight' | ' 'pointer' | 'outline' | 'pulse';
  padding: number;                     // Pixels around target
  backdrop: boolean;                   // Dim rest of page
  backdropClick: 'dismiss' | 'next' | 'block';
}

// Highlight types:
//
// SPOTLIGHT: Dark overlay with cutout around target
// ┌─────────────────────────────────────────┐
// │  ████████████████████████████████████████ │
// │  ████████████████████████████████████████ │
// │  ████████ ┌─────────────┐ ██████████████ │
// │  ████████ │  [Confirm]  │ ██████████████ │
// │  ████████ └─────────────┘ ██████████████ │
// │  ████████                    ███████████ │
// │  ████████  Click Confirm to  ███████████ │
// │  ████████  proceed          ███████████ │
// │  ████████  [Next →]         ███████████ │
// │  ████████████████████████████████████████ │
// └─────────────────────────────────────────┘
//
// POINTER: Arrow pointing to element, no overlay
// ┌─────────────────────────────────────────┐
// │  [Status ▼]                              │
// │       ↓                                   │
// │  Use this dropdown to change trip status  │
// │  [Next →] [Skip]                         │
// └─────────────────────────────────────────────┘
//
// PULSE: Animated ring around target element
// Element pulses with a glowing ring to draw attention
// Tooltip nearby explains what to do

interface TourMedia {
  type: 'image' | 'gif' | 'video' | 'lottie';
  url: string;
  alt: string;
  width?: string;
  height?: string;
}

interface TourInteraction {
  type: 'click' | 'type' | 'select' | 'drag' | 'observe';
  target: string;
  value?: string;                      // For type actions
  waitFor?: number;                    // Ms to wait for result
  successCondition?: string;           // How to know it worked
}

// Interactive step types:
//
// CLICK: User must click the highlighted element
// "Click the 'Confirm' button to change trip status"
// Tour waits for click before proceeding
//
// TYPE: User must type into a field
// "Try typing 'Kerala' in the destination field"
// Tour validates the input
//
// SELECT: User must select an option
// "Select 'Confirmed' from the status dropdown"
// Tour waits for selection
//
// OBSERVE: User just reads and clicks Next
// "This is the trip timeline — it shows all trip events"
// No interaction required, just acknowledgment
//
// DRAG: User must drag an element
// "Drag the hotel card to rearrange the itinerary order"

interface StepNavigation {
  nextLabel?: string;                  // Custom "Next" button text
  showSkip: boolean;
  showBack: boolean;
  showProgress: boolean;               // "Step 3 of 8"
  autoAdvance: boolean;                // Auto-advance after interaction
  autoAdvanceDelay?: number;           // Ms before auto-advance
}

interface StepValidation {
  // Validate that a step was completed correctly:
  type: 'input_match' | 'element_visible' | 'state_change' | 'api_call';
  expected?: any;
  failureMessage?: string;             // If validation fails
  retryable: boolean;
}
```

### Feature Discovery Tours

```typescript
interface FeatureDiscovery {
  announcements: FeatureAnnouncement[];
  changelog: ChangelogSystem;
  whatIsNew: WhatsNewPanel;
}

interface FeatureAnnouncement {
  id: string;
  featureName: string;
  version: string;                     // Platform version that introduced it
  title: string;
  description: string;
  media?: TourMedia;
  tour?: string;                       // Tour ID for detailed walkthrough
  audience: TourAudience;
  priority: 'low' | 'medium' | 'high' | 'critical';
  startDate: Date;
  endDate?: Date;                      // Stop showing after this date
  dismissedBy: string[];               // User IDs who dismissed
}

// Feature announcement delivery:
//
// IN-APP BANNER (high priority):
// ┌─────────────────────────────────────────┐
// │  ✨ New: Batch Operations                  │
// │  Select multiple trips and confirm,       │
// │  assign, or message them all at once.     │
// │  [Try It Now] [Take Tour] [Dismiss]       │
// └─────────────────────────────────────────────┘
//
// SPOTLIGHT ON NEW ELEMENT (medium priority):
// When new UI element appears, pulse highlight it
// "This is new! Click to learn about [feature]"
//
// WHAT'S NEW PANEL (all features):
// ┌─────────────────────────────────────────┐
// │  🆕 What's New — April 2026              │
// │                                            │
// │  Batch Operations            [NEW]        │
// │  Select and action multiple trips.         │
// │  [Learn More]                              │
// │                                            │
// │  Smart Filter Suggestions     [NEW]        │
// │  AI-powered filter recommendations.       │
// │  [Learn More]                              │
// │                                            │
// │  Improved WhatsApp Templates [IMPROVED]   │
// │  New variables and Hinglish support.      │
// │  [Learn More]                              │
// │                                            │
// │  📋 Previous months: [Mar] [Feb] [Jan]   │
// └─────────────────────────────────────────────┘
//
// CHANGELOG:
// Full changelog accessible from help menu
// Organized by date, tagged by feature area
// Includes: New, Improved, Fixed, Deprecated

// Feature discovery scheduling:
// - New agents: See all relevant features on first login
// - Existing agents: See only features added since last login
// - Power users: Compact changelog (no tours)
// - Managers: Features relevant to team management highlighted

// Changelog system:
interface ChangelogSystem {
  entries: ChangelogEntry[];
  categories: ('new' | 'improved' | 'fixed' | 'deprecated' | 'removed')[];
  versions: VersionInfo[];
}

interface ChangelogEntry {
  id: string;
  version: string;
  date: Date;
  category: string;
  title: string;
  description: string;
  impact: 'agent' | 'customer' | 'manager' | 'admin' | 'all';
  tour?: string;
  documentation?: string;              // Link to full docs
  feedbackId?: string;                 // Feedback collection ID
}
```

### Tour Builder & Management

```typescript
interface TourBuilder {
  mode: 'visual' | 'code';
  recorder: TourRecorder;
  editor: TourEditor;
  preview: TourPreview;
  publishing: TourPublishing;
}

interface TourRecorder {
  // Record tours by performing the action:
  // 1. Start recording mode
  // 2. Perform actions on the page
  // 3. Builder captures: clicks, inputs, navigation
  // 4. Each action becomes a tour step
  // 5. Builder auto-generates step descriptions
  // 6. Creator edits descriptions, adds media
  // 7. Preview tour
  // 8. Publish
  //
  // Recording flow:
  // [🔴 Recording...] → Click Confirm → Auto-capture step
  // ┌─────────────────────────────────────────┐
  // │  Tour Builder                            │
  // │                                            │
  // │  Step 3: Click "Confirm" button            │
  // │  Target: button[data-action="confirm"]     │
  // │  Type: click                               │
  // │  Description: "Click Confirm to..."        │
  // │  [Edit] [Delete] [Re-record]              │
  // │                                            │
  // │  Steps: [1] [2] [3●] [+ Add]             │
  // │                                            │
  // │  [Preview] [Save Draft] [Publish]         │
  // └─────────────────────────────────────────────┘
}

interface TourEditor {
  // Visual editor for tour steps:
  // - Drag to reorder steps
  // - Edit step content (title, description, media)
  // - Set highlight type and position
  // - Add interaction requirements
  // - Set skip conditions
  // - Add validation rules
  // - Preview individual steps or full tour
  //
  // Advanced options:
  // - Branching: Different paths based on user choice
  // - Conditional steps: Skip if user already knows
  // - Delay steps: Wait for page load before showing
  // - Exit conditions: End tour early if...
}

interface TourPreview {
  // Preview tour as users would see it:
  // - Exact rendering of highlights, tooltips, modals
  // - Test all interaction types
  // - Verify step order and flow
  // - Check timing and auto-advance
  // - Test skip conditions
  // - Mobile preview mode
}

interface TourPublishing {
  // Tour lifecycle:
  // DRAFT → REVIEW → PUBLISHED → ARCHIVED
  //
  // DRAFT: Being created, only creator can see
  // REVIEW: Submitted for review (manager or content team)
  // PUBLISHED: Visible to target audience
  // ARCHIVED: No longer shown, but analytics preserved
  //
  // Publishing options:
  // - Audience: Who should see this tour?
  // - Scheduling: When should it appear?
  // - Frequency: How often to show?
  // - Auto-trigger: What action starts this tour?
  // - Manual trigger: Available from tour catalog
  // - Mandatory: Required for compliance training
}

interface TourAnalytics {
  // Tour effectiveness metrics:
  tourId: string;
  metrics: {
    started: number;                   // How many users started
    completed: number;                 // How many completed all steps
    completionRate: number;            // completed / started
    avgCompletionTime: number;         // Seconds
    dropOffStep: number;               // Step where most users quit
    dropOffRate: number;               // % who didn't complete
    skippedSteps: Record<string, number>; // Step → skip count
    ratings: {
      helpful: number;
      notHelpful: number;
    };
    actionAfterTour: string;           // What users did after completing
  };
  stepMetrics: StepMetric[];
}

interface StepMetric {
  stepId: string;
  timeOnStep: number;                  // Avg seconds
  interactionRate: number;             // % who completed interaction
  skipRate: number;                    // % who skipped
  validationFailRate: number;          // % who failed validation
}

// Analytics insights:
// - "85% complete the Welcome Tour, but drop-off spikes at Step 4 (Keyboard Shortcuts)"
// - "Users who complete the Trip Builder tour convert 2x better than those who don't"
// - "The Batch Operations tour has 30% completion — content too long?"
// - "Step 3 validation fails 40% of the time — instruction unclear?"
//
// Tour improvement cycle:
// 1. Collect analytics for 2 weeks
// 2. Identify drop-off points and failures
// 3. Rewrite unclear instructions
// 4. Split long tours into shorter ones
// 5. Remove unnecessary steps
// 6. Re-publish and measure improvement
```

---

## Open Problems

1. **Tour engagement decline** — Users skip or dismiss tours, especially experienced agents who think they don't need training. Making tours feel like helpful discovery rather than mandatory training is a UX and content design challenge.

2. **Tour fragility** — Tours that target specific CSS selectors break when the UI changes. A tour targeting `button.confirm-trip` breaks if the button class changes to `button[data-action="confirm"]`. Tour maintainability requires a robust targeting strategy.

3. **Interactive tour complexity** — Tours with interactive steps (type, drag, select) need to handle edge cases: what if the user types something unexpected? What if the drag target moved? Robust validation for interactive steps is hard.

4. **Feature announcement fatigue** — If every minor update triggers an announcement, users start ignoring all of them. Thresholding (only announce significant features) and personalization (only show relevant features) are essential.

5. **Tour localization** — Tour content (text, media, examples) needs translation for multilingual agents. Gif/video content is especially hard to localize. Text-only tours are easier to translate but less engaging.

---

## Next Steps

- [ ] Build guided tour framework with spotlight, pointer, and pulse highlight modes
- [ ] Create tour builder with visual editor and recording capability
- [ ] Implement feature discovery and announcement system with scheduling
- [ ] Design tour analytics with completion tracking and drop-off analysis
- [ ] Study tour platforms (Pendo, Appcues, UserGuiding, WhatFix, Inline Manual)
