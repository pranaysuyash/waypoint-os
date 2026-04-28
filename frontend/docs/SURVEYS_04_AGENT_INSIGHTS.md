# Surveys & Feedback Collection — Agent Feedback & Internal Insights

> Research document for agent feedback collection, internal satisfaction tracking, and employee experience.

---

## Key Questions

1. **What agent feedback is critical for platform improvement?**
2. **How do we collect honest agent feedback without fear of reprisal?**
3. **What's the agent satisfaction measurement model?**
4. **How do agent insights translate to product improvements?**
5. **What's the feedback culture model for the organization?**

---

## Research Areas

### Agent Feedback Collection

```typescript
interface AgentFeedbackProgram {
  surveys: AgentSurvey[];
  channels: FeedbackChannel[];
  anonymity: AnonymityConfig;
  insights: FeedbackInsight[];
}

type AgentSurveyType =
  | 'platform_satisfaction'           // How happy are agents with the platform?
  | 'feature_request'                 // What features do agents need?
  | 'bug_report'                      // What's broken?
  | 'workflow_feedback'               // How can workflows improve?
  | 'training_feedback'               // Was training effective?
  | 'onboarding_feedback'             // How was the onboarding experience?
  | 'periodic_pulse'                  // Monthly 3-question pulse check
  | 'exit_interview';                 // Why are you leaving?

// Agent satisfaction survey (quarterly):
// 1. How satisfied are you with the platform? (1-5)
// 2. How easy is it to find the tools you need? (1-5)
// 3. How would you rate the customer communication tools? (1-5)
// 4. What's the ONE thing you'd improve? (text)
// 5. What feature do you wish existed? (text)
// 6. How supported do you feel by the platform? (1-5)
// 7. Would you recommend this platform to another agent? (0-10)

// In-app feedback mechanisms:
// 1. "Feedback" button in workbench sidebar (always accessible)
// 2. Emoji reactions on features (👍/👎 on specific tools)
// 3. Screenshot annotation (highlight a UI issue, annotate, submit)
// 4. "Suggest improvement" link on every page
// 5. Post-action micro-survey (after booking: "Was this easy?" 👍/👎)

interface AnonymityConfig {
  defaultMode: 'anonymous' | 'identified';
  agentChooses: boolean;
  anonymousFeedbackStored: boolean;
  managerCanSeeIdentified: boolean;
}

// Anonymity policy:
// Platform satisfaction surveys: Anonymous by default
// Feature requests: Identified (so we can follow up)
// Bug reports: Identified (so we can contact for details)
// Exit interviews: Anonymous (critical for honest feedback)
// General feedback: Agent chooses
```

### Agent Satisfaction Metrics

```typescript
interface AgentSatisfaction {
  overallScore: number;               // 1-5
  platformEaseOfUse: number;
  toolCompleteness: number;
  supportResponsiveness: number;
  workflowEfficiency: number;
  wouldRecommend: number;             // eNPS (employee NPS)
  verbatimThemes: ThemeAnalysis[];
}

// Agent eNPS (Employee Net Promoter Score):
// "How likely are you to recommend this platform to a colleague?"
// 0-10 scale
// Promoters (9-10): Love the platform
// Passives (7-8): Fine but not enthusiastic
// Detractors (0-6): Frustrated, would discourage others

// Agent satisfaction benchmarks:
// Platform ease of use: Target > 4.0 (travel agents are not tech-savvy)
// Tool completeness: Target > 3.5 (agents always want more features)
// Support responsiveness: Target > 4.5 (fast support = trust)
// Workflow efficiency: Target > 4.0 (agents measure themselves by speed)

// Correlation analysis:
// Agent satisfaction vs. Customer satisfaction:
//   Agents who rate platform > 4 → Customer NPS 45
//   Agents who rate platform 3-4 → Customer NPS 30
//   Agents who rate platform < 3 → Customer NPS 15
// → Improving agent experience directly improves customer experience

// Agent satisfaction drivers (by impact):
// 1. Speed (fast booking, quick search)
// 2. Reliability (no bugs, no downtime)
// 3. Completeness (all features in one place)
// 4. Mobile access (field work capability)
// 5. Support (fast help when stuck)
// 6. Training (continuous learning)
// 7. Earnings (commission visibility and tracking)
```

### Product Improvement Pipeline

```typescript
interface ProductImprovement {
  source: 'agent_feedback' | 'customer_feedback' | 'data_analysis' | 'strategic';
  insight: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  effort: 'small' | 'medium' | 'large';
  impact: 'high' | 'medium' | 'low';
  status: 'suggested' | 'planned' | 'in_development' | 'shipped';
  requesterNotified: boolean;
}

// Feedback to roadmap pipeline:
// 1. Agent submits feedback ("I wish I could compare hotel prices side by side")
// 2. System categorizes: Feature request → Pricing → Comparison
// 3. Product team reviews: Is this a common request? (15 agents asked for this)
// 4. Impact assessment: Would save 3 min/trip × 10 trips/day × 20 agents = 10 hrs/day
// 5. Prioritization: High impact, medium effort → Add to next sprint
// 6. Agent notified: "Your suggestion is being built! ETA: 2 weeks"
// 7. Feature shipped: Agent who suggested gets early access + recognition

// Feedback transparency:
// Agents can see:
// - Their submitted feedback and status
// - Popular feature requests (and vote on them)
// - What's being built (roadmap)
// - Recently shipped improvements
// This creates trust that feedback is acted upon, not ignored
```

---

## Open Problems

1. **Honest feedback fear** — Agents fear negative feedback will affect their job. Need strong anonymity guarantees and culture of constructive feedback.

2. **Feedback overload for product team** — 50 agents × 5 suggestions each = 250 feature requests. Prioritization is critical.

3. **Confirmation bias** — Agents ask for features they know, not what would be transformative. Innovation comes from understanding problems, not feature requests.

4. **Implementation lag** — Agent suggests improvement in January, ships in April. By then, they've forgotten they asked. Need tight feedback loop communication.

5. **Representative sampling** — Vocal agents dominate feedback. Quiet agents may have different needs. Need proactive outreach to underrepresented voices.

---

## Next Steps

- [ ] Design agent feedback system with anonymous and identified modes
- [ ] Build in-app feedback mechanisms (emoji, screenshot, micro-surveys)
- [ ] Create agent satisfaction tracking with eNPS
- [ ] Design feedback-to-roadmap transparency pipeline
- [ ] Study employee feedback systems (Culture Amp, Peakon, Lattice)
