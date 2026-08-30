# Waypoint OS — Comprehensive Navigation Architecture Audit & Specification

**Author:** Navigation Designer & Product Movement Architect  
**Target Application:** Waypoint OS (`travel_agency_agent`)  
**Date:** August 13, 2026  
**Status:** Canonical Reference Specification  
**Governing Doctrine:** `motto_v5.md` & First-Principles Navigation Engineering  

---

## Executive Summary & Core Mandate

The primary job of a **Navigation Designer** is not merely choosing between a sidebar or a topbar. It is designing the product's **movement system**: how users traverse product areas, objects, workspaces, task hierarchies, search results, settings, temporary contexts, and historical states without losing orientation.

In Waypoint OS — an AI-powered operating system for boutique travel agencies — navigation must seamlessly reconcile two distinct operating paradigms:
1. **High-Density Agency Operations Shell** (Desktop SaaS, multi-tenant RBAC, fast keyboard navigation, master-detail drawers, SLA urgency).
2. **Traveler & Public Wedge Surfaces** (Cartographic dark public itinerary checker, tokenized proposals, public intake collection).

This document presents a complete, 10-layer audit and architectural specification of Waypoint OS. It evaluates product topology, addressability, deep linking, browser history fidelity, object-centric context preservation, role-based scoping, and responsive navigation transformations.

---

## 1. Product Topology & Conceptual Spaces

Waypoint OS consists of **4 primary conceptual environments**, each serving a specific user persona and interaction model.

```text
Waypoint OS
├── 1. Agency Workspace Shell (Protected SaaS, /app/(agency))
│   ├── Command Area
│   │   ├── Overview (/overview)
│   │   ├── Lead Inbox (/inbox)
│   │   └── Quote Review (/reviews)
│   ├── Planning Area
│   │   ├── Trips in Planning (/trips)
│   │   │   └── Trip Workspace (/trips/[tripId])
│   │   │       ├── Intake Tab (/intake)
│   │   │       ├── Packet Tab (/packet)
│   │   │       ├── Decision Tab (/decision)
│   │   │       ├── Output/Proposal Tab (/output)
│   │   │       ├── Ops & Booking Tab (/ops)
│   │   │       ├── Followups Tab (/followups)
│   │   │       └── Timeline Tab (/timeline)
│   │   ├── Quotes (/quotes - Rollout Gate)
│   │   └── Bookings (/bookings - Rollout Gate)
│   ├── Operations Area
│   │   ├── Documents (/documents)
│   │   ├── Payments (/payments)
│   │   └── Suppliers (/suppliers - Rollout Gate)
│   ├── Intelligence Area
│   │   ├── Insights (/insights)
│   │   ├── Audit (/audit)
│   │   └── Knowledge Base (/knowledge - Rollout Gate)
│   └── Admin Area
│       ├── Settings (/settings)
│       └── Seasonal Campaigns (/seasons)
├── 2. Public Traveler Wedge (Unauthenticated / Public, /app/(traveler))
│   └── Public Itinerary Checker (/itinerary-checker)
├── 3. Public Shared Artifact Viewers (Tokenized / Public, /app/(public) & root dynamic)
│   ├── Interactive Proposal Viewer (/p/[token] or /proposals/[proposalId])
│   ├── Shared Itinerary Gateway (/g/[token])
│   └── Public Passenger Collection (/booking-collection/[agencyId]/[token])
└── 4. Corporate Portal (Enterprise Client, /app/corporate)
    └── Offsites & Group Travel (/corporate/offsites)
```

---

## 2. Information Architecture vs. Navigation Routes

| Conceptual Space | Information Architecture (IA) | Navigation Route (URL / Route) | Navigation Mechanism |
|---|---|---|---|
| **Lead Inbox** | Command → Lead Inbox | `/inbox` | Sidebar Item, `⌘K` Palette |
| **New Inquiry Action** | Command → Intake Workflow | `/workbench` (Target: `/inquiries/new`) | Primary Shell CTA Button |
| **Active Trip Context** | Planning → Trips → [Trip] | `/trips/[tripId]` | Sidebar Context Card, Table Row |
| **Trip Intake Detail** | Planning → Trip → Intake | `/trips/[tripId]/intake` | Local Sub-tab Bar |
| **Document Vault** | Operations → Documents | `/documents` | Sidebar Item |
| **Public Proposal** | Shared Artifact → Proposal | `/p/[token]` | Deep Link, Email/WhatsApp Link |
| **Agency Settings** | Admin → Settings | `/settings` | User Menu Dropdown, Sidebar |

---

## 3. Primary, Secondary & Local Navigation System

### 3.1 Primary Navigation (App Shell Sidebar)
The primary navigation persists across all agency operational pages inside `Shell.tsx` using `NAV_SECTIONS` defined in `src/lib/nav-modules.ts`.

- **`COMMAND`**: High-frequency triage (`/overview`, `/inbox`, `/reviews`).
- **`PLANNING`**: Lifecycle execution (`/trips`, `/quotes`, `/bookings`).
- **`OPERATIONS`**: Compliance & fulfillment (`/documents`, `/payments`, `/suppliers`).
- **`INTELLIGENCE`**: Performance analytics & audit (`/insights`, `/audit`, `/knowledge`).
- **`ADMIN`**: Governance & configuration (`/settings`, `/seasons`).

### 3.2 Progressive Disclosure & Rollout Gates
Modules that are architecturally defined in the domain model but undergoing staged rollout (e.g., `Quotes`, `Bookings`, `Suppliers`, `Knowledge Base`) are rendered in the sidebar with `enabled: false`. 

> [!TIP]
> **Wayfinding Best Practice:** Rendering planned modules with a subtle "Soon" badge reinforces the agency mental model without leading users to 404 dead-ends. Touch/click triggers on disabled items display a non-blocking toast explaining the module status.

### 3.3 Contextual "Current Trip" Anchor (`SidebarTripContext`)
Inside `Shell.tsx`, when an operator navigates within a specific trip context (`/trips/[tripId]/*`), the sidebar dynamically renders a **Current Trip Context Card** (`SidebarTripContext`).
- **Visual Tone**: Status-coded border and background (`green` on-track, `amber` at-risk, `red` breached SLA).
- **Wayfinding Information**: Displays trip title, SLA badge, next required operator action, and direct action link.
- **Context Preservation**: Allows switching to global sections (e.g. `/payments` or `/documents`) while keeping the active trip context visible and single-click returnable.

---

## 4. Object-Centric vs. Feature-Centric Hybrid Model

Waypoint OS uses a **hybrid navigation model**:

```text
GLOBAL FEATURE NAVIGATION            CONTEXTUAL OBJECT NAVIGATION
/inbox   ──────(Click Lead)──────►   /trips/8f92-uuid/intake
/trips   ──────(Click Row)───────►   /trips/8f92-uuid/ops
/payments ────(Click Trip Ref)───►   /trips/8f92-uuid/output
```

- **Global Feature Navigation**: `/trips`, `/inbox`, `/payments`, `/documents` allow cross-cutting administrative tasks (e.g. "Show all breached SLA payments across the agency").
- **Contextual Object Navigation**: Sub-pages under `/trips/[tripId]` bind the UI to a specific trip entity (`TripContextProvider`). Local tabs (`Intake`, `Packet`, `Decision`, `Output`, `Ops`, `Followups`, `Timeline`) let the operator refine, review, and execute without losing object identity.

---

## 5. URL Deep Linking & State Preservation Matrix

> [!IMPORTANT]
> **State Preservation Principle:** Returning to a page must return the user to where they left it. Query parameters, search filters, pagination, and selected tabs MUST be reflected in the URL.

| UI Surface / Component | State Variable | Current Storage | Target Canonical URL Pattern | Browser History Action |
|---|---|---|---|---|
| **Lead Inbox Table** | Active Tab Filter (`unassigned`, `needs_action`, `at_risk`) | Component State | `/inbox?filter=needs_action` | Push / Replace State |
| **Lead Inbox Table** | Search Query (`q`) | Component State | `/inbox?q=Santorini` | Replace State (Debounced) |
| **Lead Inbox Table** | Pagination (`page`) | Component State | `/inbox?page=2` | Push State |
| **Trips Workspace** | Status Filter (`discovery`, `shortlist`, `proposal`) | Component State | `/trips?status=proposal` | Replace State |
| **Trip Detail View** | Active Step Tab (`intake`, `decision`, `ops`) | Route Path | `/trips/[tripId]/ops` | Push State |
| **Documents Vault** | Document Type Filter (`passport`, `visa`, `voucher`) | Component State | `/documents?type=passport` | Replace State |
| **Documents Vault** | Selected Document Drawer | Component State | `/documents?docId=doc_123` | Push State (Enables sharing doc link) |
| **Agency Settings** | Active Tab (`profile`, `rules`, `users`, `integrations`) | Local State | `/settings?tab=users` | Replace State |
| **Insights Analytics** | Date Range / Timeframe | Component State | `/insights?range=30d` | Replace State |
| **Public Proposal** | Proposal Access Token | URL Parameter | `/p/[token]` | Direct Entry Point |

---

## 6. Global, Local & Command Navigation Architecture

### 6.1 Persistent Top Command Bar (`Shell.tsx`)
- **Breadcrumb Navigator**: Generates human-readable breadcrumbs (e.g., `Waypoint OS / Trips in Planning / Trip #8F92 / Ops & Booking`) using `getPageLabel`. Sanitizes internal route names (e.g., `/workbench` renders as `New Inquiry`).
- **System Health & Runtime Indicator**: Live badge reflecting API connectivity and system build version (`v0.1.0-alpha`).
- **User Avatar & Quick Action Dropdown (`UserMenu.tsx`)**: Displays user name, role badge (`Owner`, `Admin`, `Senior Agent`), agency name, and direct actions (`Agency Profile`, `Settings`, `Keyboard Shortcuts`, `Sign Out`).

### 6.2 Command Palette (`⌘K`)
- **Global Hotkey**: Bound via `useHotkey('k', togglePalette)` across the entire application shell.
- **Actions Supported**:
  - Direct navigation to any active route (`Overview`, `Inbox`, `Trips`, `Documents`, `Payments`, `Settings`).
  - Search trips by traveler name or ID.
  - Action triggers: `New Inquiry`, `Upload Document`, `Run AI Pipeline`.

---

## 7. Multi-Tenant & Role-Based Navigation Scoping

### 7.1 Multi-Tenant Isolation
- **Backend Enforcer**: `FastAPI` dependency `get_current_agency_id` coupled with Postgres Row-Level Security (RLS) policies on `trips`, `booking_tasks`, `booking_confirmations`, and `booking_documents`.
- **Frontend Hydration**: `AuthProvider` rehydrates session data (`AuthUser`, `AuthAgency`, `AuthMembership`) on app mount via `/api/auth/me`.

### 7.2 Role-Based Navigation Scoping Matrix

| Product Area / Route | `agency_owner` | `agency_admin` | `agent` (Senior/Junior) | `traveler` (Customer) |
|---|---|---|---|---|
| `/overview` | Full Access | Full Access | Full Access | No Access (Redirect) |
| `/inbox` | Full Access | Full Access | Full Access | No Access |
| `/trips/*` | Full Access | Full Access | Full Access (Assigned/Agency) | No Access |
| `/documents` | Full Access | Full Access | Full Access | No Access |
| `/payments` | Full Access (View/Edit) | Full Access (View/Edit) | Limited (View/Collect) | No Access |
| `/insights` | Full Access | Full Access | Team View Only | No Access |
| `/audit` | Full Access | Full Access | Self Audit Only | No Access |
| `/settings` | Full Access | Full Access | Profile Only | No Access |
| `/seasons` | Full Access | Full Access | View Only | No Access |
| `/p/[token]` (Proposal) | Full Access | Full Access | Full Access | Interactive View |
| `/itinerary-checker` | Public Access | Public Access | Public Access | Public Access |

---

## 8. Asynchronous & Long-Running Workflow Navigation

Long-running asynchronous processes (such as multi-stage AI itinerary generation, DMC rate ingestion, and OCR document extractions) require robust wayfinding so users do not feel trapped on a loading screen.

```text
USER ACTION                 BACKGROUND ENGINE                 NAVIGATION STATE
POST /run             ───►  RunLedger (run_id)         ───►  /runs/[run_id] (SSE Stream)
                            - Step 1: Packet Checkpoint        - Non-blocking notification banner
                            - Step 2: Validation Checkpoint    - Operator can navigate away
                            - Step 3: Decision Checkpoint      - Re-entry via Sidebar Trip Context
POST /documents/extract ─►  DocumentExtractionAttempt  ───►  /documents?docId=123&status=extracting
```

1. **Non-Blocking Execution**: Initiating an AI run from `/workbench` or `/trips/[id]/intake` returns an immediate `run_id`.
2. **Re-entry Gateways**:
   - Live SSE stream widget in the topbar or sidebar context card.
   - Run Status Route (`/runs/[run_id]`) inspectable via `GET /runs/{run_id}/steps/{step_name}`.
   - Activity feed link in `/trips/[tripId]/timeline`.

---

## 9. Responsive & Mobile Navigation Model

Desktop high-density navigation does not scale to mobile screens by simply shrinking font sizes or placing everything behind a hamburger menu.

```text
DESKTOP NAVIGATION (≥ 768px)               MOBILE NAVIGATION (< 768px)
┌──────────┬────────────────────────┐      ┌────────────────────────────────┐
│ Sidebar  │ Top Command Header     │      │ Header (Logo + Search ⌘K)      │
│ (240px)  ├────────────────────────┤      ├────────────────────────────────┤
│          │ Main Content Area      │      │ Main Content Area (Fluid)      │
│          │                        │      ├────────────────────────────────┤
│          │                        │      │ Bottom Navigation Bar (Fixed)  │
│          │                        │      │ [Inbox] [Trips] [New] [Doc] [⚙]│
└──────────┴────────────────────────┘      └────────────────────────────────┘
```

- **Desktop (≥ 768px)**: 240px fixed left sidebar with persistent categories, collapsible context card, and sticky header.
- **Mobile (< 768px)**:
  - Sidebar collapses into a fixed **5-Item Bottom Navigation Bar** (`Inbox`, `Trips`, `New Inquiry`, `Documents`, `Settings`).
  - Full-screen sheet drawers for complex master-detail inspection (e.g. document extraction or trip decision overrides).
  - Touch targets enforced at minimum 44×44px.

---

## 10. Navigation Smell Catalog & Remediation Plan

Our baseline audit identified **10 specific navigation smells** in the codebase, accompanied by exact remediation plans:

### Smell 1: Route vs. Module Semantic Mismatch (`/workbench`)
- **Issue**: The primary shell CTA button ("New Inquiry") routes to `/workbench`. In `nav-modules.ts`, comments acknowledge `/workbench` is a temporary route name.
- **Remediation**: Create canonical route `/inquiries/new` rendering the intake wizard, with `/workbench` maintaining backwards-compatible redirect.

### Smell 2: Un-persisted Table Filters & Search State
- **Issue**: `/inbox`, `/trips`, and `/documents` store search query (`q`) and active filter tabs in React local state. Refreshing the browser resets the view.
- **Remediation**: Refactor tab selection and search filters to bind to Next.js `useSearchParams()` and `useRouter.push(..., { scroll: false })`.

### Smell 3: Deep Document Drawer Lacks Addressability
- **Issue**: Opening a document detail drawer on `/documents` does not update the URL. Operators cannot share a direct link to a specific passport/visa extraction for review.
- **Remediation**: Append `?docId={document_id}` to URL upon drawer open; hydrate drawer on direct page load if `docId` is present.

### Smell 4: Settings Tabs Missing URL Binding
- **Issue**: Switching between `Profile`, `Agency Rules`, `Users`, and `Integrations` in `/settings` uses React local state.
- **Remediation**: Bind settings tabs to `?tab=users` query parameter.

### Smell 5: Missing Back Button on Deep Trip Sub-pages
- **Issue**: Navigating directly to `/trips/[tripId]/ops` via an email link lacks an explicit top-level "Back to Trips" button if breadcrumbs are missed.
- **Remediation**: Standardize `BackToOverviewLink` component across all sub-pages under `/trips/[tripId]/*`.

### Smell 6: Unlinked Notification Targets
- **Issue**: System error banner ("CRITICAL: Data inconsistency detected") lacks a direct diagnostic navigation action.
- **Remediation**: Add explicit link `Inspect Audit Log` (`/audit?issueId=...`) to system toast and notification alerts.

### Smell 7: Modal vs. Page Navigation Discrepancies
- **Issue**: Creation of workspace codes or DMC supplier holds opens non-addressable modals.
- **Remediation**: Ensure modals that initiate multi-step flows support URL query triggers (`?modal=new-supplier-hold`).

### Smell 8: Duplicate Destination Routes (`/knowledge` vs `/knowledge-base`)
- **Issue**: Folder structure contains both `src/app/(agency)/knowledge/` and `src/app/(agency)/knowledge-base/`.
- **Remediation**: Consolidate route architecture to `/knowledge` and add 301 redirect for `/knowledge-base`.

### Smell 9: Un-scoped Mobile Menu Drawer Focus Lock
- **Issue**: On small viewports, opening mobile menu sheet does not trap focus correctly for keyboard/screen-reader users.
- **Remediation**: Implement `focusNextOutside` trap and `aria-expanded` states on mobile drawer trigger inside `Shell.tsx`.

### Smell 10: Inconsistent Search Result Context Retention
- **Issue**: Using `⌘K` command palette to navigate to a trip resets current filters on destination page.
- **Remediation**: Pass previous route context in router state so browser back returns operator to filtered search list.

---

## Deliverables & Sign-Off

1. **`NAVIGATION_DESIGN_AUDIT.md`**: Master Audit & Navigation Architecture Specification (this document).
2. **`NAVIGATION_TASKS.md`**: Granular Task Tracking & Action Item Register.
3. **`walkthrough.md`**: Verification Summary & Architectural Artifact.
