# Settings Dashboard Specification (Draft)

**Status**: Planning / Prototyping
**Relationship to newer docs**: This draft is now subordinate to `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md` and should be reconciled with the canonical governance docs rather than treated as an independent source of truth.
**Goal**: Centralize agency configuration, autonomy control, and persona management in a non-binding, extensible UI.

---

## 1. Design Principles (Adaptable & Scalable)
*   **Modular Architecture**: Each section (Autonomy, Operational, Persona) is a standalone component. Adding new settings should not require modifying the entire dashboard.
*   **API-Driven State**: The UI reads from `AgencySettings` and pushes updates via PATCH/POST.
*   **"Draft & Publish" Workflow**: Configuration changes are applied in-memory, then persisted only when "Save Changes" is triggered.

---

## 2. Dashboard Structure

### A. Autonomy (The D1 Gradient)
A visualization of the Autonomy Policy gates.
- **Decision Matrix**: A grid mapping `decision_state` (e.g., `PROCEED_TRAVELER_SAFE`) to `Gate Action` (`auto`, `review`, `block`).
- **Mode Overrides**: Toggle emergency overrides (e.g., "Force all to Review in Emergency mode").
- **Suitability Settings**: Simple toggle for `auto_proceed_with_warnings`.

### B. Operational Parameters
- **Hours & Channels**: Editable fields for `operating_hours`, `operating_days`, and multi-select for `preferred_channels`.
- **Financials**: `target_margin_pct` input with basic validation.

### C. Persona & Brand
- **Tone Selector**: Dropdown selection for `brand_tone` (e.g., `cautious`, `professional`, `confident`).
- **Contextual Knowledge**: Placeholder area for managing "Agency Knowledge" (link to current Playbooks).

---

## 3. Implementation Roadmap

### Phase 1: Read-Only Integration
- [ ] Create `api/settings/get` endpoint that returns full `AgencySettings` (combining Autonomy + Operational).
- [ ] Implement `SettingsDashboard` shell in `frontend/src/app/settings/page.tsx`.
- [ ] Build readonly UI for all fields.

### Phase 2: Configuration Persistence
- [ ] Implement UI for `AutonomyPolicy` updates (Decision Matrix).
- [ ] Implement UI for `OperationalParameters` (Hours, Channels).
- [ ] Add "Save" feedback loop (pending changes indicators).

### Phase 3: Persona Extensibility
- [ ] Integrate agent persona fields (tone, language, specific constraints).

---

## 4. Scalability Notes
- **Extensibility**: When new settings are added to `AgencySettings` (e.g., `webhook_urls`, `integration_keys`), the dashboard should dynamically generate the form via a `SettingsRegistry` approach.
- **Security**: Autonomy settings are gated via RBAC (Owner-only). Dashboard visibility will be checked server-side.
