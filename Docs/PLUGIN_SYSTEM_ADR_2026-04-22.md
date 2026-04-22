# Plugin System Architecture Decision Record

**Date**: 2026-04-22
**Status**: Accepted
**Replaces**: `Docs/PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md` (draft)
**Purpose**: Formalize the plugin model that keeps core judgment deterministic while enabling safe extensibility

---

## 1. Context

The hybrid engine (`src/decision/`) currently registers 9 rules (5 main + 4 not-applicable) statically in `__init__.py`. The suitability module (`src/suitability/`) has a static catalog of 18 activities. Every new decision type or activity requires editing core code.

The D4 sub-decision addendum (`Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md`) explicitly deferred Tier 3 (LLM contextual scoring) because the plugin boundary was undefined.

D6 eval (`Docs/D6_EVAL_CONTRACT_DESIGN_2026-04-22.md`) requires that every judgment source be traceable — a requirement the current static coupling cannot easily satisfy.

We need a plugin system that:
1. Keeps core judgment deterministic
2. Allows new scorers/rules/analyzers without monolith growth
3. Supports eval traceability (every plugin output must have provenance)
4. Enables phased maturity (`stub → heuristic → verified → ml-assisted`)

---

## 2. Decision

We will adopt an **explicit in-repo registry** pattern for v1. No dynamic loading. No third-party marketplace. All plugins are first-party code deployed with the application.

### 2.1 Plugin Contract

Every plugin must expose:
```python
class PluginManifest:
    plugin_id: str           # Unique identifier
    version: str             # SemVer
    maturity: Literal["stub", "heuristic", "verified", "ml-assisted"]
    layer: Literal["nb01", "nb02", "nb03", "nb04", "nb05", "nb06", "cross_layer"]
    
    # Execution contract
    input_schema: Dict        # JSON Schema of accepted inputs
    output_schema: Dict       # JSON Schema of produced outputs
    max_runtime_ms: int        # Timeout for execution guard
    
    # Provenance
    requires_rationale: bool   # Must emit reasoning
    deterministic: bool        # Is output deterministic for given input?
    
    # Lifecycle
    eval_fixture_dir: Optional[str]  # Where golden path fixtures live
    shadow_enabled: bool       # Can run in shadow mode
    gating_required: bool      # Must pass eval before production enablement
```

### 2.2 Registry Design

```python
class PluginRegistry:
    """Explicit registry — no dynamic discovery."""
    
    def __init__(self):
        self._plugins: Dict[str, PluginManifest] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register(self, manifest: PluginManifest, factory: Callable) -> None:
        """Register a plugin with explicit code reference."""
        if manifest.plugin_id in self._plugins:
            raise PluginConflictError(manifest.plugin_id)
        self._plugins[manifest.plugin_id] = manifest
        self._factories[manifest.plugin_id] = factory
    
    def get(self, plugin_id: str) -> Optional[PluginManifest]:
        return self._plugins.get(plugin_id)
    
    def list_by_layer(self, layer: str) -> List[PluginManifest]:
        return [p for p in self._plugins.values() if p.layer == layer]
    
    def list_by_maturity(self, min_maturity: str) -> List[PluginManifest]:
        """Filter by minimum maturity level."""
        maturity_order = ["stub", "heuristic", "verified", "ml-assisted"]
        min_idx = maturity_order.index(min_maturity)
        return [p for p in self._plugins.values() 
                if maturity_order.index(p.maturity) >= min_idx]
```

### 2.3 Execution Wrapper

```python
class PluginExecutor:
    """Safe execution with timeouts, error isolation, and fallback chains."""
    
    def execute(
        self,
        plugin_id: str,
        inputs: Dict[str, Any],
        fallback_chain: Optional[List[str]] = None,
    ) -> PluginResult:
        
        manifest = self.registry.get(plugin_id)
        if not manifest:
            return PluginResult.error(f"Plugin {plugin_id} not found")
        
        # Validate inputs against schema
        try:
            validate(inputs, manifest.input_schema)
        except ValidationError as e:
            return PluginResult.error(f"Invalid input: {e}")
        
        # Execute with timeout
        try:
            factory = self.registry._factories[plugin_id]
            plugin = factory()
            
            result = run_with_timeout(
                plugin.execute,
                inputs,
                timeout_ms=manifest.max_runtime_ms
            )
            
            # Validate outputs
            validate(result, manifest.output_schema)
            
            # Add provenance
            result["_provenance"] = {
                "plugin_id": plugin_id,
                "version": manifest.version,
                "maturity": manifest.maturity,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "deterministic": manifest.deterministic,
            }
            
            if manifest.requires_rationale and "rationale" not in result:
                return PluginResult.error("Rationale required but missing")
            
            return PluginResult.ok(result)
            
        except TimeoutError:
            return self._try_fallback(fallback_chain, inputs, "timeout")
        except Exception as e:
            return self._try_fallback(fallback_chain, inputs, f"error: {e}")
    
    def _try_fallback(
        self,
        chain: Optional[List[str]],
        inputs: Dict[str, Any],
        reason: str
    ) -> PluginResult:
        if not chain:
            return PluginResult.error(f"No fallback available ({reason})")
        
        for fallback_id in chain:
            result = self.execute(fallback_id, inputs, chain=None)
            if result.is_ok:
                result.data["_provenance"]["fallback_from"] = reason
                return result
        
        return PluginResult.error("All fallbacks exhausted")
```

### 2.4 Maturity Progression

| Maturity | Meaning | Production? | Eval Required? |
|----------|---------|-------------|----------------|
| `stub` | Placeholder / no-op. Returns default. | Yes (no-op safe) | No |
| `heuristic` | Simple rules. May produce false positives. | Yes, gated to review | Golden path only |
| `verified` | Passes golden path + shadow mode. Stable. | Yes, may auto-proceed | Full eval suite |
| `ml-assisted` | Requires ML model. Interpretable only. | Owner-configurable | Continuous eval |

### 2.5 Plugin Lifecycle

```
1. Implement Plugin Contract + unit tests
   ↓
2. Register in explicit registry (with manifest)
   ↓
3. Add golden path fixtures to eval_fixture_dir
   ↓
4. Run golden path eval → mark as "heuristic"
   ↓
5. Enable in shadow mode on production traffic
   ↓
6. Shadow comparison passes → mark as "verified"
   ↓
7. Add to default policy (or per-agency opt-in)
```

---

## 3. Plugin Domains (v1)

### Domain A: Suitability Scoring (D4 Tier 3)

**Plugin ID**: `suitability_tier3_llm_scorer`
**Layer**: `nb02`
**Maturity**: `ml-assisted` (future)

```python
class SuitabilityTier3Plugin:
    """LLM-based contextual suitability scorer."""
    
    manifest = PluginManifest(
        plugin_id="suitability_tier3_llm_scorer",
        version="0.1.0",
        maturity="stub",  # Starts as stub
        layer="nb02",
        input_schema={ /* activity + traveler profile + context */ },
        output_schema={ /* suitability_score + rationale + confidence */ },
        max_runtime_ms=5000,
        requires_rationale=True,
        deterministic=False,  # LLM is stochastic
        eval_fixture_dir="tests/evals/fixtures/suitability_tier3",
        shadow_enabled=True,
        gating_required=True,
    )
    
    def execute(self, inputs):
        activity = inputs["activity"]
        profile = inputs["traveler_profile"]
        context = inputs["trip_context"]
        
        # Currently stub: always returns medium confidence
        return {
            "suitability_score": 0.5,
            "rationale": "Stub scorer — not yet implemented",
            "confidence": 0.0,
        }
```

### Domain B: Audit Rule Plugins (D6)

**Plugin ID**: `audit_risk_{category}`
**Layer**: `nb04`
**Maturity**: `heuristic` → `verified`

Replaces the current hardcoded risk flag generation with plugin-registered rules.

### Domain C: Data Source Plugins (Gap #03)

**Plugin ID**: `source_{provider}`
**Layer**: `nb01`
**Maturity**: `stub` → `heuristic`

For external data sources (visa APIs, weather services, hotel rates). Normalizes to common contract.

---

## 4. Policy Precedence

Every plugin result is interpreted with this precedence:

```
1. Hard safety invariants (STOP_NEEDS_REVIEW always blocks)
2. traveler facts (explicit_user, manual_override)
3. agency policy overrides (D1 mode overrides)
4. memory/history (D5 learned rules)
5. plugin results (maturity matters)
6. global heuristic/fallback
```

A `verified` plugin result overrides a `heuristic` plugin result. A `stub` plugin is ignored. An `ml-assisted` plugin is gated to review unless eval precision > threshold.

---

## 5. Per-Agency vs Global Enablement

**v1 Decision**: Plugins are globally registered. Agency enablement is controlled via D1 policy.

```python
# In AgencyAutonomyPolicy
enabled_plugins: List[str] = field(default_factory=list)
plugin_maturity_floor: str = "heuristic"  # Don't enable stubs
```

If an agency doesn't enable `suitability_tier3_llm_scorer`, Tier 3 scoring falls back to Tier 1+2 deterministic rules.

**v2 Consideration** (post-Gap #02): Per-agency plugin marketplace. Not in scope now.

---

## 6. Dependency Graph

**v1 Decision**: Flat ordered chains with explicit fallback lists. No dependency graph.

```python
# In manifest
fallback_chain: List[str] = ["suitability_tier2_context", "suitability_tier1_deterministic"]
```

If Tier 3 fails → fall back to Tier 2 → fall back to Tier 1.

**v2 Consideration**: Add DAG dependency graph when we have >10 plugins.

---

## 7. Minimum Provenance Contract

Every plugin output MUST include:

```json
{
  "_provenance": {
    "plugin_id": "suitability_tier3_llm_scorer",
    "version": "0.1.0",
    "maturity": "stub",
    "executed_at": "2026-04-22T12:00:00Z",
    "deterministic": false,
    "fallback_from": null,
    "execution_time_ms": 42
  }
}
```

This is required for:
- D6 eval traceability
- D5 override attribution ("which plugin was overriden?")
- D1 autonomy audit ("why did this decision reach this state?")
- Debugging ("which version of the scorer produced this result?")

---

## 8. Safety Model

| Guard | Mechanism | Default |
|-------|---------|---------|
| Timeout | `run_with_timeout()` wrapper | 5000ms |
| Error isolation | Each plugin runs in own try/except | Yes |
| Fallback chain | Explicit ordered list | Mandatory |
| Output validation | JSON Schema enforcement | Yes |
| Rationale enforcement | Raises if `requires_rationale=True` but missing | Yes |
| Maturity gate | `verified` required for auto-proceed | Yes |
| Eval gate | `gating_required=True` blocks production until eval passes | Yes |

---

## 9. Migration: Existing Rules → Plugins

The 9 existing rules in `src/decision/rules/` should be migrated to plugins as the first test of the system.

### Migration Order
1. `budget_feasibility` — simplest rule, well-tested
2. `composition_risk` — medium complexity
3. `elderly_mobility` + `toddler_pacing` — similar structure
4. `visa_timeline` — requires external data (good test for future data-source plugins)
5. Not-applicable rules — move to stub maturity

### Post-Migration
- `src/decision/rules/` becomes `src/plugins/decision_rules/`
- `src/plugins/` becomes the canonical plugin directory
- `src/suitability/` migrates to `src/plugins/suitability/` (future)

---

## 10. Non-Goals

| Not in v1 | Reason |
|-----------|--------|
| Third-party marketplace | Security, trust, verification overhead |
| Remote code execution plugins | Attack surface too large |
| Dynamic loading at runtime | Complexity exceeds value |
| Per-agency custom plugins | Needs multi-tenant isolation (Gap #08) |
| Plugin dependency graphs | Flat chains sufficient for v1 |
| Plugin versioning with rollback | Registry restart required for now |

---

## 11. Implementation Order

1. **Phase 0** — `src/plugins/` directory + base interfaces (`PluginManifest`, `PluginRegistry`, `PluginExecutor`)
2. **Phase 1** — Migrate one rule (`budget_feasibility`) to plugin to test the framework
3. **Phase 2** — Migrate all 9 rules to plugins, delete `src/decision/rules/`
4. **Phase 3** — Add `suitability_tier3_llm_scorer` as stub plugin
5. **Phase 4** — Add audit rule plugin lane for D6

---

## 12. Verification

```bash
# Test registry
uv run pytest tests/plugins/test_registry.py -q

# Test execution wrapper
uv run pytest tests/plugins/test_executor.py -q

# Test migrated rules still work
uv run pytest tests/test_decision_rules.py -q  # After migration

# Test provenance contract
uv run pytest tests/plugins/test_provenance.py -q
```

---

## References

- `Docs/PLUGIN_SYSTEM_EXPLORATION_DRAFT_2026-04-17.md` — Original draft
- `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md` — D4 Tier 3 deferral rationale
- `Docs/D6_EVAL_CONTRACT_DESIGN_2026-04-22.md` — Eval traceability requirements
- `Docs/V02_GOVERNING_PRINCIPLES.md` — Layer ownership and deterministic-first principle
- `Docs/CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md` — Manifest-driven eval pattern

---

Decision approved: 2026-04-22
Next review: after Phase 2 migration (all 9 rules)
