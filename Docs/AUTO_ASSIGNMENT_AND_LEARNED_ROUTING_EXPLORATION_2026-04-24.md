# Auto-Assignment and Learned Routing Exploration

**Date**: 2026-04-24
**Status**: Exploration
**Scope**: Governed auto-assignment of cases to human operators using skills, workload, continuity, and bounded learning signals. This is a research and contract-shaping pass, not an implementation spec.
**Related docs**:

- `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`
- `CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md`
- `ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md`
- `SETTINGS_ROUTE_SUBROUTE_UX_CONTRACT_2026-04-23.md`
- `GOVERNANCE_AUDIT_EVENT_TAXONOMY_2026-04-23.md`
- `ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`
- `ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md`
- `BLIND_COMPARISON_ARENA_EXPLORATION_2026-04-23.md`
- `INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md`

---

## Executive Summary

The right version of auto-assignment is not a black-box manager that silently scores people and routes work however it wants.

The strong version is a **governed routing layer** with three levels:

1. deterministic eligibility,
2. transparent recommendation ranking,
3. bounded learning that calibrates ranking only inside an owner/admin-approved policy envelope.

The core insight is that **case assignment is a matching problem, not a worker evaluation system**.

That means the product should optimize for:

- sending the right case to someone who can actually handle it,
- preserving continuity when a traveler or trip already has operator context,
- avoiding overload and SLA collapse,
- learning from outcomes without turning into hidden algorithmic performance management.

### Recommended Decisions

1. Learned routing should initially apply to **initial assignment and ranked suggestion flows**, not to implicit escalation or silent reassignment.
2. **Matching decisions** and **performance evaluation decisions** must remain separate. The system may learn from performance patterns, but should not reduce operators to one opaque score.
3. **Continuity beats optimization** when the traveler, trip, or review context already belongs with a current operator unless policy explicitly says otherwise.
4. The first shippable version should be **suggestion-first** with explanations, then optional low-risk auto-apply later.
5. Every automated recommendation or automatic assignment must be **auditable, explainable, and contestable**.

---

## Why This Exists

The governance roadmap already defines:

- canonical human roles,
- routing slots,
- escalation preserving the `primary_assignee`,
- a real `/settings/assignments` surface,
- and adaptive governance that can learn from evidence.

What it does not yet define is the best way to handle this next question:

- How should the system assign new work to the right operator as the agency grows?
- What should be deterministic vs. learned?
- Which signals are safe to use?
- When is auto-assignment acceptable, and when is it too risky or too opaque?

This exploration answers those questions before implementation creates another ad-hoc assignment path.

---

## Current Repo Evidence

The codebase already has partial ingredients for assignment, workload, and operator performance, but not yet a canonical learned-routing foundation.

### 1. Assignment is still a single-slot storage model

Current persistence in `spine_api/persistence.py` stores one assignment record per trip with:

- `trip_id`
- `agent_id`
- `agent_name`
- `assigned_at`
- `assigned_by`

This is materially below the routing model defined in `ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md`, which requires `primary_assignee`, `reviewer`, `escalation_owner`, `watchers`, handoff state, and separate ownership/governance axes.

### 2. Review escalation still behaves like reassignment in runtime code

Current review handling in `src/analytics/review.py` still routes escalated or repeated-revision work to `management_queue` by mutating `assigned_to` directly.

That conflicts with the canonical governance decision that escalation adds oversight while preserving the current primary assignee by default.

### 3. Team performance data is partly real and partly simulated

`src/analytics/metrics.py` already computes some operator metrics, but:

- customer satisfaction is derived from extracted feedback ratings when available,
- active/completed trip counts are grounded in trip data,
- conversion rate is simulated,
- average response time is simulated,
- workload score is a simple function of active count.

This means the current team-metrics layer is not yet reliable enough to drive learned routing decisions directly.

### 4. Workload signals exist, but only in coarse form

`spine_api/server.py` exposes `/api/team/workload`, which already counts assigned trips and compares them against a stored capacity value.

That is useful as a deterministic seed signal, but it is not yet a full routing model.

### 5. Audit and frontend types are not yet on canonical governance contracts

- `spine_api/persistence.py` still emits generic events such as `trip_assigned` and `trip_unassigned`.
- `src/analytics/review.py` still emits umbrella `review_action` events.
- `frontend/src/types/governance.ts` still uses the older `owner | manager | agent | viewer` vocabulary instead of `Owner | Admin | SeniorAgent | JuniorAgent | Viewer`.

That matters because learned routing should not ship before roles, routing state, and audit naming are stabilized.

### 6. The broader product analysis already identified the gap

`INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md` explicitly notes that the system still has **no auto-assignment** and no mature workload routing. So this is a real known product gap, not speculative scope growth.

---

## External Reference Patterns

## 1. Skills-Based Routing Is The Baseline, Not The Finish Line

Operational systems like ServiceNow and Zendesk frame routing around:

- explicit skill determination,
- skill qualification,
- skill ranking,
- availability and workload,
- queue and channel context.

This is the correct baseline lesson for Waypoint:

- first determine who is eligible,
- then rank among eligible operators,
- do not begin with a hidden performance score.

Reference patterns:

- ServiceNow skills-based routing documentation
- Zendesk skills-based routing guidance

## 2. Skills-Based Routing Has Real Operational Complexity

Operations-research work on skill-based routing consistently shows that once there are multiple worker types, queue states, and demand classes, naive routing logic performs badly.

The relevant lesson is not "use reinforcement learning immediately." It is:

- routing becomes a multi-factor queueing problem quickly,
- queue lengths and overload matter,
- cross-training matters,
- and local optimization can create system-level bottlenecks.

So the product should avoid simplistic rules like "always send luxury Europe leads to the highest-converting Europe expert" if that expert is already overloaded.

## 3. Matching Decisions And Performance Evaluation Should Stay Separate

Research on algorithmic work assignment and algorithmic HRM suggests an important split:

- people often accept algorithms more readily for objective matching/allocation tasks,
- they are more skeptical when algorithms drift into human-style evaluation or judgment-heavy decisions,
- transparency, contestability, and human oversight materially affect fairness perceptions.

This is directly relevant here.

Waypoint can safely be more ambitious about **matching work to operators** than about building a hidden machine that decides who is a good or bad employee.

---

## The Core Framing

The product should frame this capability as:

**Assignment intelligence = governed case-to-operator matching.**

Not:

- employee ranking,
- algorithmic performance management,
- invisible gamification,
- or silent replacement of human routing authority.

That framing matters because it changes what signals are appropriate.

Good routing signals answer:

- who can handle this case,
- who should handle it now,
- who already has useful context,
- and who is likely to progress it without breaching policy or SLA.

Bad routing signals answer:

- who the system "likes" in general,
- who had the highest raw revenue last month,
- who closes the most easy leads,
- or who looks fastest without controlling for case difficulty.

---

## Foundational Principles

### 1. Eligibility Before Optimization

The system must first determine who is even eligible to receive a case.

Eligibility should include things like:

- role permission,
- active membership,
- queue access,
- stage permission,
- destination or product specialization,
- channel/language/time-zone fit,
- capacity availability.

Learning should never override hard eligibility constraints.

### 2. Continuity Before Fresh Optimization

If the traveler or trip already has a strong operator relationship, continuity should usually win.

Examples:

- repeat traveler already handled by a specific agent,
- trip already has a `primary_assignee`,
- current operator asked for review but not handoff,
- escalation exists but reassignment was not explicitly chosen.

This preserves context and matches the canonical routing spec.

### 3. Matching Is Not Performance Management

The system may use outcome-informed routing signals, but it should not create an opaque global worker score that silently drives access to work.

If performance-derived signals exist, they should be:

- contextual,
- normalized by trip class,
- bounded by minimum sample rules,
- and visible enough to explain and challenge.

### 4. Learning Should Calibrate, Not Dominate

Early learned routing should tune or rank within a deterministic policy, not replace it.

This means:

- policy defines what matters,
- data calibrates the weight or ordering,
- owner/admin govern whether learning can influence suggestions or auto-apply.

### 5. Assignment Must Stay Governed

This capability belongs under `/settings/assignments`, not buried inside inbox code or a debug panel.

Admins and owners should be able to see:

- whether assignment is manual, suggestion-based, or auto-apply for a queue,
- which signals are active,
- what rules are Owner-only,
- and how the system explains each recommendation.

### 6. Assignment Signals Need Auditability

If the system recommends or applies an assignment, the agency should be able to answer:

- who got it,
- who else was eligible,
- why this operator ranked highest,
- whether the assignment was auto-applied or human-confirmed,
- and whether the human accepted or overrode the recommendation.

---

## Recommended Model

## Layer 1: Deterministic Eligibility

This layer answers:

- Which operators are allowed to receive this work at all?

Candidate inputs:

- canonical role (`SeniorAgent`, `JuniorAgent`, etc.)
- active membership
- current assignment policy
- queue access
- specialization tags
- supported channels or shift availability
- capacity floor / max concurrent active trips

If an operator is not eligible, the rest of the system should never rank them.

## Layer 2: Transparent Routing Score

This layer answers:

- Among eligible operators, who is the best fit right now?

The recommendation should be explainable as a score breakdown, not a magic number.

Example signal families:

- continuity bonus
- specialization match
- trip-class familiarity
- capacity headroom
- active SLA pressure
- recent handoff pressure
- channel/time-zone fit
- review or escalation burden

The important point is that the UI can show why someone ranked high or low.

## Layer 3: Bounded Learning Calibration

This layer answers:

- Over time, do our ranking weights need to change for a specific trip class or queue?

This is where learning belongs:

- not direct uncontrolled auto-routing,
- but tuning recommendations using observed outcomes and overrides.

Learning examples:

- family-Europe summer leads perform better with one cluster of agents,
- luxury FIT trips are frequently reassigned away from junior operators,
- one queue is overfitting to a "top performer" and causing SLA overload,
- a particular operator gets better outcomes on complex visa-heavy trips.

---

## Signal Families

## Safe And High-Value Signals

### Continuity Signals

- prior traveler/operator relationship
- existing trip ownership
- review or handoff history
- same customer household or account

### Capability Signals

- destination familiarity
- trip-type specialization
- seniority threshold
- language/channel compatibility
- allowed stage scope

### Capacity Signals

- active trip load
- capacity remaining
- current SLA risk
- review backlog
- handoff backlog

### Outcome Signals

Only when normalized and sufficiently sampled:

- response timeliness by trip class
- approval rate by class and risk band
- post-trip satisfaction by class
- override frequency by class
- reassignment/handoff frequency by class

## Signals That Need Strong Guardrails

- raw win rate without controlling for trip difficulty
- raw revenue generated without complexity normalization
- owner override counts without cause classification
- simple completion speed on trips that vary widely in complexity
- sentiment or behavior-derived worker scoring that operators cannot inspect or contest

## Signals That Should Be Off-Limits Or Extreme-Caution Only

- protected-class proxies
- hidden productivity surveillance signals
- broad personality inference
- LLM-generated judgments about operator character or effort

---

## Canonical Policy Shape

The exact contract should be specified later, but the assignment settings surface will likely need a policy shape like this:

```ts
type AssignmentMode =
  | 'manual_only'
  | 'ranked_suggestions'
  | 'auto_assign_low_risk'
  | 'auto_assign_selected_queues'

type AssignmentPolicy = {
  mode: AssignmentMode
  eligibleRoles: ('Owner' | 'Admin' | 'SeniorAgent' | 'JuniorAgent')[]
  requiredSignals: string[]
  optionalSignals: string[]
  continuityPriority: 'low' | 'medium' | 'high' | 'required_when_present'
  autoAssignQueues: string[]
  minConfidenceToAutoAssign: number
  learningEnabled: boolean
  explainabilityRequired: boolean
  fairnessReviewRequired: boolean
}
```

The important thing is not the exact field names yet. The important thing is that assignment policy becomes:

- explicit,
- mutable through governed settings,
- and distinct from per-trip assignment execution.

---

## What Learning Should Actually Learn

The most useful learning target is not:

- "who is the best agent overall?"

It is:

- "for this class of case, under this workload state, which assignment pattern works best?"

That implies the system should learn over **trip classes** or **routing cohorts**, not over one giant undifferentiated pool.

Examples of useful cohorts:

- destination region
- trip type
- value band
- complexity band
- urgency band
- intake channel
- traveler profile / repeat status
- visa or documentation burden

This also aligns with the D1 direction toward customer+trip classification rather than flat one-size-fits-all policy.

---

## Recommended Delivery Sequence

## Phase A: Instrumentation And Reality Check

Before any learned routing:

- replace simulated team metrics with real measured signals where possible,
- stabilize canonical roles,
- stabilize routing slots,
- emit canonical audit events,
- define specialization and capability attributes for operators.

Output:

- trustworthy routing inputs,
- no user-facing auto-assignment yet.

## Phase B: Ranked Suggestions

Ship suggestion mode first.

Behavior:

- system ranks eligible operators,
- owner/admin sees reason breakdown,
- human confirms assignment,
- accepts or overrides recommendation,
- override reason becomes a learning signal.

Why this is the correct first ship:

- produces audit data,
- lets operators inspect logic,
- avoids premature automation,
- exposes where signal quality is weak.

## Phase C: Learning-Assisted Ranking

Only after sufficient data quality:

- tune score weights per trip class,
- surface confidence and recommendation rationale,
- require minimum sample counts before class-level learning influences ranking,
- log accepted vs. overridden recommendations.

This should still be suggestion-first.

## Phase D: Limited Auto-Assignment

Auto-apply should begin only in objective, lower-risk conditions such as:

- fresh intake queues,
- simple standard trip classes,
- no continuity conflict,
- adequate eligible pool,
- confidence above threshold,
- no current overload anomaly.

This phase should never mean:

- escalation-driven reassignment,
- hidden reassignment of active owned work,
- or unreviewable operator scoring.

---

## Relationship To Existing Governance Contracts

## Canonical Roles

The role matrix already defines who may claim, operate, reassign, or review work.

Learned routing must inherit those permissions.

It cannot create a parallel permission model.

## Assignment State Machine

The state machine already establishes the critical invariant:

- escalation does not imply reassignment.

Learned auto-assignment should therefore be scoped primarily to:

- unassigned work,
- explicit handoff flows,
- or explicit reassignment flows where policy allows.

It should not silently mutate ownership during escalation.

## Settings Route

The settings UX contract already gives `/settings/assignments` responsibility for:

- routing defaults,
- escalation defaults,
- claim policy,
- workload policy.

Learned assignment policy belongs here as part of routing/workload governance.

## Audit Taxonomy

The audit taxonomy does not yet define learned-routing-specific events, but this exploration strongly implies future event families like:

- `assignment_recommendation_generated`
- `assignment_recommendation_accepted`
- `assignment_recommendation_overridden`
- `assignment_auto_applied`
- `assignment_learning_policy_changed`

These are not locked yet, but the capability clearly needs a canonical audit extension rather than generic `settings_changed` or `trip_assigned` overload.

## D5 Override Learning

This capability is a natural consumer of override signals.

Examples:

- admin repeatedly rejects the recommended assignee for visa-heavy trips,
- one queue repeatedly needs manual rebalancing,
- certain suggestions are accepted unchanged for one trip class.

That data should feed policy suggestions, not silent auto-rewrites.

## Blind Comparison Arena

The arena exploration is also relevant here.

If Waypoint later evaluates two routing strategies blindly, the resulting preference and outcome data could become a higher-quality calibration source than raw assignment counts.

---

## Fairness And Human Factors

This is one of the highest-risk parts of the design.

The danger is not only bias against customers. It is also unfair or demoralizing treatment of operators.

The system should therefore preserve:

- explanation,
- recourse,
- bounded automation,
- and participation by owners/admins in changing policy.

Important principle:

- algorithms are better suited to **mechanical matching** than to **human-style evaluation**.

So Waypoint should be confident about:

- matching by specialization, availability, workload, queue fit.

And much more cautious about:

- inferring operator merit,
- punishing lower-volume operators,
- or letting opaque historical patterns harden into unfair allocation.

---

## What This Should Not Become

This should not become:

- a hidden worker leaderboard,
- a punitive algorithmic manager,
- a replacement for canonical routing slots,
- an excuse to keep generic audit events,
- or a justification for shipping learning before data quality is real.

It should also not block the simpler deterministic version.

For many agencies, the highest-value first step may simply be:

- explicit skills,
- explicit capacity,
- continuity-aware ranking,
- and transparent recommendations.

That alone would be materially better than today's state.

---

## Recommended Immediate Follow-On Artifacts

If this direction is accepted, the best next documents would be:

1. **Assignment Signal Taxonomy Spec** — canonical routing signals, allowed/forbidden features, cohort definitions, and minimum sample rules.
2. **People Skills + Capacity Profile Addendum** — what operator attributes must live in membership/profile data for routing to work.
3. **Assignments Settings Addendum** — exact `/settings/assignments` controls for mode, queues, continuity, and learning posture.
4. **Routing Audit Addendum** — canonical learned-routing event names and diff payloads.
5. **Metrics Readiness Audit** — which current team/workload signals are real enough to trust and which are still simulated placeholders.

---

## Final Recommendation

The best approach is:

- start with explicit skill and capacity routing,
- keep continuity as a first-class routing signal,
- use learning to calibrate recommendations rather than replace governance,
- ship ranked suggestions before auto-apply,
- and treat auto-assignment as a governed assignment-policy surface, not a hidden performance engine.

That preserves the roadmap's core values:

- explicit roles,
- explicit routing ownership,
- explicit settings governance,
- explicit audit history,
- and adaptive learning that proposes or tunes behavior without erasing human control.
