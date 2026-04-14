# PM Templates and Frameworks

**Date**: 2026-04-14
**Purpose**: Ready-to-use templates for product management work

---

## Template 1: MVP Scope Definition

```markdown
# MVP Scope: [Product Name]

## Vision Statement
[One sentence: Who it's for, what it does, why it matters]

## Success Criteria
[What must be true for MVP to be considered successful]

## Non-Negotiables (Must Have)
1. [Feature] - [Why it's non-negotiable]
2. [Feature] - [Why it's non-negotiable]
3. [Feature] - [Why it's non-negotiable]

## Nice-to-Haves (Should Have)
1. [Feature] - [Why it's valuable but not critical]
2. [Feature] - [Why it's valuable but not critical]

## Won't Have (Explicitly Out of Scope)
1. [Feature] - [Why it's out of scope]
2. [Feature] - [Why it's out of scope]

## Assumptions
1. [Assumption] - [How we'll validate]
2. [Assumption] - [How we'll validate]

## Risks
1. [Risk] - [Mitigation]
2. [Risk] - [Mitigation]

## Definition of Done
- [ ] Can process a real trip from end to end
- [ ] 5 design partners have used it successfully
- [ ] NPS > 30
- [ ] No critical bugs
- [ ] Documentation exists

---
```

### Filled Example: Agency OS MVP

```markdown
# MVP Scope: Agency OS

## Vision Statement
AI-powered assistant that helps travel agents turn messy client messages into organized trip options in minutes instead of hours.

## Success Criteria
- 5 design partners actively using it for real trips
- 80%+ say it saved them time
- 60%+ say quality is acceptable or better
- 40%+ week 4 retention

## Non-Negotiables (Must Have)
1. **Intent extraction** - Core value, must understand freeform text
2. **Contradiction detection** - Prevents wasted effort on impossible trips
3. **Option generation** - 2-3 ranked options with rationale
4. **Agent review workflow** - Human must always be in control
5. **Client presentation** - Shareable link or PDF

## Nice-to-Haves (Should Have)
1. **Learning from patterns** - Improves with use
2. **Analytics dashboard** - Agency owner visibility
3. **Trip history** - Reference past trips

## Won't Have (Explicitly Out of Scope)
1. **Booking integrations** - Agents handle booking themselves
2. **CRM integrations** - Not needed yet
3. **Mobile app** - Web-first is sufficient
4. **Multi-language** - English only for MVP
5. **White-labeling** - Platform branding for now

## Assumptions
1. **Agencies will paste client WhatsApp messages** - Validate with design partners
2. **AI output quality is "good enough" initially** - NPS target > 30
3. **Agencies will pay ₹999/month** - Pre-sell 5 customers

## Risks
1. **Privacy concerns about sharing client data** - Strong data policy, agency owns data
2. **AI quality inconsistent** - Human review gate, gradual rollout
3. **Adoption too slow** - Focus on high-touch onboarding

## Definition of Done
- [x] Can process a real trip from end to end
- [ ] 5 design partners have used it successfully
- [ ] NPS > 30
- [ ] No critical bugs
- [ ] Documentation exists

---
```

---

## Template 2: Feature PRD

```markdown
# Feature: [Name]

## Metadata
- **Status**: [Backlog / In Progress / In Review / Done]
- **Priority**: [P0 / P1 / P2 / P3]
- **Owner**: [Who's responsible]
- **Target Release**: [When]

## Problem Statement
[What user problem does this solve? Include quotes from users if possible]

## Proposed Solution
[Description of the solution]

## Success Metrics
| Metric | Baseline | Target | How to Measure |
|--------|----------|--------|----------------|
| [Metric 1] | [Current] | [Target] | [Method] |
| [Metric 2] | [Current] | [Target] | [Method] |

## User Stories
- As a [user type], I want [action], so that [benefit]
- As a [user type], I want [action], so that [benefit]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## Technical Considerations
[Any technical notes, dependencies, or constraints]

## Design Requirements
[UI/UX requirements, mockups needed]

## Open Questions
1. [Question] - [Who needs to answer]
2. [Question] - [Who needs to answer]

---
```

---

## Template 3: Assumption Log

```markdown
# Assumption Log

| ID | Assumption | Owner | Status | Validation Method | Due Date | Result |
|----|------------|-------|--------|-------------------|----------|--------|
| A001 | Agencies will paste client data | [Name] | Not Validated | 5 design partners | [Date] | [Validated/Invalidated] |
| A002 | AI quality is sufficient | [Name] | Not Validated | NPS survey | [Date] | [Validated/Invalidated] |
| A003 | Price point ₹999 works | [Name] | Not Validated | Pre-sale | [Date] | [Validated/Invalidated] |

## Status Legend
- **Not Validated**: We haven't tested this yet
- **In Validation**: Experiment running
- **Validated**: Assumption holds true
- **Invalidated**: Assumption was wrong, pivot needed

---
```

---

## Template 4: Weekly Product Review

```markdown
# Weekly Product Review - Week of [Date]

## Metrics Dashboard
| Metric | This Week | Last Week | Change | Trend |
|--------|-----------|-----------|--------|-------|
| Active agencies | _ | _ | _ | ↗️ → ↘️ |
| Trips processed | _ | _ | _ | ↗️ → ↘️ |
| Activation rate | _% | _% | _ | ↗️ → ↘️ |
| Week 4 retention | _% | _% | _ | ↗️ → ↘️ |
| NPS | _ | _ | _ | ↗️ → ↘️ |

## Shipping This Week
- [Feature] - [Brief description]
- [Bug fix] - [Brief description]
- [Improvement] - [Brief description]

## Learning This Week
### What We Learned
- [Insight 1]
- [Insight 2]

### What Surprised Us
- [Surprise 1]
- [Surprise 2]

### User Feedback (Highlights)
> "[Quote from user]"

### User Feedback (Pain Points)
> "[Quote from user]"

## Decisions Made
1. [Decision] - [Rationale]
2. [Decision] - [Rationale]

## Blockers
| Blocker | Impact | Owner | Status | ETA |
|---------|--------|-------|--------|------|
| [Blocker] | [High/Med/Low] | [Name] | [Open/In Progress/Resolved] | [Date] |

## Next Week Priorities
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

## Risks to Watch
- [Risk 1] - [Mitigation]
- [Risk 2] - [Mitigation]

---
```

---

## Template 5: User Interview Script

```markdown
# User Interview Script

## Introduction (2 min)
"Hi [Name], thanks for taking the time. I'm [Your Name] from Agency OS. 
We're building a tool for travel agents and I'd love to learn about your 
current process. This is not a sales pitch — I'm here to learn."

## Warm-up (3 min)
1. Can you tell me a bit about your agency?
2. How long have you been in travel?
3. What types of trips do you typically plan?

## Current Process (10 min)
1. Walk me through how a typical trip planning request comes in.
   [Probe: What's the first thing you do?]
   [Probe: What information do you usually have?]
   [Probe: What's the most time-consuming part?]
   
2. Tell me about a recent trip that was challenging to plan.
   [Probe: What made it challenging?]
   [Probe: How did you handle it?]
   
3. How do you currently organize information from clients?
   [Probe: WhatsApp, email, notes app?]
   [Probe: Ever miss anything important?]

## Pain Points (10 min)
1. What's the most frustrating part of your planning process?
2. What tasks do you find yourself doing repeatedly?
3. What would make your life 10x easier?
4. If you could wave a magic wand, what would you fix?

## Solution Testing (10 min)
[Show mockup or describe solution]

1. What are your initial reactions to this?
2. How would this fit into your workflow?
3. What would make you NOT use this?
4. What would make this indispensable?

## Closing (2 min)
"This has been incredibly helpful. Is there anything else I should have asked?
Would you be willing to try this when we have something ready to test?"

## Post-Interview Notes
- Key insights:
- Pain points identified:
- Feature requests:
- Willingness to try: [Yes/No/Maybe]
- Follow-up needed: [Yes/No]

---
```

---

## Template 6: Experiment Brief

```markdown
# Experiment: [Name]

## Hypothesis
We believe that [doing X] will result in [Y], because [rationale].

## Success Criteria
- [Metric 1]: [Target]
- [Metric 2]: [Target]

## Method
[Describe what you'll do]

## Timeline
- Start: [Date]
- End: [Date]
- Total duration: [Days/Weeks]

## Required Resources
- [Resource 1]
- [Resource 2]

## Success Metrics
| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| [Metric] | [Target] | _ | _ |

## Learnings
### What Worked
- [Learning 1]
- [Learning 2]

### What Didn't Work
- [Learning 1]
- [Learning 2]

### Next Steps
- [Action 1]
- [Action 2]

---
```

---

## Template 7: Go/No-Go Decision

```markdown
# Go/No-Go Decision: [Feature/Project]

## Proposal
[Brief description of what we're considering building]

## Evaluation Criteria
Score each from 1-5 (1 = Poor, 5 = Excellent)

### Strategic Fit (1-5)
- Does this align with our vision?
- Does this serve our target users?
- Score: ___/5

### User Value (1-5)
- Does this solve a real problem?
- How much value does it create?
- Score: ___/5

### Feasibility (1-5)
- Can we build this?
- Do we have the resources?
- Score: ___/5

### ROI (1-5)
- Effort vs. impact
- Opportunity cost
- Score: ___/5

### Risk (1-5)
- What could go wrong?
- How bad would failure be?
- Score: ___/5 (higher = lower risk)

### Data Validation (1-5)
- Do we have evidence users want this?
- Have we tested assumptions?
- Score: ___/5

## Total Score
___ / 30

## Decision
- **GO**: Build this
- **NO**: Don't build this
- **DEFER**: Revisit later

## Rationale
[Explain the decision]

---
```

---

## Template 8: Retrospective

```markdown
# Retrospective - [Sprint/Month/Quarter]

## What Went Well
- [Win 1]
- [Win 2]
- [Win 3]

## What Didn't Go Well
- [Issue 1]
- [Issue 2]
- [Issue 3]

## What We Learned
- [Lesson 1]
- [Lesson 2]

## Action Items
| Item | Owner | Due Date | Status |
|------|-------|----------|--------|
| [Action 1] | [Name] | [Date] | [Open/Done] |
| [Action 2] | [Name] | [Date] | [Open/Done] |

---
```

---

## Template 9: Stakeholder Map

```markdown
# Stakeholder Map

## Stakeholder Analysis

| Stakeholder | Interest | Influence | Engagement Strategy | Status |
|-------------|----------|-----------|---------------------|--------|
| [Name/Group] | [High/Med/Low] | [High/Med/Low] | [How to engage] | [Engaged/Not/In Progress] |

## Interest-Influence Matrix

```
High Influence ───────────────────────────────────
│                                              │
│  MANAGE CLOSELY                KEEP SATISFIED│
│  (High Interest)                         (High Interest)
│                                              │
Low Influence ───────────────────────────────────
│                                              │
│  MONITOR                        KEEP INFORMED│
│  (Low Interest)                          (High Interest)
│                                              │
└──────────────────────────────────────────────
  Low Interest                    High Interest
```

## Communication Plan
- [Stakeholder]: [Frequency], [Channel], [Content]
- [Stakeholder]: [Frequency], [Channel], [Content]

---
```

---

## Template 10: Premortem

```markdown
# Premortem: [Project/Product]

## The Scenario
It's [6 months] from now and [Project/Product] has FAILED.

## Brainstorm: Why Did It Fail?
[List all possible reasons, no matter how unlikely]

1. [Reason 1]
2. [Reason 2]
3. [Reason 3]
...

## Risk Analysis
For each reason above:

| Failure Reason | Probability | Impact | Mitigation |
|----------------|-------------|--------|------------|
| [Reason] | [High/Med/Low] | [High/Med/Low] | [What to do now] |

## Early Warning Signs
What signals would indicate we're heading toward failure?

1. [Signal 1] - [What to do if seen]
2. [Signal 2] - [What to do if seen]
3. [Signal 3] - [What to do if seen]

---
```

---

## Quick Reference: When to Use Which Template

| Situation | Use Template |
|-----------|--------------|
| Starting a new feature | Feature PRD |
| Planning MVP scope | MVP Scope Definition |
| Weekly check-in | Weekly Product Review |
| Before building anything | Assumption Log + Experiment Brief |
| Talking to users | User Interview Script |
| Deciding whether to build | Go/No-Go Decision |
| After a sprint/release | Retrospective |
| Starting a project | Premortem |
| Planning stakeholder engagement | Stakeholder Map |
