# Architecture Decision Record: Frontend Component System

**Status**: Proposed → Accepted  
**Date**: 2026-04-15  
**Author**: Frontend Agent  

## Context

The Travel Agency Agent frontend requires a complete redesign to be both functional and beautiful. It must:
- Support "Travel" (maps, routes, geography)
- Support "Agency" (pipelines, workflows, operations)  
- Support "Agent" (AI nodes, decision flows, intelligence)
- Be B2B-optimized (streamlined, data-dense, efficient)
- Support future multi-agent development (toggle between implementations)

## Decision

We will implement a **layered component architecture** with:

1. **Theme System**: Toggle between visual themes (Travel Map, Agency Pipeline, Agent Flow)
2. **Component Variants**: Multiple implementations of same component with toggle
3. **Feature-Based Organization**: Components grouped by feature, not type
4. **Strict Separation**: UI primitives (dumb) vs Container components (smart)

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER (Theme-aware)                           │
│  ├─ TravelTheme: Maps, routes, waypoints                    │
│  ├─ AgencyTheme: Kanban, pipelines, cards                  │
│  └─ AgentTheme: Nodes, flows, neural visualization         │
├─────────────────────────────────────────────────────────────┤
│  COMPONENT LAYER (Multi-variant)                            │
│  ├─ Shell (navigation wrapper)                             │
│  ├─ Workbench (tab container)                               │
│  ├─ DataCard (facts, decisions, strategy)                  │
│  └─ Visualization (maps, flows, charts)                    │
├─────────────────────────────────────────────────────────────┤
│  PRIMITIVE LAYER (Theme-agnostic)                           │
│  ├─ Button, Badge, Input, Select                           │
│  ├─ Table, List, Card                                      │
│  └─ Tooltip, Modal, Dropdown                               │
├─────────────────────────────────────────────────────────────┤
│  STATE LAYER                                                │
│  ├─ workbenchStore (Zustand)                               │
│  ├─ themeStore (current theme + variant)                   │
│  └─ navigationStore (routing state)                        │
└─────────────────────────────────────────────────────────────┘
```

## Component Toggle System

Each major component supports multiple implementations:

```typescript
// Component variants can be toggled via URL param or UI control
interface ComponentVariant {
  id: string;           // "v1", "v2", "agent", "travel"
  author?: string;      // Agent identifier for multi-agent work
  component: React.FC;  // The actual component
  metadata: {
    description: string;
    status: 'experimental' | 'stable' | 'deprecated';
    features: string[];
  };
}

// Usage
<Workbench variant="v1" />  // Original
<Workbench variant="v2" />  // New design
<Workbench variant="travel" /> // Map-focused
```

## Theme System

Three visual themes representing the three aspects of the product:

### Travel Theme
- Visual: Cartographic dark mode, route lines, waypoint markers
- Colors: Ocean blues, land grays, route cyans
- Patterns: Maps, itineraries, destination cards

### Agency Theme  
- Visual: Operations dashboard, kanban boards, pipeline stages
- Colors: Professional neutrals with state colors
- Patterns: Cards, lists, progress bars, queues

### Agent Theme
- Visual: Neural networks, processing nodes, data flows
- Colors: AI purples, processing cyans, decision ambers
- Patterns: Node graphs, confidence heatmaps, signal flows

## File Organization

```
frontend/src/
├── components/
│   ├── primitives/          # Theme-agnostic UI
│   │   ├── Button.tsx
│   │   ├── Badge.tsx
│   │   └── ...
│   ├── composites/          # Feature components
│   │   ├── DataCard/
│   │   │   ├── index.tsx    # Smart wrapper
│   │   │   ├── variants/
│   │   │   │   ├── v1.tsx   # Original
│   │   │   │   ├── v2.tsx   # New design
│   │   │   │   └── travel.tsx # Map variant
│   │   │   └── types.ts
│   │   ├── RouteMap/
│   │   ├── PipelineFlow/
│   │   └── DecisionNode/
│   ├── layouts/
│   │   ├── Shell.tsx        # App shell
│   │   ├── Workbench.tsx    # Workbench layout
│   │   └── Dashboard.tsx    # Dashboard layout
│   └── visualizations/      # Complex visual components
│       ├── TripRoute.tsx
│       ├── SpinePipeline.tsx
│       └── ConfidenceGraph.tsx
├── hooks/
│   ├── useTheme.ts          # Theme management
│   ├── useComponentVariant.ts
│   └── useWorkbench.ts
├── stores/
│   ├── themeStore.ts
│   └── workbenchStore.ts
└── themes/
    ├── travel.ts
    ├── agency.ts
    └── agent.ts
```

## State Management

### Zustand Stores

1. **themeStore**: Current theme, component variants, preferences
2. **workbenchStore**: Workbench data, active tab, results
3. **navigationStore**: Route state, history, breadcrumbs

### Theme State

```typescript
interface ThemeState {
  currentTheme: 'travel' | 'agency' | 'agent';
  componentVariants: Record<string, string>; // component -> variantId
  setTheme: (theme: string) => void;
  setComponentVariant: (component: string, variant: string) => void;
}
```

## Multi-Agent Development Support

### Component Manifest

Each component variant registers in a manifest:

```typescript
// components-manifest.json (generated)
{
  "Workbench": {
    "v1": { "file": "./composites/Workbench/variants/v1.tsx", "author": "legacy" },
    "v2": { "file": "./composites/Workbench/variants/v2.tsx", "author": "claude-1" },
    "travel": { "file": "./composites/Workbench/variants/travel.tsx", "author": "claude-2" }
  }
}
```

### Toggle UI

A debug/developer panel allows switching variants:

```
┌────────────────────────────────────┐
│  Component Inspector        [X]    │
├────────────────────────────────────┤
│  Workbench: [v1 ▼]                 │
│  • v1 (legacy)                     │
│  • v2 (claude-1)                   │
│  • travel (claude-2)               │
├────────────────────────────────────┤
│  DataCard: [travel ▼]              │
│  • v1                              │
│  • v2                              │
│  • travel ★                        │
└────────────────────────────────────┘
```

## Decision Criteria

| Criterion | Weight | Approach |
|-----------|--------|----------|
| Maintainability | High | Clear separation, typed interfaces |
| Extensibility | High | Variant system, plugin architecture |
| Performance | Medium | Code splitting, lazy loading |
| Developer Experience | High | Clear patterns, good docs |
| Multi-agent Support | Critical | Variant system, manifest |

## Consequences

### Positive
- Can experiment with multiple designs simultaneously
- Future agents can contribute new variants without breaking existing
- Users can choose preferred visual style
- Clear boundaries for testing and documentation

### Negative
- More files to maintain
- Need variant selection UI
- Slightly higher bundle size (mitigated by code splitting)

## Implementation Phases

1. **Phase 1**: Primitives + Shell + basic variant system
2. **Phase 2**: Workbench with tab navigation
3. **Phase 3**: All 5 tabs (Intake, Packet, Decision, Strategy, Safety)
4. **Phase 4**: Visual components (maps, flows, nodes)
5. **Phase 5**: Multi-variant polish + toggle UI

## References

- Docs/DESIGN.md: Visual design system
- Component Spec: OPERATOR_WORKBENCH_COMPONENT_SPEC
- Reference HTML: Archive/design_refs/
