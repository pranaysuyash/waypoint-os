# Multi-Agent Runtime Expanded Agent Plan

- Date: 2026-05-04
- Purpose: Expand the agent roadmap after checking repo context files, product feature specs, domain ops docs, and research specs.

## Correction To Current State

The runtime should not stop at follow-up and quality escalation. Repo context explicitly calls for live trip tracking, tool-calling intelligence, document/visa support, stage-specific workflows, GDS/booking safeguards, and issue playbooks.

Important context files checked:

- `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
- `Docs/context/agent-start/SESSION_CONTEXT.md`
- `Docs/context/TRAVEL_AGENCY_CONTEXT_2_DIGEST_2026-04-14.md`
- `Docs/context/TRIP_VISA_DOCUMENT_RISK_SCENARIO_2026-04-15.md`
- `Docs/product_features/AI_AGENT_TEAM_ORCHESTRATOR.md`
- `Docs/product_features/AGENT_OPERATIONS_COMMAND_CENTER.md`
- `Docs/product_features/DYNAMIC_ITINERARY_PULSE.md`
- `Docs/product_features/SAFETY_AND_SECURITY_REAL_TIME_ALERTS.md`
- `Docs/research/OPS_SPEC_WEATHER_PIVOT.md`
- `Docs/research/GDS_SPEC_CONNECTIVITY.md`
- `Docs/research/REG_SPEC_VISA_AUTOMATION.md`
- `Docs/research/OPS_SPEC_PREDICTIVE_REBOOKING.md`
- `Docs/research/OPS_SPEC_SUPPLIER_INTELLIGENCE.md`

## Architecture Principle

Agents should be grouped by operational stage and authority level:

1. **Observe**: call tools, ingest data, normalize results, and attach evidence.
2. **Assess**: compare live/contextual data to trip state and policy.
3. **Recommend**: draft actions, options, checklists, or escalation packets.
4. **Act only where safe**: update internal metadata, create tasks, mark due/escalated.
5. **Human approval for commitments**: no auto-send to customer, no ticketing, no payment, no supplier contract, no visa/legal finality.

## Proposed Agent Families

### 1. Live Intelligence / Tool-Calling Agents

| Agent | Job | Tools / Feeds | Output | Safe Authority |
| --- | --- | --- | --- | --- |
| `destination_intelligence_agent` | Check live destination conditions before proposal/travel. | Weather, AQI, advisories, events, safety feeds. | `destination_intelligence_snapshot`, risk score, evidence URLs/timestamps. | Attach evidence and recommend pivots. |
| `weather_pivot_agent` | Monitor trip/event-level weather and propose pivots. | Weather/radar APIs, event venue coordinates. | Weather pivot packet, indoor alternatives, transport/gear recommendations. | Internal recommendations only. |
| `flight_status_agent` | Check flight schedule, delay, gate, and disruption risk. | Flight status APIs/GDS/NDC later. | Flight status snapshot, delay risk, affected-trip issue. | Create issue/escalation task; no rebooking. |
| `ticket_price_watch_agent` | Watch fare/rate movement after quote or before booking. | Flight/hotel price APIs, supplier feeds. | Price movement alert, revalidation requirement. | Alert; no purchase. |
| `safety_alert_agent` | Monitor disruptions and duty-of-care risks. | Travel advisories, news/security feeds, health alerts. | Safety alert packet and affected-traveler list. | Escalate and draft check-in message. |

These agents require a shared `ToolResult` contract before implementation:

```json
{
  "tool_name": "weather",
  "query": {"destination": "Singapore", "date": "2026-05-15"},
  "fetched_at": "2026-05-04T00:00:00Z",
  "source": "provider_name",
  "confidence": 0.82,
  "data": {},
  "raw_reference": "redacted-or-url",
  "expires_at": "2026-05-04T06:00:00Z"
}
```

### 2. Document / Compliance Agents

| Agent | Job | Inputs | Output | Safe Authority |
| --- | --- | --- | --- | --- |
| `document_readiness_agent` | Build document checklist for passports, visas, insurance, transit. | Destination, nationality, route, traveler ages, trip dates. | `document_readiness_checklist`, missing items, must-confirm list. | Block readiness metadata; no legal finality. |
| `visa_timeline_agent` | Estimate visa lead-time risk and deadline pressure. | Travel dates, nationality, consulates, route complexity. | Deadline risk, latest safe application dates, alternative route suggestion. | Escalate timing risk. |
| `identity_vault_agent` | Track expiry and document collection state. | Traveler document metadata only. | Expiry warnings and collection reminders. | Reminder/task creation only. |

### 3. Stage-Specific Workflow Agents

| Stage | Agent | Job |
| --- | --- | --- |
| Intake / Discovery | `front_door_agent` | Already added: classify, missing fields, priority, acknowledgment draft. |
| Qualification | `sales_activation_agent` | Already added: idle lead follow-up scheduling. |
| Feasibility | `constraint_feasibility_agent` | Detect impossible combinations: budget/date/visa/pace/accessibility. |
| Shortlist | `destination_shortlist_agent` | Rank candidate destinations from constraints and live intelligence. |
| Proposal | `proposal_readiness_agent` | Ensure proposal has options, risks, budget transparency, and next action. |
| Booking handoff | `booking_readiness_agent` | Verify traveler names/docs/payer/special requirements before human booking. |
| In-trip | `dynamic_itinerary_pulse_agent` | Track live changes and create internal issue/pivot packets. |
| Post-trip | `retention_afterglow_agent` | Schedule feedback, review request, repeat-trip suggestions. |

### 4. Supplier / GDS / Booking-Safe Agents

| Agent | Job | Boundary |
| --- | --- | --- |
| `supplier_intelligence_agent` | Track supplier reliability, response times, preferred inventory, dark patterns. | No autonomous supplier commitments. |
| `gds_schema_bridge_agent` | Normalize GDS/NDC/provider outputs into canonical travel objects. | No ticketing without explicit human approval. |
| `quote_revalidation_agent` | Revalidate quote drift before payment/ticketing. | Hard-block stale quote metadata. |
| `pnr_shadow_agent` | Compare agency booking record to GDS/PNR record for ghost-booking risk. | Alert only until GDS integration is real. |

## Recommended Build Sequence

### Phase A: Tool Result Foundation

1. Add `src/agents/tool_contracts.py` with `ToolResult`, `ToolEvidence`, `ToolFreshnessPolicy`.
2. Add `ToolCallingAgent` base protocol: `build_queries()`, `call_tools()`, `normalize_results()`, `assess()`.
3. Add evidence persistence under existing audit/agent event surfaces.

Acceptance:

- tool results include source, fetched timestamp, expiry, confidence, and normalized data;
- tests prove stale tool data is not used as fresh evidence;
- no secret values from `frontend/.env.local` are logged.

### Phase B: Document + Live Intelligence Foundation

1. `document_readiness_agent`
2. `destination_intelligence_agent`
3. `weather_pivot_agent`

Acceptance:

- document scenario in `Docs/context/TRIP_VISA_DOCUMENT_RISK_SCENARIO_2026-04-15.md` produces a checklist and must-confirm list;
- weather/destination agent can attach a live or mocked evidence packet with freshness;
- agents only recommend/escalate, not auto-book or auto-send.

### Phase C: Stage Agents

1. `constraint_feasibility_agent`
2. `proposal_readiness_agent`
3. `booking_readiness_agent`
4. `dynamic_itinerary_pulse_agent`

Acceptance:

- each stage has a deterministic trigger contract;
- stage agents update existing trip fields or agent metadata only;
- all stage transitions continue through canonical `/trips/{trip_id}/stage`.

### Phase D: Supplier/GDS Hardening

1. `quote_revalidation_agent`
2. `gds_schema_bridge_agent`
3. `pnr_shadow_agent`
4. `supplier_intelligence_agent`

Acceptance:

- canonical travel object schema exists;
- quote drift > threshold hard-blocks booking readiness;
- GDS/NDC outputs are normalized before any reasoning model sees them.

## Immediate Next Implementation Recommendation

Implemented in this pass:

- `src/agents/tool_contracts.py` with `ToolFreshnessPolicy`, `ToolEvidence`, and `ToolResult`.
- `src/agents/live_tools.py` with deterministic mock weather and opt-in Open-Meteo weather adapter.
- Configurable HTTP provider adapters in `src/agents/live_tools.py` for flight status, quote/price watch, and safety alert feeds.
- A State Department travel advisory safety adapter in `src/agents/live_tools.py`, gated behind `TRAVEL_AGENT_SAFETY_PROVIDER=state_dept`.
- `document_readiness_agent` in `src/agents/runtime.py`.
- `destination_intelligence_agent` in `src/agents/runtime.py`.
- `weather_pivot_agent` in `src/agents/runtime.py`.
- `constraint_feasibility_agent` in `src/agents/runtime.py`.
- `proposal_readiness_agent` in `src/agents/runtime.py`.
- `booking_readiness_agent` in `src/agents/runtime.py`.
- `flight_status_agent` in `src/agents/runtime.py`.
- `ticket_price_watch_agent` in `src/agents/runtime.py`.
- `safety_alert_agent` in `src/agents/runtime.py`.
- `gds_schema_bridge_agent`, `pnr_shadow_agent`, and `supplier_intelligence_agent` in `src/agents/runtime.py`.
- Durable SQL work coordination through `SQLWorkCoordinator`, `AgentWorkLease`, and `alembic/versions/add_agent_work_leases.py`.
- Async TripStore adapter boundary hardening in `spine_api/server.py`, so synchronous agent scans resolve accidental coroutine results from SQL-backed list/update calls.
- SQL sync/async bridge hardening in `spine_api/persistence.py`, using a serialized background bridge and loop-local TripStore SQL engines for synchronous SQL facade calls.
- Stale ownerless audit-lock recovery in `spine_api/persistence.py`.
- Frontend BFF preservation of agent-operation metadata in `frontend/src/lib/bff-trip-adapters.ts`.
- Operator packet-page surface for document, destination, weather, feasibility, proposal, booking, flight, price, safety, supplier, GDS, and PNR packets in `frontend/src/components/workspace/panels/PacketPanel.tsx`.
- Catch-all proxy route-map entries for canonical runtime/event APIs in `frontend/src/lib/route-map.ts`.
- Packet-page refresh action that runs the canonical backend runtime pass through `/api/agents/runtime/run-once`.
- Tests in `tests/test_agent_runtime.py` covering stale evidence, document checklist output, destination intelligence freshness, weather pivot packets, constraint feasibility blockers, proposal readiness, booking readiness, flight status, ticket price watch, safety alerts, and supplier/GDS checks.
- Regression coverage in `tests/test_agent_tripstore_adapter.py` for async TripStore adapter behavior.
- Frontend adapter coverage in `frontend/src/lib/__tests__/bff-trip-adapters.test.ts`.

Implementation result:

- `DocumentReadinessAgent` builds internal passport, visa, insurance, and transit readiness metadata.
- It writes `document_readiness_checklist`, `document_risk_level`, and `must_confirm_documents`.
- It includes tool evidence with source, fetched timestamp, expiry, confidence, and freshness.
- It explicitly avoids legal finality and requires authoritative verification before quote or booking.
- `DestinationIntelligenceAgent` writes `destination_intelligence_snapshot`, `destination_risk_level`, and internal recommendations.
- It uses `ToolResult` for weather evidence and refuses stale weather evidence as current proof.
- The default weather adapter is deterministic/mock; setting `TRAVEL_AGENT_ENABLE_LIVE_TOOLS=1` uses the keyless Open-Meteo adapter.
- Flight, price, and safety tools can now be switched from deterministic local tools to configured HTTP JSON providers with URL-template environment variables while preserving the same `ToolResult` output contract.
- The safety tool can use a State Department advisory adapter for public advisory evidence; the output remains operator evidence and does not claim legal/compliance finality.
- `WeatherPivotAgent` writes `weather_pivot_packet`, `weather_pivot_risk_level`, and operator next action from fresh destination intelligence.
- It refuses stale destination/weather evidence and asks operators to refresh intelligence before making pivot decisions.
- `ConstraintFeasibilityAgent` writes `constraint_feasibility_assessment`, `feasibility_status`, hard blockers, soft constraints, missing facts, and operator next action.
- It detects budget pressure, compressed dates, document readiness risk, weather pivot risk, pace, accessibility, and senior-traveler constraints without auto-rejecting or mutating canonical stage.
- `ProposalReadinessAgent` writes `proposal_readiness_assessment`, `proposal_readiness_status`, missing elements, unresolved risks, and operator next action.
- It blocks thin/risky proposals from operator review until options, budget assumptions, risks, and next action are present.
- `BookingReadinessAgent` writes `booking_readiness_assessment`, `booking_readiness_status`, missing elements, blocking risks, and operator next action.
- It verifies names, DOB/passport, payer, contact, special requirement confirmation, and unresolved proposal/document/feasibility risks before human booking.
- `FlightStatusAgent` writes `flight_status_snapshot`, `flight_disruption_risk_level`, and operator next action from `ToolResult` flight evidence.
- `TicketPriceWatchAgent` writes `ticket_price_watch_alert`, `quote_revalidation_required`, `price_watch_risk_level`, and operator next action from `ToolResult` price evidence.
- `SafetyAlertAgent` writes `safety_alert_packet`, `safety_risk_level`, affected travelers, and operator next action from `ToolResult` safety evidence.
- `GDSSchemaBridgeAgent` writes canonical travel objects from provider records.
- `PNRShadowAgent` writes mismatch checks between booking data and PNR records.
- `SupplierIntelligenceAgent` writes supplier reliability/response risk metadata.
- Durable SQL work coordination is implemented through `SQLWorkCoordinator`, `AgentWorkLease`, and `alembic/versions/add_agent_work_leases.py`.
- `_TripStoreAdapter` resolves accidental async `list_trips` and `update_trip` results before agent scans consume them.
- The SQL TripStore sync facade no longer creates a fresh event loop per call and no longer shares one TripStore async engine across the FastAPI loop and bridge loop, avoiding asyncpg loop-bound pool/lock failures under runtime scans.
- Ownerless stale audit lock directories are reclaimed so interrupted audit writes do not block supervisor startup events.
- The frontend `Trip` model now carries `agentOperations`, and the packet page renders the new runtime packets for operators instead of hiding them behind raw JSON.
- Operators can trigger a runtime refresh from the packet page without adding a duplicate API route; the existing catch-all proxy forwards to `POST /agents/runtime/run-once`.

Previous recommendation rationale:

Reason:

- It matches repo context, especially visa/document risk.
- It is high-value and low-risk.
- It can be tested without paid supplier APIs by using deterministic source adapters/mocks.
- It establishes the same evidence/freshness pattern later needed by weather, flight, safety, and ticket-price agents.

## Next Implementation Recommendation

Remaining hardening work should focus on production durability and real provider adapters.

Acceptance:

- Apply and operationalize the SQL work-lease migration before multi-worker deployment.
- Wire chosen production vendors into `TRAVEL_AGENT_FLIGHT_STATUS_URL_TEMPLATE`, `TRAVEL_AGENT_PRICE_WATCH_URL_TEMPLATE`, and `TRAVEL_AGENT_SAFETY_ALERT_URL_TEMPLATE`, including credentials through header environment variables.
- Deepen operator controls from read-only packet visibility into task actions, acknowledgments, and provider refresh/revalidation flows.

## OpenAI Key Note

`frontend/.env.local` exists for local OpenAI-backed tests. Treat it as local-only. Do not print, copy, commit, or include secret values in artifacts.
