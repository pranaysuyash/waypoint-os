# Exploration Backlog

**Last Updated:** 2026-04-18

A living document of areas to explore, ideas to investigate, and potential improvements. Add items freely — this is a brainstorming space, not a commitment queue.

---

## Intake & Pipeline

- [ ] Geography extraction improvements (city database, airport codes, ambiguous names)
- [ ] Multi-envelope accumulation edge cases
- [ ] Normalizer accuracy on messy real-world messages
- [ ] Date parsing for international date formats
- [ ] Currency extraction and normalization (USD, EUR, AED, etc.)
- [ ] Multi-language intake support (hindi, etc.)
- [ ] Attachment/document ingestion (PDFs, images)

## Safety & Leakage

- [ ] Expand leakage detection patterns
- [ ] Test internal_only fields more thoroughly
- [ ] Safety invariant validation across all decision states
- [ ] Automated leakage scanner for prompt templates
- [ ] Redaction techniques for sensitive traveler data

## Decision Engine

- [ ] Push rule hit rate to 70%+ (see rule_expansion_todo.md)
- [ ] LLM integration testing (see rule_expansion_todo.md)
- [ ] Learn from real traffic patterns
- [ ] Dynamic rule compilation from cached LLM decisions
- [ ] Decision confidence scoring
- [ ] A/B testing framework for decision rules

## API & Server

- [ ] spine-api performance optimization
- [ ] Additional health check endpoints
- [ ] Rate limiting and request queuing
- [ ] WebSocket support for real-time updates
- [ ] API authentication/authorization
- [ ] Request tracing and debugging tools

## Frontend (Next.js)

- [ ] Trip workspace improvements
- [ ] Operator workbench components
- [ ] Traveler-facing surfaces
- [ ] Mobile responsive design
- [ ] Real-time decision updates
- [ ] PDF generation for proposals

## Testing Infrastructure

- [ ] Real-world scenario expansion
- [ ] Shadow mode comparison framework
- [ ] Regression prevention tools
- [ ] Load testing for spine-api
- [ ] Property-based testing
- [ ] Visual regression tests

## Data & Persistence

- [ ] Trip state persistence (Postgres schema)
- [ ] Customer profile storage
- [ ] Conversation history retention
- [ ] Cache eviction policies
- [ ] Data backup/recovery procedures

## Observability

- [ ] Structured logging standards
- [ ] Metrics dashboard (Grafana)
- [ ] Alerting rules and thresholds
- [ ] Error tracking (Sentry integration)
- [ ] Performance profiling

## Documentation

- [ ] API reference docs (OpenAPI/Swagger)
- [ ] Contributor onboarding guide
- [ ] Deployment/runbook procedures
- [ ] Architecture diagrams (C4 model)
- [ ] FAQ for common issues

## Operations

- [ ] Deployment automation (CI/CD)
- [ ] Environment configuration management
- [ ] Secret rotation procedures
- [ ] Incident response runbook
- [ ] Cost monitoring and optimization

## Integrations

- [ ] Email service provider (SendGrid/Postmark)
- [ ] WhatsApp Business API
- [ ] Payment gateway integration
- [ ] Calendar booking (Cal.com)
- [ ] SMS notifications

## Security

- [ ] Input validation patterns
- [ ] Output sanitization
- [ ] Rate limiting per user
- [ ] DDoS protection
- [ ] Security audit checklist

## UX/Workflow

- [ ] Journey mapping for each persona
- [ ] Accessibility audit (WCAG)
- [ ] Keyboard navigation
- [ ] Screen reader testing
- [ ] Error message UX improvements

## Business Logic

- [ ] Quote generation and formatting
- [ ] Margin calculation logic
- [ ] Commission tracking
- [ ] Cancellation policy engine
- [ ] Refund processing workflow

## Content/Knowledge

- [ ] Destination database expansion
- [ ] Visa requirement knowledge base
- [ ] Seasonal pricing patterns
- [ ] Activity suitability tags
- [ ] Restaurant/attraction catalog

---

## How to Add Items

1. Choose a relevant section (or create a new one)
2. Add a brief, descriptive item as a checkbox
3. Include links to related docs/issues if applicable
4. Date the update at the top

## Moving Items Out

When an item moves from backlog → active work:
1. Create a dedicated doc or task for it
2. Remove or check off the item here
3. Add a reference link to the active work
