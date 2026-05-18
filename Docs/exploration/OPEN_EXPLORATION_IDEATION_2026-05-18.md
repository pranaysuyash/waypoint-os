# Open Exploration Ideation — Iteration 1 (2026-05-18)

**Date**: 2026-05-18
**Status**: Open ideation. Not exploration docs yet — this surfaces and ranks candidates so you can pick which deserve full treatment.
**Mode**: Peer-level opinions, opinionated rankings, push-back where warranted.
**Parent**: [../EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)
**Sibling**: [OFF_MAP_CANDIDATES_2026-05-18.md](OFF_MAP_CANDIDATES_2026-05-18.md) (data/ML-specific)

---

## Framing

The existing map is heavily weighted toward: data/ML pipelines, AI decisions, integration architecture, eval frameworks. Recent additions extended that axis. This document deliberately spreads to **other axes** — product surfaces, market shape, domain depth, people/process inside the agency, compliance, customer-facing surfaces — so we're not over-indexing on one dimension.

For each candidate I give: what it is, why it matters here (concrete tie to the product), what it doesn't solve, my honest rank, and whether it should become a full exploration doc.

I will be wrong about some of these — that's the point. Push back, redirect, kill, or expand any of them.

---

## CATEGORY A — Trust, Safety, and the Operator–AI Relationship

### A1. AI Agent Autonomy Levels Framework — HIGH

**What**: An explicit, configurable framework that defines, per decision class, whether the AI: (L0) does nothing, (L1) suggests, (L2) acts with confirmation, (L3) acts and notifies, (L4) acts silently. Per-agency, per-role, per-decision-class. Auditable.

**Why it matters here**: The product is moving toward agentic behavior but the implicit autonomy contract is unclear. Today every new AI action triggers a debate about "should this be automatic?" An explicit framework converts that debate into config. Pairs with override controls and explainability — same trust surface.

**What it doesn't solve**: model quality, hallucination, edge cases. It's a *policy* layer, not a *capability* layer.

**Recommend full doc?** **Yes, soon**. Foundational for everything agentic. Without it, agentic features ship with ad-hoc autonomy decisions baked in and become impossible to govern later.

---

### A2. Provenance / Reversibility / Audit-Grade Decision Ledger — MEDIUM-HIGH

**What**: Beyond debug-level explainability (off-map #1), this is regulatory-grade provenance: every customer-affecting decision is logged with full input/output/version/timestamp, and every action is reversible within an SLA. Required for travel agencies operating in regulated geos.

**Why it matters here**: Travel is regulated (ABTA, ATOL, ARC, GDPR, payment regs). At some point, "show me every AI decision that touched this customer's booking" becomes a hard requirement, not nice-to-have. Building this in early is dramatically cheaper than retrofitting.

**What it doesn't solve**: doesn't replace explainability (different audience — auditors vs operators); doesn't substitute for compliance certification.

**Recommend full doc?** **Yes, paired with A1** — same underlying infrastructure. The audit ledger is the substrate; explainability is one consumer; autonomy framework is another.

---

### A3. Disruption / Disaster Response Workflows — MEDIUM

**What**: Specialized workflows for the moments that define an agency's reputation: flight cancelled, hurricane hits, country becomes unsafe, supplier defaults. Surfaces all affected trips, suggests rebooking, drafts customer comms, tracks resolution.

**Why it matters here**: This is where agencies prove their value vs DIY booking. Today the workflow is ad-hoc and stressful. Done well, it's a real moat — Booking.com and Expedia genuinely cannot do this.

**What it doesn't solve**: doesn't replace the human judgment that *defines* a great agency in these moments. It tools it.

**Recommend full doc?** **Maybe** — depends on whether disruption-handling is a v1 priority or a v2 wedge. Worth a scoping conversation before a full doc.

---

## CATEGORY B — Surfaces We Don't Have Yet

### B1. Customer-Facing Surfaces (Status Page, Document Collection, Traveler App) — HIGH

**What**: Today the app is operator-facing. Adding customer-facing surfaces — shareable trip status page, document collection portal, in-trip companion, payment portal — fundamentally changes the product surface and the value capture.

**Why it matters here**:
- Every operator's "where are we with my trip?" inbound message is a missing self-serve surface.
- Document collection (passports, insurance, visa) is currently friction across email; a portal collapses that.
- An in-trip companion (itinerary, supplier contacts, local info) is a wedge competitors don't have.
- Each surface generates labeled data that improves the agent.

**What it doesn't solve**: doesn't change the agency-facing core; doesn't replace operator judgment; doesn't generate value for B2B-only positioning if that's the strategy.

**Recommend full doc?** **Yes, high priority**. This is a category-level expansion, not a feature. Deserves a scoping doc that maps which customer-facing surfaces are wedges, which are table-stakes, and which are out of scope.

---

### B2. Voice / WhatsApp / Multi-Modal Intake — HIGH

**What**: Today's intake is text-first. Travel agencies live on the phone and WhatsApp. Voice-note transcription, phone-call summarization, WhatsApp threaded intake — each is a real wedge.

**Why it matters here**: Integration Architecture (#1) already flags WhatsApp as priority research. This goes deeper: voice intake is the natural format for travel customers describing trips. Operators *already* take voice notes and re-type. An LLM-friendly voice intake pipeline collapses that step.

**What it doesn't solve**: doesn't fix the extractor's quality on novel inputs; doesn't replace text-channel handling.

**Recommend full doc?** **Yes**, as an extension/companion to Integration Architecture (#1) rather than a standalone. The integration question and the modality question are coupled.

---

### B3. Mobile-First Operator Workflow — MEDIUM

**What**: Agencies often work from supplier sites, airports, in-destination, while traveling. A mobile-first operator surface (not just responsive — purpose-built) handles in-trip support, supplier visits, on-call coverage.

**Why it matters here**: The desktop-first assumption breaks down at the moments that matter (disruption, in-trip). Pairs with disruption workflows (A3).

**What it doesn't solve**: doesn't replace the desktop workflow for intake-heavy tasks; not a wedge by itself.

**Recommend full doc?** Not yet. Worth holding until A3 (disruption) is scoped — they share design constraints.

---

## CATEGORY C — Domain Depth Nobody Else Has

### C1. Supplier-Side Intelligence — HIGH

**What**: Agencies live or die by supplier relationships. Surface supplier reliability scores (from booking history, dispute history, cancellation rates), supplier diversification metrics, lead-time data, negotiation insights. Could become "Glassdoor for travel suppliers" inside the product.

**Why it matters here**: Nothing in the existing map addresses supplier-side data. Every agency rebuilds this in spreadsheets. A computed, mineable, sharable supplier intelligence layer is a defensible moat that competitors can't easily replicate (it requires multi-agency data).

**What it doesn't solve**: doesn't fix supplier integrations (separate problem); doesn't replace human relationships with suppliers.

**Recommend full doc?** **Yes**. Distinct from the data-mining topics because the data is operational, not AI-decision-derived. Could be the highest-leverage moat in the entire product if executed well.

---

### C2. Operational Risk Surface — MEDIUM-HIGH

**What**: Travel agencies carry real balance-sheet risk: refund exposure, supplier default risk, currency exposure, cancellation exposure, ATOL/insurance exposure. Surface this in real time so owners can manage it. Adjacent to compliance but distinct.

**Why it matters here**: Owner persona is undersized in the existing map. Owners think in P&L and risk terms; today nothing in the product speaks their language. Adding this opens the owner buyer/champion dynamic.

**What it doesn't solve**: doesn't replace the agency's accounting or insurance; doesn't substitute for financial advice.

**Recommend full doc?** **Yes**, paired with C3 below — both are owner-persona concerns.

---

### C3. Trip Economics & Customer LTV — MEDIUM

**What**: True profitability per trip type, per supplier, per channel; customer lifetime value per repeat segment; cohort retention; channel attribution. BI layer for agency owners.

**Why it matters here**: Pairs with C2 — owner-persona surface. Distinct from #10 (Pricing & Monetization, which is Waypoint→agency); this is agency→customer economics.

**What it doesn't solve**: doesn't optimize pricing automatically; doesn't replace BI tools the agency may already use.

**Recommend full doc?** **Yes**, with C2.

---

### C4. Long-Term Customer Memory — MEDIUM

**What**: Beyond per-trip data, accumulate per-customer profiles across trips (with explicit consent) — preferences, dietary, family composition over time, travel style evolution. Compounds value per repeat customer.

**Why it matters here**: Repeat business is where agency margins live. Today every trip starts cold even for a 10-trip customer. Memory is differentiation.

**What it doesn't solve**: cold-start customers, privacy-sensitive segments, GDPR right-to-be-forgotten without careful design.

**Recommend full doc?** Worth scoping. Has real privacy/consent design problems that need addressing before any implementation.

---

## CATEGORY D — Business Model / Market Shape

### D1. Integration-as-Platform (Supplier Self-Onboarding) — MEDIUM, defer

**What**: Instead of building one supplier integration at a time, design a platform where suppliers integrate *themselves* (think Stripe's developer surface). Two-sided market dynamics.

**Why it matters here**: Long-term, integration count is the killer constraint. Self-serve supplier integration scales where managed integration doesn't.

**What it doesn't solve**: chicken-and-egg (no suppliers want to integrate with a small platform); doesn't help v0/v1 product.

**Recommend full doc?** **Document, explicit defer**. Real strategic question once Waypoint has supplier-side leverage. Premature now.

---

### D2. Sustainability / Carbon Accounting Wedge — LOW-MEDIUM

**What**: Per-trip carbon estimate, agency-level emissions, customer-facing offset options, corporate-travel compliance with sustainability mandates.

**Why it matters here**: Real and growing for corporate travel, emerging for premium leisure. Could be a niche wedge. Honest read: probably not a top-3 priority for SMB travel agencies right now, but real in 3-5 years.

**What it doesn't solve**: doesn't change core workflow; doesn't help agencies without sustainability-minded customers.

**Recommend full doc?** Not yet. Track as map entry; revisit if corporate-travel segment becomes a real GTM target.

---

### D3. Marketplace Dynamics & Cross-Agency Network Effects — LOW, defer

**What**: At scale (many agencies), cross-agency referrals, white-label, agency-of-agencies, shared supplier intelligence. Network-effects layer on top of the SaaS layer.

**Why it matters here**: Strategic — defines whether Waypoint stays a tool or becomes a network.

**Recommend full doc?** Not yet. Premature until Waypoint has multi-agency scale. Document as a parked strategic question.

---

## CATEGORY E — People & Process Inside the Agency

### E1. Agent Collaboration & Multi-Operator Semantics — MEDIUM-HIGH

**What**: When multiple operators touch the same trip or customer: presence ("Sarah is editing"), conflict resolution, handoff semantics, who-owns-what. Becomes acute at agency size > 3.

**Why it matters here**: Operational pain that scales with agency size. Larger agencies (the higher-ARR target) hit this first. Today probably ad-hoc / break-the-glass.

**What it doesn't solve**: doesn't replace internal communication norms; doesn't fix understaffing.

**Recommend full doc?** **Yes** — distinct enough from real-time collab patterns we'd find elsewhere because the semantics here are travel-specific (who owns the supplier conversation? who's primary on the customer relationship?).

---

### E2. Knowledge Management / Institutional Memory — MEDIUM

**What**: When a senior agent leaves, their knowledge walks. Capture, retrieval, transfer. Tribal knowledge about specific destinations, supplier quirks, regulatory edges, customer histories.

**Why it matters here**: Travel agency turnover is real. Knowledge loss is real cost. Pairs with C4 (customer memory) and C1 (supplier intelligence) — different facets of the same institutional-memory problem.

**Recommend full doc?** Useful, but consider folding into C1+C4 rather than standing alone.

---

### E3. Onboarding & Training (Operator + Agency) — MEDIUM

**What**: Junior agent ramp-up paths, new agency onboarding, role-based progressive disclosure, in-product coaching loops. Affordances (existing topic #21) starts this; full onboarding strategy doesn't exist.

**Why it matters here**: Time-to-value for new operators and new agencies is a critical retention metric. Currently implicit; deserves explicit design.

**Recommend full doc?** Worth scoping, especially the agency-onboarding side — that's the first impression for the buyer.

---

### E4. Agency-Level Analytics & Coaching (Owner Persona) — MEDIUM-HIGH

**What**: Aggregate operator behavior into owner-facing insights: who's productive, where's training needed, what's the team workflow look like, what's our team's strength profile. Distinct from BI (C3): this is people-ops for the agency.

**Why it matters here**: Owner persona is undersized. Owners buy and renew; their dashboard needs are different from operators'.

**Recommend full doc?** **Yes**, paired with C2+C3 as a coherent owner-surface workstream.

---

## CATEGORY F — Compliance & Global

### F1. Travel-Specific Compliance Stack — MEDIUM (mandatory at certain geos)

**What**: ABTA / ATOL / ARC / IATA / GDPR / PCI / sanctions screening / age-rules / minor-traveler protections / health-document handling. The map mentions security/compliance generically (#3); travel-specific compliance is its own beast.

**Why it matters here**: Hard requirement for UK/EU expansion. Hard requirement for many corporate contracts. Not optional once you cross certain thresholds.

**What it doesn't solve**: doesn't replace certification work; doesn't make the agency itself compliant (it tools them).

**Recommend full doc?** **Yes**, scoped per-geography rather than as one giant doc. Start with the geo you're targeting first.

---

### F2. Multi-Language / Cross-Cultural Intake — MEDIUM

**What**: Global agencies operate in multiple languages. Intake in any language, cultural-norm awareness in communication patterns. The extractor probably assumes English.

**Why it matters here**: Limits market reach if not addressed. Real complexity in extractors and validators.

**Recommend full doc?** Worth scoping but secondary to other items unless international GTM is imminent.

---

## SUMMARY — MY HONEST RANKING

| Rank | Topic | Category | Recommend full doc next round? |
|---|---|---|---|
| HIGH | AI Agent Autonomy Levels (A1) | Trust | **Yes** |
| HIGH | Customer-Facing Surfaces (B1) | Surfaces | **Yes** |
| HIGH | Supplier-Side Intelligence (C1) | Domain | **Yes** |
| HIGH | Voice / WhatsApp / Multi-Modal Intake (B2) | Surfaces | **Yes (paired with #1)** |
| MED-HIGH | Audit-Grade Decision Ledger (A2) | Trust | **Yes (paired with A1)** |
| MED-HIGH | Operational Risk Surface (C2) | Domain | **Yes (paired with C3+E4)** |
| MED-HIGH | Agent Collaboration & Multi-Operator (E1) | People | **Yes** |
| MED-HIGH | Agency-Level Analytics for Owners (E4) | People | **Yes (paired with C2+C3)** |
| MED | Trip Economics & Customer LTV (C3) | Domain | Yes (paired) |
| MED | Disruption / Disaster Response (A3) | Trust | Scope before full doc |
| MED | Travel-Specific Compliance (F1) | Compliance | Yes, per-geography |
| MED | Long-Term Customer Memory (C4) | Domain | Scope, privacy questions |
| MED | Knowledge Management (E2) | People | Fold into C1+C4 |
| MED | Onboarding & Training (E3) | People | Scope agency-onboarding |
| MED | Multi-Language Intake (F2) | Compliance | Scope, secondary |
| LOW-MED | Sustainability / Carbon (D2) | Business | Map only |
| MED | Mobile-First Operator UX (B3) | Surfaces | Defer, pair with A3 |
| LOW-defer | Integration-as-Platform (D1) | Business | Document, defer |
| LOW-defer | Marketplace Dynamics (D3) | Business | Document, defer |

## STRONGEST CROSS-CONNECTIONS

Several of these compound when paired:

```diagram
╭──────────────────────────╮     ╭───────────────────────────╮
│ A1 Autonomy Framework    │────▶│ A2 Audit Ledger           │
│ (policy)                 │     │ (substrate)               │
╰──────────┬───────────────╯     ╰─────────────┬─────────────╯
           │                                   │
           └──────────────┬────────────────────┘
                          ▼
              ╭─────────────────────────────╮
              │ Explainability Layer        │  ← off-map #1
              │ (consumer of both)          │
              ╰─────────────────────────────╯

╭──────────────────────────╮
│ C2 Operational Risk      │
│ C3 Trip Economics        │──┐
│ E4 Owner Analytics       │  │  Owner-persona
│                          │──┴─▶  workstream
╰──────────────────────────╯

╭──────────────────────────╮
│ C1 Supplier Intelligence │     One of the strongest
│                          │──▶  long-term moats in the
╰──────────────────────────╯     entire product
```

## RECOMMENDED NEXT ACTIONS (My Picks for You to Approve/Reject/Reorder)

If you want **deepest-leverage moats**: full doc on **C1 Supplier-Side Intelligence**.
If you want **clearest near-term wedge**: full doc on **B1 Customer-Facing Surfaces** or **B2 Voice/WhatsApp Intake**.
If you want **foundational governance work**: paired full docs on **A1 Autonomy Framework + A2 Audit Ledger**.
If you want **owner-persona traction**: paired full docs on **C2 + C3 + E4**.

## WHAT I DELIBERATELY DID NOT INCLUDE

- Generic "AI co-pilot for X" framings — too vague, no real wedge identified.
- Crypto/web3/blockchain for travel — no honest use case here.
- Generative video/marketing content for agencies — adjacent, but a different product.
- Hardware/IoT angles (smart luggage, etc.) — not a software wedge.
- VR/AR previewing of destinations — interesting but capital-intensive, premature.

If any of these *should* be considered, push back and I'll add them.

---

## NEXT ITERATION

I'll continue surfacing ideation rounds. Future iterations to consider:
- Adjacent sectors (corporate travel, group/MICE, cruise, expedition, luxury concierge — each has different problem shape).
- Adjacent personas (the **traveler's family/booker**, the **HR/EA buying corporate**, the **destination management company**).
- Adjacent geographies (each market has different compliance + cultural norms).
- Adjacent verticals beyond travel that share the same problem shape (event planning, wedding planning, real-estate concierge, healthcare coordination — all are "high-context, multi-party, time-sensitive coordination with vendor reliability concerns").

If any of these directions sound interesting, say which and I'll deepen.

---

*Open ideation document. Will be updated in subsequent iterations as more topics surface.*
