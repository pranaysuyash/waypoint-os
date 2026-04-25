# UI Research: Role-Aware Information Density

## 1. Research Goal
To define how the system visualizes the high-density data required for 'Operational Integrity' (Audit Signals, Supplier Risks, Fractional Invoicing) without overwhelming the user.

## 2. Key Concept: Persona-Based Density

### The 'Liquid Garden' (Owner/Operator View)
- **Persona**: The agency owner who needs "Wide & Shallow" visibility across 1,000 trips.
- **Visual Style**: Glassmorphism, vibrancy, and high-level health signals.
- **Research Features**:
  - **The Integrity Map**: A spatial visualization of all active trips. Trips "glow" red if the `IntegrityWatchdog` detects a drift.
  - **Supplier Health Layer**: A translucent overlay showing real-time risk scores for airlines/hotels currently in the pipeline.
  - **Mass-Action Command Bar**: A floating glass dock for triggered re-protection events (e.g., "Approve all re-bookings for displaced Travelers on LCC X").

### The 'Precision Inbox' (Agent View)
- **Persona**: The junior or senior agent focusing on "Narrow & Deep" execution for one trip at a time.
- **Visual Style**: High contrast, crisp lines, and atomic task focus.
- **Research Features**:
  - **The Split-Cost Canvas**: A drag-and-drop workspace for Multi-Party Reconciliation. Agents can "throw" segments into family-specific buckets.
  - **The Audit Sidebar**: A vertical ticker of "Adversarial Insights" (e.g., "Found $50 savings on this hotel segment").
  - **Crisis Mode UI**: When a trip hits a `CRITICAL` state, the UI desaturates all non-essential elements to focus exclusively on the recovery path.

---

## 3. Audit Signal Visualization
Researching how to display "Success" vs "Integrity Failure" signals.

| Signal | Logic | UI Representation |
| :--- | :--- | :--- |
| **Integrity Drift** | Data in `DashboardAggregator` != `AuditStore`. | "Static" or "Glitch" effect on the trip card. |
| **Supplier Risk** | Supplier on insolvency watch-list. | Pulsing amber border around the segment. |
| **Handoff Breach** | SLA expired for a critical review. | The "Dead Man's Switch" countdown timer (Persistent). |

---

## 4. Proposed Settings Extensions
Researching the "Operational Controls" for `SettingsPanel.tsx`:

- **Audit Verbosity**: (Low / Medium / Forensic)
- **Autonomic Recovery Budget**: (Slider: $0 - $1,000 per traveler)
- **Multi-Party Enforcement**: (Toggle: Prevent send without 100% split coverage)

---

## 5. Next Steps
- Create high-fidelity mockups of the **Split-Cost Canvas**.
- Research "Haptic" or "Audio" feedback for critical integrity alerts.
