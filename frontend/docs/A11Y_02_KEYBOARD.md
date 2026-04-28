# Accessibility & Assistive Technology — Keyboard Navigation

> Research document for keyboard-only navigation, focus management, skip links, and keyboard shortcuts.

---

## Key Questions

1. **How do we ensure full keyboard operability?**
2. **What focus management patterns are needed?**
3. **How do we handle focus in modals, panels, and dynamic content?**
4. **What keyboard shortcuts improve agent productivity?**
5. **How do we test keyboard accessibility?**

---

## Research Areas

### Keyboard Navigation Model

```typescript
interface KeyboardNavigation {
  tabOrder: TabOrderConfig;
  shortcuts: KeyboardShortcut[];
  focusManagement: FocusConfig;
  skipLinks: SkipLinkConfig;
}

interface TabOrderConfig {
  logical: boolean;                    // Tab order follows visual order
  rovingTabindex: RovingTabindexConfig[];
  focusTraps: FocusTrapConfig[];
}

// Tab order principles:
// 1. Tab order follows visual reading order (top-to-bottom, left-to-right)
// 2. Interactive elements only (links, buttons, inputs) receive focus
// 3. Non-interactive content is NOT in tab order (use headings for navigation)
// 4. Grouped controls use roving tabindex (only one item in group is tabbable)
// 5. Modal dialogs trap focus within the dialog
//
// Workbench tab order:
// 1. Skip to main content link
// 2. Main navigation (Inbox, Workbench, Settings)
// 3. Panel tabs (Intake, Trip, Output)
// 4. Active panel content
// 5. Context panel (if present)
// 6. Footer/status bar
//
// Roving tabindex patterns:
// - Panel tabs: Only active tab is tabbable, arrow keys switch tabs
// - Inbox trip list: Only focused trip is tabbable, arrow keys navigate
// - Toolbar buttons: First button tabbable, arrow keys move between
// - Radio groups: Only selected radio tabbable

interface KeyboardShortcut {
  key: string;                        // "Ctrl+K", "Escape", "/"
  action: string;                     // "Open command palette"
  context: ShortcutContext;
  category: ShortcutCategory;
}

type ShortcutContext =
  | 'global'                          // Works everywhere
  | 'workbench'                       // Only in workbench
  | 'inbox'                           // Only in inbox
  | 'trip_builder'                    // Only when editing trip
  | 'modal';                          // Only when modal is open

type ShortcutCategory =
  | 'navigation'                      // Moving between sections
  | 'actions'                         // Common actions
  | 'editing'                         // Text/content editing
  | 'search';                         // Finding things

// Keyboard shortcut map (inspired by Gmail/Linear):
//
// GLOBAL:
// Ctrl+K    → Command palette (search actions, trips, agents)
// /         → Focus search
// ?         → Show keyboard shortcuts help
// Escape    → Close modal / cancel action
// Ctrl+/    → Toggle sidebar
// g then i  → Go to Inbox
// g then w  → Go to Workbench
// g then s  → Go to Settings
// g then a  → Go to Analytics
//
// INBOX:
// j / k     → Next/previous trip
// Enter     → Open selected trip
// e         → Archive trip
// s         → Star/pin trip
// r         → Assign to me
// u         → Unassign
// f         → Forward to agent
// c         → Create new trip from inquiry
// 1-5       → Set priority (1=highest)
//
// TRIP BUILDER:
// Tab       → Next editable field
// Shift+Tab→ Previous editable field
// Ctrl+Enter → Save changes
// Ctrl+Shift+P → Publish to storefront
// Ctrl+B    → Add new component (block)
// Ctrl+D    → Duplicate selected component
// Delete    → Remove selected component
// Alt+↑/↓   → Move component up/down
//
// EDITING:
// Ctrl+Z    → Undo
// Ctrl+Shift+Z → Redo
// Ctrl+S    → Save draft
// Ctrl+Shift+S → Save and close
//
// MODAL:
// Escape    → Close modal
// Tab       → Next focusable element (trapped in modal)
// Enter     → Confirm primary action
//
// SHORTCUT CONFLICT AVOIDANCE:
// - Don't override browser shortcuts (Ctrl+T, Ctrl+W, Ctrl+L)
// - Don't override OS shortcuts (Alt+Tab, Ctrl+Alt+Del)
// - Single-key shortcuts only active when no input focused
// - Show shortcut hints in tooltips (e.g., "Save (Ctrl+S)")
```

### Focus Management

```typescript
interface FocusConfig {
  initialFocus: InitialFocusRule[];
  afterAction: PostActionFocusRule[];
  modals: ModalFocusConfig;
  routeChanges: RouteChangeFocusConfig;
  dynamicContent: DynamicFocusConfig;
}

// Focus management rules:
//
// Page load:
// - Focus on main content area (via skip link target)
// - NOT on the first interactive element (annoying for SR users)
//
// After opening modal:
// - Focus moves to first interactive element in modal
// - Tab trapped within modal (can't tab to background)
// - Escape closes modal
// - On close: Focus returns to trigger element
//
// After panel switch:
// - Focus moves to new panel content
// - Announce panel change via live region
// - "Switched to Trip Builder panel"
//
// After form submission:
// - Success: Focus on success message
// - Error: Focus on first error field
// - Warning: Focus on warning message
//
// After list action (archive, delete):
// - Focus moves to next item in list
// - If last item deleted: Focus on previous item
// - If list empty: Focus on "No items" message
//
// After dynamic content load:
// - Don't auto-focus loaded content (disorienting)
// - Announce via live region: "3 new trips loaded"
// - User can Tab to new content naturally
//
// Route changes (SPA navigation):
// - Focus on main content area
// - Announce new page: "Navigated to Trip Details"
// - Don't focus on skip link (surprising)

interface ModalFocusConfig {
  onOpen: FocusTarget;
  onClose: FocusTarget;
  trap: boolean;
  initialFocus: 'first-interactive' | 'primary-button' | 'specific-element';
}

// Modal focus trap implementation:
// 1. Record currently focused element (return target)
// 2. Move focus to modal container
// 3. Add event listeners for Tab and Shift+Tab
// 4. On Tab: If focus on last element, wrap to first element
// 5. On Shift+Tab: If focus on first element, wrap to last element
// 6. On Escape: Close modal, restore focus to return target
// 7. On overlay click: Close modal (optional, configurable)
//
// Nested modals:
// - Only innermost modal traps focus
// - Closing inner modal restores to outer modal
// - Max 2 levels of nesting (avoid confusion)
```

### Skip Links & Navigation Aids

```typescript
interface SkipLinkConfig {
  links: SkipLink[];
  visibility: SkipLinkVisibility;
}

interface SkipLink {
  target: string;                     // CSS selector or element ID
  label: string;                      // "Skip to main content"
  position: number;                   // Order in skip link chain
}

// Skip links (visible on Tab focus, hidden otherwise):
// 1. "Skip to main content" → <main> element
// 2. "Skip to navigation" → <nav> element
// 3. "Skip to trip builder" → Active panel content
// 4. "Skip to context panel" → <aside> element
//
// Implementation:
// - Skip links are the first focusable elements on the page
// - Visually hidden by default (clip + position off-screen)
// - Visible when focused (outline + background)
// - Keyboard: Tab from address bar → Skip link appears
// - Enter: Jump to target, focus on target element
//
// Breadcrumb navigation:
// - Home > Inbox > Trip: Kerala Backwaters
// - Each breadcrumb is a link (keyboard accessible)
// - aria-label="Breadcrumb"
// - aria-current="page" on last breadcrumb
//
// Page outline (accessibility helper):
// - Generated from heading hierarchy
// - Available via keyboard shortcut (?)
// - Lists all headings as clickable links
// - Allows quick navigation for screen reader users
// - "Page outline: 1. Trip Details, 2. Itinerary, 3. Pricing..."
```

---

## Open Problems

1. **Keyboard shortcut discoverability** — Users don't know shortcuts exist. Need discoverable shortcuts (hints in tooltips, command palette, cheat sheet).

2. **Complex panel navigation** — Multi-panel workbench with resizable panels, tabs within panels, and nested content is difficult to navigate with Tab key alone.

3. **Shortcut conflicts** — Different browsers and screen readers have their own keyboard shortcuts. Finding unique combinations that don't conflict is challenging.

4. **Focus restoration after async operations** — After a network request completes and UI updates, focus can be lost. Need to track and restore focus after async actions.

5. **Keyboard-only drag and drop** — Trip component reordering via drag-and-drop needs keyboard alternative (Alt+Arrow keys) with equivalent visual feedback.

---

## Next Steps

- [ ] Implement skip links and logical tab order across all pages
- [ ] Create keyboard shortcut system with command palette
- [ ] Build focus management for modals, panels, and route changes
- [ ] Design keyboard-only trip component reordering
- [ ] Study keyboard-first apps (Gmail, Linear, GitHub, Jira keyboard shortcuts)
