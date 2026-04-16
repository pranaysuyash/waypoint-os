# Waypoint OS UX Redesign - Implementation Checklist

**Created:** 2026-04-16  
**Status:** Tracking document for UX overhaul

---

## Phase 1: Critical Fixes (Immediate)

### Dashboard Layout Issues
- [ ] Fix PipelineBar text overlap (7 stages crammed horizontally)
  - Priority: Critical
  - Solution: Implement vertical stepper or collapsible view
  - Files: `frontend/src/app/page.tsx`

- [ ] Add empty state to RecentTrips component
  - Priority: High
  - Current: Shows blank area for new users
  - Expected: "No trips yet" with CTA to create first trip

- [ ] Fix flickering loading states
  - Priority: High
  - Current: Skeleton loaders with animate-pulse causing visual flicker
  - Solution: Delayed loading pattern (300ms threshold)
  - Files: `frontend/src/hooks/useTrips.ts`, `frontend/src/app/page.tsx`

- [ ] Simplify pipeline visual to max 5 stages
  - Priority: Medium
  - Current: "Lead/Qualified/Planning/Quoted/Booked/Traveling/Complete"
  - Expected: Align with workbench stages (New Inquiry → Final Review)

### Technical Decision States
- [ ] Replace technical labels with travel industry terms
  - Priority: Medium
  - Current: "PROCEED_SAFE", "STOP_REVIEW", "BRANCH / DRAFT"
  - Expected: "Ready to Book", "Needs Review", "Draft Options"

---

## Phase 2: Governance Pages (Placeholders → Functional)

### Owner Reviews Page (`/owner/reviews`)
- [ ] Create approval queue interface
  - Status: Currently placeholder (8 lines)
  - Features needed:
    - Trip cards requiring approval
    - Approval thresholds ($ amount, risk flags)
    - Approve/Request Changes/Reassign actions
    - Bulk actions support
  - Mock data: 5 trips needing review

### Owner Insights Page (`/owner/insights`)
- [ ] Build analytics dashboard
  - Status: Currently placeholder (8 lines)
  - Features needed:
    - Pipeline velocity by stage
    - Team performance metrics
    - Bottleneck identification
    - Conversion rates
    - Revenue pipeline
    - Export to CSV/PDF
  - Time ranges: 7 days, 30 days, custom

### Enhanced Inbox (`/inbox`)
- [ ] Add assignment functionality
  - Priority: High
  - Features:
    - Assign trip to agent
    - Reassignment with history
    - Bulk assignment
    - Auto-assignment rules

- [ ] Add priority scoring
  - Auto-calculate based on:
    - Trip value
    - Days in current stage
    - Client history
    - Deadline proximity

- [ ] Add bulk actions
  - Select multiple trips
  - Bulk assign, snooze, export

- [ ] Add quick view modal
  - Don't navigate away from inbox
  - Approve/reject inline

---

## Phase 3: Onboarding Flow

### Setup Wizard
- [ ] Step 1: Welcome screen
  - Value proposition
  - Time estimate (2 minutes)
  - Get Started / Skip options

- [ ] Step 2: Agency setup
  - Agency name
  - Role selection (Owner/Manager/Agent)
  - Team size
  - Timezone

- [ ] Step 3: Connect inbox (optional)
  - Gmail/Outlook integration
  - Skip option
  - Sample data alternative

- [ ] Step 4: Interactive demo
  - Sample trip walkthrough
  - Each pipeline stage explained
  - Hands-on interaction

### First-Time Dashboard
- [ ] Onboarding banner
  - Collapsible after completion
  - Progress indicator (3/8 steps)
  - Quick actions to complete setup

- [ ] Getting started checklist
  - Setup agency ✓
  - See how Waypoint works ✓
  - Connect inbox →
  - Invite team (optional)
  - Process first trip
  - etc.

- [ ] Sample data
  - Pre-loaded sample inquiry
  - "Review this sample" CTA
  - Clears when first real trip added

---

## Phase 4: Dashboard Customization

### Widget System
- [ ] Define widget components
  - Priority Inbox (large/medium/small)
  - Pipeline Visual (vertical/horizontal/minimal)
  - Quick Actions (grid/list)
  - Team Workload (manager only)
  - Recent Activity
  - Alerts/Notifications

- [ ] Implement visibility toggle
  - Show/hide widgets
  - Persist preferences

- [ ] Implement drag-and-drop layout
  - Reorder widgets
  - Resize widgets
  - Persist layout

- [ ] Role-based defaults
  - Owner: Full suite
  - Manager: Team focus
  - Agent: Task focus
  - Customizable per user

---

## Phase 5: Settings & Configuration

### Agency Settings
- [ ] Profile (name, logo, timezone)
- [ ] Pipeline configuration
  - Edit stage names
  - Add/remove stages
  - Set required fields per stage
  - Automation rules
- [ ] Notification templates
- [ ] Billing/plan management

### Team Management
- [ ] Member invitation
- [ ] Role assignment
- [ ] Workload capacity settings
- [ ] Permission matrix
- [ ] Deactivation

### Integrations
- [ ] Email (Gmail/Outlook)
- [ ] Calendar sync
- [ ] Supplier APIs
- [ ] Webhooks

---

## Phase 6: Workbench Improvements

### PipelineFlow Component
- [ ] Remove redundant visualization
  - Current: PipelineFlow + Tabs show same info
  - Solution: Collapsible PipelineFlow or integrate into tab headers

### Tab Content
- [ ] IntakeTab: Customer message parsing
- [ ] PacketTab: Trip details form
- [ ] DecisionTab: Go/No-go checklist
- [ ] StrategyTab: Build options
- [ ] SafetyTab: Final review checklist

### Process Trip Button
- [ ] Actual functionality (currently just loading state)
- [ ] Integration with backend
- [ ] Progress feedback

---

## Files to Modify

### High Priority
```
frontend/src/app/page.tsx                    # Dashboard layout
frontend/src/hooks/useTrips.ts               # Loading states
frontend/src/app/owner/reviews/page.tsx      # Placeholder → functional
frontend/src/app/owner/insights/page.tsx     # Placeholder → functional
frontend/src/app/inbox/page.tsx             # Add assignment, bulk actions
frontend/src/app/workbench/PipelineFlow.tsx  # Remove redundancy
```

### Medium Priority
```
frontend/src/app/workbench/page.tsx          # Workbench layout
frontend/src/components/layouts/Shell.tsx     # Navigation updates
frontend/src/lib/design-system.ts           # Update terminology
```

### New Files Needed
```
frontend/src/app/settings/agency/page.tsx
frontend/src/app/settings/team/page.tsx
frontend/src/app/settings/pipeline/page.tsx
frontend/src/app/settings/integrations/page.tsx
frontend/src/components/onboarding/
  - WelcomeStep.tsx
  - AgencySetupStep.tsx
  - ConnectInboxStep.tsx
  - DemoStep.tsx
frontend/src/components/widgets/
  - PriorityInbox.tsx
  - PipelineVisual.tsx
  - QuickActions.tsx
  - TeamWorkload.tsx
  - RecentActivity.tsx
```

---

## Dependencies

### Phase 1 Blockers
- None - can start immediately

### Phase 2 Blockers
- API endpoints for:
  - `/api/reviews` (trips needing approval)
  - `/api/insights` (metrics, analytics)
  - `/api/inbox/assign` (assignment functionality)

### Phase 3 Blockers
- User onboarding state persistence
- Sample data generation

### Phase 4 Blockers
- @dnd-kit/core for drag-and-drop
- User preferences storage

---

## Success Metrics

### Phase 1
- PipelineBar readable at 1000px viewport
- Zero flickering on dashboard load
- New users see empty state guidance

### Phase 2
- Owner Reviews page functional (not placeholder)
- Owner Insights page shows real metrics
- Inbox supports assignment

### Phase 3
- 80% complete setup within 5 minutes
- 100% can process sample trip
- 60% can articulate Waypoint OS value

### Phase 4
- 90% successfully customize widgets
- 80% can rearrange layout
- 100% preferences persist

---

## Notes

- **Animations:** Deferred to later phase (Phase 5+)
- **Mobile:** All changes must be responsive
- **Accessibility:** Maintain ARIA labels, keyboard navigation
- **Performance:** Dashboard load <2s, workbench <1s

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2026-04-16 | 1.0 | Initial checklist |
