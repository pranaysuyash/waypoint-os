# Workflow Automation — Process Orchestration & State Machines

> Research document for orchestrating multi-step workflows and managing process state.

---

## Key Questions

1. **What multi-step processes need orchestration (booking pipeline, onboarding, payment collection)?**
2. **What's the right orchestration model — state machines, BPMN, or custom DAGs?**
3. **How do we handle long-running processes that span days or weeks?**
4. **What's the checkpoint and recovery strategy for failed process steps?**
5. **How do we visualize process state for agents and managers?**

---

## Research Areas

### Process Definitions

```typescript
interface ProcessDefinition {
  processId: string;
  name: string;
  version: number;
  states: ProcessState[];
  transitions: ProcessTransition[];
  initialState: string;
  terminalStates: string[];
  timeout: string;              // Max duration for the entire process
}

interface ProcessState {
  stateId: string;
  name: string;
  type: 'start' | 'normal' | 'decision' | 'parallel' | 'end' | 'error';
  onEnter?: ActionRef[];
  onExit?: ActionRef[];
  timeout?: string;
  timeoutTransition?: string;   // State to transition to on timeout
}

interface ProcessTransition {
  transitionId: string;
  from: string;
  to: string;
  event: string;
  guard?: RuleCondition;        // Only transition if condition met
  actions?: ActionRef[];
}

// Example: Booking Pipeline Process
// START → INTAKE → PROCESSING → PRICING → QUOTE_REVIEW → QUOTE_SENT
//       ↘ FAILED                                       ↘ BOOKING_IN_PROGRESS
//                                                      ↘ CONFIRMED → DOCUMENTATION → COMPLETE
```

### Process Instance Execution

```typescript
interface ProcessInstance {
  instanceId: string;
  processId: string;
  processVersion: number;
  currentState: string;
  context: ProcessContext;
  history: ProcessHistoryEntry[];
  startedAt: Date;
  completedAt?: Date;
  status: 'running' | 'suspended' | 'completed' | 'failed' | 'timed_out';
}

interface ProcessContext {
  tripId: string;
  variables: Record<string, unknown>;
  checkpoints: Checkpoint[];
}

interface ProcessHistoryEntry {
  timestamp: Date;
  fromState: string;
  toState: string;
  event: string;
  actor: string;
  actionsExecuted: string[];
  durationMs: number;
}

interface Checkpoint {
  stateName: string;
  savedAt: Date;
  contextSnapshot: Record<string, unknown>;
  // Enables resuming from this point if process fails
}
```

### Key Processes to Orchestrate

| Process | Steps | Duration | Complexity |
|---------|-------|----------|------------|
| Trip booking pipeline | 8-12 steps | Hours to days | High |
| Customer onboarding | 6-8 steps | Days | Medium |
| Supplier onboarding | 10-15 steps | Weeks | High |
| Payment collection | 5-7 steps | Days | Medium |
| Refund processing | 6-8 steps | Days | Medium |
| Insurance claim | 8-12 steps | Weeks | High |
| Contract lifecycle | 10-15 steps | Weeks | High |
| Agent certification | 5-8 steps | Months | Medium |

### Parallel Execution & Fork/Join

```typescript
interface ParallelGateway {
  type: 'fork' | 'join';
  branches: string[];
  joinCondition: 'all' | 'any' | 'n_of';   // Wait for all, any, or N branches
  n?: number;
}

// Example: After booking confirmation, run in parallel:
// Branch A: Generate voucher documents
// Branch B: Send confirmation email
// Branch C: Update customer CRM profile
// Branch D: Process commission calculation
// Join: Wait for all 4 branches before moving to DOCUMENTATION state
```

---

## Open Problems

1. **Long-running process persistence** — A booking pipeline may run for days. Process state must survive server restarts. Need durable state storage.

2. **Process migration** — When a process definition is updated (v2), what happens to running instances on v1? Need version migration strategy.

3. **Compensation transactions** — If step 4 of 6 fails, steps 1-3 may have had side effects (email sent, payment taken). Need compensation (undo) actions.

4. **Human-in-the-loop** — Many steps require human approval or action. The process must pause and resume, potentially days later.

5. **Process observability** — Managers need to see where 500 active bookings are in the pipeline. Need aggregated process state visualization.

---

## Next Steps

- [ ] Evaluate workflow orchestration engines (Temporal, Camunda, Inngest)
- [ ] Map the trip booking pipeline as a process definition
- [ ] Design checkpoint and recovery strategy
- [ ] Study compensation transaction patterns (Saga pattern)
- [ ] Design process state visualization dashboard
