# Workspace Routing Feature — Requirements

**Feature Name:** workspace-routing  
**Version:** 1.0.0  
**Date:** 2026-04-16  
**Status:** Requirements Phase

---

## 1. Problem Statement

### Current State
- Inbox (`/inbox`) displays trip cards with triage UX
- Clicking a trip card routes to `/workbench` (generic workbench)
- `/workspace/[tripId]/*` routes exist but are placeholders only
- No trip-scoped operator workflow is operational

### Target State
- Inbox cards route to trip-scoped workspaces at `/workspace/[tripId]/*`
- Operators can work on individual trips with full pipeline visibility
- Workspace provides context-aware navigation and state management

### Impact
- **Blocking:** Operators cannot properly manage individual trips
- **User Experience:** Current flow forces generic workbench instead of trip-specific context
- **Product Risk:** Incomplete operator workflow prevents real-world usage

---

## 2. User Stories

### Primary Personas
- **Agency Owner:** Needs to review and manage multiple trips
- **Senior Agent:** Needs to process trips through full pipeline
- **Junior Agent:** Needs guided workflow for trip processing

### User Stories

#### As an Agency Owner
- **US-1.1:** I want to click on a trip in the inbox and see all relevant information for that specific trip
- **US-1.2:** I want to navigate between intake, packet, decision, and strategy views for a single trip
- **US-1.3:** I want to see all trips in my agency with clear status indicators

#### As a Senior Agent
- **US-2.1:** I want to work on one trip at a time with full context
- **US-2.2:** I want to see validation results, decision state, and strategy suggestions for the current trip
- **US-2.3:** I want to mark trips as complete and move to the next one

#### As a Junior Agent
- **US-3.1:** I want clear guidance on what information is missing for each trip
- **US-3.2:** I want to see blockers and follow-up questions specific to the current trip
- **US-3.3:** I want to easily escalate trips that need review

---

## 3. Functional Requirements

### FR-1: Trip-Scoped Workspace Shell
- **FR-1.1:** The app must provide a `/workspace/[tripId]` route that serves as the workspace shell
- **FR-1.2:** The workspace shell must display trip metadata (ID, stage, operating mode)
- **FR-1.3:** The workspace shell must provide navigation to sub-routes (intake, packet, decision, strategy, safety, output)

### FR-2: Navigation System
- **FR-2.1:** Clicking a trip card in `/inbox` must route to `/workspace/[tripId]/intake`
- **FR-2.2:** Workspace sub-routes must be accessible via tab navigation
- **FR-2.3:** Navigation must preserve trip context across route changes
- **FR-2.4:** Navigation must support browser back/forward history

### FR-3: Trip Context Management
- **FR-3.1:** The workspace must load trip data from the spine when the route is accessed
- **FR-3.2:** Trip data must be cached in session state to avoid redundant spine calls
- **FR-3.3:** Trip context must persist when navigating between workspace sub-routes
- **FR-3.4:** Trip context must be cleared when leaving the workspace

#### FR-3.5: Session Persistence
- **FR-3.5.1:** Storage mechanism: `sessionStorage` (persists across tab refreshes, clears on tab close)
- **FR-3.5.2:** Data persisted: `spineResults` (full `SpineResult` objects)
- **FR-3.5.3:** Cache key format: `workspace:spine:${tripId}`
- **FR-3.5.4:** TTL: Session-based (no explicit TTL, clears on tab close)
- **FR-3.5.5:** Session timeout: 30 minutes of inactivity triggers cache clear
- **FR-3.5.6:** Explicit clear triggers: "Run Spine" button click, explicit "Clear Cache" button, tab close

### FR-4: Tab Content
Each workspace sub-route must display relevant information:

#### FR-4.1: `/workspace/[tripId]/intake`
- Display raw input from agency notes
- Show extracted facts with confidence scores
- Display validation report (errors/warnings)
- Show ambiguities and contradictions

#### FR-4.2: `/workspace/[tripId]/packet`
- Display canonical packet in JSON format
- Toggle between structured view and raw JSON
- Show derived signals and hypotheses
- Display evidence references for each field

#### FR-4.3: `/workspace/[tripId]/decision`
- Show decision state with color-coded badge
- Display confidence score
- List hard blockers, soft blockers, and risk flags
- Show follow-up questions with priority
- Display rationale and branch options

#### FR-4.4: `/workspace/[tripId]/strategy`
- Show session strategy (goal, priority sequence, tone)
- Display suggested opening and exit criteria
- Show internal bundle (agent-only)
- Show traveler-safe bundle

#### FR-4.5: `/workspace/[tripId]/safety`
- Display three-panel view: raw packet → sanitized view → traveler bundle
- Show leakage detection results
- Indicate strict mode status

#### FR-4.6: `/workspace/[tripId]/output`
- Display final traveler-safe output
- Show follow-up sequence
- Display branch prompts (if applicable)

### FR-5: State Management
- **FR-5.1:** Use Zustand for workspace state management
- **FR-5.2:** Store current trip ID in URL parameters
- **FR-5.3:** Store last successful spine result in session state
- **FR-5.4:** Support "Run Spine" button to refresh trip data

---

## 4. Non-Functional Requirements

### NFR-1: Performance
- **NFR-1.1:** Workspace load time must be under 500ms for cached data
- **NFR-1.2:** Spine execution must complete in under 2 seconds
- **NFR-1.3:** Navigation between tabs must be instant (<100ms)

### NFR-2: Reliability
- **NFR-2.1:** Workspace must handle spine failures gracefully
- **NFR-2.2:** Cached data must persist across page refreshes
- **NFR-2.3:** Navigation must work even if spine is unavailable

### NFR-3: Usability
- **NFR-3.1:** Operators must be able to complete a trip workflow in under 5 minutes
- **NFR-3.2:** Navigation must be intuitive with clear visual indicators
- **NFR-3.3:** Error messages must be actionable and specific

### NFR-4: Maintainability
- **NFR-4.1:** Workspace components must be reusable across trip contexts
- **NFR-4.2:** State management must be centralized and testable
- **NFR-4.3:** Code must follow existing project conventions

---

## 5. Acceptance Criteria

### AC-1: Navigation
- [ ] Clicking a trip card in `/inbox` routes to `/workspace/[tripId]/intake`
- [ ] Tab navigation works correctly between workspace sub-routes
- [ ] Browser back/forward history works as expected
- [ ] URL updates correctly with route changes

### AC-2: Data Display
- [ ] All workspace tabs display relevant trip data
- [ ] Data is consistent across tabs (same trip context)
- [ ] Validation errors and warnings are clearly shown
- [ ] Decision state and confidence are visible

### AC-3: State Management
- [ ] Trip data is cached in session state
- [ ] Data persists when navigating between tabs
- [ ] Data is cleared when leaving workspace
- [ ] "Run Spine" button refreshes data correctly

### AC-4: Error Handling
- [ ] Graceful handling of spine failures
- [ ] Clear error messages for missing trip data
- [ ] Fallback behavior when data is unavailable

### AC-5: Code Quality
- [ ] All components follow existing project conventions
- [ ] State management is centralized and testable
- [ ] Code is properly typed with TypeScript
- [ ] Tests cover critical workflows

---

## 6. Out of Scope

### OOS-1: Future Enhancements
- Bulk trip operations (select multiple trips)
- Advanced filtering/sorting in inbox
- Trip comparison view
- Export functionality

### OOS-2: External Integrations
- Real-time updates via WebSocket
- Email notifications for trip status changes
- Integration with external CRM systems

### OOS-3: Advanced Features
- AI-assisted trip processing
- Automated triage rules
- Predictive analytics for trip outcomes

---

## 7. Dependencies

### Dep-1: Backend
- Spine API must be available at `/api/spine/run`
- Trip data must be accessible via existing API routes

### Dep-2: Frontend
- Next.js App Router must be properly configured
- Zustand must be available for state management
- Existing workbench components must be reusable

### Dep-3: Design
- Design system must provide necessary components (tabs, cards, badges)
- Color coding for decision states must be available

---

## 8. Risks and Assumptions

### Risks
- **R-1:** Workspace tab components may be too complex to implement quickly
- **R-2:** State management complexity may increase maintenance burden
- **R-3:** Navigation history may not work as expected with client-side routing
- **R-4:** Session storage may not persist across all browser scenarios

### Assumptions
- **A-1:** Workspace tab components will be created as NEW components (not reused from workbench)
- **A-2:** Zustand is the appropriate state management solution
- **A-3:** Next.js App Router handles client-side navigation correctly
- **A-4:** sessionStorage provides adequate persistence for workspace sessions

---

## 9. Success Metrics

### SM-1: User Efficiency
- Time to complete a trip workflow: <5 minutes
- Number of clicks to process a trip: <10

### SM-2: User Satisfaction
- Operator feedback score: >4/5
- Error rate: <5% of trips

### SM-3: System Health
- Workspace load time: <500ms
- Spine execution time: <2 seconds
- Navigation latency: <100ms

---

## 10. Future Considerations

### FC-1: Scalability
- Support for 100+ concurrent trip workspaces
- Efficient memory usage for large trip data

### FC-2: Extensibility
- Easy to add new workspace tabs
- Plugin architecture for custom trip types

### FC-3: Analytics
- Track user behavior in workspace
- Identify common workflow patterns
- Measure feature adoption

---

## Appendix

### A. References
- `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md` — Full frontend product spec
- `Docs/FRONTEND_WORKFLOW_COVERAGE_2026-04-16.md` — Current workflow coverage
- `frontend/src/app/workbench/` — Existing workbench implementation (INPUT components)
- `frontend/src/app/workspace/` — New workspace components (DISPLAY components)

### B. Glossary
- **Trip:** A travel planning request from an agency
- **Spine:** Core processing pipeline (NB01 → NB02 → NB03)
- **Workspace:** Trip-scoped interface for operator workflow
- **Tab:** Sub-view within a workspace (intake, packet, decision, etc.)
