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

### Phase B: Document + Live Intelligence MVP

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
- `document_readiness_agent` in `src/agents/runtime.py`.
- Tests in `tests/test_agent_runtime.py` covering stale evidence and document checklist output.

Implementation result:

- `DocumentReadinessAgent` builds internal passport, visa, insurance, and transit readiness metadata.
- It writes `document_readiness_checklist`, `document_risk_level`, and `must_confirm_documents`.
- It includes tool evidence with source, fetched timestamp, expiry, confidence, and freshness.
- It explicitly avoids legal finality and requires authoritative verification before quote or booking.

Previous recommendation rationale:

Reason:

- It matches repo context, especially visa/document risk.
- It is high-value and low-risk.
- It can be tested without paid supplier APIs by using deterministic source adapters/mocks.
- It establishes the same evidence/freshness pattern later needed by weather, flight, safety, and ticket-price agents.

## Next Implementation Recommendation

Implement `destination_intelligence_agent` plus a mocked/live-switchable weather adapter next.

Acceptance:

- Uses `ToolResult` for every live/weather/safety result.
- Refuses stale tool data as current evidence.
- Attaches `destination_intelligence_snapshot` with fetched timestamps, source, expiry, and confidence.
- Recommends only internal pivots/escalations; no customer sends or booking changes.

## OpenAI Key Note

`frontend/.env.local` exists for local OpenAI-backed tests. Treat it as local-only. Do not print, copy, commit, or include secret values in artifacts.
