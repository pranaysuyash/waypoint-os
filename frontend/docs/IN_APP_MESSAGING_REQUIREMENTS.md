# In-App Messaging Requirements

**Date**: 2026-04-16
**Project**: Travel Agency Agent (TAA)
**Status**: Requirements gathering - Detailed discussion pending

---

## Problem Statement

Travel Agency Agent is an operational tool for travel agents. We need to communicate with operators **during their work** without disrupting their workflow. This is not about marketing popups - it's about operational communication and effective onboarding.

---

## Use Cases Identified

### 1. Onboarding New Operators
**Problem**: New operators don't know how to use the workbench effectively
**Need**: Guided introduction to the interface that doesn't feel like a tutorial

**Current state**:
- No onboarding flow
- Users must figure things out independently
- Inconsistent understanding of features

**Desired state**:
- First-time users get a contextual tour
- Can reference help materials while working
- Progressive disclosure of advanced features

---

### 2. Operational Updates
**Problem**: Operators need to know about system changes, protocol updates, incidents
**Need**: Real-time communication without interrupting active work

**Examples**:
- "Spine API experiencing delays, expect slower responses"
- "New safety protocol: All Moscow trips require manual review"
- "System maintenance in 30 minutes - save your work"
- "Feature released: You can now export trip summaries"

**Current state**:
- No in-app communication channel
- Updates likely via external channels (slack, email)
- Operators may miss critical information

---

### 3. Contextual Help
**Problem**: Operators forget what certain fields, tabs, or statuses mean
**Need**: Help available at the moment of need, without leaving the workflow

**Examples**:
- "What does 'confidence score' mean?" → Tooltip on hover
- "How do I handle incomplete itinerary data?" → Help panel
- "What's the difference between these decision states?" → Inline explanation

---

## Requirements (Tentative - To Be Discussed)

### Functional Requirements
- [ ] Show announcements at appropriate priority levels
- [ ] Onboard new users without annoying experienced ones
- [ ] Provide contextual help during work
- [ ] Remember what users have dismissed
- [ ] Don't interrupt during critical operations (spine running, form entry)

### Non-Functional Requirements
- [ ] Fast loading (messages shouldn't slow down the app)
- [ ] Accessible (keyboard nav, screen reader compatible)
- [ ] Mobile-friendly
- [ ] Respects user preferences

### Content Types Needed
| Type | Example Content | Priority | Owner |
|------|-----------------|----------|-------|
| System status | API delays, maintenance | High | Engineering |
| Protocol updates | New review rules, process changes | High | Operations |
| Feature announcements | New features, improvements | Medium | Product |
| Help content | Field explanations, process guides | Medium | Documentation |
| Onboarding | First-time user tours | High | Design |

---

## Open Questions for Detailed Discussion

1. **Who creates content?** Engineering? Operations? Dedicated content role?
2. **Approval process?** Who signs off on operational announcements?
3. **Content storage?** Database? CMS? Static files?
4. **Targeting rules?** By role? By tenure? By past behavior?
5. **Analytics?** What do we need to measure? How do we use the data?
6. **Existing tools?** Are we integrating with anything (e.g., Intercom, LaunchDarkly)?
7. **Mobile vs Desktop?** Different messaging strategies?
8. **Multi-language?** Do we support non-English operators?

---

## Design Considerations

### What "Deeply Integral" Means

Messages should be **part of the UI**, not layered on top:

- ✅ Announcement banner under header (part of layout)
- ✅ Tooltip that appears next to the thing it explains
- ✅ Help panel that slides in from existing margin
- ✅ Tour that highlights actual UI elements (fake overlay)

- ❌ Full-screen modal that blocks work
- ❌ Popup that appears after 5 seconds regardless of context
- ❌ Center overlay that must be dismissed before working

### Priority and Interruption

| Priority | Interruption Level | Example |
|----------|-------------------|---------|
| Critical | Stops work (rare) | "System shutting down in 5 min" |
| High | Noticeable but skippable | "New protocol for Russia trips" |
| Medium | Visible but non-blocking | "New feature available" |
| Low | On-demand only | Help panel, tooltips |

---

## Technical Approach (To Be Confirmed)

### Components Under Consideration
```
src/components/messaging/
├── AnnouncementBanner.tsx    # Top banner for updates
├── FeatureTour.tsx            # Step-by-step tour
├── Tooltip.tsx                # Inline help on hover
├── HelpPanel.tsx              # Collapsible reference
└── InlineCallout.tsx          # Tips in workflow
```

### State Management
- Track dismissed announcements (don't show again)
- Track completed tours (don't repeat)
- Track help panel open/closed state
- Sync with localStorage for persistence

### API Requirements
```
GET  /api/announcements      # Active announcements for user
POST /api/announcements/{id}/dismiss
GET  /api/help               # Help content for current page
POST /api/tours/{id}/complete
```

---

## Related Work

- **Design System**: Already has COLORS, ELEVATION tokens - can reuse
- **Accessibility**: Already have sr-only, focus management - leverage
- **Components**: Card, Button, Icon exist - build on them

---

## Next Steps

1. **Discuss requirements in detail** - Confirm use cases, priorities
2. **Define content workflow** - Who creates, approves, publishes?
3. **Review technical approach** - Any constraints or preferences?
4. **Design visual treatment** - How should it look/feel?
5. **Plan implementation** - Phased rollout, what to build first

---

## References

- Current UI Rating: 8.5/10 (just improved)
- Frontend: `/frontend/src/`
- Design Tokens: `/frontend/src/lib/tokens.ts`
- Accessibility: `/frontend/src/lib/accessibility.tsx`
