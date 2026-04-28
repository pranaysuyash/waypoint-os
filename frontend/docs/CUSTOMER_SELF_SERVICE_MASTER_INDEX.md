# Customer Self-Service Portal — Master Index

> Exploration of customer-facing portal for trip management, documents, and support.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Dashboard & Trip View](CUSTOMER_PORTAL_01_DASHBOARD.md) | Portal layout, trip detail with progress stages, self-service capabilities |
| 02 | [Booking Management](CUSTOMER_PORTAL_02_BOOKING_MANAGEMENT.md) | Modification requests, cancellation flows, conflict resolution |
| 03 | [Documents & Sharing](CUSTOMER_PORTAL_03_DOCUMENTS.md) | Document library, offline access, sharing model, update notifications |
| 04 | [Support & Communication](CUSTOMER_PORTAL_04_SUPPORT.md) | Support channels, customer-agent chat, FAQ, feedback submission |

---

## Key Themes

- **Progressive self-service** — Customers handle routine tasks (view itinerary, download documents, submit modifications) without agent involvement
- **Transparent status** — Every request shows real-time status; no "we'll get back to you" black boxes
- **Agent escalation path** — Self-service handles 80% of queries; complex issues escalate seamlessly to a human agent with full context
- **Mobile-first** — Most customer interactions happen on mobile during travel
- **Trust through visibility** — Customers see what the agent sees (pricing breakdown, supplier details, timeline) to build confidence

## Integration Points

- **Trip Builder** — Portal reads trip data produced by the agent workbench
- **Document Generation** — Documents generated for trips are surfaced in the portal
- **Notification System** — Portal events (modification requests, document updates) flow through the notification pipeline
- **Payment Gateway** — Customers can view invoices and make payments directly
- **Audit Trail** — All customer actions are logged for compliance and support context
