# Feature Flags & Configuration — Dynamic Configuration

> Research document for runtime configuration, remote config, and configuration management.

---

## Key Questions

1. **What configuration should be dynamic vs. static (deployed with code)?**
2. **How do we manage configuration across microservices without coupling?**
3. **What's the configuration change workflow — who approves, who applies?**
4. **How do we handle configuration rollbacks and versioning?**
5. **What's the configuration delivery mechanism — push, pull, or hybrid?**

---

## Research Areas

### Configuration Taxonomy

```typescript
type ConfigCategory =
  | 'feature_toggle'         // Boolean flags (feature on/off)
  | 'business_rule'          // Pricing rules, commission rates
  | 'threshold'              // Rate limits, timeouts, batch sizes
  | 'ui_config'              // Layout, theme, component variants
  | 'integration'            // API keys, endpoints, credentials
  | 'schedule'               // Maintenance windows, blackout dates
  | 'content'                // Promotional text, banner messages
  | 'algorithm'              // Weights, scoring parameters
  | 'compliance';            // Regulatory thresholds, consent versions

interface DynamicConfig {
  configId: string;
  key: string;                      // Namespaced: "pricing.hotel.margin_default"
  category: ConfigCategory;
  valueType: 'string' | 'number' | 'boolean' | 'json' | 'array';
  value: unknown;
  defaultValue: unknown;            // Fallback if config service unavailable
  description: string;
  environment: string;
  version: number;
  updatedAt: Date;
  updatedBy: string;
  changeReason: string;
  auditTrail: ConfigAuditEntry[];
}

// What should be dynamic vs. static:
// DYNAMIC (change without deploy):
//   - Feature flags, A/B test allocations
//   - Pricing margins, commission rates
//   - API timeouts, retry limits
//   - Promotional banners, seasonal messages
//   - Supplier API credentials (rotation)
//   - Maintenance mode toggle
//
// STATIC (deployed with code):
//   - Database schema, table names
//   - API route definitions
//   - Authentication algorithms
//   - Encryption key references
//   - Required environment variables
```

### Configuration Management

```typescript
interface ConfigChangeRequest {
  requestId: string;
  configKey: string;
  currentValue: unknown;
  proposedValue: unknown;
  reason: string;
  requestedBy: string;
  impactAssessment: ImpactAssessment;
  approvals: ConfigApproval[];
  status: 'pending' | 'approved' | 'rejected' | 'applied' | 'rolled_back';
}

interface ImpactAssessment {
  affectedServices: string[];
  affectedFeatures: string[];
  estimatedUsers: number;
  rollbackPlan: string;
  monitoringPlan: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
}

interface ConfigApproval {
  approver: string;
  approved: boolean;
  comment?: string;
  timestamp: Date;
}

// Approval matrix:
// Low risk (UI text, banner) → Auto-approve for config owners
// Medium risk (thresholds, timeouts) → 1 approval from tech lead
// High risk (pricing, commission) → 2 approvals (tech lead + business)
// Critical (credentials, compliance) → 3 approvals + change window

interface ConfigAuditEntry {
  version: number;
  previousValue: unknown;
  newValue: unknown;
  changedBy: string;
  changedAt: Date;
  changeReason: string;
  changeRequestId?: string;
  rollbackSupported: boolean;
}
```

### Delivery Mechanisms

```typescript
interface ConfigDeliveryConfig {
  method: DeliveryMethod;
  refreshInterval: number;          // Seconds
  fallbackStrategy: FallbackStrategy;
  changeNotification: ChangeNotification;
}

type DeliveryMethod =
  | { type: 'pull'; url: string; pollingIntervalMs: number }
  | { type: 'push'; websocketUrl: string; reconnectMs: number }
  | { type: 'hybrid'; pullIntervalMs: number; pushUrl: string }
  | { type: 'file'; path: string; watchIntervalMs: number }
  | { type: 'edge'; cdnUrl: string; staleWhileRevalidate: boolean };

// Delivery strategy by consumer:
// Frontend (browser) → Edge/CDN with SSE for updates, localStorage cache
// Next.js API routes → Pull with 30s cache + push for critical changes
// Python spine → Pull with 60s cache (less dynamic needs)
// Background workers → Pull on startup + periodic refresh
// External integrations → File-based config for supplier-specific settings

// Cache hierarchy:
// 1. In-memory (fastest, stale for refreshInterval)
// 2. Local storage / file cache (survives restart)
// 3. Remote config service (source of truth)
```

### Configuration Validation

```typescript
interface ConfigValidation {
  configKey: string;
  validations: ValidationRule[];
}

interface ValidationRule {
  type: ValidationType;
  parameters: Record<string, unknown>;
  errorMessage: string;
}

type ValidationType =
  | 'type_check'            // Value must be number/string/boolean
  | 'range'                 // Number must be between min and max
  | 'enum'                  // Value must be one of allowed values
  | 'regex'                 // String must match pattern
  | 'json_schema'           // JSON must conform to schema
  | 'dependency'            // Value must be consistent with another config
  | 'custom';               // Custom validation function

// Validation examples:
// pricing.hotel.margin_default: type_check=number, range=[0.05, 0.50]
// booking.cancellation.policy: enum=['flexible', 'moderate', 'strict']
// api.hotel.timeout_ms: type_check=number, range=[1000, 30000]
// notification.whatsapp.template: regex=^[a-z_]+$, max_length=50
// pricing.dynamic.enabled: dependency → requires pricing.engine.version = 'v2'

// Pre-change validation:
// 1. Schema validation (type, range, enum)
// 2. Dependency check (all dependencies satisfied?)
// 3. Impact simulation (what features change?)
// 4. Gradual application (can we apply to 1% first?)
```

---

## Open Problems

1. **Config drift across services** — Each service caches config independently. During a change, some services have old values, some new. Need coordination for breaking changes.

2. **Secret management overlap** — API keys and credentials are both "configuration" and "secrets." Need clear boundary between config service and secret manager (Vault, AWS Secrets Manager).

3. **Config change blast radius** — Changing a pricing margin affects all bookings. Need canary-based config changes (apply to 1% of traffic first).

4. **Multi-environment consistency** — Staging should mirror production, but with test values. Need environment-aware config with inheritance.

5. **Config observability** — When a bug occurs, it's hard to know if a config change caused it. Need config change correlation with metrics and logs.

---

## Next Steps

- [ ] Catalog all static and dynamic configuration in the platform
- [ ] Design configuration schema and validation framework
- [ ] Build config change approval workflow
- [ ] Design config delivery mechanism with cache hierarchy
- [ ] Study configuration management tools (Consul, etcd, AWS AppConfig, LaunchDarkly)
