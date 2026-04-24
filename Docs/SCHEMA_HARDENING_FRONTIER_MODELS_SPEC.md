# TECHNICAL_SPEC: Schema Hardening for Frontier Features

## 1. Overview
This document defines the database schema expansions required to support the Batch 2 and 3 Frontier features. These models are designed for **PostgreSQL** and **SQLAlchemy**, following the multi-tenant architecture established in the core models.

## 2. Proposed Models

### A. `GhostWorkflow` (Autonomic Execution)
*Purpose*: Tracks silent, automated tasks performed by the Ghost Concierge.
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary Key |
| `workspace_id` | UUID | Foreign Key (Workspace) |
| `trip_id` | UUID | Foreign Key (Trip) |
| `task_type` | String | e.g., 'transfer_verify', 'visa_check', 'sim_activate' |
| `status` | Enum | 'pending', 'executing', 'completed', 'failed', 'escalated' |
| `action_payload` | JSONB | Details of the action taken (e.g., API request/response) |
| `autonomic_level` | Integer | 0-4 (Permission level required) |
| `started_at` | DateTime | Timestamp |
| `completed_at` | DateTime | Timestamp |

### B. `EmotionalStateLog` (Anxiety Mitigation)
*Purpose*: High-fidelity tracking of traveler sentiment and mitigation efficacy.
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary Key |
| `traveler_id` | UUID | Foreign Key (User) |
| `trip_id` | UUID | Foreign Key (Trip) |
| `sentiment_score` | Float | 0.0 (Hostile) to 1.0 (Delighted) |
| `anxiety_trigger` | String | e.g., 'flight_delay', 'no_show_driver' |
| `mitigation_action_id` | UUID | Link to the action taken (e.g., lounge credit) |
| `recovery_time_ms` | Integer | Time taken for sentiment to return to baseline |
| `recorded_at` | DateTime | Timestamp |

### C. `IntelligencePoolRecord` (Federated Risk Intel)
*Purpose*: Anonymized industry-wide risk data.
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary Key |
| `incident_type` | String | e.g., 'airline_policy_change', 'customs_strike' |
| `anonymized_data` | JSONB | The pattern of the failure (No PII) |
| `severity` | Integer | 1-5 |
| `confidence` | Float | 0.0 to 1.0 |
| `source_agency_hash` | String | Cryptographic hash for verification without ID |
| `verified_at` | DateTime | Timestamp |

### D. `LegacyAspiration` (Life-Mapping)
*Purpose*: Decadal travel goal persistence.
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary Key |
| `traveler_id` | UUID | Foreign Key (User) |
| `goal_title` | String | e.g., 'Antarctica 2030' |
| `target_year` | Integer | e.g., 2030 |
| `fitness_window_age` | Integer | Max age for optimal physical activity |
| `estimated_cost` | Numeric | Target budget |
| `status` | Enum | 'aspirational', 'planning', 'executed', 'cancelled' |

## 3. Data Integrity & Verification
- **AuditStore Hooks**: Every record creation in these tables must trigger an event in the `AuditStore` for transparency.
- **Integrity Constraints**: Multi-tenant isolation enforced via `workspace_id` at the database level.
- **Post-Quantum Encryption**: `LegacyAspiration` and `GhostWorkflow` payloads to be encrypted with the **Quantum-Secure Diplomatic Pouch** logic.

## 4. Next Steps
1. **Migration Script**: Generate Alembic migrations for these tables.
2. **API Scaffolding**: Create FastAPI endpoints for `GhostWorkflow` tracking.
3. **Mock Data Generation**: Create synthetic records for the **Operational Stress Digital Twin**.
