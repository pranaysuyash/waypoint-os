# Research: Real-World Validation Strategy

**Status**: 🔵 Specification — From Lab to Production  
**Topic ID**: 19  
**Parent**: [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)  
**Last Updated**: 2026-06-21

### Current Live Evidence (2026-06-21)

- Authenticated login works with `newuser@test.com` / `testpass123`.
- The main overview loads as a live command center.
- The planning list groups duplicate-looking work into fewer cards.
- The planning status label now reads `Ready to build options` instead of `Need Trip Options`.
- A valid trip deep link opens a real trip workspace.
- A stale deep link now falls back to a recovery screen that tells the operator to return to Trips in Planning and reopen the trip.
- A thin Dubai intake still blocks on missing origin/budget, which is the right call for a first quote.
- After restarting the backend, an explicit `Origin city: Nairobi` / `Budget: USD 4,500` intake now promotes to `Ready to build options`.
- Ready trips now show `Recommended details` as optional refinements instead of sounding like blockers.
- The Zanzibar intake rerun now stores `destination: Zanzibar` in the trip record, which fixes the earlier origin-leak regression.
- The inbox operations cards now keep recency in a single SLA chip instead of duplicating it in the metrics row, making the dense queue easier to scan.
- Lead inbox rows with missing destinations now fall back to trip type instead of rendering `Unknown leisure`.
- Lead inbox rows with missing destinations now headline as `Trip details incomplete` for faster queue scanning.
- The inbox header count label no longer has duplicate wrapper markup after the role-view cleanup.
- The team-lead inbox profile now shows ownership, SLA, and priority without repeating the recency metric.
- Finance and fulfillment inbox profiles now show `Options` for stage instead of the raw `options` enum, which makes the queue read more like an operator surface than a backend payload.
- Grouped quote examples now avoid repeating the same title twice, so the quote list reads more like a summary and less like a duplicated payload.
- The quote review queue now falls back to `Trip details incomplete` for unknown destinations instead of showing `Unknown leisure`.
- The trips planning stage trail now renders as a clean plain-language progress line instead of a punctuation mashup.
- The Bali intake now completes when the traveler message uses explicit origin, party size, destination, travel dates, budget, and visa-risk wording.
- The date parser now understands common month-day ranges like `July 10 to July 16`.
- `visa_concerns_present` now carries heuristic maturity, which removes the discovery validation hard-fail from the live Bali flow.
- The generated trip route still returns `Unauthorized` after clicking `View Trip`, so the workbench handoff into the trip workspace remains a separate bug.
- The live simulation doc is available at [Docs/travel_agency_main_app_simulation_2026-06-21.md](../travel_agency_main_app_simulation_2026-06-21.md).

### Current Build Wording

- Decision-state labels now say `Waiting on Customer` instead of `Need More Info`.

---

## The Challenge

Lab tests verify the system works in theory. Real-world validation proves it works in practice.

**The gap**: A system that passes all unit tests can still fail in production because:
- Real agency notes are messier than test fixtures
- Real customers ask unexpected follow-ups
- Real margins matter more than test scores
- Real agents have habits and workflows

---

## Validation Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REAL-WORLD VALIDATION ROADMAP                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 0          PHASE 1           PHASE 2           PHASE 3               │
│  Lab Validated →  Shadow Mode   →  Pilot Agency  →  Scale                  │
│  (Now)            (2 weeks)        (1 month)        (3+ months)            │
│                                                                             │
│  • Unit tests     • Run parallel    • 1-2 agencies  • Multiple agencies    │
│  • Fixtures       • Compare to      • Real quotes   • Production load      │
│  • Evals          • human output    • Full feedback • Continuous improve   │
│                   • No customer     • Iterate       • Platform mode        │
│                     exposure                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Lab Validated (Current)

### What We Have

| Component | Status | Evidence |
|-----------|--------|----------|
| NB01 Intake | ✅ | Unit tests, extraction fixtures |
| NB02 Gap/Decision | ✅ | 30 scenario tests, 100% pass |
| NB03 Session Strategy | ✅ | 15 tests, all decision states |
| Contracts | ✅ | Clear input/output specs |

### Exit Criteria

- [x] All unit tests passing
- [x] Fixture-driven eval running
- [x] Golden path demo working
- [ ] End-to-end fixture success rate >80%

---

## Phase 1: Shadow Mode (2 weeks)

### Concept

Run the system **in parallel** with human agents. System generates proposals, agents don't see them (initially). We compare system output to human output.

### Setup

```python
# Shadow mode implementation
class ShadowModeCollector:
    """
    Capture real agency inputs, run through system, store results.
    """
    
    def on_new_lead(self, lead: AgencyLead):
        # Always route to human agent (control)
        human_agent.assign(lead)
        
        # Also run through system (shadow)
        system_result = pipeline.run(lead.raw_input)
        
        # Store for comparison
        db.shadow_runs.insert({
            "lead_id": lead.id,
            "timestamp": now(),
            "raw_input": lead.raw_input,
            "system_proposal": system_result.proposal,
            "system_decision": system_result.decision_state,
            "system_confidence": system_result.confidence,
        })
```

### Data Collection

For each shadow run, capture:

| Field | Purpose |
|-------|---------|
| Raw input | What the customer actually sent |
| System proposal | What the system generated |
| Decision state | What the system decided |
| Generation time | Speed benchmark |
| Human proposal (manual) | What agent actually sent (collected after) |

### Comparison Analysis

```python
def analyze_shadow_results():
    """
    Compare system output to human output.
    """
    results = db.shadow_runs.find().limit(100)
    
    metrics = {
        "coverage": 0,  # Did system produce a proposal?
        "time_ratio": [],  # System time / Human time
        "human_override_rate": 0,  # How often human changed
    }
    
    for result in results:
        # Did system produce output?
        if result.system_proposal:
            metrics["coverage"] += 1
        
        # Time comparison
        if result.human_proposal_time:
            metrics["time_ratio"].append(
                result.system_generation_time / result.human_proposal_time
            )
        
        # Did human change significantly?
        if result.human_proposal:
            similarity = compare_proposals(
                result.system_proposal, 
                result.human_proposal
            )
            if similarity < 0.7:  # Less than 70% similar
                metrics["human_override_rate"] += 1
    
    return metrics
```

### Success Criteria

| Metric | Target | Why |
|--------|--------|-----|
| Coverage | >90% | System handles most real inputs |
| Time ratio | <0.3 | System is 3x+ faster than human |
| Override rate | <50% | Human doesn't change most of the time |
| Safety incidents | 0 | No harmful recommendations |

### Exit Criteria

- [ ] 100+ shadow runs collected
- [ ] Coverage >90%
- [ ] No safety issues
- [ ] Agent feedback gathered ("would you use this?")

---

## Phase 2: Pilot Agency (1 month)

### Concept

One agency uses the system for **real quotes**. Full integration, real customers, but limited scope.

### Partner Selection

**Ideal pilot partner**:
- Small agency (1-3 agents) — easier coordination
- Tech-comfortable owner — less change resistance
- High quote volume — more data faster
- Mix of destinations — tests breadth
- Willing to give feedback — critical for iteration

**Incentive for partner**:
- Free use during pilot
- Priority support
- Input into product direction
- Discounted pricing post-pilot

### Scope Limits

| Limit | Rationale |
|-------|-----------|
| Max 2 destinations | Reduce complexity |
| Standard packages only | Template-based generation |
| Agent review required | Safety net |
| Business hours only | Support availability |

### Integration

```python
# Pilot integration
class PilotIntegration:
    """
    Production integration for pilot agency.
    """
    
    def generate_quote(self, request: QuoteRequest) -> QuoteResponse:
        # Run pipeline
        result = pipeline.run(request)
        
        # Always require agent review (pilot safety)
        if result.decision_state == "PROCEED_TRAVELER_SAFE":
            return QuoteResponse(
                status="AGENT_REVIEW_REQUIRED",
                proposal=result.proposal,
                internal_sheet=result.internal_sheet,
                ai_confidence=result.confidence,
            )
        else:
            return QuoteResponse(
                status="NEEDS_MORE_INFO",
                questions=result.questions,
            )
    
    def agent_approves(self, proposal_id: str, feedback: dict):
        """
        Agent reviews and approves/edits proposal.
        """
        proposal = db.proposals.get(proposal_id)
        
        # Track changes
        diff = calculate_diff(proposal.ai_version, proposal.agent_edited_version)
        
        # Store feedback
        db.feedback.insert({
            "proposal_id": proposal_id,
            "agent_id": feedback.agent_id,
            "changes": diff,
            "sent_to_customer": feedback.sent,
            "conversion_outcome": None,  # Filled later
        })
        
        # Send to customer
        if feedback.sent:
            email.send(proposal.agent_edited_version, to=proposal.customer_email)
```

### Feedback Loop

**Daily**:
- Agent logs issues encountered
- System team reviews "agent changed" proposals
- Quick fixes deployed

**Weekly**:
- Review conversion outcomes
- Identify patterns in agent changes
- Adjust templates/prompts

**Exit Interview**:
- Structured feedback session
- What worked, what didn't
- Would they pay for this?

### Success Criteria

| Metric | Target |
|--------|--------|
| Quotes generated | >50 |
| Agent adoption | >70% of eligible quotes |
| Avg agent changes | <3 per proposal |
| Time saved per quote | >50% |
| Conversion rate | Within 5% of pre-pilot baseline |
| Agent satisfaction | >7/10 |

### Exit Criteria

- [ ] 50+ quotes generated
- [ ] Agent satisfaction >7/10
- [ ] No major safety issues
- [ ] Clear path to product-market fit

---

## Phase 3: Scale (3+ months)

### Concept

Multiple agencies, production workload, continuous improvement.

### Rollout Strategy

**Cohort 1 (Month 1)**:
- 3-5 agencies
- Similar profile to pilot
- Intensive support

**Cohort 2 (Month 2)**:
- 10-15 agencies
- Self-serve onboarding
- Community support

**Cohort 3+ (Month 3+)**:
- Open access
- Automated onboarding
- Usage-based pricing

### Feature Flags

```python
# Gradual feature rollout
FEATURE_FLAGS = {
    "auto_send": False,  # Always require agent review initially
    "multi_destination": False,  # Start with single destination
    "custom_packages": False,  # Start with templates only
    "voice_integration": False,  # Text only initially
}

# Enable per agency
def can_use_feature(agency_id: str, feature: str) -> bool:
    agency = db.agencies.get(agency_id)
    return FEATURE_FLAGS[feature] or agency.beta_features.get(feature, False)
```

### Pricing Model

**Option A: Per Quote**
- ₹50-100 per quote generated
- Aligns with value (time saved)
- Easy to understand

**Option B: Monthly Subscription**
- ₹3000-5000/month for small agency
- Unlimited quotes
- Predictable revenue

**Option C: Hybrid**
- Base subscription: ₹2000/month (includes 50 quotes)
- Overage: ₹30/quote
- Best of both worlds

**Pilot learning**: Which model do agents prefer?

---

## Success Metrics (Full Production)

### Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Monthly Active Agencies | 50+ | Count of agencies generating >5 quotes/month |
| Quotes per Agency | 20+/month | Average usage |
| Gross Margin | >70% | Revenue - AI costs - infra |
| Churn Rate | <10%/month | Agencies stopping usage |
| NPS | >40 | Agent satisfaction survey |

### Product Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Generation Success Rate | >95% | Proposals successfully generated |
| Agent Edit Rate | <30% | Proposals changed significantly |
| Time to Quote | <30 min | Median time from request to proposal |
| Conversion Lift | +10% | vs pre-system baseline |

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Latency | <5s p99 | End-to-end generation time |
| Error Rate | <1% | Failed generations |
| Cost per Quote | <₹10 | LLM + infra costs |

---

## Risk Mitigation

### Risk: System Generates Bad Proposal

**Mitigation**:
- Phase 1: Shadow mode (no customer exposure)
- Phase 2: Agent review required
- Safety checks before any customer-facing output
- Kill switch (immediate disable)

### Risk: Agents Don't Adopt

**Mitigation**:
- Start with friendly pilot partner
- Address feedback immediately
- Show time savings clearly
- Make it easier than current workflow

### Risk: Cost Unsustainable

**Mitigation**:
- Track cost per quote from day 1
- Optimize prompts for efficiency
- Cache common responses
- Cap usage if needed

### Risk: Data Privacy Concerns

**Mitigation**:
- Clear data handling policy
- Customer data encrypted
- No data sharing without consent
- Option for on-premise deployment

---

## Timeline Summary

| Phase | Duration | Key Activities | Success Criteria |
|-------|----------|----------------|------------------|
| 0. Lab | Now | Tests, fixtures | 80%+ fixture pass |
| 1. Shadow | 2 weeks | Parallel running | 90% coverage, no safety issues |
| 2. Pilot | 4 weeks | Real quotes, 1 agency | 50+ quotes, agent satisfaction >7 |
| 3. Scale | 3+ months | Multi-agency rollout | 50+ active agencies |

---

## Immediate Next Steps

1. **Identify pilot partner** — Reach out to 3-5 agencies, gauge interest
2. **Build shadow mode collector** — Simple tool to capture real inputs
3. **Create agent feedback form** — Structured way to collect opinions
4. **Define safety checklist** — What must be true before customer exposure

---

*This is a roadmap for getting from lab to production.*

## Live Chrome Verification Addendum

- Verified in the original Chrome session via CDP/Playwright on `http://localhost:3010`
- A small-agency call capture for `Singapore` with `2 adults and 1 child` now preserves `party_size = 3` instead of collapsing to `1`
- `Budget INR 2.5L` now parses to `250000` and displays as compact INR `₹2.5L` instead of `₹3`
- The workbench → trip-page handoff remains healthy after the parser and formatter fix

## Live Chrome Addendum: Strategy Route Preview

- Verified in the original Chrome session via CDP/Playwright on `http://localhost:3010/trips/trip_a4cd135cf395/strategy`
- The trip options page now renders an actual strategy brief instead of the previous `Options builder not connected yet` placeholder
- The live page shows the operator-facing structure we want: session goal, suggested opening, priority sequence, tone, guardrails, and assumptions when needed
- The backend trip response now exposes `strategy`, which keeps the persisted trip contract aligned with the UI
- This closes the specific gap where the app was already doing the work but the route still behaved like it was disconnected

## Live Chrome Addendum: Destination Disambiguation

- Verified in the original Chrome session via CDP/Playwright on `http://localhost:3010/workbench?draft=new&tab=intake&capture_mode=call&entry=new`
- A Nairobi-based agency request initially misread `Nairobi` as the trip destination, producing a bad `Nairobi leisure trip` title
- After tightening the destination filter and rerunning the same scenario, the stored trip resolved to `Zanzibar` with `Origin Nairobi`
- The same rerun also showed the strategy brief no longer repeating the same internal-data warning twice
- This is the kind of live issue that matters because agency metadata should never override the traveler’s real destination intent

## Live Chrome Addendum: Ready CTA Advance

- Verified in the original Chrome session via CDP/Playwright on the Zanzibar trip intake page
- The `Continue to options` CTA now routes to the strategy page in the no-recommended-details state
- Before the fix the button was enabled but did nothing, which made the ready state feel broken
- This keeps the last intake action aligned with the promise the app makes when it says the trip is ready

## Live Chrome Addendum: Ready CTA Copy Alignment

- Verified in the original Chrome session via CDP/Playwright on a ready Bali trip with INR budget, destination, and dates captured
- The footer CTA was updated from `Continue to options` to `Build trip options` so the label matches the actual processing action
- The route to options remains available through the top `Open options` link, so navigation and processing are now visually distinct
- This removes a confusing promise mismatch right at the moment the trip becomes ready

## Live Chrome Addendum: Strategy Placeholder Cleanup

- Verified in the original Chrome session via CDP/Playwright on the ready Bali trip strategy page
- The strategy preview previously rendered `Check TBD and Bali together` when origin was missing
- The preview builder now falls back to `Check the trip details around Bali`, which avoids leaking placeholder tokens into the live options brief
- This is a small wording change, but it materially improves the operator’s trust in the generated brief

## Live Chrome Addendum: Output Empty-State Handoff

- Verified in the original Chrome session via CDP/Playwright on the Bali trip output page
- The output page previously routed the operator back to Options even when quote assessment context already existed
- The empty state now routes to Quote Assessment when that context is present, which is a better reflection of the trip lifecycle
- The copy now explicitly says the traveler-safe output bundle still needs to be generated, so the page no longer implies the wrong next step

## Live Chrome Addendum: Timeline Stage Label Cleanup

- Verified in the original Chrome session on the trip timeline page after restoring the live auth session
- The timeline card badge previously showed raw `Unknown` for an unset stage
- The shared timeline label helper now renders `Stage not set`, which keeps the operational timeline readable and consistent with the rest of the app
- This is a small label fix, but it removes a confusing raw enum leak from the operator-facing history view

## Live Chrome Addendum: Overview Queue Language Cleanup

- Verified in the original Chrome session on the overview page after normalizing the shared date-window formatter
- The queue previously showed `Travel TBD` in enquiry and quote cards when the date window was missing
- The same queue now renders `Travel Dates to confirm`, which reads as an actual planning state rather than a placeholder
- Quote rows with synthetic `TRIP-UNKNOWN` references now suppress that fake id entirely, which keeps the queue from presenting placeholder metadata as if it were a real trip reference
- This is worth keeping in the validation log because it was visible in the busiest command-center surface, not just in a low-traffic detail panel
