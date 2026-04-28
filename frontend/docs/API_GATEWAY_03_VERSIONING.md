# API Gateway — Versioning Strategy

> Research document for API versioning, backward compatibility, and migration patterns.

---

## Key Questions

1. **What versioning strategy fits our architecture — URL-based, header-based, or content negotiation?**
2. **How long do we support old API versions?**
3. **How do we communicate breaking changes to API consumers?**
4. **What's the migration workflow from v1 to v2 for internal consumers?**
5. **How do we test version compatibility?**

---

## Research Areas

### Versioning Approaches

```typescript
type VersioningStrategy =
  | { type: 'url_path'; example: '/api/v2/trips' }
  | { type: 'header'; header: 'X-API-Version'; example: '2' }
  | { type: 'content_type'; example: 'application/vnd.agency.v2+json' }
  | { type: 'query_param'; param: 'version'; example: 'v=2' };

// Recommended: URL-based versioning
// Rationale: Simplest for consumers, clearest in logs, easy to route
// Drawback: URL proliferation, but manageable with 2-3 active versions
```

### Version Lifecycle

```typescript
interface VersionLifecycle {
  version: string;
  status: VersionStatus;
  releasedAt: Date;
  sunsetDate?: Date;              // No new features
  deprecatedAt?: Date;            // Consumers should migrate
  retiredAt?: Date;               // No longer served
}

type VersionStatus =
  | 'current'             // Active development
  | 'stable'              // Bug fixes only
  | 'sunset'              // No changes, still served
  | 'deprecated'          // Still served, consumers warned
  | 'retired';            // No longer served

// Lifecycle policy:
// current → stable (when next version released)
// stable → sunset (6 months after next version)
// sunset → deprecated (3 months after sunset)
// deprecated → retired (3 months after deprecated)
// Total support window: ~12 months per version
```

### Breaking Change Classification

```typescript
type ChangeType =
  // Breaking changes (require new version)
  | 'field_removed'               // Response field deleted
  | 'field_renamed'               // Field name changed
  | 'type_changed'                // Field type changed (string → number)
  | 'endpoint_removed'            // API endpoint deleted
  | 'endpoint_renamed'            // URL path changed
  | 'auth_changed'                // Authentication method changed
  | 'error_format_changed'        // Error response structure changed
  // Non-breaking changes (same version)
  | 'field_added'                 // New response field
  | 'optional_param_added'        // New optional query param
  | 'performance_improved'        // Faster response
  | 'bug_fixed';                  // Response matches documented behavior

interface ChangeLog {
  version: string;
  releaseDate: Date;
  changes: ChangeEntry[];
  migrationGuide?: string;
}

interface ChangeEntry {
  type: ChangeType;
  breaking: boolean;
  description: string;
  affectedEndpoints: string[];
  migrationNotes: string;
}
```

### Consumer Management

```typescript
interface APIConsumer {
  consumerId: string;
  name: string;
  type: 'frontend' | 'mobile' | 'partner' | 'internal';
  currentVersion: string;
  contactEmail: string;
  deprecationNoticesSent: number;
  migrationDeadline: Date;
}

// Deprecation communication plan:
// Day 0: Version deprecated, changelog published
// Day 7: Email to all consumers
// Day 30: Second email with migration guide
// Day 60: Warning headers in API responses
// Day 75: Final email, 15-day deadline
// Day 90: Version retired, 410 Gone response
```

---

## Open Problems

1. **Internal vs. external versioning** — The frontend and mobile app are internal consumers. Do they need the same versioning discipline as external partners?

2. **Database schema coupling** — API v2 may need database schema changes. Running v1 and v2 simultaneously requires backward-compatible schemas.

3. **Testing matrix explosion** — Each new version doubles the test matrix. v1 + v2 + v3 means testing every feature against 3 versions.

4. **Consumer tracking** — We may not know all consumers of our API (partner integrations, scripts). How to notify unknown consumers?

5. **Feature flags vs. versioning** — Some changes can be delivered via feature flags without a new version. When to use each approach?

---

## Next Steps

- [ ] Document current API endpoints and consumers
- [ ] Design version lifecycle policy
- [ ] Create breaking change checklist for PR reviews
- [ ] Set up API changelog (keep-a-changelog format)
- [ ] Design deprecation notification system
