# UI/UX Affordances — Wide-Open Brainstorm

**Date**: 2026-05-09  
**Status**: Pre-research — 8-role interrogation  
**Method**: Wide-open brainstorm (Strategist, Operator, Skeptic, Executioner, Trickster, Cartographer, Future Self, Champion)

---

## Why This Matters

The Travel Agency Agent is an operational cockpit for travel professionals. Operators need to:
- Know what actions are possible at every moment
- See system state at a glance (AI processing vs draft vs verified)
- Trust that clicking something does what it says
- Never discover a critical action by accident

Affordances are the bridge between UI as "display" and UI as "tool." Right now, affordance awareness is incidental (9 documents mention the term, 0 systematically analyze it). That's a gap worth closing before the UI scales to multi-agent workflows, 4 personas, and AI-stateful surfaces.

---

## Role 1: Strategist — Why This, Why Now?

**Core thesis**: As the product moves from prototype to operational tool, affordance failures become trust failures. A button that looks clickable but does nothing erodes confidence faster than a missing feature.

**Market timing**:
- Travel agency CRMs universally lack computed priority / smart affordances (white space from DESIGN_2D_PRIORITY_MODEL research)
- AI-stateful UIs are new territory — no established affordance patterns for "the AI is thinking" vs "the AI needs your review" vs "the AI is done"
- Mobile/tablet usage growing in travel agencies — hover-only affordances become invisible
- 4 personas means 4 different affordance needs (Owner wants aggregate controls, Traveler wants simple action paths)

**What success looks like**:
- Every UI element passes the "what can I do here?" test without text labels
- False affordances: 0 in audit (elements that look actionable but aren't)
- Hidden affordances: 0 in audit (actions that exist but can't be discovered)
- Operators can name the state of any trip at a glance (color, shape, position)
- Mobile affordances work as well as desktop

**Risk of doing nothing**: Accumulating small affordance violations that erode trust. The "export button that doesn't export" pattern (already found in Audit Report TASK-010). Each violation is tiny. Together, they make the product feel unreliable.

---

## Role 2: Operator — What Does Real Usage Look Like?

**Persona: Ravi (Owner) using the app at his desk, phone ringing, two junior agents asking questions.**

Ravi's flow:
1. Opens dashboard → sees 20 trips → needs to pick which to work on
2. Clicks a trip → right rail opens (good: progressive disclosure)
3. Hovers over edit icon → sees it (good: desktop affordance works)
4. But on his iPad between meetings → no hover → edit icon invisible → **hidden affordance** (already documented in DATA_CAPTURE_UI_UX_AUDIT)
5. Clicks "Export" in Insights → nothing happens → **false affordance** (already found)
6. Tries to see why AI made a decision → unclear what's clickable → **missing signifier**

**Operational cost of affordance failures**:
- Hidden affordance: 5-10 seconds of hunting per action → 3-5 minutes per day → 15-25 hours/year per agent
- False affordance: 30 seconds of confusion + support question → 5+ minutes per incident
- Missing state affordance: wrong action taken on stale data → minutes to hours of rework

**What operators actually need**:
- "Tell me what I can do here, right now, without reading"
- "Show me what state this is in so I don't act on old data"
- "Don't let me click things that won't work"
- "If there's an action hidden behind a hover, tell me — or make it always visible"

---

## Role 3: Skeptic — Push Back on the Premise

**Counter-argument**: "This is academic. Our users are busy travel agents, not UX reviewers. They'll figure out the UI. We have real features to build."

**Response**: The data says otherwise. We already have 10 documented affordance violations across 9 documents. The export button (false affordance), the hover-only edit (hidden affordance), the waitlist email box (false affordance). Each one represents a moment where a user tried to do something and couldn't. That's not academic — that's friction with a real cost.

**Counter-argument**: "Affordances are obvious. Buttons look clickable. That's common sense."

**Response**: Common sense is wrong about:
- AI-stateful UI: "Processing" vs "Draft" vs "Verified" — these states require different affordances but currently look the same
- Multi-device: Desktop affordances (hover, right-click) that don't exist on touch
- Power vs novice: Junior agents need different affordance density than owners
- Cross-platform: What Mac users expect vs Windows vs mobile

**Counter-argument**: "We can fix affordance issues as we find them. No need for systematic research."

**Response**: We found 10 violations without looking systematically. A systematic audit will find more, and the framework will prevent new ones from being introduced. Prevention is cheaper than fixing after users complain.

---

## Role 4: Executioner — How Would We Actually Do This?

**Scope this for actionable output, not a textbook.**

**Phase 1: Audit framework (3 days)**
1. Define affordance types that matter for operational software
2. Create audit checklist from Norman + Nielsen + Hartson
3. Run audit against current UI (10-15 screens)
4. Document all violations with severity (P0-P3)

**Phase 2: Pattern library (2 days)**
1. Document what good affordances look like in our context
2. Create signifier patterns for AI states (processing/draft/verified/error)
3. Define cross-device affordance rules (hover → tap → long-press mapping)
4. Codify persona-specific affordance density rules

**Phase 3: Implementation guidelines (1 day)**
1. Add affordance review to design QA checklist
2. Create component-level affordance specs for new components
3. Define false/hidden affordance regression tests

**Key deliverables**:
- Affordance audit report with screenshots and P0-P3 severities
- Affordance pattern library (10-15 patterns with code examples)
- Design QA checklist addition (5-10 affordance checks)
- Component specs for stateful UI affordances

**What NOT to do**:
- Don't write a 50-page HCI textbook
- Don't try to cover every affordance type (social/cultural affordances are out of scope for V1)
- Don't rebuild the UI — identify the worst violations and fix them

---

## Role 5: Trickster — What's the Unexpected Angle?

**Angle 1: Affordances as competitive moat.**
No travel agency CRM treats affordances systematically. If our UI is the first one where agents never ask "where do I click?" or "why didn't that work?" — that's a real differentiator. Operators evaluate tools on trust, not feature lists.

**Angle 2: False affordances as user research gold.**
A user clicking a non-functional button and being confused is the best data we have. Every false affordance is a revealed desire. The export button that doesn't work tells us users want to export. The waitlist box that does nothing tells us users want to waitlist.

**Angle 3: The best affordance fix might be removing something, not adding something.**
Instead of adding hover tooltips everywhere, maybe the hover-only edit should become always-visible. Instead of adding "this is processing" text, maybe the state change should be the affordance (e.g., the card pulses while processing, settles when done).

**Angle 4: Platform conventions as free affordances.**
Mac users know cmd+S saves. Windows users know ctrl+C copies. Mobile users know long-press selects. We don't need to invent new affordances — we need to not break the ones users already know.

---

## Role 6: Cartographer — Map the Territory

**Affordance type landscape for operational software:**

```
AFFORDANCE TYPES (operational software context)
├── Perceived affordances
│   ├── What buttons/links look like they do
│   ├── What cards/items look like they reveal
│   └── What status indicators communicate
├── Hidden affordances
│   ├── Hover-only controls
│   ├── Right-click menus
│   ├── Keyboard shortcuts
│   └── Gesture-based actions (mobile)
├── False affordances
│   ├── Non-functional buttons
│   ├── Non-functional form fields
│   ├── Disabled states that don't explain why
│   └── Visual cues that don't match behavior
├── Pattern affordances
│   ├── Platform conventions (cmd/ctrl, right-click, long-press)
│   ├── Design system conventions (our patterns users learn)
│   └── Industry conventions (travel CRM patterns)
└── AI-state affordances (new category)
    ├── "AI is thinking" (processing state)
    ├── "AI needs review" (draft state)
    ├── "AI is done" (verified state)
    ├── "AI is uncertain" (confidence indicators)
    └── "Action may be irreversible" (commitment cues)
```

**Related systems already in the codebase:**

| System | Affordance relevance | Current state |
|--------|---------------------|---------------|
| UX Anti-Patterns doc | False precision, modal fatigue, dashboard graveyard | Foundational (73 lines) |
| DATA_CAPTURE_UI_UX_AUDIT | Hidden affordance (hover-only edit), missing lead capture | 715 lines, actionable |
| Audit Report | False affordance (export button), hidden affordance (edit) | P2 priority |
| travel_agency_process_issue_review | False affordance (waitlist email) | Documented |
| DESIGN_2D_PRIORITY_MODEL | Color+shape+text for state indicators | Design complete |
| frontend DESIGN docs | Upload zone affordance, card expand/collapse | Scattered |

**Gap analysis:**

| Topic | Covered? | Where? |
|-------|----------|--------|
| Affordance theory (Norman, etc.) | ❌ Nowhere | Would be new |
| Systematic affordance audit | ❌ Nowhere | Would be new |
| Affordance pattern library | ❌ Nowhere | Would be new |
| AI-state affordances | ❌ Nowhere | Would be new |
| Cross-device affordance mapping | Partially | DATA_CAPTURE_AUDIT covers hover/touch |
| Platform conventions | Partially | DESIGN.md upload zone |
| False affordance detection | Ad-hoc | Found in 3 reviews but no method |
| Design QA affordance checklist | ❌ Nowhere | Would be new |

---

## Role 7: Future Self — What Does "Done" Look Like?

**6 months from now, affordances are part of the design culture.**

- Every PR includes an affordance check: "Does this add any new UI elements? Have they been reviewed for false/hidden affordances?"
- New hire onboarding includes: "Here's our affordance pattern library — 15 patterns, 3 minutes to read."
- The design QA checklist has a section: "Affordance check" (5 items, 30 seconds to verify).
- Zero affordance-related support tickets in the last 3 months.
- Ravi can use the app on his iPad without hunting for hidden controls.
- Export button has been removed if not functional, or wired up. No false affordances remain.

**What "done" is NOT**:
- A 100-page academic document no one reads
- A single audit that fixes today's issues but tomorrow's design still has the same problems
- "We'll add affordance checks later, after shipping"

**The bar**: A new component created today has affordance checks before it merges. Not after. Not "in the next sprint."

---

## Role 8: Champion — Why I'm Fighting for This

Every affordance violation is a moment where someone trusted the software and was let down. Not dramatically — just a tiny "oh, that didn't work" that compounds into "I don't trust this tool."

Travel agents are not software enthusiasts. They use the tool to get a job done. When a button doesn't work, they don't file a bug — they find a workaround, or they find a different tool. Each false affordance is a small vote against us.

The fix is not expensive. It's a framework, a checklist, a few hours of audit, and a commitment that new components pass the "what can I do here?" test. The ROI is in trust, which is the one thing a travel agency CRM cannot live without.

---

## Summary: What We're Actually Doing Here

**We are not writing a textbook on HCI. We are doing:**

1. ~~Adding affordance awareness~~ ✅ Audit complete, framework exists
2. **Fixing the known violations** — export button, hover-only edit, waitlist email (a few hours of work)
3. ~~Auditing for unknown violations~~ ✅ 14 issues found (3 P0, 4 P1, 4 P2, 3 P3)
4. **Writing down AI-state affordance patterns** — because this is new territory and nobody has patterns yet
5. **Preventing new violations** — through the checklist, not through process overhead

**Audit complete**: [AFFORDANCE_AUDIT_FINDINGS_2026-05-09.md](./AFFORDANCE_AUDIT_FINDINGS_2026-05-09.md) — 14 findings across 15+ component files. Root cause: 6 of 14 issues are the `opacity-0 group-hover:opacity-100` hover-reveal pattern. 5 quick wins identified.

---

---

## Appendix B: Installed Affordances Skill (vjrivmon/app-gestion-familiar)

Installed via `npx skillfish add vjrivmon/app-gestion-familiar affordances` → `~/.claude/skills/affordances/` (and 29 other agents)

**Content summary** (bilingual Spanish/English):
- Covers Gibson (1966) and Norman (1988) origins
- 4 types: Physical affordances (Gibson), Perceived affordances (Norman), Signifiers, Anti-patterns
- Application patterns: buttons, links, forms, controls with specific visual cues
- Metrics: Discoverability Score, First Click Accuracy, Error Rate, Time to First Interaction
- Anti-patterns: links that don't look like links, flat buttons without hover, clickable areas without signals
- Related principles: feedback-principle, nielsen-visibility, constraints-principle

**Relevance**: Provides the foundational HCI vocabulary (Gibson physical affordances vs Norman perceived affordances vs signifiers) that was missing from all other skills. The taxonomy and anti-patterns are directly usable as audit criteria.

---

## Appendix C: Other Skills Installed

| Source | Skills | Installed To |
|--------|--------|-------------|
| `vjrivmon/app-gestion-familiar` | affordances | ~/.claude/skills/affordances/ + 29 agents |
| `Leonxlnx/taste-skill` | brandkit, industrial-brutalist-ui, gpt-taste, image-to-code, imagegen-frontend-mobile, imagegen-frontend-web, minimalist-ui, full-output-enforcement, redesign-existing-projects, high-end-visual-design, stitch-design-taste, design-taste-frontend | `.agents/skills/` |
| `giuseppe-trisciuoglio/developer-kit@shadcn-ui` | shadcn-ui | `.agents/skills/shadcn-ui/` |
| `mblode/agent-skills@ui-animation` | ui-animation | `.agents/skills/ui-animation/` |
| `vercel-labs/agent-skills@web-design-guidelines` | web-design-guidelines | `.agents/skills/web-design-guidelines/` |

---

## Appendix A: Skill Store Discovery Results

The instructions specify 9 skill locations. All 9 were checked:

| # | Store | Checked | Relevant Skills Found |
|---|-------|---------|----------------------|
| 1 | `~/Projects/skills/` | ✅ | `hig-components-menus` (mentions "affordance"), `product-design`, `baseline-ui` |
| 2 | `~/.claude/skills/` | ✅ | Generic design QA skills, no affordance depth |
| 3 | `~/.agents/skills/` | ✅ | Mirror of .claude |
| 4 | `~/.hermes/skills/` | ✅ | `visual-design`, `design` (implementation-focused) |
| 5 | `~/Projects/external-skills/` | ✅ | **Owl-Listener__designer-skills** (63 skills, 8 plugins — PRIMARY MATCH), **sickn33__antigravity-awesome-skills** (ui-ux-designer, product-design, baseline-ui) |
| 6 | `~/Projects/openai-skills/` | ✅ | No UX/HCI/affordance content |
| 7 | `~/.codex/skills/` | ✅ | `gstack-design-review`, `gstack-design-consultation` (design QA, not theory) |
| 8 | `~/.codex/skills/.system/` | ✅ | No relevant skills |
| 9 | `$CODEX_HOME/skills/` | ✅ | `CODEX_HOME` not set |

### Key Discovery: Owl-Listener__designer-skills (63 skills across 8 plugins)

**Path**: `~/Projects/external-skills/Owl-Listener__designer-skills/`

This is the most comprehensive design/HCI skillset found across all 9 stores:

| Plugin | Skills | Affordance Relevance |
|--------|--------|---------------------|
| **prototyping-testing** | `heuristic-evaluation`, `test-scenario`, `usability-test-plan`, `a-b-test-design`, `wireframe-spec`, `user-flow-diagram`, `click-test-plan`, `accessibility-test-plan` | **HIGH** — Only heuristic evaluation skill found anywhere. Nielsen's 10 heuristics. |
| **interaction-design** | `micro-interaction-spec`, `animation-principles`, `state-machine`, `gesture-patterns`, `error-handling-ux`, `loading-states`, `feedback-patterns` | **HIGH** — TRFL framework (Trigger-Rules-Feedback-Loops) is a signifier grammar. State machine skill maps every state to UI representation. |
| **design-research** | `user-persona`, `empathy-map`, `journey-map`, `interview-script`, `usability-test-plan`, `card-sort-analysis`, `diary-study-plan`, `affinity-diagram`, `jobs-to-be-done` | **HIGH** — Complete user research toolkit. interview-script + usability-test-plan directly applicable. |
| **design-ops** | `design-critique`, `design-qa-checklist`, `design-review-process`, `design-sprint-plan`, `handoff-spec`, `team-workflow`, `version-control-strategy` | **MEDIUM** — QA checklist covers states but lacks explicit affordance checks. Methodology repurposable. |
| **design-systems** | `accessibility-audit`, `component-spec`, `design-token`, `documentation-template`, `icon-system`, `naming-convention`, `pattern-library`, `theming-system` | **MEDIUM** — Pattern library structure repurposable for affordance patterns. Accessibility audit provides severity framework. |
| **designer-toolkit** | `case-study`, `design-rationale`, `design-system-adoption`, `design-token-audit`, `presentation-deck`, `ux-writing` | **LOW** |
| **ui-design** | `layout-grid`, `color-system`, `typography-scale`, `responsive-design`, `visual-hierarchy`, `spacing-system`, `dark-mode-design`, `data-visualization` | **LOW** — Visual design, not interaction/HCI. |
| **ux-strategy** | `competitive-analysis`, `design-principles`, `experience-map`, `north-star-vision`, `opportunity-framework`, `design-brief`, `metrics-definition` | **LOW** — Strategic, not operational. |

### Other Relevant Skills Found

| Skill | Store | Relevance |
|-------|-------|-----------|
| `sickn33__antigravity-awesome-skills/product-design` | external-skills | **HIGH** — Explicitly names affordances ("what is clickable looks clickable"), 10-item UI critique checklist, cognitive design principles |
| `sickn33__antigravity-awesome-skills/baseline-ui` | external-skills | **MEDIUM** — "NEVER use glow effects as primary affordances" rule, 87 MUST/SHOULD/NEVER constraints |
| `sickn33__antigravity-awesome-skills/ui-ux-designer` | external-skills | **LOW** — Capability inventory, no operational content |
| `sickn33__antigravity-awesome-skills/design-spells` | external-skills | **LOW** — Creative inspiration, risk heuristic only |
| `hig-components-menus` | ~/Projects/skills/ | **LOW** — Only skill outside Owl-Listener that uses the word "affordance" (line 17) |

### Gap Confirmed

No skill across **all 9 stores** explicitly covers:
- Gibson's/Norman's affordance theory
- HCI as a discipline
- Cognitive load / mental models in UX
- A dedicated affordance audit methodology

**Conclusion from skill discovery**: The Owl-Listener skillset (especially `heuristic-evaluation`, `state-machine`, `micro-interaction-spec`, `feedback-patterns`, `usability-test-plan`, `interview-script`) + `sickn33/product-design` provide the methodological infrastructure. But none cover affordances as a dedicated topic. The research is still warranted — and these skills can serve as tools *within* the research process rather than replacing it.

---

- `Docs/UX_ANTI_PATTERNS_AND_BEST_PRACTICES.md` — Covers false precision, modal fatigue, dashboard graveyard. Already affordance-adjacent.
- `Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md` — 715 lines. Most detailed affordance-adjacent research. Documents hover-only edit as hidden affordance.
- `Docs/AUDIT_REPORT.md` — TASK-010: Improve capture UI affordance (hover-only). P2.
- `Docs/travel_agency_process_issue_review_2026-04-29.md` — "False affordance" of the waitlist email box.
- `Docs/DESIGN_2D_PRIORITY_MODEL_2026-05-08.md` — Color+shape+text for state indicators (accessibility meets affordance).
- `frontend/docs/status/PRODUCTB_EVENT_SCHEMA_IMPLEMENTATION_2026-05-07.md` — Share/report UI affordances without event emission.
- `frontend/DESIGN.md` — Upload zone drag-and-drop affordance.
- `frontend/docs/DESIGN_02_COMPONENTS_DEEP_DIVE.md` — Component-level design patterns (affordance-adjacent).
- `frontend/docs/DESIGN_03_PATTERNS_DEEP_DIVE.md` — UX pattern deep-dive.
- `frontend/docs/ACCESSIBILITY_04_UX.md` — Inclusive UX design patterns, WCAG compliance.

**Skills gap confirmed**: No skill across any of the 4 stores (Projects, .claude, .agents, .hermes) covers HCI theory, affordances research, heuristic evaluation, or design pattern libraries systematically. HIG-adjacent skills (`hig-components-menus`, `hig-components-controls`) touch on practical affordances but lack theoretical depth. A dedicated skill would need to be created.
