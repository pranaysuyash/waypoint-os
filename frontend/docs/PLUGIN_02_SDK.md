# Platform Plugin & Extension System — Developer SDK

> Research document for plugin developer SDK, template scaffolding, debugging tools, testing framework, and documentation generation.

---

## Key Questions

1. **What SDK tools do plugin developers need?**
2. **How do we provide templates and scaffolding for common plugin types?**
3. **What debugging and testing tools support plugin development?**
4. **How do we auto-generate plugin documentation?**
5. **What's the developer onboarding experience for new plugin creators?**

---

## Research Areas

### Plugin SDK Architecture

```typescript
interface PluginSDK {
  cli: PluginCLI;
  templates: PluginTemplates;
  testing: PluginTestFramework;
  debugging: PluginDebugger;
  docs: DocumentationGenerator;
}

interface PluginCLI {
  commands: CLICommand[];
  config: CLIConfig;
}

// CLI commands:
// waypoint-plugin init <name>          — Create new plugin from template
// waypoint-plugin dev                  — Start local development server
// waypoint-plugin build                — Build plugin for distribution
// waypoint-plugin test                 — Run plugin tests
// waypoint-plugin lint                 — Lint plugin code
// waypoint-plugin pack                 — Package plugin as distributable ZIP
// waypoint-plugin publish              — Submit plugin to marketplace
// waypoint-plugin validate             — Validate manifest and code
// waypoint-plugin permissions          — Check and audit permissions
// waypoint-plugin docs                 — Generate documentation
//
// Plugin init flow:
// $ waypoint-plugin init tally-sync
// ? Plugin category: (Use arrow keys)
//   ❯ accounting
//     channel_integration
//     payment_gateway
//     workflow_automation
//     custom
// ? Display name: Tally Accounting Sync
// ? Description: Auto-sync invoices to Tally Prime
// ? Permissions needed:
//   ◉ invoice.read
//   ◉ customer.read
//   ◻ customer.write
//   ◻ trip.read
// ? Hooks to subscribe:
//   ◉ invoice.created
//   ◉ payment.received
//   ◉ credit_note.issued
// ◻ trip.confirmed
// ? Configuration fields:
//   Tally Server URL: __________________
//   Tally Company Name: ________________
//   Sync Frequency: [Daily / Hourly / Real-time]
//
// Creating plugin "tally-sync"...
// ✅ Created tally-sync/
//   ├── manifest.json
//   ├── src/
//   │   ├── index.ts
//   │   ├── hooks.ts
//   │   ├── config.ts
//   │   └── tally-client.ts
//   ├── tests/
//   │   └── hooks.test.ts
//   ├── README.md
//   └── package.json
//
// Next steps:
//   cd tally-sync
//   waypoint-plugin dev

// Plugin template structure:
interface PluginTemplate {
  name: string;                        // "accounting-sync"
  description: string;
  files: TemplateFile[];
  dependencies: string[];
  sampleCode: string;
  testCases: string[];
}

// Template types:
// 1. Basic Hook Plugin: Subscribe to events, process data
// 2. UI Extension Plugin: Add panels, widgets, routes
// 3. API-only Plugin: Expose custom endpoints
// 4. Full Plugin: Hooks + UI + API + Scheduled tasks
// 5. Payment Gateway: Implement payment provider interface
// 6. Channel Integration: Implement messaging channel interface
// 7. Supplier Connector: Implement supplier API adapter
// 8. Document Template: Custom document generation template
// 9. AI Plugin: AI-powered assistant or analysis tool
// 10. Dashboard Widget: Analytics and reporting widget
```

### Plugin Testing Framework

```typescript
interface PluginTestFramework {
  unit: UnitTestFramework;
  integration: IntegrationTestFramework;
  e2e: E2ETestFramework;
  mocking: MockingFramework;
  fixtures: TestFixtures;
}

// Unit testing:
// Test individual hook handlers, API routes, UI components
//
// import { testHook, mockTrip, mockInvoice } from '@waypoint/plugin-test';
//
// describe('Tally Sync Plugin', () => {
//   test('syncs invoice to Tally on invoice.created', async () => {
//     const invoice = mockInvoice({ amount: 50000, customer: 'Acme Corp' });
//     const result = await testHook('invoice.created', { invoice });
//
//     expect(result.success).toBe(true);
//     expect(result.tallyVoucherNumber).toBeDefined();
//     expect(result.syncedAmount).toBe(50000);
//   });
//
//   test('handles Tally connection failure gracefully', async () => {
//     mockTallyServer.respondWith(500, 'Server Error');
//     const invoice = mockInvoice({ amount: 50000 });
//
//     await expect(testHook('invoice.created', { invoice }))
//       .rejects.toThrow('Tally sync failed');
//   });
// });
//
// Integration testing:
// Test plugin with real platform APIs (mocked backend)
//
// import { createPluginTestBed } from '@waypoint/plugin-test';
//
// describe('Tally Plugin Integration', () => {
//   let testBed: PluginTestBed;
//
//   beforeAll(async () => {
//     testBed = await createPluginTestBed({
//       plugin: './src',
//       config: {
//         tallyUrl: 'http://localhost:9000',
//         companyName: 'Test Company',
//       },
//       mocks: {
//         tally: true,  // Mock Tally server
//         platform: true, // Mock platform APIs
//       }
//     });
//   });
//
//   test('full invoice lifecycle', async () => {
//     // Create a trip and confirm booking
//     const trip = await testBed.createTrip({
//       destination: 'Kerala',
//       customer: { name: 'Rajesh Kumar' }
//     });
//
//     // Generate invoice
//     const invoice = await testBed.generateInvoice(trip.id, {
//       amount: 85000
//     });
//
//     // Verify Tally sync happened
//     const tallyRecords = await testBed.mocks.tally.getRecords();
//     expect(tallyRecords).toHaveLength(1);
//     expect(tallyRecords[0].amount).toBe(85000);
//   });
// });
//
// Test fixtures:
// Pre-built test data for common scenarios:
// - Sample trips (Kerala, Goa, Singapore, Dubai)
// - Sample customers (individual, corporate, group)
// - Sample invoices (paid, unpaid, partial, refunded)
// - Sample bookings (confirmed, cancelled, modified)
// - Sample messages (inquiry, complaint, feedback)
// - Edge cases: Empty data, maximum values, unicode, special chars

// Plugin debugging tools:
interface PluginDebugger {
  localDev: LocalDevServer;
  logging: PluginLogger;
  profiler: PluginProfiler;
  inspector: PluginInspector;
}

// Local development server:
// waypoint-plugin dev — Starts local server with:
// - Hot reload: Code changes reflected instantly
// - Mock platform APIs: Simulated trip, customer, booking data
// - Event simulator: Fire test events manually
// - UI preview: Render UI extensions in isolated frame
// - Network inspector: View all HTTP calls made by plugin
// - Storage viewer: Inspect plugin key-value storage
// - Console: View plugin logs in real-time
//
// Plugin profiler:
// - Memory usage over time
// - CPU time per hook execution
// - API call frequency and latency
// - Storage growth rate
// - Alert when approaching resource limits
//
// Plugin inspector:
// - View registered hooks and their handlers
// - See which hooks fired recently and results
// - Inspect API routes registered by plugin
// - View configuration state
// - Check permission grants
// - View scheduled tasks and their status
```

### Documentation Generation

```typescript
interface DocumentationGenerator {
  api: APIDocumentation;
  readme: ReadmeGenerator;
  changelog: ChangelogGenerator;
  examples: ExampleGenerator;
}

// Auto-generated documentation from plugin code:
//
// README.md structure:
// # Tally Accounting Sync
//
// > Auto-sync Waypoint OS invoices to Tally Prime
//
// ## Installation
// 1. Install from Plugin Marketplace
// 2. Configure Tally server URL and company name
// 3. Activate plugin
//
// ## Configuration
// | Field | Required | Description |
// |-------|----------|-------------|
// | Tally Server URL | Yes | URL of Tally Prime server |
// | Company Name | Yes | Tally company to sync to |
// | Sync Frequency | No | Daily (default) / Hourly / Real-time |
//
// ## Permissions
// - `invoice.read` — Read invoice data for sync
// - `customer.read` — Read customer details
//
// ## Events
// | Event | Handler | Description |
// |-------|---------|-------------|
// | `invoice.created` | `onInvoiceCreated` | Sync new invoice to Tally |
// | `payment.received` | `onPaymentReceived` | Record payment in Tally |
//
// ## API Endpoints
// `GET /api/plugins/tally-sync/status` — Get sync status
// `POST /api/plugins/tally-sync/sync` — Trigger manual sync
//
// ## Changelog
// ### v1.2.0 (2026-04-15)
// - Add real-time sync option
// - Fix: Handle Tally server timeout gracefully
//
// ## Support
// Email: developer@example.com
// Docs: https://docs.example.com/tally-sync

// Developer onboarding experience:
// 1. Sign up: Register as plugin developer (email, verify identity)
// 2. Quick start: 5-minute tutorial with working sample plugin
// 3. Templates: Browse and fork from 10+ starter templates
// 4. Documentation: Complete API reference, guides, and examples
// 5. Community: Forum for Q&A, Discord for real-time help
// 6. Testing: Submit test results with plugin for faster review
// 7. Publishing: One-command publish with auto-validation
// 8. Analytics: Dashboard showing plugin installs, usage, errors
//
// Developer SDK packages:
// @waypoint/plugin-sdk — Core SDK (types, utilities, test framework)
// @waypoint/plugin-cli — CLI tools (init, dev, build, publish)
// @waypoint/plugin-test — Testing utilities (mocks, fixtures, assertions)
// @waypoint/plugin-ui — UI components for extensions (React components)
// @waypoint/plugin-docs — Documentation generator
```

---

## Open Problems

1. **SDK maintenance burden** — The SDK must track platform API changes across versions. Breaking changes in the platform must be communicated clearly and the SDK updated promptly.

2. **Testing realism** — Mock platform APIs may not perfectly replicate production behavior. Plugins that pass all tests may still fail in production due to timing, scale, or edge cases.

3. **Developer adoption** — Building a developer ecosystem requires critical mass. Without enough users, few developers will build plugins. Without enough plugins, few users will adopt the platform.

4. **Multi-language SDK** — TypeScript/JavaScript SDK serves web developers but excludes Python developers (data science, ML plugins). Maintaining SDKs in multiple languages multiplies the effort.

5. **Plugin debugging in production** — Debugging a failing plugin in a live environment is much harder than in local development. Production-safe debugging tools (logging, tracing) without exposing sensitive data is challenging.

---

## Next Steps

- [ ] Build plugin CLI with init, dev, build, test, and publish commands
- [ ] Create plugin template library for common plugin categories
- [ ] Design plugin testing framework with mocks and fixtures
- [ ] Implement local development server with hot reload and event simulation
- [ ] Study plugin SDKs (Shopify CLI, WordPress Plugin Developer Hub, Stripe Apps SDK, Figma Plugin API)
