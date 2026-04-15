# In-App Messaging System Design

**Context**: Travel Agency Agent (TAA) - Operational tool for travel agents
**Goal**: Onboard new operators and deliver operational updates without disrupting workflow

---

## Architecture

### Message Types

| Type | Purpose | Placement | Dismissal |
|------|---------|-----------|-----------|
| **Announcement Banner** | Critical updates, system status | Top of page (under header) | Dismissible per-session |
| **Tooltip/Tour** | Feature onboarding | Inline, attached to UI | Dismiss once, don't show again |
| **Side Panel** | Extended help, process guides | Right side, collapsible | Toggle open/close |
| **Inline Callout** | Contextual tips | Within content flow | Auto-dismiss after action |
| **Modal** | Critical alerts, breaking changes | Centered overlay (rare) | Requires acknowledgment |

---

## Component Structure

```
src/components/
├── messaging/
│   ├── AnnouncementBanner.tsx    # Top banner for updates
│   ├── FeatureTour.tsx            # Step-by-step tour for new users
│   ├── Tooltip.tsx                # Inline tooltips (what is this?)
│   ├── HelpPanel.tsx              # Collapsible side panel
│   ├── InlineCallout.tsx          # Tips within workflow
│   └── useAnnouncements.ts        # Hook for fetching announcements
```

---

## Implementation Plan

### 1. Announcement Banner System

**Use cases**: "Spine API is experiencing delays", "New safety protocol deployed", "System maintenance in 30min"

```tsx
// src/components/messaging/AnnouncementBanner.tsx
interface Announcement {
  id: string;
  type: "info" | "warning" | "success" | "critical";
  title: string;
  message: string;
  action?: { label: string; href: string };
  dismissible: boolean;
  startsAt: string;
  expiresAt?: string;
  targetRole?: "all" | "operators" | "owners";
}
```

**Behavior**:
- Poll API for active announcements
- Show banner under command bar (not overlay)
- Remember dismissed via localStorage
- Auto-hide when expired
- Critical messages require acknowledgment

---

### 2. Feature Tour / Onboarding

**Use cases**: First-time user sees "Let me show you around", returning users see "New feature: X"

```tsx
// src/components/messaging/FeatureTour.tsx
interface TourStep {
  id: string;
  target: string;              // CSS selector for element to highlight
  title: string;
  content: string;
  position: "top" | "right" | "bottom" | "left";
  action?: { label: string; callback: () => void };
}

// Example tours
const NEW_USER_TOUR: TourStep[] = [
  {
    id: "welcome",
    target: "",
    title: "Welcome to TAA",
    content: "Let's walk through how to process a trip request.",
    position: "center"
  },
  {
    id: "inbox-intro",
    target: "[href='/inbox']",
    title: "Your Inbox",
    content: "Trip requests arrive here. Prioritize by urgency and completeness.",
    position: "right"
  },
  {
    id: "workbench-intro",
    target: "[href='/workbench']",
    title: "The Workbench",
    content: "Process trips through Intake → Packet → Decision → Strategy → Safety.",
    position: "left"
  }
];
```

**Behavior**:
- Check localStorage for `seen_tours` array
- Show tour if user hasn't seen it AND is on relevant page
- Can be re-triggered via "Help → Show me around"
- Progress indicator (Step 1 of 5)
- Skip anytime, don't show again

---

### 3. Contextual Tooltips

**Use cases**: Hover over "Safety" tab shows "This checks for data leaks", hover over confidence score shows explanation

```tsx
// src/components/messaging/Tooltip.tsx
interface TooltipProps {
  children: React.ReactNode;
  content: string | React.ReactNode;
  position?: "top" | "right" | "bottom" | "left";
  delay?: number;              // Hover delay before showing
  persistent?: boolean;        // Don't auto-hide
}
```

**Behavior**:
- Hover or focus triggers
- Keyboard accessible (Tab to focus, Enter to dismiss)
- Escape key closes all
- Z-index management (above everything)

---

### 4. Help Panel (Collapsible)

**Use cases**: "Process guide for visa requirements", "How to handle incomplete data", expandable reference

```tsx
// src/components/messaging/HelpPanel.tsx
interface HelpSection {
  id: string;
  title: string;
  content: string | React.ReactNode;
  relevantPages?: string[];    // Only show on these routes
}
```

**Behavior**:
- Collapsible from right side
- Context-aware (shows relevant help for current page)
- Searchable help content
- "Was this helpful?" feedback
- Persist open/closed state

---

### 5. Inline Callouts

**Use cases**: "Tip: You can drag to reorder these", "Shortcut: Press Cmd+K to search"

```tsx
// src/components/messaging/InlineCallout.tsx
interface InlineCalloutProps {
  type: "tip" | "warning" | "info";
  title: string;
  content: string;
  dismissible: boolean;
  onDismiss?: () => void;
}
```

**Behavior**:
- Appears within content flow
- Subtle, doesn't break reading
- Can be actioned (e.g., "Got it" marks complete)
- Don't show again after action

---

## State Management

```tsx
// src/stores/messaging.ts
interface MessagingStore {
  // Dismissed announcements (ids)
  dismissedAnnouncements: string[];
  dismissAnnouncement: (id: string) => void;

  // Completed tours
  completedTours: string[];
  completeTour: (id: string) => void;

  // Help panel state
  helpPanelOpen: boolean;
  toggleHelpPanel: () => void;

  // Inline callouts dismissed
  dismissedCallouts: string[];
  dismissCallout: (id: string) => void;
}
```

---

## API Endpoints

```typescript
// GET /api/announcements - Active announcements for current user
// POST /api/announcements/{id}/dismiss - Mark as dismissed
// GET /api/help - Help content for current page
// POST /api/tours/{id}/complete - Mark tour as completed
```

---

## Priority Rules

1. **Critical announcements** > Tours > Tooltips > Help panel
2. **Only one active tour at a time**
3. **Don't interrupt during active operations** (spine running, form in progress)
4. **Respect user preferences** (if they dismissed, don't show again)

---

## Example User Flow

### New Operator Day 1
1. Landing page → Full-page welcome (can skip)
2. Enter workbench → Feature tour starts (auto-highlight inbox, workbench)
3. After tour complete → Help panel opens with "Getting Started" guide
4. Throughout day → Contextual tooltips on hover
5. If idle → "Need help?" callout appears

### Returning Operator
1. No tour (already seen)
2. Announcement banner if new updates
3. "New feature" badge on relevant elements
4. Help panel available but closed by default

### During Operational Issue
1. Critical announcement appears at top (red, can't dismiss)
2. Expands to show details on click
3. Links to relevant documentation
4. Disappears when resolved

---

## Design System Integration

**Colors** (from existing tokens):
```tsx
const MESSAGE_COLORS = {
  info: COLORS.accentBlue,
  warning: COLORS.accentAmber,
  success: COLORS.accentGreen,
  critical: COLORS.accentRed,
}
```

**Components reuse**:
- Card component for message containers
- Button component for actions
- Badge component for "New" indicators
- Icon component for icons

---

## Accessibility

- All messages keyboard navigable
- Focus trap for tours
- Screen reader announcements
- High contrast mode support
- Reduced motion respects prefers-reduced-motion

---

## Measurement

Track:
- Tour completion rate
- Announcement click-through
- Help panel usage
- Tooltip engagement
- Time to first successful action (for new users)

---

## Next Steps

1. Create `src/components/messaging/` directory
2. Build AnnouncementBanner component (highest priority)
3. Add announcement API endpoints
4. Build FeatureTour with driver.js or similar
5. Add contextual tooltips to key UI elements
6. Build HelpPanel with search
7. Add to workbench page
