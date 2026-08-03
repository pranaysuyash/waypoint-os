# Corporate Travel Manager (EA) Workflows & B2B DMC Supplier Portal Paradigm

**Date**: 2026-08-03  
**Status**: EXPLORATION & MULTI-ROLE BRAINSTORM (Uncommitted per User Directives)  
**Authors**: Antigravity & User (Multi-Subagent Brainstorm Pass)  
**Governing Rule**: `motto_v4.md` (ADR-First, §0.12 Decision Record Requirement, Non-Destructive Documentation Preservation)

---

## 1. Executive Summary & Core Architectural Principle

Waypoint OS expands beyond consumer travel agencies and social creators to serve two high-value institutional segments:
1. **Corporate Travel Managers & Executive Assistants (EAs)**: Managing executive offsites, board meetings, and multi-employee travel.
2. **B2B Destination Management Companies (DMCs) & Preferred Suppliers**: Uploading contracted wholesale rates, seasonal blackout dates, and package inventory directly to agencies.

### `motto_v4` Rule 0 (Zero Shadow Pipelines)
Crucially, these domains do **not** introduce separate database structures, shadow pipelines, or parallel AI routing engines. They leverage the exact same canonical core architecture:
- **Canonical Intake & Workspace Pipeline**: `src/intake/lifecycle.py`, `src/intake/decision.py`, `spine_api/persistence.py` (`TripStore`, `AuditStore`).
- **Autonomic Monitoring Engine**: `spine_api/routers/concierge.py`.
- **Yield & Margin Engine**: `spine_api/routers/yield_arbitrage.py`.

---

## 2. Multi-Role Brainstorm Synthesis (Wide-Open Brainstorm Pass)

Using the **Wide-Open Brainstorming Framework**, six distinct perspective roles evaluated the Corporate EA and B2B DMC Supplier domain:

### A. Strategist Role (Product Thesis & Positioning)
- **Thesis**: Mid-sized corporate accounts ($500k–$5M annual travel spend) are currently underserved. Enterprise legacy tools (SAP Concur) cost $400/user/year while lacking real-time disruption assistance and net-margin supplier transparency.
- **Positioning**: Waypoint OS offers a lightweight, policy-enforced corporate workspace that unifies executive travel intake, Duty-of-Care flight monitoring, and wholesale DMC rates without enterprise bloat.

### B. Operator Role (Day-to-Day Mechanics & Workflows)
- **EA Daily Workflow**: EA inputs 15 executive travelers for a Zurich board offsite $\rightarrow$ Corporate Policy Engine audits flight cabin classes and per-diem hotel caps (£350/night London) $\rightarrow$ Non-compliant choices trigger a 1-click EA self-justification or VP approval workflow.
- **DMC Daily Workflow**: DMC supplier logs into `/supplier/contracts` $\rightarrow$ uploads net wholesale rate sheet $\rightarrow$ Waypoint OS verifies agency yield margin vs retail MSRP.

### C. Skeptic Role (Failure Modes & Bloat Warnings)
- **Failure Mode 1 (Over-Engineered Policy Bloat)**: Complex nested corporate travel policies (e.g. 50 different per-diem rules by seniority) turn the platform into a bloated enterprise compliance tool.
  *Mitigation*: Implement 3 standardized per-diem tiers (`JUNIOR`, `MANAGER`, `EXECUTIVE`) with simple city cap overlays.
- **Failure Mode 2 (DMC Portal Abandonment)**: DMCs will refuse to fill complex 40-field web forms to list packages.
  *Mitigation*: Provide 1-click CSV/Excel upload with AI column auto-mapping (`/api/v1/supplier/contracts/upload`).

### D. Executioner Role (Shortest Path to MVP)
- **Minimal Corporate MVP**:
  1. Corporate Policy Audit Endpoint (`POST /api/v1/corporate/policy-audit`).
  2. Multi-Executive Group Monitor (`POST /api/v1/concierge/group-monitor/{group_id}`).
  3. Consolidated Corporate Invoice Exporter.
- **Minimal DMC MVP**:
  1. Supplier CSV Upload Endpoint (`POST /api/v1/supplier/contracts/upload`).
  2. Yield Arbitrage Verification (`GET /api/v1/yield/arbitrage/{trip_id}`).

---

## 3. Concrete Data Models (`pydantic`)

### A. Corporate Policy Enforcer Data Models
```python
from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel

class EmployeeGrade(str, Enum):
    JUNIOR = "JUNIOR"
    MANAGER = "MANAGER"
    VP = "VP"
    C_EXEC = "C_EXEC"

class CabinClass(str, Enum):
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"

class GeoPerDiemCap(BaseModel):
    city_code: str  # e.g., "LON", "NYC", "ZRH"
    currency: str = "GBP"
    max_hotel_rate_per_night: float  # e.g. 350.0 for London
    max_meal_per_diem: float         # e.g. 75.0 per day

class CorporatePolicyRules(BaseModel):
    policy_id: str
    company_id: str
    policy_name: str
    geo_caps: List[GeoPerDiemCap]
    cabin_class_matrix: Dict[EmployeeGrade, Dict[str, CabinClass]]
    preferred_hotel_chains: List[str] = ["Marriott", "Taj", "Hyatt"]
    require_manager_approval_threshold_gbp: float = 500.0
    strict_policy_mode: bool = False

class PolicyViolation(BaseModel):
    code: str  # "PER_DIEM_EXCEEDED", "CABIN_CLASS_DISCREPANCY"
    severity: str  # "WARNING", "HARD_BLOCK"
    description: str
    amount_exceeded: float
    currency: str

class PolicyEnforcementResult(BaseModel):
    trip_id: str
    is_compliant: bool
    requires_approval: bool
    violations: List[PolicyViolation]
    audited_at: str
```

### B. B2B DMC Wholesale Rate Contract Models
```python
class RateType(str, Enum):
    NET_WHOLESALE = "NET_WHOLESALE"
    COMMISSIONABLE_RETAIL = "COMMISSIONABLE_RETAIL"

class ContractedPackageItem(BaseModel):
    package_id: str
    supplier_id: str
    destination: str
    title: str
    inclusions: List[str]
    retail_msrp: float
    net_wholesale_rate: float
    contracted_commission_pct: float
    currency: str = "USD"
    blackout_dates: List[str]
    inventory_allocation: int
    soft_hold_window_hours: int = 48

class SupplierContractUpload(BaseModel):
    supplier_id: str
    supplier_name: str
    contract_ref: str
    valid_from: str
    valid_to: str
    rate_type: RateType
    packages: List[ContractedPackageItem]
```

---

## 4. API Endpoints Specification

| Category | Endpoint Route | HTTP Method | Description |
| :--- | :--- | :--- | :--- |
| **Corporate Policy** | `/api/v1/corporate/policies` | `GET / POST` | Manage company per-diem caps and cabin class rules. |
| **Corporate Policy** | `/api/v1/corporate/policy-audit` | `POST` | Audit a proposal against corporate policies. |
| **Corporate Override** | `/api/v1/corporate/overrides/request` | `POST` | EA request for per-diem or cabin policy exception. |
| **Corporate Override** | `/api/v1/corporate/overrides/approve` | `POST` | Manager/VP approval for pending policy override. |
| **Duty-of-Care** | `/api/v1/corporate/duty-of-care/cockpit` | `GET` | EA Duty-of-Care dashboard with live traveler statuses. |
| **Flight Sync** | `/api/v1/corporate/offsites/sync/{group_id}`| `GET` | Multi-executive arrival window & shuttle sync state. |
| **Concierge Group** | `/api/v1/concierge/group-monitor/{group_id}`| `POST` | Group offsite disruption watcher and cascade engine. |
| **Supplier Inventory**| `/api/v1/supplier/contracts/upload` | `POST` | DMC wholesale rate sheet and package ingestion. |
| **Supplier Inventory**| `/api/v1/supplier/inventory/soft-hold` | `POST` | Reserve a 48h zero-cost soft hold on DMC inventory. |
| **Yield Arbitrage** | `/api/v1/yield/arbitrage/{trip_id}` | `GET` | Verify DMC net wholesale yield vs GDS/Bedbank rates. |

---

## 5. Master Pending Decisions Inventory (Decisions 14–17)

- [ ] **Pending Decision 14 (Corporate EA Surface Route)**: Dedicated workspace route (`/corporate/offsites`) vs shared Workbench toggle.
- [ ] **Pending Decision 15 (Corporate Policy Override Workflow)**: Mandatory manager approval for policy exceptions vs EA self-justification note.
- [ ] **Pending Decision 16 (DMC Rate Sheet Ingestion)**: Native web supplier portal (`/supplier/portal`) vs AI Excel rate sheet parser.
- [ ] **Pending Decision 17 (DMC Payout Settlement)**: Direct GDS settlement vs 30-day corporate invoice invoicing.

---

## 6. Autonomic Agentic Flow & Manual Switch Integration

```
+-----------------------------------+     +-----------------------------------+
|  EA Duty-of-Care Cockpit          | --> | Ghost Concierge Disruption Engine |
|  (GET /corporate/duty-of-care)    |     | (POST /concierge/group-monitor)   |
+-----------------------------------+     +-----------------------------------+
                  |                                         |
                  v                                         v
+-----------------------------------+     +-----------------------------------+
|  Manual Takeover Switch           |     | Yield & Commission Arbitrage      |
|  (Pause Auto-Rebook / EA Control) |     | (Wholesale Rate Optimization)     |
+-----------------------------------+     +-----------------------------------+
```

- **Autonomic Flight Disruption Watcher**: The Ghost Concierge background monitor (`spine_api/routers/concierge.py`) queries real-time flight statuses for multi-executive offsites. Upon detecting flight delays (e.g. Flight LX18 delayed by 45m), the agent calculates impact on shared airport shuttles and hotel check-in windows.
- **Automated Ground Transfer Rescheduling**: If the flight delay causes executive arrivals to miss scheduled shuttles, the agent reschedules ground transfers or alerts hotel concierge.
- **Manual Takeover Switch (`[ ⚡ TAKEOVER ]`)**: Executive Assistants (EAs) and Tour Operators can toggle manual takeover at any time from `/corporate/offsites`. This immediately pauses automated solver actions, preserving full human operational control.

---

## 7. Update Log (Append-Only)

- **2026-08-03**: Documented Corporate EA & DMC Supplier paradigm based on 4-role wide-open brainstorm pass. Appended Autonomic Agentic Workflows and Manual Takeover Switch specifications (`motto_v4` §0.3.1).


