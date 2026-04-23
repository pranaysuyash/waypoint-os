# UX & Design Documentation Index

> Travel Agency Agent Workspace — "Palantir for travel agencies"
> Last updated: 2026-04-22

---

## Design Context

| Document | Purpose | Status |
|----------|---------|--------|
| [UX_DISCOVERY_SESSION_2026-04-22.md](./UX_DISCOVERY_SESSION_2026-04-22.md) | Brand context, business goals, emotional tone, feature candidates | ✅ Complete |
| [ANTI_PATTERNS_RESEARCH.md](./ANTI_PATTERNS_RESEARCH.md) | What to avoid — AI slop, travel clichés, enterprise clutter | ✅ Complete |

**Key Design Principles:**
- **Precise** — Accurate data, no ambiguity
- **Efficient** — Fast workflows, minimal friction
- **Reassuring** — Agent feels supported and confident

**Emotional Tone:** NOT "user-friendly" — but **REASSURING**. The system should make agents feel confident, protected from mistakes, and supported during panic moments.

---

## Working Principles

| Principle | Application |
|-----------|-------------|
| **Long-term phased planning** | No "MVP" terminology — plan complete feature, implement phase by phase |
| **Documentation first** | Document decisions, rationale, and discussion for future reference |
| **Anti-pattern exploration** | Research and discuss what to avoid, not just what to build |
| **Design context gathering** | Understand brand, users, and emotional tone before designing |

---

## Feature Design Briefs

| Feature | Document | Status |
|---------|----------|--------|
| Owner Onboarding Flow | [DESIGN_BRIEF_Onboarding_Flow.md](./DESIGN_BRIEF_Onboarding_Flow.md) | ✅ Ready for implementation |
| Command Palette (Cmd+K) | [DESIGN_BRIEF_Command_Palette.md](./DESIGN_BRIEF_Command_Palette.md) | ✅ Ready for implementation |
| Quality/Confidence Indicators | — | ⏳ Pending |
| Customer Profile Sidebar | — | ⏳ Pending |
| Crisis Mode | — | ⏳ Pending |

---

## Implemented Features

| Feature | Document | Status |
|---------|----------|--------|
| Inbox Sorting (8 options, bidirectional) | [FEATURE_DOCUMENTATION.md](./FEATURE_DOCUMENTATION.md) | ✅ Complete |
| Multi-Currency Support (10 currencies) | [FEATURE_DOCUMENTATION.md](./FEATURE_DOCUMENTATION.md) | ✅ Complete |
| Editable Workspace Fields | [FEATURE_DOCUMENTATION.md](./FEATURE_DOCUMENTATION.md) | ✅ Complete |
| Smart Combobox (fuzzy matching) | [FEATURE_DOCUMENTATION.md](./FEATURE_DOCUMENTATION.md) | ✅ Complete |
| Field Change Logging / Audit Trail | [FEATURE_DOCUMENTATION.md](./FEATURE_DOCUMENTATION.md) | ✅ Complete |

Quick reference: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

---

## Design Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-22 | Palantir-inspired dark theme | Data-dense, serious, analytical tool for professionals |
| 2026-04-22 | Emotional tone = "Reassuring" | User rejected "user-friendly" framing; focus on confidence and support |
| 2026-04-22 | Command Palette as next feature | Aligns with "fast responses" goal and P1-S1 panic scenario |
| 2026-04-22 | No currency conversion (yet) | Focus on recording customer's stated currency |
| 2026-04-22 | Title case normalization for combobox | Prevents duplicates while allowing flexibility |
| 2026-04-22 | No "MVP" terminology | Long-term phased planning, not minimum viable approach |

---

## Persona Scenarios (Reference)

### P1: Solo Agent
- **S1:** 11 PM WhatsApp panic — needs instant access to any trip
- **S2:** Repeat customer forgot preferences — needs customer history
- **S3:** Creating quotes fast — needs efficiency

### P2: Agency Owner
- **S1:** Quote disaster (agent missed details) — needs quality indicators
- **S2:** Agent left with tribal knowledge — needs documentation/history
- **S3:** Business visibility — needs operational dashboard

### P3: Junior Agent
- **S1:** Is this quote right? — needs confidence/reassurance
- **S2:** What do I do next? — needs guidance
- **S3:** I made a mistake — needs undo/fix capabilities

---

## Anti-Patterns (Quick Reference)

### ABSOLUTE BANS
- ❌ Border-left stripes (`border-left: 4px solid ...`)
- ❌ Gradient text (`background-clip: text`)
- ❌ Glassmorphism everywhere
- ❌ Generic card grids
- ❌ Stock travel imagery (beaches, palms)

### AVOID
- Consumer booking site patterns
- Dashboard overwhelm (too many metrics)
- Notification spam
- Modal chains
- False confidence (hiding uncertainty)

### EMBRACE
- Data-dense displays
- Asymmetric layouts
- Progressive disclosure
- Inline editing
- Keyboard-first navigation

---

## Visual Style Reference

**Theme:** Dark, Palantir-inspired
**Typography:** TBD (font selection pending)
**Colors:** Dark background, high contrast, limited accents
**Layout:** Panel-based workspace, data-dense
**Motion:** Fast, purposeful, no bounce/elastic easing

---

## Implementation Roadmap

### Completed (Wave 1-2)
- Inbox sorting
- Multi-currency budget
- Editable fields with SmartCombobox
- Audit trail

### Next (Wave 3)

**Priority Re-evaluated:** Timeline/Story Panel now highest priority based on user feedback

1. **Trip Timeline Panel** — Phase 1: Foundation
   - Complete story from inquiry to current state
   - AI analysis trail with rationale
   - Conversation history
   - Decision timeline with reversals
   - Mock scenarios for demo

2. **Owner Onboarding Flow** — Phase 1: Foundation
   - Email + password signup
   - Immediate workspace access
   - Workspace code generation
   - Team invitation

3. **Command Palette (Cmd+K)** — Phase 1: Foundation
   - Global search across trips
   - Navigate to trip from search
   - Recent trips tracking
   - Core actions (New trip, Go to inbox)

4. **Quality/Confidence Indicators**
   - Progress bars for quote completeness
   - Validation badges
   - Confidence scores

5. **Customer Profile Panel**
   - Trip history
   - Preferences
   - Notes

### Planned (Wave 4+)
- Crisis Mode (emergency handling)
- Operational Dashboard
- Mobile adaptation
- Natural language queries

---

## Related Code

- `frontend/src/app/inbox/page.tsx` — Inbox with sorting
- `frontend/src/components/workspace/panels/IntakePanel.tsx` — Editable fields, SmartCombobox
- `frontend/src/components/ui/SmartCombobox.tsx` — Smart dropdown component
- `frontend/src/lib/combobox.ts` — Fuzzy matching utilities
- `frontend/src/lib/currency.ts` — Currency formatting
- `frontend/src/hooks/useFieldAuditLog.ts` — Audit trail hook
- `frontend/src/components/workspace/panels/ChangeHistoryPanel.tsx` — Change history UI

---

## File Structure

```
frontend/Docs/
├── UX_INDEX.md                              # This file
├── UX_DISCOVERY_SESSION_2026-04-22.md       # Design context discovery
├── ANTI_PATTERNS_RESEARCH.md                # What to avoid
├── DESIGN_BRIEF_Command_Palette.md          # Command Palette design
├── FEATURE_DOCUMENTATION.md                 # Implemented features reference
└── IMPLEMENTATION_SUMMARY.md                # Quick reference guide
```

---

**Note:** This index is maintained as part of the living documentation. Update as features are implemented and new design decisions are made.
