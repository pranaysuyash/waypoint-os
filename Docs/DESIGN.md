# Travel Agency Agent — Design System

**Version**: 2.0.0  
**Date**: 2026-04-15  
**Style**: Agentic Intelligence + Travel Geography  

---

## 1. Design Philosophy

### The Name is The Design

**"Travel"** → Maps, routes, destinations, geography, itineraries, waypoints  
**"Agency"** → Workflow, pipelines, customers, operations, orchestration  
**"Agent"** → AI, nodes, flows, decision trees, processing, intelligence

### Core Visual Metaphors

1. **The Route Map**: Every trip is a journey. Visualize as paths with waypoints (destinations), stops (blockers), and alternate routes (branch options).

2. **The Pipeline Flow**: NB01→NB02→NB03 is a processing pipeline. Visualize as nodes connected by data flows.

3. **The Intelligence Layer**: AI decisions are visualized as confidence heatmaps, signal strength, and decision nodes.

4. **The Agency Operations**: Customers, pipelines, and workloads visualized as cards, kanban boards, and queues.

### Visual Thesis

> A travel intelligence dashboard where geography meets decision science. Dark cartographic aesthetic with data-rich overlays. Routes glow with confidence levels. Decision nodes pulse with state colors. The interface feels like mission control for travel operations.

---

## 2. Color System

### Background Hierarchy (Cartographic Dark)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-canvas` | `#080a0c` | Deepest background - the map canvas |
| `--bg-surface` | `#0f1115` | Cards, panels - raised terrain |
| `--bg-elevated` | `#161b22` | Elevated elements - highlights |
| `--bg-highlight` | `#1c2128` | Active selections, hover |
| `--bg-input` | `#111318` | Input fields, code blocks |

### Text Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--text-primary` | `#e6edf3` | Primary text, labels |
| `--text-secondary` | `#a8b3c1` | Secondary info, metadata — lightened from #8b949e for WCAG AA compliance (5.2:1) |
| `--text-tertiary` | `#9ba3b0` | Disabled, placeholders — lightened from #6e7681 for ~4.5:1 contrast |
| `--text-muted` | `#8b949e` | Subtle borders, inactive — formerly #484f58 (was 2.8:1, too low) |
| `--text-accent` | `#58a6ff` | Links, interactive |

### Accent Colors (State + Geography)

| Token | Value | Meaning |
|-------|-------|---------|
| `--accent-green` | `#3fb950` | PROCEED, safe routes, success |
| `--accent-amber` | `#d29922` | BRANCH, alternate routes, warning |
| `--accent-red` | `#f85149` | STOP, blockers, danger zones |
| `--accent-blue` | `#58a6ff` | ASK_FOLLOWUP, water, links |
| `--accent-purple` | `#a371f7` | AI processing, owner mode, special |
| `--accent-cyan` | `#39d0d8` | Data flows, information streams |
| `--accent-orange` | `#ff9248` | Urgency, heat zones |

### State Color Mapping

| Decision State | Background Glow | Border | Text | Icon |
|----------------|-----------------|--------|------|------|
| `PROCEED_TRAVELER_SAFE` | `rgba(63,185,80,0.08)` | `#3fb950` | `#3fb950` | ✓ Route clear |
| `PROCEED_INTERNAL_DRAFT` | `rgba(217,164,32,0.08)` | `#d29922` | `#d29922` | ⏵ Draft mode |
| `BRANCH_OPTIONS` | `rgba(217,164,32,0.12)` | `#d29922` | `#d29922` | ⇄ Junction |
| `STOP_NEEDS_REVIEW` | `rgba(248,81,73,0.12)` | `#f85149` | `#f85149` | ✕ Blocker |
| `ASK_FOLLOWUP` | `rgba(88,166,255,0.08)` | `#58a6ff` | `#58a6ff` | ? Question |

### Geographic Accent Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--geo-land` | `#1c2128` | Map land areas |
| `--geo-water` | `#0d2137` | Map water, oceans |
| `--geo-route` | `#39d0d8` | Active routes, paths |
| `--geo-route-dim` | `#1a3a3f` | Inactive routes |
| `--geo-waypoint` | `#d29922` | Stops, waypoints |
| `--geo-destination` | `#3fb950` | Final destinations |

### Border Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--border-default` | `#30363d` | Default separators |
| `--border-hover` | `#8b949e` | Interactive borders |
| `--border-active` | `#58a6ff` | Focus, active |
| `--border-route` | `rgba(57,208,216,0.3)` | Route lines |

---

## 3. Typography

### Font Stack

```css
--font-display: "Sora", system-ui, sans-serif;        /* Headings, UI (loaded via next/font) */
--font-body: "Rubik", system-ui, sans-serif;          /* Body text (loaded via next/font) */
--font-mono: "JetBrains Mono", "SF Mono", monospace;  /* Code, data */
--font-data: "IBM Plex Mono", monospace;              /* Numbers, metrics */
--font-map: "Sora", system-ui, sans-serif;             /* Map labels */
```

### Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `text-2xs` | 10px | 500 | 1.3 | Micro labels, timestamps |
| `text-xs` | 11px | 400 | 1.4 | Badges, metadata |
| `text-sm` | 12px | 400 | 1.5 | Labels, captions |
| `text-base` | 13px | 400 | 1.5 | Body text |
| `text-md` | 14px | 400 | 1.5 | Standard UI |
| `text-lg` | 16px | 500 | 1.4 | Section headers |
| `text-xl` | 18px | 600 | 1.3 | Card titles |
| `text-2xl` | 24px | 600 | 1.2 | Page headings |
| `text-mono` | 13px | 400 | 1.4 | Data values, field names |
| `text-mono-sm` | 12px | 400 | 1.4 | Compact data |

### Typography Patterns

**Section Labels**: `text-xs`, `--text-secondary`, `font-weight: 600`, `text-transform: uppercase`, `letter-spacing: 0.08em`

**Data Field Names**: `text-mono-sm`, `--text-secondary`

**Data Values**: `text-mono`, `--text-primary`, `font-weight: 500`

**Confidence Scores**: `text-mono`, `--text-secondary`

**Map Labels**: `text-xs`, `--text-secondary`, `letter-spacing: 0.02em`

---

## 4. Spacing System

Base unit: `4px`

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight gaps |
| `--space-2` | 8px | Default element spacing |
| `--space-3` | 12px | Card padding, section gaps |
| `--space-4` | 16px | Container padding |
| `--space-5` | 20px | Major gaps |
| `--space-6` | 24px | Page sections |
| `--space-8` | 32px | Large breaks |
| `--space-10` | 40px | Page margins |
| `--space-12` | 48px | Major section breaks |

---

## 5. Layout

### Grid System

- **Base Grid**: 12 columns
- **Gutter**: 16px
- **Max Width**: 1680px (full-bleed dashboard)
- **Page Padding**: 24px horizontal

### Layout Patterns

**Three-Column Agency Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ LEFT (60%)       │ CENTER (25%)      │ RIGHT (15%)          │
│ Main Content      │ Sidebar           │ Meta/Actions         │
│ ─────────────     │ ───────────       │ ────────────         │
│ • Trip details    │ • Quick stats     │ • Provenance         │
│ • Facts table     │ • Flags           │ • Timeline           │
│ • Derived signals │ • Risk indicators │ • Evidence links     │
└─────────────────────────────────────────────────────────────┘
```

**Pipeline Flow Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  [NB01: INTAKE] → [NB02: DECISION] → [NB03: STRATEGY]       │
│     [Packet]        [State]            [Bundles]            │
│                                                        │
│  ═══════════════════════════════════════════════════   │
│  Data Flow Visualization (horizontal or vertical)     │
└─────────────────────────────────────────────────────────────┘
```

**Kanban Agency View**:
```
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ INBOX   │ REVIEW  │ OPTIONS │ QUOTES  │ BOOKED  │
│ ─────── │ ─────── │ ─────── │ ─────── │ ─────── │
│ [Card]  │ [Card]  │ [Card]  │ [Card]  │ [Card]  │
│ [Card]  │         │ [Card]  │         │ [Card]  │
│ [Card]  │         │         │         │         │
└─────────┴─────────┴─────────┴─────────┴─────────┘
```

---

## 6. Visual Elements

### 6.1 Route/Path Visualizations

**Active Route Line**:
```css
.route-line {
  height: 2px;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue));
  border-radius: 1px;
  position: relative;
}

.route-line::after {
  content: '';
  position: absolute;
  right: 0;
  top: -2px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-cyan);
  box-shadow: 0 0 8px var(--accent-cyan);
}
```

**Waypoint Marker**:
```css
.waypoint {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid var(--border-default);
  background: var(--bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
}

.waypoint.active {
  border-color: var(--accent-cyan);
  background: rgba(57, 208, 216, 0.1);
  box-shadow: 0 0 0 4px rgba(57, 208, 216, 0.1);
}

.waypoint.destination {
  border-color: var(--accent-green);
  background: rgba(63, 185, 80, 0.1);
}
```

**Junction/Branch Indicator**:
```css
.junction {
  display: flex;
  align-items: center;
  gap: 4px;
}

.junction-line {
  width: 20px;
  height: 2px;
  background: var(--border-default);
}

.junction-node {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent-amber);
  position: relative;
}

.junction-node::before,
.junction-node::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 2px;
  background: var(--border-default);
  transform-origin: left center;
}

.junction-node::before {
  transform: rotate(-30deg);
}

.junction-node::after {
  transform: rotate(30deg);
}
```

### 6.2 Node/Flow Visualizations

**Pipeline Node**:
```css
.pipeline-node {
  padding: 12px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  position: relative;
}

.pipeline-node.active {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 1px var(--accent-blue), 0 0 20px rgba(88, 166, 255, 0.1);
}

.pipeline-node.processing::after {
  content: '';
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  border-radius: 8px;
  border: 1px solid transparent;
  border-top-color: var(--accent-cyan);
  animation: node-spin 1s linear infinite;
}

@keyframes node-spin {
  to { transform: rotate(360deg); }
}
```

**Data Flow Connector**:
```css
.flow-connector {
  position: relative;
  height: 2px;
  background: var(--border-default);
}

.flow-connector.active {
  background: linear-gradient(90deg, var(--accent-cyan), transparent);
  background-size: 20px 2px;
  animation: flow-move 1s linear infinite;
}

@keyframes flow-move {
  to { background-position: -20px 0; }
}
```

**Decision Diamond**:
```css
.decision-diamond {
  width: 48px;
  height: 48px;
  transform: rotate(45deg);
  border: 1px solid var(--border-default);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.decision-diamond-content {
  transform: rotate(-45deg);
  font-size: 11px;
  font-weight: 600;
}

.decision-diamond.proceed {
  border-color: var(--accent-green);
  background: rgba(63, 185, 80, 0.1);
}

.decision-diamond.stop {
  border-color: var(--accent-red);
  background: rgba(248, 81, 73, 0.1);
}
```

### 6.3 Map-Style Cards

**Geographic Card**:
```css
.geo-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  overflow: hidden;
}

.geo-card-map {
  height: 120px;
  background: linear-gradient(135deg, var(--geo-land) 0%, var(--geo-water) 100%);
  position: relative;
}

.geo-card-content {
  padding: 16px;
}
```

**Mini Route Preview**:
```css
.route-preview {
  position: relative;
  height: 60px;
  background: var(--geo-land);
  border-radius: 8px;
  overflow: hidden;
}

.route-preview-path {
  position: absolute;
  top: 50%;
  left: 16px;
  right: 16px;
  height: 2px;
  background: var(--geo-route);
  transform: translateY(-50%);
}

.route-preview-waypoints {
  position: absolute;
  top: 50%;
  left: 16px;
  right: 16px;
  display: flex;
  justify-content: space-between;
  transform: translateY(-50%);
}
```

---

## 7. Components

### 7.1 Cards

**Standard Card**:
```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 16px;
}
```

**Data Card with Route Indicator**:
```css
.data-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 16px;
  position: relative;
}

.data-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 24px;
  bottom: 24px;
  width: 3px;
  background: var(--accent-color, var(--border-default));
  border-radius: 0 2px 2px 0;
}
```

**Metric Card**:
```css
.metric-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.metric-value {
  font-size: 32px;
  font-weight: 200;
  line-height: 1;
  color: var(--text-primary);
}

.metric-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  margin-top: 8px;
}
```

### 7.2 Badges

**Authority Badge** (monospace, colored by source):
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 500;
  font-family: var(--font-mono);
  text-transform: lowercase;
  border: 1px solid;
}

.badge-explicit-user {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.2);
}

.badge-explicit-owner {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border-color: rgba(59, 130, 246, 0.22);
}

.badge-derived {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.2);
}

.badge-hypothesis {
  background: rgba(113, 113, 122, 0.12);
  color: #a1a1aa;
  border-color: rgba(113, 113, 122, 0.2);
}
```

**State Badge**:
```css
.state-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.state-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.state-badge.proceed::before {
  background: var(--accent-green);
  box-shadow: 0 0 6px var(--accent-green);
}

.state-badge.stop::before {
  background: var(--accent-red);
  box-shadow: 0 0 6px var(--accent-red);
}

.state-badge.branch::before {
  background: var(--accent-amber);
  box-shadow: 0 0 6px var(--accent-amber);
}

.state-badge.ask::before {
  background: var(--accent-blue);
  box-shadow: 0 0 6px var(--accent-blue);
}
```

### 7.3 Tables

**Data Table**:
```css
.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.data-table th {
  padding: 10px 12px;
  text-align: left;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-default);
}

.data-table td {
  padding: 12px;
  font-size: 13px;
  border-bottom: 1px solid var(--border-default);
  vertical-align: top;
}

.data-table tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}
```

**Field Row with Confidence Bar**:
```css
.field-row {
  display: grid;
  grid-template-columns: 1fr 2fr 100px 80px;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-default);
}

.confidence-bar {
  width: 60px;
  height: 4px;
  background: var(--bg-highlight);
  border-radius: 2px;
  overflow: hidden;
}

.confidence-bar-fill {
  height: 100%;
  background: var(--accent-color);
  border-radius: 2px;
  transition: width 0.3s ease;
}
```

### 7.4 Navigation

**Sidebar Navigation**:
```css
.sidebar {
  width: 240px;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-default);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  margin: 2px 8px;
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background: var(--bg-highlight);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-blue);
  color: #0d1117;
  font-weight: 500;
}

.nav-item .icon {
  width: 18px;
  height: 18px;
}
```

**Tab Navigation**:
```css
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border-default);
}

.tab {
  padding: 12px 20px;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.15s ease;
}

.tab:hover {
  color: var(--text-primary);
}

.tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent-blue);
  font-weight: 500;
}
```

### 7.5 Buttons

**Primary Button**:
```css
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--accent-blue);
  color: #0d1117;
  font-size: 13px;
  font-weight: 500;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary:hover {
  background: #6eb5ff;
}
```

**Secondary Button**:
```css
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-highlight);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  border: 1px solid var(--border-default);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-secondary:hover {
  background: var(--bg-elevated);
  border-color: var(--border-hover);
}
```

**Ghost Button**:
```css
.btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-ghost:hover {
  background: var(--bg-highlight);
  color: var(--text-primary);
}
```

### 7.6 Inputs

**Text Input**:
```css
.input {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-input);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  transition: all 0.15s ease;
}

.input:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1);
}

.input::placeholder {
  color: var(--text-tertiary);
}

.input.monospace {
  font-family: var(--font-mono);
}
```

**Textarea**:
```css
.textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  background: var(--bg-input);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  transition: all 0.15s ease;
}

.textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1);
}
```

---

## 8. Special Patterns

### 8.1 Confidence Indicators

**Confidence Dot**:
```css
.confidence-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.confidence-dot.high { background: var(--accent-green); }
.confidence-dot.medium { background: var(--accent-amber); }
.confidence-dot.low { background: var(--accent-red); }
```

**Confidence Bar with Label**:
```css
.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence-bar-bg {
  width: 50px;
  height: 4px;
  background: var(--bg-highlight);
  border-radius: 2px;
  overflow: hidden;
}

.confidence-bar-fill {
  height: 100%;
  border-radius: 2px;
}

.confidence-value {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
  width: 32px;
  text-align: right;
}
```

### 8.2 Status Indicators

**Status Dot with Pulse**:
```css
.status-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: relative;
}

.status-pulse::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: pulse-ring 2s ease-out infinite;
}

.status-pulse.active {
  background: var(--accent-green);
}

.status-pulse.active::before {
  background: rgba(63, 185, 80, 0.3);
}

@keyframes pulse-ring {
  0% { transform: translate(-50%, -50%) scale(0.5); opacity: 1; }
  100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
}
```

### 8.3 Evidence Tooltip

**Evidence Hover Card**:
```css
.evidence-trigger {
  position: relative;
  cursor: help;
}

.evidence-tooltip {
  position: absolute;
  z-index: 50;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  padding: 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  opacity: 0;
  pointer-events: none;
  transition: all 0.15s ease;
  margin-bottom: 8px;
}

.evidence-trigger:hover .evidence-tooltip {
  opacity: 1;
  pointer-events: auto;
}

.evidence-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.evidence-content {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-primary);
}

.evidence-source {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-tertiary);
  margin-top: 8px;
}
```

### 8.4 Empty States

**Empty State with Icon**:
```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-state-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  color: var(--text-tertiary);
}

.empty-state-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.empty-state-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}
```

---

## 9. Animation

### Transitions

```css
--transition-fast: 150ms ease;
--transition-base: 200ms ease;
--transition-slow: 300ms ease;
```

### Key Animations

**Node Processing**:
```css
@keyframes node-processing {
  0% { box-shadow: 0 0 0 0 rgba(57, 208, 216, 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(57, 208, 216, 0); }
  100% { box-shadow: 0 0 0 0 rgba(57, 208, 216, 0); }
}

.processing {
  animation: node-processing 1.5s ease-out infinite;
}
```

**Route Pulse**:
```css
@keyframes route-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.route-active {
  animation: route-pulse 2s ease-in-out infinite;
}
```

**Fade In**:
```css
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-in {
  animation: fade-in 0.2s ease-out;
}
```

---

## 10. CSS Variable Setup

```css
:root {
  /* Backgrounds */
  --bg-canvas: #080a0c;
  --bg-canvas-rgb: 8 10 12;
  --bg-surface: #0f1115;
  --bg-elevated: #161b22;
  --bg-highlight: #1c2128;
  --bg-input: #111318;
  --bg-count-badge: #21262d;
  --bg-rationale: #0d1117;

  /* Text — WCAG AA compliant on dark backgrounds (4.5:1 minimum) */
  --text-primary: #e6edf3;         /* 15.4:1 */
  --text-secondary: #a8b3c1;       /* 5.2:1 — lightened from design spec for AA */
  --text-tertiary: #9ba3b0;        /* ~4.5:1 — lightened from design spec for AA */
  --text-muted: #8b949e;           /* 3.9:1 — for large text only */
  --text-accent: #58a6ff;
  --text-placeholder: #484f58;
  --text-on-accent: #0d1117;
  --text-rationale: #c9d1d9;

  /* Accents */
  --accent-green: #3fb950;
  --accent-green-rgb: 63 185 80;
  --accent-amber: #d29922;
  --accent-amber-rgb: 210 153 34;
  --accent-red: #f85149;
  --accent-red-rgb: 248 81 73;
  --accent-blue: #58a6ff;
  --accent-blue-rgb: 88 166 255;
  --accent-blue-hover: #6eb5ff;
  --accent-purple: #a371f7;
  --accent-purple-rgb: 163 113 247;
  --accent-cyan: #39d0d8;
  --accent-orange: #ff9248;

  /* Geographic */
  --geo-land: #1c2128;
  --geo-water: #0d2137;
  --geo-route: #39d0d8;
  --geo-route-dim: #1a3a3f;
  --geo-waypoint: #d29922;
  --geo-destination: #3fb950;

  /* Borders */
  --border-default: #30363d;
  --border-hover: #8b949e;
  --border-active: #58a6ff;
  --border-route: rgba(57, 208, 216, 0.3);

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Typography */
  --font-display: "Sora", system-ui, sans-serif;
  --font-body: "Rubik", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "SF Mono", monospace;
  --font-data: "IBM Plex Mono", monospace;
  --font-map: "Sora", system-ui, sans-serif;

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-spring: 500ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
```

---

## 11. Iconography

Use **Lucide React** for all icons. Key icons for the travel agent theme:

### Navigation Icons
- `Map` - Trips/routes
- `Inbox` - Messages
- `Briefcase` - Workbench
- `BarChart3` - Insights
- `Users` - Customers
- `Settings` - Configuration

### State Icons
- `CheckCircle2` - Proceed/Success
- `AlertTriangle` - Warning/Branch
- `XCircle` - Stop/Blocker
- `HelpCircle` - Ask/Question
- `RefreshCw` - Processing
- `Clock` - Pending

### Travel Icons
- `Plane` - Flights
- `Building2` - Hotels
- `MapPin` - Destinations
- `Route` - Itinerary
- `Compass` - Discovery
- `Globe` - International

### Data Icons
- `GitBranch` - Branch options
- `Workflow` - Pipeline
- `Activity` - Activity log
- `Zap` - Quick actions
- `Filter` - Filtering
- `Search` - Search

### Icon Sizes
- Navigation: 18px
- Inline: 14px
- Status indicators: 16px
- Empty states: 48px
- Buttons: 14px

---

## 12. Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| `xs` | < 480px | Single column, stacked navigation |
| `sm` | 480-640px | Single column, condensed cards |
| `md` | 640-1024px | Two column, collapsible sidebar |
| `lg` | 1024-1280px | Three column, full sidebar |
| `xl` | 1280-1536px | Full layout, max density |
| `2xl` | > 1536px | Full layout, spacious |

---

*This design system captures the essence of Travel Agency Agent: where travel geography meets AI decision intelligence. Routes, nodes, flows, and maps form the visual language.*
