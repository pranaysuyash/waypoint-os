# Testing Strategy — Master Index

> Complete navigation guide for all Testing documentation

---

## Series Overview

**Topic:** Testing Strategy and Quality Assurance
**Status:** Complete (6 of 6 documents)
**Last Updated:** 2026-04-26

---

## Document Series

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 1 | [Testing Philosophy](#testing-01) | Test pyramid, quality metrics, testing culture | ✅ Complete |
| 2 | [Unit Testing](#testing-02) | Component testing, hooks, utilities, Vitest | ✅ Complete |
| 3 | [Integration Testing](#testing-03) | API testing, database, MSW, Playwright | ✅ Complete |
| 4 | [E2E Testing](#testing-04) | User flows, critical paths, test data | ✅ Complete |
| 5 | [Visual Regression](#testing-05) | Chromatic, Storybook, screenshot testing | ✅ Complete |
| 6 | [Performance Testing](#testing-06) | Load testing, bundle analysis, budgets | ✅ Complete |

---

## Document Summaries

### TESTING_01: Testing Philosophy

**File:** `TESTING_STRATEGY_01_PHILOSOPHY.md`

**Proposed Topics:**
- Test pyramid principles
- Quality vs speed tradeoffs
- Testing culture and ownership
- What not to test
- Test maintenance philosophy
- Quality gates and CI
- Testing metrics and KPIs
- Regression testing strategy

---

### TESTING_02: Unit Testing

**File:** `TESTING_STRATEGY_02_UNIT.md`

**Proposed Topics:**
- Component testing with RTL
- Hook testing patterns
- Utility function testing
- Mock vs stub vs spy
- Test doubles and fixtures
- Coverage goals and limits
- Fast test execution
- Test isolation

---

### TESTING_03: Integration Testing

**File:** `TESTING_STRATEGY_03_INTEGRATION.md`

**Proposed Topics:**
- API route testing
- Database integration tests
- MSW for API mocking
- Service layer testing
- Third-party integration testing
- Contract testing
- Test containers
- State management testing

---

### TESTING_04: E2E Testing

**File:** `TESTING_STRATEGY_04_E2E.md`

**Proposed Topics:**
- Playwright setup
- Critical user journeys
- Authentication flows
- Booking workflows
- Payment testing (sandbox)
- Test data management
- Flaky test mitigation
- Parallel execution

---

### TESTING_05: Visual Regression

**File:** `TESTING_STRATEGY_05_VISUAL.md`

**Proposed Topics:**
- Chromatic integration
- Storybook for visual testing
- Screenshot comparison
- Cross-browser testing
- Responsive visual testing
- Interaction testing
- Review workflow
- False positive handling

---

### TESTING_06: Performance Testing

**File:** `TESTING_STRATEGY_06_PERFORMANCE.md`

**Proposed Topics:**
- Lighthouse CI
- Bundle analysis
- Performance budgets
- Load testing with k6
- Memory leak detection
- Core Web Vitals monitoring
- Database query performance
- Caching effectiveness

---

## Related Documentation

**Cross-References:**
- [DevOps & Infrastructure](./DEVOPS_DEEP_DIVE_MASTER_INDEX.md) — CI/CD integration
- [Design System](./DESIGN_SYSTEM_DEEP_DIVE_MASTER_INDEX.md) — Component testing
- [Security Architecture](./SECURITY_DEEP_DIVE_MASTER_INDEX.md) — Security testing

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Vitest** | Faster than Jest, native ESM, better UI |
| **React Testing Library** | Encourages user-centric testing |
| **Playwright** | Cross-browser, faster than Cypress, auto-waiting |
| **MSW** | API mocking at network level, works in browser and Node |
| **Chromatic** | Visual testing, integrates with PRs |
| **k6** | Scriptable load testing, good observability |

---

## Testing Stack

```txt
Unit/Integration:  Vitest + React Testing Library + MSW
E2E:              Playwright
Visual:           Chromatic + Storybook
Performance:      Lighthouse CI + k6
Coverage:         c8 (built into Vitest)
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Testing philosophy documented
- [ ] Vitest configured and integrated
- [ ] RTL patterns established
- [ ] CI test pipeline running

### Phase 2: Coverage
- [ ] Core components unit tested
- [ ] API routes integration tested
- [ ] Critical flows E2E tested
- [ ] Storybook visual tests running

### Phase 3: Automation
- [ ] PR test gates enabled
- [ ] Performance budgets enforced
- [ ] Visual regression on PRs
- [ ] Load tests in CI

### Phase 4: Culture
- [ ] Testing guidelines in AGENTS.md
- [ ] Test writing training
- [ ] Quality metrics dashboard
- [ ] Regular test audits

---

## Coverage Goals

| Layer | Goal | Notes |
|-------|------|-------|
| **Unit** | 70% | Focus on business logic, not implementation |
| **Integration** | Key paths | API routes, database operations |
| **E2E** | Critical flows | Booking, payment, auth (not everything) |
| **Visual** | All components | Catch UI regressions early |

---

**Last Updated:** 2026-04-26

**Current Progress:** 6 of 6 documents complete (100%)
