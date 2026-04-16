# Waypoint OS UX Redesign Masterplan

**Date:** 2026-04-16  
**Status:** Draft - Ready for Review  
**Scope:** Complete dashboard and pipeline UX overhaul

---

## Executive Summary

The current Waypoint OS dashboard has critical layout issues causing text overlap, confusing information hierarchy, and poor first-time user experience. This masterplan documents the full user journey, audits current problems, and proposes a customizable, scalable architecture.

**Key Issues Identified:**
1. PipelineBar: 7 stages crammed horizontally with overlapping text labels
2. No empty states - just "Loading..." or blank areas
3. No onboarding flow - users land in "Operations Overview" with no guidance
4. No customization - every user sees the same layout regardless of role
5. Workbench pipeline has competing visual elements (PipelineFlow + Tabs showing same info)

---

## Part 1: User Journey Mapping

### Entry Point Analysis

#### Scenario A: First-Time User (New Agency)
**User:** Sarah, owner of "Wanderlust Travel Co" (3 employees)
**Goal:** Understand what Waypoint OS does and process her first inquiry

```
Entry → Email Invite / Direct Signup
  │
  ▼
[Welcome Screen]
  • "Welcome to Waypoint OS"
  • One-sentence value prop: "Process travel inquiries faster"
  • CTA: "Set up your first trip"
  │
  ▼
[Quick Setup Wizard - 3 steps]
  Step 1: Agency info (name, logo, timezone)
  Step 2: Team members (optional - can skip)
  Step 3: Connect inbox (email integration)
  │
  ▼
[First Trip Guided Experience]
  • Pre-filled sample inquiry
  • Walkthrough of each pipeline stage
  • "This is how you'll process real inquiries"
  │
  ▼
[Dashboard - Personalized View]
  • "Your pipeline is ready!"
  • Checklist: "Connect your email" → "Process first real inquiry" → "Invite team"
  • Quick actions prominently displayed
```

#### Scenario B: Daily Active User
**User:** Mike, senior agent at established agency
**Goal:** Process 5-10 inquiries efficiently, track status

```
Entry → Bookmark / Auto-login
  │
  ▼
[Dashboard - Personalized View]
  • Priority: New inquiries requiring attention
  • Pipeline summary (his assigned trips)
  • Quick filters: "Today", "Urgent", "Ready to quote"
  • One-click to workbench
  │
  ▼
[Workbench - Task-Focused]
  • Current trip in focus (from yesterday or new)
  • Stage-appropriate form pre-filled
  • Side panel: Related trips, customer history
```

#### Scenario C: Manager/Owner
**User:** Jennifer, agency owner monitoring operations
**Goal:** See team performance, spot bottlenecks

```
Entry → Dashboard with Analytics
  │
  ▼
[Operations Overview]
  • Team workload distribution
  • Pipeline velocity metrics
  • Alerts: trips stuck >48hrs, capacity issues
  • Revenue pipeline (if integrated)
```

---

## Part 2: Current Layout Audit

### Issue Matrix

| Component | Issue | Severity | Impact |
|-----------|-------|----------|--------|
| **PipelineBar** | 7 stages, labels overlap at container width <900px | Critical | Unreadable on laptops |
| **PipelineBar labels** | "Lead/Qualified/Planning/Quoted/Booked/Traveling/Complete" - too many stages visible | High | Cognitive overload |
| **StatCards** | 4 cards fixed grid, no context for new users | Medium | Numbers without meaning |
| **RecentTrips** | No data shows empty state, but no guidance | Medium | Dead end for new users |
| **Jump To nav** | Hardcoded "5 pending", "2 awaiting" - not dynamic | Low | Stale information |
| **Workbench PipelineFlow** | Competes with Tabs - same info, two visualizations | High | Redundant, confusing |
| **Decision States** | Technical labels (PROCEED_SAFE, STOP_REVIEW) | Medium | Agency terminology mismatch |

### Visual Analysis

```
Current Dashboard Layout (Desktop ~1400px)
═══════════════════════════════════════════════════════════════

Operations Overview                            Open workbench →
Waypoint OS · decision intelligence

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Active   │  │ Pending  │  │ Ready    │  │ Needs    │
│ Trips    │  │ Review   │  │ to Book  │  │ Attention│
│    12    │  │    3     │  │    5     │  │    1     │
│ +3 week  │  │ 2 overdue│  │ +1 today │  │ action   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
   [OVERLAP ZONE: At 1200px, stat cards wrap awkwardly]

┌─────────────────────────────────┬───────────────────────────┐
│  Recent Trips               See→│  Pipeline                 │
│                                  │  ┌─────────────────────┐  │
│  ● Paris Honeymoon    PROCEED  │  │ ▓▓▓▓░░▓▓░░▓░░░░▓▓▓ │  │
│    TRIP-001            SAFE     │  │ 4  3  6  5  8  2  12│  │
│    2h ago                        │  │Lead Qua Pla Quo Boo│  │ <- LABEL OVERLAP
│                                  │  │  Tri tot       Com │
│  ● Tokyo Business... BRANCH     │  │                    │
│    TRIP-002           /DRAFT    │  │  [CRAMPED TEXT]   │
│    5h ago                        │  │                    │
│                                  ├───────────────────────────┤
│  ● Bali Family Trip STOP_REVIEW │  │  Jump To              │
│    TRIP-003            [RED]     │  │  ┌─────────────────┐  │
│    1d ago                        │  │  │ Inbox queue  ●  │  │
│                                  │  │  │ 5 pending       │  │
│                                  │  │  ├─────────────────┤  │
│                                  │  │  │ Workbench    ●  │  │
│                                  │  │  │ analyze trip    │  │
│                                  │  │  ├─────────────────┤  │
│                                  │  │  │ Reviews      ●  │  │
│                                  │  │  │ 2 awaiting      │  │
│                                  │  │  └─────────────────┘  │
│                                  │  │                       │
│                                  │  │  Decision States      │
│                                  │  │  ● PROCEED_SAFE       │
│                                  │  │  ● BRANCH / DRAFT     │
│                                  │  │  ● STOP_REVIEW        │
│                                  │  │  ● ASK_FOLLOWUP       │
└──────────────────────────────────┴───────────────────────────┘

CRITICAL ISSUES:
1. Pipeline bar labels overlap at 1000-1200px viewport
2. "Lead/Qualified/Planning" etc - what do these mean to travel agents?
3. No empty state guidance for first-time users
4. Technical decision states don't match travel industry terminology
5. Sidebar wastes space on static info (Decision States legend)
```

---

## Part 3: Proposed Architecture - Customizable Dashboard

### Philosophy: "Progressive Disclosure + Role-Based Layouts"

#### Core Principles
1. **First visit:** Guided, simplified view with clear CTAs
2. **Return visits:** Personalized dashboard based on role and preferences
3. **Power users:** Dense, information-rich layout with quick actions
4. **Mobile:** Collapsible cards, vertical pipeline, swipeable actions

### Layout System

```
Dashboard Grid Architecture
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ Header (Always Visible)                                     │
│ Waypoint OS · {Agency Name}      [Search] [Notifications] [Profile]│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ONBOARDING BANNER (Dismissible, first 3 visits)             │
│ "Welcome! Complete setup: ▓▓▓░░░░ 3/7" [Resume Setup] [×]    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CUSTOMIZABLE WIDGET GRID (User can drag/resize/show/hide)   │
│                                                             │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│ │ Priority    │  │ Pipeline    │  │ Quick Actions       │ │
│ │ Inbox       │  │ Visual      │  │                     │ │
│ │             │  │ (Vertical   │  │ [+ New Inquiry]     │ │
│ │ • Paris     │  │  or Min)   │  │ [Process Queue]     │ │
│ │ • Tokyo     │  │             │  │ [View Reports]      │ │
│ │ • Bali      │  │ ┌─────┐    │  │                     │ │
│ │             │  │ │Stage│    │  │                     │ │
│ │ [Process]   │  │ │ 2/5 │    │  │                     │ │
│ │             │  │ └─────┘    │  │                     │ │
│ └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│ ┌──────────────────────────────┐  ┌─────────────────────┐   │
│ │ Recent Activity              │  │ Team/Stats          │   │
│ │                            │  │ (Role: Manager)     │   │
│ │ [Activity Feed]            │  │                     │   │
│ │                            │  │ • Mike: 3 active    │   │
│ │                            │  │ • Sarah: 2 active   │   │
│ │                            │  │ • Bottleneck Alert  │   │
│ └──────────────────────────────┘  └─────────────────────┘   │
│                                                             │
│ [+ Add Widget]  [Customize Layout]  [Reset to Default]       │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 4: Component Specifications

### Widget 1: Pipeline Visual

**Problem Solved:** Text overlap, information overload

**Design Options (User Selectable):**

#### Option A: Vertical Stepper (Default for new users)
```
┌─────────────────┐
│ Trip Pipeline   │
├─────────────────┤
│ ✓ New Inquiry   │
│ ✓ Trip Details  │
│ → Ready to Quote│ <- Active (highlighted)
│ ○ Build Options │
│ ○ Final Review  │
├─────────────────┤
│ [Continue →]    │
└─────────────────┘
```

#### Option B: Compact Horizontal (For power users)
```
┌──────────────────────────────────┐
│ Pipeline: Inquiry → Quote → Book│
├──────────────────────────────────┤
│ ▓▓▓▓▓▓▓▓▓░░░ 7/12 trips          │
│ ████████░░░░  Stage 3 active     │
│                                  │
│ View breakdown [▼]              │
└──────────────────────────────────┘
```

#### Option C: Minimized (For dense layouts)
```
┌──────────┐
│ Pipeline │
├──────────┤
│ Stage 3/5│
│ 7 active │
│ [Expand] │
└──────────┘
```

### Widget 2: Priority Inbox

**Problem Solved:** No empty state, no prioritization

**States:**

#### Empty (First-time user)
```
┌──────────────────────────┐
│ 📥 Priority Inbox         │
├──────────────────────────┤
│                          │
│   🎯 No inquiries yet    │
│                          │
│   Connect your email to    │
│   automatically import   │
│   customer requests.       │
│                          │
│   [Connect Email]          │
│   or [Create Manual Trip] │
│                          │
└──────────────────────────┘
```

#### With Data (Active user)
```
┌──────────────────────────┐
│ 📥 Priority Inbox (4)    │
├──────────────────────────┤
│ 🔴 Overdue: Paris trip   │
│    2 days waiting         │
│    [Process Now]         │
├──────────────────────────┤
│ 🟡 Today: Tokyo inquiry  │
│    Arrived 3 hours ago    │
│    [View Details]        │
├──────────────────────────┤
│ ⏱️ Recent: Bali family   │
│    Started yesterday      │
│                          │
│ [View All →]             │
└──────────────────────────┘
```

### Widget 3: Quick Actions

**Problem Solved:** No clear CTAs for common tasks

```
┌─────────────────────────┐
│ ⚡ Quick Actions        │
├─────────────────────────┤
│                         │
│ [+ New Inquiry]        │
│ Primary, high emphasis  │
│                         │
│ ┌───────┐ ┌───────────┐│
│ │Process│ │   View    ││
│ │ Queue │ │ Analytics ││
│ └───────┘ └───────────┘│
│                         │
│ ┌───────┐ ┌───────────┐│
│ │ Team  │ │ Settings  ││
│ │ Mgmt  │ │           ││
│ └───────┘ └───────────┘│
│                         │
└─────────────────────────┘
```

---

## Part 5: Onboarding Flow Redesign

### Step-by-Step User Onboarding

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Welcome                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Welcome to Waypoint OS, Sarah!                              │
│                                                             │
│  Let's set up your agency dashboard. This takes 2 minutes. │
│                                                             │
│  [Get Started]  [Skip for now]                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Agency Setup                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Agency Name: [Wanderlust Travel Co.      ]                 │
│  Your Role:   [Owner ▼]                                     │
│  Team Size:   [1-5 ▼]                                       │
│                                                             │
│  [Continue →]  [Back]                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Connect Your Inbox (Optional)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Automatically import customer inquiries                    │
│                                                             │
│  [Connect Gmail]  [Connect Outlook]  [I'll do this later]   │
│                                                             │
│  ✓ Skip to see a sample inquiry instead                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 4: See How It Works (Interactive Demo)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "Here's how you'll process a typical inquiry"              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐│
│  │ SAMPLE: Paris Honeymoon Inquiry                        ││
│  │                                                       ││
│  │ "Hi, we're planning a 2-week honeymoon to Paris..."   ││
│  │                                                       ││
│  │ [Continue →] See how Waypoint processes this         ││
│  └───────────────────────────────────────────────────────┘│
│                                                             │
│  [Take the Tour →]  [Skip to Dashboard]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Your Dashboard is Ready!                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Dashboard customized for agency owner                    │
│  ✅ Sample data loaded (clears when you add real trips)      │
│  ⏳ Connect inbox to receive real inquiries                  │
│                                                             │
│  [Go to Dashboard]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Post-Onboarding Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ DASHBOARD: Day 1 Experience                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 🎉 Getting Started Guide (Collapsible after completion)││
│ │ ▓▓▓▓░░░░░░ 3/8 steps complete                            ││
│ │                                                           ││
│ │ ✓ Set up your agency                                     ││
│ │ ✓ See how Waypoint works                                 ││
│ │ → Connect your inbox (or create first trip manually)    ││
│ │ ○ Invite team members (optional)                         ││
│ │ [Continue Setup →] [Dismiss]                            ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌──────────────────────────────┐  ┌───────────────────────┐  │
│ │ 📥 Sample Inbox              │  │ 🎯 Pipeline Overview │  │
│ │                             │  │                       │  │
│ │ "Paris Honeymoon Inquiry"   │  │  ┌───────────────┐    │  │
│ │                             │  │  │ 1. New Inquiry│    │  │
│ │ [Review this sample trip →] │  │  │ 2. Details ✓  │    │  │
│ │                             │  │  │ 3. Quote →    │    │  │
│ │ (Real trips will appear here│  │  │ 4. Options ○  │    │  │
│ │  after you connect email)   │  │  │ 5. Review ○   │    │  │
│ │                             │  │  └───────────────┘    │  │
│ └──────────────────────────────┘  │                       │  │
│                                   │ Current: Building quote│ │
│                                   └───────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 6: Scenario Simulations

### Scenario 1: Boutique Agency - First Week

**Agency Profile:**
- Name: "Adventure Awaits Travel"
- Size: 2 agents (owner + 1 employee)
- Weekly volume: 5-10 inquiries
- Specialty: Adventure travel

**Week 1 Timeline:**

| Day | User Action | System Response |
|-----|-------------|-----------------|
| 1 | Signs up via email invite | Shows welcome + 3-step setup |
| 1 | Completes agency setup | Dashboard loads with sample data |
| 1 | Clicks "Take the Tour" | Interactive walkthrough of pipeline |
| 2 | Skips email connect | Banner: "Connect inbox to auto-import" |
| 3 | Creates first manual trip | Trip appears in pipeline, Stage 1 |
| 3 | Processes to Stage 3 | Confetti animation, "Great start!" |
| 5 | Receives 2 email inquiries | Auto-imported to inbox, notifications sent |
| 7 | Dashboard shows: 3 active, 1 overdue | "Priority" widget highlights overdue item |

**Dashboard Configuration After Week 1:**
- **Widgets Shown:** Priority Inbox (large), Pipeline (compact), Quick Actions
- **Widgets Hidden:** Team Stats (only 2 people), Analytics (not enough data)
- **Onboarding:** 6/8 steps complete, banner collapsed but accessible

### Scenario 2: Established Agency - Migration

**Agency Profile:**
- Name: "Executive Travel Solutions"
- Size: 15 agents + 3 managers
- Weekly volume: 100+ inquiries
- Existing: Spreadsheet-based workflow

**Migration Timeline:**

| Day | User Action | System Response |
|-----|-------------|-----------------|
| 1 | Bulk imports 50 past trips | Staged in "Archive" view |
| 1 | Invites 5 team members | Team roster populated |
| 2 | Assigns roles (agent/manager) | Dashboards customize per role |
| 3 | Managers see "Team Workload" widget | Shows capacity distribution |
| 5 | Customizes pipeline stages | Adds "Waiting for supplier" stage |
| 7 | Dashboard shows: Pipeline velocity, Team stats, Alerts | Dense, information-rich layout |

**Dashboard Configuration (Manager View):**
- **Widgets:** Team Workload, Pipeline Velocity, Revenue Forecast, Priority Alerts
- **Widgets Hidden:** Quick Actions (uses workbench directly), Tutorial elements
- **Layout:** 3-column grid, high information density

### Scenario 3: Solo Agent - Minimalist Preference

**Agency Profile:**
- Name: "Personal Journeys"
- Size: 1 (solo operator)
- Weekly volume: 3-5 inquiries
- Preference: Minimal UI, focus on work

**Configuration:**

**Dashboard (Minimal):**
```
┌─────────────────────────────────────────────────────────────┐
│ Waypoint OS · Personal Journeys                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [+ New Inquiry]                                         ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Active Trips: 2                                         ││
│ │                                                         ││
│ │ • Paris Honeymoon                    [Resume →]       ││
│ │   Stage 3/5 · Updated 2h ago                            ││
│ │                                                         ││
│ │ • Tokyo Business                       [Review →]       ││
│ │   Stage 2/5 · Updated 1d ago                            ││
│ │                                                         ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ [View All (2)]                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Hidden Widgets:** Pipeline visual, Team stats, Analytics, Quick Actions grid  
**Shown:** Simple list, clear CTAs, minimal chrome

---

## Part 7: Technical Implementation

### Component Visibility System

```typescript
// Dashboard configuration store
interface DashboardConfig {
  layout: 'default' | 'compact' | 'dense';
  widgets: WidgetConfig[];
  onboardingComplete: boolean;
  dismissedBanners: string[];
}

interface WidgetConfig {
  id: string;
  visible: boolean;
  position: { x: number; y: number };
  size: 'small' | 'medium' | 'large';
  collapsed?: boolean;
}

// Role-based defaults
const DEFAULT_WIDGETS: Record<UserRole, WidgetConfig[]> = {
  owner: [
    { id: 'priority-inbox', visible: true, size: 'large', position: { x: 0, y: 0 } },
    { id: 'pipeline-visual', visible: true, size: 'medium', position: { x: 1, y: 0 } },
    { id: 'team-workload', visible: true, size: 'medium', position: { x: 2, y: 0 } },
    { id: 'quick-actions', visible: true, size: 'small', position: { x: 2, y: 1 } },
    { id: 'alerts', visible: true, size: 'medium', position: { x: 0, y: 1 } },
  ],
  agent: [
    { id: 'priority-inbox', visible: true, size: 'large', position: { x: 0, y: 0 } },
    { id: 'pipeline-visual', visible: true, size: 'medium', position: { x: 1, y: 0 }, collapsed: true },
    { id: 'quick-actions', visible: true, size: 'medium', position: { x: 1, y: 1 } },
    { id: 'recent-activity', visible: true, size: 'medium', position: { x: 0, y: 1 } },
  ],
  // etc.
};
```

### Drag-and-Drop Architecture

```typescript
// Using @dnd-kit/core for drag-and-drop
import { DndContext, useDraggable, useDroppable } from '@dnd-kit/core';

function CustomizableDashboard() {
  const [widgets, setWidgets] = useState<WidgetConfig[]>([]);
  
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;
    
    // Reorder widgets based on drop position
    setWidgets(reorderWidgets(widgets, active.id, over.id));
  };
  
  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="dashboard-grid">
        {widgets.filter(w => w.visible).map(widget => (
          <DraggableWidget key={widget.id} config={widget}>
            <WidgetContent type={widget.id} />
          </DraggableWidget>
        ))}
      </div>
    </DndContext>
  );
}
```

### Responsive Breakpoints

```css
/* Pipeline widget responsive behavior */
@media (max-width: 900px) {
  .pipeline-widget {
    /* Switch to vertical stepper */
    flex-direction: column;
  }
  
  .pipeline-labels {
    /* Hide or collapse text */
    display: none;
  }
  
  .pipeline-compact {
    /* Show compact version */
    display: block;
  }
}

@media (max-width: 600px) {
  .dashboard-grid {
    /* Single column layout */
    grid-template-columns: 1fr;
  }
  
  .widget-large {
    /* Full width on mobile */
    grid-column: 1;
  }
}
```

---

## Part 8: Priority Implementation Plan

### Phase 1: Critical Fixes (Week 1)

**Goal:** Fix immediate usability issues

| Task | Effort | Impact |
|------|--------|--------|
| Fix PipelineBar text overlap | 2d | Critical - Layout broken on laptops |
| Add empty state to RecentTrips | 1d | High - New users see blank area |
| Simplify pipeline visual to 5 stages max | 1d | High - Reduce cognitive load |
| Replace technical labels with travel terms | 1d | Medium - "Stop/Proceed" → "Ready/Needs Review" |
| Add onboarding banner component | 2d | High - Guide first-time users |

### Phase 2: Onboarding Flow (Week 2-3)

**Goal:** Guide users to first value

| Task | Effort | Impact |
|------|--------|--------|
| Build 3-step setup wizard | 3d | High - Agency info, role selection |
| Create interactive demo mode | 4d | High - Sample trip walkthrough |
| Implement progress persistence | 2d | Medium - Save setup state |
| Build getting started checklist | 2d | High - Visible progress |

### Phase 3: Customization System (Week 4-6)

**Goal:** Let users customize their view

| Task | Effort | Impact |
|------|--------|--------|
| Build widget visibility toggle | 2d | Medium - Show/hide components |
| Implement drag-and-drop layout | 5d | High - Rearrange widgets |
| Create widget size variants | 3d | Medium - Compact vs expanded |
| Add role-based default layouts | 2d | Medium - Owner vs agent views |
| Build layout persistence | 2d | Medium - Save user preferences |

### Phase 4: Advanced Features (Week 7-8)

**Goal:** Power user features

| Task | Effort | Impact |
|------|--------|--------|
| Analytics dashboard | 4d | Low - Historical trends |
| Team workload visualization | 3d | Medium - Manager feature |
| Custom pipeline stages | 3d | Low - Agency-specific workflows |
| Mobile-optimized layout | 4d | Medium - Responsive improvements |

---

## Appendix: User Testing Script

### Test 1: First-Time User Onboarding

**Participants:** 5 travel agency owners who haven't used Waypoint OS

**Tasks:**
1. Sign up and complete setup wizard (measure completion rate, time)
2. Find and process the sample trip (measure time to value)
3. Return to dashboard and identify next steps

**Success Metrics:**
- 80% complete setup within 5 minutes
- 100% successfully process sample trip
- 60% can articulate what Waypoint OS does

### Test 2: Dashboard Customization

**Participants:** 10 existing users (mix of roles)

**Tasks:**
1. Hide two widgets they don't use
2. Rearrange widgets to preferred order
3. Save and confirm layout persists on refresh

**Success Metrics:**
- 90% successfully hide widgets
- 80% successfully rearrange
- 100% layout persists

### Test 3: Mobile Responsiveness

**Participants:** 5 users on mobile/tablet

**Tasks:**
1. View dashboard on mobile device
2. Navigate to workbench
3. Process a trip through 2 stages

**Success Metrics:**
- 0 critical layout breaks
- 100% can complete core tasks
- Average task completion time <2x desktop

---

## Part 9: Governance Pages Redesign

### Current State Audit

**Existing Governance Pages:**

| Page | Status | Issues |
|------|--------|--------|
| `/owner/reviews` | Placeholder only | No actual functionality, just heading |
| `/owner/insights` | Placeholder only | No actual functionality, just heading |
| `/inbox` | Implemented but basic | Missing bulk actions, no assignment, no priority scoring |

**Missing Governance Pages:**

| Page | Purpose |
|------|---------|
| `/settings/agency` | Agency configuration, branding, defaults |
| `/settings/team` | Team management, roles, permissions |
| `/settings/pipeline` | Pipeline stage customization |
| `/settings/integrations` | Email, CRM, supplier connections |
| `/admin/audit-log` | Activity tracking, compliance |
| `/admin/data-export` | GDPR compliance, backups |

### Governance User Stories

#### Owner Role
```
As an agency owner, I need to:
• See which trips need my approval (high-value, high-risk)
• Monitor team workload and spot bottlenecks
• Configure pipeline stages to match our workflow
• Set approval thresholds (e.g., trips >$10K need owner review)
• Access financial insights and conversion metrics
• Manage team members and their permissions
```

#### Manager Role
```
As a team manager, I need to:
• View team capacity and redistribute workload
• Review trips flagged by agents
• Monitor service level agreements (SLAs)
• Generate reports for owner
• Handle escalations from agents
```

### Proposed Governance Structure

```
Governance Navigation
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Settings (Gear icon in header)                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AGENCY SETTINGS                                            │
│  ├─ Profile (name, logo, timezone)                         │
│  ├─ Pipeline (stages, fields, automation)                   │
│  ├─ Notifications (email templates, alerts)                 │
│  └─ Billing (plan, usage, invoices)                         │
│                                                             │
│  TEAM MANAGEMENT                                            │
│  ├─ Members (invite, roles, deactivate)                    │
│  ├─ Workload (capacity, assignments)                        │
│  └─ Permissions (feature access by role)                    │
│                                                             │
│  INTEGRATIONS                                               │
│  ├─ Email (Gmail, Outlook connection)                       │
│  ├─ Calendar (Google, Outlook sync)                         │
│  ├─ Suppliers (API connections)                             │
│  └─ Webhooks (custom integrations)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📊 Owner Dashboard (Crown icon, owner/manager only)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  QUICK STATS                                                │
│  ├─ Active trips: 23                                       │
│  ├─ Avg response time: 4.2h                                │
│  ├─ Pipeline velocity: 2.1 days/stage                      │
│  └─ Conversion rate: 68%                                   │
│                                                             │
│  ALERTS (Requires Attention)                                │
│  ├─ 🔴 2 trips stuck >48hrs (assign to agent)              │
│  ├─ 🟡 5 trips need owner review (>$10K threshold)        │
│  ├─ 🔵 3 agents at capacity (>15 trips each)              │
│  └─ ⚪ 12 supplier quotes pending >24hrs                  │
│                                                             │
│  TEAM WORKLOAD                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Mike ████████████░░░░ 12 trips  ████ response: 3.2h      ││
│  │ Sarah ████████████████░░ 16 trips  ██████ response: 5.1h││
│  │ Alex ██████░░░░░░░░░░ 6 trips  ██ response: 2.8h        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Page Specifications

#### Page: Owner Reviews (`/owner/reviews`)

**Purpose:** Approval queue for trips requiring owner attention

**Current:** Placeholder heading only  
**Proposed:**

```
┌─────────────────────────────────────────────────────────────┐
│ Reviews Requiring Approval · 5 items                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Filters: [All ▼] [Value: >$5K ▼] [Days waiting: >2 ▼]    │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 🔴 PRIORITY · Moscow Solo Trip                           ││
│ │    TRP-2026-MSC-0422 · $12,400 · 2 days waiting          ││
│ │                                                         ││
│ │    Reason flagged: High-value + Unusual destination      ││
│ │    Agent note: "Client has visa concerns, need guidance" ││
│ │                                                         ││
│ │    [View Details] [Approve] [Request Changes] [Reassign] ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 🟡 Andaman Honeymoon · TRP-2026-AND-0420 · $8,200        ││
│ │    1 day waiting · Awaiting supplier confirmation        ││
│ │    [Quick Review] [Details]                              ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ [Load More]                                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Approval thresholds configurable ($ amount, destination risk, trip type)
- Bulk actions: Approve multiple, reassign, add notes
- Time-in-stage warnings
- Integration with agent notes

#### Page: Owner Insights (`/owner/insights`)

**Purpose:** Business intelligence and performance monitoring

**Current:** Placeholder heading only  
**Proposed:**

```
┌─────────────────────────────────────────────────────────────┐
│ Agency Performance Dashboard                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TIME RANGE: [Last 7 days ▼]  [Last 30 days] [This Month]   │
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │   23 → 18    │ │   4.2 days   │ │    $47,200   │       │
│  │   Inquiries  │ │   Avg Time   │ │   Pipeline   │       │
│  │    to Booked │ │   to Quote   │ │    Value     │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
│                                                             │
│  PIPELINE VELOCITY                                          │
│  ┌───────────────────────────────────────────────────────┐│
│  │ Stage 1 → Stage 2: 1.2 days ████████░░░░░░░░░░░░░░  ││
│  │ Stage 2 → Stage 3: 0.8 days █████░░░░░░░░░░░░░░░░░  ││
│  │ Stage 3 → Stage 4: 2.1 days █████████████░░░░░░░░░░░  ││  ← Slowest
│  │ Stage 4 → Stage 5: 1.5 days ██████████░░░░░░░░░░░░░░  ││
│  │ Stage 5 → Booked: 0.5 days ███░░░░░░░░░░░░░░░░░░░░░  ││
│  └───────────────────────────────────────────────────────┘│
│                                                             │
│  BOTTLENECK ANALYSIS                                        │
│  • Stage 3 ("Ready to Quote") taking 2.1 days avg         │
│    Primary causes:                                         │
│    - Supplier response delays (60% of cases)               │
│    - Incomplete trip details (25% of cases)                │
│    - [View breakdown →]                                    │
│                                                             │
│  TEAM PERFORMANCE                                           │
│  ┌───────────────────────────────────────────────────────┐│
│  │ Agent   │ Conversions │ Avg Response │ CSAT │ Status  ││
│  ├───────────────────────────────────────────────────────┤│
│  │ Mike    │    14/18    │    3.2h      │ 4.8  │ ✅     ││
│  │ Sarah   │    12/20    │    5.1h      │ 4.5  │ ⚠️     ││
│  │ Alex    │     8/9     │    2.8h      │ 4.9  │ ✅     ││
│  └───────────────────────────────────────────────────────┘│
│                                                             │
│  ESCALATION HEATMAP                                        │
│  [Visual: Calendar with days colored by escalation count]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Configurable date ranges
- Pipeline velocity by stage
- Bottleneck identification with root cause analysis
- Team performance comparison
- Export to CSV/PDF

#### Page: Inbox Enhanced (`/inbox`)

**Purpose:** Central triage and assignment hub

**Current:** Basic card grid, filters  
**Proposed:**

```
┌─────────────────────────────────────────────────────────────┐
│ 📥 Trip Inbox · 23 items · Auto-refresh: 5m               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Select All]  [Assign ▼]  [Bulk Actions ▼]  [Refresh]      │
│                                                             │
│  Filters: [All Types ▼] [All Agents ▼] [Priority: Any ▼]  │
│  Sort: [Urgency ▼]                                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ☐  🔴 Moscow Solo    │ Assigned: -       │ Age: 2d    ││
│  │      $12,400 · Jun 10-20 │ Priority: High    │ Stage: 1  ││
│  │      [Assign] [View] [Snooze] [Escalate]              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ☐  🟡 Paris Honeymoon │ Assigned: Mike    │ Age: 1d    ││
│  │      $8,500 · May 15-22 │ Priority: Medium  │ Stage: 2  ││
│  │      [Reassign] [View] [Snooze]                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ☐  🟢 Bali Family    │ Assigned: Sarah   │ Age: 2h    ││
│  │      $6,200 · Aug 1-10 │ Priority: Low     │ Stage: 4  ││
│  │      [View]                                             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  [Load More]                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Bulk selection and actions
- Priority auto-scoring (based on value, deadline, client history)
- Assignment suggestions (load balancing)
- Snooze (remind me in X hours)
- Quick view modal (don't leave page)
- SLA indicators (green/yellow/red based on time in stage)

#### Page: Settings - Pipeline (`/settings/pipeline`)

**Purpose:** Customize pipeline stages to match agency workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Pipeline Configuration                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DEFAULT PIPELINE (5 stages)                                 │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ☰  1. New Inquiry                                     │  │
│  │     Capture initial customer request                  │  │
│  │     Fields: Email, Destination, Dates, Party size     │  │
│  │     [Edit] [Remove]                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ☰  2. Trip Details                                    │  │
│  │     Extract and verify trip information               │  │
│  │     [Edit] [Remove]                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  │ ... (stages 3-5)                                      │  │
│                                                             │
│  [+ Add Stage]                                              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ⚙️ Automation Rules                                    │  │
│  │                                                        │  │
│  │  • Move to "Ready to Quote" when: All required        │  │
│  │    fields complete AND Supplier response received       │  │
│  │                                                        │  │
│  │  • Alert owner when: Trip value > $10,000             │  │
│  │                                                        │  │
│  │  [+ Add Rule]                                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  [Save Changes]  [Reset to Default]  [Preview Pipeline]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Governance Permissions Matrix

| Feature | Owner | Manager | Agent | View-Only |
|---------|-------|---------|-------|-----------|
| Owner Reviews | ✅ Approve | ✅ View only | ❌ | ❌ |
| Insights Dashboard | ✅ Full | ✅ Full | ✅ Own stats | ❌ |
| Team Management | ✅ Full | ✅ View only | ❌ | ❌ |
| Pipeline Config | ✅ Full | ❌ | ❌ | ❌ |
| Agency Settings | ✅ Full | ❌ | ❌ | ❌ |
| Inbox Bulk Actions | ✅ Full | ✅ Full | ✅ Own only | ❌ |
| Trip Reassignment | ✅ Full | ✅ Full | ❌ | ❌ |
| Audit Log | ✅ Full | ✅ View | ❌ | ❌ |

### Implementation Priority

**Phase 1: Core Governance (Week 1-2)**
1. Owner Reviews page (actual functionality)
2. Enhanced Inbox with assignment
3. Basic team workload view

**Phase 2: Insights (Week 3-4)**
1. Owner Insights dashboard
2. Pipeline velocity metrics
3. Team performance comparison

**Phase 3: Configuration (Week 5-6)**
1. Settings pages (agency, team, pipeline)
2. Permission system
3. Custom pipeline stages

**Phase 4: Advanced (Week 7-8)**
1. Automation rules engine
2. Audit logging
3. Advanced reporting (exports)

---

## Document History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-04-16 | 1.0 | Initial comprehensive UX redesign plan | AI Assistant |
| 2026-04-16 | 1.1 | Added Governance section with owner pages, insights, settings | AI Assistant |

---

## Next Steps

1. **Review** this document with stakeholders
2. **Prioritize** Phase 1 critical fixes for immediate implementation
3. **Design** widget components and drag-and-drop interactions
4. **Schedule** user testing sessions
5. **Implement** onboarding flow first (highest impact)
6. **Build** Owner Reviews page (currently just placeholder)
