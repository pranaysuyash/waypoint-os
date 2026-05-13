# Workflow Visualization & Component Map

> **Date:** 2026-05-12
> **Status:** Complete — 100% source coverage, 17 workflows, interactive HTML
> **Files:** `workflows.html`, `data/workflows.json`, `tools/workflows/inject_data.py`, `tools/workflows/validate_html.py`

---

## 1. What Was Requested

A single-page interactive HTML visualization that:

- Documents **all workflows** between packages and components in the `travel_agency_agent` app
- Is **driven from a JSON data source** (`data/workflows.json`)
- Allows **clicking a workflow** to highlight the flow and annotate data passed between components
- Covers **every source file** in `src/` — zero blind spots

---

## 2. What Was Built

### Deliverables

| File | Purpose | Size |
|------|---------|------|
| `data/workflows.json` | Authoritative data source — all packages, components, workflows, steps, edges | ~76 KB |
| `workflows.html` | Self-contained interactive visualization — open in any browser, no server needed | ~112 KB |
| `tools/workflows/inject_data.py` | Rebuilds HTML from JSON — run after any `workflows.json` change | 51 lines |
| `tools/workflows/validate_html.py` | Validates JSON integrity, HTML structure, tag balance | 51 lines |

### Stats

| Metric | Count |
|--------|-------|
| Packages | 14 |
| Components | 105 (100% of `src/` — every `.py` and `.go` file) |
| Workflows | 17 |
| Steps | 109 |
| Data Edges | 141 |

### The 17 Workflows

| # | Icon | Workflow | Steps | Edges | What It Covers |
|---|------|----------|-------|-------|----------------|
| 1 | ⚡ | **Full Spine Pipeline** | 13 | 45 | End-to-end intake: extraction → validation → gates → decision → suitability → frontier → strategy → fees → plan → safety → readiness → audit |
| 2 | 👤 | **Invite New Team Member** | 5 | 5 | Platform onboarding: adapter → encryption → jurisdiction → agency config → audit |
| 3 | 🔍 | **Run Extraction Pipeline** | 10 | 6 | Standalone extraction: 7 parallel extractors → geography → normalizer → packet assembly |
| 4 | 🎯 | **Decision & Risk Assessment** | 9 | 10 | NB02 deep dive: blockers → budget → ambiguity → hybrid engine → elderly/composition/visa/budget rules → synthesis |
| 5 | 🛡️ | **Safety, Sanitization & Leakage** | 5 | 5 | Traveler safety: internal field ID → packet sanitization → bundle leakage → view leakage → aggregation |
| 6 | 🧠 | **Strategy & Prompt Bundle Generation** | 4 | 5 | NB03: session strategy → internal bundle → traveler-safe bundle → plan candidate |
| 7 | 🏔️ | **Suitability Assessment Flow** | 6 | 6 | Activity scoring: participant extraction → catalog lookup → scoring → confidence → context rules → critical flag enforcement |
| 8 | 📊 | **Readiness & Go/No-Go Decision** | 5 | 3 | Readiness aggregation: signal collection → completeness → quality → safety gate → verdict |
| 9 | 🤖 | **Agent Runtime & Live Tools** | 8 | 5 | Agent system: registration → dispatch → flight/price/safety/weather tools → events → recovery |
| 10 | 🧩 | **LLM-Powered Extraction** | 5 | 6 | Document extraction: model chain → Gemini/OpenAI vision → pricing → LLM client |
| 11 | 💻 | **ToDesktop Build Pipeline** | 3 | 2 | Desktop packaging: Next.js build → ToDesktop config → native installers |
| 12 | ✅ | **Booking & Confirmation** | 6 | 8 | Post-readiness: plan finalization → payment → booking record → notification → ticketing → audit |
| 13 | ❌ | **Cancellation & Refund** | 7 | 8 | Cancellation lifecycle: request → policy evaluation → refund processing → status update → rebooking → notification → audit |
| 14 | 💬 | **WhatsApp Communication** | 4 | 4 | Messaging pipeline: message formatting → WhatsApp dispatch → event logging → audit |
| 15 | 🚨 | **Emergency Escalation** | 7 | 8 | Emergency response: detection → dispatch → recovery → live tools → notification → escalation events → audit trail |
| 16 | ⭐ | **Post-Trip Feedback & Review** | 7 | 8 | Post-trip: completion detection → feedback request → aggregation → audit → cost reconciliation → learning integration → dashboard |
| 17 | 🌐 | **Federated Intelligence & Negotiation** | 5 | 7 | Multi-agent: intelligence aggregation → negotiation → strategy refinement → plan update → re-readiness |

---

## 3. How It Works

### Architecture

```
data/workflows.json          (single source of truth)
        │
        ▼
tools/workflows/inject_data.py   (rebuild script)
        │
        ▼
workflows.html              (self-contained visualization)
        │
        ▼
Browser                     (open directly, no server)
```

### Data Flow

1. **Author edits `data/workflows.json`** — add/remove components, workflows, edges
2. **Run `python3 tools/workflows/inject_data.py`** — replaces `const DATA = {...};` line in HTML
3. **Open `workflows.html`** — browser renders SVG graph from embedded JSON

### Visualization Modes

- **All Workflows view** — circular layout with all 105 components grouped by package, all 141 edges visible
- **Workflow view** — select any workflow from sidebar or dropdown → only that workflow's components appear, arranged left-to-right in step order, auto-zoomed to fit
- **Click a node** — highlights connected edges, opens detail panel with description, connected workflows, and data handoffs
- **Search** — sidebar filter + full-screen `/` overlay search across components and workflows
- **Pan/Zoom** — mouse drag to pan, scroll wheel to zoom, Reset button to restore

### Rebuild Pipeline

```bash
# After editing data/workflows.json:
python3 tools/workflows/inject_data.py    # rebuild HTML
python3 tools/workflows/validate_html.py  # verify integrity
```

The inject script uses line-based replacement (not regex) to swap the `const DATA = ...;` block, avoiding the fragile regex that previously consumed the rendering engine.

---

## 4. How This Helps

### For New Developers

- **Onboarding in 5 minutes** — open `workflows.html`, click through each workflow, see exactly how data flows from raw input to traveler-facing output
- **No code archaeology** — the visualization shows which modules connect, what data passes between them, and why each step exists
- **Package relationships** — instantly see that `decision_engine` feeds into `strategy`, which feeds into `fees`, which feeds into `plan_candidate`

### For Architecture Decisions

- **Blast radius analysis** — before changing a module, click it to see all workflows that touch it
- **Dependency mapping** — understand which components would break if you refactor `safety.py` or `gates.py`
- **Gap detection** — the 100% coverage check ensures no module is invisible to the architecture

### For Code Reviews

- **Verify data contracts** — each edge documents exactly what data passes between components (e.g., `CanonicalPacket → DecisionResult`)
- **Trace decision logic** — follow the Decision & Risk Assessment workflow to see all rule engines, hybrid engine paths, and risk flag generation
- **Audit safety boundaries** — the Safety & Sanitization workflow shows exactly where internal data is stripped before traveler-facing output

### For Product Planning

- **Feature impact** — adding a new workflow (e.g., "Loyalty Program") shows which existing components need extension
- **Missing capabilities** — the visualization reveals what the system doesn't do yet (e.g., no real-time pricing integration workflow)
- **Operator understanding** — non-technical stakeholders can see the 17 workflows the system handles

---

## 5. The Exploration Map

### How to Navigate

1. **Start broad** — "All Workflows" view shows the full architecture at a glance
2. **Pick a workflow** — click any workflow in the sidebar to isolate its flow
3. **Click a component** — see its description, connected workflows, and data handoffs
4. **Search** — type `/` to search for any component or workflow by name

### Exploration Paths

**Path A: The Intake Pipeline (Core)**
```
Full Spine Pipeline → Run Extraction → Decision → Strategy → Safety → Readiness
```
This is the heart of the system. Follow this path to understand how a traveler's raw message becomes a structured plan.

**Path B: The Decision Engine (Risk)**
```
Decision & Risk Assessment → Hybrid Engine → Rule Engines → Budget/Composition/Visa/Elderly
```
Deep dive into how the system decides whether to proceed, ask follow-up questions, or escalate.

**Path C: The Safety Boundary (Trust)**
```
Safety & Sanitization → Internal Field ID → Packet Sanitization → Leakage Detection
```
Understand the structural separation between internal data and traveler-facing output.

**Path D: The Agent Runtime (Automation)**
```
Agent Runtime → Live Tools → Flight/Price/Safety/Weather → Recovery → Events
```
See how agents are dispatched, how live tools operate, and how failures are recovered.

**Path E: The Post-Trip Loop (Learning)**
```
Booking → Cancellation → Post-Trip Feedback → Dashboard → Strategy Update
```
Understand the full lifecycle from booking through post-trip learning.

**Path F: The LLM Layer (AI)**
```
LLM-Powered Extraction → Model Chain → Gemini/OpenAI Vision → Pricing Extraction
```
See how LLM-based document extraction works alongside the regex pipeline.

### Component Coverage Map

Every source file in `src/` is mapped:

| Package | Components | Key Files |
|---------|-----------|-----------|
| **intake** | 27 | orchestration, extractors, validation, decision, gates, strategy, safety, packet_models, geography, readiness, frontier, negotiation, federated, normalizer, checker_agent, scenario_policy, sourcing_path, specialty_knowledge, telemetry, route_analysis, regional_risk, risk_action_policy, traveler_proposal, config/agency_settings |
| **agents** | 6 | runtime, live_tools, tool_contracts, risk_contracts, recovery_agent, events |
| **suitability** | 7 | integration, scoring, catalog, models, options, context_rules, confidence |
| **decision_engine** | 13 | hybrid_engine, cache_key, cache_schema, cache_storage, health, rule_budget, rule_composition, rule_elderly, rule_toddler, rule_visa, rule_additional, rule_not_applicable, whatsapp_formatter |
| **analytics** | 6 | engine, logger, metrics, models, policy_rules, review |
| **extraction** | 13 | gemini_vision_extractor, openai_vision_extractor, model_chain, pricing, pdf_utils, vision_client, gemini_client, openai_client, local_llm, schemas, smoke_test, exceptions, gemini_vision_client |
| **llm** | 7 | base, openai_client, gemini_client, local_llm, usage_guard, usage_store, agents/__init__ |
| **services** | 11 | dashboard_aggregator, integrity_service, payment_gateway, booking_engine, notification_service, ticketing, cancellation_trigger, cancellation_policy, rebooking_engine, frontend, todesktop |
| **evals** | 8 | audit/metrics, audit/runner, audit/manifest, audit/public_authority, audit/gates, audit/snapshot, audit/fixtures, audit/rules/activity |
| **security** | 3 | encryption, privacy_guard, jurisdiction_policy |
| **fees** | 1 | calculation |
| **public_checker** | 1 | live_checks |
| **adapters** | 1 | __init__ |
| **schemas** | 1 | __init__ |

---

## 6. Maintenance

### Adding a New Workflow

1. Edit `data/workflows.json` — add to the `"workflows"` array:
   ```json
   {
     "id": "my_new_flow",
     "label": "My New Flow",
     "description": "What this flow does.",
     "icon": "🆕",
     "steps": [...],
     "edges": [...]
   }
   ```
2. Add a color to `EDGE_COLORS` in `workflows.html` (or rebuild via inject)
3. Run `python3 tools/workflows/inject_data.py`

### Adding a New Component

1. Edit `data/workflows.json` — add to the relevant package's `"components"` array:
   ```json
   { "id": "new_component", "label": "new_component.py", "desc": "What it does." }
   ```
2. Wire it into at least one workflow's edges
3. Run `python3 tools/workflows/inject_data.py`

### Adding a New Package

1. Edit `data/workflows.json` — add to the `"packages"` object:
   ```json
   "new_package": {
     "label": "New Package",
     "color": "#hexcolor",
     "description": "What this package does.",
     "components": [...]
   }
   ```
2. Add the color to `PACKAGE_COLORS` in the JS (handled by inject)
3. Run `python3 tools/workflows/inject_data.py`

### Validation

Always run after changes:
```bash
python3 tools/workflows/inject_data.py && python3 tools/workflows/validate_html.py
```

---

## 7. Known Limitations

1. **Circular layout in All Workflows view** — with 105 nodes, the circular scatter is dense. Use workflow view for clarity.
2. **Edge labels overlap** — when many edges cross, labels can overlap. Click a workflow to isolate its edges.
3. **No force-directed layout** — the current layout is static (circular for all, left-to-right for workflow view). A force-directed layout would improve spacing but add complexity.
4. **Self-referencing edges** — some edges (e.g., `decision → decision`) are self-references that don't render as visible arrows.
5. **Component deduplication** — `__init__.py` files across multiple packages share the same label, making sidebar search ambiguous.
