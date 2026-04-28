# Feature Flags & Configuration — Governance & Operations

> Research document for flag governance, operational patterns, and organizational practices.

---

## Key Questions

1. **How do we prevent flag sprawl and ensure timely cleanup?**
2. **What's the RBAC model for flag management?**
3. **How do we audit flag changes and correlate them with incidents?**
4. **What's the disaster recovery plan for the config service?**
5. **How do we train teams on responsible flag usage?**

---

## Research Areas

### Flag Governance Framework

```typescript
interface FlagGovernance {
  policies: FlagPolicy[];
  rbac: FlagRBAC;
  lifecycle: LifecyclePolicy;
  audit: AuditConfig;
  alerts: GovernanceAlert[];
}

interface FlagPolicy {
  policyId: string;
  name: string;
  description: string;
  rule: PolicyRule;
  enforcement: 'blocking' | 'warning' | 'advisory';
}

type PolicyRule =
  | { type: 'max_lifetime'; flagType: FlagType; maxDays: number }
  | { type: 'require_expiry'; flagType: FlagType[] }
  | { type: 'require_owner'; flagType: FlagType[] }
  | { type: 'require_description'; minLength: number }
  | { type: 'naming_convention'; pattern: string }
  | { type: 'max_active_flags'; limit: number; scope: 'team' | 'global' }
  | { type: 'approval_required'; flagType: FlagType[]; minApprovers: number }
  | { type: 'no_eval_in_critical_path'; flagKeys: string[] };

// Example policies:
// Release flags must have expiry ≤ 30 days
// Experiment flags must have hypothesis and defined metrics
// Ops flags must have an owner and rollback plan
// No more than 200 active flags globally
// Flags evaluated in booking flow must have < 5ms evaluation time
// All production flag toggles require approval for high-impact flags
```

### RBAC Model

```typescript
interface FlagRBAC {
  roles: FlagRole[];
  permissions: FlagPermission[];
  assignments: RoleAssignment[];
}

type FlagRole =
  | 'flag_admin'            // Full control: create, toggle, delete, manage access
  | 'flag_manager'          // Create, toggle owned flags, request changes
  | 'flag_viewer'           // View flag state and history
  | 'flag_auditor';         // View audit logs, compliance reports

type FlagPermission =
  | 'flag:create'
  | 'flag:read'
  | 'flag:update'
  | 'flag:toggle'
  | 'flag:delete'
  | 'flag:retire'
  | 'flag:override_env'     // Override in specific environment
  | 'flag:manage_access'
  | 'flag:view_audit'
  | 'flag:export_data';

interface RoleAssignment {
  role: FlagRole;
  scope: FlagScope;
  assignee: string;
  assignedBy: string;
}

type FlagScope =
  | { type: 'global' }
  | { type: 'domain'; domain: string }     // e.g., 'booking', 'pricing'
  | { type: 'flag'; flagKeys: string[] }
  | { type: 'environment'; environments: string[] };

// RBAC matrix:
// flag_admin   → All permissions, global scope
// flag_manager → Create/toggle/read in owned domain
// flag_viewer  → Read-only across all domains
// flag_auditor → View audit logs, no toggle ability
```

### Operational Patterns

```typescript
interface FlagOperations {
  killSwitches: KillSwitch[];
  maintenanceMode: MaintenanceConfig;
  deploymentIntegration: DeploymentConfig;
  incidentPlaybooks: IncidentPlaybook[];
}

interface KillSwitch {
  flagKey: string;
  description: string;
  impactIfDisabled: string;
  owner: string;
  lastTestedAt: Date;
  testSchedule: string;
}

// Standard kill switches for travel platform:
// booking.hotel.enabled → Disable hotel booking (supplier issue)
// booking.flight.enabled → Disable flight booking (GDS issue)
// payment.processing.enabled → Disable payment processing
// spine.run.enabled → Disable spine processing (manual fallback)
// notification.whatsapp.enabled → Disable WhatsApp (API issue)
// pricing.dynamic.enabled → Fallback to static pricing
// search.external.enabled → Fallback to cached results

interface MaintenanceConfig {
  maintenanceFlag: string;          // Global maintenance mode flag
  message: string;
  affectedFeatures: string[];
  estimatedDuration: string;
  notificationLeadTime: string;
}

// Maintenance mode levels:
// Level 0: Normal operation
// Level 1: Read-only (can view but not modify)
// Level 2: Degraded (core features only: view existing bookings)
// Level 3: Maintenance (system unavailable, show maintenance page)
```

### Audit & Compliance

```typescript
interface FlagAuditConfig {
  auditAllChanges: boolean;
  retentionDays: number;
  correlateWithMetrics: boolean;
  alertOnAnomalousChanges: boolean;
}

interface FlagAuditEntry {
  timestamp: Date;
  action: FlagAuditAction;
  flagKey: string;
  actor: string;
  previousState: unknown;
  newState: unknown;
  reason: string;
  correlationId: string;            // Link to incident or change request
  environment: string;
}

type FlagAuditAction =
  | 'created'
  | 'updated'
  | 'toggled'
  | 'deleted'
  | 'retired'
  | 'overridden'
  | 'approval_granted'
  | 'approval_rejected';

// Compliance requirements:
// 1. All flag changes in production are audited
// 2. Flag changes correlate with metric changes (did error rate spike?)
// 3. Experiment decisions documented with statistical evidence
// 4. Pricing flag changes tracked for regulatory compliance
// 5. Flag state can be reconstructed for any point in time (time-travel debug)

// Incident correlation:
// When an incident is declared:
// 1. Query all flag changes in last 24 hours
// 2. Cross-reference with metric anomalies
// 3. Flag changes shown in incident timeline
// 4. One-click rollback for suspect changes
```

---

## Open Problems

1. **Flag as architecture** — When flags become permanent ("this flag has been active for 2 years"), they're not flags — they're architecture. Need a path from flag to permanent feature.

2. **Cross-team flag ownership** — A pricing flag affects agents, customers, and accounting. Who owns it? Need clear ownership with cross-team notification on changes.

3. **Flag testing in CI/CD** — Every PR should be tested against both states of relevant flags. CI pipeline needs flag-aware test fixtures.

4. **Regulatory flag requirements** — Some features must be enabled/disabled by jurisdiction (e.g., dynamic pricing regulated in some markets). Need geo-aware flags with legal compliance.

5. **Flag migration** — When migrating from one flag system to another, how do you maintain continuity? Need migration playbooks with zero downtime.

---

## Next Steps

- [ ] Design flag governance policy document with team input
- [ ] Create RBAC matrix for flag management roles
- [ ] Define standard kill switches for critical platform features
- [ ] Build flag change audit dashboard with metric correlation
- [ ] Create flag lifecycle training material for engineering teams
