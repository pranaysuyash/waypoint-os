# Error Handling & Resilience — Master Index

> Exploration of error handling patterns, frontend UX, observability, and incident management.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Patterns & Architecture](ERROR_HANDLING_01_PATTERNS.md) | Error taxonomy, retry strategies, circuit breakers, graceful degradation |
| 02 | [Frontend Error UX](ERROR_HANDLING_02_FRONTEND.md) | Error presentation patterns, recovery actions, connection state, spine error handling |
| 03 | [Observability & Alerting](ERROR_HANDLING_03_OBSERVABILITY.md) | Error monitoring stack, alert severity, distributed tracing, error dashboards |
| 04 | [Incident Management & Recovery](ERROR_HANDLING_04_INCIDENT.md) | Incident response workflow, stakeholder communication, postmortems, disaster recovery |

---

## Key Themes

- **Graceful degradation over hard failure** — When an external service fails, show cached data with a banner, not a broken page
- **Agent-friendly errors** — Errors include both a customer-safe message and an agent-visible detail with suggested actions
- **Retry with intelligence** — Exponential backoff with jitter for transient failures; no retry for client errors or payment failures
- **Circuit breakers on all external services** — Hotel APIs, airline GDS, payment gateways all get circuit breakers to prevent cascading failures
- **Observability as a first-class concern** — Correlation IDs propagate from frontend through API to spine to external services

## Integration Points

- **Spine Pipeline** — Spine run failures have dedicated error states with partial results and retry-from-stage
- **Notification System** — Critical errors trigger alerts to on-call via PagerDuty/Slack
- **Audit Trail** — All errors are logged with correlation IDs for postmortem analysis
- **Agent Workbench** — Connection state indicator shows real-time health; pending actions queue when offline
- **Customer Portal** — Customer-facing errors use sanitized messages; never expose stack traces or internal details
