# Agent Training — Onboarding Workflow

> Research document for new agent onboarding, role setup, and first-day experience.

---

## Key Questions

1. **What's the ideal onboarding timeline for a new travel agent (day 1, week 1, month 1)?**
2. **What role-based variations exist in the onboarding flow (junior, senior, specialized)?**
3. **How do we verify an agent is ready to handle real customers?**
4. **What system access and tool training is required before first booking?**
5. **How do we measure onboarding effectiveness?**

---

## Research Areas

### Onboarding Phases

```typescript
interface OnboardingPlan {
  planId: string;
  role: AgentRole;
  phases: OnboardingPhase[];
  totalDuration: string;
  completionCriteria: CompletionCriteria[];
}

type AgentRole =
  | 'junior_agent'      // Entry-level, handles simple trips
  | 'senior_agent'      // Experienced, handles complex/enterprise
  | 'specialist'        // Domain expert (cruise, MICE, corporate)
  | 'team_lead'         // Manages team of agents
  | 'operations';       // Back-office operations

interface OnboardingPhase {
  phase: string;
  duration: string;
  objectives: string[];
  tasks: OnboardingTask[];
  assessment?: Assessment;
  gate: GateCriteria;            // Must pass before next phase
}

// Phase structure:
// Phase 1 (Day 1-2): Company orientation + system access
// Phase 2 (Day 3-5): Platform training (workbench, intake, spine)
// Phase 3 (Week 2): Simulated bookings with mentor oversight
// Phase 4 (Week 3-4): Supervised real bookings
// Phase 5 (Month 2-3): Independent work with periodic review

interface OnboardingTask {
  taskId: string;
  title: string;
  type: 'reading' | 'video' | 'hands_on' | 'simulation' | 'shadowing' | 'assessment';
  estimatedDuration: string;
  required: boolean;
  completedAt?: Date;
  verifiedBy?: string;
}
```

### System Access Provisioning

```typescript
interface SystemAccessChecklist {
  agentId: string;
  accessItems: AccessItem[];
  provisionedAt?: Date;
  provisionedBy: string;
}

interface AccessItem {
  system: string;
  accessLevel: string;
  status: 'pending' | 'requested' | 'provisioned' | 'verified';
  requiredBy: string;            // Onboarding phase that needs this
}

// Systems to provision:
// - Workbench account (role-based permissions)
// - CRM access (customer data)
// - Booking system (GDS credentials)
// - Communication tools (email, WhatsApp Business)
// - Payment system (refund limits)
// - Document generation
// - Knowledge base
// - Internal Slack/Teams channels
```

### Simulation & Practice Environment

```typescript
interface SimulationEnvironment {
  // Sandbox workbench with fake customer data
  mode: 'sandbox';
  // Pre-built scenarios for practice
  scenarios: SimulationScenario[];
  // No real bookings or payments
  safeMode: true;
  // Mentor can observe and provide feedback
  mentorAccess: boolean;
}

interface SimulationScenario {
  scenarioId: string;
  title: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  description: string;
  customerPersona: string;
  tripRequirements: string;
  expectedActions: string[];
  evaluationCriteria: EvaluationCriteria[];
  duration: string;
  hints: string[];
}
```

---

## Open Problems

1. **Onboarding at scale** — Hiring 20 agents at once overwhelms mentor capacity. Need self-service onboarding with automated checks.

2. **Knowledge assessment validity** — Written tests don't measure actual booking proficiency. Simulation-based assessment is better but harder to build.

3. **Role specialization timing** — When does a general agent become a specialist? Too early means shallow knowledge; too late means missed market opportunity.

4. **Remote onboarding** — Post-pandemic, agents may be remote. Shadowing and hands-on training need virtual alternatives.

5. **Onboarding content freshness** — Travel products, pricing, and policies change frequently. Onboarding materials can become outdated quickly.

---

## Next Steps

- [ ] Design role-based onboarding plan templates
- [ ] Build simulation scenario library for top 10 booking types
- [ ] Design system access provisioning automation
- [ ] Study onboarding platforms (Lessonly, WorkRamp, Docebo)
- [ ] Create onboarding effectiveness metrics dashboard
