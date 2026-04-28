# Platform Plugin & Extension System — Architecture

> Research document for plugin lifecycle management, sandboxed execution, permission model, and extension API surface design.

---

## Key Questions

1. **How do we design a plugin architecture that is secure and extensible?**
2. **What plugin lifecycle stages are needed (install, activate, configure, deactivate)?**
3. **How do we sandbox third-party plugin code safely?**
4. **What permission model controls plugin access to platform data?**
5. **What API surface do we expose to plugin developers?**

---

## Research Areas

### Plugin Architecture

```typescript
interface PluginArchitecture {
  registry: PluginRegistry;
  runtime: PluginRuntime;
  sandbox: PluginSandbox;
  permissions: PermissionModel;
  lifecycle: PluginLifecycle;
  api: PluginAPI;
}

interface PluginRegistry {
  plugins: PluginManifest[];
  categories: PluginCategory[];
  review: ReviewProcess;
  distribution: DistributionConfig;
}

interface PluginManifest {
  id: string;                          // "com.waypoint.whatsapp-integration"
  name: string;                        // "WhatsApp Business Integration"
  version: string;                     // "1.2.3" (semver)
  description: string;
  author: PluginAuthor;
  category: PluginCategory;
  permissions: PluginPermission[];
  dependencies: PluginDependency[];
  hooks: PluginHook[];
  configuration: PluginConfig[];
  compatibility: CompatibilitySpec;
  pricing: PluginPricing;
}

type PluginCategory =
  | 'channel_integration'              // WhatsApp, Telegram, LINE
  | 'payment_gateway'                  // Razorpay, Stripe, PayU
  | 'supplier_connect'                 // GDS, bedbank, DMC connectors
  | 'analytics'                        // Custom dashboards, reports
  | 'communication'                    // Email, SMS, notification
  | 'workflow_automation'              // Custom triggers, actions
  | 'document_generation'              // Custom templates, formats
  | 'crm'                              // Customer relationship tools
  | 'accounting'                       // Tally, Zoho, QuickBooks sync
  | 'ai_assistant'                     // AI-powered tools
  | 'marketing'                        // Campaign, SEO, social media
  | 'compliance'                       // GST, TDS, regulatory
  | 'accessibility'                    // Screen reader, translation
  | 'custom_field'                     // Custom data fields, forms
  | 'ui_extension';                    // Panel extensions, widgets

// Example plugins:
// 1. WhatsApp Business Integration: Send itineraries via WhatsApp
//    Category: channel_integration
//    Permissions: messaging.send, customer.read, trip.read
//    Hooks: trip.confirmed, itinerary.generated, payment.received
//
// 2. Tally Accounting Sync: Auto-sync invoices to Tally
//    Category: accounting
//    Permissions: invoice.read, invoice.write, customer.read
//    Hooks: invoice.created, payment.received, credit_note.issued
//
// 3. Custom Packing List Generator: Generate destination-specific packing lists
//    Category: document_generation
//    Permissions: trip.read, destination.read
//    Hooks: trip.confirmed, destination.viewed
//
// 4. AI Itinerary Enhancer: Suggest improvements to agent-built itineraries
//    Category: ai_assistant
//    Permissions: trip.read, trip.write, destination.read, activity.read
//    Hooks: itinerary.drafted, itinerary.shared
//
// 5. Google Calendar Sync: Add trip dates to agent's Google Calendar
//    Category: workflow_automation
//    Permissions: trip.read, agent.calendar
//    Hooks: trip.confirmed, trip.date_changed, trip.cancelled

interface PluginAuthor {
  name: string;
  email: string;
  website?: string;
  verified: boolean;                   // Identity verified
  rating: number;                      // Community rating
  plugins: number;                     // Number of published plugins
}

interface PluginDependency {
  pluginId: string;                    // Required plugin
  versionRange: string;                // "^1.0.0"
  optional: boolean;
}

interface CompatibilitySpec {
  platformVersion: string;             // ">=2.0.0"
  browserSupport?: string[];           // ["chrome >= 90", "safari >= 14"]
  nodeVersion?: string;                // For server-side plugins
  regions?: string[];                  // ["IN", "SG", "AE"] (if region-specific)
}
```

### Plugin Lifecycle

```typescript
interface PluginLifecycle {
  states: PluginState[];
  transitions: StateTransition[];
  events: LifecycleEvent[];
}

type PluginState =
  | 'uploaded'                         // Plugin code uploaded to registry
  | 'under_review'                     // Under security and quality review
  | 'approved'                         // Review passed, available in marketplace
  | 'rejected'                         // Review failed, feedback provided
  | 'installed'                        // Installed by agency (not active)
  | 'activating'                       // Running activation hook
  | 'active'                           // Running and processing events
  | 'deactivating'                     // Running deactivation hook
  | 'inactive'                         // Installed but not active
  | 'error'                            // Runtime error, auto-deactivated
  | 'updating'                         // Updating to new version
  | 'deprecated'                       // Author marked as deprecated
  | 'removed';                         // Removed from system

// Plugin lifecycle flow:
// 1. UPLOAD: Developer uploads plugin package to registry
//    - Package format: ZIP with manifest.json, source code, assets
//    - Auto-validation: manifest schema, file size, naming conventions
//
// 2. REVIEW: Automated + manual review
//    - Static analysis: Code scanning for security vulnerabilities
//    - Permission audit: Are requested permissions justified?
//    - Performance check: Bundle size, memory usage estimate
//    - Manual review: For sensitive categories (payment, data access)
//    - Timeline: 3-5 business days for standard, 7-10 for sensitive
//
// 3. INSTALL: Agency admin installs plugin
//    - Permission grant: Admin reviews and approves permissions
//    - Configuration: Required settings filled in (API keys, etc.)
//    - Dependency check: All required plugins installed?
//    - Database migrations: Plugin-specific tables/columns created
//
// 4. ACTIVATE: Plugin starts running
//    - Activation hook: Plugin.onActivate(config)
//    - Hook registration: Plugin registers for event hooks
//    - API routes: Plugin routes become available
//    - UI extensions: Plugin panels/widgets appear in workbench
//
// 5. RUN: Plugin processes events
//    - Event hooks fire on platform events (trip.confirmed, etc.)
//    - API endpoints handle plugin-specific requests
//    - UI extensions render in designated slots
//    - Background tasks run on schedule
//
// 6. DEACTIVATE: Admin deactivates plugin
//    - Deactivation hook: Plugin.onDeactivate()
//    - Hook unregistration: Stop receiving events
//    - API routes removed
//    - UI extensions hidden
//    - Data preserved (not deleted until uninstall)
//
// 7. UPDATE: New version available
//    - Auto-update check: Compare installed vs. available version
//    - Migration: Plugin.onUpdate(oldVersion, newVersion)
//    - Re-activation with new code
//    - Rollback if activation fails

interface PluginHook {
  event: string;                       // "trip.confirmed"
  handler: string;                     // Function name in plugin code
  priority: number;                    // 1-100 (lower = runs first)
  async: boolean;                      // Can run asynchronously?
  filter: boolean;                     // Can modify event data?
}

// Plugin hook event catalog:
//
// TRIP EVENTS:
// trip.created — New trip created
// trip.updated — Trip details changed
// trip.confirmed — Trip booking confirmed
// trip.cancelled — Trip cancelled
// trip.completed — Trip travel dates passed
// trip.shared — Trip shared with customer
//
// BOOKING EVENTS:
// booking.created — Component booked (hotel, flight, etc.)
// booking.cancelled — Component cancelled
// booking.modified — Booking dates/details changed
//
// PAYMENT EVENTS:
// payment.requested — Payment link generated
// payment.received — Payment received
// payment.refunded — Refund processed
// payment.overdue — Payment past due
//
// COMMUNICATION EVENTS:
// message.received — New customer message
// message.sent — Message sent to customer
// message.template.used — Template message sent
//
// DOCUMENT EVENTS:
// itinerary.generated — Itinerary PDF created
// invoice.generated — Invoice created
// voucher.generated — Voucher created
//
// CUSTOMER EVENTS:
// customer.created — New customer profile
// customer.updated — Customer details changed
// customer.feedback — Customer feedback received
//
// SYSTEM EVENTS:
// agent.login — Agent logged in
// agent.logout — Agent logged out
// daily.summary — Daily summary generation
// scheduled.task — Custom scheduled task

// Plugin hook execution model:
// Synchronous hooks: Block until all handlers complete
//   Used for: Data modification (filters), validation
//   Timeout: 5 seconds per handler
//   Failure: Block the event, notify admin
//
// Asynchronous hooks: Fire and process in background
//   Used for: Notifications, sync, analytics
//   Timeout: 30 seconds per handler
//   Failure: Retry 3 times with exponential backoff, then alert admin
//
// Hook priority ordering:
// 1-20: Platform core handlers
// 21-40: Security and compliance plugins
// 41-60: Data sync and accounting plugins
// 61-80: Communication and notification plugins
// 81-100: Analytics and reporting plugins
```

### Plugin Sandbox & Security

```typescript
interface PluginSandbox {
  execution: ExecutionEnvironment;
  resourceLimits: ResourceLimit[];
  networkAccess: NetworkPolicy;
  dataAccess: DataAccessPolicy;
}

// Execution environment:
// Browser plugins: Sandboxed iframe / Web Worker
//   - No access to parent DOM (only designated slots)
//   - Limited storage quota (10MB per plugin)
//   - No eval() or dynamic code loading
//   - CSP headers enforced
//
// Server-side plugins: Containerized (Docker / V8 isolate)
//   - Memory limit: 256MB per plugin instance
//   - CPU limit: 0.5 cores
//   - Storage limit: 100MB
//   - Network: Whitelisted domains only
//   - Execution timeout: 30 seconds per request
//   - No filesystem access (except plugin storage)
//   - No subprocess execution
//
// Resource limits per plugin:
//   API calls: 100 requests/minute
//   Event hooks: Process within 5s (sync) / 30s (async)
//   Database queries: 50/minute, max 10,000 rows returned
//   Storage: 100MB (documents), 10MB (key-value)
//   Concurrent tasks: 3 simultaneous
//   Scheduled tasks: Max 1 per minute
//
// Network access policy:
//   Default: No external network access
//   Whitelisted: Developer specifies required domains
//   Examples:
//     WhatsApp plugin: api.whatsapp.com, graph.facebook.com
//     Tally plugin: tallysolutions.com (for cloud sync)
//     Stripe plugin: api.stripe.com, js.stripe.com
//   Admin must approve each domain during installation
//   All network calls logged for audit
//
// Data access policy:
//   READ permissions: Specify which data types plugin can read
//   WRITE permissions: Specify which data types plugin can modify
//   DELETE: Never granted (soft-delete via API only)
//   PII access: Requires explicit permission + audit logging
//   Data export: Plugin cannot export data to external services
//     without explicit PII transfer permission
//
// Security review process:
// 1. Static analysis: Scan for known vulnerability patterns
//    - OWASP top 10: SQL injection, XSS, CSRF, etc.
//    - Dependency audit: Known CVEs in npm/pip packages
//    - Permission audit: Are requested permissions minimal?
//
// 2. Dynamic analysis: Run plugin in sandboxed test environment
//    - Memory leak detection
//    - Performance profiling
//    - Network call verification
//    - Error handling check
//
// 3. Manual review (for sensitive categories):
//    - Payment plugins: PCI compliance review
//    - Data sync plugins: Data protection review
//    - AI plugins: Bias and safety review
//    - Admin plugins: Privilege escalation review
```

### Plugin API Surface

```typescript
interface PluginAPI {
  data: DataAPI;
  ui: UIAPI;
  storage: StorageAPI;
  messaging: MessagingAPI;
  scheduling: SchedulingAPI;
  http: HTTPClientAPI;
}

// Data API — Access to platform data (permission-gated):
// trip.get(id) — Read trip details
// trip.search(query) — Search trips
// trip.update(id, changes) — Update trip (with permission)
// customer.get(id) — Read customer profile
// customer.search(query) — Search customers
// destination.get(slug) — Read destination data
// booking.get(id) — Read booking details
// payment.get(id) — Read payment details
// invoice.get(id) — Read invoice details
//
// UI API — Extend platform UI:
// ui.registerPanel(slot, component) — Add panel to workbench
//   Available slots: sidebar, trip_detail_tab, customer_tab,
//                    inbox_action, settings_tab, dashboard_widget
// ui.registerAction(action) — Add action button
//   Available contexts: trip_actions, booking_actions, customer_actions
// ui.registerRoute(path, component) — Add page/route
// ui.showNotification(message) — Show toast notification
// ui.openModal(component) — Show modal dialog
//
// Storage API — Plugin-specific storage:
// storage.set(key, value) — Store key-value data
// storage.get(key) — Retrieve stored data
// storage.delete(key) — Delete stored data
// storage.list(prefix) — List keys with prefix
// storage.quota() — Check storage usage
//
// Messaging API — Send messages:
// messaging.send(customerId, message) — Send to customer
// messaging.notify(agentId, message) — Notify agent
// messaging.email(to, subject, body) — Send email
// messaging.sms(to, message) — Send SMS
//
// Scheduling API — Schedule tasks:
// scheduling.schedule(cron, handler) — Schedule recurring task
// scheduling.delay(handler, milliseconds) — Schedule one-time task
// scheduling.cancel(taskId) — Cancel scheduled task
//
// HTTP Client API — External API calls:
// http.get(url, options) — HTTP GET (whitelisted domains only)
// http.post(url, body, options) — HTTP POST
// http.put(url, body, options) — HTTP PUT
// http.delete(url, options) — HTTP DELETE
// All HTTP calls: Logged, rate-limited, timeout enforced
```

---

## Open Problems

1. **Sandbox escape risk** — No sandbox is perfectly secure. Browser-based sandboxes (iframe, Web Worker) have known escape vectors. Server-side containers add operational complexity.

2. **Plugin performance impact** — Poorly written plugins can slow down the platform. Memory leaks, blocking operations, and excessive API calls degrade the experience for all users. Resource enforcement must be strict.

3. **Plugin compatibility matrix** — With 50+ plugins installed, version conflicts between plugins and with the platform core create a combinatorial testing problem. Automated compatibility testing is essential.

4. **Plugin developer experience** — Building, testing, and debugging plugins requires good tooling (SDK, CLI, local dev server, hot reload). Without a great developer experience, few plugins will be built.

5. **Plugin governance at scale** — Reviewing, approving, and monitoring hundreds of plugins requires significant investment in tooling and human reviewers. Balancing speed of approval with quality of review is challenging.

---

## Next Steps

- [ ] Design plugin manifest schema and registry architecture
- [ ] Build plugin lifecycle management with sandboxed execution
- [ ] Create permission model with granular data access controls
- [ ] Design plugin API surface with SDK documentation
- [ ] Study plugin architectures (Shopify App Store, WordPress Plugins, VS Code Extensions, Figma Plugins)
