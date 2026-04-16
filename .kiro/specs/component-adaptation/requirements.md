# Component Adaptation Spec — Requirements

**Feature Name:** component-adaptation  
**Version:** 1.0.0  
**Date:** 2026-04-16  
**Status:** Requirements Phase

---

## 1. Problem Statement

### Current State
- **Workbench IntakeTab.tsx** is an INPUT interface:
  - Contains trip selector dropdown
  - Contains customer message textarea
  - Contains agent notes textarea
  - Contains stage/mode dropdowns
  - Contains "Run Spine" button
  - Purpose: Collect input and trigger spine execution

- **Workspace spec** expects DISPLAY interface:
  - Should display cached spine results
  - Should NOT have input forms
  - Should NOT have "Run Spine" button
  - Purpose: Display processed trip data

### The Gap
The workspace design assumes it can reuse workbench components like `IntakeTab.tsx`, but:
- Workbench: INPUT → Process → Display
- Workspace: Display ONLY (cached data)

These are fundamentally different interfaces that cannot be reused without significant modification.

### Impact
- **Blocking:** Cannot implement workspace routing without resolving this gap
- **Code Quality:** Reusing INPUT components as DISPLAY creates confusion
- **Maintenance:** Mixed concerns make future changes harder

---

## 2. User Stories

### Primary Personas
- **Agency Owner:** Needs to view trip data without accidentally modifying it
- **Senior Agent:** Needs to review processed trip data with full context
- **Junior Agent:** Needs clear, focused display of trip information

### User Stories

#### As an Agency Owner
- **US-1.1:** I want to view trip data in a read-only format
- **US-1.2:** I want to see all processed information (facts, decisions, strategy) in one place
- **US-1.3:** I want clear visual separation between input and output views

#### As a Senior Agent
- **US-2.1:** I want to see the final processed output without input forms
- **US-2.2:** I want to see confidence scores and decision rationale clearly
- **US-2.3:** I want to easily identify what information is missing

#### As a Junior Agent
- **US-3.1:** I want clear, focused display of trip information
- **US-3.2:** I want to see blockers and follow-up questions prominently
- **US-3.3:** I want to understand the decision process

---

## 3. Functional Requirements

### FR-1: Component Classification
- **FR-1.1:** Identify all workbench components that need adaptation
- **FR-1.2:** Classify each component as INPUT, DISPLAY, or BOTH
- **FR-1.3:** Document which components can be reused as-is
- **FR-1.4:** Document which components need new DISPLAY-only versions

### FR-2: Component Reuse Strategy
- **FR-2.1:** Define criteria for when to reuse vs rebuild
- **FR-2.2:** Create new DISPLAY-only components where needed
- **FR-2.3:** Add `displayMode` prop to components that can serve both purposes

### FR-3: Component Mapping
| Workbench Component | Workspace Counterpart | Strategy |
|---------------------|----------------------|----------|
| IntakeTab | DisplayIntakeTab | Rebuild (INPUT → DISPLAY) |
| PacketTab | DisplayPacketTab | Rebuild (INPUT → DISPLAY) |
| DecisionTab | DisplayDecisionTab | Rebuild (INPUT → DISPLAY) |
| StrategyTab | DisplayStrategyTab | Rebuild (INPUT → DISPLAY) |
| SafetyTab | DisplaySafetyTab | Rebuild (INPUT → DISPLAY) |
| OutputTab | DisplayOutputTab | Rebuild (INPUT → DISPLAY) |

### FR-4: Display-Only Interface
Each workspace tab must:
- **FR-4.1:** Accept `spineResult` as prop (not session state)
- **FR-4.2:** Display data without input forms
- **FR-4.3:** Show confidence scores and decision rationale
- **FR-4.4:** Highlight missing information clearly
- **FR-4.5:** Support "Run Spine" button ONLY in workspace shell, not tabs

---

## 4. Non-Functional Requirements

### NFR-1: Code Quality
- **NFR-1.1:** Components must follow existing project conventions
- **NFR-1.2:** Display components must be pure (no side effects)
- **NFR-1.3:** Input components must be separate from display components

### NFR-2: Performance
- **NFR-2.1:** Display components must render in <100ms
- **NFR-2.2:** No redundant spine calls from display components

### NFR-3: Maintainability
- **NFR-3.1:** Clear separation between INPUT and DISPLAY components
- **NFR-3.2:** Component names clearly indicate purpose
- **NFR-3.3:** Documentation explains when to use each variant

---

## 5. Acceptance Criteria

### AC-1: Component Inventory
- [ ] All workbench components identified
- [ ] Each component classified as INPUT/DISPLAY/BOTH
- [ ] Component reuse strategy documented

### AC-2: Component Implementation
- [ ] New DISPLAY-only components created
- [ ] Existing INPUT components unchanged
- [ ] No cross-contamination between INPUT and DISPLAY

### AC-3: Workspace Integration
- [ ] Workspace tabs display data correctly
- [ ] No input forms in workspace tabs
- [ ] "Run Spine" button only in workspace shell

### AC-4: Code Quality
- [ ] All components properly typed
- [ ] Tests cover both INPUT and DISPLAY variants
- [ ] Documentation updated

---

## 6. Out of Scope

### OOS-1: Future Enhancements
- Dynamic component loading
- Component theming
- Component composition

### OOS-2: External Changes
- Modifying workbench functionality
- Changing spine API
- Altering data models

---

## 7. Dependencies

### Dep-1: Existing Code
- Workbench components must exist for analysis
- Component structure must be understood

### Dep-2: Design
- Component reuse strategy must be defined
- Component mapping must be documented

---

## 8. Risks and Assumptions

### Risks
- **R-1:** Some components may be too tightly coupled to reuse
- **R-2:** Creating duplicate components increases maintenance burden
- **R-3:** Component naming may cause confusion

### Assumptions
- **A-1:** Workbench components can be analyzed and classified
- **A-2:** DISPLAY-only variants can be created without major refactoring
- **A-3:** Component reuse strategy will reduce code duplication

---

## 9. Success Metrics

### SM-1: Code Quality
- Number of INPUT/DISPLAY components: <10 total
- Code duplication: <5% between variants
- Test coverage: >80%

### SM-2: Developer Experience
- Time to understand component purpose: <5 minutes
- Time to add new component: <1 hour
- Time to debug component: <30 minutes

---

## 10. Future Considerations

### FC-1: Component Library
- Extract common display components
- Create shared UI library
- Standardize component patterns

### FC-2: Dynamic Adaptation
- Auto-generate DISPLAY variants from INPUT
- Component composition system
- Template-based component generation

---

## Appendix

### A. References
- `frontend/src/app/workbench/` — Existing workbench components
- `frontend/src/app/workspace/` — New workspace components
- `Docs/DESIGN.md` — Design system guidelines

### B. Glossary
- **INPUT Component:** Component that collects user input and triggers processing
- **DISPLAY Component:** Component that shows processed data without input
- **BOTH Component:** Component that can serve both purposes with props