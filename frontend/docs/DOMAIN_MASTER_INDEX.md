# Core Domain Model Foundation — Master Index

> Bridging research: unified data model layer connecting all subsystem research into coherent entity, workflow, event, and API contract definitions.

---

## Series Overview

This series bridges the gap between 100+ exploration research documents and implementation. It defines the canonical domain models that all subsystems depend on — entities, workflows, events, and API contracts — as a coherent foundation for Pydantic (backend) and TypeScript (frontend) implementation.

**Target Audience:** Backend engineers, frontend engineers, data architects, API designers

**Key Constraint:** The existing codebase uses Trip as the central entity. This series proposes splitting Trip into Enquiry + Trip + Booking while maintaining backward compatibility.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [DOMAIN_01_ENTITIES.md](DOMAIN_01_ENTITIES.md) | Core entities: Enquiry, Booking, Buyer, HumanAgent, Vendor, Payment |
| 2 | [DOMAIN_02_WORKFLOWS.md](DOMAIN_02_WORKFLOWS.md) | Workflow state machines: Ingestion, Triage, Communication, Fulfillment, Disruption |
| 3 | [DOMAIN_03_EVENTS.md](DOMAIN_03_EVENTS.md) | Event sourcing, event taxonomy, projections, CQRS |
| 4 | [DOMAIN_04_CONTRACTS.md](DOMAIN_04_CONTRACTS.md) | REST API contracts, BFF proxy, validation, WebSocket events |

---

## Key Themes

### 1. Entity Separation
Enquiry (inquiry phase), Trip (planning phase), and Booking (reserved phase) are distinct entities with different state machines, not states within a single Trip model.

### 2. Workflow-Driven Architecture
Every entity transition is governed by a workflow state machine with typed transitions, guard conditions, and trigger events. No entity changes state without a corresponding workflow event.

### 3. Event-Sourced Audit Trail
All state changes produce domain events that form an immutable audit trail. Projections derive read-optimized views from the event stream.

### 4. Contract-First API Design
API contracts are defined as TypeScript types that generate both Pydantic models (backend) and API client types (frontend). Validation rules are shared across the stack.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Lead Management (LEAD_*) | Enquiry entity, ingestion workflow |
| Booking Engine (BOOKING_ENGINE_*) | Booking entity, fulfillment workflow |
| CRM (CRM_*) | Buyer entity, customer 360 projection |
| Workforce (WORKFORCE_*) | HumanAgent entity, assignment workflow |
| Supplier Relationship (SUPPLIER_*) | Vendor entity, rate agreements |
| Payment & Finance (FINANCE_*, RECONCILIATION_*) | Payment entity, payment workflow |
| Notification (NOTIFICATION_*) | Communication workflow, WebSocket events |
| Analytics & BI (ANALYTICS_*) | Revenue pipeline projection, event queries |
| Data Governance (DATA_GOVERNANCE_*) | Provenance chain, event audit trail |
| Audit & Compliance (AUDIT_*) | Event sourcing, immutable audit log |
| Error Handling (ERROR_HANDLING_*) | Disruption recovery workflow |
| Workflow Automation (WORKFLOW_*) | Generic workflow engine patterns |
| AI Copilot (AI_COPILOT_*) | AI actor in event metadata, suggested actions |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend Models | Pydantic v2 | Request/response validation, serialization |
| Frontend Types | TypeScript | API client types, form validation |
| Schema Generation | OpenAPI 3.1 | Auto-sync between backend and frontend |
| Event Store | PostgreSQL + outbox | Transactional event publishing |
| Projections | Custom + Redis | Read-optimized views |
| Real-time | WebSocket / SSE | Live event streaming to workspace |
| Validation | JSON Schema | Shared validation rules |

---

## Existing Codebase Mapping

| Canonical Model | Current Codebase Location | Status |
|----------------|--------------------------|--------|
| Enquiry | `spine_api/models/trips.py` (Trip) | Needs split |
| Trip | `spine_api/models/trips.py` (Trip) | Partial — field mapping needed |
| Booking | Missing | New model |
| Buyer | Missing (User exists in tenant.py) | New model |
| HumanAgent | Missing (User exists in tenant.py) | New model |
| Vendor | Missing | New model |
| Payment | Missing | New model |
| CanonicalPacket | `src/intake/packet_models.py` | Exists |
| Validation | `spine_api/models/trips.py` (validation field) | Partial |
| Provenance | `src/intake/packet_models.py` (provenance) | Partial |

---

**Created:** 2026-04-29
