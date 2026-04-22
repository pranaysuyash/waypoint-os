# Design Brief: Command Palette (Cmd+K)

> Feature: Global command palette for instant access to trips and actions
> Status: Design phase — ready for implementation
> Date: 2026-04-22

---

## 1. Feature Summary

A keyboard-first command palette (activated via Cmd+K) that lets agents instantly search trips, navigate to any workspace, and execute common actions without touching the mouse. Primary use case: the "11 PM WhatsApp panic" scenario where an urgent customer message arrives and the agent needs to find their trip, understand status, and respond within seconds.

**Who:** Solo agents and small agency teams working under time pressure
**What:** Global search + quick actions interface
**Why:** Speed = more customers served. Mouse navigation is too slow for urgent responses.

---

## 2. Primary User Action

**Type Cmd+K → Search → Hit Enter → Act**

The critical path is:
1. Customer WhatsApp arrives at 11 PM
2. Agent hits Cmd+K (muscle memory, no thinking)
3. Types customer name or destination
4. Sees trip, hits Enter
5. Lands in workspace, can respond immediately

**Success metric:** Agent can go from notification to workspace in under 3 seconds.

---

## 3. Design Direction

**Tone:** Instant, capable, reassuring. The palette should feel like "I can find anything" — a safety net for panic moments.

**Aesthetic alignment with Palantir inspiration:**
- Dark overlay with focused search
- Minimal chrome, maximum data density
- Keyboard shortcuts visible (teach by showing)
- No decorative elements — every pixel serves speed

**Reference patterns:**
- Linear's Cmd+K: Search + actions combined
- Superhuman: Speed, keyboard-first
- Slack Cmd+K: Familiar mental model

---

## 4. Layout Strategy

```
┌─────────────────────────────────────────────────────────┐
│  Overlay: 50% black backdrop                            │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🔍 Search trips, actions, destinations...        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Recent                                           │   │
│  │  ● John Doe - Thailand  [Enter→]                │   │
│  │  ● Smith Family - Kerala    [Enter→]            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Actions                                          │   │
│  │  + New trip         [Cmd+N]                      │   │
│  │  → Go to inbox       [Cmd+I]                     │   │
│  │  → Go to workspace   [Cmd+W]                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Trips matching "Thailand"                        │   │
│  │  ● Thailand Honeymoon - John Doe     [Workspace] │   │
│  │    SLA: Amber • Budget: ₹2L • Due in 2 days     │   │
│  │  ● Thailand Family - Smith Family  [Workspace]   │   │
│  │    SLA: Green • Budget: ₹3.5L • Due in 1 week   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Visual hierarchy:**
1. Search input (always focused)
2. Recent trips (quick access to last 5)
3. Actions (common operations)
4. Search results (fuzzy matches)

**Key layout decisions:**
- Centered modal, max-width 600px
- Results grouped by type (Recent, Actions, Trips)
- Each result shows actionable info (SLA status, urgency)
- Keyboard hints visible (teach while using)

---

## 5. Key States

### Default State (Cmd+K pressed)
- Search input focused, cursor ready
- Recent trips shown (last 5 accessed)
- Common actions listed
- Empty state guidance: "Start typing to search..."

### Searching State (User typing)
- Real-time fuzzy filtering as user types
- Results update instantly
- Loading indicator only if fetching from server
- Highlight matching text in results

### No Results State
- Clear message: "No trips or actions found"
- Suggestion: "Try a different search or create a new trip"
- Action button: "Create new trip" highlighted

### Error State
- Network error: "Couldn't search. Retrying..." with auto-retry
- Degrad gracefully: Show recent trips even if search fails

### Navigation State
- Arrow keys navigate results
- Up/down wraps around
- Enter triggers selected action
- Escape closes palette

### Post-Action State
- Palette closes, user navigated to destination
- OR palette stays open for multi-action workflows (e.g., batch operations)

---

## 6. Interaction Model

### Keyboard Interactions
| Key | Action |
|-----|--------|
| `Cmd+K` | Open/close palette |
| `Escape` | Close palette |
| `↑/↓` | Navigate results |
| `Enter` | Trigger selected result |
| `Tab` | Cycle through result groups |
| `Cmd+N` | Create new trip (from anywhere) |
| `Cmd+I` | Go to inbox |
| `Cmd+W` | Go to workspace |

### Mouse Interactions
- Click outside → close
- Click result → navigate
- Click × in search → clear search
- Scroll in results → overflow scroll

### Search Behavior
- **Fuzzy matching:** "thland" matches "Thailand"
- **Multi-field search:** Searches across customer name, destination, trip ID
- **Action search:** Type "create" to show "Create new trip" action
- **Scope:** Searches ALL trips, not just current view

### Feedback
- Hover: Background tint on selected result
- Focus: Blue border on search input
- Selection: Arrow key selection shows visual indicator
- Loading: Subtle spinner in search input (right side)

---

## 7. Content Requirements

### Labels & Copy
- Search placeholder: "Search trips, actions, destinations..."
- Recent section header: "Recent"
- Actions section header: "Actions"
- Results section header: "Trips matching '{query}'"
- No results: "No trips or actions found"
- Keyboard hints: "[Enter→]" shown next to actionable items

### Result Item Content
Each trip result shows:
- Primary: Customer name or trip identifier
- Secondary: Destination, trip type
- Meta: SLA status (color), urgency indicator, budget
- Shortcut: "[Enter→]" or "[Workspace]"

### Action Items
- Icon + Label + Shortcut
- Examples: "+ New trip", "→ Go to inbox", "→ Go to workspace"

### Empty State Copy
- Default: "Start typing to search trips, destinations, or actions"
- No results: "No trips match '{query}'. Want to create a new trip?"

---

## 8. Recommended References

For implementation, consult:
- `reference/interaction-design.md` — Keyboard patterns, focus management
- `reference/typography.md` — Result item hierarchy, search input styling
- `reference/spatial-design.md` — Modal positioning, overflow handling

---

## 9. Technical Considerations

### Performance
- Debounce search input by 150ms (balance speed vs. flicker)
- Cache recent trips in memory (avoid re-fetching on every open)
- Virtualize results if 50+ items (unlikely but plan for it)

### Accessibility
- Focus trap: Tab stays within palette when open
- Escape always closes
- ARIA live regions for search results count
- Keyboard navigation fully functional without mouse

### State Management
- Recent trips: Track last 5 accessed trips
- Search index: Client-side search on loaded data, server search for larger sets
- Keyboard shortcuts: Global listener, conflicts with browser shortcuts

---

## 10. Open Questions

1. **Search scope:** Search all trips or just current view? → All trips (panic scenario needs access to everything)
2. **Action filtering:** Should actions be context-aware? → Yes, show workspace actions only when in workspace
3. **Result grouping:** Fixed sections (Recent/Actions/Trips) or dynamic? → Fixed sections, results shown below
4. **Mobile support:** Does Cmd+K work on mobile? → No, replace with bottom search bar on mobile
5. **Batch operations:** Should palette support multi-select? → Phase 2, not initial scope

---

## 11. Success Criteria

- [ ] Cmd+K opens palette from anywhere in app
- [ ] Search returns results in <200ms for 1000+ trips
- [ ] Keyboard navigation works without mouse
- [ ] Recent trips are accurate and useful
- [ ] Agent can navigate from notification to workspace in <3 seconds
- [ ] Palette feels instant and capable (reassuring)

---

## 12. Anti-Patterns to Avoid

- ❌ Don't show decorative icons for every result (wastes space)
- ❌ Don't use glassmorphism or blur effects (reduces readability)
- ❌ Don't hide keyboard shortcuts (teach by showing)
- ❌ Don't make results too sparse (data density is good)
- ❌ Don't use skeleton loaders (search should be instant)
- ❌ Don't show generic "AI assistant" chat interface (this is search, not chat)

---

## Implementation Roadmap

**Phase 1: Foundation**
1. Cmd+K opens modal
2. Search trips by customer name, destination
3. Navigate to trip on Enter
4. Recent trips tracking
5. Core actions (New trip, Go to inbox)

**Phase 2: Capability Expansion**
1. Actions search (type "create" to see create actions)
2. Context-aware actions (workspace vs inbox)
3. Keyboard shortcut hints
4. Result item metadata (SLA, budget, urgency)

**Phase 3: Power Features**
1. Batch operations (multi-select)
2. Custom actions/shortcuts
3. Search filters (by status, destination)
4. Mobile adaptation

**Phase 4: Intelligence**
1. Predictive search (learn from patterns)
2. Natural language queries ("show me urgent thailand trips")
3. Action suggestions based on context
4. Integration with other features (Quality Indicators, Customer Profiles)

---

**Ready for implementation.** This brief aligns with the Palantir-inspired, data-dense, fast, and reassuring design direction established in UX discovery.
