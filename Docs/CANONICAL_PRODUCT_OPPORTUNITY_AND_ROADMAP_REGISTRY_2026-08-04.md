# Waypoint OS: Canonical Product Opportunity & Roadmap Registry

*Date: August 4, 2026*
*Author: Antigravity AI (Pair Engineering Partner)*
*Status: Canonical Product Opportunity & Roadmap Registry (Ground-Truth Reconciled)*

---

## Executive Verdict

Waypoint OS is no longer merely a travel-agency copilot. The repository already contains the foundations of five overlapping products:

1. **Agency operations system** for converting enquiries into executable trips.
2. **Decision and quality-control system** for constraints, suitability, compliance, reviews, and approvals.
3. **Revenue and supply system** for pricing, margins, suppliers, commissions, and yield.
4. **Traveler experience and trip-operations system** for proposals, document collection, confirmations, live operations, and disruptions.
5. **Agentic governance platform** for automation, human oversight, auditability, recovery, evaluation, and per-agency controls.

The current OpenAPI snapshot contains **179 API paths**, covering substantially more than the README’s original intake-to-strategy framing.

The documentation corpus is even larger. It includes 340+ persona scenarios, many roadmap generations, product-feature explorations, vertical studies, ADRs, frontier research, and speculative concepts. However, the persona documentation explicitly warns that most additional scenarios are research inputs, not implemented commitments. Only the mapped core scenarios should be treated as connected to the pipeline without further verification.

The principal problem is therefore **not idea scarcity**. It is:

- duplicate concepts under different names;
- routes that exist but may not be product-complete;
- historical roadmaps that contradict current code;
- implementation claims that have not been reconciled;
- exploratory concepts mixed with committed work;
- speculative frontier ideas competing visually with launch-critical features;
- no single feature registry tying personas, pain points, commercial value, implementation evidence, dependencies, and outcomes together.

The project rules correctly require documentation to be verified against code, related patterns to be searched systematically, and exploratory work to be preserved without silently treating it as truth.

The next document must therefore be a **canonical product opportunity and roadmap registry**, not another prose brainstorm.

---

# 1. Evidence Model for the Roadmap

Every roadmap item receives one of these evidence labels:

| Label | Meaning |
|---|---|
| **C: Code-backed surface** | Route, model, service, component, test, or runtime surface exists. This does not automatically mean production-ready. |
| **D: Documented explicit feature** | Clearly specified in product docs, ADRs, roadmap files, or scenario documentation. |
| **I: Implicit capability** | Naturally follows from current architecture, data, workflows, or adjacent features. |
| **M: Market-derived opportunity** | Identified from competitor analysis, external product patterns, or market structure. |
| **F: Frontier research** | Legitimate exploration, but not a current product commitment. |
| **R: Rejected, deferred, or superseded** | Preserved for institutional memory but excluded from the active roadmap. |

Every item also receives an implementation status separate from its evidence:

- Verified working
- Partially working
- Surface exists, behavior unverified
- Specification only
- Research required
- Deferred
- Rejected
- Superseded
- Frontier lab

This distinction is essential. For example, current routes exist for AI-agent, communications, and support settings, while older roadmap addenda say those models were absent. The historical roadmap is therefore not reliable as a current status source without code-level reconciliation.

---

# 2. Canonical Platform Model

Waypoint should be understood as ten linked systems:

```text
Acquire
  ↓
Capture
  ↓
Understand
  ↓
Remember
  ↓
Decide
  ↓
Source and Price
  ↓
Propose and Convert
  ↓
Book and Collect
  ↓
Operate and Protect
  ↓
Learn and Improve
```

Surrounding the complete chain are:

```text
Team Governance
Financial Control
Security and Compliance
Agentic Automation
Analytics and Intelligence
Partner Ecosystem
```

This is the durable product model. Individual verticals such as leisure agencies, creators, DMCs, corporate travel, and group operators should be configurations of this core, not separate pipelines.

The original product vision already describes most of this chain: discovery, itinerary creation, revisions, visa and documentation, booking coordination, in-trip operations, and post-trip memory. It also correctly defines the sourcing hierarchy as internal packages, preferred suppliers, network/DMC inventory, then open-market inventory.

---

# 3. Full Feature Inventory

All duplicate names have been consolidated into canonical feature families.

## 3.1 Acquisition, Lead Generation, and Distribution

### Code-backed or surfaced [C]
- Public itinerary checker
- Public checker event stream
- Public checker result retrieval
- Public checker export
- Social enquiry parser
- Social teaser unmasking
- Direct inbound parsing endpoint
- Fast enquiry intake foundations
- Public proposal links
- Public booking-data collection links
- Signup, join-code, invitation, and workspace-code flows
- Seasonal campaign creation
- Seasonal campaign simulation
- Campaign preflight
- Campaign dispatch
- Messaging dispatch and provider webhooks
- Integration provider registry

### Explicitly documented [D]
- Chrome extension for WhatsApp Web and Gmail capture
- Mobile share-sheet capture
- Voice-note-to-enquiry conversion
- Email forwarding intake
- Link-in-bio creator intake
- Creator-branded intake links
- Consumer itinerary-audit funnel
- “Audit then connect to agency” lead handoff
- Free teaser proposal followed by deposit-based unmasking
- Agency website enquiry widgets
- Partner and referral intake
- Host-agency white-label acquisition
- DMC-to-agency referrals
- Creator-to-agency co-selling
- Corporate offsite intake
- Content-led acquisition
- Trade-community distribution
- Travel association partnerships

### Implicit opportunities [I] / Market [M]
- Embeddable enquiry widget SDK
- QR-based offline enquiry capture
- Affiliate and partner attribution
- Campaign-to-booking attribution
- Lead-source profitability
- Duplicate-lead detection
- Spam and low-intent filtering
- Intent scoring
- Lead routing by destination, value, language, and specialization
- Referral fee accounting
- Consent capture by acquisition source
- Partner-branded landing-page generator
- Destination feasibility calculators as SEO acquisition
- Visa/document checkers as SEO acquisition
- Public trip-risk and accessibility checkers
- Shareable family preference collection links
- Agency marketplace handoff
- Franchise and multi-brand lead routing

---

## 3.2 Omnichannel Intake and Extraction

### Code-backed or surfaced [C]
- General inbound enquiry parsing
- Social-message parsing
- Optimistic trip-state synchronization
- Server-sent trip-state event stream
- Draft creation
- Draft event history
- Draft restoration
- Draft promotion into canonical trips
- Draft-to-run association
- Document extraction attempts
- Extraction retries
- Extraction version snapshots
- Human acceptance and rejection of extracted data
- Applying accepted extraction results to trip state
- Activity provenance records

### Explicitly documented [D]
- WhatsApp message stitching
- Email thread stitching
- Voice-note transcription and extraction
- Screenshot and image extraction
- OCR for passports, visas, tickets, confirmations, and rate sheets
- Visual-intent extraction from inspiration images
- Local PII detection before model calls
- Browser-side PII scrubbing
- Edge SLM/ONNX extraction
- Offline capture queue
- Background model downloading
- Progressive model pre-caching
- Cross-channel identity stitching
- Confidence-aware extraction
- Local-first fallbacks

### Implicit opportunities [I]
- Attachment bundle parsing
- Multi-message conversational context reconstruction
- Language detection and multilingual extraction
- Transliteration-aware entity matching
- Contact and traveler identity resolution
- Duplicate enquiry merging
- Entity conflict detection
- Historical-value versus newly stated-value reconciliation
- Source-level provenance for every field
- “Why was this field inferred?” explanations
- Structured correction feedback
- Per-channel extraction quality metrics
- Extraction model routing based on input type
- Sensitive-field redaction previews
- Agency-specific vocabulary and abbreviation dictionaries
- Supplier-name/entity normalization
- Low-confidence human-review queues
- Bulk enquiry import from historical inboxes and spreadsheets

---

## 3.3 Lead Lifecycle, CRM, and Relationship Memory

### Code-backed or surfaced [C]
- Trip records & stages
- Trip timelines
- Inbox queues & statistics
- Bulk inbox actions
- Assignment and ownership
- Follow-up generation & dashboard
- Snooze, reschedule, and completion tracking
- Draft lifecycle
- Activity and agent events
- Review actions

### Explicitly documented [D]
- Cross-trip customer memory
- Repeat-customer preferences
- Relationship notes
- Family and household memory
- Past mobility and health constraints
- Dietary preferences
- Hotel and room preferences
- Brand and airline preferences
- Anniversary and milestone memory
- Ghosted-lead handling
- Window-shopper identification
- Churn interventions
- Referral and repeat-trip triggers
- Customer-history browser
- Lead-lifecycle state machine
- Scope-creep tracking
- Revision history & comparison

### Implicit opportunities [I]
- Individual, family, company, and group relationship graph
- Contact merge and deduplication
- Shared household preferences
- Corporate traveler profile
- Creator-audience traveler profile
- Lifetime value calculation
- Recency-frequency-value analysis
- Next-best-action recommendations
- Re-engagement recommendations
- Relationship-strength scoring
- Consent-aware memory
- Data expiry and forgetting controls
- Brand-voice memory by advisor
- Client-specific communication style
- Referral graph
- Past objections and resolution history
- Lost-deal reason analysis
- Agency handover without relationship loss
- Advisor departure continuity
- Client portfolio transfer
- Client preference confidence and last-confirmed date

---

## 3.4 Constraint, Suitability, Risk, and Decision Intelligence

### Code-backed or surfaced [C]
- Trip suitability results
- Suitability acknowledgment & reassessment
- Overrides & override histories
- Agentic trip evaluation
- Policy audit & trust scorecard
- Decision-state pipeline
- Gap identification
- High-value review gates
- Manual review actions
- Traveler-safe output boundary

### Explicitly documented [D]
- Visa and passport hard blockers
- Budget feasibility
- Mobility constraints
- Senior-traveler & toddler pacing
- Dietary requirements & accessibility
- Group conflict detection
- Fatigue and rest windows
- Over-packed itinerary detection
- Route and transfer feasibility
- Weather and climate adaptation
- Ethical and cultural sensitivity
- Corporate policy & supplier-contract compliance
- Cancellation-risk evaluation
- Traveler anxiety mitigation
- Insurance requirement checks
- Traveler-safe leakage prevention
- RAG grounding and citations
- Confidence-driven proceed/ask/stop logic

### Implicit opportunities [I]
- Configurable constraint-policy language
- Agency-specific constraint rules
- Destination-specific hard constraints
- Regulatory rules with effective dates
- Evidence-backed rule provenance
- Constraint conflict explanations
- Alternative generation after a blocker
- Hard-versus-soft preference separation
- Risk-budget configuration
- Traveler risk-tolerance profiles
- Scenario comparison
- “Cheapest feasible” versus “best fit” versus “highest margin” views
- Counterfactual analysis
- Group consensus and dissent tracking
- Insurance-policy suitability
- Accessibility verification
- Duty-of-care risk scoring
- Pre-booking red-team audit
- Pre-departure audit
- In-trip continuous reassessment
- Post-trip outcome validation
- Human override reason capture
- Override-pattern analysis
- Regret and complaint risk prediction

---

## 3.5 Research, Sourcing, Inventory, and Content

### Code-backed or surfaced [C]
- Activity provenance
- Yield opportunities & supplier-swap surfaces
- Integration registry
- Geography datasets
- Suitability-aware activity data
- Strategy and bundle pipeline

### Explicitly documented [D]
- Internal package library
- Preferred supplier inventory
- DMC, consortium & open-market sourcing
- DMC & hotel rate-sheet upload
- AI column mapping
- Supplier portal
- Net and commissionable rates
- Seasonal rate periods & blackout dates
- Inventory allocations & soft holds
- Supplier reliability, compliance & blacklists
- Destination knowledge base
- Reusable content library
- Visual-intent matching & mood/taste graph
- Dark inventory & community hosts
- Competitive supplier bidding & auctions

### Implicit opportunities [I]
- Canonical supplier-product-option hierarchy
- Supplier contract versioning & expiry alerts
- Rate validity windows
- Currency normalization
- Child, occupancy, room, and meal-plan rules
- Cancellation-policy normalization
- Stop-sale and blackout alerts
- Supplier quote-request workflow & SLA tracking
- Quote parsing from supplier email
- Supplier booking-request generation
- Automated supplier follow-up
- Supplier quality and incident history
- Reliability versus margin ranking
- Agency-specific preferred supplier weighting
- Contracted versus spot-rate comparison
- Rate anomaly detection
- Duplicate inventory reconciliation
- Inventory freshness score
- Content rights and licensing
- Content deduplication
- Reusable destination modules
- Supplier images and content approval
- Agency-specific content overrides
- Destination seasonality & availability confidence
- External GDS/bedbank adapter layer
- Source-of-truth conflict handling

---

## 3.6 Pricing, Revenue, Margin, and Yield

### Code-backed or surfaced [C]
- Yield arbitrage by trip
- Yield-opportunity queue
- Supplier swapping
- Revenue analytics
- Payment read model & booking payment data
- Trust-scorecard commercial signals
- Proposal price-lock concepts
- High-value review gates

### Explicitly documented [D]
- Net rates vs gross rates
- Markup & commission rules
- Margin protection
- Supplier comparison
- Price-lock countdowns
- Creator/agency commission splits
- Agent commission tracking
- Multi-currency arbitrage
- Deposit collection & multi-party payments
- Supplier payouts & agency tiering
- Commercial-fit optimization
- Price-drop re-shopping
- Resource futures & inventory hedging
- Budget reality checking

### Implicit opportunities [I]
- Quote versioning
- Cost-versus-sell waterfall
- Item-level margin & trip-level contribution margin
- Advisor-level, destination-level & supplier-level profitability
- Channel profitability
- Customer-acquisition-cost attribution
- Discount approval & minimum-margin guard
- Markup profiles by customer, product, or destination
- Dynamic service fees, planning fees, change fees, cancellation fees
- Refund logic & deposit schedules
- Payment plans
- FX spread visibility & currency exposure
- Tax and GST calculation (including India GST invoices)
- Commission accrual & reconciliation
- Unclaimed commission detection
- Supplier payment schedule
- Expected-versus-actual margin & leakage detection
- Quote expiration & price-change approval
- Revenue & cash-flow forecasting
- Profitability simulation before proposal
- “Best traveler fit within minimum commercial guardrail”

---

## 3.7 Proposal, Quotation, Trust, and Conversion

### Code-backed or surfaced [C]
- Proposal-link generation
- Tokenized public proposal retrieval
- Proposal acceptance
- Trust scorecard
- Public itinerary audit
- Public result export
- Messaging dispatch & follow-up generation
- Teaser unmasking

### Explicitly documented [D]
- Interactive mobile proposal & PDF export
- Branded proposals & creator/DMC co-branding
- Price-lock countdown
- Masked supplier and hotel names
- Deposit-to-unmask
- Suitability match score
- Verified supplier badges & cancellation badges
- Risk explanations & traveler-safe messaging
- Trade-off explanations
- Budget-versus-comfort comparison
- Scope and inclusion transparency
- One-click acceptance

### Implicit opportunities [I]
- Side-by-side proposal comparison
- Traveler comments and annotations
- Family voting & group approval
- Option ranking & advisor recommendation rationale
- Revision requests attached to proposal elements
- Proposal version history
- E-signature, terms acceptance & privacy consent
- Proposal open/read analytics & section-level engagement
- Share tracking, watermarking & IP-protection controls
- Expiring links & one-time access codes
- Custom domains, accessibility modes & localization
- Automated reminder sequences & proposal abandonment recovery
- A/B testing & brand-template library
- Proposal quality score & price-transparency configurations
- Planning-fee collection & booking handoff

---

## 3.8 Booking-Data Collection, Documents, and Verification

### Code-backed or surfaced [C]
- Public booking-data collection (tokenized)
- Public document upload & submission
- Internal document storage and download
- Document acceptance/rejection & extraction attempts
- Retries, apply/reject extraction & version snapshots
- Pending booking data & payment-related data
- Confirmation recording, verification & voiding

### Explicitly documented [D]
- Passport & visa-document collection
- Insurance collection & waivers
- Credit-card authorization
- Document checklists & missing-document reminders
- Visa checklist generation
- Name/date mismatch detection
- Document-expiry checks
- Secure traveler vault & PII scrubbing
- OCR and structured extraction
- Human verification & distributed group collection

### Implicit opportunities [I]
- Document requirements by destination, nationality, age, and trip type
- Household document reuse & expiry alerts
- Passport-validity calculations & visa-status tracking
- Consent receipts & secure sharing with suppliers
- Fine-grained document access & automatic redaction
- Malware scanning & duplicate-document detection
- Tamper detection & image-quality checks
- Structured form filling & missing-field escalation
- Bulk group collection & guardian consent for minors
- Medical document handling & data-retention policies
- Traveler self-delete/export & versioned traveler identity
- Document-to-booking reconciliation
- Name transliteration checking & secure download audit trails

---

## 3.9 Booking Execution and Supplier Operations

### Code-backed or surfaced [C]
- Booking-task generation, retrieval, completion & cancellation
- Confirmation records & verification
- Execution timeline & agent events
- Assignment, escalation & readiness tracking

### Explicitly documented [D]
- Booking readiness checklist
- Supplier booking requests & confirmation parsing
- Trip master record
- Pickup and transfer schedules
- Day-wise operations dashboard
- Rooming lists, flight lists, bus lists & group manifests
- Guide allocation & voucher generation
- Service ordering & local-handoff management
- SIM and last-mile coordination
- Booking reconciliation & supplier-response tracking

### Implicit opportunities [I]
- Reservation-state machine (request, option, hold, confirm, cancel, refund)
- PNR and reservation synchronization
- Supplier acknowledgment & deadline alerts
- Deposit & cancellation deadline management
- Service-level alerts & resource conflicts
- Driver and guide assignment & capacity management
- Operational run sheets & calendar export
- Mobile field-operations view & offline manifests
- Emergency contact sheets & supplier communication history
- Booking evidence, receipts & actual-versus-planned execution
- No-show and service-failure logging (linked to supplier score)
- Automatic post-service confirmation & traveler arrival confirmation
- Operations handover between shifts

---

## 3.10 Traveler, Family, and Group Experience

### Code-backed or surfaced [C]
- Public proposal & acceptance
- Public checker & booking collection
- Document upload & messaging
- Concierge monitoring & live event streams
- Execution timeline & confirmation data

### Explicitly documented [D]
- Traveler dashboard & interactive itinerary
- Group portal & creator-host portal
- Family preference collector & group voting
- Shared itinerary, split payments & payment tracking
- Document sharing & post-booking updates
- Emergency contacts, flight status & weather alerts
- Local tips & traveler concierge
- Feedback, post-trip review & live itinerary pulse
- Expense tracking, SOS & offline itinerary

### Implicit opportunities [I]
- Traveler PWA & native mobile app
- Wallet passes & offline vouchers
- Push notifications & calendar synchronization
- Map, navigation & meeting points
- Local-language assistance & time-zone-aware reminders
- Group announcements & per-traveler visibility permissions
- Minor/guardian accounts & accessibility modes
- Companion/caretaker access & shared packing lists
- In-trip polls, concierge requests & issue reporting
- Incident evidence upload & reimbursement capture
- Travel journal & media collection
- Post-trip memory confirmation & referral generation

---

## 3.11 Communications and Follow-up

### Code-backed or surfaced [C]
- Message sending & provider webhooks
- Follow-up generation, dashboard, snooze, reschedule & completion
- Alert destinations & testing
- Communication, support & seasonal campaign settings

### Explicitly documented [D]
- WhatsApp Cloud API & email delivery
- Traveler-safe communication & tone calibration
- One-click copy generation
- Proactive post-booking updates & disruption alerts
- Group announcements & voice intake
- SMS, creator tone & agency brand voice
- Multilingual communication & playbooks

### Implicit opportunities [I]
- Unified inbox (Gmail/Outlook sync)
- Thread-to-trip association & read/delivery status
- Bounce and failure handling & consent/opt-out management
- Template library & conditional sequences
- Behavioral triggers & personalization tokens
- Advisor approval & translation with human preview
- Time-zone scheduling & quiet hours
- Escalation based on non-response
- Conversation sentiment & anxiety detection
- Communication burden metrics & advisor workload routing
- Message provenance & AI draft vs human-edited comparison
- Brand consistency checks & spam/compliance controls

---

## 3.12 Disruption Management, Concierge, and Duty of Care

### Code-backed or surfaced [C]
- Trip monitoring & disruption listing
- Auto-rebooking endpoint
- Corporate duty-of-care cockpit
- Execution timeline, messaging & agent events
- Manual review, overrides & alerting foundations

### Explicitly documented [D]
- Ghost Concierge
- Flight and hotel disruption monitoring
- Downstream schedule impact & transfer rescheduling
- Late check-in notices & group cascade analysis
- Corporate offsite & creator-group monitoring
- Traveler live updates & zero-cost rebooking
- Human approval for financially consequential actions
- Autonomy modes & manual takeover switch
- Crisis orchestration dashboard & geolocation safety
- Threat alerts & climate-adaptive rerouting
- Consumer-rights & compensation support

### Implicit opportunities [I]
- Multi-source disruption ingestion
- Impact graph across flights, transfers, hotels, events, and meetings
- Recovery option search & cost/risk comparison
- Traveler prioritization & group splitting/reunification
- Emergency supplier sourcing & crisis runbooks
- Mass notifications & response acknowledgment
- Incident command view & duty-of-care check-ins
- Welfare status & emergency contact escalation
- Insurance claim preparation & compensation eligibility
- Refund tracking & service recovery credits
- Post-incident review & supplier-failure feedback
- Autonomy threshold configuration & financial reserve controls

---

## 3.13 Team, Workforce, Quality, and Knowledge Management

### Code-backed or surfaced [C]
- Team members & invitations
- Role and permission framework (RBAC)
- Team workload (assign, claim, reassign, return, escalate, unassign)
- High-value review gate, signoff & review queue
- Bulk review actions & agent drill-down analytics
- Assignment dashboard data & audit trail

### Explicitly documented [D]
- Junior-agent guided workflows & mandatory review gates
- Training modules & best-practices library
- Knowledge base & mistake-prevention warnings
- Personal & agency templates
- Performance scorecards & capacity planning
- Workforce gamification & simulation-based training
- Specialist-agent marketplace
- Knowledge retention upon employee departure

### Implicit opportunities [I]
- Skill-based, destination-based & language-based routing
- Complexity-based assignment & advisor capacity prediction
- Fairness and burnout constraints & shift/on-call coverage
- QA sampling & risk-based mandatory review
- Peer review & reviewer calibration
- Coaching recommendations & competency matrix
- Training from actual mistakes & certification workflows
- Shadow mode for juniors & progressive autonomy
- Knowledge article suggestions & expert escalation
- Cross-agency specialist contracting
- Role-specific dashboards & commission/performance alignment

---

## 3.14 Finance, Accounting, Payments, and Reconciliation

### Code-backed or surfaced [C]
- Payment read model & booking payment data
- Revenue analytics & yield calculations
- Booking collections & high-value gates

### Explicitly documented [D]
- Traveler payments, payment plans & deposits
- Multi-party payments & creator split payouts
- Supplier payments & commission tracking
- Invoice generation (including India GST & UPI support)
- Multi-currency accounts receivable/payable
- Price locks, refunds & agency service fees

### Implicit opportunities [I]
- Double-entry operational ledger
- Payment allocation, installment schedules & dunning
- Failed-payment recovery & refund workflow
- Cancellation fee allocation & chargeback evidence
- Trust-account handling & supplier payable schedule
- Cash-flow forecasting & commission accrual/reconciliation
- Commission statement import & dispute matching
- Team commission splits & referral payouts
- Tax invoice generation & GST/TDS treatment
- Currency gains/losses & accounting-system synchronization
- Expense cards & controlled field-spend cards
- Trip-level & agency-level P&L export
- Budget versus actual & financial approval workflows

---

## 3.15 Corporate Travel and Executive-Assistant Workflows

### Code-backed or surfaced [C]
- Corporate policy audit & duty-of-care cockpit
- Team approvals, group monitoring & execution timeline

### Explicitly documented [D]
- Corporate offsite intake & employee-grade rules
- Cabin-class policies & per-diem city caps
- Preferred hotel chains & out-of-policy exceptions
- Manager approval & EA self-justification
- Executive preference memory & arrival synchronization

### Implicit opportunities [I]
- Cost centers, departments & project codes
- HRIS synchronization & traveler eligibility
- Pre-trip approval & policy versioning
- Bleisure separation & spend forecasts
- Corporate cards & expense integration
- Traveler location check-in & security escalation
- Sustainability reporting & venue sourcing

---

## 3.16 Creator, Influencer, and Group-Host Workflows

### Code-backed or surfaced [C]
- Social enquiry parsing & teaser unmasking
- Proposal links & acceptance
- Trust scorecards, messaging & yield analysis

### Explicitly documented [D]
- Creator link-in-bio storefront & fast-paste mode
- Two-stage teaser & deposit funnel (masked details)
- Creator co-branding & group-host cockpit
- Creator/agency commission splits & group portal
- Host autonomy & brand-safety controls

### Implicit opportunities [I]
- Campaign-to-enquiry attribution & audience segmentation
- Waitlists, trip drops & limited inventory
- Affiliate links & sponsor attribution
- UGC rights & post-trip content collection
- Host certification & creator trip P&L

---

## 3.17 Analytics, Intelligence, and Experimentation

### Code-backed or surfaced [C]
- Summary, pipeline, revenue, team, funnel & bottleneck analytics
- Escalation analytics & product KPI endpoints
- Review analytics, alerts & export
- Agent drill-down & dashboard statistics
- KDD clusters, cluster detail, digest & frontier intelligence reports

### Explicitly documented [D]
- Conversion analysis & margin analysis
- Supplier performance & seasonal forecasting
- Lead-lifecycle analytics & autonomy performance
- Scenario replay, experiment lineage & autoresearch

### Implicit opportunities [I]
- Cohort retention, seat activation & time-to-first-value
- Proposal turnaround & proposal-to-acceptance
- Trip-stage velocity & revision burden
- Advisor utilization & quality by advisor
- Model cost per trip & model quality per task
- Human-edit distance & override frequency
- Customer-health score & churn prediction

---

## 3.18 Security, Privacy, Compliance, and Governance

### Code-backed or surfaced [C]
- Authentication (login, logout, refresh, password reset)
- Workspace joining & RBAC framework
- Tenant-scoped routes & audit routes
- LLM guard settings, autonomy settings & approval settings

### Explicitly documented [D]
- Tenant isolation & row-level security (RLS)
- PII scrubbers & local extraction
- Data privacy (GDPR, India DPDP)
- Audit-chain hashing & RAG citation provenance
- Compliance hard gates & traveler-safe leakage guards

### Implicit opportunities [I]
- SSO, SCIM, MFA & Passkeys
- Delegated & temporary access
- Regional data residency & encryption-key management
- Consent ledger & processing records
- Anomaly detection & SOC 2 / ISO 27001 control mapping
- Legal hold & evidence export

---

## 3.19 Agentic Runtime, Autonomy, Recovery, and Evaluation

### Code-backed or surfaced [C]
- Agent runtime status & runtime events
- Manual "run once" & recovery-agent foundations
- Agent events per trip & agentic trip evaluation
- LLM usage guard, autonomy settings & approval settings

### Explicitly documented [D]
- Multi-agent orchestrator & shadow agents
- Self-healing recovery & prompt-tuning agent
- Three-tier autonomy & human takeover switch
- Cost budgets & model fallbacks

### Implicit opportunities [I]
- Agent registry & capability manifests
- Per-agent budget & per-agent model routing
- Action simulation & dry run cards
- Reversible actions, idempotency & failure isolation
- Agent shadow mode & champion/challenger evaluation

---

## 3.20 Ecosystem, Network, and Marketplace

### Explicitly documented [D]
- Host-agency distribution & white-label agency platform
- DMC supplier portal & supplier marketplace
- Inter-agency specialist marketplace & cross-agency intelligence pooling

### Implicit opportunities [I]
- App marketplace & integration marketplace
- Supplier onboarding network & agency specialization directory
- API monetization & embedded decision engine
- Shared but privacy-safe learning & partner settlement rails

---

## 3.21 Frontier Lab (Preserved Explorations)

### Documented Frontier Research [F]
- Biometric wellness & jetlag mitigation
- Operational stress digital twin
- Spatial pre-visualization (Vision Pro / 3D NeRF)
- Dynamic trip magazines & climate-adaptive itineraries
- Orbital and sub-orbital space travel logistics
- Sovereign & diplomatic motorcade logistics
- Post-quantum identity & quantum-secure storage
- Autonomous resource futures & micro-climate SAR satellite AI
- Neurodiverse sensory optimization & 183-day tax residency tracking
- Smart contract milestone escrows & OSINT counter-surveillance
- Pet relocation logistics & extreme survival altitude ops
- VR anxiety rehearsal & inter-agency commission syndicates
- DNA & ancestry heritage search trips & family conflict mitigation
- 3-Michelin dining sniper & real-time currency spend cards

---

# 4. Persona-Driven Roadmap Matrix

## Agency-Side Personas

| Persona | Core Pain | Required Platform Features |
|---|---|---|
| **Solo Advisor** | Fragmented enquiries, memory burden, slow response | Native capture, drafts, follow-ups, CRM memory, quick proposals, templates, commission view |
| **Junior Advisor** | Does not know what is missing or unsafe | Guided workflow, hard blockers, knowledge retrieval, review gates, escalation, explanations |
| **Senior Advisor** | Too many interruptions and reviews | Risk-based review queues, advanced editing, reusable expertise, exception handling |
| **Agency Owner** | Quality variance, margin leakage, team visibility | Workload, assignments, revenue, margins, reviews, approval policies, operational dashboards |
| **Ops Coordinator** | Confirmations, suppliers, pickups, deadlines | Booking tasks, confirmations, manifests, supplier communication, timelines, incident handling |
| **Finance / Accounts** | Invoices, commissions, supplier payables | Ledger, AR/AP, commission matching, payouts, GST, accounting integrations |

## Customer & Partner Personas

| Persona | Core Pain | Required Platform Features |
|---|---|---|
| **Primary Trip Planner** | Coordinating everyone & admin load | Group collection, voting, documents, payment tracking, announcements |
| **Senior / Accessible** | Generic plans ignore real constraints | Accessibility evidence, mobility-aware routing, fatigue rules, verified suppliers |
| **UHNW Traveler** | Discretion, personalization, friction | Relationship memory, privacy, concierge, preferred suppliers, zero-app links |
| **DMC / Supplier** | Manual quotes, slow agency response | Rate ingestion, inventory, soft holds, supplier portal, yield visibility |
| **Corporate Travel Mgr** | Policy, cost, safety, reporting | Policy engine, duty of care, approval workflows, analytics |

---

# 5. Vertical Expansion Strategy

```
TIER A: CLOSEST CORE ICP (Months 1–12)
├── 1. Mid-market Outbound Leisure Agencies (4–15 seats) [PRIMARY ICP]
├── 2. Boutique & Specialist Agencies (Luxury, Family, Honeymoon, Adventure, Accessible)
├── 3. Inbound Tour Operators & DMCs
├── 4. Group & Multi-Day Tour Operators
└── 5. Host Agencies & Consortia Networks

TIER B: REUSABLE VERTICAL MODES (Months 12–24)
├── 6. Creator-Led Group Travel
├── 7. Corporate Offsites & Executive Travel
├── 8. MICE (Meetings, Incentives, Conferences, Exhibitions)
├── 9. Destination Weddings & Retreats
└── 10. Educational, Student & Sports Team Travel

TIER C: SPECIALIST OR REGULATED VERTICALS (Months 24+)
├── 11. Medical Travel & Wellness Sanatoriums
├── 12. Extreme Expedition Travel (Everest/Antarctica)
├── 13. Cruise & Private Yacht Charters
└── 14. Film, Production & Government Logistics

TIER D: FRONTIER LAB (Unscheduled Research)
└── Space Tourism, Post-Biological Travel, Civilizational Archives
```

---

# 6. Strategic Whitespace & Competitive Moats

Waypoint’s true strategic moats are built around **six core pillars**:

1.  **Decision OS vs. Content Generator**: Owning constraint evaluation, missing information discovery, risk auditing, and trade-off explanations.
2.  **Tri-Factor Optimization**: Simultaneously optimizing for Traveler Fit + Operational Fit + Commercial Margin.
3.  **Dual-Output Boundary**: Strict separation between internal decision context and traveler-safe communication.
4.  **Human-Controlled Agentic Autonomic Loop**: Monitor -> Detect -> Simulate -> Recommend -> Approve -> Execute -> Audit.
5.  **Cross-Lifecycle Memory**: The same canonical state powers intake, planning, pricing, documents, booking, operations, and retention.
6.  **Small-Team Operational Scaling**: Equipping a 4-seat agency with the quality control and yield of a 500-seat host agency.

---

# 7. Recommended Execution Horizons

## Horizon 0: Canonical Truth & Launch Integrity (Immediate)
1. Reconcile every claimed feature against current code and tests.
2. Select Primary ICP (Outbound Leisure Agencies, 4–15 seats).
3. Complete the core end-to-end launch journey:
   `Capture Enquiry -> Structured Trip -> Resolve Gaps -> Suitability Audit -> Source & Price -> Traveler Proposal -> Acceptance -> Booking Data/Docs -> Confirmation -> Operational Timeline`.

## Horizon 1: Habitual Agency Workflow (Months 1–6)
- **Frictionless Capture**: Chrome extension, Gmail/Outlook, WhatsApp webhooks, voice notes.
- **State Trust**: Server-sent event streams, optimistic UI reconciliation, field-level audit.
- **Client Memory**: Cross-trip profiles, household graphs, preference confidence.
- **Supplier & Rate Intelligence**: CSV/Excel rate ingestion, rate seasons, blackout dates, supplier comparisons.
- **Proposal-to-Acceptance**: Interactive proposals, trade-off views, deposit collection.

## Horizon 2: Lead-to-Cash & Booking Operations (Months 6–12)
- Traveler data collection & document verification.
- Booking tasks, supplier requests, confirmation parsing.
- Payments, invoices, commission reconciliation, supplier payables.
- In-trip communications & disruption handling.

## Horizon 3: Vertical Expansion Modes (Months 12–24)
- DMC / Supplier Portal Mode.
- Group & Multi-Day Operator Mode.
- Host-Agency White-Label Infrastructure.
- Creator & Corporate Offsite Modes.

## Horizon 4: Ecosystem & Platform Network (Months 24+)
- Developer Agent App Store & Partner API.
- B2B Supplier Clearinghouse & Intelligence Network.
- Embedded White-Label Banking APIs.

---

# 8. Anti-Roadmap (What NOT to Build Now)

1. **Do NOT build a generic consumer trip-planning chatbot**.
2. **Do NOT attempt to build a GDS from scratch**.
3. **Do NOT build a full corporate travel & expense (T&E) replacement**.
4. **Do NOT prioritize visual novelty (3D/NeRF) over workflow completion**.
5. **Do NOT expose full autonomy without mandatory human signoff on financial/legal actions**.
6. **Do NOT put speculative frontier concepts in the active sprint backlog**.

---

# 9. Ten Strategic Defaults

1. **Primary ICP**: Outbound and specialist travel agencies with 4–15 operating seats.
2. **Core Positioning**: Constraint-aware operations and revenue OS (not an AI itinerary generator).
3. **Immediate Focus**: Frictionless intake, relationship memory, supplier/rate intelligence, proposal conversion, booking readiness.
4. **First Adjacency**: DMC, supplier, and multi-day group operations.
5. **Second-Wave Modes**: Host agencies, creators, corporate EAs/offsites, MICE.
6. **B2C Role**: Public audit, traveler portal, and agency lead generation (not direct consumer SaaS).
7. **Autonomy Posture**: Guarded copilot by default, with mandatory human approval for financial, legal, safety, and relationship-risk actions.
8. **Roadmap Architecture**: One canonical registry with separate Current, Adjacent, and Frontier horizons.
9. **Frontier Policy**: Preserve all research ideas in the Frontier Lab, schedule none without an explicit business decision.
10. **Document Destination**: Written to canonical path `Docs/CANONICAL_PRODUCT_OPPORTUNITY_AND_ROADMAP_REGISTRY_2026-08-04.md`.

---

*This document represents the absolute canonical ground truth, unifying codebase reality, explicit documentation, market opportunities, and long-term research frontiers.*
