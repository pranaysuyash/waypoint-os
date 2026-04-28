# Workflow Automation — Monitoring & Alerting

> Research document for workflow monitoring, SLA tracking, and operational alerting.

---

## Key Questions

1. **What workflow metrics need real-time monitoring?**
2. **How do we detect and alert on stuck or slow processes?**
3. **What SLA targets apply to different workflow stages?**
4. **How do we build operational dashboards for workflow health?**
5. **What's the incident response workflow for process failures?**

---

## Research Areas

### Workflow Metrics

```typescript
interface WorkflowMetrics {
  processId: string;
  period: DateRange;
  // Volume metrics
  instancesStarted: number;
  instancesCompleted: number;
  instancesFailed: number;
  instancesActive: number;
  // Time metrics
  averageDuration: number;
  p50Duration: number;
  p95Duration: number;
  p99Duration: number;
  // Stage metrics
  stageMetrics: StageMetric[];
  // SLA metrics
  slaBreaches: number;
  slaBreachPercent: number;
  // Error metrics
  errorRate: number;
  errorTypes: ErrorBreakdown[];
  retryCount: number;
}

interface StageMetric {
  stageName: string;
  averageDuration: number;
  p95Duration: number;
  waitTime: number;              // Time waiting for human action
  errorRate: number;
  throughput: number;            // Instances per hour
}
```

### SLA Configuration

```typescript
interface WorkflowSLA {
  processId: string;
  stages: StageSLA[];
  overall: OverallSLA;
}

interface StageSLA {
  stageName: string;
  targetDuration: string;        // Max time in this stage
  warningAt: string;             // Alert before SLA breach
  escalationAt: string;          // Escalate if breached
  autoAction?: string;           // Auto-escalate or auto-resolve
}

// Example SLA for booking pipeline:
// INTAKE: 30 min target, 20 min warning, 45 min escalation
// PROCESSING: 5 min target, 3 min warning, 10 min escalation
// PRICING: 2 hr target, 1.5 hr warning, 3 hr escalation
// QUOTE_REVIEW: 4 hr target, 3 hr warning, 6 hr escalation
// BOOKING: 24 hr target, 18 hr warning, 36 hr escalation
```

### Operational Dashboard

```typescript
interface WorkflowDashboard {
  // Active processes
  activeProcesses: {
    byStage: Record<string, number>;
    byStatus: Record<string, number>;
    atRisk: ProcessAlert[];        // Approaching SLA breach
    breached: ProcessAlert[];       // SLA already breached
    stuck: ProcessAlert[];          // No activity for >threshold
  };
  // Throughput
  throughputChart: TimeSeriesData;
  // Bottlenecks
  bottlenecks: Bottleneck[];
  // Recent failures
  recentFailures: FailureSummary[];
}

interface ProcessAlert {
  instanceId: string;
  processName: string;
  currentStage: string;
  timeInStage: string;
  slaTarget: string;
  timeRemaining: string;
  assignee: string;
  severity: 'warning' | 'critical';
  suggestedAction: string;
}

interface Bottleneck {
  stageName: string;
  averageWaitTime: number;
  queuedInstances: number;
  capacity: number;
  utilization: number;
  recommendation: string;
}
```

### Incident Response

```typescript
interface ProcessIncident {
  incidentId: string;
  processInstanceId: string;
  type: 'stuck' | 'failed' | 'sla_breach' | 'error_spike';
  severity: 'low' | 'medium' | 'high' | 'critical';
  detectedAt: Date;
  description: string;
  affectedEntities: string[];
  response: IncidentResponse;
}

interface IncidentResponse {
  actions: ResponseAction[];
  status: 'detected' | 'investigating' | 'mitigating' | 'resolved';
  assignee: string;
  timeline: ResponseTimelineEntry[];
}

// Automated response patterns:
// Stuck process → Alert assignee → After 30 min, alert manager → Auto-retry
// Failed process → Alert ops team → Create incident ticket → Auto-retry with backoff
// SLA breach → Alert agent + manager → Offer expedited alternative
// Error spike → Alert engineering → Enable circuit breaker → Fallback mode
```

---

## Open Problems

1. **Alert noise** — Too many SLA warnings desensitize the team. Need smart alerting that prioritizes truly critical situations.

2. **Bottleneck identification** — A stage appears slow, but the real bottleneck is upstream (decisions pile up). Need causal analysis, not just symptom detection.

3. **Correlation across processes** — A supplier API outage affects 50 active booking processes. Need to correlate individual process failures to systemic issues.

4. **SLA target calibration** — Setting SLAs too tight creates constant alerts; too loose means poor service. Need data-driven SLA target setting.

5. **Historical analysis** — "What was the average booking pipeline time last December?" Requires long-term metric retention and trending.

---

## Next Steps

- [ ] Design workflow monitoring metrics pipeline
- [ ] Create SLA configuration for key processes
- [ ] Build operational dashboard wireframes
- [ ] Design alert routing and escalation rules
- [ ] Study workflow monitoring tools (Temporal UI, Camunda Cockpit)
