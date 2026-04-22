# Settings / Profile Exploration

**Date**: 2026-04-22
**Status**: Exploration
**Scope**: Clarify what a first real settings/profile surface should mean in the current frontend.

---

## Executive Summary

The current frontend has no route-level settings or profile destination. What exists today is a **workbench-only diagnostic drawer** for pipeline toggles, not a persistent account or agency configuration surface.

The missing capability is actually three separate products:

1. **Operator profile** — personal name, avatar, notification preferences, working defaults, signature/tone shortcuts.
2. **Agency settings** — brand, operating model, default channels, margin/tone/configuration.
3. **Team and access controls** — users, roles, permissions, assignment rules.

These should not be collapsed into a single undifferentiated page because they have different owners, different persistence needs, and different blockers.

---

## Current State Evidence

### Navigation

- `frontend/src/components/layouts/Shell.tsx` exposes only `Inbox`, `Workspaces`, `Overview`, `Pending Reviews`, `Analytics`, and `Workbench`.
- There is no `/settings`, `/profile`, `/account`, or `/agency` entry in the primary navigation.

### Existing "Settings"

- `frontend/src/app/workbench/SettingsPanel.tsx` is a right-side dialog labeled `Pipeline settings`.
- It controls only:
  - strict leakage check,
  - technical data visibility,
  - scenario selection.
- This is a QA/power-user control panel, not an account/settings experience.

### Route Surface

- Current app routes center on trip operations and owner analytics:
  - `/`
  - `/inbox`
  - `/workspace`
  - `/workspace/[tripId]/...`
  - `/owner/reviews`
  - `/owner/insights`
  - `/workbench`
- No route exists for operator identity or agency administration.

### Data and Persistence Constraints

- `frontend/src/stores/themeStore.ts` persists a small local preference set (`theme`, `componentVariants`, `density`), which means a local-only preferences surface is possible immediately.
- `frontend/src/types/governance.ts` already defines `UserRole` and `TeamMember` types, but they are not backed by real identity or auth enforcement yet.
- `Docs/DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md` confirms there is no real auth/session/user system yet.
- `Docs/DISCOVERY_GAP_CONFIGURATION_MANAGEMENT_2026-04-16.md` confirms per-agency settings are still a documented gap and recommends an agency settings entity.

---

## Product Interpretation

### What "Profile" Can Mean Right Now

**Can ship now without auth:**

- Display name / operator initials
- UI density and theme controls
- Personal working defaults
- Notification preference placeholders
- Default traveler-facing signature or tone presets

**Cannot be fully real yet without auth:**

- Secure password/email management
- Cross-device personal preferences tied to a user account
- Team-specific permissions scoped to a logged-in identity
- Invite, deactivate, or role-edit teammates

### What "Settings" Can Mean Right Now

**Best near-term fit:**

- Agency profile basics
- Market specialization and budget ranges
- Brand/tone defaults
- Channel defaults (WhatsApp/email)
- Operational defaults (hours, approval posture, review thresholds)

**Blocked or partial until backend matures:**

- Real margin policy computation tied to backend estimators
- Supplier whitelists with persistence
- Tenant-safe feature flags
- Full role-based access and approval policy enforcement

---

## Recommended Information Architecture

### Recommendation

Create a single top-level route for now:

- `/settings`

Inside it, split the page into clear sections/tabs:

1. **Profile**
2. **Agency**
3. **Workspace Preferences**
4. **Notifications**
5. **Team & Access** (disabled / coming soon unless auth lands first)

This avoids route sprawl while still separating concerns.

### Why This Is Better Than A Single Flat Form

- "Profile" and "Agency" have different owners.
- Local preferences can ship fast even if auth is missing.
- Agency configuration can become the canonical home for future backend settings.
- Team/access can be visibly planned without pretending it is functional yet.

---

## Sequencing Recommendation

### Phase 1 — Useful Immediately

Ship `/settings` with:

- Profile summary card
- Workspace preferences backed by local persisted store
- Agency basics form backed by mock/local state or existing API stubs
- Notification preferences as structured placeholders

### Phase 2 — Operationally Valuable

Add agency configuration tied to real backend storage:

- market focus
- budget bands
- brand voice
- operating hours
- approval defaults

### Phase 3 — Identity-Correct

After auth lands, upgrade:

- personal profile persistence
- role-aware nav visibility
- team invites / assignments / permissions
- audit trail for settings changes

---

## Recommended First Build

If only one page should be explored next, the best first version is:

### `/settings` v1

**Section 1: Operator Profile**

- name
- role badge
- preferred signature
- traveler communication style preset

**Section 2: Agency Basics**

- agency name
- primary market
- trip budget band
- specialties
- primary channels

**Section 3: Workspace Preferences**

- density
- theme/mode
- show technical data by default
- strict leakage default

**Section 4: Notifications**

- review-needed alerts
- assignment alerts
- daily summary

**Section 5: Team & Access**

- visible but marked as pending auth/identity implementation

---

## Decision Notes

- **ACCEPT**: Add a real route-level settings surface soon; the gap is user-visible and already referenced in product docs.
- **ACCEPT+MODIFY**: Treat "settings/profile" as one destination with multiple internal sections, not as a literal single-purpose profile page.
- **DEFER**: Full team/permissions management until auth and tenant-aware persistence are real.
- **REJECT**: Expanding the existing workbench settings drawer into the canonical app settings surface. It is scoped to QA/pipeline controls and lives in the wrong context.

---

## Open Questions

1. Is the first audience for this page the **agency owner**, the **everyday operator**, or both?
2. Should the first version optimize for **personal preferences** or **agency configuration**?
3. Do you want `/settings` to include **team/access** visibly from day one, even if disabled?
4. Should settings live as a quiet admin form, or as a more strategic "agency control center" page?
