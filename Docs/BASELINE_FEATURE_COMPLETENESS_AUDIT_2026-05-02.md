# Feature Completeness Baseline Audit

**Date**: 2026-05-02
**Purpose**: Map every feature area from the vision/product spec/JTBD docs against actual implementation state. Combine code-level verification with independent first-principles assessment of what's missing, what's wrong, and what must be built.

**Source Docs Applied**:
- `PRODUCT_VISION_AND_MODEL.md` — 7-stage operational model (A through G)
- `MASTER_PRODUCT_SPEC.md` — voice intake, audit mode, architecture loops
- `PROJECT_THESIS.md` — 5 key optimization objectives
- `UX_JOBS_TO_BE_DONE.md` — jobs hierarchy per persona
- `UX_USER_JOURNEYS_AND_AHA_MOMENTS.md` — "aha moment" definitions
- `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` — irreducible primitives

**Method**: Each feature area rated on 3 axes:
- **Code Status**: What's actually in the repo
- **Vision Alignment**: Does it match what the vision describes?
- **Independent Assessment**: What a system like this actually needs (separate from both code and docs)

---

## FEATURE AREA A: Client Discovery & Intent Capture

### Vision Promised

> Smart intake, auto-follow-up generation, traveler profile summary. Dynamic question router. Two-screen model (agency forwards inquiry → traveler gets live brief link).

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Freeform text intake | ✅ Done | `extractors.py` (1,808L), regex + LLM extraction pipeline |
| Structured JSON intake | ✅ Done | `SourceEnvelope.from_structured()` |
| WhatsApp message intake | ❌ Not started | No WhatsApp API integration |
| PDF itinerary intake | ❌ Not started | Core audit mode feature — zero code |
| URL itinerary intake | ❌ Not started | Same as above |
| Voice call intake | ❌ Not started | Designed in `PHASE2_CALL_CAPTURE_IMPLEMENTATION.md` |
| Dynamic question router | 🟡 Partial | `QUESTION_PRIORITY_ORDER` exists but no iterative next-question engine. All follow-ups generated at once. |
| Two-screen model (agency + traveler) | ❌ Not started | No traveler-facing live brief surface |
| Traveler profile persistence | ❌ Not started | No customer entity in DB, no cross-trip memory |

### Independent Assessment

The intake pipeline works for text but is architecturally wrong for what comes next. The extraction monolith (1,808 lines) can't absorb PDF, voice, WhatsApp, and URL intake without decomposing. The two-screen model — arguably the product's biggest UX differentiator — has zero implementation.

**The missing primitive**: A "source adapter" abstraction. Every intake format (WhatsApp text, PDF, voice transcription, URL scrape, form input) should implement the same adapter interface: `Adapter.parse(input) → List[SourceEnvelope]`. Without this, each new format requires touching the extraction monolith.

**What the vision says but code hasn't addressed**: The `MASTER_PRODUCT_SPEC` describes a voice intake loop where the traveler answers questions and sees a Live Trip Brief update in real-time on a right panel. This requires:
1. A session model (agency creates session → generates link → traveler joins)
2. A real-time websocket or polling channel for the brief to update
3. A structured brief renderer (not text — visual trip card that updates)
4. Integration with the NB02 decision engine to drive the question sequence

None of this exists.

### Verdict: 🟡 PARTIAL (3/10)

**What blocks it**: Extraction monolith for new formats. No session model. No real-time channel.

**First thing to build**: Source adapter protocol + PDF extraction adapter (unlocks audit mode GTM wedge).

---

## FEATURE AREA B: Draft Itinerary Creation

### Vision Promised

> Itinerary skeleton generation, family/senior-aware pacing, hotel-area recommendations. Generate 2-3 ranked options with trade-off tables.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Itinerary skeleton generation | ❌ Not started | No itinerary data model exists |
| Family-aware pacing | 🟡 Partial | Tier 2 suitability does toddler/elderly pacing flags. Not connected to itinerary generation. |
| Hotel-area recommendations | ❌ Not started | No hotel/vendor model at all |
| Option generation (2-3 ranked) | ❌ Not started | `BRANCH_OPTIONS` state exists in decision model but no option space construction |
| Trade-off ranking | ❌ Not started | No weighted multi-criteria ranking |
| Rendered itinerary output | ❌ Not started | Output is `PromptBundle` — text blobs. No structured option rendering. |
| Per-person suitability in output | ❌ Not started | Suitability engine runs (Tier 1+2) but results are never rendered into itinerary options |
| Cost breakdown by category | ❌ Not started | `budget_breakdown` exists in frontend types but not in actual output |

### Independent Assessment

This is the biggest gap in the entire system. The spine correctly captures intent and makes decisions, but produces nothing visual or structured. The "aha moment" from the UX journeys — "This took 15 minutes instead of 2 days" — depends entirely on this feature area working.

**What an itinerary option should be** (not what it is):

```
ItineraryOption:
  id: "opt_1"
  name: "Italy: Culture + Coast"
  days: [
    Day 1: Rome arrival, evening walking tour {fits: all ✅}
    Day 2: Colosseum + Forum {fits: adults ✅, kids ✅, elderly ⚠️ walking}
    ...
  ]
  costs:
    flights: ₹1.2L
    stay: ₹1.5L
    activities: ₹60K
    food: ₹40K
    buffer: ₹30K
    total: ₹4.0L
  suitability:
    overall: 0.85
    per_person:
      adult_1: {score: 0.9, concerns: []}
      elderly_1: {score: 0.6, concerns: ["Day 2 walking heavy", "Day 4 stairs"]}
  trade_offs:
    vs_option_2: "More culture, less beach. ₹20K cheaper."
  why_this_fits: "Great balance of culture and coast for family with teenagers. No 6 AM starts. Local food scene."
```

None of this rendering exists. The system produces `PromptBundle.user_message` — a text string. A human would need to manually convert it into a proposal, defeating the "workflow compression" thesis.

### Verdict: 🔴 NOT IMPLEMENTED (1/10)

**What blocks it**: No itinerary data model. No structured output rendering.

**First thing to build**: `ItineraryOption` data model + rendered output from packet facts.

---

## FEATURE AREA C: Revision Loop

### Vision Promised

> "What changed and why" comparison, tradeoff views (Budget vs. Comfort vs. Activity), no structured change tracking.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Packet revision history | 🟡 Partial | `CanonicalPacket.events` logs mutations. No snapshot support. |
| "What changed" diff | ❌ Not started | No diff computation between packet versions |
| Trade-off views | ❌ Not started | No multi-dimensional comparison UI |
| Revision counter | ✅ Done | `CanonicalPacket.revision_count` exists |
| Change rationale attachment | ❌ Not started | Events capture what changed but not why |

### Independent Assessment

The event log captures mutations but can't answer "what was the packet like BEFORE the operator changed the budget from 4L to 5L?" This requires snapshots — immutable copies of the packet at key points (after intake, after operator edits, after traveler feedback).

The UX vision describes "endless WhatsApp loops, scope creep, no structured change tracking." The system needs:
1. Packet snapshots at intake/decision/output boundaries
2. A diff function that compares two snapshots
3. A timeline renderer that shows "Version 1 → Version 2 → Version 3" with what changed each time

### Verdict: 🔴 NOT IMPLEMENTED (1/10)

**What blocks it**: No snapshot mechanism. Depends on snapshot feature from Architecture Audit.

---

## FEATURE AREA D: Visa & Documentation

### Vision Promised

> Visa checklist generator by profile, document collection tracker, status dashboards.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Visa timeline risk detection | ✅ Done | `visa_timeline_risk` rule in hybrid engine |
| Visa checklist generation | ❌ Not started | No visa requirement database |
| Document collection tracker | ❌ Not started | No document storage model |
| Passport status tracking | 🟡 Partial | `passport_status` field exists in `QUESTION_PRIORITY_ORDER` |
| Document risk signal | 🟡 Partial | `document_risk` is a derived-only field in validation but never computed |

### Independent Assessment

Visa/document management is a P1 Gap (#10 in the Master Gap Register). The rule engine can detect timeline risk, but the system has no visa requirement database to generate checklists from.

**What's needed**: A data-driven visa requirement model (per destination × nationality) that can:
1. Answer "does this traveler need a visa for this destination?"
2. Compute lead time: "visa processing takes 15 working days, trip is in 10 days → RISK"
3. Generate a checklist: passport copy, photos, bank statements, flight tickets, hotel bookings

This is data-intensive, not logic-intensive. It needs a curated database, not more code.

### Verdict: 🔴 NOT IMPLEMENTED (2/10)

**What blocks it**: No visa requirement database. Gap #10.

---

## FEATURE AREA E: Booking Coordination

### Vision Promised

> Booking readiness checklist, confirmation parser, Trip Master Record.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Booking readiness signal | 🟡 Partial | `booking_readiness` in `DERIVED_ONLY_FIELDS` but never computed |
| Confirmation parser | ❌ Not started | No booking confirmation data model |
| Trip Master Record | ❌ Not started | No master record entity |
| Booking state tracking | ❌ Not started | No booking state in DB |

### Independent Assessment

Booking coordination is downstream of itinerary creation. It needs a booking data model first — what's booked, with which supplier, at what cost, with what confirmation. Without an itinerary, there's nothing to book.

This is a Phase F item — build after output rendering is working.

### Verdict: 🔴 NOT IMPLEMENTED (0/10)

---

## FEATURE AREA F: In-Trip Operations

### Vision Promised

> Day-wise ops dashboard, pickup schedule tracker, disruption playbooks.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Day-wise ops dashboard | ❌ Not started |
| Pickup schedule tracker | ❌ Not started |
| Disruption playbooks | ❌ Not started |
| Emergency operating mode | ✅ Done | `emergency` mode exists in packet model + strategy |
| Ghost concierge | 🟡 Partial | `frontier_orchestrator.py` has ghost_triggered/ghost_workflow_id |
| Sentiment/anxiety detection | 🟡 Partial | `frontier_orchestrator.py` has sentiment_score/anxiety_alert |

### Independent Assessment

In-trip ops is a P2 gap (#09). The emergency mode and frontier infrastructure exist, but there's no operational dashboard. This is a Phase G item — after core booking and itinerary features land.

### Verdict: 🟡 SEEDED (2/10)

**What's there**: Emergency mode classification, basic frontier signals.
**What's missing**: Everything operational.

---

## FEATURE AREA G: Post-Trip Memory

### Vision Promised

> Traveler memory, learned preferences, future-trip suggestion engine.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Lifecycle tracking | ✅ Done | `LifecycleInfo` with 16 states, repeat_trip_count, win/loss reasons |
| Post-trip operating mode | ✅ Done | `post_trip` mode in packet model |
| Repeat customer detection | 🟡 Partial | `is_repeat_customer` in `DERIVED_ONLY_FIELDS` — never computed |
| Traveler memory/preferences | ❌ Not started | No customer preference store |
| Future-trip suggestion engine | ❌ Not started |
| Post-trip feedback collection | ❌ Not started | Gap #11 |

### Independent Assessment

The `LifecycleInfo` model is comprehensive and ready. But it needs a customer entity with persistence to store preferences across trips. Currently, every trip treats a repeat customer as new.

### Verdict: 🟡 MODEL EXISTS, NOT WIRED (3/10)

---

## FEATURE AREA H: Sourcing Hierarchy

### Vision Promised

> Optimize for Internal Packages → Preferred Partners → Network/Consortium → Open Market. Per-agency sourcing policy. Margin optimization.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Sourcing path signal | 🔴 Stub | `sourcing_path` with `maturity="stub"`, defaults to "open_market" or "network" |
| SourcingPolicy contract | ✅ Designed | `ARCHITECTURE_DECISION_D3_SOURCING_HIERARCHY` defines full contract |
| Internal packages | ❌ Not started | No package catalog |
| Preferred supplier inventory | ❌ Not started | No supplier data model |
| Margin floors per tier | ❌ Not started |
| Category-specific overrides | ❌ Not started |
| Supplier preferences/blocks | ❌ Not started |

### Independent Assessment

Sourcing is the thesis's margin lever. But it's blocked on Gap #01 (vendor/cost/sourcing). The system doesn't need live supplier data to START — it needs the abstraction that supplier data will plug into.

**What should exist now**: A `SourcingPolicy` runtime object per agency, a `SourcingTier` enum (INTERNAL, PREFERRED, NETWORK, OPEN_MARKET), and a decision rule that picks a tier based on policy + trip characteristics. Even if all tiers resolve to OPEN_MARKET today, the data model and decision path would be in place for when supplier data arrives.

**What must NOT happen**: Don't simulate sourcing with elaborate hardcoded heuristics and call it "implemented." This is the D3 ADR's explicit guidance.

### Verdict: 🔴 STUB ONLY (1/10)

**What blocks it**: Gap #01 vendor/cost/sourcing. No supplier data model.

---

## FEATURE AREA I: Per-Person Suitability

### Vision Promised

> Per-person utility scoring. Wasted spend detection. Split-day recommendations. "Universal Studios = 20% utility for toddlers."

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Activity catalog | ✅ Done | 17 static activities in `catalog.py` |
| Tier 1: age/intensity/tag rules | ✅ Done | `scoring.py` with `TAG_RULES`, age/weight bounds |
| Tier 2: day/trip coherence | ✅ Done | `context_rules.py` with intensity thresholds |
| Pipeline integration | ✅ Done | `integration.py` wired into orchestration.py (Phase 3.5) |
| Per-person utility percentage | ❌ **NOT DONE** | **Core thesis concept. 0% implemented.** |
| Wasted spend calculation | ❌ **NOT DONE** | **Core thesis concept. 0% implemented.** |
| Split-day recommendations | ❌ Not started | "Suggest alternative for low-utility members" |
| Tier 3: LLM contextual scorer | ❌ Not started | Gated by plugin system + eval framework |
| Agency-specific activity catalog | ❌ Not started | Static catalog only |
| Context population from packet | 🟡 Partial | `SuitabilityContext` has rich fields but they're not populated from actual packet data |
| Activity scoring for all catalog items | 🔴 Bug | `assess_activity_suitability()` only checks `STATIC_ACTIVITIES[:10]` |

### Independent Assessment

The suitability architecture is correct. The deterministic-first approach (Tier 1 rules → Tier 2 context → Tier 3 LLM) is exactly right. But the two most important thesis features are completely absent:

1. **Utility percentage**: The system can say "toddler excluded from snorkeling" but can't say "this activity has 20% utility for this toddler." Utility != exclusion. A museum visit might have 80% utility for a toddler (boring but not harmful), while a water park has 100% utility. The system needs a utility scoring function, not just an exclusion/inclusion flag.

2. **Wasted spend**: If 3 out of 5 family members get <30% utility from an activity that costs ₹5,000/person, that's ₹15,000 of wasted spend. The thesis explicitly calls this out as a key value prop. Zero implementation.

**What's also wrong**: The catalog is hardcoded (17 activities) and only 10 are scored. The context model has fields for season, climate, trip duration — but they're never populated. SuitabilityContext is always empty/default.

### Verdict: 🟡 FOUNDATION EXISTS, THESIS FEATURES MISSING (5/10)

**The architecture is right. The implementation is incomplete at exactly the points the thesis emphasizes.**

---

## FEATURE AREA J: Autonomy & Governance (D1)

### Vision Promised

> Agency-owned autonomy policy. Per-decision_state gates (auto/review/block). Human-in-the-loop for safety-critical decisions.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| AutonomyPolicy model | ✅ Done | `AgencyAutonomyPolicy` with approval_gates, mode_overrides |
| Three-layer autonomy (judgment→policy→human) | ✅ Done | `NB02JudgmentGate` + `AutonomyOutcome` |
| STOP_NEEDS_REVIEW → block invariant | ✅ Done | Enforced in gate (line 195) AND in settings post_init |
| Per-decision_state gates | ✅ Done | `_DEFAULT_APPROVAL_GATES` with 5 states |
| Mode overrides | ✅ Done | Emergency: PROCEED_TRAVELER_SAFE→block. Audit: PROCEED_INTERNAL_DRAFT→review |
| Warning policy | ✅ Done | `auto_proceed_with_warnings` flag |
| Legacy thresholds (backward compat) | ✅ Done | `min_proceed_confidence`, `min_draft_confidence` still present |
| Adaptive autonomy (customer+trip classification) | ❌ Not started | Needs pilot data |
| Settings persistence | ✅ Done | SQLite-backed `AgencySettingsStore` |

### Independent Assessment

D1 is the most complete architecture decision. The three-layer model is correct and well-implemented. The only gap is adaptive autonomy — which by design should NOT exist until pilot override data exists.

**What's architecturally interesting**: The system separates the RAW NB02 verdict from the POLICY-ALLOWED action. This means the decision engine can say "this should proceed," the policy says "but your agency requires review," and the output carries both pieces of information. This is exactly right for audit trails and override learning.

**What to watch**: The dual threshold system (legacy `min_proceed_confidence` + new `approval_gates`) is confusing. Once the ADR-native model is proven in production, remove the legacy thresholds.

### Verdict: ✅ STRONG (8/10)

---

## FEATURE AREA K: Free Engine / Trip Audit (D2)

### Vision Promised

> Consumer-facing "Trip Audit" — upload your itinerary, see if it fits your group. Lead-gen wedge. Handoff to partner agencies.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| `audit` operating mode | ✅ Done | Wired in packet model, decision routing, strategy, frontend selectors |
| Audit-mode decision logic | ✅ Done | value_gap check, audit-specific blocker suppression |
| Audit-mode tests | ✅ Done | In test_nb02_v02.py, test_nb03_v02.py |
| Document extraction (PDF/URL) | ❌ **NOT DONE** | **The entire feature depends on this. None exists.** |
| Itinerary parsing from docs | ❌ Not started |
| Wasted spend scoring | ❌ Not started |
| Fit Score framework (5 dimensions) | ❌ Not started | Spec in AUDIT_AND_INTELLIGENCE_ENGINE.md |
| Consumer presentation_profile | ❌ Not started | D2 consumer surface |
| Public itinerary-checker page | 🟡 Partial | `/itinerary-checker` page exists but uses agency spine, degrades to incomplete_intake |
| Lead-gen handoff flow | ❌ Not started |

### Independent Assessment

D2 is the most important GTM wedge. The fact that `audit` mode is a first-class operating mode with decision routing and tests means the infrastructure is ready. But the feature itself depends entirely on document extraction — which doesn't exist.

**The architectural trap**: D2 is sequenced correctly in the ADR (agency audit first → consumer surface after D6 proves accuracy). But audit mode is marked "exists" in status docs because the operating_mode field exists — not because the feature works. This creates false confidence.

**What must happen**: (1) Build document extraction. (2) Run the extraction through NB01→NB02→NB03 with audit operating_mode. (3) Verify the output is useful BEFORE building any consumer-facing surface. (4) Build D6 eval harness to gate consumer release.

### Verdict: 🔴 INFRASTRUCTURE EXISTS, FEATURE ABSENT (2/10)

**The mode is there. The extraction isn't. Don't claim D2 is "partially done" because the enum value exists.**

---

## FEATURE AREA L: Override & Feedback Learning (D5)

### Vision Promised

> Override events captured. Pattern detection. Policy suggestion engine. Owner approval required for changes.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Override API | ✅ Done | P1-02: POST /trips/{id}/override |
| OverrideEvent contract | ✅ Designed | 3 categories, 2-phase learning, required rationale |
| Feedback bus | ❌ Not started | No event publish/subscribe |
| Override storage | ❌ Not started | Blocked by Gap #02 (persistence) |
| Pattern detection | ❌ Not started | "intake_extractor overridden 15x on family trips" |
| Policy suggestion engine | ❌ Not started |
| Owner approval workflow | ❌ Not started |

### Independent Assessment

The override API exists but the LEARNING loop doesn't. This is correct sequencing — you can't learn from overrides before overrides exist and are stored. D5 Phase 2 (adaptive governance) should be built after the system has real-world override data from pilot agencies.

**Architectural requirement**: The feedback bus should be event-driven (publish override → subscribe pattern detector → queue suggestion → owner inbox). This decouples the override action from the learning analysis, allowing each to evolve independently.

### Verdict: 🟡 API EXISTS, LEARNING NOT STARTED (3/10)

---

## FEATURE AREA M: Evaluation & Quality (D6)

### Vision Promised

> Manifest-driven eval categories (planned→shadow→gating). 200-500 gold-labeled cases. Mutation loop for prompt optimization.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Test suite | ✅ Done | ~1,104 test functions across 71 files |
| Fixture compare framework | ✅ Done | In orchestration.py (Section 4), 6 assertion types |
| Scenario-based testing | ✅ Done | test_comprehensive_v02.py, test_realworld_scenarios.py |
| `src/evals/` directory | ❌ Not started | Does not exist |
| Golden path fixtures | ❌ Not started |
| Shadow replay framework | ❌ Not started |
| Manifest runner | ❌ Not started |
| Category promotion machinery | ❌ Not started |
| Gating status used by presentation logic | ❌ Not started |

### Independent Assessment

The test suite is large (1,104 tests) but doesn't replace the eval harness. Tests verify contracts. The eval harness verifies QUALITY. These are different.

**What D6 needs**: A separate `src/evals/` package that:
1. Loads manifest files defining eval categories (budget_accuracy, suitability_precision, extraction_recall)
2. Runs pipeline against golden path fixtures (known inputs → expected outputs)
3. Produces a composite score per category
4. Gates features: "suitability precision < 0.8 → don't show traveler"
5. In shadow mode: capture real production runs, replay against code changes, flag regressions

This is NOT the same as pytest. It's a quality measurement framework.

**The urgent reason to build D6 now**: Every claim of "the feature is ready" is unverifiable without it. D2 consumer surface can't ship without D6. D4 Tier 3 can't be evaluated without D6. D5 learning can't be measured without D6.

### Verdict: 🔴 CRITICAL GAP (2/10)

**The test suite is strong. The quality measurement framework doesn't exist. These are different things.**

---

## FEATURE AREA N: Output Delivery & Channels

### Vision Promised

> Multi-channel output: WhatsApp, email, web proposal. Agency-branded. Structured, not text.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Web output (workbench) | ✅ Done | Frontend renders pipeline results |
| WhatsApp output | 🟡 Partial | `whatsapp_formatter.py` exists but not connected to delivery |
| Email output | ❌ Not started | Gap #03 |
| SMS output | ❌ Not started |
| Agency-branded proposals | ❌ Not started |
| Structured output (not text) | ❌ Not started | Output is PromptBundle — text blobs |
| shareToken / secure links | ❌ Not started | Designed in UNIFIED_COMMUNICATION_STRATEGY.md |

### Independent Assessment

The system produces internal output (workbench) but has no external delivery. The `whatsapp_formatter.py` exists but formats text, not structured itineraries. The vision describes WhatsApp as the primary channel for Indian agencies, yet the system can't send a WhatsApp message.

**What's architecturally needed**: A channel abstraction:
```python
class OutputChannel:
    def deliver(self, traveler_bundle, channel_config) -> DeliveryResult
```

With implementations for WhatsApp (WATI/Twilio), Email (SendGrid/SES), and Web (shareToken link → traveler portal). Each channel formats the structured itinerary for its medium — WhatsApp gets a compact version, email gets a rich HTML version, web gets an interactive version.

### Verdict: 🔴 INTERNAL ONLY, NO EXTERNAL DELIVERY (2/10)

---

## FEATURE AREA O: Financial & Pricing

### Vision Promised

> Quote/collected/pending/confirmed state tracking. Fee calculation. Margin optimization. Budget decomposition.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Fee calculation | ✅ Done | `src/fees/calculation.py`, wired in orchestration.py |
| Budget decomposition | 🟡 Partial | `budget_breakdown` model in frontend types but not fully implemented |
| Payment state tracking | ❌ Not started | Gap #04 |
| Quote state machine | ❌ Not started |
| Margin optimization per sourcing tier | ❌ Not started |

### Independent Assessment

Fee calculation works but produces a single number. Real-world travel pricing has uncertainty — supplier rates change, currencies fluctuate, seasonal surcharges kick in. The pricing model should produce ranges with confidence bands.

**What's needed**: `EstimatedCost { low: float, high: float, confidence: float }` — not a single number. This feeds into budget feasibility with "there's a 60% chance this trip fits within your budget" rather than "feasible / infeasible."

### Verdict: 🟡 BASIC EXISTS, NOT PRODUCTION (3/10)

---

## FEATURE AREA P: Analytics & Reporting

### Vision Promised

> Owner dashboards, conversion metrics, KPI tracking, team performance.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Analytics module | 🟡 Scaffolded | `src/analytics/engine.py` (136L), `metrics.py`, `models.py`, `review.py` |
| Dashboard stats endpoint | ✅ Done | `GET /dashboard/stats` in server.py |
| Conversion metrics | ❌ Not started |
| Team performance | ❌ Not started |
| KPI dashboards | ❌ Not started |
| Export functionality | 🟡 Mock | `POST /analytics/export` returns mock URL |

### Independent Assessment

The analytics module is scaffolded but not operational. `calculations.py` was proposed in the dashboard governance plan but never built. The dashboard stats endpoint returns data but the analytics module that should produce it is mostly stubs.

### Verdict: 🟡 SCAFFOLDED, NOT OPERATIONAL (2/10)

---

## FEATURE AREA Q: Multi-Tenant Infrastructure

### Vision Promised

> Per-agency isolation. Role-based access. Workspace codes. Team management.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Auth (JWT + bcrypt) | ✅ Done | Custom JWT, httpOnly cookies |
| Agency/User/Membership models | ✅ Done | PostgreSQL + SQLAlchemy 2.0 |
| Workspace codes | ✅ Done | Generation, validation, join flow |
| Role-based permissions | ✅ Done | 5 roles with permission matrix |
| Signup/Login/Logout | ✅ Done | Frontend + backend |
| Tenant scoping in queries | 🟡 Partial | Some routes scope by agency_id, not all |
| RLS policies | ❌ Not started | Documented, not implemented |
| JSON→Postgres migration | 🟡 Partial | Tenant models in Postgres, operational data still in JSON |
| Feature flags per agency | ❌ Not started |

### Independent Assessment

Identity and tenancy are well-implemented. The gap is in the transition from JSON to Postgres for operational data (trips, assignments, audit events) and the lack of RLS as defense-in-depth.

### Verdict: 🟡 MOSTLY DONE, NEEDS HARDENING (6/10)

---

## FEATURE AREA R: Production & Deployment

### Vision Promised

> Deployable on Render/Fly.io. Docker support. Observability. Production hardening.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Docker support | 🟡 Partial | Dockerfile exists but has hyphen-vs-underscore path issue (deployment only — local dev uses `uv run uvicorn`) |
| Render config | ✅ Done | `render.yaml` exists |
| Fly.io config | ✅ Done | `fly.toml` exists |
| OpenTelemetry | ✅ Done | OTel spans on all pipeline stages |
| LLM usage guard | ✅ Done | Dogfood-only (single process). Needs Redis for production. |
| PII scrubbing | ✅ Done | Logging filter installed |
| Rate limiting | ❌ Not started |
| CI/CD pipeline | ❌ Not started | No GitHub Actions for test/build |
| Health endpoint | ✅ Done | `/health` returns OK |

### Independent Assessment

The system is deployable locally but not production-hardened. The Dockerfile issue (hyphens vs underscores) is a 15-minute fix when needed — local dev uses `uv run uvicorn`. Rate limiting, CI/CD, and Redis-backed guard storage are the production blockers.

### Verdict: 🟡 DEV-READY, NOT DEPLOY-READY (4/10)

---

## FEATURE AREA S: Traveler-Facing Surfaces

### Vision Promised

> Traveler portal. Itinerary checker. Live trip brief. Secure share links.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Itinerary checker page | 🟡 Partial | `/itinerary-checker` page exists, uses agency spine, degrades to incomplete |
| Traveler portal | ❌ Not started |
| Live trip brief | ❌ Not started |
| Secure share links | ❌ Not started |
| Traveler auth | ❌ Not started | No traveler account concept |

### Independent Assessment

The itinerary checker page exists as a placeholder but can't actually check itineraries (no document extraction). The traveler portal — where a client sees their itinerary, visa checklist, payment status — has zero implementation.

### Verdict: 🔴 NOT STARTED (1/10)

---

## FEATURE AREA T: Agency Marketplace / Network Effects

### Vision Promised

> Partner agency handoff. Federated intelligence. Anonymized cross-agency data.

### Code Reality

| Sub-Feature | Status | Notes |
|-------------|--------|-------|
| Federated intelligence | 🟡 Stub | `federated_intelligence.py` exists, content minimal |
| Partner agency network | ❌ Not started |
| Handoff protocol | ❌ Not started |
| Anonymized data aggregation | ❌ Not started |

### Independent Assessment

This is Phase Z — post-revenue, post-pilot. The federated intelligence module exists as a stub. Building partner agency features before a single agency uses the product is premature.

### Verdict: ⬜ FUTURE (0/10)

---

## CONSOLIDATED FEATURE MATRIX

| Area | Feature | Status | Score | Priority |
|------|---------|--------|-------|----------|
| A | Client Discovery & Intent Capture | 🟡 Partial | 3/10 | P0 |
| B | Draft Itinerary Creation | 🔴 Not implemented | 1/10 | **P0** |
| C | Revision Loop | 🔴 Not implemented | 1/10 | P1 |
| D | Visa & Documentation | 🔴 Not implemented | 2/10 | P1 |
| E | Booking Coordination | 🔴 Not implemented | 0/10 | P2 |
| F | In-Trip Operations | 🟡 Seeded | 2/10 | P2 |
| G | Post-Trip Memory | 🟡 Model exists | 3/10 | P2 |
| H | Sourcing Hierarchy | 🔴 Stub only | 1/10 | P1 |
| I | Per-Person Suitability | 🟡 Foundation | 5/10 | **P0** |
| J | Autonomy & Governance (D1) | ✅ Strong | 8/10 | Complete |
| K | Free Engine / Trip Audit (D2) | 🔴 Infra only | 2/10 | **P0** |
| L | Override & Feedback (D5) | 🟡 API only | 3/10 | P1 |
| M | Evaluation & Quality (D6) | 🔴 Critical gap | 2/10 | **P0** |
| N | Output Delivery & Channels | 🔴 Internal only | 2/10 | P1 |
| O | Financial & Pricing | 🟡 Basic | 3/10 | P1 |
| P | Analytics & Reporting | 🟡 Scaffolded | 2/10 | P2 |
| Q | Multi-Tenant Infrastructure | 🟡 Mostly done | 6/10 | P1 |
| R | Production & Deployment | 🟡 Dev-ready | 4/10 | P2 |
| S | Traveler-Facing Surfaces | 🔴 Not started | 1/10 | P2 |
| T | Agency Marketplace | ⬜ Future | 0/10 | P3 |

**Overall score: 49 / 200 (24.5%)**

---

## BUILD SEQUENCE (Dependency-Ordered)

### Wave 0: Foundation (Complete ✅)
- Q: Multi-tenant infrastructure
- J: Autonomy & governance

### Wave 1: Core Pipeline (Now — Weeks 1-4)

| # | Feature | Why First |
|---|---------|-----------|
| 1 | M: D6 Eval harness | All quality claims need measurement |
| 2 | I: Per-person utility scoring + wasted spend | Thesis differentiators. Foundation exists. |
| 3 | A: Source adapter protocol + PDF extraction | Unlocks D2 audit mode and all future intake formats |
| 4 | B: Structured itinerary output model + rendering | The "aha moment." Everything visual depends on this. |

### Wave 2: Output & Delivery (Weeks 5-8)

| # | Feature | Why |
|---|---------|-----|
| 5 | K: D2 Audit mode (wired end-to-end) | GTM wedge. Depends on Wave 1 PDF extraction. |
| 6 | N: WhatsApp/email output channels | Agency workflow integration |
| 7 | C: Revision graph / diff model | Operator UX for change tracking |
| 8 | H: SourcingPolicy abstraction (no data yet) | Architecture placeholder for supplier data |

### Wave 3: Operations (Weeks 9-12)

| # | Feature | Why |
|---|---------|-----|
| 9 | D: Visa requirement database + checklist generator | Operational completeness |
| 10 | O: Financial state tracking (quote→confirmed) | Revenue operations |
| 11 | L: D5 Override feedback bus (Phase 1) | Override capture + storage |

### Wave 4: Scale (Weeks 13-16)

| # | Feature | Why |
|---|---------|-----|
| 12 | P: Analytics dashboards | Owner visibility |
| 13 | S: Traveler portal (basic) | Client-facing surface |
| 14 | E: Booking coordination | Downstream of itinerary |
| 15 | R: Production hardening (Redis, rate limiting, CI/CD) | Deployment |

### Wave 5: Future

| # | Feature |
|---|---------|
| 16 | F: In-trip operations dashboard |
| 17 | G: Post-trip memory + preference learning |
| 18 | T: Agency marketplace / network effects |

---

## WHAT THE 24.5% SCORE MEANS

The system is a **decision engine** that doesn't produce decisions anyone can see. It's a **workflow compression tool** that compresses the thinking but not the output. It's an **agency OS** where the OS boots but no applications are installed.

The spine is correct. The pipeline is deterministic. The data model is rich. But none of the features that make this a TRAVEL product — itinerary rendering, per-person suitability display, document extraction for audit mode, WhatsApp output — exist.

**The "aha moment" gap is real**: The UX journeys describe an agent going from WhatsApp message to personalized options in 15 minutes. The code can process the message and make decisions in 30 seconds, but produces text blobs that a human must manually convert into a proposal. The 15-minute promise is structurally impossible with the current output layer.

**What changes when D6, utility scoring, and rendered output land**: The score jumps from 24.5% to ~55%. The system can then produce actual itinerary options with suitability badges and cost breakdowns. This is the minimum viable "aha moment."

---

*This document — BASELINE_FEATURE_COMPLETENESS_AUDIT_2026-05-02.md — is the authoritative source for feature completeness. Update it when features ship. Cross-reference with ARCHITECTURE_AUDIT_CODEBASE for component-level ratings and DOCUMENTATION_HEALTH_AUDIT for doc quality.*