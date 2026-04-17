# Plugin System Exploration (Draft) — 2026-04-17

## Status
- **Draft / Not Final**
- Goal: define the plugin model that keeps the core deterministic while enabling safe extensibility.

## Why Explore This Next
The project already points to a protocol + registry pattern (catalog/scorer/allocator style). A formal plugin system can:
- speed feature expansion without monolith growth
- keep layer ownership clean (analyzers vs routers)
- allow phased rollout (stub -> heuristic -> verified -> ml-assisted)

## Scope of This Exploration
This draft is for architecture and sequencing, not final implementation lock.

## Candidate Plugin Domains (High Leverage)
1. **Suitability plugins**
   - `ActivityCatalogProvider`
   - `SuitabilityScorer`
   - `ScheduleAllocator`
2. **Audit rule plugins**
   - category-specific risk evaluators (budget, activity, pacing, logistics, docs)
3. **Data-source plugins**
   - static config, agency config, external APIs (normalized to common contracts)
4. **Ops/Live plugins**
   - flight disruption signal provider
   - alert routing adapter

## Core Design Questions to Resolve
1. **Registration model**
   - explicit registry in code vs entrypoint-based discovery
2. **Contract strictness**
   - Protocol only vs Protocol + versioned capability metadata
3. **Execution model**
   - sync-only v1 vs controlled async plugin execution
4. **Safety model**
   - timeout, error isolation, fallback order, hard stop conditions
5. **Policy precedence**
   - traveler facts > agency overrides > memory > policy > global heuristic

## Recommended v1 Architecture
- Start with explicit in-repo registries (no dynamic loading yet).
- Require each plugin to expose:
  - `plugin_id`
  - `version`
  - `maturity` (`stub|heuristic|verified|ml_assisted`)
  - deterministic input/output contract
- Add wrapper execution guardrails:
  - max runtime per plugin
  - typed error envelope
  - fallback chain with explicit provenance

## Minimal Plugin Lifecycle
1. Implement plugin contract + unit tests
2. Register plugin in registry
3. Add fixture-based evaluation
4. Mark manifest status (`planned -> shadow -> gating`)
5. Enable in production policy

## Proposed Execution Order
1. Formalize base plugin interfaces and capability metadata
2. Build execution wrapper (timeouts, errors, fallback)
3. Migrate one existing analyzer path to plugin-managed execution
4. Add audit-rule plugin lane
5. Add external data plugin lane

## Non-Goals (for this draft)
- Third-party marketplace/plugin store
- remote code execution plugins
- untrusted plugin loading

## Open Decisions
- Should plugin enablement be per-agency config or global rollout flag?
- Do we need plugin dependency graphs in v1 or only flat ordered chains?
- What is the minimum evidence/provenance contract every plugin must emit?
