# Multi-Agent Runtime Travel-Ops Alignment

- Date: 2026-05-04
- Purpose: Correct the runtime plan from generic multi-agent infrastructure toward actual travel-agency operating work.

## Correction

The prior completion report was too generous in its final verdict. It correctly added a runtime, registry, event surfaces, tests, and two executable agents, but the agent set was not yet aligned enough with how travel agencies actually leak revenue and operational quality.

The real workflow pressure points are:

- scattered inquiries and weak first triage,
- no clear lead ownership or next step,
- slow or inconsistent follow-up,
- missing qualification data before proposal work,
- quality/document risk before proposal or booking handoff,
- human-controlled booking and client-facing communication.

## Evidence Used

| Source | Operational Takeaway |
| --- | --- |
| `Docs/INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md` | Prioritizes Sales, QualityGate, Retention, Inbox/FrontDoor, Document, and ops orchestration gaps. |
| `Docs/DETAILED_AGENT_MAP.md` | Separates conversational/extractor/scorer/validator/composer agents; supports narrow role agents over one broad planner. |
| `spine_api/server.py` | Existing state already supports stage transitions, follow-ups, booking data, pending booking data, suitability, review, and assignments. |
| IATA Travel Agent Handbook / Travel Centre | Travel documentation and accredited-agent obligations need authoritative source checks and human-safe boundaries. |
| Travel CRM/workflow references | Follow-up should be stage-driven and ownership-driven, not inbox-memory-driven. |

## Implementation Added After Alignment

| Agent | File | Trigger | Output |
| --- | --- | --- | --- |
| `front_door_agent` | `src/agents/runtime.py` | New/incomplete/discovery inquiry without a front-door assessment | `front_door_assessment`, `lead_priority`, `recommended_next_action`, acknowledgment draft. |
| `sales_activation_agent` | `src/agents/runtime.py` | Open lead idle beyond stage SLA and no pending follow-up | `follow_up_due_date`, `follow_up_status=pending`, reason, follow-up draft. |

These are intentionally conservative:

- no message sending,
- no booking,
- no supplier commitments,
- no owner approval bypass,
- no duplicate routes or alternate pipeline.

## Current Agent Order

1. `front_door_agent`
2. `sales_activation_agent`
3. `follow_up_agent`
4. `quality_escalation_agent`
5. `recovery_agent` remains lifespan-managed outside the supervisor registry.

## Next Implementation Plan

Superseded/expanded by `Docs/status/MULTI_AGENT_RUNTIME_EXPANDED_AGENT_PLAN_2026-05-04.md`, which adds live tool-calling, document, stage, supplier, GDS, weather, ticket, and safety agents after checking more repo context files.

1. `DocumentReadinessAgent`
   - Implemented in `src/agents/runtime.py`.
   - Emits missing passport/visa/insurance/transit checklist metadata and never claims final legal advice.
   - Uses `ToolResult` evidence from `src/agents/tool_contracts.py`.
2. `BookingReadinessAgent`
   - Verify `booking_data` / `pending_booking_data` completeness at proposal/booking stage.
   - Acceptance: flags missing names, DOB/passport, payer, and special requirements; no GDS booking.
3. SQL-backed leases
   - Replace in-memory idempotency with durable DB leases before multi-worker production.
   - Acceptance: concurrent workers cannot execute the same idempotency key.

## Local OpenAI Test Key

`frontend/.env.local` exists and can be used for local tests that explicitly require OpenAI. Secret values must not be printed, copied into docs, or persisted into artifacts. `frontend/.nv.local` does not exist.
