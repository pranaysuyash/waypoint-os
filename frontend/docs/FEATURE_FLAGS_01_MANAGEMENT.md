# Feature Flags & Configuration — Management & Architecture

> Research document for feature flag systems, flag lifecycle, and configuration management.

---

## Key Questions

1. **What's the feature flag lifecycle from creation to retirement?**
2. **How do we manage flags across environments (dev, staging, production)?**
3. **What's the flag evaluation model — client-side, server-side, or edge?**
4. **How do we handle flag dependencies and mutual exclusivity?**
5. **What's the governance model — who can create, toggle, and retire flags?**

---

## Research Areas

### Flag Taxonomy

```typescript
type FlagType =
  | 'release'              // Gradual rollout of new features
  | 'experiment'           // A/B test with metrics tracking
  | 'ops'                  // Operational toggle (kill switch, circuit breaker)
  | 'permission'           // Entitlement / entitlement gating
  | 'config'               // Dynamic configuration value
  | 'migration'            // Data/schema migration toggle
  | 'schedule';            // Time-bounded activation

interface FeatureFlag {
  flagId: string;
  key: string;                      // e.g., "booking.hotel.new_search_ui"
  name: string;
  description: string;
  type: FlagType;
  owner: string;                    // Team or individual
  createdAt: Date;
  expiresAt?: Date;                 // Mandatory for release/experiment flags
  status: FlagStatus;
  targeting: TargetingRule[];
  evaluation: EvaluationConfig;
  dependencies: FlagDependency[];
}

type FlagStatus =
  | 'draft'
  | 'active'
  | 'paused'
  | 'retired'
  | 'stale';                        // Active past expiry, needs cleanup

// Flag naming convention:
// <domain>.<feature>.<component>
// e.g., booking.hotel.new_search_ui
//       pricing.dynamic.margin_boost
//       notification.whatsapp.business_api
//       spine.run.async_pipeline
```

### Targeting Rules

```typescript
interface TargetingRule {
  ruleId: string;
  description: string;
  priority: number;                 // Lower = evaluated first
  conditions: TargetingCondition[];
  allocation: AllocationStrategy;
}

interface TargetingCondition {
  attribute: string;                // User attribute or context
  operator: 'eq' | 'neq' | 'in' | 'not_in' | 'gt' | 'lt' | 'contains' | 'regex' | 'segment';
  values: string[] | number[];
}

type AllocationStrategy =
  | { type: 'boolean'; value: boolean }
  | { type: 'percentage'; percentage: number; salt?: string }
  | { type: 'variant'; variants: VariantAllocation[] }
  | { type: 'scheduled'; activateAt: Date; deactivateAt?: Date }
  | { type: 'gradual'; startAt: Date; endAt: Date; startPct: number; endPct: number };

interface VariantAllocation {
  variantName: string;
  percentage: number;
  payload?: unknown;                // Variant-specific config
}

// Targeting examples:
// 1. Internal testing: agent.role IN ['admin', 'qa'] → true
// 2. Gradual rollout: booking.created_at > 2026-04-01 → 25% true
// 3. Geography: customer.country IN ['IN'] → true (India-first launch)
// 4. Segment: customer.segment = 'enterprise' → variant 'premium_v2'
// 5. Kill switch: always → false (ops flag to disable feature)
```

### Flag Dependencies

```typescript
interface FlagDependency {
  dependsOnFlagKey: string;
  condition: 'enabled' | 'disabled' | 'variant';
  variantValue?: string;
}

// Dependency examples:
// booking.hotel.new_search_ui requires booking.hotel.api_v2 = enabled
// pricing.dynamic.enabled requires pricing.engine.v2 = enabled
// notification.whatsapp.business_api requires notification.whatsapp.consent = enabled

// Circular dependency detection:
// Flag A → Flag B → Flag C → Flag A = ERROR, reject at creation time

// Stale flag detection:
// Release flag active > 30 days → Alert owner
// Experiment flag active > 60 days → Alert owner
// Ops flag with no toggle in 90 days → Suggest retirement
```

### Environment Management

```typescript
interface EnvironmentConfig {
  environment: 'development' | 'staging' | 'production';
  flagOverrides: FlagOverride[];
  defaultRules: TargetingRule[];
  evaluationMode: 'local' | 'remote' | 'hybrid';
}

interface FlagOverride {
  flagKey: string;
  environment: string;
  value: boolean | string | number;
  reason: string;                   // Why this override exists
  expiresAt?: Date;
  createdBy: string;
}

// Environment strategies:
// Development → All flags local, hot-reload on file change
// Staging → Mirrors production with test overrides
// Production → Remote evaluation with local cache fallback

// Flag promotion workflow:
// Dev (create & test) → Staging (validate) → Production (gradual rollout)
// Each environment can have different targeting rules
```

---

## Open Problems

1. **Flag sprawl** — Teams create flags but never clean them up. Need automated stale flag detection and retirement workflow.

2. **Evaluation latency** — Remote flag evaluation adds latency to every request. Need local caching with configurable TTL and real-time updates via SSE/WebSocket.

3. **Flag consistency** — A flag evaluated on the server may differ from the client cache. Need strategies for cache invalidation and consistency.

4. **Testing flag combinations** — With 50+ flags, testing all combinations is impossible. Need combinatorial testing strategies and flag-aware test fixtures.

5. **Flag permissions** — Who can toggle what? A misconfigured ops flag can take down production. Need role-based access control for flag management.

---

## Next Steps

- [ ] Evaluate feature flag platforms (LaunchDarkly, Unleash, Flagsmith, custom)
- [ ] Design flag naming convention and taxonomy for travel platform
- [ ] Create flag lifecycle management workflow
- [ ] Design stale flag detection and automated cleanup
- [ ] Study flag evaluation performance at scale
